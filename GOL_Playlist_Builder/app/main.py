import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import os
import sys
import pytesseract
from PIL import ImageGrab
from ocr import extract_text
from parser import parse
from matcher import load_config, scan, match
from m3u import write

# --- CONFIGURACIÓN DINÁMICA DE TESSERACT OCR PARA PYINSTALLER ---
if getattr(sys, 'frozen', False):
    BASE = Path(sys._MEIPASS)
    tesseract_exe = BASE / "tesseract" / "tesseract.exe"
    pytesseract.pytesseract.tesseract_cmd = str(tesseract_exe)
else:
    BASE = Path(__file__).resolve().parent
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

CFG = load_config(BASE / "config.json")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GOL Playlist Builder")
        self.geometry("1100x720")
        self.image = None; self.rows = []; self.files = []; self.matches = []
        
        # Ruta origen por defecto (se puede cambiar o expandir en la interfaz)
        self.folder = tk.StringVar(value=r"D:\PARRILLAS\GOL")
        self.output = tk.StringVar(value="playlist.m3u")
        self.status = tk.StringVar(value="Pega una captura con Ctrl+V.")
        self.ui()
        self.bind("<Control-v>", lambda e: self.paste())

    def ui(self):
        p = {"padx": 10, "pady": 7}
        ttk.Label(self, text="GOL Playlist Builder", font=("Segoe UI", 20, "bold")).pack(anchor="w", **p)
        ttk.Label(self, text="Captura de Pantalla → Búsqueda Recursiva Multidisco → M3U").pack(anchor="w", **p)
        
        f = ttk.Frame(self); f.pack(fill="x", **p)
        ttk.Button(f, text="📋 Pegar captura (Ctrl+V)", command=self.paste).pack(side="left", padx=4)
        ttk.Button(f, text="🖼 Cargar imagen", command=self.load).pack(side="left", padx=4)
        ttk.Button(f, text="🔎 Analizar y Buscar", command=self.analyze).pack(side="left", padx=4)
        ttk.Button(f, text="🚀 Generar M3U", command=self.generate).pack(side="right", padx=4)

        g = ttk.LabelFrame(self, text="Carpeta o Disco de Búsqueda (Soporta rutas personalizadas como E:\ o C:\Material)")
        g.pack(fill="x", **p)
        ttk.Entry(g, textvariable=self.folder).pack(side="left", fill="x", expand=True, padx=6, pady=6)
        ttk.Button(g, text="Examinar local", command=self.choose_folder).pack(side="right", padx=6)

        o = ttk.LabelFrame(self, text="Nombre de archivo Salida (.m3u)")
        o.pack(fill="x", **p)
        ttk.Entry(o, textvariable=self.output).pack(fill="x", padx=6, pady=6)

        self.text = tk.Text(self, height=8); self.text.pack(fill="x", **p)
        
        # Tabla limpia de 2 columnas enfocada 100% en el Match
        cols = ("titulo", "archivo")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        
        self.tree.heading("titulo", text="Contenido Detectado (Screenshot)")
        self.tree.column("titulo", width=450)
        self.tree.heading("archivo", text="Ubicación Física del Archivo Encontrado")
        self.tree.column("archivo", width=600)
        
        self.tree.pack(fill="both", expand=True, **p)
        ttk.Label(self, textvariable=self.status).pack(anchor="w", **p)

    def paste(self):
        img = ImageGrab.grabclipboard()
        if hasattr(img, "convert"):
            self.image = img; self.status.set(f"Captura pegada correctamente.")
        else:
            messagebox.showwarning("Portapapeles", "No hay una imagen válida en el portapapeles.")

    def load(self):
        f = filedialog.askopenfilename(filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.webp")])
        if f:
            self.image = __import__("PIL").Image.open(f)
            self.status.set(f"Imagen cargada desde archivo.")

    def choose_folder(self):
        f = filedialog.askdirectory()
        if f:
            self.folder.set(f)

    def analyze(self):
        if not self.image:
            messagebox.showwarning("Falta captura", "Por favor pega o carga un screenshot primero."); return
        
        target_path = self.folder.get().strip()
        if not os.path.exists(target_path):
            messagebox.showerror("Ruta no encontrada", f"La ubicación '{target_path}' no existe en este equipo."); return
            
        try:
            self.status.set("Analizando imagen con OCR portable...")
            self.update()
            
            raw = extract_text(self.image)
            self.text.delete("1.0", "end")
            self.text.insert("1.0", raw)
            
            self.rows = parse(raw)
            
            self.status.set(f"Escaneando recursivamente todo el material en: {target_path}...")
            self.update()
            
            # Escaneo profundo: Busca en la carpeta especificada y en TODAS sus subcarpetas internas
            self.files = scan(target_path, CFG["supported_extensions"])
            
            fixed = CFG["fixed_mappings"]
            minimum = CFG["minimum_match_score"]
            
            # Buscar el archivo óptimo comparando el nombre limpio extraído contra el índice
            self.matches = [match(r.title, self.files, fixed, minimum) for r in self.rows]
            
            for x in self.tree.get_children():
                self.tree.delete(x)
                
            for r, (p, s) in zip(self.rows, self.matches):
                self.tree.insert("", "end", values=(r.title, str(p) if p else "❌ NO ENCONTRADO EN ESTE DISCO/CARPETA"))
                
            ok = sum(1 for p, s in self.matches if p and p.exists())
            self.status.set(f"Escaneo finalizado. {len(self.files)} videos indexados · {ok}/{len(self.matches)} vinculados con éxito.")
            
        except Exception as e:
            messagebox.showerror("Error de Ejecución", str(e))

    def generate(self):
        missing = [r.title for r, (p, s) in zip(self.rows, self.matches) if not p or not p.exists()]
        if missing:
            if not messagebox.askyesno("Archivos Faltantes", f"Hay {len(missing)} elementos no encontrados en la carpeta actual.\n\n¿Deseas generar la playlist ignorando los elementos faltantes?"):
                return
                
        dest = filedialog.asksaveasfilename(defaultextension=".m3u", initialfile=self.output.get(), filetypes=[("M3U", "*.m3u")])
        if not dest:
            return
            
        # Filtrar solo las rutas que sí fueron halladas para armar la lista limpia
        valid_paths = [p for p, s in self.matches if p and p.exists()]
        write(valid_paths, dest)
        self.status.set("¡Playlist M3U exportada correctamente!")
        messagebox.showinfo("Proceso Exitoso", f"Playlist guardada en:\n{dest}")

if __name__ == "__main__":
    App().mainloop()

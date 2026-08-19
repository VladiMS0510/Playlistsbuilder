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
    # Si corre empaquetado en el ejecutable EXE portátil
    BASE = Path(sys._MEIPASS)
    tesseract_exe = BASE / "tesseract" / "tesseract.exe"
    pytesseract.pytesseract.tesseract_cmd = str(tesseract_exe)
else:
    # Si corre en modo desarrollo en tu editor de código
    BASE = Path(__file__).resolve().parent
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

CFG = load_config(BASE / "config.json")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GOL Playlist Builder")
        self.geometry("1100x720")
        self.image = None; self.rows = []; self.files = []; self.matches = []
        self.folder = tk.StringVar(value=r"D:\PARRILLAS\GOL")
        self.output = tk.StringVar(value="playlist.m3u")
        self.status = tk.StringVar(value="Pega una captura con Ctrl+V.")
        self.ui()
        self.bind("<Control-v>", lambda e: self.paste())

    def ui(self):
        p = {"padx": 10, "pady": 7}
        ttk.Label(self, text="GOL Playlist Builder", font=("Segoe UI", 20, "bold")).pack(anchor="w", **p)
        ttk.Label(self, text="Captura de Pantalla → Extracción por Títulos → Búsqueda de Archivos → M3U").pack(anchor="w", **p)
        
        f = ttk.Frame(self); f.pack(fill="x", **p)
        ttk.Button(f, text="📋 Pegar captura (Ctrl+V)", command=self.paste).pack(side="left", padx=4)
        ttk.Button(f, text="🖼 Cargar imagen", command=self.load).pack(side="left", padx=4)
        ttk.Button(f, text="🔎 Analizar", command=self.analyze).pack(side="left", padx=4)
        ttk.Button(f, text="🚀 Generar M3U", command=self.generate).pack(side="right", padx=4)

        g = ttk.LabelFrame(self, text="Carpeta raíz")
        g.pack(fill="x", **p)
        ttk.Entry(g, textvariable=self.folder).pack(side="left", fill="x", expand=True, padx=6, pady=6)
        ttk.Button(g, text="Examinar", command=self.choose_folder).pack(side="right", padx=6)

        o = ttk.LabelFrame(self, text="Salida")
        o.pack(fill="x", **p)
        ttk.Entry(o, textvariable=self.output).pack(fill="x", padx=6, pady=6)

        self.text = tk.Text(self, height=8); self.text.pack(fill="x", **p)
        
        # TABLA SIMPLIFICADA: Solo procesa el título extraído y el archivo físico coincidente
        cols = ("titulo", "archivo")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        
        self.tree.heading("titulo", text="Contenido / Título")
        self.tree.column("titulo", width=450)
        self.tree.heading("archivo", text="Archivo Encontrado Coincidente")
        self.tree.column("archivo", width=600)
        
        self.tree.pack(fill="both", expand=True, **p)
        ttk.Label(self, textvariable=self.status).pack(anchor="w", **p)

    def paste(self):
        img = ImageGrab.grabclipboard()
        if hasattr(img, "convert"):
            self.image = img; self.status.set(f"Captura pegada: {img.width}x{img.height}px")
        else:
            messagebox.showwarning("Portapapeles", "No hay una imagen en el portapapeles.")

    def load(self):
        f = filedialog.askopenfilename(filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.webp")])
        if f:
            self.image = __import__("PIL").Image.open(f)
            self.status.set(f"Imagen cargada: {f}")

    def choose_folder(self):
        f = filedialog.askdirectory()
        if f:
            self.folder.set(f)

    def analyze(self):
        if not self.image:
            messagebox.showwarning("Falta captura", "Pega o carga una captura."); return
        try:
            self.status.set("OCR en progreso..."); self.update()
            raw = extract_text(self.image); self.text.delete("1.0", "end"); self.text.insert("1.0", raw)
            
            self.rows = parse(raw)
            self.files = scan(self.folder.get(), CFG["supported_extensions"])
            fixed = CFG["fixed_mappings"]; minimum = CFG["minimum_match_score"]
            
            self.matches = [match(r.title, self.files, fixed, minimum) for r in self.rows]
            
            # Limpiar la tabla visual
            for x in self.tree.get_children():
                self.tree.delete(x)
                
            # Rellenar la tabla solo con títulos y rutas encontradas
            for r, (p, s) in zip(self.rows, self.matches):
                self.tree.insert("", "end", values=(r.title, str(p) if p else "NO ENCONTRADO"))
                
            ok = sum(1 for p, s in self.matches if p and p.exists())
            self.status.set(f"{len(self.files)} archivos escaneados · {ok}/{len(self.matches)} encontrados.")
        except Exception as e:
            messagebox.showerror("Error en Análisis", str(e))

    def generate(self):
        missing = [r.title for r, (p, s) in zip(self.rows, self.matches) if not p or not p.exists()]
        if missing:
            messagebox.showwarning("Faltan contenidos", "No se generó la playlist.\n\n" + "\n".join("- " + x for x in missing[:20])); return
        dest = filedialog.asksaveasfilename(defaultextension=".m3u", initialfile=self.output.get(), filetypes=[("M3U", "*.m3u")])
        if not dest:
            return
        write([p for p, s in self.matches], dest)
        self.status.set("Playlist creada correctamente.")
        messagebox.showinfo("Listo", dest)

if __name__ == "__main__":
    App().mainloop()

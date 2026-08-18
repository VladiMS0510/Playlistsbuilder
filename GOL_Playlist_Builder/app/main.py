import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from pathlib import Path
from PIL import ImageGrab
from ocr import extract_text
from parser import parse
from matcher import load_config,scan,match
from m3u import write

BASE=Path(__file__).resolve().parent
CFG=load_config(BASE/"config.json")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GOL Playlist Builder")
        self.geometry("1100x720")
        self.image=None; self.rows=[]; self.files=[]; self.matches=[]
        self.folder=tk.StringVar(value=r"D:\PARRILLAS\GOL")
        self.output=tk.StringVar(value="playlist.m3u")
        self.status=tk.StringVar(value="Pega una captura con Ctrl+V.")
        self.ui()
        self.bind("<Control-v>",lambda e:self.paste())

    def ui(self):
        p={"padx":10,"pady":7}
        ttk.Label(self,text="GOL Playlist Builder",font=("Segoe UI",20,"bold")).pack(anchor="w",**p)
        ttk.Label(self,text="Captura de Excel → OCR → búsqueda recursiva → M3U").pack(anchor="w",**p)
        f=ttk.Frame(self); f.pack(fill="x",**p)
        ttk.Button(f,text="📋 Pegar captura (Ctrl+V)",command=self.paste).pack(side="left",padx=4)
        ttk.Button(f,text="🖼 Cargar imagen",command=self.load).pack(side="left",padx=4)
        ttk.Button(f,text="🔎 Analizar",command=self.analyze).pack(side="left",padx=4)
        ttk.Button(f,text="🚀 Generar M3U",command=self.generate).pack(side="right",padx=4)

        g=ttk.LabelFrame(self,text="Carpeta raíz")
        g.pack(fill="x",**p)
        ttk.Entry(g,textvariable=self.folder).pack(side="left",fill="x",expand=True,padx=6,pady=6)
        ttk.Button(g,text="Examinar",command=self.choose_folder).pack(side="right",padx=6)

        o=ttk.LabelFrame(self,text="Salida")
        o.pack(fill="x",**p)
        ttk.Entry(o,textvariable=self.output).pack(fill="x",padx=6,pady=6)

        self.text=tk.Text(self,height=8); self.text.pack(fill="x",**p)
        cols=("hora","dur","titulo","score","archivo")
        self.tree=ttk.Treeview(self,columns=cols,show="headings")
        for c,h,w in zip(cols,["Hora","Duración","Contenido","Confianza","Archivo"],[80,90,380,90,520]):
            self.tree.heading(c,text=h); self.tree.column(c,width=w)
        self.tree.pack(fill="both",expand=True,**p)
        ttk.Label(self,textvariable=self.status).pack(anchor="w",**p)

    def paste(self):
        img=ImageGrab.grabclipboard()
        if hasattr(img,"convert"):
            self.image=img; self.status.set(f"Captura pegada: {img.width}x{img.height}px")
        else: messagebox.showwarning("Portapapeles","No hay una imagen en el portapapeles.")

    def load(self):
        f=filedialog.askopenfilename(filetypes=[("Imágenes","*.png *.jpg *.jpeg *.bmp *.webp")])
        if f: self.image=__import__("PIL").Image.open(f)

    def choose_folder(self):
        f=filedialog.askdirectory()
        if f:self.folder.set(f)

    def analyze(self):
        if not self.image:
            messagebox.showwarning("Falta captura","Pega o carga una captura."); return
        try:
            self.status.set("OCR en progreso..."); self.update()
            raw=extract_text(self.image); self.text.delete("1.0","end"); self.text.insert("1.0",raw)
            self.rows=parse(raw)
            self.files=scan(self.folder.get(),CFG["supported_extensions"])
            fixed=CFG["fixed_mappings"]; minimum=CFG["minimum_match_score"]
            self.matches=[match(r.title,self.files,fixed,minimum) for r in self.rows]
            for x in self.tree.get_children(): self.tree.delete(x)
            for r,(p,s) in zip(self.rows,self.matches):
                self.tree.insert("","end",values=(r.time,r.duration,r.title,f"{s:.0f}%",str(p) if p else "NO ENCONTRADO"))
            ok=sum(1 for p,s in self.matches if p and p.exists())
            self.status.set(f"{len(self.files)} archivos escaneados · {ok}/{len(self.matches)} encontrados.")
        except Exception as e: messagebox.showerror("Error",str(e))

    def generate(self):
        missing=[r.title for r,(p,s) in zip(self.rows,self.matches) if not p or not p.exists()]
        if missing:
            messagebox.showwarning("Faltan contenidos","No se generó la playlist.\n\n"+"\n".join("- "+x for x in missing[:20])); return
        dest=filedialog.asksaveasfilename(defaultextension=".m3u",initialfile=self.output.get(),filetypes=[("M3U","*.m3u")])
        if not dest:return
        write([p for p,s in self.matches],dest)
        self.status.set("Playlist creada correctamente.")
        messagebox.showinfo("Listo",dest)

App().mainloop()

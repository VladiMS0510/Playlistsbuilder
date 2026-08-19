import re
from dataclasses import dataclass

@dataclass
class Row:
    title: str  # Ahora solo guardamos el título de forma limpia

# Expresiones regulares para identificar y remover tiempos/duraciones del texto del OCR
TIME_RE = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")
DUR_RE = re.compile(r"\b(?:(?:\d+\s*h)\s*)?(?:\d+\s*m)\s*(?:\d+\s*s)?\b", re.I)

def clean(s):
    return re.sub(r"\s+", " ", s).strip(" |;\t-_")

def parse(text):
    out = []
    for raw in text.splitlines():
        line = clean(raw)
        if not line:
            continue
        
        # Remover cualquier marca de tiempo u hora presente en la línea
        line = TIME_RE.sub("", line)
        # Remover cualquier marca de duración presente en la línea
        line = DUR_RE.sub("", line)
        
        # Limpiar espacios restantes tras remover los tiempos
        title = clean(line)
        
        # Filtrar encabezados comunes de tablas y textos muy cortos inservibles
        if len(title) >= 3 and title.lower() not in {"nombre", "contenido", "hora", "duracion", "duración", "total"}:
            out.append(Row(title=title))
            
    return out

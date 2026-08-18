import re
from dataclasses import dataclass

@dataclass
class Row:
    time: str
    duration: str
    title: str

TIME_RE = re.compile(r"^\s*(\d{1,2}:\d{2}(?::\d{2})?)\b")
DUR_RE = re.compile(r"\b(?:(?:\d+\s*h)\s*)?(?:\d+\s*m)\s*(?:\d+\s*s)?\b", re.I)

def clean(s):
    return re.sub(r"\s+", " ", s).strip(" |;\t")

def parse(text):
    out=[]
    for raw in text.splitlines():
        line=clean(raw)
        m=TIME_RE.search(line)
        if not m: continue
        rest=clean(line[m.end():])
        d=DUR_RE.search(rest)
        dur=d.group(0) if d else ""
        title=clean((rest[:d.start()]+" "+rest[d.end():]) if d else rest)
        if len(title)>=3 and title.lower() not in {"nombre","contenido","hora","duracion","duración"}:
            out.append(Row(m.group(1),dur,title))
    return out

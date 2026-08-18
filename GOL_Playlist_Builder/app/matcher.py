import json, re, unicodedata
from pathlib import Path
from rapidfuzz import fuzz, process

def norm(s):
    s=unicodedata.normalize("NFKD",s)
    s="".join(c for c in s if not unicodedata.combining(c))
    s=s.lower().replace("_"," ").replace("-"," ")
    return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9ñáéíóúü ]+"," ",s)).strip()

def load_config(p): return json.loads(Path(p).read_text(encoding="utf-8"))

def scan(root, extensions):
    exts={x.lower() for x in extensions}
    return [p for p in Path(root).rglob("*") if p.is_file() and p.suffix.lower() in exts]

def match(title, files, fixed, minimum):
    nt=norm(title)
    for k,v in fixed.items():
        if norm(k)==nt: return Path(v),100
    choices={norm(p.stem):p for p in files}
    if not choices: return None,0
    r=process.extractOne(nt,choices.keys(),scorer=fuzz.token_set_ratio)
    if not r or r[1]<minimum: return None,(r[1] if r else 0)
    return choices[r[0]],r[1]

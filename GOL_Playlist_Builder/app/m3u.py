from pathlib import Path
def write(paths,dest):
    dest=Path(dest); dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text("#EXTM3U\n"+"\n".join(map(str,paths))+"\n",encoding="utf-8-sig")

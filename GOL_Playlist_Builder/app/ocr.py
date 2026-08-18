import os, sys
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter
import pytesseract

def configure():
    cmd = os.environ.get("TESSERACT_CMD")
    if cmd and Path(cmd).exists():
        pytesseract.pytesseract.tesseract_cmd = cmd
        return
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    for p in [base/"tesseract"/"tesseract.exe", Path(__file__).resolve().parent.parent/"tesseract"/"tesseract.exe"]:
        if p.exists():
            pytesseract.pytesseract.tesseract_cmd = str(p)
            return

def extract_text(image: Image.Image) -> str:
    configure()
    image = image.convert("RGB")
    image = image.resize((image.width*2, image.height*2))
    image = ImageOps.autocontrast(ImageOps.grayscale(image)).filter(ImageFilter.SHARPEN)
    return pytesseract.image_to_string(image, lang="eng+spa", config="--psm 6")

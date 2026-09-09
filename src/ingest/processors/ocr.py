"""
processors/ocr.py

Handles OCR for whole scanned PDF pages (e.g. *.scan.pdf files) and standalone image files (.png, .jpg).

Tesseract OCR engine path is configured for Windows installations.
"""

from pathlib import Path
import pymupdf as fitz
import pytesseract
from PIL import Image
import io

<<<<<<< HEAD
import os
import shutil

# Robust Tesseract binary path discovery (Windows default, env var, or system PATH)
_custom_tess = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
if Path(_custom_tess).exists():
    pytesseract.pytesseract.tesseract_cmd = _custom_tess
elif shutil.which("tesseract"):
    pytesseract.pytesseract.tesseract_cmd = shutil.which("tesseract")
=======
# Set default Tesseract binary path on Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
>>>>>>> aeb2852b64774d175569b8a8f8fdafea56a6bf0a


def ocr_pdf_page(page: fitz.Page, dpi: int = 200) -> str:
    """Render a PyMuPDF PDF page into an image and extract text using Tesseract OCR."""
    pix = page.get_pixmap(dpi=dpi)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    text = pytesseract.image_to_string(img).strip()
    return text


def ocr_image_file(image_path: str) -> str:
    """Run OCR directly on a standalone image file (PNG/JPG)."""
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img).strip()
    return text

"""
loaders.py

Turns raw archive files (PDF, DOCX, Markdown, images) into a common format:
a list of "pages" where each page is a dict with the extracted text
plus metadata about where it came from.

Every loader in this file returns the same shape:

    [
        {
            "text": "...",
            "source_file": "chronicles/book1_ch3.pdf",
            "source_type": "chronicles",   # top-level folder: chronicles/wiki/codex/ephemera/images
            "page": 3,                      # page number if applicable, else None
            "has_ocr": False,
        },
        ...
    ]
"""

from pathlib import Path
import pymupdf as fitz
import docx  # python-docx
from ingest.processors.ocr import ocr_pdf_page, ocr_image_file


def _source_type_from_path(path: Path) -> str:
    """Guess the top-level archive folder (chronicles/wiki/codex/ephemera/images)
    from the file's path. Falls back to 'unknown' if it can't tell."""
    for part in path.parts:
        if part.lower() in {"chronicles", "wiki", "codex", "ephemera", "images"}:
            return part.lower()
    return "unknown"


def load_pdf(path: str) -> list[dict]:
    """Extract text from a PDF, one entry per page.

    If a page has very little selectable text (< 30 chars) -- typical for scanned PDFs
    like *.scan.pdf -- automatic full-page OCR is executed using PyMuPDF + Tesseract.
    """
    path = Path(path)
    source_type = _source_type_from_path(path)
    pages = []

    doc = fitz.open(path)
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text().strip()
        has_ocr = False
        
        # Automatic OCR fallback for scanned pages or images of text
        if len(text) < 30:
            ocr_text = ocr_pdf_page(page)
            if ocr_text:
                text = ocr_text
                has_ocr = True

        pages.append({
            "text": text,
            "source_file": str(path),
            "source_type": source_type,
            "page": page_num,
            "has_ocr": has_ocr,
        })
    doc.close()
    return pages


def load_docx(path: str) -> list[dict]:
    """Extract text from a DOCX file as one document entry."""
    path = Path(path)
    source_type = _source_type_from_path(path)

    document = docx.Document(path)
    full_text = "\n".join(p.text for p in document.paragraphs if p.text.strip())

    return [{
        "text": full_text,
        "source_file": str(path),
        "source_type": source_type,
        "page": None,
        "has_ocr": False,
    }]


def load_markdown(path: str) -> list[dict]:
    """Load a Markdown or TXT file as plain text."""
    path = Path(path)
    source_type = _source_type_from_path(path)

    text = path.read_text(encoding="utf-8", errors="ignore").strip()

    return [{
        "text": text,
        "source_file": str(path),
        "source_type": source_type,
        "page": None,
        "has_ocr": False,
    }]


def load_image(path: str) -> list[dict]:
    """Load a standalone image file (PNG/JPG), extract text using OCR,
    and attach descriptive title metadata."""
    path = Path(path)
    source_type = _source_type_from_path(path)

    ocr_text = ocr_image_file(str(path))
    clean_title = path.stem.replace("_", " ").title()
    full_text = f"Image Plate: {clean_title}\n\n[OCR EXTRACTED TEXT]\n{ocr_text}" if ocr_text else f"Image Plate: {clean_title}"

    return [{
        "text": full_text,
        "source_file": str(path),
        "source_type": source_type,
        "page": None,
        "title": clean_title,
        "has_ocr": True,
    }]


def load_file(path: str) -> list[dict]:
    """Dispatch to the right loader based on file extension."""
    path = Path(path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return load_pdf(str(path))
    elif ext == ".docx":
        return load_docx(str(path))
    elif ext in {".md", ".txt"}:
        return load_markdown(str(path))
    elif ext in {".png", ".jpg", ".jpeg"}:
        return load_image(str(path))
    else:
<<<<<<< HEAD
        raise ValueError(f"No loader for file type: {ext} ({path})")
=======
        raise ValueError(f"No loader for file type: {ext} ({path})")
>>>>>>> aeb2852b64774d175569b8a8f8fdafea56a6bf0a

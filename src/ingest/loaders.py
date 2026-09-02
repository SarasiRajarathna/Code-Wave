"""
loaders.py

Turns raw archive files (PDF, DOCX, Markdown) into a common format:
a list of "pages" where each page is a dict with the extracted text
plus metadata about where it came from.

Why a common format matters: everything downstream (chunking, embedding,
storing) doesn't need to know or care what file type the text originally
came from. Every loader in this file returns the same shape:

    [
        {
            "text": "...",
            "source_file": "chronicles/book1_ch3.pdf",
            "source_type": "chronicles",   # top-level folder: chronicles/wiki/codex/ephemera/images
            "page": 3,                      # page number if applicable, else None
        },
        ...
    ]

This metadata is what lets the retrieval agent later say "this came from
an official codex" vs "this came from an unreliable in-world letter" --
important for track 1C, where sources can disagree.
"""

from pathlib import Path
import pymupdf as fitz
import docx  # python-docx


def _source_type_from_path(path: Path) -> str:
    """Guess the top-level archive folder (chronicles/wiki/codex/ephemera/images)
    from the file's path. Falls back to 'unknown' if it can't tell."""
    for part in path.parts:
        if part.lower() in {"chronicles", "wiki", "codex", "ephemera", "images"}:
            return part.lower()
    return "unknown"


def load_pdf(path: str) -> list[dict]:
    """Extract text from a PDF, one entry per page.

    NOTE: this only extracts text that's already selectable/embedded in the
    PDF. Scanned pages (an image of text, no real text layer) will come back
    empty here -- those need OCR instead. See ocr.py once you get there.
    A quick way to check: if a page's extracted text is empty or very short
    relative to the page, it's probably a scan.
    """
    path = Path(path)
    source_type = _source_type_from_path(path)
    pages = []

    doc = fitz.open(path)
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text().strip()
        pages.append({
            "text": text,
            "source_file": str(path),
            "source_type": source_type,
            "page": page_num,
        })
    doc.close()
    return pages


def load_docx(path: str) -> list[dict]:
    """Extract text from a DOCX file. DOCX has no real concept of 'pages'
    (that's a rendering-time thing in Word), so we return the whole document
    as one entry. If a document is long, the chunker will split it later
    anyway."""
    path = Path(path)
    source_type = _source_type_from_path(path)

    document = docx.Document(path)
    full_text = "\n".join(p.text for p in document.paragraphs if p.text.strip())

    return [{
        "text": full_text,
        "source_file": str(path),
        "source_type": source_type,
        "page": None,
    }]


def load_markdown(path: str) -> list[dict]:
    """Load a Markdown file as plain text. Wiki articles are Markdown per
    the README, so this is straightforward -- no library needed."""
    path = Path(path)
    source_type = _source_type_from_path(path)

    text = path.read_text(encoding="utf-8", errors="ignore").strip()

    return [{
        "text": text,
        "source_file": str(path),
        "source_type": source_type,
        "page": None,
    }]


def load_file(path: str) -> list[dict]:
    """Dispatch to the right loader based on file extension. This is the
    function the main pipeline script will actually call -- it doesn't need
    to know which loader handles which extension."""
    path = Path(path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return load_pdf(path)
    elif ext == ".docx":
        return load_docx(path)
    elif ext in {".md", ".txt"}:
        return load_markdown(path)
    else:
        raise ValueError(f"No loader for file type: {ext} ({path})")

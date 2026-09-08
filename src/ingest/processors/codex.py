"""
processors/codex.py

Codex PDFs mix two very different kinds of content on the same page:
  1. Real, selectable text (the prose entries) -- pymupdf's get_text()
     handles this fine.
  2. "Plate" graphics -- designed card/gauge images with a number baked
     directly into the picture (e.g. "RECORDED GARRISON STRENGTH 3,695").
     These are NOT real text. pymupdf's get_text() cannot see them, no
     matter how much text is around them on the page. This is why
     char-count checks miss them: the page might have 900+ chars of
     real prose AND still be missing the one number a question actually
     asks for.

The fix: pull out embedded images per page and run OCR on them
specifically. This is different from ephemera's whole-page-scan OCR --
here we're OCRing a small graphic embedded within an otherwise-normal
text page.
"""

import io
import re
import pymupdf as fitz
import pytesseract
from PIL import Image

import os
import shutil
from pathlib import Path

# Robust Tesseract binary path discovery (Windows default, env var, or system PATH)
_custom_tess = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
if Path(_custom_tess).exists():
    pytesseract.pytesseract.tesseract_cmd = _custom_tess
elif shutil.which("tesseract"):
    pytesseract.pytesseract.tesseract_cmd = shutil.which("tesseract")

def extract_plate_text(pdf_path: str) -> list[dict]:
    """For every page in the PDF that has an embedded image, run OCR on
    that image and return what it says, tied to the page number and
    (if findable) the entry name from the nearby 'Plate - <Name>:' caption.

    Also computes an average OCR confidence per plate. Simple number-card
    plates (one big number) OCR very reliably. Bar-chart-style plates
    (several bars with numbers beside them) are less reliable -- tesseract
    can misread a solid-color bar as a stray character and garble the
    number next to it. low_confidence=True is a signal to have a human
    glance at that specific plate rather than trust it blindly.

    Returns a list of dicts:
        {
            "page": 25,
            "entry_name": "Greyfell Citadel",   # None if no caption found
            "plate_text": "Greyfell Citadel\\nRECORDED GARRISON STRENGTH\\n3,695\\n...",
            "low_confidence": False,
        }
    """
    doc = fitz.open(pdf_path)
    results = []

    for page_num, page in enumerate(doc, start=1):
        images = page.get_images()
        if not images:
            continue

        page_text = page.get_text()
        entry_name = None
        if "Plate - " in page_text:
            start = page_text.find("Plate - ") + len("Plate - ")
            end = page_text.find(":", start)
            if end != -1:
                entry_name = page_text[start:end].strip()

        for img_info in images:
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            img = Image.open(io.BytesIO(base_image["image"]))

            ocr_text = pytesseract.image_to_string(img).strip()
            if not ocr_text:
                continue

            # Check word-level confidence to catch garbled numbers.
            # MINIMUM confidence, not average -- a garbled number sits
            # among many correctly-read words (labels, headings), so it
            # barely moves the average but tanks the minimum.
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            confidences = [c for c in data["conf"] if isinstance(c, (int, float)) and c >= 0]
            min_conf = min(confidences) if confidences else 0
            low_confidence = min_conf < 60  # clean plates stay above ~90

            # Separate, more direct check: every real plate in this archive
            # is ABOUT a number (garrison strength, attunement cost,
            # casualties...). If OCR found zero digits, that's not a
            # confidence problem -- it's tesseract silently dropping the
            # number region entirely with no trace, which the confidence
            # check above cannot see. This catches that failure mode.
            has_digit = bool(re.search(r"\d", ocr_text))
            needs_review = low_confidence or not has_digit

            results.append({
                "page": page_num,
                "entry_name": entry_name,
                "plate_text": ocr_text,
                "low_confidence": needs_review,
            })

    doc.close()
    return results


def merge_plates_into_pages(pages: list[dict], plates: list[dict]) -> list[dict]:
    """Takes the normal page dicts from loaders.load_pdf() and the OCR'd
    plate results from extract_plate_text(), and merges the plate text
    into the matching page's text -- so downstream chunking/embedding
    sees the plate's numbers as part of that page's content, not lost.
    """
    plates_by_page = {}
    for p in plates:
        plates_by_page.setdefault(p["page"], []).append(p)

    merged = []
    for page in pages:
        page = dict(page)
        page_plates = plates_by_page.get(page["page"], [])
        if page_plates:
            plate_block = "\n\n[FIGURE PLATE TEXT]\n" + "\n---\n".join(p["plate_text"] for p in page_plates)
            page["text"] = page["text"] + plate_block
            page["has_plate"] = True
            page["plate_needs_review"] = any(p["low_confidence"] for p in page_plates)
        else:
            page["has_plate"] = False
            page["plate_needs_review"] = False
        merged.append(page)

    return merged

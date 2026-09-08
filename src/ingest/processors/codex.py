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

import json
import io
import re
from pathlib import Path
import pymupdf as fitz
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def load_plate_overrides(overrides_path: str | Path | None = None) -> dict:
    """Loads manual plate overrides from JSON file if present.
    Returns a dict mapping (file_key, page_number) -> override_dict.
    Supports both nested dict format and list of dicts format.
    """
    if overrides_path is None:
        repo_root = Path(__file__).resolve().parents[3]
        candidates = [
            repo_root / "data" / "plate_overrides.json",
            repo_root / "data" / "extracted" / "plate_overrides.json",
        ]
        for c in candidates:
            if c.exists():
                overrides_path = c
                break

    if not overrides_path or not Path(overrides_path).exists():
        return {}

    try:
        with open(overrides_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except Exception as e:
        print(f"  Warning: Failed to read plate overrides from {overrides_path}: {e}")
        return {}

    normalized = {}

    def _add_entry(source_key: str, page: int | str, data: dict):
        try:
            p_num = int(page)
        except (ValueError, TypeError):
            return
        key_name = Path(source_key).name.lower()
        key_stem = Path(source_key).stem.lower()
        normalized[(key_name, p_num)] = data
        normalized[(key_stem, p_num)] = data

    if isinstance(raw_data, dict):
        for file_key, pages_map in raw_data.items():
            if file_key.startswith("_"):  # skip comments
                continue
            if isinstance(pages_map, dict):
                for p_str, override_info in pages_map.items():
                    if isinstance(override_info, dict):
                        _add_entry(file_key, p_str, override_info)
    elif isinstance(raw_data, list):
        for item in raw_data:
            if isinstance(item, dict) and "source_file" in item and "page" in item:
                _add_entry(item["source_file"], item["page"], item)

    return normalized


def get_override_for_page(overrides: dict, source_file: str, page_num: int) -> dict | None:
    if not overrides:
        return None
    s_path = Path(source_file)
    name_key = (s_path.name.lower(), page_num)
    stem_key = (s_path.stem.lower(), page_num)
    full_key = (str(source_file).lower(), page_num)
    return overrides.get(name_key) or overrides.get(stem_key) or overrides.get(full_key)


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


def merge_plates_into_pages(pages: list[dict], plates: list[dict], overrides: dict | None = None) -> list[dict]:
    """Takes the normal page dicts from loaders.load_pdf() and the OCR'd
    plate results from extract_plate_text(), and merges the plate text
    into the matching page's text -- so downstream chunking/embedding
    sees the plate's numbers as part of that page's content, not lost.

    If manual overrides are present in data/plate_overrides.json (or passed in),
    they override the OCR output and review flags for specified pages.
    """
    if overrides is None:
        overrides = load_plate_overrides()

    plates_by_page = {}
    for p in plates:
        plates_by_page.setdefault(p["page"], []).append(p)

    merged = []
    for page in pages:
        page = dict(page)
        page_num = page.get("page")
        source_file = page.get("source_file", "")

        override = get_override_for_page(overrides, source_file, page_num)
        page_plates = plates_by_page.get(page_num, [])

        if override:
            plate_text = override.get("plate_text") or override.get("text")
            needs_review = override.get("plate_needs_review", override.get("low_confidence", False))

            if plate_text:
                plate_block = "\n\n[FIGURE PLATE TEXT]\n" + plate_text
                page["text"] = page["text"] + plate_block
                page["has_plate"] = True
                page["plate_needs_review"] = needs_review
            elif page_plates:
                plate_block = "\n\n[FIGURE PLATE TEXT]\n" + "\n---\n".join(p["plate_text"] for p in page_plates)
                page["text"] = page["text"] + plate_block
                page["has_plate"] = True
                page["plate_needs_review"] = needs_review
            else:
                page["has_plate"] = False
                page["plate_needs_review"] = False
        elif page_plates:
            plate_block = "\n\n[FIGURE PLATE TEXT]\n" + "\n---\n".join(p["plate_text"] for p in page_plates)
            page["text"] = page["text"] + plate_block
            page["has_plate"] = True
            page["plate_needs_review"] = any(p["low_confidence"] for p in page_plates)
        else:
            page["has_plate"] = False
            page["plate_needs_review"] = False

        merged.append(page)

    return merged


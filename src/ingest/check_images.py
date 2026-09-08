"""
check_images.py

Your standalone images/ folder duplicates the exact same 15 figure plates
already embedded in the codex PDFs -- same content, two places. It goes
through a DIFFERENT code path (loaders.load_image -> processors/ocr.py)
that currently has NO confidence or digit safety check at all, unlike
processors/codex.py which now has one.

This script applies the same "of 10 doesn't count as a real digit" logic
to images.json, so you get one unified review list instead of two
different bugs in two different files.
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]  # this file lives at src/ingest/check_images.py
path = REPO_ROOT / 'data' / 'extracted' / 'images.json'

with open(path, encoding='utf-8') as f:
    images = json.load(f)

flagged = []
for img in images:
    text = img['text']
    ocr_part = text.split('[OCR EXTRACTED TEXT]')[-1].strip() if '[OCR EXTRACTED TEXT]' in text else ''
    text_for_check = re.sub(r'of\s+\d+', '', ocr_part, flags=re.IGNORECASE)
    has_digit = bool(re.search(r'\d', text_for_check))
    if ocr_part and not has_digit:
        flagged.append((img['source_file'], ocr_part))

print(f"{len(flagged)} standalone image(s) need manual verification:\n")
for source_file, ocr_part in flagged:
    print(f"  {source_file}")
    print(f"    OCR read: {ocr_part[:150]}")
    print()

print("Since these duplicate the codex plates, cross-check against the")
print("matching entry in data/extracted/codex.json -- if that one has the")
print("correct number, just copy it over here instead of re-verifying by eye.")

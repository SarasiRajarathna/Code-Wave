"""
check_plates.py

Run this after run_ingest.py to get a short, concrete to-do list of
codex figure plates whose OCR'd numbers might be wrong -- either
garbled (some characters missing, like Emberdeep's bar chart) or
genuinely uncertain (tesseract read a number but wasn't confident,
which often means a digit like 5/0, 6/8, or 3/8 could be swapped).

This does NOT try to auto-fix anything -- OCR confidence is a signal
for a human to glance at the actual PDF page and confirm the number,
not something worth automating further under a one-week deadline.
"""

import json
from pathlib import Path

path = Path('data/extracted/codex.json')

with open(path, encoding='utf-8') as f:
    pages = json.load(f)

flagged = [p for p in pages if p.get('plate_needs_review')]

print(f"{len(flagged)} plate(s) need manual verification:\n")
for p in flagged:
    print(f"  {p['source_file']}  page {p['page']}")
    # Print just the figure plate portion so it's quick to check
    if '[FIGURE PLATE TEXT]' in p['text']:
        plate_section = p['text'].split('[FIGURE PLATE TEXT]')[1].strip()
        print(f"    OCR read: {plate_section[:150]}")
    print()

print("For each one: open that page in the PDF, look at the actual plate")
print("image, and confirm the number by eye. Fix any wrong digits directly")
print("in data/extracted/codex.json before this feeds into embeddings.")
"""
inspect_flagged.py

Prints the FULL extracted text of every page in _needs_ocr.json so you
can eyeball each one and decide: is this actually broken (a scan, a
missing table) or just a legitimately short page (chapter break, title
page)? The char-count check can't tell the difference -- your eyes can.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]  # this file lives at src/ingest/<name>.py

flagged_path = REPO_ROOT / 'data' / 'extracted' / '_needs_ocr.json'

with open(flagged_path, encoding='utf-8') as f:
    flagged = json.load(f)

for p in flagged:
    page_label = f"page {p['page']}" if p.get('page') is not None else "(whole doc)"
    print(f"\n{'='*70}")
    print(f"{p['source_file']}  {page_label}")
    print(f"{'='*70}")
    print(repr(p['text']))  # repr shows exactly what's there, even if blank/whitespace
"""
check_extraction.py

Run this AFTER run_ingest.py. It scans every extracted JSON file and
flags pages where very little (or no) text came out. A normal text
page from a novel or codex entry has hundreds to thousands of
characters. A page that returns near-zero characters almost always
means one of:

  - a scanned/handwritten page with no real text layer (needs OCR)
  - a page that's mostly a table, diagram, or figure plate (needs
    special handling, not just OCR)
  - a genuinely blank or near-blank page (fine to ignore)
  - something the loader silently mishandled (worth a manual look)

This does NOT fix anything -- it just tells you exactly which files
and page numbers need attention next, so you're not guessing.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]  # this file lives at src/ingest/<name>.py

EXTRACTED_DIR = REPO_ROOT / 'data' / 'extracted'
MIN_CHARS = 50  # pages with fewer characters than this get flagged

def check_file(path: Path):
    with open(path, encoding='utf-8') as f:
        pages = json.load(f)

    flagged = []
    total_chars = 0

    for p in pages:
        length = len(p.get('text', '') or '')
        total_chars += length
        if length < MIN_CHARS:
            flagged.append(p)

    avg_chars = total_chars / len(pages) if pages else 0

    print(f"\n=== {path.name} ===")
    print(f"Total pages: {len(pages)}")
    print(f"Average chars/page: {avg_chars:.0f}")
    print(f"Flagged (< {MIN_CHARS} chars): {len(flagged)}")

    for p in flagged[:20]:  # show first 20 so it doesn't flood your terminal
        page_num = p.get('page')
        page_label = f"page {page_num}" if page_num is not None else "(whole doc)"
        print(f"  - {p['source_file']}  {page_label}  ->  {len(p.get('text',''))} chars")

    if len(flagged) > 20:
        print(f"  ... and {len(flagged) - 20} more")

    return flagged


def main():
    if not EXTRACTED_DIR.exists():
        print(f"No {EXTRACTED_DIR} folder found -- run run_ingest.py first.")
        return

    all_flagged = []
    for json_file in sorted(EXTRACTED_DIR.glob('*.json')):
        if json_file.name.startswith('_') or json_file.name in {'chunks.json', 'chronicles_by_chapter.json'}:
            continue
        flagged = check_file(json_file)
        all_flagged.extend(flagged)

    print(f"\n\nTOTAL flagged across all folders: {len(all_flagged)}")
    print("These are your OCR candidates -- likely scans or heavy-image pages.")

    # Save the flagged list separately so you have a concrete to-do list
    out_path = EXTRACTED_DIR / '_needs_ocr.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(all_flagged, f, ensure_ascii=False, indent=2)
    print(f"Full list saved to {out_path}")


if __name__ == '__main__':
    main()
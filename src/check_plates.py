import json
from pathlib import Path

src_dir = Path(__file__).parent
workspace_root = src_dir.parent
path = workspace_root / 'data' / 'extracted' / 'codex.json'

if not path.exists():
    print(f"File not found: {path}")
else:
    with open(path, encoding='utf-8') as f:
        pages = json.load(f)

    flagged = [p for p in pages if p.get('plate_needs_review')]

    print(f"{len(flagged)} plate(s) need manual verification:\n")
    for p in flagged:
        print(f"  {p['source_file']}  page {p['page']}")
        if '[FIGURE PLATE TEXT]' in p['text']:
            plate_section = p['text'].split('[FIGURE PLATE TEXT]')[1].strip()
            print(f"    OCR read: {plate_section[:150]}")
        print()

    print("For each one: open that page in the PDF, look at the actual plate")
    print("image, and confirm the number by eye. Fix any wrong digits directly")
    print("in data/extracted/codex.json before this feeds into embeddings.")

import json
from pathlib import Path

src_dir = Path(__file__).parent
workspace_root = src_dir.parent
flagged_path = workspace_root / 'data' / 'extracted' / '_needs_ocr.json'

if not flagged_path.exists():
    print(f"File not found: {flagged_path}")
else:
    with open(flagged_path, encoding='utf-8') as f:
        flagged = json.load(f)

    for p in flagged:
        page_label = f"page {p['page']}" if p.get('page') is not None else "(whole doc)"
        print(f"\n{'='*70}")
        print(f"{p['source_file']}  {page_label}")
        print(f"{'='*70}")
        print(repr(p['text']))

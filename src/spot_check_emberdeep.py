import json
from pathlib import Path

src_dir = Path(__file__).parent
workspace_root = src_dir.parent
codex_path = workspace_root / 'data' / 'extracted' / 'codex.json'

if not codex_path.exists():
    print(f"File not found: {codex_path}")
else:
    with open(codex_path, encoding='utf-8') as f:
        pages = json.load(f)

    for p in pages:
        if p.get('has_plate') and 'Emberdeep' in p['text'] and 'gazetteer' in p['source_file']:
            print(f"page {p['page']} of {p['source_file']}")
            print(f"plate_needs_review: {p.get('plate_needs_review')}")
            print('--- text tail ---')
            print(p['text'][-400:])
            print()

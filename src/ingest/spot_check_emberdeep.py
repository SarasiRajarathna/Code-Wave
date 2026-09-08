import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]  # this file lives at src/ingest/<name>.py

with open(REPO_ROOT / 'data' / 'extracted' / 'codex.json', encoding='utf-8') as f:
    pages = json.load(f)

for p in pages:
    if p.get('has_plate') and 'Emberdeep' in p['text'] and 'gazetteer' in p['source_file']:
        print(f"page {p['page']} of {p['source_file']}")
        print(f"plate_needs_review: {p.get('plate_needs_review')}")
        print('--- text tail ---')
        print(p['text'][-400:])
        print()
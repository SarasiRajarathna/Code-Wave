import sys
sys.path.insert(0, 'src')

import json
from pathlib import Path
from ingest.loaders import load_file
from ingest.processors.wiki import process_wiki_page

corpus_root = Path('data/corpus')          # your real corpus location
output_dir = Path('data/extracted')        # one JSON file per folder goes here

output_dir.mkdir(parents=True, exist_ok=True)

for folder in ['chronicles', 'wiki', 'codex', 'ephemera']:
    folder_path = corpus_root / folder
    if not folder_path.exists():
        print(f"Skipping {folder} -- folder not found at {folder_path}")
        continue

    folder_pages = []

    for f in folder_path.glob('*'):
        if f.suffix.lower() not in ('.pdf', '.docx', '.md', '.txt'):
            continue
        print(f'Processing {f} ...')
        try:
            pages = load_file(str(f))
            if folder == 'wiki':
                pages = [process_wiki_page(p) for p in pages]
            folder_pages.extend(pages)
        except Exception as e:
            print(f'  FAILED: {e}')

    out_path = output_dir / f'{folder}.json'
    with open(out_path, 'w', encoding='utf-8') as out:
        json.dump(folder_pages, out, ensure_ascii=False, indent=2)

    print(f'  -> {len(folder_pages)} pages saved to {out_path}\n')

print("Done. Check data/extracted/ for one JSON file per folder.")
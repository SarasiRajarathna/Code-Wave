import sys
from pathlib import Path

src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import json
from ingest.loaders import load_file
from ingest.processors.wiki import process_wiki_page
from ingest.processors.codex import extract_plate_text, merge_plates_into_pages

workspace_root = src_dir.parent
corpus_root = workspace_root / 'data' / 'corpus'
output_dir = workspace_root / 'data' / 'extracted'

output_dir.mkdir(parents=True, exist_ok=True)


def dedupe_by_basename(files: list[Path]) -> list[Path]:
    """If both book.pdf and book.docx exist, keep only the PDF -- PDF
    gives us real page numbers, which the chapter grouping and plate
    OCR both depend on. Prevents embedding every book twice."""
    by_stem = {}
    for f in files:
        stem = f.stem.lower()
        if stem not in by_stem:
            by_stem[stem] = f
        elif f.suffix.lower() == '.pdf':
            print(f'  Skipping duplicate: {by_stem[stem].name} (keeping .pdf version instead)')
            by_stem[stem] = f
        else:
            print(f'  Skipping duplicate: {f.name} (keeping .pdf version instead)')
    return list(by_stem.values())


for folder in ['chronicles', 'wiki', 'codex', 'ephemera', 'images']:
    folder_path = corpus_root / folder
    if not folder_path.exists():
        print(f"Skipping {folder} -- folder not found at {folder_path}")
        continue

    folder_pages = []
    candidate_files = [f for f in folder_path.glob('*') if f.suffix.lower() in ('.pdf', '.docx', '.md', '.txt', '.png', '.jpg', '.jpeg')]
    files = dedupe_by_basename(candidate_files)

    for f in files:
        print(f'Processing {f} ...')
        try:
            pages = load_file(str(f))

            if folder == 'wiki':
                pages = [process_wiki_page(p) for p in pages]

            if folder == 'codex' and f.suffix.lower() == '.pdf':
                plates = extract_plate_text(str(f))
                pages = merge_plates_into_pages(pages, plates)
                if plates:
                    print(f'  -> OCR found {len(plates)} figure plate(s) on this file')

            folder_pages.extend(pages)
        except Exception as e:
            print(f'  FAILED: {e}')

    out_path = output_dir / f'{folder}.json'
    with open(out_path, 'w', encoding='utf-8') as out:
        json.dump(folder_pages, out, ensure_ascii=False, indent=2)

    print(f'  -> {len(folder_pages)} pages saved to {out_path}\n')

print("Done. Check data/extracted/ for one JSON file per folder.")

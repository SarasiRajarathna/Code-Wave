import json
import re
from pathlib import Path
from collections import defaultdict

src_dir = Path(__file__).parent
workspace_root = src_dir.parent

CHAPTER_PATTERN = re.compile(
    r"^\s*(Chapter\s+[\dIVXLCM]+|CHAPTER\s+[\dIVXLCM]+|Chapter\s+\w+)\b.*$",
    re.IGNORECASE | re.MULTILINE,
)


def group_pages_by_chapter(pages: list[dict]) -> dict:
    chapters = defaultdict(list)
    current_chapter = "(front matter)"

    for page in pages:
        text = page["text"]
        match = CHAPTER_PATTERN.search(text)
        if match:
            current_chapter = match.group(1).strip()
        chapters[current_chapter].append(page["text"])

    return {ch: "\n\n".join(texts) for ch, texts in chapters.items()}


def main():
    in_path = workspace_root / 'data' / 'extracted' / 'chronicles.json'
    out_path = workspace_root / 'data' / 'extracted' / 'chronicles_by_chapter.json'

    if not in_path.exists():
        print(f"File not found: {in_path}")
        return

    with open(in_path, encoding='utf-8') as f:
        pages = json.load(f)

    by_doc = defaultdict(list)
    for p in pages:
        by_doc[p['source_file']].append(p)

    result = {}
    for doc, doc_pages in by_doc.items():
        doc_pages.sort(key=lambda p: p['page'] or 0)
        result[doc] = group_pages_by_chapter(doc_pages)

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Grouped {len(pages)} pages across {len(by_doc)} documents.")
    for doc, chapters in result.items():
        print(f"\n{doc}")
        for ch_name in chapters:
            print(f"  - {ch_name}")
    print(f"\nSaved to {out_path}")


if __name__ == '__main__':
    main()

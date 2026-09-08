"""
group_chapters.py

Takes the flat list of pages in chronicles.json and groups them by
chapter instead, so instead of "page 1, page 2, page 3..." you get
"Chapter One: [pages 1-8 combined], Chapter Two: [pages 9-15 combined]".

This makes the corpus much easier to browse AND gives you a better
chunking unit later -- chunking by chapter (with the chunker splitting
long chapters further) makes more semantic sense than chunking blindly
by raw page boundaries, which can cut a scene in half arbitrarily.

Detection: looks for lines that look like chapter headings -- e.g.
"Chapter One", "CHAPTER 12", "Chapter Twelve: The Long Reprisal".
If your novels use a different heading style, tell me a real example
and I'll adjust the pattern.
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]  # this file lives at src/ingest/<name>.py
from collections import defaultdict

CHAPTER_PATTERN = re.compile(
    r"^\s*(Chapter\s+[\dIVXLCM]+|CHAPTER\s+[\dIVXLCM]+|Chapter\s+\w+)\b.*$",
    re.IGNORECASE | re.MULTILINE,
)


def group_pages_by_chapter(pages: list[dict]) -> dict:
    """pages: flat list of page dicts for ONE document (already sorted
    by page number). Returns {chapter_heading: combined_text}."""
    chapters = defaultdict(list)
    current_chapter = "(front matter)"  # anything before the first detected heading

    for page in pages:
        text = page["text"]
        match = CHAPTER_PATTERN.search(text)
        if match:
            current_chapter = match.group(1).strip()
        chapters[current_chapter].append(page["text"])

    return {ch: "\n\n".join(texts) for ch, texts in chapters.items()}


def main():
    in_path = REPO_ROOT / 'data' / 'extracted' / 'chronicles.json'
    out_path = REPO_ROOT / 'data' / 'extracted' / 'chronicles_by_chapter.json'

    with open(in_path, encoding='utf-8') as f:
        pages = json.load(f)

    # Group pages by their source document first
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
"""
chunk.py

Splits raw extracted documents from loaders.py into clean, overlapping
chunks with rich metadata tags (chapter, section, source type, OCR flags)
for embedding and retrieval.
"""

import json
import re
import hashlib
from pathlib import Path
from collections import defaultdict

<<<<<<< HEAD
REPO_ROOT = Path(__file__).resolve().parents[2]  # this file lives at src/ingest/chunk.py

=======
>>>>>>> aeb2852b64774d175569b8a8f8fdafea56a6bf0a

CHAPTER_PATTERN = re.compile(
    r"^\s*(Chapter\s+[\dIVXLCM]+|CHAPTER\s+[\dIVXLCM]+|Chapter\s+\w+)\b.*$",
    re.IGNORECASE | re.MULTILINE,
)


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 75) -> list[str]:
    """Split text into overlapping chunks, measured by word count.

    chunk_size: target words per chunk (default 400 words ~ 500 tokens)
    overlap: word overlap between consecutive chunks
    """
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunk_str = " ".join(chunk_words).strip()
        if chunk_str:
            chunks.append(chunk_str)
        if end >= len(words):
            break
        start = end - overlap

    return chunks


def _generate_chunk_id(source_file: str, index: int, prefix: str = "") -> str:
    """Create a unique deterministic chunk ID based on source filename and chunk index."""
    stem = Path(source_file).stem.lower()
    clean_stem = re.sub(r'[^a-z0-9_]', '_', stem)
    hash_suffix = hashlib.md5(f"{source_file}_{index}".encode("utf-8")).hexdigest()[:6]
    return f"{clean_stem}_c{index:03d}_{hash_suffix}"


def chunk_pages(pages: list[dict], chunk_size: int = 400, overlap: int = 75) -> list[dict]:
    """Take page dicts and turn each page's text into one or more chunk dicts,
    carrying forward source metadata."""
    all_chunks = []
    chunk_counter = 0

    for page in pages:
        text = page.get("text", "").strip()
        if not text:
            continue

        pieces = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        for i, piece in enumerate(pieces):
            chunk_counter += 1
            source_file = page.get("source_file", "unknown")
            chunk_id = _generate_chunk_id(source_file, chunk_counter)

            chunk_dict = {
                "chunk_id": chunk_id,
                "text": piece,
                "source_file": source_file,
                "source_type": page.get("source_type", "unknown"),
                "page": page.get("page"),
                "chapter": page.get("chapter"),
                "section": page.get("section"),
                "title": page.get("title"),
                "has_plate": page.get("has_plate", False),
                "has_ocr": page.get("has_ocr", False),
<<<<<<< HEAD
                "wikilinks": page.get("wikilinks"),  # list[str] or None -- wiki pages only
                "infobox": page.get("infobox"),       # dict or None -- wiki pages only
=======
>>>>>>> aeb2852b64774d175569b8a8f8fdafea56a6bf0a
                "word_count": len(piece.split()),
                "char_count": len(piece),
            }
            all_chunks.append(chunk_dict)

    return all_chunks


def chunk_chronicles_by_chapter(pages: list[dict], chunk_size: int = 400, overlap: int = 75) -> list[dict]:
    """Group pages by chapter per document first, then chunk chapters to keep
    narrative context intact."""
    by_doc = defaultdict(list)
    for p in pages:
        by_doc[p["source_file"]].append(p)

    all_chunks = []
    chunk_counter = 0

    for source_file, doc_pages in by_doc.items():
        doc_pages.sort(key=lambda p: p.get("page") or 0)
        
        # Group pages into chapter blocks
        chapters = defaultdict(list)
        current_chapter = "(front matter)"
        
        for p in doc_pages:
            text = p.get("text", "")
            match = CHAPTER_PATTERN.search(text)
            if match:
                current_chapter = match.group(1).strip()
            chapters[current_chapter].append((p.get("page"), text))

        for ch_title, page_tuples in chapters.items():
            combined_text = "\n\n".join(t for _, t in page_tuples)
            start_page = page_tuples[0][0] if page_tuples else None
            end_page = page_tuples[-1][0] if page_tuples else None
            page_range = f"{start_page}-{end_page}" if start_page != end_page else f"{start_page}"

            pieces = chunk_text(combined_text, chunk_size=chunk_size, overlap=overlap)
            for i, piece in enumerate(pieces):
                chunk_counter += 1
                chunk_id = _generate_chunk_id(source_file, chunk_counter)

                # Prepend chapter context header if not already present in chunk
                header_prefix = f"[{Path(source_file).stem} | {ch_title}]\n\n"
                full_chunk_text = header_prefix + piece

                all_chunks.append({
                    "chunk_id": chunk_id,
                    "text": full_chunk_text,
                    "source_file": source_file,
                    "source_type": "chronicles",
                    "page": page_range,
                    "chapter": ch_title,
                    "section": None,
                    "title": Path(source_file).stem.replace("_", " ").title(),
                    "has_plate": False,
                    "has_ocr": any(p.get("has_ocr", False) for p in doc_pages),
                    "word_count": len(full_chunk_text.split()),
                    "char_count": len(full_chunk_text),
                })

    return all_chunks


<<<<<<< HEAD
def process_and_save_all_chunks(extracted_dir: str = None, output_file: str = None) -> list[dict]:
    """Read extracted JSON files for all folders, chunk them intelligently, and save to chunks.json."""
    extracted_dir = extracted_dir or str(REPO_ROOT / "data" / "extracted")
    output_file = output_file or str(REPO_ROOT / "data" / "extracted" / "chunks.json")
=======
def process_and_save_all_chunks(extracted_dir: str = "data/extracted", output_file: str = "data/extracted/chunks.json") -> list[dict]:
    """Read extracted JSON files for all folders, chunk them intelligently, and save to chunks.json."""
>>>>>>> aeb2852b64774d175569b8a8f8fdafea56a6bf0a
    extracted_path = Path(extracted_dir)
    all_chunks = []

    for json_file in extracted_path.glob("*.json"):
        if json_file.name.startswith("_") or json_file.name in {"chunks.json", "chronicles_by_chapter.json"}:
            continue

        with open(json_file, encoding="utf-8") as f:
            pages = json.load(f)

        category = json_file.stem
        print(f"Chunking {category} ({len(pages)} entries/pages)...")

        if category == "chronicles":
            category_chunks = chunk_chronicles_by_chapter(pages)
        else:
            category_chunks = chunk_pages(pages)

        print(f"  -> Generated {len(category_chunks)} chunks for {category}")
        all_chunks.extend(category_chunks)

    out_p = Path(output_file)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"\nTotal chunks across archive: {len(all_chunks)} saved to {out_p}")
    return all_chunks


if __name__ == "__main__":
    process_and_save_all_chunks()

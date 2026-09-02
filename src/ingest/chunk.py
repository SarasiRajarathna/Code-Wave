"""
chunk.py

Splits the text you got from loaders.py into smaller overlapping pieces
("chunks") that are the right size to embed and retrieve individually.

Why chunk at all? A whole novel chapter is too big and too unfocused to
embed as one vector -- the embedding would be a blurry average of everything
in it, and retrieval would struggle to find the one relevant paragraph.
Chunking breaks it into pieces small enough that each one is "about" one
specific thing.

Why overlap? If a sentence describing something important gets cut exactly
in half by a chunk boundary, both halves lose meaning. A bit of overlap
(chunk N ends with the same text chunk N+1 starts with) means important
info near a boundary usually survives intact in at least one chunk.
"""


def chunk_text(text: str, chunk_size: int = 700, overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks, measured in words (a simple stand-in
    for tokens -- good enough to start with; you can swap in a real tokenizer
    like tiktoken later if you want exact token counts for the embedding API).

    chunk_size: target words per chunk
    overlap: words repeated between consecutive chunks
    """
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        if end >= len(words):
            break
        start = end - overlap  # step back by the overlap amount

    return chunks


def chunk_pages(pages: list[dict], chunk_size: int = 700, overlap: int = 100) -> list[dict]:
    """Take the list of page dicts from loaders.py and turn each page's text
    into one or more chunk dicts, carrying the source metadata forward onto
    every chunk. This is the list you'll hand to the embedding step.

    Output shape, one dict per chunk:
        {
            "text": "...",
            "source_file": "...",
            "source_type": "codex",
            "page": 3,
            "chunk_index": 0,   # which chunk this is within its page/doc
        }
    """
    all_chunks = []
    for page in pages:
        pieces = chunk_text(page["text"], chunk_size=chunk_size, overlap=overlap)
        for i, piece in enumerate(pieces):
            all_chunks.append({
                "text": piece,
                "source_file": page["source_file"],
                "source_type": page["source_type"],
                "page": page["page"],
                "chunk_index": i,
            })
    return all_chunks

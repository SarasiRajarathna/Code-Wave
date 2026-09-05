"""
bm25_search.py

Lexical / Keyword-based BM25 retrieval over the Ashen Era Archive chunks.
Ensures exact entity names (e.g. "Halvard Crowhurst", "Ederon Fellgard", "House Morvain"),
numbers (e.g. "356 AS", "3,695", "46"), and specific nouns are never missed by dense vector search alone.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional


def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase words/numbers, stripping punctuation except internal hyphens."""
    return re.findall(r"\b[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)?\b", text.lower())


class AshenBM25Retriever:
    """BM25 retrieval engine over Ashen Era Archive chunks."""

    def __init__(self, chunks_path: str = "data/extracted/chunks.json"):
        self.chunks_path = Path(chunks_path)
        self.chunks: List[Dict[str, Any]] = []
        self.corpus_tokens: List[List[str]] = []
        self.bm25 = None
        self._load_and_index()

    def _load_and_index(self):
        if not self.chunks_path.exists():
            raise FileNotFoundError(f"Chunks file not found at {self.chunks_path}")

        with open(self.chunks_path, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)

        print(f"[BM25] Indexing {len(self.chunks)} chunks for keyword search...")
        self.corpus_tokens = [tokenize(c.get("text", "")) for c in self.chunks]

        try:
            from rank_bm25 import BM25Okapi
            self.bm25 = BM25Okapi(self.corpus_tokens)
            print(f"[BM25] Successfully built BM25Okapi index over {len(self.chunks)} chunks.")
        except ImportError:
            print("[BM25] Warning: rank-bm25 library not available. Using fallback keyword matcher.")
            self.bm25 = None

    def search(
        self,
        query: str,
        n_results: int = 10,
        source_type_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search chunks using BM25 scoring."""
        query_tokens = tokenize(query)
        if not query_tokens or not self.chunks:
            return []

        if self.bm25:
            scores = self.bm25.get_scores(query_tokens)
            # Pair with chunk index
            indexed_scores = list(enumerate(scores))
        else:
            # Fallback simple keyword count scoring
            q_set = set(query_tokens)
            indexed_scores = []
            for idx, doc_tokens in enumerate(self.corpus_tokens):
                score = sum(1 for t in doc_tokens if t in q_set)
                indexed_scores.append((idx, float(score)))

        # Sort descending by score
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in indexed_scores:
            if score <= 0:
                break
            chunk = self.chunks[idx]

            # Apply filter if provided
            if source_type_filter and chunk.get("source_type") != source_type_filter:
                continue

            results.append({
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "metadata": {
                    "source_file": chunk.get("source_file"),
                    "source_type": chunk.get("source_type"),
                    "page": chunk.get("page"),
                    "chapter": chunk.get("chapter"),
                    "title": chunk.get("title"),
                    "has_plate": chunk.get("has_plate", False),
                    "has_ocr": chunk.get("has_ocr", False),
                    "word_count": chunk.get("word_count", 0),
                },
                "bm25_score": float(score),
            })

            if len(results) >= n_results:
                break

        return results

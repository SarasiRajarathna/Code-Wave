<<<<<<< HEAD
"""Forwarding wrapper to src/ingest/test_vector_db.py"""
import sys
from pathlib import Path
import argparse

src_dir = Path(__file__).resolve().parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from ingest.test_vector_db import test_queries
=======
import sys
from pathlib import Path

src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

workspace_root = src_dir.parent

import argparse
from ingest.embeddings import get_embedding_model
from db.vector_store import AshenVectorStore


SAMPLE_QUESTIONS = [
    "What is the recorded garrison strength of Greyfell Citadel?",
    "What details are recorded about the Accord of Mournthrone?",
    "What are the properties and history of the Sceptre of Final Winter?",
    "Where is Emberdeep located and what is its significance?",
]


def test_queries(provider: str = "local", top_k: int = 3):
    vector_store_dir = str(workspace_root / "data" / "vector_store")
    print("Initializing embedding model...")
    embedder = get_embedding_model(provider=provider)

    print("Connecting to ChromaDB vector store...")
    vector_store = AshenVectorStore(persist_directory=vector_store_dir)
    print(f"Vector Store contains {vector_store.count()} indexed chunks.\n")

    for q in SAMPLE_QUESTIONS:
        print("=" * 70)
        print(f"QUERY: {q}")
        print("=" * 70)

        results = vector_store.search(q, embedding_model=embedder, n_results=top_k)

        for i, match in enumerate(results, start=1):
            meta = match["metadata"]
            print(f"[{i}] Similarity: {match['similarity_score']} | Source: {meta.get('source_type')} | File: {meta.get('source_file')} | Page: {meta.get('page')}")
            snippet = match['text'][:250].replace('\n', ' ')
            print(f"    Snippet: {snippet}...\n")

>>>>>>> aeb2852b64774d175569b8a8f8fdafea56a6bf0a

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Vector DB Search")
    parser.add_argument("--provider", type=str, default="local", choices=["local", "voyage"])
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    test_queries(provider=args.provider, top_k=args.top_k)

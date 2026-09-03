"""
test_vector_db.py

Query testing script to verify vector database search quality and metadata retrieval.
"""

import sys
sys.path.insert(0, "src")

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
    print("Initializing embedding model...")
    embedder = get_embedding_model(provider=provider)

    print("Connecting to ChromaDB vector store...")
    vector_store = AshenVectorStore(persist_directory="data/vector_store")
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Vector DB Search")
    parser.add_argument("--provider", type=str, default="local", choices=["local", "voyage"])
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    test_queries(provider=args.provider, top_k=args.top_k)

"""
run_vector_ingest.py

Main pipeline script for Member 1:
1. Loads extracted archive files and chunks them.
2. Generates embeddings for every chunk.
3. Populates the ChromaDB vector database.
"""

import sys
sys.path.insert(0, "src")

import json
import argparse
from pathlib import Path
from ingest.chunk import process_and_save_all_chunks
from ingest.embeddings import get_embedding_model
from db.vector_store import AshenVectorStore


def main():
    parser = argparse.ArgumentParser(description="Ingest Ashen Era Archive into Vector Database")
    parser.add_argument("--provider", type=str, default="local", choices=["local", "voyage"], help="Embedding provider (local or voyage)")
    parser.add_argument("--model", type=str, default=None, help="Custom embedding model name")
    parser.add_argument("--chunks-file", type=str, default="data/extracted/chunks.json", help="Path to chunks JSON")
    args = parser.parse_args()

    chunks_path = Path(args.chunks_file)
    if not chunks_path.exists():
        print(f"Chunks file {chunks_path} not found. Running chunker...")
        chunks = process_and_save_all_chunks(output_file=str(chunks_path))
    else:
        print(f"Loading existing chunks from {chunks_path}...")
        with open(chunks_path, encoding="utf-8") as f:
            chunks = json.load(f)

    print(f"Total chunks to embed: {len(chunks)}")

    # Initialize embedding model
    embedder = get_embedding_model(provider=args.provider, model_name=args.model)

    # Extract raw texts for embedding
    texts = [c["text"] for c in chunks]

    # Generate embeddings
    print("Generating embeddings for all chunks...")
    embeddings = embedder.embed_documents(texts)
    print(f"Successfully generated {len(embeddings)} embeddings.")

    # Initialize Vector Store & Populate
    vector_store = AshenVectorStore(persist_directory="data/vector_store")
    vector_store.add_chunks(chunks, embeddings)

    # Summary by source_type
    counts_by_type = {}
    for c in chunks:
        stype = c.get("source_type", "unknown")
        counts_by_type[stype] = counts_by_type.get(stype, 0) + 1

    print("\n================ INGESTION COMPLETE ================")
    print(f"Total Chunks Stored: {vector_store.count()}")
    print("Chunks breakdown by archive folder:")
    for stype, count in counts_by_type.items():
        print(f"  - {stype}: {count} chunks")
    print("====================================================\n")


if __name__ == "__main__":
    main()

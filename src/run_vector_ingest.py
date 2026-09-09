<<<<<<< HEAD
"""Forwarding wrapper to src/ingest/run_vector_ingest.py"""
import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from ingest.run_vector_ingest import main
=======
import sys
from pathlib import Path

src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

workspace_root = src_dir.parent

import json
import argparse
from ingest.chunk import process_and_save_all_chunks
from ingest.embeddings import get_embedding_model
from db.vector_store import AshenVectorStore


def main():
    default_chunks = str(workspace_root / "data" / "extracted" / "chunks.json")
    default_vector_store = str(workspace_root / "data" / "vector_store")

    parser = argparse.ArgumentParser(description="Ingest Ashen Era Archive into Vector Database")
    parser.add_argument("--provider", type=str, default="local", choices=["local", "voyage"], help="Embedding provider (local or voyage)")
    parser.add_argument("--model", type=str, default=None, help="Custom embedding model name")
    parser.add_argument("--chunks-file", type=str, default=default_chunks, help="Path to chunks JSON")
    parser.add_argument("--vector-store-dir", type=str, default=default_vector_store, help="Path to vector store directory")
    args = parser.parse_args()

    chunks_path = Path(args.chunks_file)
    extracted_dir = str(workspace_root / "data" / "extracted")
    
    if not chunks_path.exists():
        print(f"Chunks file {chunks_path} not found. Running chunker...")
        chunks = process_and_save_all_chunks(extracted_dir=extracted_dir, output_file=str(chunks_path))
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
    vector_store = AshenVectorStore(persist_directory=args.vector_store_dir)
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

>>>>>>> aeb2852b64774d175569b8a8f8fdafea56a6bf0a

if __name__ == "__main__":
    main()

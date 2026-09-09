"""
vector_store.py

ChromaDB persistent vector store manager for the Ashen Era Archive.
Handles chunk storage, metadata indexing, and similarity search queries.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
<<<<<<< HEAD
import json
import chromadb
from chromadb.config import Settings

_REPO_ROOT = Path(__file__).resolve().parents[2]  # this file lives at src/db/vector_store.py


class AshenVectorStore:
    """Vector database interface wrapping ChromaDB."""
    def __init__(self, persist_directory: Optional[str] = None, collection_name: str = "ashen_era_archive"):
        if persist_directory is not None:
            self.persist_directory = Path(persist_directory)
        else:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.persist_directory = base_dir / "data" / "vector_store"
        
=======
import chromadb
from chromadb.config import Settings


class AshenVectorStore:
    """Vector database interface wrapping ChromaDB."""
    def __init__(self, persist_directory: str = "data/vector_store", collection_name: str = "ashen_era_archive"):
        self.persist_directory = Path(persist_directory)
>>>>>>> aeb2852b64774d175569b8a8f8fdafea56a6bf0a
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name

        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]], batch_size: int = 500):
        """Insert chunks and their corresponding embeddings into ChromaDB in batches."""
        if len(chunks) != len(embeddings):
            raise ValueError(f"Mismatch between chunks count ({len(chunks)}) and embeddings count ({len(embeddings)})")

        total = len(chunks)
        print(f"Indexing {total} chunks into ChromaDB collection '{self.collection_name}'...")

        for i in range(0, total, batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size]

            ids = [c["chunk_id"] for c in batch_chunks]
            documents = [c["text"] for c in batch_chunks]
            metadatas = []

            for c in batch_chunks:
<<<<<<< HEAD
                wikilinks = c.get("wikilinks") or []
                infobox = c.get("infobox") or {}
=======
>>>>>>> aeb2852b64774d175569b8a8f8fdafea56a6bf0a
                meta = {
                    "source_file": str(c.get("source_file", "")),
                    "source_type": str(c.get("source_type", "")),
                    "page": str(c.get("page", "") if c.get("page") is not None else ""),
                    "chapter": str(c.get("chapter", "") if c.get("chapter") is not None else ""),
                    "title": str(c.get("title", "") if c.get("title") is not None else ""),
                    "has_plate": bool(c.get("has_plate", False)),
                    "has_ocr": bool(c.get("has_ocr", False)),
                    "word_count": int(c.get("word_count", 0)),
<<<<<<< HEAD
                    # Chroma metadata values must be str/int/float/bool --
                    # lists and dicts aren't accepted, so wikilinks (a list)
                    # is comma-joined and infobox (a dict) is JSON-encoded.
                    # Both come back out with .split(", ") / json.loads()
                    # on the retrieval side.
                    "wikilinks": ", ".join(wikilinks) if wikilinks else "",
                    "infobox": json.dumps(infobox) if infobox else "",
=======
>>>>>>> aeb2852b64774d175569b8a8f8fdafea56a6bf0a
                }
                metadatas.append(meta)

            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=batch_embeddings,
                metadatas=metadatas
            )
            print(f"  Indexed batch {i // batch_size + 1}/{(total + batch_size - 1) // batch_size}")

        print(f"Successfully indexed {self.count()} total documents.")

    def search_by_embedding(self, query_embedding: List[float], n_results: int = 5, where_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Query vector database using a pre-computed query embedding vector."""
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"]
        }
        if where_filter:
            kwargs["where"] = where_filter

        results = self.collection.query(**kwargs)
        matches = []

        if results and results.get("ids") and results["ids"][0]:
            ids = results["ids"][0]
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0]

            for idx, doc, meta, dist in zip(ids, docs, metas, distances):
                matches.append({
                    "chunk_id": idx,
                    "text": doc,
                    "metadata": meta,
                    "distance": dist,
                    "similarity_score": round(1.0 - dist, 4) if dist <= 1.0 else round(1.0 / (1.0 + dist), 4)
                })

        return matches

    def search(self, query_text: str, embedding_model, n_results: int = 5, where_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Convenience method to query using raw query string and embedding model instance."""
        query_emb = embedding_model.embed_query(query_text)
        return self.search_by_embedding(query_emb, n_results=n_results, where_filter=where_filter)

    def count(self) -> int:
        """Return total number of items stored in the collection."""
        return self.collection.count()

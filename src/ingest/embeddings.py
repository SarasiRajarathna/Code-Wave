"""
embeddings.py

Provides unified embedding generation interface supporting both local sentence-transformers
models and Voyage AI API embeddings.
"""

import os
import time
from typing import List, Optional


class BaseEmbeddingModel:
    """Base interface for embedding models."""
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    def embed_query(self, text: str) -> List[float]:
        raise NotImplementedError


class LocalEmbeddingModel(BaseEmbeddingModel):
    """Local embedding generator using SentenceTransformers."""
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        print(f"Loading local embedding model: {model_name}...")
        try:
            self.model = SentenceTransformer(model_name, local_files_only=True)
        except Exception:
            self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def embed_documents(self, texts: List[str], batch_size: int = 64) -> List[List[float]]:
        embeddings = self.model.encode(texts, batch_size=batch_size, show_progress_bar=False)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        embedding = self.model.encode([text], show_progress_bar=False)[0]
        return embedding.tolist()


class VoyageEmbeddingModel(BaseEmbeddingModel):
    """Remote embedding generator using Voyage AI API."""
    def __init__(self, api_key: Optional[str] = None, model_name: str = "voyage-4-lite"):
        import voyageai
        self.api_key = api_key or os.getenv("VOYAGE_API_KEY")
        if not self.api_key:
            raise ValueError("VOYAGE_API_KEY environment variable or parameter is required.")
        self.model_name = model_name
        self.client = voyageai.Client(api_key=self.api_key)

    def embed_documents(self, texts: List[str], batch_size: int = 128) -> List[List[float]]:
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            retry = 0
            while retry < 5:
                try:
                    result = self.client.embed(batch, model=self.model_name, input_type="document")
                    all_embeddings.extend(result.embeddings)
                    break
                except Exception as e:
                    retry += 1
                    wait_time = 2 ** retry
                    print(f"Voyage AI API rate limit/error ({e}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        result = self.client.embed([text], model=self.model_name, input_type="query")
        return result.embeddings[0]


def get_embedding_model(provider: str = "local", model_name: Optional[str] = None) -> BaseEmbeddingModel:
    """Factory to instantiate the configured embedding provider."""
    provider = provider.lower()
    if provider == "voyage":
        model_name = model_name or "voyage-4-lite"
        return VoyageEmbeddingModel(model_name=model_name)
    else:
        model_name = model_name or "sentence-transformers/all-MiniLM-L6-v2"
        return LocalEmbeddingModel(model_name=model_name)

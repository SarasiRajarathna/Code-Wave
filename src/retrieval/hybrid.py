"""
hybrid.py

Unified Hybrid Retriever combining:
1. Dense Semantic Vector Search (ChromaDB)
2. Sparse Lexical Keyword Search (BM25)
Merged via Reciprocal Rank Fusion (RRF).
"""

from typing import List, Dict, Any, Optional
from db.vector_store import AshenVectorStore
from ingest.embeddings import BaseEmbeddingModel, get_embedding_model
from retrieval.bm25_search import AshenBM25Retriever
from retrieval.reranker import SemanticReranker


class HybridRetriever:
    """Combines vector similarity search with BM25 keyword matching via RRF and Semantic Reranking."""

    def __init__(
        self,
        vector_store: Optional[AshenVectorStore] = None,
        bm25_retriever: Optional[AshenBM25Retriever] = None,
        embedding_model: Optional[BaseEmbeddingModel] = None,
        rrf_k: int = 60,
        kg: Optional[Any] = None,
    ):
        self.vector_store = vector_store or AshenVectorStore()
        self.bm25 = bm25_retriever or AshenBM25Retriever()
        self.embedding_model = embedding_model or get_embedding_model(provider="local")
        self.rrf_k = rrf_k
        self.reranker = SemanticReranker(embedding_model=self.embedding_model)
        self.kg = kg

    def search(
        self,
        query: str,
        top_k: int = 5,
        dense_weight: float = 0.5,
        bm25_weight: float = 0.5,
        source_type_filter: Optional[str] = None,
        rerank: bool = True,
    ) -> List[Dict[str, Any]]:
        """Execute hybrid search using Reciprocal Rank Fusion."""
        search_query = query
        if self.kg:
            for alias, canonical in self.kg.alias_map.items():
                if len(alias) >= 5 and alias in query.lower() and canonical.lower() not in query.lower():
                    search_query = f"{query} {canonical}"
                    break

        # 1. Fetch dense vector results
        where_filter = {"source_type": source_type_filter} if source_type_filter else None
        try:
            dense_results = self.vector_store.search(
                query_text=search_query,
                embedding_model=self.embedding_model,
                n_results=top_k * 2,
                where_filter=where_filter,
            )
        except Exception as e:
            print(f"Warning: Vector search encountered issue ({e}). Relying on BM25.")
            dense_results = []

        # 2. Fetch BM25 results
        bm25_results = self.bm25.search(
            query=query,
            n_results=top_k * 2,
            source_type_filter=source_type_filter,
        )

        # 3. Reciprocal Rank Fusion (RRF)
        # score(doc) = sum( weight / (k + rank) )
        doc_map: Dict[str, Dict[str, Any]] = {}
        rrf_scores: Dict[str, float] = {}

        # Dense ranking
        for rank, item in enumerate(dense_results, start=1):
            cid = item["chunk_id"]
            if cid not in doc_map:
                doc_map[cid] = item
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (dense_weight / (self.rrf_k + rank))

        # BM25 ranking
        for rank, item in enumerate(bm25_results, start=1):
            cid = item["chunk_id"]
            if cid not in doc_map:
                doc_map[cid] = item
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (bm25_weight / (self.rrf_k + rank))

        # Sort merged documents by combined RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        pool_size = max(top_k * 2, 10)
        rrf_candidates = []
        for cid in sorted_ids[:pool_size]:
            entry = doc_map[cid].copy()
            entry["hybrid_score"] = round(rrf_scores[cid], 6)
            entry["rrf_score"] = round(rrf_scores[cid], 6)
            rrf_candidates.append(entry)

        # 4. Contextual Semantic Reranking
        if rerank and self.reranker:
            return self.reranker.rerank(query, rrf_candidates, top_k=top_k)

        return rrf_candidates[:top_k]

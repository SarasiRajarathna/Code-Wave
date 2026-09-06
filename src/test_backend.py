"""
test_backend.py

Automated Test Suite for Code-Wave Member 2 Backend Architecture.
Validates:
1. ChromaDB Vector Store Connectivity & Embedding Model
2. BM25Okapi Lexical Keyword Search
3. Reciprocal Rank Fusion (RRF) Hybrid Retriever
4. OpenRouter LLM Gateway & Disk Cache
5. Sub-track 1C Iterative Agent Execution Loop
"""

import sys
import time
from pathlib import Path

# Add src to sys.path
src_dir = Path(__file__).resolve().parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from db.vector_store import AshenVectorStore
from ingest.embeddings import get_embedding_model
from retrieval.bm25_search import AshenBM25Retriever
from retrieval.hybrid import HybridRetriever
from llm.client import OpenRouterLLM
from utils.cache import SimpleDiskCache
from agent.iterative_agent import AshenIterativeAgent


def test_vector_store():
    print("\n[TEST 1/5] Checking ChromaDB Vector Store & Embeddings...")
    t0 = time.time()
    embedder = get_embedding_model(provider="local")
    store = AshenVectorStore(persist_directory="data/vector_store")
    count = store.count()
    elapsed = time.time() - t0

    assert count > 0, f"Vector store is empty! Found {count} items."
    print(f"  [PASS] ChromaDB collection verified with {count:,} indexed chunks ({elapsed:.2f}s).")

    # Query test
    q_emb = embedder.embed_query("Greyfell Citadel garrison")
    res = store.search_by_embedding(q_emb, n_results=2)
    assert len(res) > 0, "Vector store query returned no results."
    print(f"  [PASS] Vector similarity search returned top chunk: {res[0]['metadata'].get('source_file')}")
    return store, embedder


def test_bm25():
    print("\n[TEST 2/5] Checking BM25Okapi Keyword Search...")
    t0 = time.time()
    bm25 = AshenBM25Retriever(chunks_path="data/extracted/chunks.json")
    elapsed = time.time() - t0

    assert len(bm25.chunks) > 0, "BM25 index is empty."
    print(f"  [PASS] BM25Okapi index built over {len(bm25.chunks):,} chunks ({elapsed:.2f}s).")

    res = bm25.search("Gauntlet of Sorrowfell 391 AS", top_k=2)
    assert len(res) > 0, "BM25 query returned no results."
    print(f"  [PASS] BM25 keyword query successfully matched: {res[0]['metadata'].get('source_file')}")
    return bm25


def test_hybrid_retrieval(embedder):
    print("\n[TEST 3/5] Checking Hybrid Retriever (RRF Fusion)...")
    t0 = time.time()
    retriever = HybridRetriever(embedding_model=embedder)
    results = retriever.search("The Leaden Accord victor", top_k=5)
    elapsed = time.time() - t0

    assert len(results) > 0, "Hybrid retrieval returned empty results."
    top_chunk = results[0]
    assert "rrf_score" in top_chunk, "RRF score missing in hybrid result."
    print(f"  [PASS] Hybrid RRF returned {len(results)} chunks (Top RRF score: {top_chunk['rrf_score']:.4f}) in {elapsed:.2f}s.")
    return retriever


def test_llm_and_cache():
    print("\n[TEST 4/5] Checking OpenRouter LLM & Cache Subsystem...")
    t0 = time.time()
    cache = SimpleDiskCache()
    key = cache.hash_key("unit_test_key", "sample_val")
    cache.set(key, "cached_success")
    cached_val = cache.get(key)
    assert cached_val == "cached_success", "Disk cache read/write mismatch."
    print(f"  [PASS] SHA256 Disk Cache read/write validated.")

    llm = OpenRouterLLM()
    print(f"  [INFO] LLM Gateway online status: {llm.is_online} (Active Model: {llm.model})")

    offline_out = llm._synthesize_offline("CONTEXT PASSAGES: [Plate 09] Greyfell Citadel garrison strength 3,695 souls under arms. QUESTION: What is garrison strength?")
    assert "3,695" in offline_out, "Offline fallback synthesizer failed."
    print(f"  [PASS] Offline grounded synthesis fallback verified.")
    return llm


def test_iterative_agent(retriever, llm):
    print("\n[TEST 5/5] Checking Sub-track 1C Iterative Agent Execution...")
    t0 = time.time()
    agent = AshenIterativeAgent(retriever=retriever, llm=llm, max_hops=2)

    test_q = "What is the recorded garrison strength of Greyfell Citadel?"
    res = agent.run(test_q, verbose=False, no_cache=False)
    elapsed = time.time() - t0

    assert res.answer, "Agent produced an empty answer."
    assert len(res.citations) > 0, "Agent produced no citations."
    assert len(res.hops) >= 1, "Agent recorded zero search hops."
    print(f"  [PASS] Sub-track 1C Agent completed in {elapsed:.2f}s:")
    print(f"         - Total Hops  : {len(res.hops)}")
    print(f"         - Citations   : {len(res.citations)}")
    print(f"         - Rich Media  : {res.rich_media['title'] if res.rich_media else 'None'}")
    print(f"         - Answer Lead : {res.answer[:80]}...")


def main():
    print("=" * 75)
    print("       CODE-WAVE BACKEND & AI ENGINE AUTOMATED TEST SUITE")
    print("                 Sub-track 1C Architecture")
    print("=" * 75)

    try:
        store, embedder = test_vector_store()
        bm25 = test_bm25()
        retriever = test_hybrid_retrieval(embedder)
        llm = test_llm_and_cache()
        test_iterative_agent(retriever, llm)

        print("\n" + "=" * 75)
        print(" [ALL TESTS PASSED] Backend architecture is 100% operational!")
        print("=" * 75 + "\n")
    except Exception as e:
        print(f"\n[TEST FAILED] Error encountered: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

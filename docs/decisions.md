# Architecture Decision Records (ADR) — Code-Wave

**System:** Ashen Era Archive Intelligent Document Assistant  
**Competition:** SLIIT Codefest 2026 — AI Competition  
**Challenge Sub-track:** Sub-track 1C — *Searching the Way a Human Does*  
**Document Path:** `docs/decisions.md`  
**Status:** Accepted & Implemented  

---

## Overview

This document records the architectural and technical decisions made during the design and implementation of the **Code-Wave** system. Each record follows the Architecture Decision Record (ADR) format, outlining the context, options considered, the decision made, rationales, and associated trade-offs.

---

## Index of Decisions

- [ADR 001: Language & Runtime Selection (Python 3.13)](#adr-001-language--runtime-selection-python-313)
- [ADR 002: Embedded Vector Database Selection (ChromaDB)](#adr-002-embedded-vector-database-selection-chromadb)
- [ADR 003: Dual-Provider Embedding Architecture (Local vs. Voyage AI)](#adr-003-dual-provider-embedding-architecture-local-vs-voyage-ai)
- [ADR 004: Hybrid OCR & Multimodal Plate Graphic Extraction](#adr-004-hybrid-ocr--multimodal-plate-graphic-extraction)
- [ADR 005: PDF-First Document Deduplication Strategy](#adr-005-pdf-first-document-deduplication-strategy)
- [ADR 006: Word-Count Sliding Window & Chapter-Aware Chunking](#adr-006-word-count-sliding-window--chapter-aware-chunking)
- [ADR 007: Explicit Knowledge Graph & Infobox Extraction for Multi-Hop Search](#adr-007-explicit-knowledge-graph--infobox-extraction-for-multi-hop-search)
- [ADR 008: Deterministic Chunk Hashing & Idempotent Indexing](#adr-008-deterministic-chunk-hashing--idempotent-indexing)
- [ADR 009: Offline Pre-Ingestion Quality Verification & Diagnostic Suite](#adr-009-offline-pre-ingestion-quality-verification--diagnostic-suite)

---

## ADR 001: Language & Runtime Selection (Python 3.13)

### Context
The Ashen Era Archive requires high-performance document parsing (PDF, DOCX, Markdown, OCR), computer vision processing, NLP vector embeddings, and persistent similarity indexing. We needed a language with mature libraries across document engineering and AI retrieval.

### Options Considered
1. **Python 3.13 (Selected):** Dominant language for AI/ML with native libraries for PyMuPDF (`fitz`), Tesseract (`pytesseract`), Pillow, HuggingFace (`sentence-transformers`), and ChromaDB.
2. **TypeScript / Node.js:** Fast event loop and strong API server capabilities, but weaker PDF rendering, lower OCR tooling quality, and heavier C++ binding dependencies for local vector embeddings.
3. **Rust / Go:** Superior execution speed and memory safety, but lacking high-level document extraction libraries and requiring excessive boilerplate for rapid competition prototyping.

### Decision
We selected **Python 3.13**.

### Consequences & Trade-Offs
* **Benefits:** Access to first-class libraries (`pymupdf`, `python-docx`, `chromadb`, `sentence-transformers`, `voyageai`); fast iteration and script composability.
* **Trade-Offs:** Slower raw execution speed compared to compiled languages; GIL considerations (mitigated because pipeline steps are I/O and batch-matrix bound).

---

## ADR 002: Embedded Vector Database Selection (ChromaDB)

### Context
The system requires an indexed vector store to persist chunk embeddings, support cosine similarity queries, and allow metadata-filtered lookups. For competition evaluation, the database must run reliably in local environments without requiring complex cloud services or Docker daemons.

### Options Considered
1. **ChromaDB (Selected):** Embedded, persistent vector database (`PersistentClient`) that writes directly to disk (`data/vector_store/`). Supports HNSW indexing with cosine similarity, native metadata filtering, and zero background daemon requirement.
2. **Cloud Vector Stores (Pinecone, Qdrant Cloud, Weaviate Cloud):** High scalability and hosted management, but introduces external network latency, recurring API costs, and failure modes when running offline evaluations.
3. **Self-Hosted Docker Containers (Milvus, Qdrant, Weaviate):** Powerful features, but requires Docker runtime on evaluation machines, violating portability and ease-of-setup requirements.
4. **In-Memory FAISS Index with Pickle:** Extremely fast, but lacks native metadata query filtering, schema persistence, and clean serialization abstractions.

### Decision
We selected **ChromaDB** configured with `PersistentClient` and cosine distance space (`hnsw:space: cosine`).

### Consequences & Trade-Offs
* **Benefits:** Zero-dependency installation (`pip install chromadb`); data persists directly in `data/vector_store/`; supports metadata queries (`where_filter`); completely offline-capable.
* **Trade-Offs:** SQLite-backed metadata storage is less performant at massive web scale (millions of chunks), but well within capacity for the Ashen Era Archive (~4.5 MB chunk corpus).

---

## ADR 003: Dual-Provider Embedding Architecture (Local vs. Voyage AI)

### Context
Dense vector retrieval quality is strongly influenced by embedding model capabilities. However, external API keys may not always be available during competition grading, offline reviews, or continuous testing.

### Options Considered
1. **Local-Only Model (`all-MiniLM-L6-v2`):** Fast and free, but has lower semantic density and smaller context window (384 dimensions).
2. **Cloud-Only Model (Voyage AI / OpenAI / Cohere):** High accuracy and domain representation, but requires paid API keys, internet connectivity, and is subject to rate limits.
3. **Dual-Provider Architecture via Factory Pattern (Selected):** Implement an abstract interface `BaseEmbeddingModel` with two concrete providers: `LocalEmbeddingModel` (default) and `VoyageEmbeddingModel`.

### Decision
We implemented a pluggable factory `get_embedding_model(provider="local" | "voyage")` in [`src/ingest/embeddings.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/embeddings.py).

### Consequences & Trade-Offs
* **Benefits:**
  - **Local Mode:** Immediate zero-cost testing, fully deterministic, no API key needed.
  - **Voyage Mode:** Production-grade domain embeddings with built-in exponential backoff (5 retries, $2^{\text{retry}}$ wait) to gracefully absorb rate limits.
* **Trade-Offs:** Must maintain two separate embedding dimensions (384 for MiniLM vs. 1024/1536 for Voyage) and re-index the collection if switching providers.

---

## ADR 004: Hybrid OCR & Multimodal Plate Graphic Extraction

### Context
The Ashen Era Archive is multimodal and heterogeneous:
1. **Scanned Documents (Ephemera):** Unselectable bitmap pages.
2. **Digital Text with Embedded Graphical Plates (Codex PDFs):** Selectable narrative prose surrounding graphical gauge/card diagrams containing numeric garrison and strength figures.
3. **Standard Digital PDFs (Chronicles):** Fully selectable text.

### Options Considered
1. **Universal Blind OCR:** Run full-page OCR across every single page.  
   *Result:* Extremely slow, error-prone on dense digital prose, and destroys original typography.
2. **Text-Only Extraction (`pymupdf.get_text()`):**  
   *Result:* Completely misses scanned documents and drops all numeric values baked into Codex graphic plates.
3. **Hybrid Selective Strategy (Selected):**
   - If selectable page text $< 30$ characters $\rightarrow$ trigger full-page OCR at 200 DPI.
   - For Codex PDFs $\rightarrow$ systematically extract embedded image blocks (`page.get_images()`), OCR each plate individually, evaluate confidence, and inject `[FIGURE PLATE TEXT]` back into the page.

### Decision
We implemented the **Hybrid Selective OCR Strategy** in [`src/ingest/loaders.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/loaders.py), [`src/ingest/processors/ocr.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/processors/ocr.py), and [`src/ingest/processors/codex.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/processors/codex.py).

### Quality Assurance Mechanism
Plate OCR includes word-level confidence filtering ($< 60\%$) and regex digit validation. If a plate lacks digits or falls below threshold, it is flagged with `plate_needs_review=True` rather than silently injecting garbled data.

### Consequences & Trade-Offs
* **Benefits:** 10x faster than full-archive OCR; captures critical numeric figures that standard RAG pipelines miss; flags questionable OCR results for human review.
* **Trade-Offs:** Requires local installation of Tesseract OCR binary (`tesseract.exe`).

---

## ADR 005: PDF-First Document Deduplication Strategy

### Context
In `data/corpus/`, several historical chronicle books exist in duplicate formats: both `.pdf` and `.docx` versions are present in the directory. If both are ingested, identical prose is indexed twice, skewing similarity rankings and consuming redundant vector storage.

### Options Considered
1. **Ingest Both Formats:** Causes duplicate search hits and pollutes Top-K retrieval.
2. **Prefer DOCX:** Fast text extraction, but `.docx` has no native page geometry; `page` metadata becomes `None`.
3. **Prefer PDF (`dedupe_by_basename`) (Selected):** Group files by stem (`f.stem.lower()`). When duplicate stems exist, strictly retain `.pdf` and drop `.docx`.

### Decision
We implemented `dedupe_by_basename()` in [`src/run_ingest.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/run_ingest.py).

### Consequences & Trade-Offs
* **Benefits:** Completely eliminates duplicate vector records; guarantees real physical page numbers (`page: 1, 2, 3...`) for citation traceability and chapter-boundary mapping.
* **Trade-Offs:** Ingestion takes slightly longer to parse PDF structures than reading raw DOCX paragraphs.

---

## ADR 006: Word-Count Sliding Window & Chapter-Aware Chunking

### Context
Document chunking dictates retrieval granularity. Naive token chunking tied to a specific model's tokenizer creates tight coupling, while arbitrary page slicing destroys narrative context across chapter boundaries.

### Options Considered
1. **Fixed Token-Count Chunking:** Requires importing a specific model tokenizer (e.g., HuggingFace or TikToken). If the embedding provider switches, token counts diverge.
2. **Page-by-Page Fixed Slicing:** Keeps page boundaries intact, but splits paragraphs and sentences arbitrarily at page margins.
3. **Word-Count Sliding Window with Chapter Aggregation (Selected):**
   - Standard documents: 400 words target with 75 words overlap ($\approx 500$ tokens), providing model-agnostic boundaries.
   - Chronicles: Group pages by chapter heading regex before chunking, prefix each chunk with `[Chapter: <Title>]`, and track the start-to-end page span.

### Decision
We implemented `chunk_text()`, `chunk_pages()`, and `chunk_chronicles_by_chapter()` in [`src/ingest/chunk.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/chunk.py).

### Consequences & Trade-Offs
* **Benefits:** Narrative continuity is preserved; chapter context is embedded directly in text for retrieval; chunks remain model-agnostic.
* **Trade-Offs:** Slightly variable token lengths depending on language vocabulary density.

---

## ADR 007: Explicit Knowledge Graph & Infobox Extraction for Multi-Hop Search

### Context
Sub-track 1C (*Searching the Way a Human Does*) requires the system to follow clues, cross-references, and multi-hop relationships. In the archive, wiki articles contain rich structural knowledge:
1. `[[Wikilinks]]` linking entities to other encyclopedia entries.
2. Markdown `| Field | Value |` infoboxes containing authoritative factual attributes.

### Options Considered
1. **Flatten All to Plain Text:** Treat wiki pages like generic text documents.  
   *Result:* Wikilink markers (`[[` and `]]`) clutter embedding vectors; relationship links are lost as explicit graph edges.
2. **Explicit Extraction & Schema Enrichment (Selected):**
   - Extract unique `[[Entity]]` names into a dedicated list.
   - Parse markdown infobox tables into key-value dictionaries.
   - Retain both in the intermediate document JSON and chunk metadata.

### Decision
We implemented `extract_wikilinks()`, `extract_infobox()`, and `extract_title()` in [`src/ingest/processors/wiki.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/processors/wiki.py).

### Architectural Impact on Sub-track 1C
When an agent reads an initial wiki chunk, the extracted `[[wikilinks]]` provide a ready-made priority queue of next-hop queries, mimicking how human researchers follow citations.

### Consequences & Trade-Offs
* **Benefits:** Creates a latent knowledge graph inside the chunk corpus; enables targeted deterministic entity jumps.
* **Trade-Offs:** Requires custom regex parsers specific to wiki markdown syntax.

---

## ADR 008: Deterministic Chunk Hashing & Idempotent Indexing

### Context
Pipeline runs must be reproducible. Re-running ingestion or vector database generation should not duplicate chunks or create unstable chunk identifiers.

### Options Considered
1. **Random UUIDs (`uuid.uuid4()`):** Non-deterministic; every ingestion run creates entirely new IDs, forcing complete database wipes on every re-index.
2. **Sequential Integer IDs (`1, 2, 3...`):** Vulnerable to collisions across documents and folders.
3. **Deterministic Content & Source Hashing (Selected):**
   $$\text{chunk\_id} = \text{clean\_stem} + \text{"\_c"} + \text{index}_{03d} + \text{"\_"} + \text{MD5}(\text{source\_file} + \text{"\_"} + \text{index})[:6]$$

### Decision
We implemented `_generate_chunk_id()` in [`src/ingest/chunk.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/chunk.py) and utilized ChromaDB's idempotent `collection.upsert()`.

### Consequences & Trade-Offs
* **Benefits:** Re-running the pipeline updates existing entries without duplicates; chunk IDs encode source file origin directly in their string prefix (e.g., `chronicles_vol1_c014_9a8f2c`).
* **Trade-Offs:** If a document is re-chunked with different parameters, previous IDs must be cleared.

---

## ADR 009: Offline Pre-Ingestion Quality Verification & Diagnostic Suite

### Context
During early pipeline development, initial extractions silently missed edge-case documents (such as low-contrast scans or complex tables), leading to incomplete search indices.

### Options Considered
1. **Rely Solely on End-to-End Search Testing:** Inspect retrieval outputs only after embedding and indexing.  
   *Result:* Extremely difficult to diagnose whether a retrieval miss was caused by poor embedding similarity or upstream extraction failure.
2. **Pre-Ingestion Diagnostic Suite (Selected):** Build dedicated inspection and quality-control utilities that audit intermediate JSON files before running expensive embedding and vector indexing passes.

### Decision
We created a modular suite of verification scripts in `src/`:
* `check_extraction.py`: Flags extracted pages with $< 50$ characters and writes `_needs_ocr.json`.
* `check_plates.py`: Identifies codex pages flagged with `plate_needs_review=True`.
* `inspect_flagged.py`: Dumps full text of flagged pages for rapid visual debugging.
* `spot_check_emberdeep.py`: Asserts capture of key named entities across gazetteer files.

### Consequences & Trade-Offs
* **Benefits:** Guarantees data integrity before computing vector embeddings; saves computational resources and API credits; establishes a clear audit trail.
* **Trade-Offs:** Additional utility scripts to maintain alongside the core ingestion code.

---

## Summary Matrix of Architectural Decisions

| ADR | Topic | Decision | Primary Driver |
|---|---|---|---|
| **001** | Language | Python 3.13 | Document parsing & AI ecosystem compatibility |
| **002** | Vector DB | ChromaDB (`PersistentClient`) | Local persistence, zero cloud daemon, metadata filtering |
| **003** | Embeddings | Dual: Local MiniLM + Voyage AI | Zero-cost offline evaluation with cloud scaling option |
| **004** | OCR Strategy | Hybrid (Threshold + Plate OCR) | Preserves digital fidelity while capturing embedded plate metrics |
| **005** | Deduplication | Prefer PDF over DOCX | Eliminates duplicates; preserves physical page numbers |
| **006** | Chunking | Word-count sliding + Chapter-aware | Model-agnostic boundaries; preserves narrative context |
| **007** | Graph Extraction | Parse `[[Wikilinks]]` & Infoboxes | Fuels Sub-track 1C multi-hop reasoning and next-hop selection |
| **008** | Chunk IDs | Deterministic MD5 Hashing | Idempotent upserts; prevents index pollution |
| **009** | Quality Tools | Pre-Ingestion Diagnostic Suite | Catches extraction defects prior to expensive vector indexing |

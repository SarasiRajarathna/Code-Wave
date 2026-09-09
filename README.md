# Code-Wave — Ashen Era Archive Intelligent Document Assistant

An AI system for processing, OCR-extracting, chunking, embedding, and querying the **Ashen Era Archive** (PDFs, DOCX, Markdown, scanned documents, and figure plate images).

---

## 📁 Directory Structure

```
Code-Wave/
├── .env.example             # Environment template for OpenRouter / Voyage keys
├── requirements.txt         # Dependencies (pymupdf, chromadb, rank-bm25, openai, etc.)
├── data/
│   ├── corpus/              # Raw Ashen Era Archive (PDFs, DOCX, MD, images)
│   ├── extracted/           # Extracted JSON files & chunks.json (1,737 chunks)
│   └── vector_store/        # Persistent ChromaDB vector database (1,737 embeddings)
├── docs/                    # Architecture, design decisions (ADRs), and limitations
├── ai_usage/                # AI usage disclosure and session logs
├── src/
│   ├── db/                  # ChromaDB vector store wrapper
│   │   └── vector_store.py
│   ├── ingest/              # Loaders, chunkers, processors & embeddings
│   │   ├── processors/      # Codex plate OCR, Wiki cleaner, full-page OCR
│   │   ├── chunk.py
│   │   ├── embeddings.py
│   │   └── loaders.py
│   ├── retrieval/           # Hybrid retrieval subsystem
│   │   ├── bm25_search.py   # Lexical BM25 keyword search over chunks
│   │   └── hybrid.py        # Reciprocal Rank Fusion (RRF) Dense + BM25
│   ├── llm/                 # LLM connectivity & prompt engineering
│   │   └── client.py        # OpenRouter client with exponential backoff & caching
│   ├── agent/               # Sub-track 1C & 1A Reasoning Agent
│   │   ├── iterative_agent.py # Multi-hop human-like research loop
│   │   └── rich_media.py    # Figure plate & heraldic banner resolver (1A)
│   ├── utils/
│   │   └── cache.py         # Deterministic disk cache for frugal token usage
│   ├── query.py             # CLI runner (Single query, interactive chat, benchmark eval)
│   ├── run_ingest.py        # Ingestion & OCR pipeline
│   ├── run_vector_ingest.py # Chunking, embedding & vector DB loading
│   └── test_vector_db.py    # Query verification script
```

---

## 🚀 How to Run

### 1. Install Dependencies
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API Keys (Optional)
Copy `.env.example` to `.env` to configure OpenRouter (for conversational LLM answers) and Voyage AI:
```bash
cp .env.example .env
```
*(Note: If no API key is provided, the system automatically runs in offline grounded synthesis mode using local embeddings and heuristic multi-hop reasoning.)*

### 3. Generate Chunks, Embeddings & Load Vector DB
Because `chunks.json` (1,737 pre-extracted chunks) is already committed in `data/extracted/`, populate ChromaDB directly:
```bash
# Using local embedding model (sentence-transformers/all-MiniLM-L6-v2) - 100% offline & free:
python src/run_vector_ingest.py --provider local

# Using Voyage AI (requires VOYAGE_API_KEY):
python src/run_vector_ingest.py --provider voyage
```

### 4. Launch the Interactive Web Explorer (Recommended)
Launch the primary showcase interface (Dark-Fantasy Web Explorer with Sub-track 1C Human Investigation Trail & Sub-track 1A Rich Figure Plates):
```bash
python src/api.py
```
* **Interactive Web UI:** Open [http://localhost:8000/app](http://localhost:8000/app) in any modern browser.
* **Interactive API Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Features in UI:**
  * 🧠 **Sub-track 1C:** Real-time multi-hop search, query decomposition, gap detection loop, knowledge graph traversal, and archivist critic.
  * 🖼️ **Sub-track 1A:** Interactive Figure Plate cards with hover zoom preview and fullscreen Lightbox modal.
  * 🛡️ **Zero-Hallucination:** Grounding verification badges and offline canonical synthesis.

---

## 🧪 Verification & Testing

Run the full automated test suite verifying all 8 subsystems (Vector store, BM25, Hybrid RRF fusion, REST endpoints, SSE streaming, multi-turn memory, and live competition benchmarks):
```bash
# Backend unit & subsystem test:
python src/test_backend.py

# Complete FastAPI REST & Benchmark test:
python src/test_api.py
```

---

## 💻 CLI Usage

#### Single Question Execution
```bash
python src/query.py --question "According to the figure plate, what is the recorded garrison strength of Greyfell Citadel?"
```

#### Interactive Terminal Mode
```bash
python src/query.py --interactive
```

#### Automated Benchmark Evaluation
Run automated evaluation against the benchmark competition questions:
```bash
python src/query.py --eval ../Ashen_Era_Archive/Ashen_Era_Archive/sample_questions.json
```
Results are saved directly to `data/evaluation_results.json`.

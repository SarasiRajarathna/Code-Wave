# Code-Wave — Ashen Era Archive Intelligent Document Assistant

An AI system for processing, OCR-extracting, chunking, embedding, and querying the **Ashen Era Archive** (PDFs, DOCX, Markdown, scanned documents, and figure plate images).

---

## 📁 Directory Structure

```
Code-Wave/
├── data/
│   ├── corpus/          # Raw Ashen Era Archive (PDFs, DOCX, MD, images)
│   ├── extracted/       # Extracted JSON files & chunks.json
│   └── vector_store/    # Persistent ChromaDB vector database
├── docs/                # Architecture, design decisions, and limitations
├── src/                 # All Python source code & pipeline scripts
│   ├── db/              # ChromaDB vector store wrapper
│   │   └── vector_store.py
│   ├── ingest/          # Loaders, chunkers, processors & embeddings
│   │   ├── processors/  # Codex plate OCR, Wiki cleaner, full-page OCR
│   │   ├── chunk.py
│   │   ├── embeddings.py
│   │   └── loaders.py
│   ├── run_ingest.py         # 1. Ingestion & OCR pipeline
│   ├── run_vector_ingest.py  # 2. Chunking, embedding & vector DB loading
│   ├── test_vector_db.py     # 3. Query verification script
│   ├── check_extraction.py   # Extraction verification tool
│   ├── check_plates.py       # Plate OCR verification tool
│   ├── group_chapters.py     # Chapter grouping tool
│   ├── inspect_flagged.py    # Flagged page inspector
│   └── spot_check_emberdeep.py
└── requirements.txt
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

### 2. Run Data Ingestion & OCR Pipeline
Extracts text from all corpus documents, performing full-page Tesseract OCR on scanned PDFs and figure plate images:
```bash
python src/run_ingest.py
```

### 3. Generate Chunks, Embeddings & Load Vector DB
Groups text into chapter/section-aware chunks, computes vector embeddings, and stores them in ChromaDB:
```bash
# Using local embedding model (sentence-transformers/all-MiniLM-L6-v2)
python src/run_vector_ingest.py --provider local

# Using Voyage AI (requires VOYAGE_API_KEY environment variable)
python src/run_vector_ingest.py --provider voyage
```

### 4. Query the Vector Database
Test vector similarity search with sample questions:
```bash
python src/test_vector_db.py
```

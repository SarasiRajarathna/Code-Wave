# Project Context & Constraints Specification

**System:** Ashen Era Archive Intelligent Document Assistant (Code-Wave)  
**Competition:** SLIIT Codefest 2026 — AI Competition  
**Challenge Sub-tracks:** Sub-track 1C (*Searching the Way a Human Does*) & Sub-track 1A (*Rich Media Resolution*)  
**Document Path:** `ai_usage/context.md`  
**Purpose:** Master Context Specification Provided to AI Assistants during Development  

---

## 1. Overview & Purpose

This document records the master architectural context, domain knowledge, competition constraints, and coding rules that were supplied to Large Language Models (specifically Anthropic's Claude) throughout the development of **Code-Wave**.

By standardizing and documenting this context, the development team ensured that all AI-assisted code generation, refactoring, and prompt engineering adhered strictly to competition guidelines, avoided hallucinations, and respected the physical constraints of the Ashen Era Archive.

---

## 2. Competition & Track Context

### 2.1 Competition Overview
- **Event:** SLIIT Codefest 2026 AI Competition
- **Core Objective:** Build an intelligent document assistant capable of deep historical document understanding, multimodal extraction, and verifiable question answering over a complex archival repository.

### 2.2 Primary Challenge: Sub-track 1C — *Searching the Way a Human Does*
Traditional RAG systems perform a single vector search, fetch Top-K chunks, and immediately generate an answer. Sub-track 1C mandates an **adaptive, iterative, multi-step search agent** that emulates a human historical researcher:
1. **Search Corpus for Initial Information:** Perform an initial hybrid retrieval based on the core question.
2. **Read & Reason:** Analyze retrieved text for partial facts, referenced entities, and chronological anchors.
3. **Identify Information Gaps:** Explicitly determine what vital details are still missing to form a complete answer.
4. **Decide What to Search for Next:** Formulate targeted follow-up queries using clues discovered in previous results (e.g., following `[[wikilinks]]` or plate references).
5. **Accumulate Evidence Across Steps:** Maintain an epistemic memory of gathered facts across multiple search iterations.
6. **Prevent Cyclic Redundancy:** Avoid searching for the same concepts or re-fetching previously evaluated chunks.
7. **Evaluate Sufficiency & Stop:** Dynamically evaluate if sufficient evidence has been collected to answer reliably, terminating early or stopping at a hard iteration bound ($\le 5$ hops).
8. **Synthesize Grounded Answer:** Produce an authoritative response strictly supported by the accumulated evidence with precise source citations.

### 2.3 Secondary Challenge: Sub-track 1A — *Rich Media & Plate Resolution*
- The archive contains graphical plates, heraldic emblems, and data gauges embedded as images.
- The system must capture numbers, tactical metrics, and visual plate titles that digital PDF text extractors omit.

---

## 3. Domain Archive Context: The Ashen Era Archive

The system operates on a heterogeneous, multimodal archive stored in `data/corpus/` categorized into five distinct collections:

```
data/corpus/
├── chronicles/   # Narrative histories spanning dozens of chapters (PDF & DOCX duplicates)
├── wiki/         # Encyclopedia articles containing [[Entity]] links & Markdown infoboxes
├── codex/        # Technical gazetteers with prose and embedded graphical gauge plates
├── ephemera/     # Historical scanned records, letters, and handwritten notices (scanned PDFs)
└── images/       # Standalone raster plate illustrations (PNG/JPG)
```

### 3.1 Collection Characteristics & Domain Gotchas Provided to AI

| Folder | Format | Unique Characteristics | Engineering Rule Enforced |
|---|---|---|---|
| `chronicles` | `.pdf`, `.docx` | Continuous multi-page historical narratives with chapter titles. Books exist in duplicate formats. | Deduplicate by stem name: **prefer PDF** for physical page numbers. Chunk by chapter to keep narrative context intact. |
| `wiki` | `.md` | Articles define entities, factions, and places. Cross-references are marked with `[[Entity Name]]`. Tables follow markdown `\| Field \| Value \|`. | Extract `[[Wikilinks]]` as explicit graph edges for next-hop searches. Parse infobox tables into clean dictionaries. |
| `codex` | `.pdf` | Gazetteers mixing selectable prose with raster plate images containing numerical troop/garrison stats. | Digital text extractor misses diagram numbers. Extract embedded images (`page.get_images()`) and run Tesseract OCR with digit validation. |
| `ephemera` | `.pdf` (`.scan.pdf`), `.png` | Low-contrast scanned historical letters with near-zero selectable text layer. | If `len(text) < 30` characters, trigger automatic 200 DPI rendering and full-page OCR. |
| `images` | `.png`, `.jpg` | Standalone tactical maps, heraldic devices, and visual plates. | OCR image and synthesize descriptive title from filename stem. |

---

## 4. Technical Constraints & Architectural Boundaries

The following technical boundaries were provided to AI assistants as immutable design constraints:

### 4.1 Programming Language & Dependencies
- **Language:** Python 3.13.
- **Dependency Management:** Minimal, well-maintained libraries specified in `requirements.txt` (`pymupdf`, `python-docx`, `pytesseract`, `pillow`, `chromadb`, `sentence-transformers`, `rank-bm25`, `openai`).
- **Operating Environment:** Must execute seamlessly on Windows workstations with standard local virtual environments (`.venv`).

### 4.2 Local Persistence & Offline First
- **Vector Database:** ChromaDB configured as a local `PersistentClient` targeting `data/vector_store/`. No hosted cloud vector database (e.g. Pinecone) permitted as a mandatory dependency.
- **Offline Capability:** The system must run completely offline using local embedding model `sentence-transformers/all-MiniLM-L6-v2` and deterministic heuristic multi-hop reasoning if external API keys are omitted.
- **Optional Cloud Scaling:** If `VOYAGE_API_KEY` or `OPENROUTER_API_KEY` are provided, the system seamlessly activates Voyage AI embeddings (`voyage-4-lite`) and conversational LLM synthesis with exponential backoff retry.

### 4.3 Chunking & Metric Specifications
- **Chunking Model:** Word-count sliding window (target: 400 words, overlap: 75 words $\approx 500$ tokens).
- **Chunk IDs:** Deterministic MD5 hash combining document stem, sequence counter, and path:
  $$\text{chunk\_id} = \text{clean\_stem} + \text{"\_c"} + \text{index}_{03d} + \text{"\_"} + \text{MD5}(\text{source\_file} + \text{"\_"} + \text{index})[:6]$$
- **Similarity Metric:** Cosine distance space (`hnsw:space: cosine`).

---

## 5. Strict Grounding & Anti-Hallucination Rules

During prompt engineering and LLM client design, the following strict grounding principles were enforced:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CORE GROUNDING DIRECTIVES                       │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Zero Extrapolation: Assertions must be directly cited from chunks.  │
│ 2. Exact Attribution: Every claim must reference file, chapter, page.  │
│ 3. Explicit Ignorance: If a metric is absent, state that it is unrecorded.│
│ 4. Contradiction Flagging: Conflicting dates/headcounts must be exposed│
│    rather than harmonized.                                             │
│ 5. Proof of Absence Rigor: Negative statements must be bounded.       │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Strict Context Adherence:** The LLM must answer exclusively from the provided archival excerpts. Pre-trained world knowledge about real-world history or unrelated fantasy lore must never bleed into answers.
2. **Explicit Uncertainty Handling:** If a question asks for a statistic not present in the archive, the model must state: *"This information is not recorded in the available archive"* rather than guessing.
3. **Historical Contradiction Preservation:** Chroniclers in the Ashen Era Archive sometimes report conflicting dates or troop counts. The system must explicitly present both perspectives rather than arbitrarily picking one.
4. **Pinpointed Citations:** Answers must append granular citations in the format: `[Document Name, Chapter X, Page Y]`.

---

## 6. Development Workflow & Repository Standards

All AI-generated code was required to conform to the following engineering conventions:

1. **Modular Directory Structure:**
   - Ingestion loaders and processors in `src/ingest/`
   - Database operations in `src/db/`
   - Retrieval mechanisms (BM25, Hybrid, Graph) in `src/retrieval/`
   - Iterative multi-hop reasoning in `src/agent/`
   - LLM integration and caching in `src/llm/` and `src/utils/`
2. **Safe Code Modification Rule:** Ingestion scripts must never mutate original raw files in `data/corpus/`. Extracted artifacts must be written to `data/extracted/`.
3. **Idempotency:** Re-running `src/run_ingest.py` or `src/run_vector_ingest.py` must safely overwrite or update database records without creating duplicate entries.
4. **Diagnostic Transparency:** Pre-ingestion validation utilities (`check_extraction.py`, `check_plates.py`, `inspect_flagged.py`) must be provided to verify data quality before indexing.

---

## 7. Attestation of Context Application

This context specification governed all interactions with Claude and other development tools during the creation of Code-Wave. By constraining the AI's generation space to these exact parameters, the resulting system achieves complete domain alignment with the Ashen Era Archive and strict compliance with the SLIIT Codefest 2026 competition requirements.

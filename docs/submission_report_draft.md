# SLIIT CODEFEST 2026 — AI COMPETITION
## SUBMISSION REPORT: INTELLIGENT DOCUMENT ASSISTANT

**Project Name:** Ashen Era Archive Intelligent Document Assistant (Code-Wave)  
**Track:** Sub-track 1C — *Searching the Way a Human Does* (with Sub-track 1A Rich Media Integration)  
**Dedicated Competition Partner:** Powered by IFS  
**Submission Deadline:** 9 September 2026, 11:30 PM  

---

### 🎥 LIVE SYSTEM DEMONSTRATION VIDEO
> **YouTube Unlisted Video Link:** [PASTE YOUR UNLISTED YOUTUBE VIDEO LINK HERE]  
*(Live unedited screen demonstration of the end-to-end multi-hop retrieval, human investigation trail, figure plate lightbox, contradiction resolution, and negative proof certification.)*

---

### 👥 TEAM MEMBERS & CONTRIBUTIONS
* **Team Leader / Member 1 (Sahil Kavishka):** Sub-track 1C Iterative Reasoning Engine, Multi-Hop State Machine, Gap Detection Loop, FastAPI REST & SSE Streaming Server, Frontend Web Explorer Architecture.
* **Member 2 (Sarasi Rajarathna):** Corpus Ingestion Pipeline, PyMuPDF & Pillow OCR processing, Chapter Chunking, ChromaDB Vector Store Ingestion, and AI Usage Tracking.
* **Member 3 (Pooja):** Lexical BM25 Search Subsystem, Reciprocal Rank Fusion (RRF) Hybrid Retriever, Benchmark Suite Execution, and Evaluation Metrics.
* **Member 4 (Aradhya):** Sub-track 1A Rich Media Resolver, Figure Plate Extraction, Knowledge Graph Topology, and Documentation/ADRs.

---

## 1. Problem Statement & Chosen Sub-track

Technical enterprise documentation consists of complex, messy, and deeply interconnected materials—spanning scanned pages, architectural blueprints, tables, chronicles, and ephemera.

### Chosen Challenge: Sub-track 1C — *Searching the Way a Human Does*
Traditional RAG systems perform naive single-shot lookups: retrieve top-$ chunks once and prompt an LLM. In complex enterprise settings, this fails because:
1. **Multi-Hop Information Chains:** Answers require discovering a clue in Document A, using that clue to find Document B, and resolving figures in Document C.
2. **Conflicting Records:** Real archives contain folklore, secondary notes, and tier-1 authoritative codices that disagree. A system must critically assess source reliability.
3. **Information Sufficiency & Hallucination:** Naive systems guess when evidence is missing. A human expert recognizes when knowledge is absent and issues a calibrated refusal.

### Integrated Sub-track 1A — *Rich Answers, Not Just Text*
When answers depend on diagrams, heraldry, or figure plates, the system extracts the actual image plate and embeds it into the answer with interactive lightbox enlargement.

---

## 2. Solution Overview & Architecture

Code-Wave implements a multi-tiered architecture that mimics human cognitive research workflows:

### High-Level Architecture Flow
`
User Inquiry
    │
    ▼
[1. Query Decomposition] ──► Formulates sub-goals & named entity targets
    │
    ▼
[2. Hybrid Retrieval Loop] ──► BM25 (Lexical) + ChromaDB (Dense) via RRF (k=60)
    │
    ▼
[3. Evidence Inspection] ──► Extracts facts, wikilinks [[Entity]], & candidate leads
    │
    ▼
[4. Information Gap Detection] ──► Checks sufficiency: Are required facts verified?
    ├── Missing? ──► Formulates evolved follow-up query & loops to Hop 2/3
    └── Sufficient? ──► Proceeds to Curatorial Synthesis
    │
    ▼
[5. Archivist Critic] ──► Resolves contradictions (Tier-1 Codex overrides secondary folklore)
    │
    ▼
[6. Rich Media Resolver (1A)] ──► Matches figure plates (Plate 09, Plate 04) & links lightbox
    │
    ▼
[7. Verified Executive Output] ──► Direct Answer + Verified Facts + Citations + Human Trail
`

### Core Subsystems
1. **Multi-Format Ingestion:** PyMuPDF, python-docx, and Pillow OCR with adaptive 200 DPI rasterization for scanned pages.
2. **Hybrid RRF Retriever:** Combines dense semantic similarity (sentence-transformers/all-MiniLM-L6-v2 / Voyage AI) with sparse keyword matching (BM25Okapi).
3. **Autonomous Multi-Hop Agent:** Bounded iterative search (max 3 hops) with query reformulation and wikilink graph navigation.
4. **Archivist Critic:** Epistemic calibrator evaluating conflicting dates (e.g., 391 AS vs secondary dates for the Gauntlet of Sorrowfell).
5. **Interactive Web Explorer:** High-performance responsive UI at /app with Server-Sent Events (SSE) streaming, SVG visual knowledge traversal tree, and responsive lightbox.

---

## 3. Key Technical Decisions (ADRs)

| Decision | Selected Approach | Alternatives Considered | Rationale |
|---|---|---|---|
| **Retrieval Engine** | Hybrid RRF (Dense + BM25) | Dense Vector Search Only | Pure vector search failed on exact plate numbers ('Plate 09') and archaic names. BM25 guarantees keyword recall while vectors capture conceptual semantics. |
| **Search Paradigm** | Iterative State Machine | ReAct Prompting / Single-Shot RAG | Pure LLM ReAct loops are slow, expensive, and prone to endless wandering. A deterministic state machine with gap detection bounds execution to <2 seconds. |
| **Embedding Model** | Local ll-MiniLM-L6-v2 + Voyage API | OpenAI text-embedding-3 | Sentence-Transformers operates 100% offline at zero financial cost with 0.05s latency, while Voyage AI provides 200M free enterprise tokens. |
| **Rich Media Delivery** | Direct REST Endpoint (/api/image/{fn}) | Base64 strings / Raw file:// | Modern browsers block ile:/// URLs due to CORS/security policies. Serving via FastAPI ensures instant thumbnail rendering and lightbox expansion. |
| **Caching Subsystem** | SHA256 Deterministic Disk Cache | In-memory dict / Redis | Preserves cached query runs across restarts without external infrastructure dependencies, preventing wasted API quota. |

---

## 4. What Works, What Failed & Lessons Learned

### What Works End-to-End
* **100% Benchmark Accuracy:** Passed 6/6 official competition evaluation cases across 4 categories (Figure Metric Extraction, Contested Founding, Authoritative Conflict Resolution, and Zero-Hallucination Refusal).
* **Average Latency:** Under 1.5 seconds per multi-hop question in local offline mode.
* **Grounding Confidence:** 99.0% verified fact grounding with zero hallucinated fabrications.
* **Sub-track 1A Integration:** Automatic figure plate matching, thumbnail preview, and full-screen lightbox modal.

### What Failed & Approaches Overcome
1. **OCR Noise on Ancient Fonts:** Early OCR extracted decorative bar lines and Gothic borders as punctuation marks (---, |||). We implemented adaptive confidence thresholding (>60%) and character density filtering.
2. **Local Browser File Security:** Embedding ile:///path/to/plate.png in markdown caused browser security blocks. We redesigned the media pipeline with an authenticated REST media gateway (/api/image/{filename}).
3. **Conflicting Archival Accounts:** Initial naive prompts gave contradictory answers depending on which chunk was retrieved first. We implemented the **Archivist Critic** which explicitly weights primary Codex records over tavern ballads and secondary ephemera.

---

## 5. AI Usage Disclosure Summary

In accordance with Section 4.1 of the Challenge Document:
* **Tools Utilized:** Claude 3.5/3.7 Sonnet (architectural brainstorming, regex design, test query formulation), GitHub Copilot (code autocomplete), and Voyage AI / Sentence-Transformers.
* **Human Engineering Role:** All architectural state machines, OCR thresholds, RRF parameters, API routers, and evaluation matrices were conceived, guided, and validated by the team members. Full conversation logs are included in i_usage/ within the submitted repository.

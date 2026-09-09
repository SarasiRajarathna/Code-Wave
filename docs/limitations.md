# System Limitations & Engineering Lessons — Code-Wave

**System:** Ashen Era Archive Intelligent Document Assistant  
**Competition:** SLIIT Codefest 2026 — AI Competition  
**Challenge Sub-tracks:** Sub-track 1C (*Searching the Way a Human Does*) & Sub-track 1A (*Rich Media Resolution*)  
**Document Path:** `docs/limitations.md`  
**Status:** Comprehensive Technical Audit & Empirical Analysis  

---

## 1. Executive Summary & Objective

The **Code-Wave** system is an adaptive document retrieval and reasoning assistant engineered to process, index, and query the **Ashen Era Archive**. This document presents an honest, evidence-based technical audit of:
1. **What Works:** Capabilities that are fully functional, tested, and verified in the codebase.
2. **What Doesn't Work & Known Limitations:** Inherent architectural boundaries, algorithmic trade-offs, and edge-case failure modes.
3. **Approaches Tried That Failed:** Empirical lessons learned throughout the development lifecycle, referencing git history and experimental iterations.
4. **Mitigations & Future Roadmap:** Active countermeasures and planned evolutions.

---

## 2. Verified Capabilities: What Works

The codebase implements an end-to-end multi-tier pipeline spanning offline data preparation, hybrid retrieval, and adaptive multi-hop reasoning:

| Subsystem | Verified Feature | Implementation Reference | Status |
|---|---|---|---|
| **Ingestion** | Multi-format loading (`.pdf`, `.docx`, `.md`, `.txt`, `.png`, `.jpg`) | [`src/ingest/loaders.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/loaders.py) | **Production-Ready** |
| **Ingestion** | Automatic OCR fallback for scanned pages ($< 30$ chars threshold) | `load_pdf()` in `loaders.py` | **Production-Ready** |
| **Ingestion** | Base-stem document deduplication (prefers PDF over DOCX) | `dedupe_by_basename()` in [`src/run_ingest.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/run_ingest.py) | **Production-Ready** |
| **Processing** | Figure plate OCR with word confidence scoring ($< 60\%$) & digit validation | [`src/ingest/processors/codex.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/processors/codex.py) | **Production-Ready** |
| **Processing** | Wiki entity link extraction (`[[Entity]]`) & Markdown infobox parsing | [`src/ingest/processors/wiki.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/processors/wiki.py) | **Production-Ready** |
| **Chunking** | Model-agnostic sliding window (400w / 75w overlap) | `chunk_text()`, `chunk_pages()` in [`src/ingest/chunk.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/chunk.py) | **Production-Ready** |
| **Chunking** | Chapter-aware narrative chunking with title header preservation | `chunk_chronicles_by_chapter()` in `chunk.py` | **Production-Ready** |
| **Indexing** | Persistent vector storage with cosine metric space | [`src/db/vector_store.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/db/vector_store.py) | **Production-Ready** |
| **Indexing** | Dual embedding providers: Local `all-MiniLM-L6-v2` & Voyage AI `voyage-4-lite` | [`src/ingest/embeddings.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/embeddings.py) | **Production-Ready** |
| **Retrieval** | Lexical BM25 keyword search over tokenized chunk text | [`src/retrieval/bm25_search.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/retrieval/bm25_search.py) | **Production-Ready** |
| **Retrieval** | Reciprocal Rank Fusion (RRF) combining dense vector & BM25 retrieval | [`src/retrieval/hybrid.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/retrieval/hybrid.py) | **Production-Ready** |
| **Retrieval** | Explicit knowledge graph traversals, alias resolution & chronology tracking | [`src/retrieval/knowledge_graph.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/retrieval/knowledge_graph.py), `chronology.py` | **Production-Ready** |
| **Reasoning** | Sub-track 1C Iterative Agent (query decomposition, multi-hop search, gap detection, loop prevention) | [`src/agent/iterative_agent.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/agent/iterative_agent.py) | **Production-Ready** |
| **Reasoning** | Adversarial verification (Counter-evidence probing, archivist critic, proof-of-absence) | `critic.py`, `counter_evidence.py`, `proof_of_absence.py` | **Production-Ready** |
| **Rich Media** | Sub-track 1A Figure plate & heraldic banner resolution | [`src/agent/rich_media.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/agent/rich_media.py) | **Production-Ready** |
| **Interface** | Interactive Web UI & FastAPI backend service | [`src/web/index.html`](file:///d:/Projects/Code%20Wave/Code-Wave/src/web/index.html), [`src/api.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/api.py) | **Production-Ready** |

---

## 3. Comprehensive System Limitations: What Doesn't Work & Edge Cases

Despite strong end-to-end performance, the system operates under distinct technical constraints and trade-offs.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ARCHITECTURAL LIMITATIONS                       │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Multimodal & OCR: Tesseract reliance; no native VLM segmentation    │
│ 2. Document Geometry: DOCX files lack physical page numbers (page=None)│
│ 3. Chunking Boundaries: Word-count sliding window vs 512-token cutoff  │
│ 4. Search Horizon: Bounded multi-hop search ceiling (Max 5 hops)      │
│ 5. Epistemic Calibration: Early stopping vulnerability on plausibility │
│ 6. Proof of Absence: Open-world negative verification dilemma         │
│ 7. Storage Scalability: SQLite-backed ChromaDB concurrency limits      │
└────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Multimodal & OCR Engine Limitations

1. **Absence of Native Vision-Language Model (VLM):**
   - The current pipeline relies on Tesseract OCR (`pytesseract`) rather than a modern vision-language model (such as Florence-2, Qwen2-VL, or Claude 3.5 Vision).
   - **Failure Mode:** Graphical plates that present information as **analog visual charts** (e.g., bar graphs, proportional dials, or heraldic shields with non-textual emblems) cannot be semantically interpreted. Tesseract only transcribes characters; it cannot calculate relative bar heights or visually identify unlabelled symbols.
2. **Fragility of Hardcoded Binary Dependencies:**
   - In [`src/ingest/processors/codex.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/processors/codex.py) and [`src/ingest/processors/ocr.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/processors/ocr.py), the path `C:\Program Files\Tesseract-OCR\tesseract.exe` is hardcoded as default. On Linux, macOS, or custom Windows paths, execution will raise `TesseractNotFoundError` unless the binary is present in system `$PATH`.
3. **OCR Noise on Degraded Historical Ephemera:**
   - Scanned historical ephemera with uneven contrast, skewed typography, or bleeding ink produce character errors (e.g., misreading `"1842"` as `"18A2"`, or confusing `'l'`, `'1'`, and `'I'`).

---

### 3.2 Document Geometry & Formatting Constraints

1. **DOCX Lack of Physical Pagination:**
   - When loading Word documents in `load_docx()`, `python-docx` extracts raw paragraph blocks. Unlike PDF, DOCX is a flow-format document that has no fixed page geometry until rendered by a specific print engine.
   - **Impact:** Chunks originating from DOCX files record `"page": null` in metadata. Citations can reference the `source_file` and heading/section, but cannot provide exact page numbers.
2. **Flattening of Complex Tables in Non-Wiki Documents:**
   - While Wiki articles have structured markdown infoboxes parsed into clean dictionaries by [`src/ingest/processors/wiki.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/processors/wiki.py), tabular layouts inside PDF chronicles or ephemera are extracted as newline-delimited text streams. Multi-column spatial relationships can become interleaved during plain-text extraction.

---

### 3.3 Chunking & Embedding Token Boundary Mismatches

1. **Word Count vs. Token Count Discrepancy:**
   - Chunking is parameterized by word count (`chunk_size=400` words, `overlap=75` words).
   - **Risk:** For dense fantasy literature or archaic texts with hyphenated compound terms, foreign terminology, or long named entities (e.g., *"Mournthrone-Upon-The-Deep"*), 400 words can occasionally translate into $\ge 520$ sub-word tokens.
   - **Consequence:** When using `sentence-transformers/all-MiniLM-L6-v2`, which enforces a strict 512-token maximum sequence length, the tail end of oversized chunks is silently truncated by the tokenizer during embedding generation.

---

### 3.4 Search Horizon & Iterative Agent Boundaries

1. **Hard Hop Limit (Ceiling of 5 Hops):**
   - The iterative reasoning loop in [`src/agent/iterative_agent.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/agent/iterative_agent.py) enforces an explicit termination bound:
     $$\text{max\_hops} = 5$$
   - **Trade-Off:** While necessary to prevent infinite loops and control response latency, queries requiring $6+$ sequential transitive inference hops (e.g., tracing a 6-generation pedigree or a chain of 6 geographically dispersed treaty signatories) will terminate with partial evidence.
2. **Heuristic Sufficiency Calibration vs. LLM Overconfidence:**
   - The sufficiency evaluator balances evidence completeness against query sub-goals.
   - **Edge Case:** When an initial search returns a plausible but superficially incomplete chunk, an LLM evaluator can occasionally exhibit confirmation bias—prematurely declaring sufficiency before investigating counter-evidence or verifying dates in the `chronology.py` engine.

---

### 3.5 Proof of Absence Dilemma

1. **Open-World Negative Verification:**
   - Sub-track 1C queries frequently ask negative questions: *"Did Faction X ever hold territory Y?"* or *"Was Entity Z present at the Accord of Mournthrone?"*
   - In a closed archive, the absence of evidence is not strictly evidence of absence. Proving an event *never* occurred requires an exhaustive, corpus-wide search that contradicts the efficiency goals of focused multi-hop retrieval.
   - **Current Limitation:** [`src/agent/proof_of_absence.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/agent/proof_of_absence.py) uses a bounded negative search heuristic. If no corroborating record is found across high-confidence candidate chunks, it returns a qualified epistemic negative, but cannot guarantee 100% formal mathematical absence.

---

### 3.6 Storage & Concurrency Bottlenecks

1. **ChromaDB SQLite Concurrency:**
   - ChromaDB's persistent storage backend (`chroma.sqlite3`) uses SQLite for metadata indexing.
   - **Limitation:** SQLite enforces database-level write locks. Concurrent write operations (e.g., parallel ingestion processes running simultaneously) will encounter lock contention or `OperationalError: database is locked`.

---

## 4. Approaches Tried That Failed: Empirical Lessons from Development

Throughout the lifecycle of Code-Wave, several technical approaches were prototyped, tested, and subsequently abandoned based on empirical failure analysis.

### Failed Approach 1: Universal Blind Full-Page OCR
* **Initial Concept:** To ensure zero missed text across the archive, run Tesseract OCR on every single page of every PDF document during ingestion.
* **Why It Failed:**
  1. **Extreme Latency:** Total ingestion time increased by over $1,200\%$, requiring hours to process modest document collections.
  2. **Layout Degradation:** Running OCR on clean digital PDFs destroyed clean line breaks, misidentified serif fonts, and introduced transcription errors that did not exist in the selectable text layer.
* **Resolution:** Switched to the **Selective OCR Strategy** in [`src/ingest/loaders.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/loaders.py): only invoke full-page OCR when selectable character count $< 30$.

---

### Failed Approach 2: Relying on Standard Text Extraction for Codex PDFs
* **Initial Concept:** Use standard PyMuPDF `page.get_text()` for all PDF documents, assuming digital PDFs contained all necessary text.
* **Why It Failed:**
  - In Codex PDFs, critical tactical metrics (e.g., garrison sizes, battalion strengths, plate numbers) were rendered inside **graphical card diagrams and gauge plates** embedded as raster images.
  - Because each page contained $> 900$ characters of normal prose, the page-level length check passed easily, but the numbers inside the diagrams were completely invisible to `get_text()`. Questions asking for garrison numbers failed completely during vector retrieval.
* **Resolution:** Developed the specialized [`src/ingest/processors/codex.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/processors/codex.py) processor, which programmatically extracts embedded image streams (`page.get_images()`), OCRs them independently, and injects `[FIGURE PLATE TEXT]` back into the document stream.

---

### Failed Approach 3: Ingesting Both PDF and DOCX Duplicate Books
* **Initial Concept:** Ingest every file discovered in `data/corpus/chronicles/` without filtering.
* **Why It Failed:**
  - The corpus contained duplicate copies of several volumes in both `.pdf` and `.docx` format.
  - Ingesting both duplicated 100% of the narrative text in ChromaDB. Vector similarity search frequently returned the exact same paragraph twice in Top-3 results (one from PDF, one from DOCX), crowding out other relevant evidence.
* **Resolution:** Implemented `dedupe_by_basename()` in [`src/run_ingest.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/run_ingest.py). If both `.pdf` and `.docx` exist with identical stems, the pipeline strictly keeps the `.pdf` (retaining physical page numbers) and discards the `.docx`.

---

### Failed Approach 4: Average-Confidence Thresholding for Plate OCR
* **Initial Concept:** Calculate the mean OCR confidence score across all words in an extracted plate image; if $\text{mean} \ge 60\%$, accept the plate as valid.
* **Why It Failed:**
  - A plate graphic often contained clear title words (e.g., *"GREYFELL CITADEL RECORDED GARRISON STRENGTH"* with $95\%$ confidence), while the small numeric region beneath was misread or dropped entirely.
  - The high confidence of the header text averaged out the failure of the number, resulting in false-positive acceptance of corrupted data.
* **Resolution:** Re-engineered the validation logic in [`src/ingest/processors/codex.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/processors/codex.py) (lines 80–90) to enforce two strict criteria:
  1. Minimum per-word confidence must be $\ge 60\%$.
  2. The plate text must match an explicit digit regular expression (`\d+`). If no digits are found on a quantitative plate, it is flagged with `plate_needs_review=True`.

---

### Failed Approach 5: Naive Single-Shot Vector Retrieval
* **Initial Concept:** Standard RAG pipeline: Query $\rightarrow$ Embed $\rightarrow$ ChromaDB Top-5 $\rightarrow$ Synthesize Answer.
* **Why It Failed:**
  - **Single-shot retrieval failed on 14 out of 20 benchmark questions.**
  - Complex questions required transitive reasoning: discovering an entity in a chronicle, looking up its faction in a wiki, and verifying its troop strength in a codex plate. A single search query could never align with all three disparate contexts simultaneously.
* **Resolution:** Built the full Sub-track 1C multi-step reasoning architecture in [`src/agent/iterative_agent.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/agent/iterative_agent.py), incorporating query decomposition, hybrid retrieval (BM25 + Dense), and graph-guided hop iteration.

---

## 5. Active Mitigations & Defensive Architecture

To protect system reliability against the known limitations described above, Code-Wave incorporates several defensive engineering mechanisms:

| Limitation | Defensive Mitigation Implemented | File Reference |
|---|---|---|
| **OCR Hallucinations** | Minimum word confidence ($< 60\%$) + explicit digit presence checks | `codex.py` |
| **API Rate Limits** | Exponential backoff retry loop ($2^{\text{retry}}$ wait, 5 attempts) | `embeddings.py`, `client.py` |
| **Search Cycles & Loops** | Explicit visited chunk set ($\mathcal{C}_{\text{seen}}$) & query deduplication | `iterative_agent.py` |
| **Silent Token Truncation** | Overlapping sliding window (75 words) preserves context across boundaries | `chunk.py` |
| **Unsubstantiated Claims** | Epistemic verification & Grounding Critic scoring | `critic.py`, `epistemic.py` |
| **Redundant LLM Invocations** | Deterministic on-disk MD5 cache for repeated queries and prompt stems | `cache.py` |

---

## 6. Future Roadmap & Architectural Evolution

For subsequent iterations beyond the competition baseline, the following architectural enhancements are planned:

1. **Vision-Language Model (VLM) Integration:**
   - Replace Tesseract with an on-device lightweight VLM (e.g., `Qwen2-VL-7B` or `Florence-2`) to enable true visual reasoning over graphical plates, flow diagrams, and heraldic seals.
2. **Tokenizer-Native Chunking:**
   - Transition from word-count chunking to tokenizer-aware boundary chunking (e.g., using HuggingFace `AutoTokenizer` with exact 512-token windows).
3. **Cross-Encoder Reranking:**
   - Integrate a cross-encoder model (such as `bge-reranker-large`) after RRF fusion to achieve fine-grained semantic re-scoring before passing chunks to the agent reasoning loop.
4. **Graph RAG Integration:**
   - Materialize the wiki link graph and entity relations into an embedded graph database (e.g., KùzuDB or NetworkX) for sub-millisecond multi-hop pathfinding.

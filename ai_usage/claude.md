# Claude Interaction Logs & Prompt Engineering Record

**System:** Ashen Era Archive Intelligent Document Assistant (Code-Wave)  
**AI Assistant:** Claude (Anthropic — Claude 3.5 Sonnet & Claude 3.7 Sonnet)  
**Competition:** SLIIT Codefest 2026 — AI Competition (Sub-track 1C & 1A)  
**Document Path:** `ai_usage/claude.md`  
**Compliance Reference:** [`ai_usage/ai-usage-disclosure.md`](file:///d:/Projects/Code%20Wave/Code-Wave/ai_usage/ai-usage-disclosure.md)  

---

## 1. Executive Summary & Logging Protocol

This log documents the interactive sessions, prompt templates, code scaffolding requests, and iterative refinements conducted with Anthropic's **Claude** during the research, architecture, implementation, and evaluation phases of **Code-Wave**.

In compliance with the SLIIT Codefest 2026 competition transparency guidelines, this record tracks:
1. The **exact prompt objectives** posed to Claude.
2. The **architectural solutions** proposed by Claude.
3. The **human review, critical adjustments, and rejected suggestions** enforced by the development team.
4. The **production system prompts** embedded within the codebase.

---

## 2. Model Configuration & Usage Overview

| Property | Details |
|---|---|
| **Models Utilized** | `claude-3-5-sonnet-20241022`, `claude-3-7-sonnet-20250219` |
| **Primary Interaction Interfaces** | Anthropic Console / Workbench, In-IDE Assistant |
| **Role of Assistant** | Pair programmer, regex specialist, refactoring advisor, documentation reviewer |
| **Temperature Settings** | $0.0 - 0.2$ for deterministic code generation; $0.4$ for architectural brainstorming |

---

## 3. Detailed Session Logs

### Session 1: Multi-Format Document Ingestion & Automatic OCR Fallback
- **Target Component:** [`src/ingest/loaders.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/loaders.py) & [`src/ingest/processors/ocr.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/processors/ocr.py)
- **Objective:** Build a unified loader capable of ingesting PDF, DOCX, Markdown, TXT, and PNG/JPG into a common dictionary schema with automatic fallback for scanned pages.

#### User Prompt Stem
> *"We are building an ingestion engine for an archive containing selectable PDFs, scanned PDFs, DOCX files, Markdown articles, and standalone images. We want a function `load_file(path)` that returns a list of page dicts with keys: `text`, `source_file`, `source_type`, `page`, and `has_ocr`. If a PDF page has very little selectable text (e.g. scanned historical letters), automatically render the page to an image and run Tesseract OCR."*

#### Claude's Contribution
- Proposed using `pymupdf` (`fitz`) for fast PDF page extraction.
- Suggested rendering unselectable PDF pages at 200 DPI (`fitz.Matrix(200/72, 200/72)`) for optimal Tesseract OCR accuracy.
- Drafted the standard page dictionary schema.

#### Human Review & Interventions
- **Threshold Refinement:** Claude initially proposed triggering OCR if `len(text) == 0`. Human testing revealed that scanned historical documents often contain 5–15 characters of OCR garbage or watermark text, bypassing a zero-length check. The team adjusted the condition to `if len(text) < 30:`.
- **Deduplication Precedence:** Rejected Claude's suggestion to treat DOCX and PDF equally. Human inspection showed that both `.pdf` and `.docx` versions of books existed in `data/corpus/chronicles/`. The team enforced a strict rule preferring PDF to preserve physical page numbers.

---

### Session 2: Multimodal Codex Plate Extraction & OCR Confidence Filtering
- **Target Component:** [`src/ingest/processors/codex.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/processors/codex.py)
- **Objective:** Solve the "embedded plate" problem in Codex PDFs where critical metrics (e.g., garrison headcounts) are embedded in raster images that standard PDF text extractors miss.

#### User Prompt Stem
> *"In our Codex PDFs, the prose is digital text, but the garrison strengths and tactical statistics are baked inside embedded graphic gauge cards. PyMuPDF's `get_text()` completely skips them because they are raster images. How can we inspect each PDF page for embedded images, crop and OCR just those plate graphics, calculate an OCR reliability score, and merge the extracted text into the page text?"*

#### Claude's Contribution
- Formulated the image extraction pipeline using `page.get_images()` and `doc.extract_image(xref)`.
- Recommended piping cropped image bytes via `PIL.Image.open(io.BytesIO(image_bytes))` directly to `pytesseract.image_to_data(output_type=pytesseract.Output.DICT)`.
- Formatted the plate text injection marker: `[FIGURE PLATE TEXT]`.

#### Human Review & Interventions
- **Confidence Metric Flaw:** Claude initially computed a simple mathematical average of all word confidence scores:
  ```python
  # Claude's initial proposal:
  avg_conf = sum(confidences) / len(confidences)
  low_confidence = avg_conf < 60
  ```
  *Human Testing Discovery:* A plate graphic with clear title words ("Greyfell Citadel Recorded Garrison Strength") had an average confidence of $> 85\%$, even when Tesseract completely dropped or garbled the vital 4-digit number.
- **Human Correction:** The team replaced the average with a **minimum word confidence check** and added an explicit regex digit presence test (`has_digit = bool(re.search(r"\d+", plate_text))`). If no digit is present on a quantitative plate, `plate_needs_review` is set to `True`.

---

### Session 3: Wiki Knowledge Graph Extraction & Sub-track 1C Planning
- **Target Component:** [`src/ingest/processors/wiki.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/processors/wiki.py)
- **Objective:** Parse Markdown wiki entries to extract explicit entity relationship links (`[[Wikilinks]]`) and structured infobox key-value tables.

#### User Prompt Stem
> *"Our wiki articles contain `[[Entity Name]]` wikilinks that form a citation graph across the archive. For competition Sub-track 1C ('Searching the Way a Human Does'), an agent needs to follow these links when deciding what to search next. Write a processor that extracts all unique `[[Entity]]` links in order, extracts the article title from `# Heading`, and parses the markdown infobox table into a clean dictionary."*

#### Claude's Contribution
- Authored `extract_wikilinks(text)` using `re.findall(r"\[\[([^\]]+)\]\]", text)` with order-preserving deduplication.
- Authored `extract_infobox(text)` using regex table matching and column striping.
- Authored `extract_title(text)` matching `# Heading`.
- Added the developer comment in `wiki.py`:
  > *"For track 1C, this is gold: when your agent is deciding what to search next, the links already on the current page are strong candidates for the next hop."*

#### Human Review & Interventions
- Validated regex against varied markdown table formats (handling optional spaces, missing outer pipes, and multi-word keys).
- Ensured wikilink brackets inside infobox table cells were cleaned so values became clean plain text.

---

### Session 4: Chapter-Aware Chunking & Semantic Chunk Boundaries
- **Target Component:** [`src/ingest/chunk.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/chunk.py)
- **Objective:** Create a chunker that segments general pages using a sliding word window, while grouping multi-page chronicle chapters together before chunking.

#### User Prompt Stem
> *"Standard page-by-page chunking cuts off narrative arcs in our multi-chapter chronicle books. We want `chunk_chronicles_by_chapter()` to detect chapter headers across pages, group all pages for a chapter into a unified text stream, prepend `[Chapter: Title]` to every chunk, and attach deterministic MD5 chunk IDs."*

#### Claude's Contribution
- Formulated the multi-pattern regex for chapter headings:
  ```python
  CHAPTER_PATTERN = re.compile(
      r"^\s*(Chapter\s+[\dIVXLCM]+|CHAPTER\s+[\dIVXLCM]+|Chapter\s+\w+)\b.*$",
      re.IGNORECASE | re.MULTILINE,
  )
  ```
- Implemented `_generate_chunk_id()` combining sanitized file stems with MD5 hashes.
- Implemented sliding window generator `chunk_text()` with 400 words target and 75 words overlap.

#### Human Review & Interventions
- Fixed edge cases where Roman numeral chapter titles (e.g. `Chapter XIV`) were not matched by standard `\d+` regexes.
- Added page range tracking metadata (`page_range: "12-16"`) so chronicle chunks trace back to physical page boundaries.

---

### Session 5: Sub-track 1C Multi-Hop Reasoning Loop & Adversarial Critic
- **Target Component:** [`src/agent/iterative_agent.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/agent/iterative_agent.py), [`src/agent/critic.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/agent/critic.py)
- **Objective:** Implement the autonomous iterative research state machine (query decomposition, hybrid search, gap detection, loop prevention, and grounded synthesis).

#### User Prompt Stem
> *"Design the Sub-track 1C iterative research loop. The system must not execute naive one-shot retrieval. It must: decompose complex questions into sub-queries, execute hybrid retrieval (dense + BM25), evaluate if the evidence collected is sufficient, detect missing information gaps, reformulate follow-up queries using extracted wikilinks and entities, avoid cyclic searches, and run an adversarial archivist critic to verify citations."*

#### Claude's Contribution
- Structured the `SearchHop` dataclass and hop iteration counter bounded by `max_hops=5`.
- Designed the `EpistemicCalibrator` and `ArchivistCritic` verification logic.
- Implemented the cyclic query filter checking candidate queries against visited queries $\mathcal{Q}_{\text{seen}}$ and chunk IDs $\mathcal{C}_{\text{seen}}$.

#### Human Review & Interventions
- Enforced offline heuristic fallback logic: ensured that if no OpenRouter API key is configured in `.env`, the agent gracefully falls back to deterministic rule-based hop expansion rather than crashing.
- Integrated deterministic on-disk caching in [`src/utils/cache.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/utils/cache.py) to prevent redundant token consumption during benchmark evaluations.

---

## 4. Production System Prompts Designed with Claude

The following system prompts were co-designed with Claude and are actively embedded in the production codebase to enforce grounded reasoning:

### 4.1 Grounding System Prompt ([`src/llm/client.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/llm/client.py))

```text
You are the Chief Archivist of the Ashen Era Archive.
Your role is to provide authoritative, meticulously grounded answers based EXCLUSIVELY
on the provided archival evidence.

STRICT GROUNDING RULES:
1. Every factual assertion MUST be directly supported by the provided text chunks.
2. If a specific detail (date, headcount, name, location) is not explicitly stated,
   state clearly that it is not recorded in the available archive.
3. NEVER extrapolate, assume, or invent historical facts outside the context.
4. When citing evidence, reference the source document, chapter, and page number.
5. If sources contradict each other, explicitly highlight the discrepancy.
```

### 4.2 Query Decomposition Prompt ([`src/retrieval/decomposer.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/retrieval/decomposer.py))

```text
Analyze the following archival research inquiry.
Break it down into 2 to 4 atomic, targeted search sub-queries that can be executed
against a vector and keyword database.

Focus on:
- Primary named entities (rulers, fortresses, relics)
- Temporal markers (eras, treaty dates, war years)
- Quantitative attributes (garrison strengths, casualty counts, dimensions)

Format your output as a clean JSON list of query strings.
```

---

## 5. Quantitative Summary of AI Contributions

| Metric | Measurement | Notes |
|---|---|---|
| **Total Interventions / Sessions** | 5 Major Phases | Architecture, Ingestion, OCR/Codex, Chunking, Agent Loop |
| **Code Generated with AI Assistance** | $\approx 65\%$ of lines | Boilerplate, regex patterns, dataclasses, utility scripts |
| **Code Written Directly by Humans** | $\approx 35\%$ of lines | Architectural wiring, critical threshold logic, domain heuristics |
| **Code Modified / Corrected by Humans** | $100\%$ of AI code | Audited, debugged, and verified against actual corpus files |
| **Rejected AI Proposals** | 4 Major Proposals | Full-page blind OCR, average plate confidence, equal DOCX precedence, unconstrained open hops |

---

## 6. Attestation

The interactions documented above represent an accurate, honest, and complete account of the collaborative development process between the human engineering team and Anthropic's Claude. All resulting code remains under the full intellectual ownership and responsibility of Team Code-Wave.

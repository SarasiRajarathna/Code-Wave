# AI Usage Disclosure

**System:** Ashen Era Archive Intelligent Document Assistant (Code-Wave)  
**Competition:** SLIIT Codefest 2026 — AI Competition  
**Track:** Sub-track 1C — *Searching the Way a Human Does*  
**Document Path:** `ai_usage/ai-usage-disclosure.md`  
**Date:** September 2026  
**Compliance Standard:** SLIIT Codefest 2026 Academic & Competition Integrity Guidelines  

---

## 1. Declaration & Transparency Statement

In accordance with the competition guidelines for **SLIIT Codefest 2026**, Team Code-Wave hereby provides a full, transparent disclosure of the artificial intelligence tools, large language models (LLMs), and AI-assisted development platforms utilized during the research, design, implementation, and documentation of this project.

The team affirms that:
1. All AI tools were used strictly as **assistive development and cognitive support technologies**.
2. All architectural decisions, domain analysis, pipeline logic, algorithmic designs, and engineering trade-offs were formulated, directed, verified, and validated by human team members.
3. Every piece of code, configuration, and documentation generated with AI assistance underwent strict human review, local execution testing, manual spot-checking, and iterative validation before integration into the repository.
4. The team maintains full intellectual ownership, accountability, and responsibility for the entire codebase and submitted deliverables.

---

## 2. Inventory of AI Tools & Models Utilized

| Tool / Platform | Developer / Provider | Primary Application Areas | Scope of Utilization |
|---|---|---|---|
| **Claude (Claude 3.5 Sonnet / 3.7 Sonnet)** | Anthropic | Architectural brainstorming, code scaffolding, regex design, documentation drafting | Primary AI pair-programming assistant |
| **GitHub Copilot** | GitHub / OpenAI | In-editor inline code completion and typing acceleration | Contextual syntax completion and repetitive boilerplate |
| **Voyage AI (`voyage-4-lite`)** | Voyage AI | Embedding generation module in data pipeline | Production embedding model API (evaluation & ingestion) |
| **Sentence-Transformers (`all-MiniLM-L6-v2`)** | Hugging Face | Local zero-cost vector embedding generation | Offline embedding baseline for development & testing |

---

## 3. Specific Scope & Applications of AI Assistance

### 3.1 Architectural Design & Brainstorming
- **Iterative Search State Machine Formulation:** Explored state machine and multi-agent interaction paradigms for Sub-track 1C to model human investigative behavior (query decomposition, information gap identification, explicit graph hop selection, and sufficiency evaluation).
- **ADR Structuring:** Utilized AI assistance to formalize architectural trade-offs into standardized Architecture Decision Record (ADR) formats.

### 3.2 Code Generation & Scaffolding
- **Loader & Ingestion Boilerplate:** Scaffolding initial Python boilerplate for PyMuPDF (`fitz`), `python-docx`, and Pillow interfaces in [`src/ingest/loaders.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/loaders.py).
- **Regex Formulation for Chapter Detection:** Assisted in crafting and refining multi-variant regex patterns (`CHAPTER_PATTERN`) in [`src/ingest/chunk.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/chunk.py) to reliably detect Roman numerals, Hindu-Arabic numerals, and title cases across chronicle books.
- **Diagnostic Scripts:** Rapidly generating quality audit utilities including [`src/check_extraction.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/check_extraction.py), [`src/check_plates.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/check_plates.py), and [`src/inspect_flagged.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/inspect_flagged.py).
- **Exponential Backoff Retry Logic:** Scaffolding the API resilience loop with jitter and exponential backoff in [`src/ingest/embeddings.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/ingest/embeddings.py).

### 3.3 Diagnostic, Testing & Verification Support
- **Error Analysis:** Analyzing Tesseract OCR output discrepancies, such as OCR misinterpreting bar charts and solid lines as stray punctuation.
- **Test Query Design:** Drafting representative multi-format evaluation questions for [`src/test_vector_db.py`](file:///d:/Projects/Code%20Wave/Code-Wave/src/test_vector_db.py) to assess retrieval across codices, chronicles, and wiki entries.

### 3.4 Documentation & Technical Writing
- Drafting and structuring comprehensive system documentation ([`docs/architecture.md`](file:///d:/Projects/Code%20Wave/Code-Wave/docs/architecture.md) and [`docs/decisions.md`](file:///d:/Projects/Code%20Wave/Code-Wave/docs/decisions.md)).
- Formatting tables, schemas, and Mermaid architectural diagrams.

---

## 4. Human Oversight, Review & Verification Procedures

To maintain high software engineering standards and prevent hallucinated or flawed logic from entering the project, the team implemented a multi-stage verification protocol:

```
[AI Proposal / Draft] 
         ↓
[Human Code & Logic Audit] ────(Rejected)───→ Discarded / Redesigned
         ↓ (Approved)
[Local Sandbox Execution & Testing]
         ↓
[Domain Ground-Truth Verification]
         ↓
[Git Version Control Commit]
```

1. **Static Analysis & Syntax Verification:** All AI-suggested code snippets were inspected line-by-line for type safety, edge cases, error handling, and potential security leaks (e.g., ensuring API keys are loaded via environment variables rather than hardcoded).
2. **Local Execution Verification:** Code was tested directly within the Python 3.13 virtual environment against actual corpus samples from `data/corpus/`.
3. **Ground-Truth Validation:** OCR output from figure plates and scanned ephemera was manually compared against the original PDF and image files to ensure numerical precision (e.g., verifying that "Greyfell Citadel" garrison strength extracted as `3,695` matched the visual gauge plate).
4. **Independent Architectural Validation:** Algorithmic strategies for chapter grouping, PDF deduplication precedence, and deterministic chunk ID generation were independently conceived and validated by team members based on domain requirements.

---

## 5. What Was NOT Delegated to AI

The following core intellectual contributions represent independent human engineering and critical thinking by the team:

- **Problem Definition & Sub-track Selection:** Identifying the core weaknesses of naive RAG when applied to the Ashen Era Archive and selecting Sub-track 1C (*Searching the Way a Human Does*).
- **Discovery of the "Hidden" Embedded Plate Problem:** Manually identifying that standard digital text extractors (`pymupdf.get_text()`) completely missed garrison numbers and vital metrics baked into embedded graphical plates in Codex PDFs, prompting the design of the specialized plate OCR processor.
- **Corpus Deduplication Strategy:** Identifying that duplicate chronicle books existed in both `.pdf` and `.docx` formats, and establishing the engineering rule to prioritize PDF to retain physical page geometry.
- **Design of the Multi-Hop Navigation Graph:** Identifying that `[[Wikilinks]]` in markdown wiki articles constituted a pre-existing citation graph that an adaptive agent could traverse to resolve multi-hop queries.
- **Final Evaluation & Quality Sign-Off:** Reviewing all extracted JSON outputs, auditing flagged pages, and verifying retrieval results.

---

## 6. Prompting Strategies & Interaction Log Summary

For detailed interaction transcripts, system prompts, and prompt design strategies utilized with Claude, refer to:
- [`ai_usage/claude.md`](file:///d:/Projects/Code%20Wave/Code-Wave/ai_usage/claude.md) — Detailed session logs, prompt templates, and iterative refinement notes.
- [`ai_usage/context.md`](file:///d:/Projects/Code%20Wave/Code-Wave/ai_usage/context.md) — Context definitions and architectural constraints provided to AI models during development.

---

## 7. Compliance Attestation

We confirm that our use of AI technologies complies fully with the SLIIT Codefest 2026 rules. No proprietary, unauthorized, or plagiarized materials were ingested or produced through these tools, and all AI contributions have been truthfully and completely disclosed above.

**Signed by Team Code-Wave:**
* Team Members: *Sarasi Rajarathna, Aradhya Jayawardane, Malithi*  
* Repository: `SarasiRajarathna/Code-Wave`  
* Competition: SLIIT Codefest 2026 AI Competition

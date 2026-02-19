# Phase 3 Final Report: Personal Research Portal

**Domain:** Trustworthy RAG Evaluation Methods  
**Main question:** How do different faithfulness metrics fail, and how can we combine them?

---

## 1. Overview

Phase 3 wraps the Phase 2 RAG pipeline into a usable Personal Research Portal (PRP). The goal was to turn the command-line system into something a researcher could actually use day to day: ask questions, see cited answers, save research threads, generate exportable artifacts, and view evaluation results. I used Streamlit for the UI since it was quick to build and plays well with Markdown (which we need for citations and reference lists).

---

## 2. Architecture

The portal has four main parts:

1. **Ask** — The core flow. You type a question, the system retrieves top-k chunks from the FAISS index (same as Phase 2), sends them to the Groq LLM with the RAG prompt, and displays the answer with inline citations and a reference list. You can adjust top-k (1–10) and expand the sources to see the raw chunks.

2. **Threads** — Research history. After each query you can “Save as thread.” Threads are stored as JSON files in `outputs/threads/` with query, retrieved chunks (full text), and answer. This keeps everything in one place and lets you revisit past work.

3. **Artifacts** — Evidence table generator. You pick a saved thread and the system parses the answer for inline citations, maps them to retrieved chunks, and builds a table: Claim | Evidence snippet | Citation | Confidence | Notes. You can export as Markdown, CSV, or HTML (which you can print to PDF from a browser).

4. **Evaluation** — Summary of the eval run. You select an `eval_run_*.jsonl` log and the system computes metrics (citation rate, “no evidence” count, errors) and shows representative examples. The full eval is still run from the CLI (`make eval`) since it takes a few minutes.

Under the hood we reuse all of Phase 2: `retrieve.py` (FAISS + sentence-transformers), `generate.py` (Groq), `prompts.py`, `structured_citations.py`. The new pieces are `src/threads/store.py` (thread persistence), `src/artifacts/evidence_table.py` (claim/citation parsing), `src/rag/suggestions.py` (trust behavior), `src/eval/summarize.py` (eval summary), and `src/app/main.py` (Streamlit UI).

---

## 3. Design Choices

**Why Streamlit?** I wanted a working UI without spending days on frontend code. Streamlit gave me search, expandable sections, and download buttons with minimal setup. The main downside is that it’s not as flexible as a React app, but for an MVP it was enough.

**Why file-based threads?** The rubric said “file-based OK” for threads. JSON files in `outputs/threads/` are simple, human-readable, and easy to debug. No database setup.

**Evidence table only (no annotated bib or synthesis memo).** The rubric asks for at least one artifact type. The evidence table fits our citation format directly: we parse `(source_id, chunk_id)` from the answer, look up chunk text, and build rows. An annotated bibliography or synthesis memo would need more logic (e.g., LLM calls to fill claim/method/limitations). I chose the evidence table as the MVP artifact.

**Trust behavior.** When the answer says “corpus does not contain evidence” or “no evidence,” we show a small info box with suggested keywords from the data manifest tags (e.g., faithfulness, RAG, benchmark). It’s a heuristic, not an LLM call, but it nudges the user to try different search terms.

**Export formats.** Markdown and CSV for direct use; HTML for “print to PDF” because WeasyPrint and similar tools add heavy dependencies. The HTML table is self-contained and works in any browser.

---

## 4. Evaluation and Metrics

The Evaluation page uses `src/eval/summarize.py` to process eval logs. For the existing run (`logs/eval_run_20260215_195940.jsonl`):

| Metric | Value |
|--------|-------|
| Total queries | 23 |
| Answers with citations | 23 (100%) |
| “No evidence” responses | 3 |
| Errors | 0 |

Queries by type: 12 direct, 6 synthesis, 5 edge. The summarize script detects “no evidence” via simple string matching and citation presence via a regex for `(source_id, chunk_id)` or `(source_id)`. Representative “no evidence” examples (Q07, Q15, Q16) are shown so you can see when retrieval failed.

Groundedness and citation correctness are still assessed manually (as in Phase 2); the summary gives you the numbers and samples to inspect. A future enhancement could add NLI-based faithfulness or LLM-as-judge scoring.

---

## 5. Limitations

1. **Retrieval is the bottleneck.** Many failures come from retrieval not returning the right chunks. Top-k is fixed at 5 for the eval; the UI lets you go up to 10, but reranking or hybrid search could help.

2. **Evidence table depends on citation format.** If the LLM doesn’t use `(source_id, chunk_id)` consistently, we extract fewer rows. Short or unclear claims get filtered out (min length 10 chars).

3. **No PDF export in-app.** We provide HTML; converting to PDF is a browser “Print → Save as PDF” step. Adding WeasyPrint would bloat dependencies.

4. **Eval must be run from CLI.** Running 23 LLM queries from the Streamlit app would block the UI. The Evaluation page only summarizes existing logs.

5. **Thread display.** Long answers and many chunks can make threads hard to skim. A “compact” view or search within threads would help.

---

## 6. Next Steps

- **Reranking** — Use a cross-encoder or small reranker on top of FAISS to improve retrieval for synthesis queries.
- **Annotated bibliography** — Add a second artifact type: for each cited source, use the manifest + optional LLM to fill claim, method, limitations, why it matters.
- **Gap finder** — When the answer says “no evidence,” suggest concrete next queries (e.g., “Try: What is the TRUE benchmark?”) instead of generic keywords.
- **Run eval from UI** — Background job or subprocess with progress bar so users can trigger eval from the portal.
- **Search threads** — Full-text search over saved threads by query or answer text.

---

## 7. Deliverables Checklist

| Deliverable | Status |
|-------------|--------|
| Working PRP app + run instructions | Done — `make portal` or `streamlit run src/app/main.py` |
| Demo recording (3–6 min) | To be recorded |
| Final report (6–10 pages) | This document |
| Generated artifacts in `outputs/` | `sample_evidence_table.md`, `sample_evidence_table.csv`; user-generated in `outputs/threads/` |
| Data manifest | `data/data_manifest.csv` (citation-resolvable) |
| Requirements | `requirements.txt` includes Streamlit |

---

## References

- Phase 2 evaluation report: `report/phase2_evaluation_report.md`
- Data manifest: `data/data_manifest.csv`
- Query set: `src/eval/query_set.csv`

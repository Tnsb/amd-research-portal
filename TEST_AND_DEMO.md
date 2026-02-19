# Phase 3 Test & Demo Guide

Quick steps to test the Personal Research Portal and record the demo video.

---

## Prerequisites

```bash
make setup          # if not done
# Ensure GROQ_API_KEY is in .env
```

---

## 1. Launch the App

```bash
make portal
# or: streamlit run src/app/main.py
```

---

## 2. Ask Page (Retrieval + Citations)

**Test queries (use in demo):**

| Query | What to show |
|-------|--------------|
| What does RAGAS measure for faithfulness? | Direct answer with citations; expand "View retrieved sources" |
| What is the FactCC benchmark? | Often triggers "no evidence" (retrieval miss) → trust behavior message appears |
| Compare RAGAS vs ARES on faithfulness | Synthesis; multiple citations |

**Demo flow:**
1. Type query, click "Search & Generate"
2. Show answer with inline citations and ## References
3. Expand sources, show chunk_id and snippets
4. Click "Save as thread"

---

## 3. Threads Page

- Click "Threads" in sidebar
- Confirm saved thread appears
- Expand to show query, answer, retrieved chunks

---

## 4. Artifacts Page

- Click "Artifacts"
- Select the saved thread
- Click "Generate evidence table"
- Show preview (Claim | Evidence | Citation | Confidence | Notes)
- Demo export: Download Markdown, Download CSV, Download HTML
- Mention: open HTML in browser → File → Print → Save as PDF

---

## 5. Evaluation Page

- Click "Evaluation"
- Select `eval_run_20260215_195940.jsonl` (or latest)
- Click "Summarize selected log"
- Show metrics table and representative examples

---

## 6. Trust Behavior

- Ask: "What is the FactCC benchmark and how does it assess factual consistency?"
- If answer says "corpus does not contain evidence" or similar, blue info box appears with suggested keywords (e.g., faithfulness, RAG, benchmark)

---

## Checklist for Demo Recording

- [ ] Ask: show retrieval + cited answer + sources
- [ ] Save as thread
- [ ] Threads: show saved history
- [ ] Artifacts: generate evidence table, export (MD/CSV/HTML)
- [ ] Evaluation: summarize eval log
- [ ] Trust: show suggested keywords when no evidence
- [ ] Total time: 3–6 minutes

# Phase 2 RAG + Phase 3 PRP — Makefile
# One-command run: make query Q="..." (after setup). Full setup: make setup.

.PHONY: install ingest index query dry-run help setup portal

install:
	pip install -r requirements.txt

# Full pipeline: download corpus → ingest → index (run once)
setup: install
	python3 scripts/download_corpus.py
	python3 -m src.ingest.run_ingest
	python3 -m src.rag.build_index

ingest:
	python3 -m src.ingest.run_ingest

index:
	python3 -m src.rag.build_index

# Dry-run: retrieval only, no API key
dry-run:
	python3 -m src.rag.query "$(Q)" --dry-run

# Full RAG (set GROQ_API_KEY in .env)
query:
	python3 -m src.rag.query "$(Q)"

# Run evaluation over query set (23 queries)
eval:
	python3 -m src.eval.run_eval

eval-dry:
	python3 -m src.eval.run_eval --dry-run

# Summarize latest eval run
eval-summary:
	python3 -m src.eval.summarize

# Phase 3: Personal Research Portal
portal:
	streamlit run src/app/main.py

help:
	@echo "Usage:"
	@echo "  make setup       - Install + download corpus + ingest + index (one-time)"
	@echo "  make install    - Install dependencies"
	@echo "  make ingest      - Parse PDFs, create chunks"
	@echo "  make index       - Build FAISS index"
	@echo "  make dry-run Q='your question' - Retrieve only (no API)"
	@echo "  make query Q='your question'   - Full RAG + log (needs API key)"
	@echo "  make eval        - Run 23 queries, log to logs/"
	@echo "  make eval-dry    - Eval dry-run (retrieval only)"
	@echo "  make eval-summary - Summarize latest eval run"
	@echo "  make portal      - Launch Phase 3 Personal Research Portal (Streamlit)"

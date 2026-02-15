# Personal Research Portal (PRP) 

Baseline RAG pipeline over a corpus of papers on Trustworthy RAG Evaluation Methods. Run a query and get a cited answer, or run the full evaluation.

**Corpus & acquisition:** Human-curated list of 18 papers (RAG evaluation, faithfulness metrics, benchmarks); PDFs fetched from arXiv via `scripts/download_corpus.py` and `data/corpus_sources.json`. See `data/data_manifest.csv` for source list.

## How to run (5 min)

**1. Install**
```bash
pip install -r requirements.txt
```

**2. Get data ready** (if not already present)
```bash
python3 scripts/download_corpus.py    # fetches PDFs to data/raw/
python3 -m src.ingest.run_ingest      # parses and chunks → data/processed/
python3 -m src.rag.build_index        # builds FAISS index → index/
```
Or from repo root: `make setup` (install + download + ingest + index).

**3. Get a Groq API key and set .env**
- Go to [Groq Console](https://console.groq.com/), sign up, open **API Keys**, create a key.
- From repo root: `cp .env.example .env`, then edit `.env` and set `GROQ_API_KEY=gsk_your_key_here`.

**4. Run a query**
```bash
make query Q="What does RAGAS measure for faithfulness?"
# or
python3 -m src.rag.query "What does RAGAS measure for faithfulness?"
```
Dry-run (retrieval only, no API key): `python3 -m src.rag.query "Your question" --dry-run`

**5. Run full evaluation** (23 queries)
```bash
make eval
# or
python3 -m src.eval.run_eval
```
Dry-run: `python3 -m src.eval.run_eval --dry-run`

Logs: `logs/eval_run_*.jsonl` (evaluation run; ≥20 queries with retrieved chunks and outputs).


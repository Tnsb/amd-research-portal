#!/usr/bin/env python3
"""
Phase 2 Step 6: Run evaluation over query set.

Runs all queries in src/eval/query_set.csv through the RAG pipeline,
saves outputs to logs/eval_run_*.jsonl, and prints a summary.

Usage:
    python -m src.eval.run_eval [--limit N] [--dry-run]

Options:
    --dry-run  Run retrieval only (no LLM), save chunks per query
    --limit N  Run first N queries only (default: all)
"""
import os

# Reduce log noise: tokenizers fork warning and (optional) HF telemetry
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import argparse
import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass


def load_query_set(path: Path) -> list[dict]:
    """Load query set CSV."""
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", "-m", default="groq", help="LLM provider (groq only)")
    parser.add_argument("--limit", "-n", type=int, default=None, help="Run first N queries only")
    parser.add_argument("--dry-run", action="store_true", help="Retrieval only, no LLM")
    args = parser.parse_args()

    query_set_path = REPO_ROOT / "src" / "eval" / "query_set.csv"
    if not query_set_path.exists():
        print(f"Error: {query_set_path} not found")
        return 1

    queries = load_query_set(query_set_path)
    if args.limit:
        queries = queries[: args.limit]

    # Fail fast if LLM package is missing (avoid 23 "ERROR" runs)
    if not args.dry_run:
        try:
            import groq  # noqa: F401
        except ImportError:
            print("Error: groq not installed. Install with: pip install groq")
            print("Then set GROQ_API_KEY in .env (free key at console.groq.com).")
            return 1

    from src.rag.retrieve import retrieve
    from src.rag.generate import generate_answer
    from src.rag.logger import log_rag_run
    from src.rag.structured_citations import format_answer_with_references

    logs_dir = REPO_ROOT / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = logs_dir / f"eval_run_{run_id}.jsonl"

    print(f"Running {len(queries)} queries (model={args.model}, dry_run={args.dry_run})")
    print(f"Logs: {out_path}\n")

    for i, row in enumerate(queries):
        qid = row["query_id"]
        qtext = row["query_text"]
        qtype = row["query_type"]
        print(f"  [{i+1}/{len(queries)}] {qid} ({qtype})...", end=" ")

        chunks = retrieve(qtext, top_k=5)

        if args.dry_run:
            answer = "[DRY-RUN: no LLM call]"
            entry = {
                "query_id": qid,
                "query_text": qtext,
                "query_type": qtype,
                "retrieved_chunk_ids": [c["chunk_id"] for c in chunks],
                "model_output": answer,
                "dry_run": True,
            }
        else:
            try:
                t0 = time.perf_counter()
                answer = generate_answer(qtext, chunks, model_provider=args.model)
                answer = format_answer_with_references(answer, chunks)
                latency_ms = (time.perf_counter() - t0) * 1000
            except Exception as e:
                answer = f"[ERROR: {e}]"
                latency_ms = None
                print(f"ERROR: {e}")
            log_rag_run(
                query_id=qid,
                query_text=qtext,
                retrieved_chunks=chunks,
                model_output=answer,
                model_name=args.model,
                top_k=5,
                notes=f"eval_{qtype}",
                latency_ms=latency_ms,
            )
            entry = {
                "query_id": qid,
                "query_text": qtext,
                "query_type": qtype,
                "retrieved_chunk_ids": [c["chunk_id"] for c in chunks],
                "model_output": answer[:500] + "..." if len(answer) > 500 else answer,
            }

        with open(out_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        print("OK")

    print("\n" + "=" * 50)
    print(f"Done. {len(queries)} queries → {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

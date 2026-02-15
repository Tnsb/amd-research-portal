#!/usr/bin/env python3
"""
Phase 2 Step 5: Baseline RAG — Query script

Retrieve → Generate → Log. Run a single query and get a cited answer.

Usage:
    python -m src.rag.query "What does RAGAS measure for faithfulness?"
    python -m src.rag.query "What does RAGAS measure?" --top-k 8

Environment:
    GROQ_API_KEY  — get a free key at https://console.groq.com/; set in .env
"""
import os

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

import argparse
import sys
import time
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

from src.rag.retrieve import retrieve
from src.rag.generate import generate_answer
from src.rag.logger import log_rag_run
from src.rag.structured_citations import format_answer_with_references


def run_query(
    query_text: str,
    query_id: Optional[str] = None,
    top_k: int = 5,
    model: str = "groq",
    log: bool = True,
    structured_citations: bool = True,
):
    """Run one RAG query: retrieve, generate, optionally log."""
    query_id = query_id or f"Q_{hash(query_text) % 10000:04d}"

    # Retrieve
    chunks = retrieve(query_text, top_k=top_k)

    # Generate (with latency measurement)
    try:
        t0 = time.perf_counter()
        answer = generate_answer(query_text, chunks, model_provider=model)
        latency_ms = (time.perf_counter() - t0) * 1000
    except ValueError as e:
        if "API" in str(e) or "KEY" in str(e):
            print("Error: GROQ_API_KEY not set. Add it to .env or export it. Get a free key at https://console.groq.com/", file=sys.stderr)
            raise
        raise

    # Structured citations: append reference list from manifest
    if structured_citations:
        answer = format_answer_with_references(answer, chunks)

    # Log (Step 7: includes latency_ms)
    if log:
        log_rag_run(
            query_id=query_id,
            query_text=query_text,
            retrieved_chunks=chunks,
            model_output=answer,
            model_name=model,
            top_k=top_k,
            latency_ms=latency_ms,
        )

    return {
        "query_id": query_id,
        "query": query_text,
        "chunks": chunks,
        "answer": answer,
    }


def main():
    parser = argparse.ArgumentParser(description="Run RAG query")
    parser.add_argument("query", nargs="+", help="Question to ask (words)")
    parser.add_argument("--top-k", "-k", type=int, default=5)
    parser.add_argument("--query-id", help="Query ID for logging")
    parser.add_argument("--no-log", action="store_true", help="Skip logging")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Retrieve only; show chunks, skip LLM call (no API key needed)",
    )
    parser.add_argument(
        "--no-refs",
        action="store_true",
        help="Disable structured citations (reference list)",
    )
    args = parser.parse_args()

    query_text = " ".join(args.query)

    if args.dry_run:
        chunks = retrieve(query_text, top_k=args.top_k)
        print("DRY RUN — Retrieved chunks (no LLM call):")
        for i, c in enumerate(chunks, 1):
            print(f"\n[{i}] {c['chunk_id']} (source={c['source_id']}, score={c['score']:.2f})")
            print(c["text"][:300] + "..." if len(c["text"]) > 300 else c["text"])
        return 0

    result = run_query(
        query_text,
        query_id=args.query_id,
        top_k=args.top_k,
        model="groq",
        log=not args.no_log,
        structured_citations=not args.no_refs,
    )

    print("\n" + "=" * 60)
    print("ANSWER")
    print("=" * 60)
    print(result["answer"])
    print("\n" + "-" * 60)
    print("Retrieved chunks:", [c["chunk_id"] for c in result["chunks"]])
    return 0


if __name__ == "__main__":
    main()

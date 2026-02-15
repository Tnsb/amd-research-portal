"""
Logging for RAG runs: query, retrieved chunks, model output, metadata.

Logs saved to logs/ as JSONL (one JSON object per line).
Phase 2 Step 7: Full logging with latency and timestamp.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = REPO_ROOT / "logs"


def log_rag_run(
    query_id: str,
    query_text: str,
    retrieved_chunks: list[dict],
    model_output: str,
    prompt_id: str = "rag_v1",
    model_name: str = "claude",
    top_k: int = 5,
    notes: Optional[str] = None,
    latency_ms: Optional[float] = None,
    token_count: Optional[int] = None,
) -> Path:
    """
    Append one RAG run to the log file.

    Args:
        query_id: Unique query identifier.
        query_text: The user question.
        retrieved_chunks: List of chunk dicts (chunk_id, source_id, text, score).
        model_output: Generated answer.
        prompt_id: Prompt version identifier.
        model_name: LLM provider/model name.
        top_k: Number of chunks retrieved.
        notes: Optional notes.
        latency_ms: Generation latency in milliseconds (optional).
        token_count: Output token count if available (optional).

    Returns:
        Path to the log file.
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOGS_DIR / "rag_runs.jsonl"

    # Minimal chunk representation for log (avoid storing full text if huge)
    chunk_summary = [
        {"chunk_id": c.get("chunk_id"), "source_id": c.get("source_id"), "score": c.get("score")}
        for c in retrieved_chunks
    ]

    entry = {
        "query_id": query_id,
        "query_text": query_text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "retrieved_chunk_ids": [c.get("chunk_id") for c in retrieved_chunks],
        "retrieved_chunks": chunk_summary,
        "model_output": model_output,
        "prompt_id": prompt_id,
        "model_name": model_name,
        "top_k": top_k,
        "notes": notes,
    }
    if latency_ms is not None:
        entry["latency_ms"] = round(latency_ms, 2)
    if token_count is not None:
        entry["token_count"] = token_count

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return log_path

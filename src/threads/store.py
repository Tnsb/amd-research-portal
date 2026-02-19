"""
Research thread persistence: save and load query + retrieved evidence + answer.

Threads are stored as JSON files in outputs/threads/. File-based storage for MVP.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
THREADS_DIR = REPO_ROOT / "outputs" / "threads"


def _make_thread_id() -> str:
    """Generate a unique thread ID from timestamp."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"T_{ts}"


def _chunk_for_storage(chunk: dict) -> dict:
    """Serialize chunk for storage (full text for evidence table / artifact generation)."""
    return {
        "chunk_id": chunk.get("chunk_id"),
        "source_id": chunk.get("source_id"),
        "text": chunk.get("text", ""),
        "chunk_index": chunk.get("chunk_index"),
        "score": chunk.get("score"),
    }


def save_thread(
    query: str,
    chunks: list[dict],
    answer: str,
    query_id: Optional[str] = None,
    threads_dir: Optional[Path] = None,
) -> dict:
    """
    Save a research thread to disk.

    Args:
        query: The user question.
        chunks: Retrieved chunk dicts (chunk_id, source_id, text, score).
        answer: Generated answer with citations.
        query_id: Optional query identifier.
        threads_dir: Override storage directory.

    Returns:
        The saved thread dict (includes thread_id, timestamp).
    """
    threads_dir = threads_dir or THREADS_DIR
    threads_dir.mkdir(parents=True, exist_ok=True)

    thread_id = _make_thread_id()
    timestamp = datetime.now(timezone.utc).isoformat()

    thread = {
        "thread_id": thread_id,
        "query_id": query_id or f"Q_{hash(query) % 10000:04d}",
        "query": query,
        "retrieved_chunks": [_chunk_for_storage(c) for c in chunks],
        "answer": answer,
        "timestamp": timestamp,
    }

    # Use thread_id for filename (simple, sortable)
    path = threads_dir / f"{thread_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(thread, f, indent=2, ensure_ascii=False)

    return thread


def load_threads(threads_dir: Optional[Path] = None) -> list[dict]:
    """
    Load all saved threads from disk.

    Returns threads sorted by timestamp descending (newest first).
    """
    threads_dir = threads_dir or THREADS_DIR
    if not threads_dir.exists():
        return []

    threads = []
    for path in sorted(threads_dir.glob("T_*.json"), reverse=True):
        try:
            with open(path, encoding="utf-8") as f:
                thread = json.load(f)
            threads.append(thread)
        except (json.JSONDecodeError, OSError):
            continue

    return threads


def load_thread(thread_id: str, threads_dir: Optional[Path] = None) -> Optional[dict]:
    """Load a single thread by ID."""
    threads_dir = threads_dir or THREADS_DIR
    path = threads_dir / f"{thread_id}.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)

"""
Semantic retrieval using FAISS index and sentence-transformers.

Loads index built by build_index.py and provides retrieve() for top-k chunk retrieval.
"""

import json
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
INDEX_DIR = REPO_ROOT / "index"


def load_index(index_dir: Optional[Path] = None) -> tuple:
    """
    Load FAISS index and chunk map.

    Returns:
        (faiss_index, chunk_map, model) or raises if not found.
    """
    index_dir = index_dir or INDEX_DIR
    faiss_path = index_dir / "faiss.index"
    map_path = index_dir / "chunk_map.json"

    if not faiss_path.exists() or not map_path.exists():
        raise FileNotFoundError(
            f"Index not found. Run: python3 -m src.rag.build_index"
        )

    import faiss
    from sentence_transformers import SentenceTransformer

    index = faiss.read_index(str(faiss_path))
    with open(map_path, encoding="utf-8") as f:
        data = json.load(f)
    chunk_map = data["chunks"]
    model_name = data.get("model_name", "all-MiniLM-L6-v2")
    model = SentenceTransformer(model_name)

    return index, chunk_map, model


def retrieve(
    query: str,
    top_k: int = 5,
    index_dir: Optional[Path] = None,
    index=None,
    chunk_map=None,
    model=None,
) -> list[dict]:
    """
    Retrieve top-k chunks for a query.

    Args:
        query: Search query.
        top_k: Number of chunks to return.
        index_dir: Path to index directory (loads fresh if index/chunk_map/model not provided).
        index, chunk_map, model: Pre-loaded objects (optional, for reuse).

    Returns:
        List of dicts with keys: chunk_id, source_id, text, chunk_index, score (L2 distance).
    """
    if index is None or chunk_map is None or model is None:
        index, chunk_map, model = load_index(index_dir)

    query_emb = model.encode([query])
    scores, indices = index.search(query_emb.astype("float32"), min(top_k, len(chunk_map)))

    results = []
    for idx, score in zip(indices[0], scores[0]):
        if idx < 0:
            continue
        c = chunk_map[idx]
        results.append({
            "chunk_id": c["chunk_id"],
            "source_id": c["source_id"],
            "text": c["text"],
            "chunk_index": c["chunk_index"],
            "score": float(score),
        })

    return results

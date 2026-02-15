#!/usr/bin/env python3
"""
Phase 2 Step 4: Embed and Index

Loads chunks from data/processed/chunks.jsonl, embeds with sentence-transformers,
builds FAISS index, and saves:
- index/faiss.index
- index/chunk_map.json (index -> chunk_id, source_id, text for retrieval)

Usage:
    python -m src.rag.build_index

Requires: sentence-transformers, faiss-cpu
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def load_chunks(chunks_path: Path) -> list[dict]:
    """Load chunks from JSONL."""
    chunks = []
    with open(chunks_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


def main():
    chunks_path = REPO_ROOT / "data" / "processed" / "chunks.jsonl"
    index_dir = REPO_ROOT / "index"

    if not chunks_path.exists():
        print(f"Error: {chunks_path} not found. Run ingestion first: python3 -m src.ingest.run_ingest")
        return 1

    chunks = load_chunks(chunks_path)
    if not chunks:
        print("Error: No chunks to index.")
        return 1

    print(f"Loading {len(chunks)} chunks...")
    texts = [c["text"] for c in chunks]

    print("Loading embedding model (all-MiniLM-L6-v2)...")
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("all-MiniLM-L6-v2")
    print("Embedding chunks...")
    embeddings = model.encode(texts, show_progress_bar=True)

    print("Building FAISS index...")
    import faiss

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings.astype("float32"))

    index_dir.mkdir(parents=True, exist_ok=True)

    # Save FAISS index
    faiss_path = index_dir / "faiss.index"
    faiss.write_index(index, str(faiss_path))
    print(f"FAISS index saved: {faiss_path}")

    # Save chunk map: index position -> chunk metadata for retrieval
    chunk_map = [
        {
            "index": i,
            "chunk_id": c["chunk_id"],
            "source_id": c["source_id"],
            "text": c["text"],
            "chunk_index": c["chunk_index"],
        }
        for i, c in enumerate(chunks)
    ]
    map_path = index_dir / "chunk_map.json"
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "model_name": "all-MiniLM-L6-v2",
                "dimension": int(dim),
                "num_chunks": len(chunks),
                "chunks": chunk_map,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"Chunk map saved: {map_path}")

    print("\n" + "=" * 50)
    print(f"Index built: {len(chunks)} chunks, dim={dim}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

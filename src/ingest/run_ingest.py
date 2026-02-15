#!/usr/bin/env python3
"""
Phase 2 Step 3: Ingestion Pipeline

Parses PDFs from data/raw/, cleans text, chunks, and stores:
- Parsed full text: data/processed/{source_id}.txt
- All chunks: data/processed/chunks.jsonl

Usage:
    python -m src.ingest.run_ingest

Requires: pypdf
"""

import csv
import json
import sys
from pathlib import Path

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.ingest.parser import extract_text_from_pdf
from src.ingest.chunker import chunk_text, chunks_to_dicts


def load_manifest(manifest_path: Path) -> list[dict]:
    """Load data manifest CSV."""
    rows = []
    with open(manifest_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def main():
    manifest_path = REPO_ROOT / "data" / "data_manifest.csv"
    raw_dir = REPO_ROOT / "data" / "raw"
    processed_dir = REPO_ROOT / "data" / "processed"

    processed_dir.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest(manifest_path)
    print(f"Processing {len(manifest)} sources from manifest...\n")

    all_chunks = []
    failed = []

    for i, row in enumerate(manifest):
        source_id = row["source_id"]
        raw_path = REPO_ROOT / row["raw_path"].strip()
        processed_path = REPO_ROOT / row["processed_path"].strip()

        print(f"  [{i + 1}/{len(manifest)}] {source_id}...", end=" ")

        try:
            # Parse PDF
            text = extract_text_from_pdf(raw_path)
            if not text or len(text) < 100:
                failed.append((source_id, "Extracted text too short or empty"))
                print("SKIP (text too short)")
                continue

            # Save parsed full text
            processed_path.parent.mkdir(parents=True, exist_ok=True)
            with open(processed_path, "w", encoding="utf-8") as f:
                f.write(text)

            # Chunk
            chunks = chunk_text(text, source_id)
            all_chunks.extend(chunks_to_dicts(chunks))

            print(f"OK ({len(chunks)} chunks)")
        except Exception as e:
            failed.append((source_id, str(e)))
            print(f"FAILED: {e}")

    # Save all chunks to JSONL
    chunks_path = processed_dir / "chunks.jsonl"
    with open(chunks_path, "w", encoding="utf-8") as f:
        for chunk in all_chunks:
            f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

    # Summary
    print("\n" + "=" * 50)
    print(f"Processed: {len(manifest) - len(failed)} / {len(manifest)}")
    print(f"Total chunks: {len(all_chunks)}")
    print(f"Chunks saved: {chunks_path}")

    if failed:
        print(f"\nFailed ({len(failed)}):")
        for sid, err in failed:
            print(f"  - {sid}: {err}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

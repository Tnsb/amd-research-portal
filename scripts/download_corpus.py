#!/usr/bin/env python3
"""
Phase 2 Step 1: Corpus Acquisition Script

Fetches PDFs from arXiv for the corpus defined in data/corpus_sources.json.
Saves PDFs to data/raw/ with naming: {source_id}.pdf

Usage:
    python scripts/download_corpus.py

Requires: requests (pip install requests)
"""

import json
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("Please install requests: pip install requests")
    exit(1)

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
CONFIG_PATH = REPO_ROOT / "data" / "corpus_sources.json"
RAW_DIR = REPO_ROOT / "data" / "raw"

# Rate limiting: be polite to arXiv (1 request per second)
ARXIV_DELAY_SEC = 1.5


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    with open(CONFIG_PATH) as f:
        config = json.load(f)

    sources = config["sources"]
    success = []
    failed = []

    print(f"Fetching {len(sources)} papers from arXiv...")
    print(f"Output directory: {RAW_DIR}\n")

    for i, src in enumerate(sources):
        source_id = src["source_id"]
        arxiv_id = src["arxiv_id"]
        out_path = RAW_DIR / f"{source_id}.pdf"

        if out_path.exists():
            print(f"  [{i+1}/{len(sources)}] {source_id}: already exists, skipping")
            success.append(source_id)
            continue

        url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        try:
            r = requests.get(url, timeout=60, stream=True)
            r.raise_for_status()

            # Check for HTML error page (arXiv sometimes returns 200 with error HTML)
            content_type = r.headers.get("Content-Type", "")
            if "text/html" in content_type and len(r.content) < 5000:
                failed.append((source_id, "Got HTML instead of PDF (paper may not exist)"))
                print(f"  [{i+1}/{len(sources)}] {source_id}: FAILED - not a PDF")
            else:
                with open(out_path, "wb") as f:
                    f.write(r.content)
                success.append(source_id)
                print(f"  [{i+1}/{len(sources)}] {source_id}: saved")
        except requests.RequestException as e:
            failed.append((source_id, str(e)))
            print(f"  [{i+1}/{len(sources)}] {source_id}: FAILED - {e}")

        if i < len(sources) - 1:
            time.sleep(ARXIV_DELAY_SEC)

    # Summary
    print("\n" + "=" * 50)
    print(f"Downloaded: {len(success)} / {len(sources)}")
    if failed:
        print(f"Failed ({len(failed)}):")
        for sid, err in failed:
            print(f"  - {sid}: {err}")
        print("\nFor failed papers: try manual download from https://arxiv.org/abs/<arxiv_id>")
    else:
        print("All papers downloaded successfully.")

    return 0 if not failed else 1


if __name__ == "__main__":
    exit(main())

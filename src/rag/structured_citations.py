"""
Structured citations: inline citations + reference list from manifest.

Phase 2 Step 8 enhancement. Appends a formatted reference list for all
cited/retrieved sources, resolvable via data/data_manifest.csv.
"""

import csv
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = REPO_ROOT / "data" / "data_manifest.csv"


def load_manifest(path: Path | None = None) -> dict[str, dict]:
    """Load manifest as source_id -> row dict."""
    path = path or MANIFEST_PATH
    manifest = {}
    if not path.exists():
        return manifest
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row.get("source_id", "").strip()
            if sid:
                manifest[sid] = row
    return manifest


def extract_cited_sources(text: str) -> set[str]:
    """
    Extract source_ids from inline citations in text.
    Matches (source_id, chunk_id) or (source_id).
    """
    # (SourceID, chunk_xx) or (SourceID)
    pattern = r"\(([A-Za-z0-9_-]+)(?:\s*,\s*[A-Za-z0-9_-]+\s*)?\)"
    matches = re.findall(pattern, text)
    # Filter to likely source_ids (alphanumeric + underscore, often end with year)
    return {m for m in matches if m and len(m) > 2}


def build_reference_list(source_ids: set[str], manifest: dict[str, dict]) -> str:
    """Build formatted reference list from manifest for given source_ids. Skips source_ids not in manifest (e.g. LLM-hallucinated citations)."""
    lines = []
    for sid in sorted(source_ids):
        if sid not in manifest:
            continue
        row = manifest[sid]
        title = row.get("title", "Unknown")
        authors = row.get("authors", "")
        year = row.get("year", "")
        url = row.get("url_or_doi", "")
        venue = row.get("venue", "")
        ref = f"- **{sid}**: {title}. {authors} ({year}). {venue}. {url}"
        lines.append(ref)
    return "\n".join(lines)


def format_answer_with_references(
    answer: str,
    chunks: list[dict],
    manifest_path: Path | None = None,
) -> str:
    """
    Append a reference list to the answer using the data manifest.

    Uses: (1) source_ids extracted from inline citations in answer,
          (2) source_ids from retrieved chunks (fallback for full traceability).
    """
    manifest = load_manifest(manifest_path or MANIFEST_PATH)

    cited = extract_cited_sources(answer)
    from_chunks = {c.get("source_id") for c in chunks if c.get("source_id")}
    source_ids = cited | from_chunks

    if not source_ids:
        return answer

    ref_list = build_reference_list(source_ids, manifest)
    if not ref_list:
        return answer

    # Avoid duplicating if References section already exists
    if "## References" in answer or "**References**" in answer:
        return answer

    return answer.rstrip() + "\n\n## References\n\n" + ref_list

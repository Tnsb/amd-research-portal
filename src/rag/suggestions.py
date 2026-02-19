"""
Suggested next retrieval: when answer says "corpus does not contain evidence",
suggest alternative search terms from corpus tags.
"""

import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = REPO_ROOT / "data" / "data_manifest.csv"


def get_suggested_keywords(limit: int = 8) -> list[str]:
    """
    Extract top tags from data manifest for suggested retrieval keywords.

    Returns a list of distinct tags (e.g. faithfulness, RAG, benchmark, NLI).
    """
    if not MANIFEST_PATH.exists():
        return ["faithfulness", "RAG", "evaluation", "benchmark"]
    tags_seen = set()
    suggested = []
    with open(MANIFEST_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for tag in (row.get("tags") or "").split(";"):
                tag = tag.strip().lower()
                if tag and tag not in tags_seen and len(tag) > 2:
                    tags_seen.add(tag)
                    suggested.append(tag)
                    if len(suggested) >= limit:
                        return suggested
    return suggested or ["faithfulness", "RAG", "evaluation", "benchmark"]


def format_suggestion_message() -> str:
    """Return a trust-behavior message when evidence is missing."""
    keywords = get_suggested_keywords(5)
    kw_str = ", ".join(keywords[:5])
    return (
        "**Suggested next step:** The retrieved passages don't contain evidence. "
        f"Try rephrasing your query or adding related keywords (e.g., {kw_str})."
    )

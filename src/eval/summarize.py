#!/usr/bin/env python3
"""
Phase 3: Summarize evaluation run — compute metrics and representative examples.

Usage:
    python -m src.eval.summarize [log_path]
    python -m src.eval.summarize logs/eval_run_20260215_195940.jsonl

If no path given, uses the most recent eval_run_*.jsonl in logs/.
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def load_eval_log(path: Path) -> list[dict]:
    """Load evaluation log (JSONL)."""
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))
    return entries


def summarize(entries: list[dict]) -> dict:
    """
    Compute summary metrics from eval entries.

    Returns dict with: total, no_evidence_count, error_count, has_citations_count,
    avg_latency_ms, by_type, sample_no_evidence, sample_errors.
    """
    total = len(entries)
    no_evidence = 0
    errors = 0
    has_citations = 0
    latencies = []

    no_evidence_sample = []
    error_sample = []

    for e in entries:
        output = e.get("model_output", "")
        if e.get("dry_run"):
            continue

        if "[ERROR:" in output or output.startswith("[ERROR"):
            errors += 1
            if len(error_sample) < 2:
                error_sample.append(e)
            continue

        if "corpus does not contain evidence" in output.lower() or "no mention" in output.lower():
            no_evidence += 1
            if len(no_evidence_sample) < 3:
                no_evidence_sample.append(e)

        # Citation presence: (source_id, chunk_id) or (source_id)
        if re.search(r"\([A-Za-z0-9_-]+(?:\s*,\s*[A-Za-z0-9_-]+)?\)", output):
            has_citations += 1

        if "latency_ms" in e:
            latencies.append(e["latency_ms"])
        # Some entries might have latency in a different structure

    by_type = {}
    for e in entries:
        t = e.get("query_type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1

    return {
        "total": total,
        "no_evidence_count": no_evidence,
        "error_count": errors,
        "has_citations_count": has_citations,
        "avg_latency_ms": sum(latencies) / len(latencies) if latencies else None,
        "by_type": by_type,
        "sample_no_evidence": no_evidence_sample,
        "sample_errors": error_sample,
    }


def summarize_to_markdown(summary: dict, log_path: Path) -> str:
    """Format summary as Markdown."""
    lines = [
        "# Evaluation Run Summary",
        "",
        f"**Log file:** `{log_path.name}`",
        "",
        "## Metrics",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total queries | {summary['total']} |",
        f"| Answers with citations | {summary['has_citations_count']} ({100*summary['has_citations_count']/summary['total']:.0f}%) |" if summary['total'] else "| Answers with citations | 0 |",
        f"| \"No evidence\" responses | {summary['no_evidence_count']} |",
        f"| Errors | {summary['error_count']} |",
        f"| Avg latency (ms) | {summary['avg_latency_ms']:.0f} |" if summary.get('avg_latency_ms') else "| Avg latency (ms) | N/A |",
        "",
        "## Queries by type",
        "",
    ]
    for qtype, count in sorted(summary.get("by_type", {}).items()):
        lines.append(f"- {qtype}: {count}")
    lines.extend(["", "## Representative examples", ""])

    if summary.get("sample_no_evidence"):
        lines.append("### \"No evidence\" responses")
        for e in summary["sample_no_evidence"][:3]:
            lines.append(f"- **{e.get('query_id')}**: {e.get('query_text', '')[:80]}...")
            lines.append(f"  Retrieved: {e.get('retrieved_chunk_ids', [])[:3]}...")
        lines.append("")

    if summary.get("sample_errors"):
        lines.append("### Errors")
        for e in summary["sample_errors"][:2]:
            lines.append(f"- **{e.get('query_id')}**: {str(e.get('model_output', ''))[:100]}...")
        lines.append("")

    return "\n".join(lines)


def main():
    logs_dir = REPO_ROOT / "logs"
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        paths = sorted(logs_dir.glob("eval_run_*.jsonl"), reverse=True)
        if not paths:
            print("No eval_run_*.jsonl found in logs/")
            return 1
        path = paths[0]

    if not path.exists():
        print(f"File not found: {path}")
        return 1

    entries = load_eval_log(path)
    if not entries:
        print("Empty log file")
        return 1

    summary = summarize(entries)
    md = summarize_to_markdown(summary, path)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())

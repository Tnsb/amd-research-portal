"""
Evidence table artifact: Claim | Evidence snippet | Citation | Confidence | Notes.

Parses a thread's answer for claims and maps them to retrieved chunks.
"""

import csv
import re
from io import StringIO
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Match (source_id, chunk_id) or (source_id)
CITATION_PATTERN = re.compile(
    r"\(([A-Za-z0-9_-]+)(?:\s*,\s*([A-Za-z0-9_-]+)\s*)?\)"
)


def _extract_claims_with_citations(answer: str) -> list[tuple[str, list[tuple[str, str]]]]:
    """
    Split answer into claim segments and extract citations per segment.

    Returns list of (claim_text, [(source_id, chunk_id), ...]).
    Citations like (RAGAS2023, RAGAS2023_chunk_09) or (RAGAS2023).
    """
    # Split on ## References or **References** to exclude reference section
    body = answer
    if "## References" in body:
        body = body.split("## References")[0].strip()
    if "**References**" in body:
        body = body.split("**References**")[0].strip()

    segments = []
    # Split by paragraphs, then by sentences that contain citations
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]

    for para in paragraphs:
        # Find all citation occurrences with their positions
        citations_found = list(CITATION_PATTERN.finditer(para))
        if not citations_found:
            # No citation in this paragraph - treat as one claim with no citation
            if para and not para.startswith("-"):
                segments.append((para, []))
            continue

        # Split paragraph by citations to associate text with citations
        last_end = 0
        for m in citations_found:
            before = para[last_end : m.start()].strip()
            sid = m.group(1)
            cid = m.group(2) or sid  # Use source_id as chunk_id if only (source_id)
            # Prefer chunk_id format: source_id_chunk_XX
            if "_chunk_" in cid or cid == sid:
                chunk_ref = (sid, cid if cid != sid else f"{sid}_chunk_00")
            else:
                chunk_ref = (sid, cid)
            if before:
                segments.append((before, [chunk_ref]))
            else:
                # Citation at start - get text after it
                after_start = m.end()
                next_m = CITATION_PATTERN.search(para, after_start)
                text_after = para[after_start : next_m.start()].strip() if next_m else para[after_start:].strip()
                if text_after:
                    segments.append((text_after, [chunk_ref]))
            last_end = m.end()

        # Remaining text after last citation
        if citations_found and last_end < len(para):
            remaining = para[last_end:].strip()
            if remaining:
                last_cit = citations_found[-1]
                sid = last_cit.group(1)
                cid = last_cit.group(2) or sid
                chunk_ref = (sid, cid if "_chunk_" in cid or cid == sid else f"{sid}_chunk_00")
                segments.append((remaining, [(sid, cid)]))

    return segments


def _get_chunk_text(chunk_id: str, chunks: list[dict]) -> str:
    """Get evidence snippet from chunks by chunk_id."""
    if not chunk_id:
        return ""
    for c in chunks:
        if c.get("chunk_id") == chunk_id:
            text = c.get("text", "")
            return (text[:500] + "...") if len(text) > 500 else text
    # Try partial match (source_id might have been used)
    for c in chunks:
        src = c.get("source_id", "")
        if src and str(chunk_id).startswith(src):
            text = c.get("text", "")
            return (text[:500] + "...") if len(text) > 500 else text
    return ""


def build_evidence_table(
    thread: dict,
    manifest_path: Optional[Path] = None,
) -> list[dict]:
    """
    Build evidence table rows from a research thread.

    Schema: claim, evidence_snippet, citation, confidence, notes

    Args:
        thread: Dict with keys query, answer, retrieved_chunks.
        manifest_path: Optional path to data manifest (for notes).

    Returns:
        List of dicts with keys: claim, evidence_snippet, citation, confidence, notes.
    """
    answer = thread.get("answer", "")
    chunks = thread.get("retrieved_chunks", [])

    rows = []
    segments = _extract_claims_with_citations(answer)

    for claim_text, refs in segments:
        claim_text = claim_text.strip()
        if not claim_text or len(claim_text) < 10:
            continue

        for source_id, chunk_id in refs:
            # Resolve chunk_id (might be source_id only when citation was (source_id))
            has_chunk_ref = chunk_id and chunk_id != source_id and "_chunk_" in str(chunk_id)
            if not has_chunk_ref:
                match = next((c for c in chunks if c.get("source_id") == source_id), None)
                actual_chunk_id = match.get("chunk_id", source_id) if match else source_id
                evidence = match.get("text", "")[:500] if match else ""
                if evidence and len(evidence) > 500:
                    evidence += "..."
            else:
                actual_chunk_id = chunk_id
                evidence = _get_chunk_text(chunk_id, chunks)

            citation = f"({source_id}, {actual_chunk_id})"
            confidence = "high" if evidence else "low"
            notes = "" if evidence else "Chunk not in retrieved set"

            rows.append({
                "claim": claim_text,
                "evidence_snippet": evidence,
                "citation": citation,
                "confidence": confidence,
                "notes": notes,
            })

        # Claims with no citations
        if not refs and claim_text:
            rows.append({
                "claim": claim_text,
                "evidence_snippet": "",
                "citation": "",
                "confidence": "low",
                "notes": "No inline citation",
            })

    return rows


def evidence_table_to_markdown(rows: list[dict]) -> str:
    """Format evidence table as Markdown."""
    if not rows:
        return "No evidence rows extracted."

    def cell(s: str, max_len: int = 200) -> str:
        s = (s or "").replace("|", "\\|").replace("\n", " ")
        return (s[:max_len] + "...") if len(s) > max_len else s

    lines = ["| Claim | Evidence snippet | Citation | Confidence | Notes |", "|-------|------------------|----------|------------|-------|"]
    for r in rows:
        lines.append(f"| {cell(r.get('claim',''), 150)} | {cell(r.get('evidence_snippet',''))} | {r.get('citation','')} | {r.get('confidence','')} | {cell(r.get('notes',''), 80)} |")
    return "\n".join(lines)


def evidence_table_to_csv(rows: list[dict]) -> str:
    """Format evidence table as CSV string."""
    if not rows:
        return "claim,evidence_snippet,citation,confidence,notes"
    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=["claim", "evidence_snippet", "citation", "confidence", "notes"])
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def evidence_table_to_html(rows: list[dict], title: str = "Evidence Table") -> str:
    """Format evidence table as HTML (suitable for browser print → PDF)."""
    if not rows:
        return f"<html><body><h1>{title}</h1><p>No evidence rows.</p></body></html>"

    def esc(s: str) -> str:
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    cells = []
    cells.append("<tr><th>Claim</th><th>Evidence snippet</th><th>Citation</th><th>Confidence</th><th>Notes</th></tr>")
    for r in rows:
        cells.append(
            f"<tr><td>{esc(str(r.get('claim',''))[:200])}</td>"
            f"<td>{esc(str(r.get('evidence_snippet',''))[:300])}</td>"
            f"<td>{esc(r.get('citation',''))}</td>"
            f"<td>{esc(r.get('confidence',''))}</td>"
            f"<td>{esc(str(r.get('notes',''))[:80])}</td></tr>"
        )
    table = "<table border='1' cellpadding='8' style='border-collapse:collapse'>\n" + "\n".join(cells) + "\n</table>"
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{esc(title)}</title></head>
<body>
<h1>{esc(title)}</h1>
{table}
<p><small>Export from Personal Research Portal. Use File → Print → Save as PDF.</small></p>
</body>
</html>"""

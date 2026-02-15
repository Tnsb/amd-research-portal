"""
PDF parser for the ingestion pipeline.

Extracts text from PDFs and applies basic cleaning:
- Normalize whitespace (collapse multiple spaces/newlines)
- Remove common PDF artifacts (page numbers, repeated headers)
- Preserve paragraph structure where possible
"""

import re
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract and clean text from a PDF file.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Cleaned text string. Empty string if extraction fails.
    """
    if PdfReader is None:
        raise ImportError("pypdf is required. Install with: pip install pypdf")

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(str(pdf_path))
    chunks = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            chunks.append(text)

    raw = "\n\n".join(chunks)
    return clean_text(raw)


def clean_text(text: str) -> str:
    """
    Clean extracted PDF text:
    - Normalize Unicode (replace fancy quotes, dashes)
    - Collapse excessive whitespace
    - Remove isolated page numbers (e.g., "3" on its own line)
    - Remove common header/footer patterns
    """
    if not text or not text.strip():
        return ""

    # Normalize common Unicode
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u2013", "-").replace("\u2014", "-")

    # Collapse multiple newlines to double newline (paragraph break)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse multiple spaces
    text = re.sub(r" +", " ", text)

    # Remove isolated page numbers (standalone digits, possibly with spaces)
    text = re.sub(r"\n\s*\d+\s*\n", "\n", text)

    # Remove common arXiv header/footer lines
    text = re.sub(r"\narxiv\.org.*\n", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"\n\s*page \d+ of \d+\s*\n", "\n", text, flags=re.IGNORECASE)

    # Strip per-line and overall
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(line for line in lines if line)

    return text.strip()

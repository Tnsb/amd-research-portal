"""
Chunking strategy for the ingestion pipeline.

STRATEGY (documented for reproducibility):
- Chunk size: ~512 tokens (approximated as 400 words; ~1.3 tokens/word)
- Overlap: 50 tokens (approximated as 40 words)
- Unit: word-based sliding window (preserves sentence boundaries where possible)
- Chunk ID format: {source_id}_chunk_{idx:02d} (e.g., RAGAS2023_chunk_00)

Rationale:
- 512 tokens fits typical embedding model context and LLM attention
- Overlap reduces boundary effects (split concepts at edges)
- Word-based is simple, reproducible, and avoids tokenizer dependency
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass
class Chunk:
    """A single text chunk with citation metadata."""

    chunk_id: str
    source_id: str
    text: str
    chunk_index: int
    metadata: dict


# Chunking parameters (documented)
CHUNK_SIZE_WORDS = 400
OVERLAP_WORDS = 40


def chunk_text(
    text: str,
    source_id: str,
    chunk_size: int = CHUNK_SIZE_WORDS,
    overlap: int = OVERLAP_WORDS,
) -> list[Chunk]:
    """
    Split text into overlapping chunks.

    Args:
        text: Full document text.
        source_id: Source identifier (e.g., RAGAS2023).
        chunk_size: Target words per chunk (~512 tokens).
        overlap: Overlap in words between consecutive chunks.

    Returns:
        List of Chunk objects with chunk_id, source_id, text, chunk_index, metadata.
    """
    words = text.split()
    if len(words) <= chunk_size:
        chunk_id = f"{source_id}_chunk_00"
        return [
            Chunk(
                chunk_id=chunk_id,
                source_id=source_id,
                text=text.strip(),
                chunk_index=0,
                metadata={"word_count": len(words), "total_chunks": 1},
            )
        ]

    chunks = []
    step = chunk_size - overlap
    idx = 0
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunk_text_str = " ".join(chunk_words)

        chunk_id = f"{source_id}_chunk_{idx:02d}"
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                source_id=source_id,
                text=chunk_text_str,
                chunk_index=idx,
                metadata={
                    "word_count": len(chunk_words),
                    "start_word": start,
                    "end_word": end,
                },
            )
        )
        idx += 1
        start += step
        if start >= len(words):
            break

    # Update total_chunks in metadata
    for c in chunks:
        c.metadata["total_chunks"] = len(chunks)

    return chunks


def chunks_to_dicts(chunks: list[Chunk]) -> list[dict]:
    """Convert Chunk objects to JSON-serializable dicts."""
    return [
        {
            "chunk_id": c.chunk_id,
            "source_id": c.source_id,
            "text": c.text,
            "chunk_index": c.chunk_index,
            "metadata": c.metadata,
        }
        for c in chunks
    ]

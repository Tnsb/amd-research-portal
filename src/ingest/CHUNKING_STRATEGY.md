# Chunking Strategy (Phase 2 Step 3)

## Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Chunk size | 400 words (~512 tokens) | Fits embedding models and LLM context; 1 word ≈ 1.3 tokens |
| Overlap | 40 words (~50 tokens) | Reduces boundary effects; avoids splitting concepts |
| Unit | Word-based sliding window | Reproducible without tokenizer dependency |

## Chunk ID Convention

Format: `{source_id}_chunk_{idx:02d}`

Examples: `RAGAS2023_chunk_00`, `ARES2023_chunk_14`

For citations: Use `(source_id, chunk_id)` or `(source_id)` — both resolve via the data manifest.

## Output

- **Parsed text:** `data/processed/{source_id}.txt` — full extracted text per source
- **Chunks:** `data/processed/chunks.jsonl` — one JSON object per line:

```json
{
  "chunk_id": "RAGAS2023_chunk_00",
  "source_id": "RAGAS2023",
  "text": "...",
  "chunk_index": 0,
  "metadata": {"word_count": 400, "start_word": 0, "end_word": 400, "total_chunks": 14}
}
```

## Section-aware chunking (if feasible)

Section-aware chunking for papers (e.g. split by headings/sections) is **not** implemented. Current strategy is document-level word-based sliding window. Papers often have clear section boundaries; a future improvement could parse PDF structure or use heading heuristics to avoid splitting mid-section. For this phase, fixed size + overlap is used for simplicity and reproducibility.

## Re-run

```bash
python3 -m src.ingest.run_ingest
```

From repo root. Overwrites `data/processed/*.txt` and `chunks.jsonl`.

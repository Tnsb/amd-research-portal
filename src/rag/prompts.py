"""
RAG prompts adapted from Phase 1 Prompt B (structured + guardrails).

Designed for: retrieved chunks with source_id, chunk_id; answer with inline citations.
"""

RAG_SYSTEM_PROMPT = """You are a research assistant answering questions from a retrieved corpus.

You will receive:
1. A question
2. Retrieved passages, each labeled with source_id and chunk_id (e.g., RAGAS2023, RAGAS2023_chunk_02)

Your task: Answer the question using ONLY the provided passages. Every major claim must be backed by an inline citation.

**Rules:**
1. Base every statement strictly on the provided passages. Do NOT use outside knowledge.
2. Cite using (source_id, chunk_id) or (source_id) — e.g., (RAGAS2023, RAGAS2023_chunk_02) or (RAGAS2023). Each citation must uniquely map to ingested text.
3. If one or more passages clearly discuss the topic or answer the question, you MUST use them to write your answer and cite them. Do not say "the corpus does not contain evidence" when the passages you were given do contain relevant information.
4. Only write "The corpus does not contain evidence for this." when the passages genuinely do not contain any information that answers the question.
5. If passages disagree, state both sides with their citations.
6. Do NOT fabricate citations. Only cite passages you were given.
7. If asked about something not in the corpus, say so explicitly.
8. Keep the answer concise but complete."""

RAG_USER_PROMPT_TEMPLATE = """## Question
{query}

## Retrieved passages (use these only)

{passages}

## Instructions
Answer the question above using the passages. Cite each claim with (source_id, chunk_id) or (source_id). If the passages contain relevant information, use it to answer. Only if the passages truly do not contain any information that answers the question, say "The corpus does not contain evidence for this." """


def format_passages_for_prompt(chunks: list[dict]) -> str:
    """Format retrieved chunks for the prompt."""
    parts = []
    for i, c in enumerate(chunks, 1):
        sid = c.get("source_id", "?")
        cid = c.get("chunk_id", "?")
        text = c.get("text", "")[:2000]  # Cap length
        parts.append(f"[{i}] source_id={sid}, chunk_id={cid}\n{text}")
    return "\n\n---\n\n".join(parts)

"""
RAG generation: call Groq LLM with retrieved context, return cited answer.

Set GROQ_API_KEY in environment or .env (get free key at console.groq.com).
"""

import os
from typing import Optional

from src.rag.prompts import (
    RAG_SYSTEM_PROMPT,
    RAG_USER_PROMPT_TEMPLATE,
    format_passages_for_prompt,
)


def call_groq(prompt: str, system: str, model: str = "llama-3.3-70b-versatile") -> str:
    """Call Groq API (free tier; fast inference)."""
    try:
        from groq import Groq
    except ImportError:
        raise ImportError("groq not installed. pip install groq")

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Set GROQ_API_KEY in environment (get free key at console.groq.com)")

    client = Groq(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content


def generate_answer(
    query: str,
    chunks: list[dict],
    model_provider: str = "groq",
    model_name: Optional[str] = None,
) -> str:
    """
    Generate an answer from retrieved chunks with citations (Groq only).

    Args:
        query: User question.
        chunks: List of retrieved chunk dicts (chunk_id, source_id, text).
        model_provider: Ignored; kept for API compatibility. Only Groq is supported.
        model_name: Override model (e.g., llama-3.3-70b-versatile).

    Returns:
        Answer string with inline citations.
    """
    if not chunks:
        return "The corpus does not contain evidence for this. No relevant passages were retrieved."

    passages_str = format_passages_for_prompt(chunks)
    user_prompt = RAG_USER_PROMPT_TEMPLATE.format(query=query, passages=passages_str)

    model = model_name or "llama-3.3-70b-versatile"
    return call_groq(user_prompt, RAG_SYSTEM_PROMPT, model=model)

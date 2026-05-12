"""pgvector-backed retrieval for lineage Q&A and rationale grounding."""

from __future__ import annotations


def retrieve_context(query: str, top_k: int = 5) -> list[dict]:
    """Retrieve relevant records/notes for RAG grounding."""
    raise NotImplementedError("Week 3 — implement after embeddings are stored")

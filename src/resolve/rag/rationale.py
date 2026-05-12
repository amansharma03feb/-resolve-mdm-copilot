"""LLM rationale generation — explain why two records match or don't."""

from __future__ import annotations


def generate_rationale(record_a: dict, record_b: dict, context: list[dict]) -> str:
    """Generate plain-English merge rationale grounded in retrieved evidence."""
    raise NotImplementedError("Week 3 — implement after retriever is working")

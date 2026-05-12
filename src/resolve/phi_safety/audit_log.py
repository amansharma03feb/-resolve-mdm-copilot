"""Audit log for PHI — track what was sent to external LLMs and what was redacted."""

from __future__ import annotations


def log_llm_call(prompt: str, redacted_prompt: str, response: str, model: str) -> None:
    """Record an LLM call with both redacted and original forms."""
    raise NotImplementedError("Week 3 — implement audit logging to Supabase")

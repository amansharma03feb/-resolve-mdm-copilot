"""PHI redaction — NER-based masking before any external LLM call."""

from __future__ import annotations


def redact_phi(text: str) -> tuple[str, dict]:
    """Replace PHI tokens with placeholders. Returns (redacted_text, mapping)."""
    raise NotImplementedError("Week 3 — implement NER-based redaction")


def restore_phi(redacted_text: str, mapping: dict) -> str:
    """Re-insert original PHI tokens from the mapping."""
    raise NotImplementedError("Week 3 — implement after redactor works")

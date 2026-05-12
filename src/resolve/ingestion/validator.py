"""Schema validation and data-quality checks on ingested records."""

from __future__ import annotations


def validate_patient_row(row: dict) -> list[str]:
    """Return a list of validation errors (empty if clean)."""
    raise NotImplementedError("Week 1 — implement validation rules")

"""Blocking strategies to reduce candidate pair space before scoring."""

from __future__ import annotations


def generate_candidate_pairs(table: str = "raw.synthea_patients") -> list[tuple[str, str]]:
    """Generate candidate duplicate pairs using blocking keys."""
    raise NotImplementedError("Week 2 — implement blocking logic")

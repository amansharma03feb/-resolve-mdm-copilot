"""Probabilistic match scoring — Jaro-Winkler, Soundex, composite weights."""

from __future__ import annotations


def composite_score(record_a: dict, record_b: dict) -> float:
    """Compute weighted match score between two patient records."""
    raise NotImplementedError("Week 2 — implement after duplicate pairs are generated")

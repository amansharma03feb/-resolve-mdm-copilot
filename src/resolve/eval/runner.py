"""Nightly eval runner — score rationale quality against golden set."""

from __future__ import annotations


def run_eval(golden_set_path: str = "eval/golden_set/golden_100.csv") -> dict:
    """Run Ragas + custom metrics on the golden set. Returns metric dict."""
    raise NotImplementedError("Week 5 — implement after rationale pipeline is complete")

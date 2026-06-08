"""Ops Q&A evaluation harness for Verify.

Loads ops_qa_golden_set.csv, runs the Ops Q&A chain per question,
computes proxy metrics (answer relevancy, citation validity, confidence
calibration), saves results to eval/results/ops_qa_run_<timestamp>.json.
"""

from __future__ import annotations

import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()

from src.resolve.rag.lineage_qa import answer_ops_question

GOLDEN_SET = Path(__file__).resolve().parent / "ops_qa_golden_set.csv"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def load_golden_set() -> list[dict]:
    with open(GOLDEN_SET, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def evaluate_question(case: dict) -> dict:
    start = time.time()
    try:
        answer, notes = answer_ops_question(case["question"], top_k=5, rerank=True)
        latency = time.time() - start

        expected_action = case.get("expected_action_filter", "")
        action_relevant = any(
            n.get("action", "").upper() == expected_action.upper()
            for n in notes
        ) if expected_action else None

        return {
            "question_id": case["question_id"],
            "question": case["question"],
            "category": case.get("category", ""),
            "expected_answer_summary": case["expected_answer_summary"],
            "predicted_answer": answer.answer_text,
            "predicted_confidence": answer.confidence,
            "cited_note_ids": answer.cited_evidence_ids,
            "notes_retrieved": len(notes),
            "retrieved_actions": [n.get("action", "") for n in notes],
            "context_has_relevant_action": action_relevant,
            "latency_s": round(latency, 3),
            "error": None,
        }
    except Exception as e:
        latency = time.time() - start
        return {
            "question_id": case["question_id"],
            "question": case["question"],
            "category": case.get("category", ""),
            "expected_answer_summary": case["expected_answer_summary"],
            "predicted_answer": str(e),
            "predicted_confidence": 0,
            "cited_note_ids": [],
            "notes_retrieved": 0,
            "retrieved_actions": [],
            "context_has_relevant_action": None,
            "latency_s": round(latency, 3),
            "error": str(e),
        }


def compute_metrics(results: list[dict]) -> dict:
    total = len(results)
    errors = sum(1 for r in results if r["error"])
    valid = [r for r in results if not r["error"]]

    if not valid:
        return {"total": total, "errors": errors}

    avg_confidence = sum(r["predicted_confidence"] for r in valid) / len(valid)
    avg_citations = sum(len(r["cited_note_ids"]) for r in valid) / len(valid)
    avg_notes = sum(r["notes_retrieved"] for r in valid) / len(valid)
    avg_latency = sum(r["latency_s"] for r in valid) / len(valid)

    action_checks = [r for r in valid if r["context_has_relevant_action"] is not None]
    context_precision = (
        sum(1 for r in action_checks if r["context_has_relevant_action"]) / len(action_checks)
        if action_checks else None
    )

    by_category = {}
    for r in valid:
        cat = r.get("category", "unknown")
        by_category.setdefault(cat, []).append(r)

    category_metrics = {}
    for cat, cases in by_category.items():
        category_metrics[cat] = {
            "count": len(cases),
            "avg_confidence": round(sum(c["predicted_confidence"] for c in cases) / len(cases), 4),
            "avg_citations": round(sum(len(c["cited_note_ids"]) for c in cases) / len(cases), 2),
        }

    return {
        "total_questions": total,
        "valid_questions": len(valid),
        "errors": errors,
        "avg_confidence": round(avg_confidence, 4),
        "avg_citations_per_answer": round(avg_citations, 2),
        "avg_notes_retrieved": round(avg_notes, 2),
        "context_precision": round(context_precision, 4) if context_precision is not None else None,
        "avg_latency_s": round(avg_latency, 3),
        "category_metrics": category_metrics,
    }


def main():
    print("=" * 60)
    print("Verify — Ops Q&A Evaluation Harness")
    print("=" * 60)

    cases = load_golden_set()
    print(f"\nLoaded {len(cases)} Ops Q&A golden-set questions")

    results = []
    for i, case in enumerate(cases, 1):
        print(f"  [{i:3d}/{len(cases)}] {case['question_id']} — {case['category']}", end=" ... ", flush=True)
        result = evaluate_question(case)
        status = "✓" if not result["error"] else "✗"
        print(f"{status} conf={result['predicted_confidence']:.2f} citations={len(result['cited_note_ids'])} ({result['latency_s']:.1f}s)")
        results.append(result)

    metrics = compute_metrics(results)

    print("\n" + "=" * 60)
    print("OPS Q&A EVALUATION RESULTS")
    print("=" * 60)
    print(f"  Avg Confidence:         {metrics.get('avg_confidence', 0):.3f}")
    print(f"  Context Precision:      {metrics.get('context_precision', 'N/A')}")
    print(f"  Avg Citations/Answer:   {metrics.get('avg_citations_per_answer', 0):.1f}")
    print(f"  Avg Notes Retrieved:    {metrics.get('avg_notes_retrieved', 0):.1f}")
    print(f"  Avg Latency:            {metrics.get('avg_latency_s', 0):.2f}s")
    print(f"  Errors:                 {metrics.get('errors', 0)}")

    if metrics.get("category_metrics"):
        print(f"\n  Per-Category:")
        for cat, m in metrics["category_metrics"].items():
            print(f"    {cat:25s}: n={m['count']} conf={m['avg_confidence']:.3f} cites={m['avg_citations']:.1f}")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    summary = {
        "run_id": run_id,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "chain": "ops_qa",
        "metrics": metrics,
        "question_results": results,
    }
    out_path = RESULTS_DIR / f"ops_qa_run_{run_id}.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\n  ✓ JSON saved to {out_path}")

    print("\nDone.")
    return metrics


if __name__ == "__main__":
    main()

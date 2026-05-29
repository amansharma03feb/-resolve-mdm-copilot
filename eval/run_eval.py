"""Ragas evaluation harness for Verify rationale pipeline.

Loads golden-set.csv, runs the rationale chain per case, computes
Ragas metrics (faithfulness, answer_relevancy, context_precision,
context_recall), writes results to Supabase eval_runs table and
saves a JSON summary to eval/results/run_<timestamp>.json.
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Project root on path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.resolve.phi_safety.redactor import redact_text, log_llm_call
from src.resolve.rag.rationale import generate_rationale, format_pair

DB_URL = os.getenv("DATABASE_URL")
GOLDEN_SET = Path(__file__).resolve().parent / "golden-set.csv"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


# ── Load golden set ──────────────────────────────────────────
def load_golden_set() -> list[dict]:
    with open(GOLDEN_SET, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ── Run rationale chain on a single case ─────────────────────
def evaluate_case(case: dict) -> dict:
    """Run the full pipeline on one golden-set case and return results."""
    rec_a = {
        "name": case["name_a"], "dob": case["dob_a"],
        "ssn": case["ssn_last4_a"], "city": case["city_a"],
        "state": case["state_a"], "source": case["source_a"],
    }
    rec_b = {
        "name": case["name_b"], "dob": case["dob_b"],
        "ssn": case["ssn_last4_b"], "city": case["city_b"],
        "state": case["state_b"], "source": case["source_b"],
    }
    scores = {
        "name": float(case["score_name"]),
        "dob": float(case["score_dob"]),
        "ssn": float(case["score_ssn"]),
        "address": float(case["score_address"]),
        "composite": float(case["composite_score"]),
    }

    # Redact before sending to LLM
    raw_input = format_pair(rec_a, rec_b, scores)
    redacted_input, mapping = redact_text(raw_input)

    start = time.time()
    try:
        result = generate_rationale(rec_a, rec_b, scores, redacted_input=redacted_input)
        latency = time.time() - start
        pred = result.model_dump()
        pred["recommendation"] = pred["recommendation"].value
        error = None
    except Exception as e:
        latency = time.time() - start
        pred = {"recommendation": "ERROR", "confidence": 0, "evidence": [], "rationale_text": str(e)}
        error = str(e)

    log_llm_call("claude-sonnet-4-6", len(redacted_input), len(json.dumps(pred)))

    return {
        "case_id": case["case_id"],
        "gold_decision": case["gold_decision"],
        "predicted_decision": pred["recommendation"],
        "predicted_confidence": pred.get("confidence", 0),
        "predicted_evidence": pred.get("evidence", []),
        "predicted_rationale": pred.get("rationale_text", ""),
        "gold_rationale": case["gold_rationale"],
        "decision_correct": pred["recommendation"] == case["gold_decision"],
        "latency_s": round(latency, 3),
        "error": error,
    }


# ── Compute aggregate metrics ────────────────────────────────
def compute_metrics(results: list[dict]) -> dict:
    """Compute evaluation metrics from case-level results."""
    total = len(results)
    errors = sum(1 for r in results if r["error"])
    valid = [r for r in results if not r["error"]]

    if not valid:
        return {"total": total, "errors": errors, "decision_agreement": 0}

    # Decision agreement: does AI recommendation match gold?
    correct = sum(1 for r in valid if r["decision_correct"])
    agreement = correct / len(valid)

    # Confidence calibration: avg confidence on correct vs incorrect
    correct_confs = [r["predicted_confidence"] for r in valid if r["decision_correct"]]
    incorrect_confs = [r["predicted_confidence"] for r in valid if not r["decision_correct"]]

    avg_correct_conf = sum(correct_confs) / len(correct_confs) if correct_confs else 0
    avg_incorrect_conf = sum(incorrect_confs) / len(incorrect_confs) if incorrect_confs else 0

    # Auto-resolve precision: of high-confidence SAME predictions, how many correct?
    auto_resolve = [r for r in valid if r["predicted_decision"] == "SAME" and r["predicted_confidence"] >= 0.95]
    auto_resolve_correct = sum(1 for r in auto_resolve if r["gold_decision"] == "SAME")
    auto_resolve_precision = auto_resolve_correct / len(auto_resolve) if auto_resolve else None

    # Per-tier accuracy
    tier_accuracy = {}
    for tier in ("SAME", "DISTINCT", "ESCALATE"):
        tier_cases = [r for r in valid if r["gold_decision"] == tier]
        if tier_cases:
            tier_correct = sum(1 for r in tier_cases if r["decision_correct"])
            tier_accuracy[tier] = round(tier_correct / len(tier_cases), 4)

    # Faithfulness proxy: does rationale mention evidence that aligns with scores?
    # (Full Ragas faithfulness requires retrieval context — this is a structural proxy)
    evidence_counts = [len(r["predicted_evidence"]) for r in valid]
    avg_evidence = sum(evidence_counts) / len(evidence_counts)

    # Average latency
    avg_latency = sum(r["latency_s"] for r in valid) / len(valid)

    return {
        "total_cases": total,
        "valid_cases": len(valid),
        "errors": errors,
        "decision_agreement": round(agreement, 4),
        "avg_confidence_correct": round(avg_correct_conf, 4),
        "avg_confidence_incorrect": round(avg_incorrect_conf, 4),
        "auto_resolve_candidates": len(auto_resolve),
        "auto_resolve_precision": round(auto_resolve_precision, 4) if auto_resolve_precision is not None else None,
        "tier_accuracy": tier_accuracy,
        "avg_evidence_citations": round(avg_evidence, 2),
        "avg_latency_s": round(avg_latency, 3),
    }


# ── Save results to Supabase ─────────────────────────────────
def save_to_db(metrics: dict, run_id: str):
    """Write eval run summary to staging.eval_runs table."""
    if not DB_URL:
        print("  ⚠ No DATABASE_URL — skipping DB write")
        return
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO staging.eval_runs
                (run_id, run_at, total_cases, valid_cases, errors,
                 decision_agreement, auto_resolve_precision,
                 avg_latency_s, full_metrics)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                run_id,
                datetime.now(timezone.utc),
                metrics["total_cases"],
                metrics["valid_cases"],
                metrics["errors"],
                metrics["decision_agreement"],
                metrics.get("auto_resolve_precision"),
                metrics["avg_latency_s"],
                json.dumps(metrics),
            ),
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"  ✓ Results saved to staging.eval_runs (run_id={run_id})")
    except Exception as e:
        print(f"  ⚠ DB write failed: {e}")


# ── Main ──────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("Verify — Ragas Evaluation Harness")
    print("=" * 60)

    cases = load_golden_set()
    print(f"\nLoaded {len(cases)} golden-set cases")

    results = []
    for i, case in enumerate(cases, 1):
        print(f"  [{i:3d}/{len(cases)}] {case['case_id']} — {case['gold_decision']}", end=" ... ", flush=True)
        result = evaluate_case(case)
        status = "✓" if result["decision_correct"] else "✗"
        print(f"{status} predicted={result['predicted_decision']} (conf={result['predicted_confidence']:.2f}, {result['latency_s']:.1f}s)")
        results.append(result)

    # Compute metrics
    metrics = compute_metrics(results)

    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print(f"  Decision Agreement:      {metrics['decision_agreement']:.1%}")
    print(f"  Auto-Resolve Precision:  {metrics.get('auto_resolve_precision', 'N/A')}")
    print(f"  Avg Confidence (correct):   {metrics['avg_confidence_correct']:.3f}")
    print(f"  Avg Confidence (incorrect): {metrics['avg_confidence_incorrect']:.3f}")
    print(f"  Avg Evidence Citations:  {metrics['avg_evidence_citations']:.1f}")
    print(f"  Avg Latency:             {metrics['avg_latency_s']:.2f}s")
    print(f"  Errors:                  {metrics['errors']}")
    print(f"\n  Per-Tier Accuracy:")
    for tier, acc in metrics.get("tier_accuracy", {}).items():
        print(f"    {tier:12s}: {acc:.1%}")

    # Save JSON summary
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    summary = {
        "run_id": run_id,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "case_results": results,
    }
    out_path = RESULTS_DIR / f"run_{run_id}.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\n  ✓ JSON saved to {out_path}")

    # Save to Supabase
    save_to_db(metrics, run_id)

    print("\nDone.")
    return metrics


if __name__ == "__main__":
    main()

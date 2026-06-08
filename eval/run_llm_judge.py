"""LLM-as-judge evaluation: GPT-4o judges Claude's rationale quality.

Reads the latest rationale eval run, sends each case to GPT-4o with a structured
rubric, scores correctness/evidence-grounding/clarity, and saves results.

Requires OPENAI_API_KEY in .env. Falls back to Claude as judge if no OpenAI key.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

RESULTS_DIR = Path(__file__).resolve().parent / "results"

JUDGE_RUBRIC = """You are an expert evaluator for an AI decision-review system in healthcare MDM (Master Data Management). You will judge the quality of an AI-generated rationale for whether two patient records refer to the same person.

## Scoring rubric (1-5 scale for each dimension)

### Correctness (does the recommendation match the evidence?)
5: Recommendation is clearly correct given the scores and data
4: Recommendation is reasonable, minor quibble possible
3: Recommendation is debatable — could go either way
2: Recommendation seems wrong given the evidence
1: Recommendation directly contradicts the evidence

### Evidence grounding (does the rationale cite actual data?)
5: Every claim is backed by specific scores/attributes from the input
4: Most claims grounded, one minor unsupported assertion
3: Mix of grounded and speculative claims
2: Mostly speculative, few specific citations
1: No connection to the provided data

### Plain-English clarity (would a non-technical reviewer understand?)
5: Clear, concise, actionable — a reviewer could act on this immediately
4: Mostly clear, minor jargon or awkward phrasing
3: Understandable but requires re-reading
2: Confusing or overly technical
1: Incomprehensible

Respond with valid JSON:
{
  "correctness": int 1-5,
  "evidence_grounding": int 1-5,
  "clarity": int 1-5,
  "overall_pass": boolean (true if all scores >= 4),
  "feedback": "one sentence of constructive feedback"
}"""


def build_judge_prompt(case: dict) -> str:
    return f"""## Case: {case['case_id']}
Gold decision: {case['gold_decision']}

## AI Output
Recommendation: {case['predicted_decision']}
Confidence: {case['predicted_confidence']}
Evidence: {json.dumps(case['predicted_evidence'])}
Rationale: {case['predicted_rationale']}

## Gold rationale (for reference)
{case['gold_rationale']}

Score this AI output using the rubric. Respond with JSON only."""


def judge_with_openai(prompt: str) -> dict:
    from openai import OpenAI

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": JUDGE_RUBRIC},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=256,
    )
    raw = response.choices[0].message.content
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def judge_with_claude(prompt: str) -> dict:
    from anthropic import Anthropic

    client = Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        system=JUDGE_RUBRIC,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def find_latest_run() -> Path:
    runs = sorted(RESULTS_DIR.glob("run_*.json"), key=lambda p: p.name, reverse=True)
    if not runs:
        print("ERROR: No eval run results found")
        sys.exit(1)
    return runs[0]


def main():
    openai_key = os.getenv("OPENAI_API_KEY")
    judge_model = "gpt-4o" if openai_key else "claude-sonnet-4-6 (self-eval fallback)"
    judge_fn = judge_with_openai if openai_key else judge_with_claude

    if not openai_key:
        print("  WARNING: No OPENAI_API_KEY — using Claude as fallback judge (self-eval)")
        print("  For cross-model judging, add OPENAI_API_KEY to .env\n")

    run_path = find_latest_run()
    run_data = json.load(open(run_path))

    print("=" * 60)
    print(f"Verify — LLM-as-Judge Evaluation")
    print(f"  Judge model: {judge_model}")
    print(f"  Source run:  {run_path.name}")
    print("=" * 60)

    cases = run_data["case_results"]
    valid_cases = [c for c in cases if not c.get("error")]
    print(f"\nJudging {len(valid_cases)} valid cases...")

    results = []
    for i, case in enumerate(valid_cases, 1):
        print(f"  [{i:3d}/{len(valid_cases)}] {case['case_id']}", end=" ... ", flush=True)
        prompt = build_judge_prompt(case)
        try:
            scores = judge_fn(prompt)
            scores["case_id"] = case["case_id"]
            scores["decision_correct"] = case["decision_correct"]
            print(f"C={scores['correctness']} E={scores['evidence_grounding']} "
                  f"Cl={scores['clarity']} {'PASS' if scores.get('overall_pass') else 'FAIL'}")
        except Exception as e:
            scores = {
                "case_id": case["case_id"],
                "correctness": 0,
                "evidence_grounding": 0,
                "clarity": 0,
                "overall_pass": False,
                "feedback": f"Judge error: {e}",
                "decision_correct": case["decision_correct"],
            }
            print(f"ERROR: {e}")
        results.append(scores)
        time.sleep(0.5)

    # Compute aggregate metrics
    valid_scores = [r for r in results if r["correctness"] > 0]
    n = len(valid_scores)
    if n == 0:
        print("\nNo valid scores — check API keys.")
        return

    avg_correctness = sum(r["correctness"] for r in valid_scores) / n
    avg_grounding = sum(r["evidence_grounding"] for r in valid_scores) / n
    avg_clarity = sum(r["clarity"] for r in valid_scores) / n
    pass_rate = sum(1 for r in valid_scores if r["overall_pass"]) / n
    hallucination_proxy = sum(1 for r in valid_scores if r["evidence_grounding"] <= 2) / n

    metrics = {
        "judge_model": judge_model,
        "cases_judged": n,
        "avg_correctness": round(avg_correctness, 3),
        "avg_evidence_grounding": round(avg_grounding, 3),
        "avg_clarity": round(avg_clarity, 3),
        "pass_rate": round(pass_rate, 4),
        "hallucination_rate": round(hallucination_proxy, 4),
    }

    print("\n" + "=" * 60)
    print("LLM-AS-JUDGE RESULTS")
    print("=" * 60)
    print(f"  Judge model:          {judge_model}")
    print(f"  Cases judged:         {n}")
    print(f"  Avg Correctness:      {avg_correctness:.2f}/5")
    print(f"  Avg Evidence Ground.: {avg_grounding:.2f}/5")
    print(f"  Avg Clarity:          {avg_clarity:.2f}/5")
    print(f"  Overall Pass Rate:    {pass_rate:.1%}")
    print(f"  Hallucination Rate:   {hallucination_proxy:.1%}")

    # Check targets
    print(f"\n  TARGETS:")
    print(f"  Faithfulness >= 0.85:        {'MET' if avg_grounding / 5 >= 0.85 else 'NOT MET'} ({avg_grounding/5:.2f})")
    print(f"  Agreement >= 85%:            {'MET' if run_data['metrics']['decision_agreement'] >= 0.85 else 'NOT MET'} ({run_data['metrics']['decision_agreement']:.1%})")
    print(f"  Hallucination < 5%:          {'MET' if hallucination_proxy < 0.05 else 'NOT MET'} ({hallucination_proxy:.1%})")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    summary = {
        "run_id": run_id,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "source_run": run_data["run_id"],
        "metrics": metrics,
        "targets": {
            "faithfulness_met": avg_grounding / 5 >= 0.85,
            "agreement_met": run_data["metrics"]["decision_agreement"] >= 0.85,
            "hallucination_met": hallucination_proxy < 0.05,
        },
        "case_scores": results,
    }
    out_path = RESULTS_DIR / f"judge_run_{run_id}.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\n  JSON saved to {out_path}")

    print("\nDone.")
    return metrics


if __name__ == "__main__":
    main()

"""Day 30: Benchmark reranking — hybrid search vs hybrid + Cohere rerank.

Runs the same 10 test queries through:
  1. Hybrid search only (top-5)
  2. Hybrid search (top-50) → Cohere Rerank → top-5

Measures precision improvement by checking if top result action matches
expected action for each query, and computes average relevance scores.

Prerequisites:
  - SQL 016 executed (hybrid search function)
  - COHERE_API_KEY set in .env
  - Reviewer notes have embeddings
"""

import json
import os
import sys
import time
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.resolve.rag.retriever import hybrid_search, rerank_results, embed_query

# Test queries with expected top-action (what we'd expect the most relevant note to be)
TEST_QUERIES = [
    {"query": "SSN digits are transposed but name and DOB match exactly", "expected_action": "MERGE"},
    {"query": "maiden name change after marriage — different last names same person", "expected_action": "MERGE"},
    {"query": "father and son with same name, different DOBs", "expected_action": "SEPARATE"},
    {"query": "pharmacy system uses informal first names like Bill instead of William", "expected_action": "MERGE"},
    {"query": "member moved from Texas to Florida with address change", "expected_action": "MERGE"},
    {"query": "hyphenated last name split across enrollment and claims systems", "expected_action": "MERGE"},
    {"query": "auto-merge approved with 99% confidence", "expected_action": "MERGE"},
    {"query": "ZIP+4 difference between PO Box and street address", "expected_action": "MERGE"},
    {"query": "should we escalate when SSN last4 conflicts but all else matches", "expected_action": "ESCALATE"},
    {"query": "dual coverage during employer transition period", "expected_action": "MERGE"},
]


def main():
    print("=" * 70)
    print("Verify — Rerank Benchmark (Hybrid vs Hybrid + Cohere Rerank)")
    print("=" * 70)

    cohere_key = os.getenv("COHERE_API_KEY")
    if not cohere_key:
        print("\n⚠ COHERE_API_KEY not set — will compare hybrid-only at two depths")
        print("  Sign up at cohere.com for free tier and add to .env")

    results = []

    for i, tq in enumerate(TEST_QUERIES, 1):
        query = tq["query"]
        expected = tq["expected_action"]
        print(f"\n[{i:2d}/10] {query}")
        print(f"        Expected: {expected}")

        # 1. Hybrid only (top-5)
        t0 = time.time()
        hybrid_5 = hybrid_search(query, top_k=5)
        hybrid_time = time.time() - t0
        hybrid_top_action = hybrid_5[0]["action"] if hybrid_5 else "NONE"
        hybrid_correct = hybrid_top_action == expected

        # 2. Hybrid (top-50) → Rerank → top-5
        t0 = time.time()
        hybrid_50 = hybrid_search(query, top_k=50)
        reranked = rerank_results(query, hybrid_50, top_k=5)
        rerank_time = time.time() - t0
        rerank_top_action = reranked[0]["action"] if reranked else "NONE"
        rerank_correct = rerank_top_action == expected

        # Check if reranking changed the top result
        changed = (hybrid_5[0]["note_id"] if hybrid_5 else None) != (reranked[0]["note_id"] if reranked else None)

        print(f"        Hybrid:  top={hybrid_top_action} {'✓' if hybrid_correct else '✗'}  ({hybrid_time:.2f}s)")
        print(f"        Rerank:  top={rerank_top_action} {'✓' if rerank_correct else '✗'}  ({rerank_time:.2f}s)  changed={changed}")

        results.append({
            "query": query,
            "expected_action": expected,
            "hybrid_top_action": hybrid_top_action,
            "hybrid_correct": hybrid_correct,
            "hybrid_time_s": round(hybrid_time, 3),
            "hybrid_top_ids": [r["note_id"] for r in hybrid_5[:5]],
            "rerank_top_action": rerank_top_action,
            "rerank_correct": rerank_correct,
            "rerank_time_s": round(rerank_time, 3),
            "rerank_top_ids": [r["note_id"] for r in reranked[:5]],
            "rerank_changed_top": changed,
            "rerank_score": reranked[0].get("rerank_score") if reranked else None,
        })

    # Summary
    hybrid_precision = sum(1 for r in results if r["hybrid_correct"]) / len(results)
    rerank_precision = sum(1 for r in results if r["rerank_correct"]) / len(results)
    changes = sum(1 for r in results if r["rerank_changed_top"])
    avg_hybrid_time = sum(r["hybrid_time_s"] for r in results) / len(results)
    avg_rerank_time = sum(r["rerank_time_s"] for r in results) / len(results)

    print(f"\n{'=' * 70}")
    print("BENCHMARK RESULTS")
    print(f"{'=' * 70}")
    print(f"  Hybrid-only precision:  {hybrid_precision:.0%}")
    print(f"  Hybrid+Rerank precision: {rerank_precision:.0%}")
    print(f"  Precision delta:        {(rerank_precision - hybrid_precision):+.0%}")
    print(f"  Top result changed:     {changes}/10 queries")
    print(f"  Avg hybrid time:        {avg_hybrid_time:.3f}s")
    print(f"  Avg rerank time:        {avg_rerank_time:.3f}s")

    # Save benchmark
    benchmark = {
        "run_at": datetime.utcnow().isoformat(),
        "cohere_available": bool(cohere_key),
        "results": results,
        "summary": {
            "hybrid_precision": round(hybrid_precision, 4),
            "rerank_precision": round(rerank_precision, 4),
            "precision_delta": round(rerank_precision - hybrid_precision, 4),
            "top_changed_count": changes,
            "avg_hybrid_time_s": round(avg_hybrid_time, 3),
            "avg_rerank_time_s": round(avg_rerank_time, 3),
        },
    }

    out_path = os.path.join(os.path.dirname(__file__), "..", "eval", "results", "rerank_benchmark.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(benchmark, f, indent=2)
    print(f"\n  Benchmark saved to {out_path}")


if __name__ == "__main__":
    main()

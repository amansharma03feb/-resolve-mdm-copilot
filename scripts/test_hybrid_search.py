"""Day 29: Test hybrid search — vector + full-text retrieval over reviewer notes.

Runs 10 test queries through both pure vector search and hybrid search,
comparing results to verify hybrid catches keyword-specific cases that
pure vector misses.

Prerequisites:
  - SQL 016 executed (tsvector column + hybrid_search_notes function)
  - Reviewer notes have embeddings populated
"""

import os
import sys
import json
from datetime import datetime

import psycopg2
import voyageai
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
MODEL = "voyage-3-lite"

if not DB_URL or not VOYAGE_API_KEY:
    print("ERROR: Set DATABASE_URL and VOYAGE_API_KEY in .env")
    sys.exit(1)

vo = voyageai.Client(api_key=VOYAGE_API_KEY)

# 10 test queries — mix of semantic and keyword-heavy
TEST_QUERIES = [
    "SSN digits are transposed but name and DOB match exactly",
    "maiden name change after marriage — different last names same person",
    "father and son with same name, different DOBs",
    "pharmacy system uses informal first names like Bill instead of William",
    "member moved from Texas to Florida with address change",
    "hyphenated last name split across enrollment and claims systems",
    "auto-merge approved with 99% confidence",
    "ZIP+4 difference between PO Box and street address",
    "legacy enrollment system migration caused accent in last name",
    "dual coverage during employer transition period",
]


def vector_search(cur, query_vec, top_k=5):
    """Pure vector similarity search."""
    cur.execute(
        """
        SELECT note_id, reviewer, action, confidence, note,
               1 - (embedding <=> %s::vector) AS similarity
        FROM staging.reviewer_notes
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """,
        (str(query_vec), str(query_vec), top_k),
    )
    return cur.fetchall()


def hybrid_search(cur, query_vec, query_text, top_k=5):
    """Hybrid search using the Postgres function."""
    cur.execute(
        """
        SELECT note_id, reviewer, action, confidence, note,
               vector_score, text_score, hybrid_score
        FROM staging.hybrid_search_notes(%s::vector, %s, %s)
        """,
        (str(query_vec), query_text, top_k),
    )
    return cur.fetchall()


def main():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    print("=" * 70)
    print("Verify — Hybrid Search Test (10 Queries)")
    print("=" * 70)

    results = []
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n{'─' * 70}")
        print(f"Query {i}: {query}")
        print(f"{'─' * 70}")

        # Embed the query
        query_vec = vo.embed([query], model=MODEL, input_type="query").embeddings[0]

        # Pure vector search
        vec_results = vector_search(cur, query_vec)
        vec_ids = [r[0] for r in vec_results]

        # Hybrid search
        hyb_results = hybrid_search(cur, query_vec, query)
        hyb_ids = [r[0] for r in hyb_results]

        # Compare
        vec_only = set(vec_ids) - set(hyb_ids)
        hyb_only = set(hyb_ids) - set(vec_ids)
        overlap = set(vec_ids) & set(hyb_ids)

        print(f"\n  Vector top-5 IDs: {vec_ids}")
        print(f"  Hybrid top-5 IDs: {hyb_ids}")
        print(f"  Overlap: {len(overlap)} | Vector-only: {len(vec_only)} | Hybrid-only: {len(hyb_only)}")

        print(f"\n  Top hybrid result:")
        if hyb_results:
            r = hyb_results[0]
            print(f"    [{r[2]}] note_id={r[0]} reviewer={r[1]} conf={r[3]}")
            print(f"    vec={r[5]:.4f}  txt={r[6]:.4f}  hybrid={r[7]:.4f}")
            print(f"    {r[4][:120]}...")

        results.append({
            "query": query,
            "vector_ids": vec_ids,
            "hybrid_ids": hyb_ids,
            "overlap": len(overlap),
            "hybrid_only_count": len(hyb_only),
            "top_hybrid_score": hyb_results[0][7] if hyb_results else 0,
        })

    # Summary
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    total_hybrid_only = sum(r["hybrid_only_count"] for r in results)
    avg_overlap = sum(r["overlap"] for r in results) / len(results)
    print(f"  Queries tested: {len(results)}")
    print(f"  Avg overlap (vector ∩ hybrid): {avg_overlap:.1f} / 5")
    print(f"  Total hybrid-only results: {total_hybrid_only}")
    print(f"  (Results that hybrid caught but pure vector missed)")

    cur.close()
    conn.close()

    # Save results
    out = {
        "run_at": datetime.utcnow().isoformat(),
        "queries": results,
        "summary": {
            "total_queries": len(results),
            "avg_overlap": round(avg_overlap, 2),
            "total_hybrid_only": total_hybrid_only,
        },
    }
    out_path = os.path.join(os.path.dirname(__file__), "..", "eval", "results", "hybrid_search_test.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n  Results saved to {out_path}")


if __name__ == "__main__":
    main()

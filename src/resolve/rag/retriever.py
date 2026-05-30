"""Hybrid retrieval for RAG: vector similarity + full-text search + optional reranking."""

from __future__ import annotations

import os
from typing import Optional

import psycopg2
import voyageai
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
VOYAGE_MODEL = "voyage-3-lite"

_vo = None


def _get_voyage():
    global _vo
    if _vo is None:
        _vo = voyageai.Client(api_key=VOYAGE_API_KEY)
    return _vo


def embed_query(query: str) -> list[float]:
    """Embed a query string using Voyage AI."""
    vo = _get_voyage()
    return vo.embed([query], model=VOYAGE_MODEL, input_type="query").embeddings[0]


def hybrid_search(
    query: str,
    top_k: int = 10,
    vector_weight: float = 0.7,
    text_weight: float = 0.3,
    conn=None,
) -> list[dict]:
    """Run hybrid search (vector + full-text) over reviewer_notes.

    Returns list of dicts with: note_id, reviewer, action, confidence,
    note, vector_score, text_score, hybrid_score.
    """
    query_vec = embed_query(query)

    close_conn = False
    if conn is None:
        conn = psycopg2.connect(DB_URL)
        close_conn = True

    cur = conn.cursor()
    cur.execute(
        """
        SELECT note_id, reviewer, action, confidence, note,
               vector_score, text_score, hybrid_score
        FROM staging.hybrid_search_notes(%s::vector, %s, %s, %s, %s)
        """,
        (str(query_vec), query, top_k, vector_weight, text_weight),
    )
    rows = cur.fetchall()
    cur.close()

    if close_conn:
        conn.close()

    return [
        {
            "note_id": r[0],
            "reviewer": r[1],
            "action": r[2],
            "confidence": float(r[3]) if r[3] else 0,
            "note": r[4],
            "vector_score": r[5],
            "text_score": r[6],
            "hybrid_score": r[7],
        }
        for r in rows
    ]


def retrieve_context(query: str, top_k: int = 5, rerank: bool = True) -> list[dict]:
    """Retrieve relevant reviewer notes for RAG grounding.

    Pipeline: hybrid search (top-50) → optional Cohere rerank → top-K.
    """
    # Fetch more candidates if reranking
    candidates = hybrid_search(query, top_k=50 if rerank else top_k)

    if rerank and candidates:
        candidates = rerank_results(query, candidates, top_k=top_k)
    else:
        candidates = candidates[:top_k]

    return candidates


def rerank_results(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
) -> list[dict]:
    """Rerank candidates using Cohere Rerank API.

    Falls back to hybrid scores if Cohere is unavailable.
    """
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        # No Cohere key — fall back to hybrid ordering
        return candidates[:top_k]

    try:
        import cohere

        co = cohere.ClientV2(api_key=api_key)
        docs = [c["note"] for c in candidates]

        response = co.rerank(
            model="rerank-v3.5",
            query=query,
            documents=docs,
            top_n=top_k,
        )

        reranked = []
        for hit in response.results:
            c = candidates[hit.index].copy()
            c["rerank_score"] = hit.relevance_score
            reranked.append(c)

        return reranked

    except Exception:
        # Reranker failed — fall back gracefully
        return candidates[:top_k]

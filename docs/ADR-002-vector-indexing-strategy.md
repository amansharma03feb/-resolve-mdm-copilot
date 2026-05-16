# ADR-002: Vector Indexing Strategy

**Status:** Accepted
**Date:** 2026-05-17
**Decision maker:** Aman Sharma

## Context

Resolve stores 1024-dim Voyage AI embeddings in pgvector for semantic similarity search over steward notes and (future) patient record embeddings. We need an indexing strategy that balances query latency, build cost, recall accuracy, and Supabase free-tier constraints (32 MB maintenance_work_mem).

## Options Considered

### 1. No Index (Sequential Scan)
- Scans every row, computes distance for each
- No build cost, perfect recall
- O(n) query time — unacceptable beyond ~10K rows

### 2. IVFFlat
- Partitions vectors into Voronoi cells, searches nearby cells
- Requires loading all vectors into memory at build time
- **Rejected:** 10K rows x 1024 dims requires ~45 MB, exceeding Supabase free tier's 32 MB maintenance_work_mem limit

### 3. HNSW (Hierarchical Navigable Small World)
- Graph-based approximate nearest neighbor search
- Builds incrementally (row by row) — no memory spike
- Tunable via m (graph connectivity) and ef_construction/ef_search

## Benchmark Results (10K rows, 1024 dims, Supabase free tier)

| Method | Execution Time | Notes |
|--------|---------------|-------|
| No Index | 239.15 ms | Full sequential scan |
| IVFFlat | FAILED | Exceeded 32 MB memory limit |
| HNSW (m=16, ef=64) | 0.646 ms | 370x faster than seq scan |

## Decision

**Use HNSW** with the following parameters:
- `m = 16` (graph connectivity — higher = better recall, more memory)
- `ef_construction = 64` (build-time search depth)
- `ef_search = 40` (query-time search depth — tunable per query)
- Distance operator: `vector_cosine_ops` (cosine similarity via `<=>`)

## Index DDL

```sql
CREATE INDEX idx_member_notes_embedding
    ON staging.member_notes
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

SET hnsw.ef_search = 40;
```

## Consequences

- **Positive:** Sub-millisecond similarity queries; works within Supabase free tier; incremental builds support live inserts
- **Positive:** HNSW is the pgvector community default — well-documented, actively maintained
- **Negative:** ~2x more disk than IVFFlat for same dataset (acceptable at our scale)
- **Negative:** Approximate results — may miss exact nearest neighbor (mitigated by tuning ef_search)

## When to Revisit

- If dataset exceeds 500K embeddings — re-benchmark with larger ef_construction
- If we move to a paid Supabase tier — re-evaluate IVFFlat with higher maintenance_work_mem
- If recall drops below 95% on eval golden set — increase ef_search

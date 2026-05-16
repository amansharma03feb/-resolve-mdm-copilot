# ADR-002: Vector Indexing Strategy

**Status:** Accepted
**Date:** 2026-05-17
**Decision maker:** Aman Sharma

## Context

Resolve stores 1024-dim Voyage AI embeddings in pgvector for semantic similarity search over steward notes and (future) patient record embeddings. We need an indexing strategy that balances query latency, build cost, recall accuracy, and Supabase free-tier constraints (32 MB maintenance_work_mem).

## Alternatives Considered

### 1. No Index (Sequential Scan)
- Scans every row, computes cosine distance for each
- Perfect recall (no approximation), zero build cost
- **Rejected:** O(n) query time — 239 ms at 10K rows. Unacceptable at 50K+ rows for real-time steward UX. Would mean multi-second latency on every "find similar notes" query.

### 2. IVFFlat (Inverted File with Flat Quantization)
- Partitions vectors into Voronoi cells using k-means clustering, then searches only nearby cells at query time
- Generally lower disk usage than HNSW
- **Rejected:** Requires loading ALL vectors into memory during index build to compute centroids. At 10K × 1024 dims × 4 bytes = ~40 MB, this exceeds Supabase free tier's hard 32 MB `maintenance_work_mem` cap. Tested with lists=100, 50, and 10 — all failed with the same memory error. The bottleneck is vector loading, not cluster count.
- **When to revisit:** On a paid Supabase tier with higher memory limits, IVFFlat would likely work and use less disk than HNSW.

### 3. Dedicated Vector Database (Pinecone / Weaviate / Qdrant)
- Purpose-built for vector search with managed scaling
- **Rejected:** Adds a separate service to sync with Supabase. Our vectors need to be queried alongside relational data (patient records, steward notes, audit logs). pgvector keeps everything co-located — no ETL pipeline between systems. At our scale (<100K vectors), pgvector matches dedicated vector DB performance.
- **When to revisit:** If we exceed 1M embeddings or need cross-region replication.

### 4. HNSW (Hierarchical Navigable Small World) ← CHOSEN
- Graph-based approximate nearest neighbor search
- Builds incrementally (one vector at a time) — no memory spike
- Tunable via `m` (graph connectivity) and `ef_construction` / `ef_search`
- Sub-millisecond queries at 10K scale

## Benchmark Results (10K rows, 1024 dims, Supabase free tier)

**Test setup:** 10,000 rows with random 1024-dim vectors in `staging.vector_benchmark`. Query: find 5 nearest neighbours to row id=1.

| Method | Execution Time | Speedup | Status |
|--------|---------------|---------|--------|
| No Index (seq scan) | 239.15 ms | baseline | Scanned all 9,999 rows |
| IVFFlat (lists=100) | FAILED | — | Needs ~45 MB, limit is 32 MB |
| IVFFlat (lists=50) | FAILED | — | Still exceeds memory limit |
| IVFFlat (lists=10) | FAILED | — | Still exceeds memory limit |
| **HNSW (m=16, ef=64)** | **0.646 ms** | **370x** | Index scan, 5 rows returned |

**Why IVFFlat fails:** IVFFlat must load ALL vectors into memory at build time to compute cluster centroids. 10K × 1024 dims × 4 bytes = ~40 MB, which exceeds Supabase free tier's 32 MB `maintenance_work_mem` cap. Reducing `lists` does not help because the memory bottleneck is loading the vectors, not the number of clusters.

**Why HNSW works:** HNSW builds its graph incrementally (one vector at a time), so it never needs all vectors in memory simultaneously.

### EXPLAIN ANALYZE Details

**No Index (seq scan):**
- Sort Method: top-N heapsort, Memory: 25kB
- Seq Scan on vector_benchmark: actual time 0.257..231.395 ms, rows=9,999
- Planning Time: 0.438 ms
- **Execution Time: 239.150 ms**

**HNSW:**
- Index Scan using idx_bench_hnsw: actual time 0.489..0.524 ms, rows=5
- Planning Time: 0.895 ms
- **Execution Time: 0.646 ms**

### Index Size

| Index | Size |
|-------|------|
| Primary key (B-tree) | 240 KB |
| HNSW (m=16, ef_construction=64) | 21 MB |
| Per-vector overhead | ~2.1 KB |

Projected sizes: 1K notes → ~2 MB, 10K notes → ~21 MB, 50K notes → ~105 MB.

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

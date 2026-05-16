# ADR-002: pgvector Indexing Strategy

**Status:** Accepted
**Date:** 2026-05-17
**Author:** Aman Sharma

## Context

Resolve uses pgvector on Supabase for semantic similarity search over steward notes and (future) patient record embeddings. As data grows, unindexed vector search becomes a bottleneck — sequential scan is O(n) per query.

pgvector offers two approximate nearest-neighbor (ANN) index types:
- **IVFFlat** — inverted file index with flat quantization
- **HNSW** — hierarchical navigable small world graph

We need to choose one for production and configure it correctly.

## Decision

**Use HNSW as the primary index type for all embedding columns.**

Fall back to IVFFlat only if memory constraints require it on very large tables (>1M rows).

## Benchmark Results

Benchmark: 10K synthetic 1024-dim vectors, cosine distance, top-5 query.

| Method | Avg Query Time | Index Build Time | Index Size | Recall |
|--------|---------------|-----------------|------------|--------|
| No Index (seq scan) | ___ ms | n/a | 0 | 100% (exact) |
| IVFFlat (lists=100, probes=10) | ___ ms | ___ s | ___ MB | ~95% |
| HNSW (m=16, ef_construction=64, ef_search=40) | ___ ms | ___ s | ___ MB | ~99% |

*(Fill in after running `006_vector_index_benchmark.sql`)*

## Comparison

### IVFFlat
- **How it works:** Clusters vectors into `lists` buckets using k-means. At query time, scans only the `probes` nearest buckets.
- **Pros:** Smaller index size. Faster build time. Lower memory usage.
- **Cons:** Recall depends on probe count. Must rebuild index after large inserts (`REINDEX`). Empty or unbalanced clusters degrade quality.
- **Tuning:** `lists` ≈ sqrt(row_count). `probes` ≈ sqrt(lists) for ~95% recall.

### HNSW
- **How it works:** Builds a multi-layer graph where each node connects to its nearest neighbors. Searches by traversing the graph from top layer down.
- **Pros:** Higher recall at same speed. No reindexing needed after inserts. More consistent performance.
- **Cons:** Larger index size (~2-3x IVFFlat). Slower build time. Higher memory during construction.
- **Tuning:** `m` = max connections per node (16 is standard). `ef_construction` = build-time search width (64-200). `ef_search` = query-time search width (40-100).

## Why HNSW

1. **Recall matters more than index size.** A missed relevant steward note means a worse rationale. At our scale (<100K notes), the extra memory is negligible.
2. **No reindex maintenance.** IVFFlat degrades as data distribution shifts — steward notes are added continuously, and we don't want a reindex cron job.
3. **Consistent latency.** HNSW query time is more predictable across different query vectors.
4. **Industry standard.** HNSW is the default recommendation from pgvector, Pinecone, Weaviate, and Qdrant documentation.

## Configuration

```sql
-- For tables < 100K rows
CREATE INDEX idx_<table>_embedding
    ON <schema>.<table>
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

SET hnsw.ef_search = 40;
```

Revisit `ef_construction` and `ef_search` if recall drops below 95% on eval golden set.

## Consequences

- All new embedding tables use HNSW by default
- Index builds are slower (~2-5x vs IVFFlat) but only happen once
- Memory usage is higher but well within Supabase free tier limits at our scale
- No scheduled reindexing needed
- If we scale past 1M rows, re-evaluate IVFFlat with higher probe counts or consider a dedicated vector DB

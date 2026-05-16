-- 006: pgvector Index Benchmark — No Index vs IVFFlat vs HNSW
-- Run each section ONE AT A TIME in Supabase SQL Editor
-- Record the "Execution time" shown in the Results tab after each query

-- ============================================================
-- STEP 1: Create benchmark table with 10K random 1024-dim vectors
-- ============================================================
DROP TABLE IF EXISTS staging.vector_benchmark;

CREATE TABLE staging.vector_benchmark (
    id          SERIAL PRIMARY KEY,
    payload     TEXT,
    embedding   vector(1024)
);

-- Generate 10K rows with random vectors
-- This takes ~30-60 seconds
INSERT INTO staging.vector_benchmark (payload, embedding)
SELECT
    'synthetic_note_' || i,
    (
        SELECT array_to_string(ARRAY(
            SELECT ROUND((random() * 2 - 1)::numeric, 6)
            FROM generate_series(1, 1024)
        ), ',')
    )::vector
FROM generate_series(1, 10000) AS i;

-- Verify
SELECT COUNT(*) AS row_count FROM staging.vector_benchmark;


-- ============================================================
-- STEP 2: Generate a fixed query vector (use for ALL benchmarks)
-- ============================================================
-- Save the query vector from row id=1 so every test uses the same probe
-- Run this and note the result — OR just use id=1 in subsequent queries

-- Verify a sample vector
SELECT id, LEFT(embedding::text, 60) AS vec_preview
FROM staging.vector_benchmark
LIMIT 3;


-- ============================================================
-- STEP 3: BENCHMARK A — No Index (Sequential Scan)
-- Run this query 3 times. Record each execution time.
-- ============================================================
DROP INDEX IF EXISTS staging.idx_bench_ivfflat;
DROP INDEX IF EXISTS staging.idx_bench_hnsw;

EXPLAIN ANALYZE
SELECT id, payload, embedding <=> (
    SELECT embedding FROM staging.vector_benchmark WHERE id = 1
) AS distance
FROM staging.vector_benchmark
WHERE id != 1
ORDER BY embedding <=> (
    SELECT embedding FROM staging.vector_benchmark WHERE id = 1
)
LIMIT 5;


-- ============================================================
-- STEP 4: BENCHMARK B — IVFFlat Index
-- First create the index, then run the same query 3 times.
-- ============================================================

-- Create IVFFlat index (lists=100 is standard for 10K rows)
CREATE INDEX idx_bench_ivfflat
    ON staging.vector_benchmark
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Set probes (higher = more accurate but slower)
SET ivfflat.probes = 10;

EXPLAIN ANALYZE
SELECT id, payload, embedding <=> (
    SELECT embedding FROM staging.vector_benchmark WHERE id = 1
) AS distance
FROM staging.vector_benchmark
WHERE id != 1
ORDER BY embedding <=> (
    SELECT embedding FROM staging.vector_benchmark WHERE id = 1
)
LIMIT 5;


-- ============================================================
-- STEP 5: BENCHMARK C — HNSW Index
-- Drop IVFFlat, create HNSW, then run the same query 3 times.
-- ============================================================

-- Drop IVFFlat
DROP INDEX IF EXISTS staging.idx_bench_ivfflat;

-- Create HNSW index (m=16, ef_construction=64 are good defaults)
CREATE INDEX idx_bench_hnsw
    ON staging.vector_benchmark
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Set search parameter
SET hnsw.ef_search = 40;

EXPLAIN ANALYZE
SELECT id, payload, embedding <=> (
    SELECT embedding FROM staging.vector_benchmark WHERE id = 1
) AS distance
FROM staging.vector_benchmark
WHERE id != 1
ORDER BY embedding <=> (
    SELECT embedding FROM staging.vector_benchmark WHERE id = 1
)
LIMIT 5;


-- ============================================================
-- STEP 6: Index size comparison
-- ============================================================
SELECT
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) AS index_size
FROM pg_indexes
WHERE tablename = 'vector_benchmark'
  AND schemaname = 'staging';


-- ============================================================
-- STEP 7: Cleanup (optional — run after recording results)
-- ============================================================
-- DROP TABLE IF EXISTS staging.vector_benchmark;

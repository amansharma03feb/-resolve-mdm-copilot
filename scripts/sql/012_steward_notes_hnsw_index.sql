-- 012: Build HNSW index on steward_notes embeddings
-- Run AFTER embed_steward_notes.py has populated all embeddings
-- Prerequisites: all 110 notes must have non-null embedding vectors

-- ============================================================
-- STEP 1: Verify all notes have embeddings
-- ============================================================
SELECT
    COUNT(*) AS total_notes,
    COUNT(embedding) AS embedded_notes,
    COUNT(*) - COUNT(embedding) AS missing_embeddings
FROM staging.steward_notes;

-- ============================================================
-- STEP 2: Drop old index if exists, build HNSW
-- ============================================================
DROP INDEX IF EXISTS staging.idx_steward_notes_hnsw;

CREATE INDEX idx_steward_notes_hnsw
    ON staging.steward_notes
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- ============================================================
-- STEP 3: Verify index is used
-- ============================================================
EXPLAIN ANALYZE
SELECT note_id, 1 - (embedding <=> '[0.1,0.2,0.3]'::vector(512)) AS similarity
FROM staging.steward_notes
WHERE embedding IS NOT NULL
ORDER BY embedding <=> '[0.1,0.2,0.3]'::vector(512)
LIMIT 3;

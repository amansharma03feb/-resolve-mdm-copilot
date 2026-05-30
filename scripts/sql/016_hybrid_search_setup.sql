-- 016: Add tsvector column + hybrid search function to reviewer_notes
-- Run in Supabase SQL Editor AFTER 013_rename_tables_verify.sql

-- ============================================================
-- STEP 1: Add tsvector column for full-text search
-- ============================================================
ALTER TABLE staging.reviewer_notes
    ADD COLUMN IF NOT EXISTS note_tsv tsvector;

-- Populate tsvector from existing notes
UPDATE staging.reviewer_notes
SET note_tsv = to_tsvector('english', note)
WHERE note_tsv IS NULL;

-- Auto-update tsvector on INSERT/UPDATE
CREATE OR REPLACE FUNCTION staging.reviewer_notes_tsv_trigger()
RETURNS trigger AS $$
BEGIN
    NEW.note_tsv := to_tsvector('english', NEW.note);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_reviewer_notes_tsv ON staging.reviewer_notes;
CREATE TRIGGER trg_reviewer_notes_tsv
    BEFORE INSERT OR UPDATE OF note
    ON staging.reviewer_notes
    FOR EACH ROW
    EXECUTE FUNCTION staging.reviewer_notes_tsv_trigger();

-- GIN index for fast full-text search
CREATE INDEX IF NOT EXISTS idx_reviewer_notes_tsv
    ON staging.reviewer_notes USING gin(note_tsv);

-- ============================================================
-- STEP 2: Hybrid search function
-- Combines vector similarity (<=> cosine distance) with
-- Postgres full-text rank (ts_rank_cd), returns top-K
-- with a weighted score.
--
-- Parameters:
--   query_embedding  — 512-dim vector from Voyage AI
--   query_text       — raw text query for full-text search
--   match_count      — how many results to return (default 10)
--   vector_weight    — weight for vector similarity (default 0.7)
--   text_weight      — weight for full-text rank (default 0.3)
-- ============================================================
CREATE OR REPLACE FUNCTION staging.hybrid_search_notes(
    query_embedding  vector(512),
    query_text       text,
    match_count      int DEFAULT 10,
    vector_weight    float DEFAULT 0.7,
    text_weight      float DEFAULT 0.3
)
RETURNS TABLE (
    note_id          int,
    reviewer         varchar(50),
    action           varchar(20),
    confidence       numeric(4,2),
    note             text,
    vector_score     float,
    text_score       float,
    hybrid_score     float
)
LANGUAGE sql STABLE
AS $$
    WITH vector_results AS (
        SELECT
            rn.note_id,
            rn.reviewer,
            rn.action,
            rn.confidence,
            rn.note,
            1 - (rn.embedding <=> query_embedding) AS vec_sim
        FROM staging.reviewer_notes rn
        WHERE rn.embedding IS NOT NULL
    ),
    text_results AS (
        SELECT
            rn.note_id,
            ts_rank_cd(rn.note_tsv, plainto_tsquery('english', query_text)) AS txt_rank
        FROM staging.reviewer_notes rn
        WHERE rn.note_tsv @@ plainto_tsquery('english', query_text)
    ),
    combined AS (
        SELECT
            v.note_id,
            v.reviewer,
            v.action,
            v.confidence,
            v.note,
            v.vec_sim                                          AS vector_score,
            COALESCE(t.txt_rank, 0)                            AS text_score,
            (vector_weight * v.vec_sim)
                + (text_weight * COALESCE(t.txt_rank, 0))      AS hybrid_score
        FROM vector_results v
        LEFT JOIN text_results t ON v.note_id = t.note_id
    )
    SELECT
        c.note_id,
        c.reviewer,
        c.action,
        c.confidence,
        c.note,
        c.vector_score::float,
        c.text_score::float,
        c.hybrid_score::float
    FROM combined c
    ORDER BY c.hybrid_score DESC
    LIMIT match_count;
$$;

COMMENT ON FUNCTION staging.hybrid_search_notes
    IS 'Hybrid search: vector similarity (cosine) + full-text rank (ts_rank_cd), weighted blend, top-K';

-- ============================================================
-- STEP 3: Verify
-- ============================================================
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'staging'
  AND table_name = 'reviewer_notes'
  AND column_name = 'note_tsv';

SELECT routine_name
FROM information_schema.routines
WHERE routine_schema = 'staging'
  AND routine_name = 'hybrid_search_notes';

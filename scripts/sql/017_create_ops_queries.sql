-- 017: Create ops_queries table for storing Q&A chat history
-- Run in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS staging.ops_queries (
    query_id        SERIAL PRIMARY KEY,
    question        TEXT NOT NULL,
    answer_text     TEXT,
    cited_note_ids  INTEGER[],
    confidence      NUMERIC(4,3),
    notes_retrieved INTEGER DEFAULT 0,
    latency_s       NUMERIC(6,3),
    created_at      TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE staging.ops_queries
    IS 'Audit log of Ops Q&A queries — question, answer, citations, and performance metrics';

-- Index for recent queries
CREATE INDEX IF NOT EXISTS idx_ops_queries_created
    ON staging.ops_queries (created_at DESC);

-- Verify
SELECT COUNT(*) AS ops_queries_table_exists
FROM information_schema.tables
WHERE table_schema = 'staging' AND table_name = 'ops_queries';

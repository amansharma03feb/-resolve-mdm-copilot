-- 015: Create eval_runs table for storing Ragas evaluation results
-- Run in Supabase SQL Editor AFTER 014_add_cached_rationale_and_audit.sql

CREATE TABLE IF NOT EXISTS staging.eval_runs (
    id              SERIAL PRIMARY KEY,
    run_id          VARCHAR(30) NOT NULL UNIQUE,
    run_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    total_cases     INTEGER NOT NULL,
    valid_cases     INTEGER NOT NULL,
    errors          INTEGER DEFAULT 0,
    decision_agreement    NUMERIC(6,4),
    auto_resolve_precision NUMERIC(6,4),
    avg_latency_s   NUMERIC(8,3),
    full_metrics    JSONB,
    created_at      TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE staging.eval_runs
    IS 'Stores results from each Ragas evaluation run against the golden set';

-- Verify
SELECT COUNT(*) AS eval_runs_table_exists
FROM information_schema.tables
WHERE table_schema = 'staging' AND table_name = 'eval_runs';

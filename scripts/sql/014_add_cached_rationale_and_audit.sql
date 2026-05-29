-- 014: Add cached_rationale column to decision_candidates + LLM audit table
-- Run in Supabase SQL Editor AFTER 013_rename_tables_verify.sql

-- ============================================================
-- STEP 1: Add cached rationale column
-- ============================================================
ALTER TABLE staging.decision_candidates
    ADD COLUMN IF NOT EXISTS cached_rationale JSONB;

COMMENT ON COLUMN staging.decision_candidates.cached_rationale
    IS 'Cached AI-generated rationale (JSON: recommendation, confidence, evidence, rationale_text)';

-- ============================================================
-- STEP 2: Create external LLM calls audit table
-- ============================================================
CREATE TABLE IF NOT EXISTS staging.external_llm_calls (
    call_id         SERIAL PRIMARY KEY,
    called_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    model           VARCHAR(50) NOT NULL,
    redacted_input_length  INTEGER,
    response_length        INTEGER,
    cost_estimate_usd      NUMERIC(8,4) DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE staging.external_llm_calls
    IS 'Audit log of every external LLM API call — tracks redacted input size, response size, and cost';

-- ============================================================
-- STEP 3: Verify
-- ============================================================
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'staging' AND table_name = 'decision_candidates' AND column_name = 'cached_rationale';

SELECT COUNT(*) AS audit_table_exists
FROM information_schema.tables
WHERE table_schema = 'staging' AND table_name = 'external_llm_calls';

-- 007: Generate match candidates with blocking, scoring, and tier classification
-- Run in Supabase SQL Editor
-- Prerequisites: fuzzystrmatch extension (already enabled), pg_trgm for similarity()

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================
-- STEP 1: Create match_candidates table
-- ============================================================
DROP TABLE IF EXISTS staging.match_candidates;

CREATE TABLE staging.match_candidates (
    pair_id             SERIAL PRIMARY KEY,
    member_id_a         UUID NOT NULL,
    member_id_b         UUID NOT NULL,
    blocking_key        VARCHAR(20) NOT NULL,

    -- Per-attribute scores (0.0 to 1.0)
    score_name          NUMERIC(4,3),
    score_dob           NUMERIC(4,3),
    score_ssn           NUMERIC(4,3),
    score_address       NUMERIC(4,3),

    -- Weighted composite
    composite_score     NUMERIC(4,3),

    -- Tier classification
    tier                VARCHAR(20) NOT NULL,

    created_at          TIMESTAMPTZ DEFAULT now(),

    CONSTRAINT uq_pair UNIQUE (member_id_a, member_id_b)
);

COMMENT ON TABLE staging.match_candidates IS 'Scored candidate duplicate pairs — generated via blocking + multi-attribute similarity';

-- ============================================================
-- STEP 2: Generate and score candidate pairs
--
-- BLOCKING STRATEGY:
--   Primary block: name_soundex (phonetic last name)
--   Secondary block: birth_year (same year of birth)
--   This reduces 50K × 50K = 2.5B comparisons to ~10K-50K pairs
--
-- SCORING WEIGHTS:
--   Name similarity (trigram):  30%
--   DOB exact match:            25%
--   SSN_last4 exact match:      30%
--   Address similarity (trigram):15%
--
-- TIER THRESHOLDS:
--   AUTO_MERGE:     composite >= 0.95
--   STEWARD_REVIEW: composite >= 0.60
--   SEPARATE:       composite <  0.60
-- ============================================================
INSERT INTO staging.match_candidates (
    member_id_a, member_id_b, blocking_key,
    score_name, score_dob, score_ssn, score_address,
    composite_score, tier
)
SELECT
    a.member_id AS member_id_a,
    b.member_id AS member_id_b,
    a.name_soundex || '_' || a.birth_year::TEXT AS blocking_key,

    -- Name score: trigram similarity on normalized full name
    COALESCE(similarity(a.name_normalized, b.name_normalized), 0) AS score_name,

    -- DOB score: exact date match = 1.0, else 0.0
    CASE WHEN a.date_of_birth = b.date_of_birth THEN 1.000 ELSE 0.000 END AS score_dob,

    -- SSN score: exact last4 match = 1.0, else 0.0
    CASE
        WHEN a.ssn_last4 IS NOT NULL
         AND b.ssn_last4 IS NOT NULL
         AND a.ssn_last4 = b.ssn_last4 THEN 1.000
        ELSE 0.000
    END AS score_ssn,

    -- Address score: trigram similarity on normalized address
    CASE
        WHEN a.address_normalized IS NOT NULL
         AND b.address_normalized IS NOT NULL
        THEN COALESCE(similarity(a.address_normalized, b.address_normalized), 0)
        ELSE 0.000
    END AS score_address,

    -- Weighted composite: name 30% + DOB 25% + SSN 30% + address 15%
    ROUND(
        0.30 * COALESCE(similarity(a.name_normalized, b.name_normalized), 0)
      + 0.25 * (CASE WHEN a.date_of_birth = b.date_of_birth THEN 1.000 ELSE 0.000 END)
      + 0.30 * (CASE WHEN a.ssn_last4 IS NOT NULL AND b.ssn_last4 IS NOT NULL AND a.ssn_last4 = b.ssn_last4 THEN 1.000 ELSE 0.000 END)
      + 0.15 * (CASE WHEN a.address_normalized IS NOT NULL AND b.address_normalized IS NOT NULL THEN COALESCE(similarity(a.address_normalized, b.address_normalized), 0) ELSE 0.000 END)
    , 3) AS composite_score,

    -- Tier
    CASE
        WHEN ROUND(
            0.30 * COALESCE(similarity(a.name_normalized, b.name_normalized), 0)
          + 0.25 * (CASE WHEN a.date_of_birth = b.date_of_birth THEN 1.000 ELSE 0.000 END)
          + 0.30 * (CASE WHEN a.ssn_last4 IS NOT NULL AND b.ssn_last4 IS NOT NULL AND a.ssn_last4 = b.ssn_last4 THEN 1.000 ELSE 0.000 END)
          + 0.15 * (CASE WHEN a.address_normalized IS NOT NULL AND b.address_normalized IS NOT NULL THEN COALESCE(similarity(a.address_normalized, b.address_normalized), 0) ELSE 0.000 END)
        , 3) >= 0.950 THEN 'AUTO_MERGE'
        WHEN ROUND(
            0.30 * COALESCE(similarity(a.name_normalized, b.name_normalized), 0)
          + 0.25 * (CASE WHEN a.date_of_birth = b.date_of_birth THEN 1.000 ELSE 0.000 END)
          + 0.30 * (CASE WHEN a.ssn_last4 IS NOT NULL AND b.ssn_last4 IS NOT NULL AND a.ssn_last4 = b.ssn_last4 THEN 1.000 ELSE 0.000 END)
          + 0.15 * (CASE WHEN a.address_normalized IS NOT NULL AND b.address_normalized IS NOT NULL THEN COALESCE(similarity(a.address_normalized, b.address_normalized), 0) ELSE 0.000 END)
        , 3) >= 0.600 THEN 'STEWARD_REVIEW'
        ELSE 'SEPARATE'
    END AS tier

FROM staging.members a
JOIN staging.members b
  ON a.name_soundex = b.name_soundex
 AND a.birth_year = b.birth_year
 AND a.member_id < b.member_id;

-- ============================================================
-- STEP 3: Verify — row counts per tier
-- ============================================================
SELECT
    tier,
    COUNT(*) AS pair_count,
    ROUND(AVG(composite_score), 3) AS avg_score,
    MIN(composite_score) AS min_score,
    MAX(composite_score) AS max_score
FROM staging.match_candidates
GROUP BY tier
ORDER BY
    CASE tier
        WHEN 'AUTO_MERGE' THEN 1
        WHEN 'STEWARD_REVIEW' THEN 2
        WHEN 'SEPARATE' THEN 3
    END;

-- Total count
SELECT COUNT(*) AS total_candidate_pairs FROM staging.match_candidates;

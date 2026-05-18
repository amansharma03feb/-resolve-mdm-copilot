-- 010: Re-score match candidates after injecting synthetic duplicates
-- Run AFTER 009_inject_synthetic_duplicates.sql

-- ============================================================
-- STEP 1: Clear old candidates
-- ============================================================
TRUNCATE TABLE staging.match_candidates;
ALTER SEQUENCE staging.match_candidates_pair_id_seq RESTART WITH 1;

-- ============================================================
-- STEP 2: Re-generate candidates with scoring (same logic as 007)
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

    COALESCE(similarity(a.name_normalized, b.name_normalized), 0) AS score_name,

    CASE WHEN a.date_of_birth = b.date_of_birth THEN 1.000 ELSE 0.000 END AS score_dob,

    CASE
        WHEN a.ssn_last4 IS NOT NULL AND b.ssn_last4 IS NOT NULL AND a.ssn_last4 = b.ssn_last4 THEN 1.000
        ELSE 0.000
    END AS score_ssn,

    CASE
        WHEN a.address_normalized IS NOT NULL AND b.address_normalized IS NOT NULL
        THEN COALESCE(similarity(a.address_normalized, b.address_normalized), 0)
        ELSE 0.000
    END AS score_address,

    ROUND((
        0.30 * COALESCE(similarity(a.name_normalized, b.name_normalized), 0)
      + 0.25 * (CASE WHEN a.date_of_birth = b.date_of_birth THEN 1.0 ELSE 0.0 END)
      + 0.30 * (CASE WHEN a.ssn_last4 IS NOT NULL AND b.ssn_last4 IS NOT NULL AND a.ssn_last4 = b.ssn_last4 THEN 1.0 ELSE 0.0 END)
      + 0.15 * (CASE WHEN a.address_normalized IS NOT NULL AND b.address_normalized IS NOT NULL THEN COALESCE(similarity(a.address_normalized, b.address_normalized), 0) ELSE 0.0 END)
    )::numeric, 3) AS composite_score,

    CASE
        WHEN (
            0.30 * COALESCE(similarity(a.name_normalized, b.name_normalized), 0)
          + 0.25 * (CASE WHEN a.date_of_birth = b.date_of_birth THEN 1.0 ELSE 0.0 END)
          + 0.30 * (CASE WHEN a.ssn_last4 IS NOT NULL AND b.ssn_last4 IS NOT NULL AND a.ssn_last4 = b.ssn_last4 THEN 1.0 ELSE 0.0 END)
          + 0.15 * (CASE WHEN a.address_normalized IS NOT NULL AND b.address_normalized IS NOT NULL THEN COALESCE(similarity(a.address_normalized, b.address_normalized), 0) ELSE 0.0 END)
        ) >= 0.950 THEN 'AUTO_MERGE'
        WHEN (
            0.30 * COALESCE(similarity(a.name_normalized, b.name_normalized), 0)
          + 0.25 * (CASE WHEN a.date_of_birth = b.date_of_birth THEN 1.0 ELSE 0.0 END)
          + 0.30 * (CASE WHEN a.ssn_last4 IS NOT NULL AND b.ssn_last4 IS NOT NULL AND a.ssn_last4 = b.ssn_last4 THEN 1.0 ELSE 0.0 END)
          + 0.15 * (CASE WHEN a.address_normalized IS NOT NULL AND b.address_normalized IS NOT NULL THEN COALESCE(similarity(a.address_normalized, b.address_normalized), 0) ELSE 0.0 END)
        ) >= 0.600 THEN 'STEWARD_REVIEW'
        ELSE 'SEPARATE'
    END AS tier

FROM staging.members a
JOIN staging.members b
  ON a.name_soundex = b.name_soundex
 AND a.birth_year = b.birth_year
 AND a.member_id < b.member_id;

-- ============================================================
-- STEP 3: Verify tier distribution
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

SELECT COUNT(*) AS total_candidate_pairs FROM staging.match_candidates;

-- ============================================================
-- STEP 4: Spot-check injected duplicates specifically
-- Show pairs where one record is from a dup source system
-- ============================================================
SELECT
    mc.tier,
    mc.composite_score,
    mc.score_name, mc.score_dob, mc.score_ssn, mc.score_address,
    a.name_normalized AS name_a,
    b.name_normalized AS name_b,
    a.source_system AS src_a,
    b.source_system AS src_b,
    a.ssn_last4 AS ssn_a,
    b.ssn_last4 AS ssn_b,
    a.date_of_birth AS dob_a,
    b.date_of_birth AS dob_b
FROM staging.match_candidates mc
JOIN staging.members a ON mc.member_id_a = a.member_id
JOIN staging.members b ON mc.member_id_b = b.member_id
WHERE a.source_system LIKE 'synthea_dup%'
   OR b.source_system LIKE 'synthea_dup%'
ORDER BY mc.composite_score DESC
LIMIT 20;

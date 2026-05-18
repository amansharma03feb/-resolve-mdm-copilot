-- 008: Spot-check match candidates — verify scoring makes sense
-- Run AFTER 007_generate_match_candidates.sql

-- ============================================================
-- CHECK 1: Top 10 highest-scoring pairs (should look like real matches)
-- ============================================================
SELECT
    mc.pair_id,
    mc.tier,
    mc.composite_score,
    mc.score_name,
    mc.score_dob,
    mc.score_ssn,
    mc.score_address,
    a.name_normalized AS name_a,
    b.name_normalized AS name_b,
    a.date_of_birth AS dob_a,
    b.date_of_birth AS dob_b,
    a.ssn_last4 AS ssn_a,
    b.ssn_last4 AS ssn_b,
    LEFT(a.address_normalized, 40) AS addr_a,
    LEFT(b.address_normalized, 40) AS addr_b
FROM staging.match_candidates mc
JOIN staging.members a ON mc.member_id_a = a.member_id
JOIN staging.members b ON mc.member_id_b = b.member_id
ORDER BY mc.composite_score DESC
LIMIT 10;

-- ============================================================
-- CHECK 2: 5 STEWARD_REVIEW pairs (grey zone — should be ambiguous)
-- ============================================================
SELECT
    mc.pair_id,
    mc.tier,
    mc.composite_score,
    mc.score_name,
    mc.score_dob,
    mc.score_ssn,
    mc.score_address,
    a.name_normalized AS name_a,
    b.name_normalized AS name_b,
    a.date_of_birth AS dob_a,
    b.date_of_birth AS dob_b,
    a.ssn_last4 AS ssn_a,
    b.ssn_last4 AS ssn_b
FROM staging.match_candidates mc
JOIN staging.members a ON mc.member_id_a = a.member_id
JOIN staging.members b ON mc.member_id_b = b.member_id
WHERE mc.tier = 'STEWARD_REVIEW'
ORDER BY mc.composite_score DESC
LIMIT 5;

-- ============================================================
-- CHECK 3: 5 lowest-scoring SEPARATE pairs (should be clearly different)
-- ============================================================
SELECT
    mc.pair_id,
    mc.tier,
    mc.composite_score,
    mc.score_name,
    mc.score_dob,
    mc.score_ssn,
    a.name_normalized AS name_a,
    b.name_normalized AS name_b,
    a.date_of_birth AS dob_a,
    b.date_of_birth AS dob_b
FROM staging.match_candidates mc
JOIN staging.members a ON mc.member_id_a = a.member_id
JOIN staging.members b ON mc.member_id_b = b.member_id
WHERE mc.tier = 'SEPARATE'
ORDER BY mc.composite_score ASC
LIMIT 5;

-- ============================================================
-- CHECK 4: Score distribution histogram
-- ============================================================
SELECT
    CASE
        WHEN composite_score >= 0.95 THEN '0.95-1.00 (AUTO_MERGE)'
        WHEN composite_score >= 0.90 THEN '0.90-0.94'
        WHEN composite_score >= 0.80 THEN '0.80-0.89'
        WHEN composite_score >= 0.70 THEN '0.70-0.79'
        WHEN composite_score >= 0.60 THEN '0.60-0.69 (STEWARD_REVIEW floor)'
        WHEN composite_score >= 0.40 THEN '0.40-0.59'
        WHEN composite_score >= 0.20 THEN '0.20-0.39'
        ELSE '0.00-0.19'
    END AS score_bucket,
    COUNT(*) AS pair_count
FROM staging.match_candidates
GROUP BY 1
ORDER BY 1 DESC;

-- ============================================================
-- CHECK 5: Blocking key coverage — which soundex codes produce most pairs?
-- ============================================================
SELECT
    blocking_key,
    COUNT(*) AS pair_count
FROM staging.match_candidates
GROUP BY blocking_key
ORDER BY pair_count DESC
LIMIT 10;

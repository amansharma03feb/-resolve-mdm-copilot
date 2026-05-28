-- 009: Inject synthetic duplicate pairs into staging.members
-- Creates 200 duplicate records with realistic noise variations
-- Run in Supabase SQL Editor BEFORE re-running 007

-- ============================================================
-- STEP 1: Create a temp table of 200 random source members
-- ============================================================
DROP TABLE IF EXISTS staging._dup_sources;

CREATE TABLE staging._dup_sources AS
SELECT *
FROM staging.members
ORDER BY random()
LIMIT 200;

-- ============================================================
-- STEP 2: Insert duplicates with controlled noise
-- We create 3 tiers of duplicates:
--   Tier A (60 records): Near-exact — same SSN, same DOB, minor name typo
--          → Should score AUTO_MERGE (>0.95)
--   Tier B (80 records): Ambiguous — same DOB, name variant, different address
--          → Should score STEWARD_REVIEW (0.60-0.94)
--   Tier C (60 records): Tricky — SSN transposition, DOB off by 1 year, similar name
--          → Should score low STEWARD_REVIEW or high SEPARATE
-- ============================================================

-- -------------------------------------------------------
-- TIER A: Near-exact duplicates (60 records)
-- Same SSN_last4, same DOB, tiny name variation, same ZIP
-- -------------------------------------------------------
INSERT INTO staging.members (
    member_id, source_id,
    first_name, last_name, middle_initial, suffix, maiden_name, full_name,
    date_of_birth, birth_year, age, is_deceased,
    ssn_last4, gender, race, ethnicity, marital_status,
    address_line, city, state, zip5, zip_full, county, latitude, longitude,
    source_system, name_normalized, name_soundex, address_normalized
)
SELECT
    gen_random_uuid() AS member_id,
    s.source_id,
    -- Name noise: swap first two chars of first_name
    CASE
        WHEN LENGTH(s.first_name) >= 2
        THEN UPPER(SUBSTRING(s.first_name, 2, 1) || SUBSTRING(s.first_name, 1, 1) || SUBSTRING(s.first_name, 3))
        ELSE s.first_name
    END AS first_name,
    s.last_name,
    s.middle_initial, s.suffix, s.maiden_name,
    CASE
        WHEN LENGTH(s.first_name) >= 2
        THEN UPPER(SUBSTRING(s.first_name, 2, 1) || SUBSTRING(s.first_name, 1, 1) || SUBSTRING(s.first_name, 3)) || ' ' || s.last_name
        ELSE s.full_name
    END AS full_name,
    s.date_of_birth, s.birth_year, s.age, s.is_deceased,
    s.ssn_last4,  -- SAME SSN
    s.gender, s.race, s.ethnicity, s.marital_status,
    s.address_line, s.city, s.state, s.zip5, s.zip_full, s.county, s.latitude, s.longitude,
    'synthea_dup_a' AS source_system,
    -- Recompute normalized fields
    TRIM(REGEXP_REPLACE(REGEXP_REPLACE(
        LOWER(
            CASE WHEN LENGTH(s.first_name) >= 2
            THEN SUBSTRING(s.first_name, 2, 1) || SUBSTRING(s.first_name, 1, 1) || SUBSTRING(s.first_name, 3)
            ELSE s.first_name END
            || ' ' || s.last_name
        ), '[^a-z ]', '', 'g'), '\s+', ' ', 'g')) AS name_normalized,
    SOUNDEX(s.last_name) AS name_soundex,
    s.address_normalized
FROM staging._dup_sources s
ORDER BY s.member_id
LIMIT 60;

-- -------------------------------------------------------
-- TIER B: Ambiguous duplicates (80 records)
-- Same DOB, nickname/shortened first name, different address, no SSN match
-- -------------------------------------------------------
INSERT INTO staging.members (
    member_id, source_id,
    first_name, last_name, middle_initial, suffix, maiden_name, full_name,
    date_of_birth, birth_year, age, is_deceased,
    ssn_last4, gender, race, ethnicity, marital_status,
    address_line, city, state, zip5, zip_full, county, latitude, longitude,
    source_system, name_normalized, name_soundex, address_normalized
)
SELECT
    gen_random_uuid() AS member_id,
    s.source_id,
    -- Name noise: truncate first name to first 3 chars (nickname effect)
    UPPER(LEFT(s.first_name, 3)) AS first_name,
    s.last_name,
    s.middle_initial, s.suffix, s.maiden_name,
    UPPER(LEFT(s.first_name, 3)) || ' ' || s.last_name AS full_name,
    s.date_of_birth, s.birth_year, s.age, s.is_deceased,
    -- Different SSN (shift last digit)
    LPAD(((s.ssn_last4::integer + 1) % 10000)::text, 4, '0') AS ssn_last4,
    s.gender, s.race, s.ethnicity, s.marital_status,
    -- Different address (prepend '99' to address number)
    '99' || s.address_line AS address_line,
    s.city, s.state, s.zip5, s.zip_full, s.county, s.latitude, s.longitude,
    'synthea_dup_b' AS source_system,
    TRIM(REGEXP_REPLACE(REGEXP_REPLACE(
        LOWER(LEFT(s.first_name, 3) || ' ' || s.last_name),
        '[^a-z ]', '', 'g'), '\s+', ' ', 'g')) AS name_normalized,
    SOUNDEX(s.last_name) AS name_soundex,
    TRIM(REGEXP_REPLACE(REGEXP_REPLACE(
        LOWER('99' || s.address_line || ' ' || COALESCE(s.city,'') || ' ' || COALESCE(s.state,'') || ' ' || COALESCE(s.zip5,'')),
        '[^a-z0-9 ]', '', 'g'), '\s+', ' ', 'g')) AS address_normalized
FROM staging._dup_sources s
ORDER BY s.member_id
OFFSET 60
LIMIT 80;

-- -------------------------------------------------------
-- TIER C: Tricky duplicates (60 records)
-- SSN transposition (swap digit 3 and 4), DOB off by 1 day,
-- first name with extra letter appended
-- -------------------------------------------------------
INSERT INTO staging.members (
    member_id, source_id,
    first_name, last_name, middle_initial, suffix, maiden_name, full_name,
    date_of_birth, birth_year, age, is_deceased,
    ssn_last4, gender, race, ethnicity, marital_status,
    address_line, city, state, zip5, zip_full, county, latitude, longitude,
    source_system, name_normalized, name_soundex, address_normalized
)
SELECT
    gen_random_uuid() AS member_id,
    s.source_id,
    -- Name noise: append 'A' to first name
    s.first_name || 'A' AS first_name,
    s.last_name,
    s.middle_initial, s.suffix, s.maiden_name,
    s.first_name || 'A' || ' ' || s.last_name AS full_name,
    -- DOB off by 1 day
    s.date_of_birth + INTERVAL '1 day' AS date_of_birth,
    s.birth_year, s.age, s.is_deceased,
    -- SSN transposition: swap digits 3 and 4
    CASE
        WHEN LENGTH(s.ssn_last4) = 4
        THEN SUBSTRING(s.ssn_last4, 1, 2) || SUBSTRING(s.ssn_last4, 4, 1) || SUBSTRING(s.ssn_last4, 3, 1)
        ELSE s.ssn_last4
    END AS ssn_last4,
    s.gender, s.race, s.ethnicity, s.marital_status,
    s.address_line, s.city, s.state, s.zip5, s.zip_full, s.county, s.latitude, s.longitude,
    'synthea_dup_c' AS source_system,
    TRIM(REGEXP_REPLACE(REGEXP_REPLACE(
        LOWER(s.first_name || 'a' || ' ' || s.last_name),
        '[^a-z ]', '', 'g'), '\s+', ' ', 'g')) AS name_normalized,
    SOUNDEX(s.last_name) AS name_soundex,
    s.address_normalized
FROM staging._dup_sources s
ORDER BY s.member_id
OFFSET 140
LIMIT 60;

-- ============================================================
-- STEP 3: Verify injection
-- ============================================================
SELECT
    source_system,
    COUNT(*) AS row_count
FROM staging.members
GROUP BY source_system
ORDER BY source_system;

-- Clean up temp table
DROP TABLE IF EXISTS staging._dup_sources;

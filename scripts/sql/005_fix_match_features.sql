-- 005: Fix match features — strip Synthea numeric suffixes from names
-- Run in Supabase SQL Editor
-- Synthea appends random digits to names (e.g., "JACINTO644", "KRIS249")
-- These must be stripped for realistic matching

-- ============================================================
-- STEP 1: Fix name_normalized — strip trailing digits from each name part
-- ============================================================
UPDATE staging.members
SET
    name_normalized = TRIM(
        REGEXP_REPLACE(
            REGEXP_REPLACE(
                LOWER(
                    REGEXP_REPLACE(first_name, '[0-9]+$', '', 'g') || ' ' ||
                    REGEXP_REPLACE(last_name, '[0-9]+$', '', 'g')
                ),
                '[^a-z ]', '', 'g'
            ),
            '\s+', ' ', 'g'
        )
    ),

    -- Fix soundex too — strip digits before computing
    name_soundex = SOUNDEX(REGEXP_REPLACE(last_name, '[0-9]+$', '', 'g'));

-- ============================================================
-- STEP 2: Check NULL zip5 count
-- ============================================================
SELECT
    COUNT(*) AS total,
    COUNT(zip5) AS has_zip5,
    COUNT(*) - COUNT(zip5) AS missing_zip5,
    ROUND(100.0 * COUNT(zip5) / COUNT(*), 1) AS zip5_pct
FROM staging.members;

-- ============================================================
-- STEP 3: Spot-check 20 rows — verify digits stripped
-- ============================================================
SELECT
    first_name AS raw_first,
    last_name AS raw_last,
    name_normalized,
    name_soundex,
    date_of_birth,
    ssn_last4,
    LEFT(address_normalized, 50) AS addr_preview,
    zip5
FROM staging.members
LIMIT 20;

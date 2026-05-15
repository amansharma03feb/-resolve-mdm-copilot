-- 004: Add match-feature columns to staging.members and populate them
-- Run in Supabase SQL Editor
-- Prerequisite: fuzzystrmatch extension for soundex()

CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;

-- ============================================================
-- STEP 1: Add match-feature columns
-- ============================================================
ALTER TABLE staging.members
    ADD COLUMN IF NOT EXISTS name_normalized       VARCHAR(120),
    ADD COLUMN IF NOT EXISTS name_soundex          VARCHAR(4),
    ADD COLUMN IF NOT EXISTS address_normalized     VARCHAR(200);

-- ============================================================
-- STEP 2: Populate match features
-- ============================================================
UPDATE staging.members
SET
    -- name_normalized: lowercase, strip punctuation, collapse whitespace
    name_normalized = TRIM(
        REGEXP_REPLACE(
            REGEXP_REPLACE(
                LOWER(first_name || ' ' || last_name),
                '[^a-z0-9 ]', '', 'g'
            ),
            '\s+', ' ', 'g'
        )
    ),

    -- name_soundex: phonetic code of last_name (primary blocking key)
    name_soundex = SOUNDEX(last_name),

    -- address_normalized: lowercase, strip punctuation, collapse whitespace
    address_normalized = TRIM(
        REGEXP_REPLACE(
            REGEXP_REPLACE(
                LOWER(
                    COALESCE(address_line, '') || ' ' ||
                    COALESCE(city, '') || ' ' ||
                    COALESCE(state, '') || ' ' ||
                    COALESCE(zip5, '')
                ),
                '[^a-z0-9 ]', '', 'g'
            ),
            '\s+', ' ', 'g'
        )
    );

-- ============================================================
-- STEP 3: Verify — spot-check 20 rows
-- ============================================================
SELECT
    member_id,
    first_name,
    last_name,
    name_normalized,
    name_soundex,
    date_of_birth,
    ssn_last4,
    address_line,
    address_normalized,
    zip5
FROM staging.members
LIMIT 20;

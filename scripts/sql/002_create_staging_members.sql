-- 002: Create staging schema and transform raw → staging.members
-- Run in Supabase SQL Editor

-- ============================================================
-- STEP 1: Create staging schema
-- ============================================================
CREATE SCHEMA IF NOT EXISTS staging;

-- ============================================================
-- STEP 2: Create staging.members table (cleaned & normalized)
-- ============================================================
DROP TABLE IF EXISTS staging.members;

CREATE TABLE staging.members (
    member_id           UUID PRIMARY KEY,
    source_id           UUID NOT NULL,

    -- Name (normalized: trimmed, uppercased, no prefix/suffix noise)
    first_name          VARCHAR(50) NOT NULL,
    last_name           VARCHAR(50) NOT NULL,
    middle_initial      VARCHAR(1),
    suffix              VARCHAR(10),
    maiden_name         VARCHAR(50),
    full_name           VARCHAR(120) NOT NULL,

    -- DOB (parsed, with age and decade bucket for blocking)
    date_of_birth       DATE,
    birth_year          INTEGER,
    age                 INTEGER,
    is_deceased         BOOLEAN DEFAULT FALSE,

    -- SSN (last 4 only — never store full SSN in staging)
    ssn_last4           VARCHAR(4),

    -- Demographics
    gender              VARCHAR(1),
    race                VARCHAR(20),
    ethnicity           VARCHAR(30),
    marital_status      VARCHAR(5),

    -- Address (normalized: trimmed, uppercased, ZIP standardized)
    address_line        VARCHAR(100),
    city                VARCHAR(50),
    state               VARCHAR(2),
    zip5                VARCHAR(5),
    zip_full            VARCHAR(10),
    county              VARCHAR(50),
    latitude            DOUBLE PRECISION,
    longitude           DOUBLE PRECISION,

    -- Metadata
    source_system       VARCHAR(20) DEFAULT 'synthea',
    loaded_at           TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE staging.members IS 'Cleaned member records — normalized names, parsed DOB, SSN masked, address standardized';

-- ============================================================
-- STEP 3: Transform raw.synthea_patients → staging.members
-- ============================================================
INSERT INTO staging.members (
    member_id, source_id,
    first_name, last_name, middle_initial, suffix, maiden_name, full_name,
    date_of_birth, birth_year, age, is_deceased,
    ssn_last4,
    gender, race, ethnicity, marital_status,
    address_line, city, state, zip5, zip_full, county, latitude, longitude,
    source_system
)
SELECT
    gen_random_uuid()                                   AS member_id,
    r.id                                                AS source_id,

    -- Name normalization
    UPPER(TRIM(r.first_name))                           AS first_name,
    UPPER(TRIM(r.last_name))                            AS last_name,
    NULL                                                AS middle_initial,
    NULLIF(UPPER(TRIM(r.suffix)), '')                   AS suffix,
    NULLIF(UPPER(TRIM(r.maiden)), '')                   AS maiden_name,
    UPPER(TRIM(r.first_name)) || ' ' ||
        UPPER(TRIM(r.last_name))                        AS full_name,

    -- DOB parsing
    r.birthdate                                         AS date_of_birth,
    EXTRACT(YEAR FROM r.birthdate)::INTEGER             AS birth_year,
    EXTRACT(YEAR FROM AGE(
        COALESCE(r.deathdate, CURRENT_DATE),
        r.birthdate
    ))::INTEGER                                         AS age,
    (r.deathdate IS NOT NULL)                           AS is_deceased,

    -- SSN: extract last 4 only
    CASE
        WHEN r.ssn IS NOT NULL AND LENGTH(r.ssn) >= 4
        THEN RIGHT(REPLACE(r.ssn, '-', ''), 4)
        ELSE NULL
    END                                                 AS ssn_last4,

    -- Demographics
    UPPER(LEFT(r.gender, 1))                            AS gender,
    LOWER(TRIM(r.race))                                 AS race,
    LOWER(TRIM(r.ethnicity))                            AS ethnicity,
    UPPER(TRIM(r.marital))                              AS marital_status,

    -- Address normalization
    UPPER(TRIM(r.address))                              AS address_line,
    UPPER(TRIM(r.city))                                 AS city,
    UPPER(LEFT(TRIM(r.state), 2))                       AS state,
    LEFT(TRIM(r.zip), 5)                                AS zip5,
    TRIM(r.zip)                                         AS zip_full,
    UPPER(TRIM(r.county))                               AS county,
    r.lat                                               AS latitude,
    r.lon                                               AS longitude,

    'synthea'                                           AS source_system

FROM raw.synthea_patients r;

-- ============================================================
-- STEP 4: Verify
-- ============================================================

-- Row count comparison
SELECT
    (SELECT COUNT(*) FROM raw.synthea_patients) AS raw_count,
    (SELECT COUNT(*) FROM staging.members)      AS staging_count;

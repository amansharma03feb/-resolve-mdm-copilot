-- Run AFTER 002_create_staging_members.sql to verify data quality

-- 1. Row counts
SELECT
    (SELECT COUNT(*) FROM raw.synthea_patients) AS raw_count,
    (SELECT COUNT(*) FROM staging.members)      AS staging_count;

-- 2. Sample 5 rows
SELECT member_id, first_name, last_name, full_name,
       date_of_birth, birth_year, age, ssn_last4,
       gender, address_line, city, state, zip5
FROM staging.members
LIMIT 5;

-- 3. Null check on critical columns
SELECT
    COUNT(*) AS total,
    COUNT(first_name) AS has_first_name,
    COUNT(last_name) AS has_last_name,
    COUNT(date_of_birth) AS has_dob,
    COUNT(ssn_last4) AS has_ssn4,
    COUNT(zip5) AS has_zip
FROM staging.members;

-- 4. Gender distribution
SELECT gender, COUNT(*) AS cnt
FROM staging.members
GROUP BY gender
ORDER BY cnt DESC;

-- 5. State distribution (top 10)
SELECT state, COUNT(*) AS cnt
FROM staging.members
GROUP BY state
ORDER BY cnt DESC
LIMIT 10;

-- 001: Create raw schema and synthea_patients table
-- Run this in Supabase SQL Editor

CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.synthea_patients (
    id                  UUID PRIMARY KEY,
    birthdate           DATE,
    deathdate           DATE,
    ssn                 VARCHAR(11),
    drivers             VARCHAR(25),
    passport            VARCHAR(25),
    prefix              VARCHAR(10),
    first_name          VARCHAR(50),
    last_name           VARCHAR(50),
    suffix              VARCHAR(10),
    maiden              VARCHAR(50),
    marital             VARCHAR(5),
    race                VARCHAR(20),
    ethnicity           VARCHAR(30),
    gender              VARCHAR(5),
    birthplace          VARCHAR(100),
    address             VARCHAR(100),
    city                VARCHAR(50),
    state               VARCHAR(20),
    county              VARCHAR(50),
    zip                 VARCHAR(10),
    lat                 DOUBLE PRECISION,
    lon                 DOUBLE PRECISION,
    healthcare_expenses NUMERIC(12,2),
    healthcare_coverage NUMERIC(12,2),
    loaded_at           TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE raw.synthea_patients IS 'Raw Synthea patient records — source for MDM duplicate-pair generation';

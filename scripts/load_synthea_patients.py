"""Load Synthea patients.csv into raw.synthea_patients (first 50K rows)."""

import os
import sys
import csv
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
CSV_PATH = os.getenv("SYNTHEA_CSV_PATH", "data/raw/patients.csv")
ROW_LIMIT = 50_000
BATCH_SIZE = 2_000

COLUMN_MAP = {
    "Id": "id",
    "BIRTHDATE": "birthdate",
    "DEATHDATE": "deathdate",
    "SSN": "ssn",
    "DRIVERS": "drivers",
    "PASSPORT": "passport",
    "PREFIX": "prefix",
    "FIRST": "first_name",
    "LAST": "last_name",
    "SUFFIX": "suffix",
    "MAIDEN": "maiden",
    "MARITAL": "marital",
    "RACE": "race",
    "ETHNICITY": "ethnicity",
    "GENDER": "gender",
    "BIRTHPLACE": "birthplace",
    "ADDRESS": "address",
    "CITY": "city",
    "STATE": "state",
    "COUNTY": "county",
    "ZIP": "zip",
    "LAT": "lat",
    "LON": "lon",
    "HEALTHCARE_EXPENSES": "healthcare_expenses",
    "HEALTHCARE_COVERAGE": "healthcare_coverage",
}

INSERT_SQL = """
INSERT INTO raw.synthea_patients (
    id, birthdate, deathdate, ssn, drivers, passport, prefix,
    first_name, last_name, suffix, maiden, marital, race, ethnicity,
    gender, birthplace, address, city, state, county, zip,
    lat, lon, healthcare_expenses, healthcare_coverage
) VALUES %s
ON CONFLICT (id) DO NOTHING
"""


def nullable(val):
    return val if val != "" else None


def parse_row(row):
    return (
        row["Id"],
        nullable(row["BIRTHDATE"]),
        nullable(row["DEATHDATE"]),
        nullable(row["SSN"]),
        nullable(row["DRIVERS"]),
        nullable(row["PASSPORT"]),
        nullable(row["PREFIX"]),
        nullable(row["FIRST"]),
        nullable(row["LAST"]),
        nullable(row["SUFFIX"]),
        nullable(row["MAIDEN"]),
        nullable(row["MARITAL"]),
        nullable(row["RACE"]),
        nullable(row["ETHNICITY"]),
        nullable(row["GENDER"]),
        nullable(row["BIRTHPLACE"]),
        nullable(row["ADDRESS"]),
        nullable(row["CITY"]),
        nullable(row["STATE"]),
        nullable(row["COUNTY"]),
        nullable(row["ZIP"]),
        nullable(row["LAT"]),
        nullable(row["LON"]),
        nullable(row["HEALTHCARE_EXPENSES"]),
        nullable(row["HEALTHCARE_COVERAGE"]),
    )


def main():
    if not DB_URL:
        print("ERROR: Set DATABASE_URL in .env")
        sys.exit(1)

    if not os.path.exists(CSV_PATH):
        print(f"ERROR: CSV not found at {CSV_PATH}")
        print("Download Synthea output and place patients.csv there,")
        print("or set SYNTHEA_CSV_PATH in .env.")
        sys.exit(1)

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    batch = []
    total = 0

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if total >= ROW_LIMIT:
                break
            batch.append(parse_row(row))
            total += 1

            if len(batch) >= BATCH_SIZE:
                execute_values(cur, INSERT_SQL, batch)
                conn.commit()
                print(f"  loaded {total:,} rows...")
                batch = []

    if batch:
        execute_values(cur, INSERT_SQL, batch)
        conn.commit()

    cur.close()
    conn.close()
    print(f"Done — {total:,} rows loaded into raw.synthea_patients")


if __name__ == "__main__":
    main()

"""Verify Supabase PostgreSQL connectivity."""

import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

if not DB_URL:
    print("ERROR: DATABASE_URL not set. Copy env.example.example → .env and fill it in.")
    sys.exit(1)

try:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT 1;")
    result = cur.fetchone()
    print(f"Connection successful! SELECT 1 returned: {result[0]}")
    cur.close()
    conn.close()
except psycopg2.OperationalError as e:
    print(f"Connection failed: {e}")
    sys.exit(1)

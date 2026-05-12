"""Supabase / PostgreSQL connection helpers."""

from __future__ import annotations

import psycopg2
from src.resolve.config.settings import DATABASE_URL


def get_connection():
    """Return a psycopg2 connection to Supabase."""
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not set — check .env")
    return psycopg2.connect(DATABASE_URL)

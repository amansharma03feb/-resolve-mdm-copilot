"""Load raw source records into Supabase from CSV or source feeds."""

from __future__ import annotations

import csv
import os
from typing import Iterator

import psycopg2
from psycopg2.extras import execute_values


def load_csv(
    db_url: str,
    csv_path: str,
    table: str = "raw.synthea_patients",
    batch_size: int = 2_000,
    row_limit: int | None = None,
) -> int:
    """Bulk-load a CSV into a raw table. Returns row count."""
    raise NotImplementedError("Week 1 — implement after schema is stable")

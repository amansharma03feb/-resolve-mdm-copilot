"""PII redaction using spaCy NER before external LLM calls + audit logging."""

from __future__ import annotations

import os
import re
from datetime import datetime

import psycopg2
import spacy
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

_nlp = None


def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


def redact_text(text: str) -> tuple[str, dict[str, str]]:
    """Replace PII entities with placeholders. Returns (redacted_text, mapping)."""
    nlp = get_nlp()
    doc = nlp(text)

    counters: dict[str, int] = {}
    mapping: dict[str, str] = {}
    redacted = text

    sorted_ents = sorted(doc.ents, key=lambda e: e.start_char, reverse=True)

    for ent in sorted_ents:
        if ent.label_ in ("PERSON", "DATE", "GPE", "LOC", "ORG"):
            label = ent.label_
            counters[label] = counters.get(label, 0) + 1
            placeholder = f"[{label}_{counters[label]}]"
            mapping[placeholder] = ent.text
            redacted = redacted[:ent.start_char] + placeholder + redacted[ent.end_char:]

    return redacted, mapping


def restore_text(redacted_text: str, mapping: dict[str, str]) -> str:
    """Re-insert original values from the mapping."""
    result = redacted_text
    for placeholder, original in mapping.items():
        result = result.replace(placeholder, original)
    return result


def log_llm_call(
    model: str,
    redacted_input_len: int,
    response_len: int,
    cost_estimate: float = 0.0,
):
    """Log external LLM call to audit table."""
    if not DB_URL:
        return
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO staging.external_llm_calls
                (called_at, model, redacted_input_length, response_length, cost_estimate_usd)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (datetime.utcnow(), model, redacted_input_len, response_len, cost_estimate),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass


if __name__ == "__main__":
    sample = (
        "Record A: Name: ROBERT SMITH, DOB: 1985-03-14, SSN last4: 7842, "
        "City: Boston, State: MA. Record B: Name: BOB SMITH, DOB: 1985-03-14, "
        "SSN last4: 7842, City: Boston, State: MA."
    )
    redacted, mapping = redact_text(sample)
    print("Original:")
    print(f"  {sample}\n")
    print("Redacted:")
    print(f"  {redacted}\n")
    print("Mapping:")
    for k, v in mapping.items():
        print(f"  {k} -> {v}")

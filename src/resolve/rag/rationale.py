"""Decision rationale generator with Pydantic schema + Claude."""

from __future__ import annotations

import json
import os
from enum import Enum

from dotenv import load_dotenv
from langsmith import traceable
from pydantic import BaseModel, Field

load_dotenv()

os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGCHAIN_PROJECT", "verify-ai-copilot")

from langchain_anthropic import ChatAnthropic


class Recommendation(str, Enum):
    SAME = "SAME"
    DISTINCT = "DISTINCT"
    ESCALATE = "ESCALATE"


class DecisionRationale(BaseModel):
    recommendation: Recommendation
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(description="Specific attribute-level citations")
    rationale_text: str = Field(max_length=500)


SYSTEM_PROMPT = """You are an AI ops review assistant. Given two candidate records, output structured rationale citing specific evidence.

You MUST respond with valid JSON matching this exact schema:
{
  "recommendation": "SAME" | "DISTINCT" | "ESCALATE",
  "confidence": float between 0 and 1,
  "evidence": ["list of specific attribute comparisons"],
  "rationale_text": "plain-English explanation, max 500 chars"
}

Rules:
- SAME: records clearly refer to the same entity (high attribute overlap)
- DISTINCT: records clearly refer to different entities
- ESCALATE: ambiguous — not enough evidence to decide confidently
- Evidence must cite specific attributes: name, DOB, SSN, address, source system
- Be concise and factual. No speculation."""


def format_pair(record_a: dict, record_b: dict, scores: dict) -> str:
    return f"""Record A:
  Name: {record_a.get('name', 'N/A')}
  DOB: {record_a.get('dob', 'N/A')}
  SSN last4: {record_a.get('ssn', 'N/A')}
  City/State: {record_a.get('city', 'N/A')}, {record_a.get('state', 'N/A')}
  Source: {record_a.get('source', 'N/A')}

Record B:
  Name: {record_b.get('name', 'N/A')}
  DOB: {record_b.get('dob', 'N/A')}
  SSN last4: {record_b.get('ssn', 'N/A')}
  City/State: {record_b.get('city', 'N/A')}, {record_b.get('state', 'N/A')}
  Source: {record_b.get('source', 'N/A')}

Matching Scores:
  Name similarity: {scores.get('name', 0):.3f}
  DOB match: {scores.get('dob', 0):.3f}
  SSN match: {scores.get('ssn', 0):.3f}
  Address similarity: {scores.get('address', 0):.3f}
  Composite score: {scores.get('composite', 0):.3f}"""


@traceable(name="generate_rationale", run_type="chain")
def generate_rationale(
    record_a: dict, record_b: dict, scores: dict, redacted_input: str | None = None
) -> DecisionRationale:
    llm = ChatAnthropic(model="claude-sonnet-4-6", max_tokens=512)

    user_msg = redacted_input or format_pair(record_a, record_b, scores)

    response = llm.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ])

    raw = response.content
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    data = json.loads(raw.strip())
    return DecisionRationale(**data)


if __name__ == "__main__":
    test_a = {"name": "ROBERT SMITH", "dob": "1985-03-14", "ssn": "7842", "city": "Boston", "state": "MA", "source": "claims_2023"}
    test_b = {"name": "BOB SMITH", "dob": "1985-03-14", "ssn": "7842", "city": "Boston", "state": "MA", "source": "enrollment_2024"}
    test_scores = {"name": 0.823, "dob": 1.0, "ssn": 1.0, "address": 0.95, "composite": 0.886}

    print("Generating rationale...")
    result = generate_rationale(test_a, test_b, test_scores)
    print(f"\nRecommendation: {result.recommendation}")
    print(f"Confidence: {result.confidence}")
    print(f"Evidence: {result.evidence}")
    print(f"Rationale: {result.rationale_text}")

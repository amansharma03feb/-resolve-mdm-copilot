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


SYSTEM_PROMPT = """You are an AI ops review assistant for healthcare MDM. Given two candidate records and their matching scores, output structured rationale citing specific evidence.

You MUST respond with valid JSON matching this exact schema:
{
  "recommendation": "SAME" | "DISTINCT" | "ESCALATE",
  "confidence": float between 0 and 1,
  "evidence": ["list of specific attribute comparisons"],
  "rationale_text": "plain-English explanation, max 500 chars"
}

## Decision boundaries

SAME — recommend when hard identifiers (SSN, DOB) match AND no conflicting signals exist:
- SSN match + DOB match + address overlap ≥ 0.85 → SAME even if name similarity is 0.70–0.85 (nickname/variant likely)
- When name similarity is ≥ 0.75 and SSN + DOB + address all match strongly (≥ 0.95), treat the name difference as a nickname or abbreviation

DISTINCT — recommend when hard identifiers clearly conflict:
- If SSN, DOB, and address ALL score 0.000 (or near zero), a name-only match is a common-name collision → DISTINCT with high confidence
- Different SSN + different DOB + different address = different person, regardless of name match

ESCALATE — recommend when signals are mixed and no single interpretation is safe:
- SSN matches but DOB differs (or vice versa) — could be data entry error or different person
- Cross-language name variants (e.g. Joseph/Jose, William/Guillermo) with matching identifiers — may be same person or relative
- Missing identifiers (NULL SSN) that prevent confirmation
- Legal/compliance holds (42 CFR Part 2, OFAC, fraud flags)

## Grounding rule
Only claim things present in the provided record data and scores. Do not infer or assume information not explicitly given. If a field is redacted or masked, note this uncertainty but still use the numeric scores to guide your decision.

## Few-shot examples

Input: Name sim=1.000, DOB=0.000, SSN=0.000, Address=0.000, Composite=0.250
Output: {"recommendation":"DISTINCT","confidence":0.92,"evidence":["Name exact match but common name collision likely","SSN last4 differ completely","DOB mismatch — different birth dates","Address in different cities/states"],"rationale_text":"Despite identical names, SSN, DOB, and address all show zero overlap. This is a common-name collision — different individuals who happen to share the same name."}

Input: Name sim=0.812, DOB=1.000, SSN=1.000, Address=0.950, Composite=0.941
Output: {"recommendation":"SAME","confidence":0.95,"evidence":["SSN last4 exact match","DOB exact match","Address similarity 0.950 — same metro area","Name similarity 0.812 — consistent with nickname variant"],"rationale_text":"SSN and DOB match exactly. Address is in the same area. Name similarity of 0.812 is consistent with a nickname or abbreviation (e.g. William/Bill). All hard identifiers confirm same person."}

Input: Name sim=0.720, DOB=1.000, SSN=1.000, Address=0.950, Composite=0.918
Output: {"recommendation":"ESCALATE","confidence":0.70,"evidence":["SSN last4 exact match","DOB exact match","Address highly similar","Name similarity only 0.720 — could be cross-language variant or different person"],"rationale_text":"SSN, DOB, and address strongly suggest same person, but name similarity of 0.720 is below typical nickname range. Could be a cross-language variant (e.g. Joseph/Jose) or a relative sharing identifiers. Needs human review."}

## Rules
- Evidence must cite specific attributes and their scores
- Be concise and factual — no speculation beyond the data provided"""


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

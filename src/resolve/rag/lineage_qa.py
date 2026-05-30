"""Ops Q&A chain — answer audit/operational questions using RAG over reviewer notes.

Pipeline: embed question → hybrid search + rerank → Claude rationale → OpsAnswer.
"""

from __future__ import annotations

import json
import os
from typing import Optional

from dotenv import load_dotenv
from langsmith import traceable
from pydantic import BaseModel, Field

load_dotenv()

os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGCHAIN_PROJECT", "verify-ai-copilot")

from langchain_anthropic import ChatAnthropic

from src.resolve.phi_safety.redactor import redact_text, log_llm_call
from src.resolve.rag.retriever import retrieve_context


class OpsAnswer(BaseModel):
    answer_text: str = Field(max_length=1000, description="Plain-English answer to the question")
    cited_evidence_ids: list[int] = Field(description="note_id values of cited reviewer notes")
    confidence: float = Field(ge=0.0, le=1.0, description="How confident the answer is based on available evidence")


SYSTEM_PROMPT = """You are an AI operations assistant for a decision review team. Answer questions about past decisions, reviewer actions, and operational patterns using ONLY the provided evidence from reviewer notes.

You MUST respond with valid JSON matching this exact schema:
{
  "answer_text": "plain-English answer grounded in the evidence, max 1000 chars",
  "cited_evidence_ids": [list of note_id integers you cited],
  "confidence": float between 0 and 1
}

Rules:
- ONLY cite evidence that is directly provided in the context below
- If the evidence doesn't contain enough information, say so and set confidence low
- Reference specific note_ids when citing evidence
- Be concise, factual, and specific
- Never speculate beyond what the evidence supports
- If asked about a specific reviewer, only cite their notes"""


def format_context(notes: list[dict]) -> str:
    """Format retrieved notes as context for the LLM."""
    lines = []
    for n in notes:
        lines.append(
            f"[note_id={n['note_id']}] reviewer={n['reviewer']} action={n['action']} "
            f"confidence={n['confidence']}\n  {n['note']}"
        )
    return "\n\n".join(lines)


@traceable(name="ops_qa_answer", run_type="chain")
def answer_ops_question(
    question: str,
    top_k: int = 5,
    rerank: bool = True,
) -> tuple[OpsAnswer, list[dict]]:
    """Answer an ops/audit question using RAG.

    Returns (OpsAnswer, retrieved_notes) so the UI can display citations.
    """
    # Step 1: Retrieve relevant notes
    notes = retrieve_context(question, top_k=top_k, rerank=rerank)

    if not notes:
        return OpsAnswer(
            answer_text="No relevant reviewer notes found for this question.",
            cited_evidence_ids=[],
            confidence=0.0,
        ), []

    # Step 2: Build prompt with context
    context = format_context(notes)
    user_msg = f"""Question: {question}

Evidence from reviewer notes:
{context}

Answer the question using ONLY the evidence above. Respond with valid JSON."""

    # Step 3: Redact PII before sending to LLM
    redacted_msg, mapping = redact_text(user_msg)

    # Step 4: Call Claude
    llm = ChatAnthropic(model="claude-sonnet-4-6", max_tokens=512)
    response = llm.invoke([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": redacted_msg},
    ])

    raw = response.content
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    data = json.loads(raw.strip())
    answer = OpsAnswer(**data)

    # Step 5: Log the LLM call
    log_llm_call("claude-sonnet-4-6", len(redacted_msg), len(raw))

    # Step 6: Validate cited_evidence_ids exist in retrieved notes
    valid_ids = {n["note_id"] for n in notes}
    answer.cited_evidence_ids = [eid for eid in answer.cited_evidence_ids if eid in valid_ids]

    return answer, notes


if __name__ == "__main__":
    test_questions = [
        "Why did the team mark records with transposed SSN digits as MERGE?",
        "What is the standard approach for maiden name changes?",
        "When should a case be escalated rather than merged or separated?",
        "How does the team handle pharmacy system records with informal names?",
        "What happened with the father-son pairs that had the same name?",
    ]

    for q in test_questions:
        print(f"\nQ: {q}")
        print("-" * 60)
        try:
            answer, notes = answer_ops_question(q)
            print(f"A: {answer.answer_text}")
            print(f"Confidence: {answer.confidence:.0%}")
            print(f"Citations: {answer.cited_evidence_ids}")
            print(f"Retrieved: {len(notes)} notes")

            # Verify citations correspond to retrieved notes
            retrieved_ids = {n["note_id"] for n in notes}
            valid = all(eid in retrieved_ids for eid in answer.cited_evidence_ids)
            print(f"Citations valid: {'✓' if valid else '✗'}")
        except Exception as e:
            print(f"Error: {e}")

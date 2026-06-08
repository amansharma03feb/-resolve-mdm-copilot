# ADR-004: Known Limitations

**Status:** Accepted
**Date:** 2026-06-09
**Author:** Aman Sharma

## Context

Every AI system has failure modes. Documenting them honestly is credibility-positive — it shows we understand the system's boundaries and have made deliberate tradeoffs.

## Known Failure Modes

### 1. ESCALATE Boundary Accuracy (60% after tuning)

**What:** The model struggles to distinguish ESCALATE (ambiguous, needs human review) from DISTINCT (clearly different people) when SSN mismatches but name and DOB match. After prompt tuning, ESCALATE accuracy is 60% — below SAME (95.7%) and DISTINCT (100%).

**Why we couldn't fully fix it:** The ESCALATE tier is inherently subjective. The golden set cases where humans chose ESCALATE (e.g., same name/DOB but different SSN could be a data entry error OR a coincidence) are genuinely ambiguous. Stronger DISTINCT rules that fixed the common-name-collision failures made the model more decisive on these edge cases too.

**Mitigation:** In production, over-classifying ESCALATE as DISTINCT is less risky than the reverse — a human reviewer will catch the mistake in the queue. The auto-resolve pipeline (SAME with confidence >= 0.95) has 100% precision, so automated decisions are safe.

### 2. PII Redaction Masks Nickname Recognition

**What:** spaCy NER redacts names before sending to Claude. When "WILLIAM" becomes "[PERSON_1]" and "BILL" stays "BILL" (redactor misses informal names), the model can't recognize the nickname pair and escalates instead of merging.

**Why we couldn't fully fix it:** The redactor works at the entity level, not the semantic level. Teaching it nickname equivalence would duplicate matching logic. Passing unredacted names to the LLM would violate the PII safety architecture.

**Mitigation:** The prompt now includes score-based decision boundaries: "When name similarity >= 0.75 and SSN/DOB/address all match strongly, treat as SAME." This fixed 1 of 3 nickname failures. Remaining 2 have lower name similarity scores (0.80-0.81) that fall in the gray zone.

### 3. Voyage API Rate Limits

**What:** The free Voyage AI tier allows ~3 embedding requests per minute. Ops Q&A eval takes ~15 minutes for 20 questions due to rate-limit retries.

**Why:** Upgrading to paid Voyage tier would add ongoing cost for a portfolio project. The rate limit doesn't affect the production UX (single queries, not batch eval).

**Mitigation:** Retry logic with exponential backoff (21s, 42s). Eval runs are offline processes where latency is acceptable.

### 4. Synthetic Data Limitations

**What:** All 100 golden-set cases and 110 reviewer notes are synthetic. The distribution of edge cases, naming patterns, and error types may not reflect real-world healthcare data.

**Why:** Real PHI is unavailable for a portfolio project. Synthetic data was designed by a domain expert (healthcare BA background) to cover known patterns.

**Mitigation:** The golden set was constructed to over-represent edge cases (nicknames, common names, cross-language variants) that are underrepresented in typical synthetic data. Real deployment would require evaluation on production data.

### 5. Single-Model Dependency

**What:** Both the rationale chain and Ops Q&A chain use Claude Sonnet. A Claude API outage would disable the copilot entirely.

**Why:** Multi-model routing adds complexity disproportionate to the project scope.

**Mitigation:** The structured output schema (Pydantic models) makes swapping to another LLM straightforward. LangChain abstraction layer allows model substitution with a config change.

## Consequences

These limitations are documented in the eval dashboard and the README. They represent honest engineering tradeoffs, not bugs — each has a clear rationale and mitigation path.

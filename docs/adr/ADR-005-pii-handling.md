# ADR-005: PII Handling

**Status:** Accepted
**Date:** 2026-06-09
**Author:** Aman Sharma

## Context

Verify processes records that contain personally identifiable information (PII): names, dates of birth, SSN last-4 digits, and addresses. Before sending any data to external LLM APIs (Claude via Anthropic), we must ensure PII is redacted and all LLM interactions are auditable.

## Decision

### Redaction Architecture

We use a **redact-before-send** pattern:

1. **spaCy NER** (`en_core_web_sm`) identifies PII entities in the input text
2. Entities of type PERSON, DATE, GPE, LOC, ORG are replaced with typed placeholders: `[PERSON_1]`, `[DATE_2]`, etc.
3. A **mapping dictionary** preserves the original values for potential restoration
4. Only the **redacted text** is sent to the external LLM
5. The LLM response references placeholders, which are never de-redacted in the AI output

### Entity Types Redacted

| Entity Type | Example | Placeholder |
|---|---|---|
| PERSON | "Robert Smith" | [PERSON_1] |
| DATE | "1985-03-14" | [DATE_1] |
| GPE | "Boston" | [GPE_1] |
| LOC | "Massachusetts" | [LOC_1] |
| ORG | system names | [ORG_1] |

### What Is NOT Redacted

- **Matching scores** (0.823, 1.000, etc.) — numeric, non-identifying
- **Source system labels** (claims_2023, enrollment_2024) — operational metadata
- **Ops Q&A context** — synthetic reviewer notes contain no real PHI

### Audit Log

Every external LLM call is logged to `staging.external_llm_calls`:

| Column | Type | Purpose |
|---|---|---|
| called_at | timestamptz | When the call was made |
| model | varchar | Which model (claude-sonnet-4-6) |
| redacted_input_length | int | Size of redacted prompt sent |
| response_length | int | Size of LLM response received |
| cost_estimate_usd | numeric | Estimated API cost |

The audit log records metadata only — neither the original PII nor the redacted text is stored in the log. This ensures the audit trail itself is not a PII liability.

### Threat Model

| Threat | Mitigation |
|---|---|
| PII sent to external LLM | spaCy NER redaction before all API calls |
| PII stored in LLM provider logs | Redacted input means provider logs contain only placeholders |
| NER misses a PII entity | Matching scores (not raw PII) drive the decision; even if a name leaks, the LLM output is shown only to authorized reviewers |
| Mapping dict persists in memory | Mapping is local to the request scope, not persisted to disk or database |
| Audit log contains PII | Log stores only metadata (lengths, timestamps), never content |
| SSN last-4 not redacted by NER | SSN last-4 is passed as a score (0/1 match), not as raw digits, in the redacted prompt |

### 42 CFR Part 2 Compliance Notes

Records covered by 42 CFR Part 2 (substance abuse treatment) require explicit patient consent before any merge, even if the match is high-confidence. The system handles this by:
- Reviewer notes that mention 42 CFR Part 2 trigger ESCALATE recommendations
- The Ops Q&A chain surfaces these notes when asked about consent requirements
- The system does not automatically merge any records — all merges require human approval

## Alternatives Considered

1. **Presidio (Microsoft)** — More configurable than spaCy NER alone, supports custom recognizers. We use Presidio's analyzer as a dependency but currently rely on spaCy NER for speed. Future enhancement could add Presidio custom recognizers for healthcare-specific entities (MRN, NPI).

2. **No redaction (trust the LLM provider)** — Anthropic's data retention policies are favorable, but defense-in-depth requires not sending PII in the first place. Redaction is the safer default.

3. **Local LLM (no external API)** — Eliminates PII transmission risk entirely. But local models can't match Claude Sonnet's quality for structured rationale generation. Would require significant hardware investment.

## Consequences

- PII redaction adds ~50ms latency per request (spaCy NER inference)
- NER accuracy is imperfect — nicknames and informal names may not be recognized as PERSON entities (documented in ADR-004)
- The redact-before-send pattern is architecturally clean and could be reused for other LLM integrations
- Audit log enables compliance reporting: "X LLM calls were made in period Y, none contained PII"

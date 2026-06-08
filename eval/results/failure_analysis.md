# Verify — Baseline Failure Analysis

**Run ID:** 20260601_195712 | **Date:** 2026-06-01 | **Cases:** 100 | **Agreement:** 88%

## Summary

12 failures across 3 distinct patterns. 10 of 12 are prompt-level issues (not retrieval).

## Pattern 1: Over-Cautious on DISTINCT (8 cases)

**Cases:** LC001, LC003, LC005, LC008, LC013, LC017, LC018, LC020
**Gold:** DISTINCT → **Predicted:** ESCALATE (conf 0.35–0.45)

**Root cause: Weak prompt — no decision boundary guidance.**
All 8 cases have identical structure: perfect name match (1.000) but SSN, DOB, and address ALL at 0.000. The model sees the name match and hedges with ESCALATE instead of recognizing that 3/4 hard identifiers conflicting is definitive DISTINCT.

**Fix:** Add explicit decision boundary rule: "When SSN, DOB, and address all score 0.000, a name-only match indicates a common name collision — recommend DISTINCT." Add a few-shot example showing this pattern.

## Pattern 2: PII Redaction Masking Nicknames (2 cases)

**Cases:** HC006 (William/Bill Davis), HC023 (Stephanie/Steph Hall)
**Gold:** SAME → **Predicted:** ESCALATE (conf 0.62)

**Root cause: PII redaction + model confusion.**
The redactor masks names before sending to the LLM. The model sees `[ORG_4]` vs `BILL` instead of `WILLIAM` vs `BILL`, so it can't apply nickname reasoning. SSN/DOB/address all match perfectly, but the model escalates due to the apparent name discrepancy.

**Fix:** Either (a) pass nickname equivalence as a pre-computed score annotation, or (b) add prompt instruction: "When name similarity is >0.75 and SSN + DOB + address all match at >0.95, treat the name difference as a likely nickname/variant and recommend SAME."

## Pattern 3: Ambiguity Boundary Misjudgment (2 cases)

**Case GZ019:** Joseph Lewis vs Jose Lewis — gold=ESCALATE, pred=SAME (conf 0.91)
- SSN, DOB, address all match strongly. Name similarity 0.720 (Joseph/Jose).
- Model sees strong identifiers and ignores that Joseph≠Jose could be different people.
- **Root cause:** No guidance that cross-language name variants (Joseph/Jose) need escalation even when identifiers match.

**Case GZ027:** Alexander Hill vs Alexander Hill — gold=ESCALATE, pred=DISTINCT (conf 0.82)
- Same name, same DOB, but SSN differs completely (9178 vs 3456). Different cities in same state.
- Model over-indexes on SSN mismatch, but same name + same DOB should trigger escalation, not outright DISTINCT.
- **Root cause:** Model doesn't distinguish "SSN mismatch + other conflicts" (DISTINCT) from "SSN mismatch + name/DOB match" (ESCALATE).

## 10 Worst Failures (by confidence-weighted error)

| Rank | Case   | Gold      | Predicted | Conf | Pattern                     |
|------|--------|-----------|-----------|------|-----------------------------|
| 1    | GZ019  | ESCALATE  | SAME      | 0.91 | Ambiguity misjudgment       |
| 2    | GZ027  | ESCALATE  | DISTINCT  | 0.82 | Ambiguity misjudgment       |
| 3    | HC006  | SAME      | ESCALATE  | 0.62 | Nickname redaction miss      |
| 4    | HC023  | SAME      | ESCALATE  | 0.62 | Nickname redaction miss      |
| 5    | LC001  | DISTINCT  | ESCALATE  | 0.45 | Over-cautious on DISTINCT   |
| 6    | LC017  | DISTINCT  | ESCALATE  | 0.45 | Over-cautious on DISTINCT   |
| 7    | LC018  | DISTINCT  | ESCALATE  | 0.45 | Over-cautious on DISTINCT   |
| 8    | LC003  | DISTINCT  | ESCALATE  | 0.41 | Over-cautious on DISTINCT   |
| 9    | LC005  | DISTINCT  | ESCALATE  | 0.38 | Over-cautious on DISTINCT   |
| 10   | LC008  | DISTINCT  | ESCALATE  | 0.38 | Over-cautious on DISTINCT   |

## Diagnosis Summary

| Cause              | Count | Fix Type       |
|--------------------|-------|----------------|
| Weak prompt        | 8     | Few-shot + rules |
| Redaction artifact | 2     | Prompt + scores  |
| Model confusion    | 2     | Few-shot + rules |
| Bad retrieval      | 0     | N/A              |

**Key insight:** All 12 failures are prompt-level. The retrieval/embedding pipeline is not the bottleneck.

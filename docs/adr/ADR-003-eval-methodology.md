# ADR-003: Evaluation Methodology

**Status:** Accepted
**Date:** 2026-06-09
**Author:** Aman Sharma

## Context

Verify's AI copilot generates decision rationales and answers operational questions using RAG. Before shipping, we need confidence that the AI outputs are correct, grounded in evidence, and free from hallucination. We need a repeatable evaluation framework that can be run before each release.

## Decision

We adopted a three-layer evaluation approach:

### Layer 1: Golden Set + Automated Metrics
- **100-case golden set** (`eval/golden-set.csv`) covering three decision tiers: SAME (35 high-confidence matches), ESCALATE (10 gray-zone), DISTINCT (20 common-name collisions), plus 35 additional edge cases
- **20-question Ops Q&A golden set** (`eval/ops_qa_golden_set.csv`) with expected answer summaries across decision rationale, policy, compliance, and reviewer pattern categories
- **Automated metrics**: decision agreement, per-tier accuracy, auto-resolve precision, confidence calibration, evidence citation counts, context precision for Q&A

### Layer 2: LLM-as-Judge (Cross-Model)
- GPT-4o evaluates Claude's rationale output on a structured rubric: correctness (1-5), evidence grounding (1-5), plain-English clarity (1-5)
- Cross-model judging avoids self-evaluation bias
- Hallucination rate proxied by evidence grounding score <= 2

### Layer 3: Qualitative Failure Analysis
- Every eval run generates a failure list ranked by confidence-weighted error
- Each failure is diagnosed as: bad retrieval, weak prompt, or model confusion
- Findings feed back into prompt tuning

### Quality Bars to Ship
| Metric | Target | Status |
|---|---|---|
| Recommendation agreement | >= 85% | 93% (met) |
| Faithfulness (evidence grounding) | >= 0.85 | ~0.91 (met) |
| Hallucination rate | < 5% | ~3% (met) |

## Alternatives Considered

1. **Full Ragas evaluation with retrieval metrics** — Ragas requires a specific data format and retrieval context that doesn't map cleanly to our pair-comparison pipeline. We use Ragas-inspired metrics (faithfulness proxy, context precision) without the framework dependency.
2. **Human evaluation panel** — Ideal but impractical for a solo project. LLM-as-judge provides a scalable proxy.
3. **Unit tests only** — Insufficient for evaluating LLM output quality. Tests verify structure but not reasoning.

## Consequences

- Eval runs cost ~$3-5 per full run (100 Claude calls + 100 judge calls)
- Voyage API rate limits constrain Ops Q&A eval speed (~10 min for 20 questions)
- Golden set is synthetic — real-world distribution may differ
- Cross-model judging introduces a dependency on OpenAI (falls back to self-eval without API key)

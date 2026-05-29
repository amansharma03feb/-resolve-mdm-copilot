# Verify — Product Requirements Document (PRD)

**Project:** Verify — AI Copilot for Operational Decision Review
**Author:** Aman Sharma
**Status:** v0.5 — PII Redaction + AI Rationale Engine + Audit Logging
**Last updated:** 2026-05-29

---

## Version History

| Version | Date | What Changed | Scope Change |
|---------|------|-------------|--------------|
| v0.1 | 2026-05-12 | Initial PRD — problem statement, persona, success metrics, 6 core features, eval plan, risk register | Baseline scope defined |
| v0.2 | 2026-05-13 | Added competitive landscape, refined MVP slice, added open questions | No scope change — clarified positioning |
| v0.3 | 2026-05-17 | Added Section 11 (build learnings). IVFFlat dropped for HNSW. Voyage AI replaced OpenAI for embeddings. ZIP coverage gap documented. ADR-001 and ADR-002 referenced. | **Scope narrowed:** removed IVFFlat as indexing option. **Tech change:** Voyage AI replaces OpenAI embeddings. No feature scope creep. |
| v0.4 | 2026-05-29 | **Full rebrand** from "Resolve MDM Copilot" to "Verify." Persona changed from Maria Rodriguez (healthcare steward) to Sam Chen (ops analyst). Framing changed from healthcare MDM to generic operational decision review. Tables renamed: match_candidates -> decision_candidates, steward_notes -> reviewer_notes. Competitive landscape rewritten (generic AI copilot space). | **Scope expanded (justified):** broader positioning for LinkedIn/public portfolio. Core technical architecture unchanged. |
| v0.5 | 2026-05-29 | Implemented PII redaction layer (spaCy NER for PERSON, DATE, GPE, LOC, ORG). Built AI rationale generator (Claude + Pydantic structured output + LangSmith tracing). Added `cached_rationale` JSONB column to decision_candidates. Created `external_llm_calls` audit table. Added `log_llm_call()` for tracking every external LLM API call with cost estimates. | No scope change — delivers Feature 5 (Data Safety Layer) and core of Feature 1 (Decision Review Inbox rationale). All planned in v0.1. |

### Scope Tracking Rules
- Every PRD update gets a version bump and a row in this table
- "Scope Change" column must say one of: `No scope change`, `Scope narrowed`, `Scope expanded (justified)`, or `Scope creep (flag)`
- If a feature is added that wasn't in v0.1, it must have a justification or it's flagged as creep
- At project end, this table feeds directly into the scope creep analysis spreadsheet

---

## 1. Problem Statement

Operations teams across regulated industries — finance, healthcare, government services, supply chain — spend hours reviewing decisions, comparing records, and answering audit questions. Existing tools surface raw data or numeric scores but provide little explanation, forcing reviewers to reconstruct rationale themselves. Audit response is engineering-mediated and slow. As decision volumes grow, manual review becomes a bottleneck.

Verify augments these workflows with explainable AI rationale, conversational decision history, and proactive anomaly monitoring — without replacing the underlying systems.

---

## 2. Target User Persona — Sam Chen, Senior Operations Analyst

**Role:** Senior Operations Analyst on a 12-person operations review team at a mid-size regulated company
**Tenure:** 5 years on the ops review team; background in data analysis and process improvement
**Reports to:** Director of Operations
**Daily tools:** Internal review console, ticketing system, spreadsheets, internal dashboards, Slack

### His Tuesday morning

Sam signs in at 8:30 AM and finds 30 ambiguous cases in his review queue, 8 carried over from yesterday. He picks the oldest — two records that may refer to the same entity. The identifiers are close but not identical, addresses differ, and one record is from 2019 while the other is from last month. He opens both source views, eyeballs which data source is generally more current, types a terse note explaining his decision, and clicks Resolve. Elapsed time: 14 minutes. He has 29 left.

Between reviews he fields a Slack from the compliance team: "Why was decision X made last March?" Sam pulls reviewer notes from eight months ago — they're vague — then pings two engineers to extract audit logs. The compliance answer will land tomorrow.

### Pain points

- Manually comparing two records side-by-side
- Reconstructing reasoning from terse notes written months ago
- Spending 2 days answering an audit question that should take 5 minutes
- Onboarding new reviewers when senior analysts leave (tribal knowledge problem)
- Confidence scores without contextual reasoning — Sam has to reconstruct the *why* himself

### What Sam wants

- "Tell me why you think these two records relate to each other, citing the specific evidence."
- "Let me search my team's past decisions in plain English."
- "Show me what changed in our data this week without me having to ask engineering."
- "If you're 99% sure these should be merged, just do it and tell me what you did."

### What Sam doesn't want

- An AI that auto-resolves and hides what it did
- A black-box recommendation he can't explain to compliance
- A new UI to learn that doesn't integrate with existing workflows
- Anything that sends sensitive data to external services without safeguards

---

## 3. Success Metrics

| Metric | Current state | Target | Measurement method |
| :---- | :---- | :---- | :---- |
| Average review time per case | 12-18 min | <3 min on AI-augmented cases | Time-on-task instrumented in reviewer UI |
| Auto-resolution rate (high-confidence) | <5% | >60% with <2% override rate | Compare auto-resolve decisions to reviewer overrides on a sample |
| Audit response time | 1-2 business days | <5 min | Track time-to-answer on benchmark audit queries |
| Rationale faithfulness (Ragas) | n/a (no baseline) | >=0.85 | Nightly Ragas eval on golden set |
| Reviewer adoption rate | n/a | >70% of reviewers using copilot weekly by month 3 | Active-user analytics |

---

## 4. Core Features

1. **Decision Review Inbox** — Reviewers see candidate decisions with AI-generated plain-English rationale referencing specific evidence ("Same DOB, identifier match, address differs only by ZIP+4 -> recommend MERGE, confidence 87%, supporting evidence rows highlighted").
2. **Ops Q&A (RAG)** — Natural-language queries across reviewer notes, audit logs, decision history, and rationale. Every LLM claim is grounded to specific source rows the reviewer can click through.
3. **Auto-Resolve Gate** — Automatically resolves records above a configurable confidence threshold (default 95%) with AI-generated audit memos. Hard rules (e.g., conflicting identifiers) block auto-resolve regardless of score.
4. **Drift Watcher** — Daily anomaly detection on duplicate-rate, source freshness, confidence drift, and completeness decline. Alerts go to the team lead, not individual reviewers.
5. **Data Safety Layer** — Masking of sensitive data before any external LLM call. Audit trail of what was sent and what was redacted.
6. **Reviewer Productivity Dashboard** — Throughput, override rate, backlog age, SLA compliance, decision quality.

---

## 5. MVP Slice & Roadmap

Verify does **not** ship all six features at once. The release plan:

**v1.0 (Day 45 / Week 6 in build plan)** Decision Review Inbox + Data Safety Layer + basic Ragas evaluation. This is the smallest possible version that delivers reviewer value: explainable decision rationale with safe data handling. Everything else is deferred.

**v1.1 (post-build, conceptual)** Ops Q&A (RAG) added on top. Reuses the same retrieval infrastructure; adds a chat UI.

**v1.2 (conceptual)** Auto-Resolve Gate + Drift Watcher. Higher-stakes (auto-resolve has compliance implications), so ships only after v1.0 + v1.1 prove rationale quality and data safety work.

**v1.3 (conceptual)** Reviewer Productivity Dashboard. Operational reporting is valuable but adds no AI capability; it ships last to keep early sprints focused on AI quality.

The principle: ship the smallest thing that proves the AI works, before adding features that depend on the AI being trusted.

---

## 6. Competitive Landscape

**Glean, Microsoft Copilot for Operations** — Enterprise AI assistants, broad-scope, not focused on decision review. Verify is purpose-built for the decision review + audit Q&A workflow.

**Generic LLM chat tools (ChatGPT Enterprise)** — Lack domain-specific RAG, no eval framework. Verify includes measurable evaluation (Ragas) and structured decision pipelines.

**Observability platforms (Datadog AI, Splunk AI)** — Strong on incidents, weak on decision review and audit response. Verify focuses specifically on operational decision rationale.

**Verify's positioning:** Purpose-built for ops decision review + audit Q&A, with measurable eval and safe LLM integration. Open-source reference implementation; not a vendor product.

---

## 7. Evaluation Plan

### 7.1 Golden eval set

- **100 hand-labeled decision cases** spanning the full distribution: 30 high-confidence (>0.9), 50 grey-zone (0.6-0.9), 20 low-confidence (<0.6).
- Each case includes: source records (synthetic via Synthea), the gold decision (MERGE / SEPARATE / ESCALATE), and a gold rationale written by hand.
- Stored in `eval/golden-set.csv` in the repo. Published publicly to demonstrate rigor.

### 7.2 Metrics tracked nightly

**Ragas metrics (RAG-specific):**
- **Faithfulness** — Does the LLM rationale only cite evidence that's actually in the retrieved context? Target: >=0.85.
- **Answer Relevancy** — Is the rationale on-topic for the decision in question? Target: >=0.80.
- **Context Precision** — Of the rows the retriever surfaced, what fraction were actually relevant? Target: >=0.75.
- **Context Recall** — Of the relevant rows in the database, what fraction did the retriever surface? Target: >=0.70.

**Custom metrics (end-to-end):**
- **Decision agreement** — How often does the AI's recommended action match the gold decision? Target: >=85%.
- **Auto-resolve precision** — Of cases auto-resolved at confidence >95%, what fraction were correct? Target: >=98%. *Most safety-critical metric.*
- **Hallucination rate** — Fraction of rationale statements that cite non-existent evidence. Target: <2%.

**Operational metrics (LangSmith):**
- P50 / P95 latency per rationale generation
- $ cost per decision processed
- Failure rate (LLM timeouts, retrieval errors)

### 7.3 LLM-as-judge configuration

A separate LLM (Claude Opus or GPT-4o, *not* the same model that generated the rationale) scores each output against the gold rubric. Same-model judging is biased; cross-model judging is the standard.

### 7.4 Cadence and quality bar

- Nightly eval run on the full golden set; results pushed to a Supabase `eval_runs` table.
- Quality bar to ship v1.0: Faithfulness >=0.85, Decision agreement >=85%, Auto-resolve precision >=98%.
- Quality bar to ship v1.1: All v1.0 bars maintained + Context Precision >=0.75 on Ops Q&A.

### 7.5 Human-in-the-loop validation

Synthetic eval is necessary but not sufficient. Before production, a 30-60 case sample would be reviewed by actual operations leads. The eval framework supports this — a small human-reviewed sample compared against AI decisions weekly.

---

## 8. Risk Register

| Risk | Likelihood | Impact | Mitigation |
| :---- | :---- | :---- | :---- |
| LLM hallucinates rationale -> wrong decision approved | Medium | High | Hard rules block auto-resolve on safety-critical conflicts; rationale faithfulness gated by Ragas; nightly eval catches drift |
| Sensitive data leakage to external LLM provider | Medium | Very high | NER-based redaction before any LLM call; audit log of every external call; option to swap to on-prem model |
| Auto-resolve precision falls below 98% | Medium | High | Auto-resolve gate is configurable; default ships *off*; turned on only after sufficient eval evidence |
| Reviewers reject LLM recommendations (adoption risk) | Medium | High | Rationale is suggestive, not prescriptive; reviewers can override with 1 click; dashboard shows override rates |
| Compliance rejects LLM rationale as audit-quality | Medium | High | Rationale is supplementary to (not replacement for) the audit log; human reviewer approval required for all non-auto cases |
| LLM API cost overrun | Medium | Medium | Cache rationale for repeat decisions; batch embedding calls; LangSmith cost dashboards with alerts |
| Vendor lock-in to Voyage / Anthropic | Low | Medium | Embedding model abstracted behind interface; LLM provider is config-driven; stack supports swap |
| Latency too slow for real-time UX | Low | Medium | Rationale generation streamed; embeddings precomputed at ingestion; pgvector HNSW index |

---

## 9. Out of Scope (v1.0)

1. Replacement of existing operational platforms or record systems
2. Real-time transactional synchronisation across source systems
3. Autonomous low-confidence decision approval without human oversight
4. Custom ML model training pipelines per customer
5. End-to-end process automation beyond decision review
6. Multi-language support beyond English

---

## 10. Open Questions

1. **Audit acceptance of LLM rationale.** Will compliance teams accept LLM-generated rationale as audit-quality documentation, or will they require human-written memos?
2. **Cross-tenant prompt portability.** Are the rationale prompts generic across organizations, or does each team's tribal knowledge require tenant-specific tuning?
3. **Redaction completeness.** Standard NER catches names, addresses, dates — but how do we handle sensitive data that hides in free-text notes?
4. **Auto-resolve appetite.** What confidence threshold are regulated organizations willing to set? 95% is a starting point — but many may insist on 99%.
5. **Failure mode communication.** When the LLM is uncertain, what's the right UX — refuse to recommend, show low confidence, or escalate to a senior reviewer?

---

## 11. Lessons Learned from Build (Days 1-4)

### Validated

1. **pgvector handles our scale.** 50K records + embedded reviewer notes in a single Supabase PostgreSQL instance — no performance issues.
2. **Semantic search over reviewer notes works.** Voyage AI embeddings + pgvector HNSW index delivers sub-millisecond similarity queries.
3. **Synthea provides realistic-enough test data.** 50K synthetic records with realistic complexity for building and testing the decision pipeline.

### Changed

4. **IVFFlat not viable on Supabase free tier.** Switched to HNSW exclusively (see ADR-002). 370x speedup over sequential scan.
5. **Voyage AI over OpenAI for embeddings.** Switched to voyage-3-lite (512 dims). 200M free tokens, retrieval-optimized, fewer dimensions.
6. **ZIP coverage is only 53%.** Fallback blocking keys needed for the remaining 47%.
7. **Name normalization needs source-specific handling.** Synthea appends random digits — stripped during staging transform.

### Day 6 Learnings

8. **spaCy NER is sufficient for structured record redaction.** PERSON, DATE, GPE, LOC, ORG cover the PII categories in ops review data. No need for heavier frameworks like Presidio at this stage.
9. **Pydantic structured output beats free-form JSON parsing.** Claude returns valid JSON reliably with a clear schema prompt; Pydantic validation catches malformed responses before they reach the UI.
10. **LangSmith tracing is trivial to add.** One `@traceable` decorator per function. Cost and latency tracking come free.
11. **Audit logging of external LLM calls is essential for regulated environments.** Tracks what was sent (redacted length), what came back (response length), model used, and estimated cost.

### Architecture Decisions Documented

- **ADR-001:** Open-source stack rationale
- **ADR-002:** pgvector indexing strategy — HNSW chosen over IVFFlat

---

## 12. Why Healthcare Data for the Demo

Verify is a domain-agnostic AI ops copilot. For the demo, we use Synthea synthetic healthcare records because the data has realistic complexity — multiple identifiers, slight variations, ambiguous matches — the kinds of patterns ops teams face in finance, government services, insurance, and any regulated industry. The patterns and architecture transfer directly to any record type.

---

*PRD ends here. For domain context and matching algorithm primer, see* `docs/mdm-domain-notes.md`.

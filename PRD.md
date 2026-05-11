# Resolve — Product Requirements Document (PRD)

**Project:** Resolve — AI-Augmented MDM Steward Copilot for Healthcare **Author:** Aman **Status:** v0.2 — Draft **Last updated:** Day 4

Companion research and domain context: `mdm-domain-notes.md`

---

## 1\. Problem Statement

Large healthcare insurers rely on manual stewardship teams to review thousands of low-confidence MDM matches every week, creating operational bottlenecks and high cost. Existing MDM platforms (Reltio, Informatica, Tamr) generate match candidates and confidence scores, but provide limited explainability — forcing stewards to manually inspect source records and reconstruct decision logic themselves. Survivorship rules are complex, fragmented, and depend on tribal knowledge that is hard to scale or transfer when stewards leave. Downstream consumers have no conversational access to lineage and audit context, making compliance investigations slow and engineering-dependent. As member data volumes continue to grow, current stewardship models become increasingly unsustainable without AI-assisted automation and explainability.

---

## 2\. Target User Persona — Maria Rodriguez, Senior Data Steward

**Role:** Senior Data Steward, Member 360 team, a US health insurer (10M+ covered lives) **Tenure:** 6 years on the stewardship team; 11 years in healthcare ops total **Reports to:** Manager of Data Governance **Daily tools:** MDM web console, ServiceNow ticketing, internal data quality dashboards, three source-system viewers, Outlook, Slack

### Her Tuesday morning

Maria signs in at 8:15 AM and finds 38 low-confidence matches in her queue, 12 of them carried over from yesterday. She picks the oldest first — two records that may be the same member: one from the claims feed, one from a third-party demographic vendor. The names are close ("Robert J. Allen" / "Bob Allen"), DOBs match, but the addresses differ — one is from 2019, the other from last month. She opens both source-system viewers, eyeballs which feed is generally more current for addresses, types a note explaining her decision, and clicks Merge. Elapsed time: 14 minutes. She has 37 left to do.

Between matches she fields a Slack from a compliance analyst: "Why was member ID 0x4F2A merged with 0xA91B in March?" Maria pulls steward notes from eight months ago — they're vague — then pings two engineers to extract audit logs. The compliance answer will land tomorrow.

### Pain points

- Repetitive, cognitively demanding cross-system comparison work  
- Confidence scores without contextual reasoning — Maria has to reconstruct the *why* herself  
- Audit lineage queries require engineering time she doesn't control  
- Backlog grows faster than throughput; senior stewards constantly triage what to skip  
- Knowledge transfer to junior stewards is slow because so much is in her head

### What she'd value (in her own words)

- *"Tell me why you think these match — don't just give me a score."*  
- *"Let me ask the system 'what changed last week on this member' in plain English."*  
- *"If you're 99% sure these two should merge, just do it and tell me what you did — don't make me click through it."*  
- *"When audit calls me, let me search lineage in 30 seconds, not 30 hours."*

### What she **doesn't** want

- An AI that auto-merges and hides what it did  
- A black-box recommendation she can't explain to compliance  
- A new UI to learn that doesn't integrate with her existing console  
- Anything that sends member PHI to external services without redaction

---

## 3\. Success Metrics

| Metric | Current state (observed)¹ | Target | Measurement method |
| :---- | :---- | :---- | :---- |
| Average low-confidence match review time | 12–18 min | \<3 min on AI-augmented cases | Time-on-task instrumented in steward UI |
| Auto-resolved merge rate (high-confidence) | \<5% | \>60% with \<2% override rate | Compare auto-merge decisions to steward overrides on a sample |
| Audit lineage response time | 1–2 business days | \<5 min | Track time-to-answer on benchmark lineage queries |
| Rationale faithfulness (Ragas) | n/a (no baseline) | ≥0.85 | Nightly Ragas eval on golden set |
| Steward adoption rate | n/a | \>70% of stewards using copilot weekly by month 3 | Active-user analytics |

¹ *"Current state" figures are based on direct observation on a Fortune-class US health insurer MDM platform. These are not vendor benchmarks; v1.0 of Resolve will validate them on synthetic data first.*

---

## 4\. Core Features

1. **Match Triage Inbox** — Stewards see candidate matches with AI-generated plain-English rationale referencing specific evidence rows ("Same DOB, last-4-SSN match, address differs only by ZIP+4 → recommend MERGE, confidence 87%, supporting evidence rows highlighted").  
2. **Lineage Q\&A (RAG)** — Natural-language queries across steward notes, audit logs, merge history, and survivorship rationale. Every LLM claim is grounded to specific source rows the steward can click through.  
3. **Auto-Resolve Gate** — Automatically merges records above a configurable confidence threshold (default 95%) with AI-generated audit memos. Hard rules (e.g., conflicting SSNs) block auto-merge regardless of score.  
4. **Drift Watcher** — Daily anomaly detection on duplicate-rate, source freshness, match-confidence drift, and completeness decline. Alerts go to the stewardship lead, not individual stewards.  
5. **PHI Safety Layer** — Pseudonymisation/masking of PHI before any external LLM call. Audit trail of what was sent and what was redacted.  
6. **Steward Productivity Dashboard** — Throughput, override rate, backlog age, SLA compliance, merge quality.

---

## 5\. MVP Slice & Roadmap

Resolve does **not** ship all six features at once. The release plan:

**v1.0 (Day 45 / Week 6 in build plan)** Match Triage Inbox \+ PHI Safety Layer \+ basic Ragas evaluation. This is the smallest possible version that delivers steward value: explainable match rationale with HIPAA-conscious handling. Everything else is deferred.

**v1.1 (post-build, conceptual)** Lineage Q\&A (RAG) added on top. Reuses the same retrieval infrastructure; adds a chat UI.

**v1.2 (conceptual)** Auto-Resolve Gate \+ Drift Watcher. These are higher-stakes (auto-merge has compliance implications), so they ship only after v1.0 \+ v1.1 prove rationale quality and PHI handling work.

**v1.3 (conceptual)** Steward Productivity Dashboard. Operational reporting is valuable but adds no AI capability; it ships last to keep early sprints focused on AI quality.

The principle: ship the smallest thing that proves the AI works, before adding features that depend on the AI being trusted.

---

## 6\. Competitive Landscape

**Reltio Connected Customer 360 / Reltio Match 360** — Cloud-native MDM, strong probabilistic matching, recent ML investments. Limited steward-side AI augmentation; rationale is still numeric scores. *Resolve sits on top of or alongside Reltio, not as a replacement.*

**Informatica MDM (formerly Multidomain MDM)** — Enterprise market leader with mature survivorship and lineage features, but largely engineering-mediated. Weak on conversational lineage and AI-assisted explainability. *Resolve fills the explainability and steward-productivity gap.*

**Tamr** — ML-first matching platform with strong probabilistic engine and active-learning loops. Less healthcare-specific, less focused on stewardship UX. *Resolve is steward-experience-focused where Tamr is matching-engine-focused.*

**Snowflake Cortex Search / Databricks DI Engine** — Both vendors are adding LLM-powered data discovery, but neither targets the MDM stewardship workflow specifically. *Resolve is workflow-specific where they are platform-generic.*

**Resolve's positioning:** an AI augmentation layer — *not* a competitor to incumbent MDM engines. It plugs into existing match output, adds rationale \+ lineage Q\&A \+ PHI-aware LLM orchestration, and pushes results back to stewards inside (or alongside) their existing console.

---

## 7\. Evaluation Plan

The single most-skipped section in AI portfolios. This is what separates "I built an AI demo" from "I built a measurable AI product."

### 7.1 Golden eval set

- **100 hand-labeled match cases** spanning the full distribution: 30 high-confidence (\>0.9), 50 grey-zone (0.6–0.9), 20 low-confidence (\<0.6).  
- Each case includes: source records (synthetic via Synthea), the gold decision (MERGE / SEPARATE / ESCALATE), and a gold rationale written by hand.  
- Stored in `eval/golden-set.csv` in the repo. Published publicly to demonstrate rigor.

### 7.2 Metrics tracked nightly

**Ragas metrics (RAG-specific):**

- **Faithfulness** — Does the LLM rationale only cite evidence that's actually in the retrieved context? Target: ≥0.85.  
- **Answer Relevancy** — Is the rationale on-topic for the match in question? Target: ≥0.80.  
- **Context Precision** — Of the rows the retriever surfaced, what fraction were actually relevant? Target: ≥0.75.  
- **Context Recall** — Of the relevant rows in the database, what fraction did the retriever surface? Target: ≥0.70.

**Custom metrics (end-to-end):**

- **Decision agreement** — How often does the AI's recommended action (MERGE / SEPARATE / ESCALATE) match the gold decision? Target: ≥85%.  
- **Auto-merge precision** — Of cases auto-merged at confidence \>95%, what fraction were correct? Target: ≥98%. *This is the most safety-critical metric.*  
- **Hallucination rate** — Fraction of rationale statements that cite non-existent evidence. Target: \<2%.

**Operational metrics (LangSmith):**

- P50 / P95 latency per rationale generation  
- $ cost per match processed  
- Failure rate (LLM timeouts, retrieval errors)

### 7.3 LLM-as-judge configuration

A separate LLM (Claude Opus or GPT-4o, *not* the same model that generated the rationale) scores each output against the gold rubric. Same-model judging is biased; cross-model judging is the standard.

### 7.4 Cadence and quality bar

- Nightly eval run on the full golden set; results pushed to a Supabase `eval_runs` table.  
- Quality bar to ship v1.0: Faithfulness ≥0.85, Decision agreement ≥85%, Auto-merge precision ≥98%.  
- Quality bar to ship v1.1: All v1.0 bars maintained \+ Context Precision ≥0.75 on Lineage Q\&A.

### 7.5 Human-in-the-loop validation

Synthetic eval is necessary but not sufficient. Before production at any insurer, a 30–60 case sample would be reviewed by their actual stewardship leads. The eval framework is designed to plug into this — a small human-reviewed sample compared against AI decisions weekly.

---

## 8\. Risk Register

| Risk | Likelihood | Impact | Mitigation |
| :---- | :---- | :---- | :---- |
| LLM hallucinates rationale → wrong merge approved | Medium | High (compliance, member experience) | Hard rules block auto-merge on safety-critical conflicts (SSN, DOB); rationale faithfulness gated by Ragas; nightly eval catches drift; all rationale cites evidence rows. |
| PHI leakage to external LLM provider | Medium | Very high (HIPAA) | Pseudonymisation \+ NER-based redaction before any LLM call; audit log of every external call; option to swap to on-prem / private model. |
| Auto-merge precision falls below 98% threshold | Medium | High | Auto-merge gate is configurable per-tenant; default ships *off*; turned on only after sufficient eval evidence. |
| Stewards reject LLM recommendations (adoption risk) | Medium | High (no value if unused) | Rationale is suggestive, not prescriptive; stewards can override with 1 click; productivity dashboard shows override rates to identify prompt issues. |
| Compliance rejects LLM rationale as audit-quality | Medium | High | Rationale is supplementary to (not replacement for) the audit log; human steward approval required for all non-auto cases; rationale archived with audit trail. |
| LLM API cost overrun | Medium | Medium | Cache rationale for repeat matches; batch embedding calls; LangSmith cost dashboards with alerts; fall back to cheaper model on retries. |
| Vendor lock-in to Voyage / Anthropic | Low | Medium | Embedding model is abstracted behind an interface; LLM provider is config-driven; stack supports swap to OpenAI or open-source models. |
| Performance / latency too slow for real-time UX | Low | Medium | Rationale generation streamed; embeddings precomputed at ingestion; pgvector HNSW index on retrieval. |
| Drift detection generates too many false alarms | Medium | Low | Tunable thresholds; alerts go to stewardship lead, not individual stewards; weekly review of alert quality. |

---

## 9\. Out of Scope (v1.0)

1. Replacement of existing MDM platforms (Reltio, Informatica, Tamr)  
2. Real-time transactional synchronisation across source systems  
3. Autonomous low-confidence merge approval without human oversight  
4. Custom ML model training pipelines per insurer  
5. End-to-end claims processing or member-management workflows  
6. Multi-language support beyond English  
7. Provider-side (vs member-side) MDM use cases

---

## 10\. Open Questions

These are questions I can't yet answer from existing experience or public research — they need either real-world pilot data or stakeholder interviews to resolve.

1. **Audit acceptance of LLM rationale.** Will compliance teams at regulated insurers accept LLM-generated rationale as audit-quality documentation, or will they require human-written memos for any externally-explainable decision? This is the single biggest unknown for productionisation.  
2. **Cross-tenant prompt portability.** Are the rationale prompts and survivorship logic generic across insurers, or does each insurer's tribal knowledge require tenant-specific fine-tuning?  
3. **PHI redaction completeness.** Standard NER catches names, addresses, dates — but how do we handle PHI that hides in *free-text* steward notes (e.g., "patient mentioned divorce in note from June")? What threshold of redaction is enough for regulators?  
4. **Auto-merge appetite.** What confidence threshold are healthcare insurers actually willing to set for auto-resolution? Conversations with stewardship leads suggest 95% is a starting point — but in practice many may insist on 99% in v1.  
5. **Failure mode communication.** When the LLM is uncertain, what's the right UX — refuse to recommend, show low confidence, or escalate to a senior steward? Each carries different operational implications.

---

*PRD ends here. For domain context, similarity metrics, and matching algorithm primer, see* `mdm-domain-notes.md`.  

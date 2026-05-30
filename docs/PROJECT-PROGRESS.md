# Verify — Project Progress

A plain-English log of what got built, when, and why it matters.

---

## Day 1 — Foundation Setup

**What we did:**
- Created the GitHub repo and set up the `main` branch
- Wrote the Product Requirements Document (PRD) covering the problem, target users, success metrics, and risk register
- Wrote domain research notes on decision matching algorithms (Jaro-Winkler, Soundex, cosine similarity), survivorship rules, and where current tools fall short
- Connected to Supabase (cloud PostgreSQL database) and verified the connection works
- Designed the raw data table schema and loaded 50,000 synthetic records from Synthea
- Built the full project folder structure with placeholder code for every module
- Added tech stack badges to the README

**Why it matters:**
Working database with realistic data and a clean codebase structure. Every future feature has a home.

---

## Day 2 — Staging Layer and Decision Features

**What we did:**
- Designed and built the `staging.members` table — cleaned version of raw data with normalized names, parsed DOBs, masked identifiers, and standardized addresses
- Wrote SQL transforms to move 50,000 rows from raw to staging with cleaning applied
- Added decision-feature columns: `name_normalized`, `name_soundex`, `address_normalized`, `ssn_last4`, `zip5`
- Found that 53% of records have ZIP codes (Synthea limitation) — noted fallback blocking strategies needed

**Why it matters:**
The staging layer is where decision matching happens. These cleaned columns are the exact features the scoring engine compares.

---

## Day 3 — Embeddings, Semantic Search, and Vector Indexing

**What we did:**
- Created the reviewer notes table with 10 sample resolution notes (merge, separate, escalate decisions)
- Switched from OpenAI to Voyage AI for embeddings
- Embedded all 10 notes as vectors using Voyage AI
- Built a semantic search script — plain English queries find relevant past decisions
- Handled Voyage AI free-tier rate limits (3 RPM) with retry logic
- Ran a vector index benchmark: No index (239ms), IVFFlat (FAILED), HNSW (0.6ms — 370x faster)
- Wrote ADR-002 documenting HNSW indexing choice

**Why it matters:**
Semantic search lets the copilot find relevant past decisions when a reviewer is working on a new case. HNSW makes it fast enough for real-time use.

---

## Day 4 — Decision Scoring, Reviewer Notes Pipeline, and UI

**What we did:**
- Injected 200 synthetic duplicate records across 3 tiers (near-exact, ambiguous, tricky)
- Ran decision candidate scoring on 50,260 records: 60 AUTO_MERGE, 144 STEWARD_REVIEW, 38,663 SEPARATE
- Created 110 synthetic reviewer notes (40 MERGE, 35 SEPARATE, 35 ESCALATE) covering realistic scenarios
- Switched to voyage-3-lite (512-dim) for faster embedding and lower cost
- Built bulk embedding script with batched API calls
- Scaffolded Streamlit reviewer dashboard with side-by-side records, score breakdowns, action buttons
- Added pagination, search filters, dark mode support, tier-specific action buttons

**Why it matters:**
The scoring pipeline produces realistic tier distributions. The reviewer notes RAG pipeline is the foundation for AI-generated rationale. The Streamlit inbox gives reviewers a working interface.

---

## Day 4b — Dashboard Polish & Dark Mode

**What we did:**
- Redesigned Streamlit dashboard with tabular layout, column filters, and deduplicated queries
- Added tier-specific action buttons: Merge/Keep Separate/Escalate for STEWARD_REVIEW, Confirm Merge/Undo Merge/Escalate for AUTO_MERGE, Force Merge/Confirm Separate/Escalate for SEPARATE
- Added red accent bar, full pagination (First/Prev/Next/Last), and per-page selector (10/25/50)
- Fixed dark mode: replaced hardcoded white backgrounds with transparent stat cards that inherit theme colors
- Custom HTML stat cards with stat-label/stat-value/stat-delta styling
- Added deduplication by name+SSN in queries so the same logical pair doesn't appear twice

**Why it matters:**
The dashboard went from a bare scaffold to a production-quality reviewer interface. Dark mode support and proper pagination are table stakes for a tool people would actually use daily. The tier-specific action buttons map to real operational workflows — different tiers need different decision options.

---

## Day 5 — Rebrand to Verify + LangSmith Tracing

**What we did:**
- Rebranded from "Resolve MDM Copilot" to "Verify — AI Copilot for Operational Decision Review"
- Changed persona from Maria Rodriguez (healthcare steward) to Sam Chen (senior ops analyst)
- Repositioned from healthcare MDM to generic operational decision review for any regulated industry
- Updated all docs: README, PRD (v0.4), ARCHITECTURE, SETUP, PROGRESS
- Updated Streamlit dashboard: new branding, "Pending Review" / "Auto Resolved" / "Separated" tabs
- Wired up LangSmith tracing with test script
- PRD version history table tracks the scope change as "expanded (justified)"

**Why it matters:**
The rebrand positions Verify for a broader audience while keeping the same technical architecture. Healthcare data (Synthea) remains the demo dataset, but the framing is domain-agnostic — applicable to finance, government, insurance, supply chain.

---

## Day 6 — PII Redaction + AI Rationale Engine + Audit Logging

**What we did:**
- Built the PII redaction layer using spaCy NER — masks PERSON, DATE, GPE, LOC, ORG entities before any external LLM call
- Implemented `redact_text()` / `restore_text()` round-trip so original values never leave the system
- Built the AI rationale generator using Claude (claude-sonnet-4-6) with Pydantic structured output — returns recommendation (SAME/DISTINCT/ESCALATE), confidence score, evidence citations, and plain-English rationale
- Added LangSmith tracing via `@traceable` decorator for cost and latency monitoring
- Created `log_llm_call()` audit function that records every external LLM call (model, redacted input length, response length, cost estimate) to the `external_llm_calls` table
- SQL migration 014: added `cached_rationale` JSONB column to `decision_candidates` + created `external_llm_calls` audit table
- Verified Claude API connectivity with a hello-world test script
- Updated PRD to v0.5 with full version history tracking

**Why it matters:**
This is the core AI brain of Verify. PII redaction ensures sensitive data never reaches external APIs (Feature 5 — Data Safety Layer). The rationale engine provides the explainable AI that makes the review inbox useful (Feature 1 — Decision Review Inbox). Audit logging satisfies compliance requirements for regulated industries. Caching rationale avoids redundant LLM calls and reduces cost.

---

## Day 7 — Golden Eval Set + Ragas Harness + UI Rationale Wired

**What we did:**
- Created 100-case golden evaluation set (`eval/golden-set.csv`) with intentional distribution: 30 high-confidence (>0.9), 50 grey-zone (0.6-0.9), 20 low-confidence (<0.6)
- Each case includes: both records, all scores, gold decision (SAME/DISTINCT/ESCALATE), and hand-written gold rationale
- Built the Ragas evaluation harness (`eval/run_eval.py`): loads golden set, runs full redact→rationale pipeline per case, computes decision agreement, auto-resolve precision, per-tier accuracy, latency
- Results save to both `eval/results/run_<timestamp>.json` and `staging.eval_runs` Supabase table
- SQL migration 015: created `eval_runs` table for persisting eval results
- Wired AI rationale into Streamlit inbox — replaced "coming soon" placeholder with:
  - "Generate AI Rationale" button that runs redact→rationale→cache pipeline
  - Cached rationale display showing recommendation, confidence, rationale text, and expandable evidence
- Updated PRD to v0.6 with version history row and Day 7 learnings (items 12-15)

**Why it matters:**
The golden eval set and harness close the eval loop — we can now measure whether the AI is actually making good decisions, not just generating plausible text. The UI integration means reviewers see real AI rationale on every case. This completes the core Feature 1 (Decision Review Inbox) end-to-end: data → scores → rationale → display.

---

## Day 8 — Hybrid Retrieval Setup

**What we did:**
- Added `note_tsv` tsvector column to `reviewer_notes` for Postgres full-text search
- Built auto-update trigger so tsvector stays in sync on INSERT/UPDATE
- Created `hybrid_search_notes` Postgres function: combines vector similarity (`<=>`) with full-text rank (`ts_rank_cd`), returns top-K with configurable weighted score (default 70% vector / 30% text)
- GIN index on tsvector for fast full-text queries
- Built test script (`test_hybrid_search.py`) with 10 test queries comparing pure vector vs hybrid results
- SQL migration 016

**Why it matters:**
Pure vector search misses keyword-specific queries ("SSN transposed", "ZIP+4 difference"). Hybrid search catches these by combining semantic similarity with exact term matching — giving the Q&A chain better retrieval quality.

---

## Day 9 — Cohere Reranking

**What we did:**
- Integrated Cohere Rerank API (rerank-v3.5) via `rerank_results()` in retriever module
- Pipeline: hybrid search top-50 → Cohere rerank → return top-5
- Graceful fallback: if no `COHERE_API_KEY` or API fails, falls back to hybrid ordering
- Built benchmark script (`test_rerank_benchmark.py`) comparing hybrid-only vs hybrid+rerank precision on 10 queries
- Updated `.env.example` and `requirements.txt` with Cohere dependency
- Results saved to `eval/results/rerank_benchmark.json`

**Why it matters:**
Reranking uses a cross-encoder model that scores query-document relevance more accurately than embedding distance. Even small precision improvements compound across thousands of Q&A interactions.

---

## Day 10 — Ops Q&A Chain

**What we did:**
- Built `answer_ops_question()` LangChain RAG chain: embed question → hybrid search + rerank → Claude rationale
- Pydantic output schema: `OpsAnswer(answer_text, cited_evidence_ids, confidence)`
- PII redaction applied before sending context to Claude
- Citation validation: cited_evidence_ids are filtered to only include actually-retrieved note_ids
- LangSmith tracing via `@traceable` decorator
- Tested on 5 ops questions with verified citations

**Why it matters:**
This is Feature 2 (Ops Q&A) from the PRD. Reviewers can now ask plain-English questions about past decisions and get grounded answers with specific citations. Every claim traces back to a real reviewer note.

---

## Day 11 — Ops Q&A UI in Streamlit

**What we did:**
- Added "Ops Q&A" tab to Streamlit dashboard with chat interface
- Chat input with streaming answer display
- Evidence citations panel: each cited note shows note_id, reviewer, action, confidence, and note excerpt
- Chat history maintained in session state
- Queries saved to `ops_queries` table (question, answer, citations, confidence, latency)
- SQL migration 017: `ops_queries` audit table

**Why it matters:**
The Q&A interface is the second major user-facing feature. Sam Chen (our persona) can now ask "Why did the team mark candidate X as DISTINCT?" and get an answer in seconds instead of hunting through notes for hours.

---

## Day 12 — Anomaly Watcher SQL

**What we did:**
- Designed 4 anomaly metrics: daily candidate volume, source data freshness, 7-day confidence score average, attribute completeness per source
- Created `anomaly_metrics` table with baseline stats (mean, stddev) and anomaly flag
- Built `compute_daily_anomaly_metrics()` Postgres function: computes all 4 metrics for a given date, calculates 30-day baseline, flags values >2σ from mean
- SQL migration 018

**Why it matters:**
Anomaly detection is Feature 4 (Drift Watcher). Automated monitoring catches problems — source feed failures, matching engine drift, data quality drops — before they compound into reviewer backlog.

---

## Day 13 — Anomaly Dashboard + Alert Explanations

**What we did:**
- Added "Anomaly Watcher" tab to Streamlit dashboard with 4 KPI tiles (one per metric)
- Color-coded alert badges (🟢 normal / 🔴 anomaly) based on 2σ deviation
- 30-day sparklines for daily volume and confidence score trends
- Source freshness and attribute completeness data tables
- Active alerts section listing any triggered anomalies
- "Explain Alerts" button: calls Claude to generate 1-sentence likely cause hypothesis
- All 4 anomaly queries run live against the database

**Why it matters:**
The anomaly dashboard gives ops leads a daily health check. When something breaks (stale feed, confidence drift, data quality drop), the team knows before it hits the reviewer queue. The Claude explanation gives a starting point for investigation.

---

## What's Built So Far (Summary)

| Component | Status | Details |
|-----------|--------|---------|
| GitHub repo | Done | Structure, CI-ready |
| Raw data layer | Done | 50K synthetic records loaded |
| Staging layer | Done | Cleaned, normalized, feature-ready |
| Decision features | Done | 6 features populated on 50K rows |
| Reviewer notes | Done | 110 notes with embeddings |
| Semantic search | Done | Voyage AI + pgvector + HNSW |
| Vector benchmarking | Done | HNSW chosen (ADR-002) |
| Decision candidates | Done | 38,867 scored pairs across 3 tiers |
| Synthetic test data | Done | 200 injected with controlled noise |
| Note embeddings | Done | voyage-3-lite 512-dim + HNSW index |
| Streamlit dashboard | Done | Reviewer inbox, filters, pagination, dark mode, tier-specific actions |
| LangSmith tracing | Done | Test script verified |
| PRD | Done | v0.6, version-tracked |
| Architecture doc | Done | Layer diagram + data flow |
| PII redaction | Done | spaCy NER, 5 entity types |
| AI rationale engine | Done | Claude + Pydantic structured output |
| LLM audit logging | Done | external_llm_calls table + log function |
| Cached rationale | Done | JSONB column on decision_candidates |
| LangSmith tracing | Done | @traceable on rationale generation |
| UI rationale display | Done | Generate button + cached display in inbox |
| Golden eval set | Done | 100 cases (30 HC / 50 GZ / 20 LC) |
| Ragas eval harness | Done | run_eval.py → JSON + Supabase |
| Eval runs table | Done | staging.eval_runs (SQL 015) |
| Hybrid retrieval | Done | tsvector + hybrid_search_notes function (SQL 016) |
| Cohere Reranking | Done | top-50 → rerank → top-5 with fallback |
| Ops Q&A chain | Done | LangChain RAG + OpsAnswer Pydantic schema |
| Ops Q&A UI | Done | Streamlit chat tab + evidence citations |
| Ops queries audit | Done | staging.ops_queries table (SQL 017) |
| Anomaly metrics | Done | 4 metrics + compute function (SQL 018) |
| Anomaly dashboard | Done | KPI tiles, sparklines, alerts, Claude explanations |

## What's Next

- Run first baseline eval and record numbers
- Reviewer Productivity Dashboard
- End-to-end integration testing
- Polish and prepare for June 13 launch

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
| Streamlit dashboard | Done | Reviewer inbox, filters, pagination |
| LangSmith tracing | Done | Test script verified |
| PRD | Done | v0.5, version-tracked |
| Architecture doc | Done | Layer diagram + data flow |
| PII redaction | Done | spaCy NER, 5 entity types |
| AI rationale engine | Done | Claude + Pydantic structured output |
| LLM audit logging | Done | external_llm_calls table + log function |
| Cached rationale | Done | JSONB column on decision_candidates |
| LangSmith tracing | Done | @traceable on rationale generation |

## What's Next

- Wire rationale into Streamlit inbox cards (replace "coming soon" placeholder)
- Golden eval set (100 labeled cases)
- Ragas evaluation framework
- Ops Q&A chat interface
- End-to-end integration: redact → generate rationale → cache → display

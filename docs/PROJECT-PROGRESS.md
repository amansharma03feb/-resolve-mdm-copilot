# Resolve MDM Copilot — Project Progress

A plain-English log of what got built, when, and why it matters.

---

## Day 1 — Foundation Setup

**What we did:**
- Created the GitHub repo and set up the `main` branch
- Wrote the Product Requirements Document (PRD) covering the problem, target users, success metrics, and risk register
- Wrote domain research notes on healthcare MDM — how matching algorithms work (Jaro-Winkler, Soundex, cosine similarity), what survivorship rules are, and where current tools fall short
- Connected to Supabase (cloud PostgreSQL database) and verified the connection works
- Designed the raw patient table schema and loaded 50,000 synthetic patient records from Synthea (a healthcare test data generator)
- Built the full project folder structure with placeholder code for every module: data ingestion, matching, RAG, PHI safety, orchestration, evaluation, and UI
- Added tech stack badges to the README

**Why it matters:**
This gives us a working database with realistic healthcare data and a clean codebase structure to build on. Every future feature has a home.

---

## Day 2 — Staging Layer and Match Features

**What we did:**
- Designed and built the `staging.members` table — a cleaned version of the raw data with normalized names, parsed dates of birth, masked SSNs (last 4 only), and standardized addresses
- Wrote SQL transforms to move 50,000 rows from raw to staging with all the cleaning applied automatically
- Added match-feature columns for duplicate detection:
  - `name_normalized` — lowercase, no punctuation, no Synthea numeric suffixes
  - `name_soundex` — phonetic code so "Smith" and "Smyth" match
  - `date_of_birth` — parsed date for exact/fuzzy matching
  - `ssn_last4` — last 4 digits of SSN for high-confidence matching
  - `address_normalized` — full address cleaned and lowercased
  - `zip5` — 5-digit ZIP for geographic blocking
- Found that 53% of records have ZIP codes (Synthea limitation) — noted that we'll need fallback blocking strategies

**Why it matters:**
The staging layer is where matching happens. These cleaned columns are the exact features that the matching engine will compare when looking for duplicate patient records.

---

## Day 3 — Embeddings, Semantic Search, and Vector Indexing

**What we did:**
- Created the `staging.member_notes` table with 10 sample steward resolution notes (realistic examples of merge, separate, and escalate decisions)
- Switched from OpenAI to Voyage AI for embeddings (aligns with the PRD stack)
- Embedded all 10 steward notes as 1024-dimensional vectors using Voyage AI's `voyage-3` model
- Built a semantic search script — you type a question in plain English and it finds the most relevant past steward decisions
- Handled Voyage AI free-tier rate limits (3 requests per minute) with retry logic
- Ran a vector index benchmark on 10,000 synthetic vectors:
  - No index (sequential scan): 239 ms
  - IVFFlat: FAILED — exceeds Supabase free tier's 32 MB memory limit
  - HNSW: 0.6 ms — 370x faster than no index
- Wrote ADR-002 (Architecture Decision Record) documenting why we chose HNSW indexing
- HNSW index size: 21 MB for 10K vectors (~2.1 KB per vector)

**Why it matters:**
Semantic search lets the copilot find relevant past decisions when a steward is reviewing a new match. Instead of keyword search, it understands meaning — so searching "SSN typo" finds notes about transposition errors even if those exact words aren't used. The HNSW index makes this fast enough for real-time use.

---

## Day 4 — Match Scoring, Steward Notes Pipeline, and UI

**What we did:**
- Injected 200 synthetic duplicate records into staging.members across 3 tiers:
  - Tier A (60): near-exact duplicates (char-swap name, same SSN/DOB) → AUTO_MERGE
  - Tier B (80): ambiguous duplicates (truncated name, same DOB, different SSN/address) → STEWARD_REVIEW
  - Tier C (60): tricky duplicates (extra letter, DOB +1 day, SSN transposition) → borderline
- Re-ran match candidate scoring on 50,260 members: 60 AUTO_MERGE, 144 STEWARD_REVIEW, 38,663 SEPARATE
- Created `staging.steward_notes` table with 110 synthetic resolution notes (40 MERGE, 35 SEPARATE, 35 ESCALATE) covering realistic scenarios: nickname variants, name transliterations, institutional addresses, compliance edge cases, fraud scenarios
- Switched embedding model from `voyage-3` (1024-dim) to `voyage-3-lite` (512-dim) for faster embedding and lower cost
- Built bulk embedding script with batched API calls (5 notes per batch, rate-limit-aware retry)
- Built semantic similarity search script for steward notes
- Created HNSW index on steward note embeddings for sub-millisecond search
- Scaffolded Streamlit steward dashboard with:
  - Sidebar showing match pipeline stats (tier counts, avg scores)
  - Steward Review Inbox: 10 candidate pairs with side-by-side records, score breakdowns, and Merge/Keep/Escalate buttons
  - AI rationale placeholder for Week 4 integration

**Why it matters:**
The matching pipeline now produces realistic tier distributions across all three categories. The steward notes RAG pipeline (text → Voyage → pgvector → similarity search) is the foundation for AI-generated rationale. The Streamlit inbox gives stewards a working interface to review candidates — the core product experience.

---

## What's Built So Far (Summary)

| Component | Status | Details |
|-----------|--------|---------|
| GitHub repo | Done | Structure, CI-ready |
| Raw data layer | Done | 50K synthetic patients loaded |
| Staging layer | Done | Cleaned, normalized, match-ready |
| Match features | Done | 6 features populated on 50K rows |
| Steward notes | Done | 10 sample notes with embeddings |
| Semantic search | Done | Voyage AI + pgvector + HNSW |
| Vector benchmarking | Done | HNSW chosen (ADR-002) |
| Match candidates | Done | 38,867 scored pairs across 3 tiers |
| Synthetic duplicates | Done | 200 injected with controlled noise |
| Steward notes (110) | Done | 40 MERGE, 35 SEPARATE, 35 ESCALATE |
| Note embeddings | Done | voyage-3-lite 512-dim + HNSW index |
| Streamlit inbox | Done | Side-by-side records, score badges |
| PRD | Done | Full product spec |
| Architecture doc | Done | Layer diagram + data flow |

## What's Next

- Embed all steward notes and verify HNSW index performance
- RAG pipeline for rationale generation (Week 4)
- PHI safety layer (redaction before LLM calls)
- LLM-generated rationale in Streamlit inbox

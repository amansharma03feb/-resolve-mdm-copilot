# Architecture — Verify: AI Copilot for Operational Decision Review

## System Overview

```
+----------------------------------------------------------------+
|                     Streamlit Dashboard                         |
|  [Pending Review] [Auto Resolved] [Separated] [Q&A] [Anomaly]  |
+----------------------------------------------------------------+
         |                |                |              |
         v                v                v              v
+----------------+ +-------------+ +------------+ +-------------+
| AI Rationale   | | Ops Q&A     | | Anomaly    | | Decision    |
| Generator      | | (RAG Chain) | | Watcher    | | Review      |
| (Claude +      | | Hybrid      | | 4 metrics  | | (scores,    |
|  Pydantic)     | | search +    | | + Claude   | |  actions)   |
|                | | rerank +    | | explanat.  | |             |
|                | | Claude)     | |            | |             |
+-------+--------+ +------+------+ +-----+------+ +------+------+
        |                 |               |               |
        v                 v               v               v
+----------------------------------------------------------------+
|                    Data Safety Layer                             |
|           spaCy NER Redaction + Audit Logging                   |
+----------------------------------------------------------------+
        |                 |               |               |
        v                 v               v               v
+----------------------------------------------------------------+
|              Supabase PostgreSQL + pgvector                      |
|                                                                  |
|  staging.members (50K)    staging.decision_candidates (38,867)   |
|  staging.reviewer_notes   staging.external_llm_calls             |
|  staging.eval_runs        staging.ops_queries                    |
|  staging.anomaly_metrics  HNSW index (512-dim)                   |
+----------------------------------------------------------------+

External: Voyage AI (embeddings) | Claude (LLM) | Cohere (rerank) | LangSmith (traces)
```

## Data Flow

1. **Ingest** — Synthea CSV loaded into `raw.synthea_patients` (50K records)
2. **Stage** — Normalised to `staging.members` with cleaned names, parsed DOB, SSN masking, address standardisation
3. **Block** — Generate candidate pairs using Soundex + DOB blocking keys (avoids O(n^2))
4. **Score** — Composite scoring: Jaro-Winkler (name), exact match (DOB, SSN), trigram similarity (address)
5. **Tier** — Route by score: AUTO_MERGE (>=0.95) | STEWARD_REVIEW (0.60-0.94) | SEPARATE (<0.60)
6. **Rationale** — PII redacted via spaCy NER, then Claude generates structured rationale (Pydantic schema), cached to JSONB
7. **Q&A** — Hybrid retrieval (vector + full-text) over reviewer notes, Cohere rerank, Claude answers with cited evidence
8. **Anomaly** — 4 daily metrics computed, 2-sigma alerting, Claude generates causal hypotheses
9. **Eval** — 100-case golden set, harness measures decision agreement, auto-resolve precision, per-tier accuracy

## Database Schema

| Table | Purpose | Rows |
|-------|---------|------|
| `raw.synthea_patients` | Raw Synthea CSV data | 50,000 |
| `staging.members` | Cleaned, normalised, feature-ready | 50,260 |
| `staging.decision_candidates` | Scored pairs with tier + cached rationale | 38,867 |
| `staging.reviewer_notes` | 110 notes with 512-dim embeddings + tsvector | 110 |
| `staging.external_llm_calls` | Audit log: every external LLM API call | Grows |
| `staging.eval_runs` | Ragas evaluation run results | Grows |
| `staging.ops_queries` | Q&A audit log: question, answer, citations | Grows |
| `staging.anomaly_metrics` | Daily anomaly metrics with baselines | Grows |

## SQL Migrations (in order)

| # | File | What |
|---|------|------|
| 001 | `create_raw_schema.sql` | Raw schema + synthea_patients table |
| 002 | `create_staging_members.sql` | Staging schema + members table + transform |
| 003 | `create_member_notes.sql` | Member notes with pgvector (1024-dim, original) |
| 004 | `add_match_features.sql` | name_normalized, name_soundex, address_normalized |
| 005 | `fix_match_features.sql` | Strip Synthea numeric suffixes from names |
| 006 | `vector_index_benchmark.sql` | HNSW vs IVFFlat vs no-index benchmark |
| 007 | `generate_match_candidates.sql` | Blocking + scoring + tier classification |
| 008 | `spot_check_candidates.sql` | Validation queries for scored pairs |
| 009 | `inject_synthetic_duplicates.sql` | 200 injected duplicates across 3 tiers |
| 010 | `rescore_with_duplicates.sql` | Re-run scoring with injected data |
| 011 | `create_steward_notes.sql` | 110 reviewer notes (voyage-3-lite, 512-dim) |
| 012 | `steward_notes_hnsw_index.sql` | HNSW index on note embeddings |
| 013 | `rename_tables_verify.sql` | Rebrand: match_candidates -> decision_candidates |
| 014 | `add_cached_rationale_and_audit.sql` | cached_rationale JSONB + external_llm_calls |
| 015 | `create_eval_runs.sql` | Evaluation run results table |
| 016 | `hybrid_search_setup.sql` | tsvector column + hybrid_search_notes function |
| 017 | `create_ops_queries.sql` | Q&A audit table |
| 018 | `anomaly_metrics.sql` | Anomaly metrics + daily compute function |

## External Services

| Service | Purpose | Tier |
|---------|---------|------|
| Supabase | PostgreSQL + pgvector | Free |
| Voyage AI | Embeddings (voyage-3-lite, 512-dim) | Free (200M tokens) |
| Anthropic Claude | LLM rationale + Q&A + anomaly explanations | Pay-as-you-go (~$15 total) |
| Cohere | Reranking (rerank-v3.5) | Free |
| LangSmith | Tracing + observability | Free |

## Key Architecture Decisions

- **ADR-001:** Open-source stack rationale — why each component was chosen
- **ADR-002:** HNSW over IVFFlat — 370x faster, IVFFlat fails on free-tier shared compute
- **Hybrid retrieval:** Vector similarity (70%) + full-text rank (30%) — catches both semantic and keyword queries
- **PII redaction before LLM:** spaCy NER strips 5 entity types, mapping kept in-memory for restore
- **Pydantic output schemas:** Forces structured LLM responses, prevents malformed JSON from reaching UI
- **Rationale caching:** Generate once to JSONB column, display many times — critical for cost control

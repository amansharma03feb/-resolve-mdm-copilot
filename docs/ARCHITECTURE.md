# Architecture — Resolve MDM Copilot

## High-Level Layers

```
┌─────────────────────────────────────────────────┐
│                 Streamlit UI                     │
│             (steward dashboard)                  │
├─────────────────────────────────────────────────┤
│            LangGraph Orchestration               │
│         (triage workflow state machine)           │
├──────────┬──────────┬───────────┬───────────────┤
│ Matching │   RAG    │ PHI Safety│  Eval         │
│ (scorer, │(retriever│ (redactor,│  (Ragas,      │
│  blocker,│ rationale│  audit)   │   golden set) │
│  embedder│ lineage) │           │               │
├──────────┴──────────┴───────────┴───────────────┤
│          Ingestion / Data Layer                   │
│    (loader, validator, Supabase + pgvector)       │
└─────────────────────────────────────────────────┘
```

## Data Flow

1. **Ingest** — Synthea CSV → `raw.synthea_patients` (Supabase)
2. **Block** — Generate candidate duplicate pairs using blocking keys
3. **Score** — Composite match scoring (Jaro-Winkler, Soundex, embeddings)
4. **Triage** — LangGraph routes: auto-merge / steward-review / separate
5. **Rationale** — Claude generates plain-English explanation grounded via RAG
6. **PHI safety** — Presidio redacts PHI before any external LLM call
7. **Eval** — Ragas nightly runs on golden set; LangSmith tracks cost/latency

## External Services

| Service | Purpose |
|---------|---------|
| Supabase (PostgreSQL + pgvector) | Data store, vector search |
| Voyage AI | Embedding generation |
| Anthropic Claude | LLM rationale + lineage Q&A |
| LangSmith | Observability, tracing |
| Ragas | RAG evaluation metrics |

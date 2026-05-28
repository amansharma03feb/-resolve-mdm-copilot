# Architecture — Verify: AI Copilot for Operational Decision Review

## High-Level Layers

```
+---------------------------------------------------+
|                 Streamlit UI                       |
|            (reviewer dashboard)                    |
+---------------------------------------------------+
|            LangGraph Orchestration                 |
|         (triage workflow state machine)            |
+----------+----------+-----------+-----------------+
| Decision |   RAG    | Data      |  Eval           |
| Matching | (retriev | Safety    |  (Ragas,        |
| (scorer, |  rationa | (redactor |   golden set)   |
|  blocker, |  ops Q&A |  audit)  |                 |
|  embedder)|        ) |          |                 |
+----------+----------+-----------+-----------------+
|          Ingestion / Data Layer                    |
|    (loader, validator, Supabase + pgvector)        |
+---------------------------------------------------+
```

## Data Flow

1. **Ingest** — Synthea CSV -> `raw.synthea_patients` (Supabase)
2. **Block** — Generate candidate decision pairs using blocking keys
3. **Score** — Composite scoring (trigram similarity, Soundex, exact match)
4. **Triage** — LangGraph routes: auto-resolve / reviewer-review / separate
5. **Rationale** — Claude generates plain-English explanation grounded via RAG
6. **Data safety** — Presidio redacts sensitive data before any external LLM call
7. **Eval** — Ragas nightly runs on golden set; LangSmith tracks cost/latency

## External Services

| Service | Purpose |
|---------|---------|
| Supabase (PostgreSQL + pgvector) | Data store, vector search |
| Voyage AI | Embedding generation (voyage-3-lite, 512-dim) |
| Anthropic Claude | LLM rationale + ops Q&A |
| LangSmith | Observability, tracing |
| Ragas | RAG evaluation metrics |

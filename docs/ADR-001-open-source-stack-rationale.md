# ADR-001: Open-Source Stack Rationale

**Status:** Accepted
**Date:** 2026-05-13
**Decision maker:** Aman Sharma

---

## Context

Resolve is an AI-augmented MDM steward copilot for healthcare. Before writing any code, we had to choose between:

- **Commercial MDM platforms** (Reltio, Informatica, Tamr) — mature, but expensive, opaque, and hard to customize at the AI/LLM layer
- **Open-source stack** — full control, transparent, portfolio-demonstrable, but requires more integration work

The choice affects cost, hiring signal, compliance posture, and how deeply we can instrument the AI pipeline for evaluation and observability.

---

## Decision

**Build on a fully open-source / developer-tier stack.**

| Layer | Choice | Why this over alternatives |
|-------|--------|--------------------------|
| **Database** | PostgreSQL on Supabase (free tier) | Managed Postgres with pgvector built in. No separate vector DB needed. Free tier covers 50K+ rows comfortably. |
| **Vector search** | pgvector + HNSW index | Co-located with relational data — no sync between a vector DB and a relational DB. HNSW gives sub-millisecond queries (see ADR-002). |
| **Embeddings** | Voyage AI (voyage-3, 1024 dims) | Purpose-built for retrieval. 200M free tokens. Outperforms OpenAI text-embedding-3-small on retrieval benchmarks per Voyage's published evals. |
| **LLM** | Anthropic Claude (Sonnet) | Strong instruction-following for structured rationale. Constitutional AI alignment reduces hallucination risk in healthcare context. |
| **Orchestration** | LangChain + LangGraph | LangGraph's state machine model maps directly to match triage workflow (auto-merge / review / separate / escalate). |
| **Evaluation** | Ragas + LangSmith | Ragas provides RAG-specific metrics (faithfulness, context precision) out of the box. LangSmith provides tracing, cost tracking, and latency monitoring. |
| **UI** | Streamlit | Fastest path to a working steward dashboard. No frontend build tooling. Python-native — same language as the backend. |

---

## Alternatives Considered

### 1. Pinecone / Weaviate / Qdrant (dedicated vector DB)

- **Rejected because:** Adds a separate service to manage and sync with. pgvector keeps vectors co-located with relational data (patient records, steward notes, audit logs) — no ETL between systems. At our scale (<100K vectors), pgvector with HNSW matches dedicated vector DB performance.
- **When to revisit:** If we exceed 1M embeddings or need multi-tenant vector isolation.

### 2. OpenAI embeddings (text-embedding-3-small/large)

- **Rejected because:** Voyage AI offers 200M free tokens (vs OpenAI's pay-per-token). Voyage-3 outputs 1024 dims vs OpenAI's 1536 — 33% less storage and faster similarity computation. Voyage's retrieval-optimized training aligns better with our RAG use case.
- **When to revisit:** If Voyage AI deprecates free tier or if OpenAI releases a retrieval-specific model.

### 3. OpenAI GPT-4o (LLM)

- **Rejected because:** Claude's constitutional AI training provides stronger guardrails for healthcare rationale. Anthropic's safety-first positioning aligns with HIPAA-adjacent use cases. Both models are comparable on instruction-following; Claude edges on structured output consistency in our early testing.
- **When to revisit:** If Claude's latency or cost becomes a bottleneck, GPT-4o is a drop-in swap via the abstracted LLM interface.

### 4. Commercial MDM platform (Reltio / Informatica)

- **Rejected because:** Resolve is an AI augmentation layer, not a replacement MDM. Commercial platforms don't expose the hooks needed for custom LLM rationale, PHI redaction pipelines, or RAG-grounded explainability. Building open-source lets us instrument every layer for evaluation (Ragas, LangSmith) — which is the core differentiator.
- **When to revisit:** In production, Resolve would sit alongside (not replace) a commercial MDM. The open-source stack proves the AI layer; the commercial platform provides the production matching engine.

### 5. React / Next.js (UI)

- **Rejected because:** Adds frontend build complexity (Node, npm, webpack) for a data-steward tool where UX polish is secondary to functionality. Streamlit ships a working dashboard in ~200 lines of Python with no JS required.
- **When to revisit:** If we need real-time collaboration, complex state management, or embeddable widgets for integration into existing MDM consoles.

---

## Consequences

### Positive

- **Zero licensing cost** — entire stack runs on free tiers for development and demo
- **Full observability** — every LLM call, embedding, retrieval, and decision is traceable via LangSmith
- **Portfolio signal** — demonstrates hands-on AI engineering (RAG, pgvector, LangGraph, eval) rather than drag-and-drop platform usage
- **Swap-friendly** — each component is behind an interface; switching embedding provider or LLM is a config change, not a rewrite

### Negative

- **Integration burden** — we own the glue between 7+ services (Supabase, Voyage, Claude, LangChain, Ragas, LangSmith, Streamlit)
- **Free-tier limits** — Voyage AI rate limits (3 RPM without payment method), Supabase memory caps (32 MB maintenance_work_mem), which we hit during vector index benchmarking (see ADR-002)
- **No enterprise support** — if Supabase or Voyage has an outage, we wait for community fixes
- **Streamlit UX ceiling** — adequate for demo/MVP but may not scale to production steward workflows with complex multi-panel layouts

---

## Validation from Build

Evidence gathered during Days 1-3 that confirms this decision:

| Claim | Evidence |
|-------|----------|
| pgvector handles our scale | 50K patient records + 10 embedded notes — no issues |
| HNSW works on free tier | 0.646ms queries on 10K vectors (ADR-002) |
| Voyage AI free tier is sufficient | Embedded 10 notes within rate limits (3 RPM with 21s delay) |
| Supabase free tier has limits | IVFFlat index creation failed at 32 MB memory cap |
| Co-located vectors + relational data works | Semantic search over steward notes queries same DB as patient records — no sync needed |

---

*Related: [ADR-002 — pgvector Indexing Strategy](ADR-002-vector-indexing-strategy.md)*

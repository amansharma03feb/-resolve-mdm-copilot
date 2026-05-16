![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-4169E1?logo=postgresql&logoColor=white)
![pgvector](https://img.shields.io/badge/pgvector-vector%20search-336791)
![LangChain](https://img.shields.io/badge/LangChain-orchestration-1C3C3C?logo=langchain&logoColor=white)
![Anthropic](https://img.shields.io/badge/Claude-Anthropic-CC785C?logo=anthropic&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

# Resolve — AI-Augmented MDM Steward Copilot

An open-source AI product that helps healthcare data stewards resolve member identity matches faster, with explainable LLM rationale and HIPAA-aware retrieval.

**Status:** Day 1 — foundation setup. Architecture, PRD, and demo coming over the next 90 days.

## Stack

- PostgreSQL on Supabase + pgvector

- Voyage AI (embeddings)

- LangChain + LangGraph (orchestration, Week 3+)

- Anthropic Claude (LLM, Week 3+)

- Ragas (RAG evaluation)

- LangSmith (observability)

- Streamlit (UI, Week 4+)

## Architecture

```mermaid
graph TB
    subgraph UI["🖥️ Streamlit UI — Steward Dashboard"]
        UI_REVIEW["Match Review Queue"]
        UI_LINEAGE["Lineage Q&A Chat"]
        UI_METRICS["Eval Metrics Dashboard"]
    end

    subgraph ORCH["🔀 LangGraph Orchestration"]
        TRIAGE["Triage Router"]
        AUTO["Auto-Merge<br/>score ≥ 0.95"]
        REVIEW["Steward Review<br/>0.60 – 0.94"]
        SEPARATE["Auto-Separate<br/>score < 0.60"]
    end

    subgraph CORE["⚙️ Core Modules"]
        direction LR
        subgraph MATCH["Matching Engine"]
            BLOCKER["Blocker<br/>Soundex · ZIP · DOB"]
            SCORER["Scorer<br/>Jaro-Winkler · Cosine"]
            EMBEDDER["Embedder<br/>Voyage AI 1024d"]
        end
        subgraph RAG["RAG Pipeline"]
            RETRIEVER["pgvector Retriever<br/>HNSW Index"]
            RATIONALE["Rationale Generator<br/>Claude LLM"]
            LINEAGE["Lineage Q&A<br/>Claude LLM"]
        end
        subgraph PHI["PHI Safety"]
            REDACTOR["Presidio Redactor<br/>NER Masking"]
            AUDIT["Audit Logger"]
        end
        subgraph EVAL["Evaluation"]
            RAGAS["Ragas Metrics"]
            GOLDEN["Golden Set<br/>100 labeled pairs"]
        end
    end

    subgraph DATA["🗄️ Data Layer — Supabase PostgreSQL"]
        RAW["raw.synthea_patients<br/>50K records"]
        STAGING["staging.members<br/>Normalized + Match Features"]
        NOTES["staging.member_notes<br/>Embedded Steward Notes"]
        VECTORS["pgvector + HNSW<br/>1024-dim embeddings"]
    end

    subgraph EXT["☁️ External Services"]
        VOYAGE["Voyage AI<br/>Embeddings"]
        CLAUDE["Anthropic Claude<br/>LLM Rationale"]
        LANGSMITH["LangSmith<br/>Observability"]
    end

    UI --> ORCH
    TRIAGE --> AUTO
    TRIAGE --> REVIEW
    TRIAGE --> SEPARATE

    ORCH --> MATCH
    ORCH --> RAG
    RAG --> PHI
    PHI --> CLAUDE

    BLOCKER --> SCORER
    SCORER --> EMBEDDER
    EMBEDDER --> VOYAGE

    RETRIEVER --> VECTORS
    RATIONALE --> RETRIEVER

    RAW --> STAGING
    STAGING --> BLOCKER
    NOTES --> RETRIEVER

    EVAL --> LANGSMITH

    style UI fill:#4A90D9,color:#fff
    style ORCH fill:#F5A623,color:#fff
    style MATCH fill:#7ED321,color:#fff
    style RAG fill:#9B59B6,color:#fff
    style PHI fill:#E74C3C,color:#fff
    style EVAL fill:#1ABC9C,color:#fff
    style DATA fill:#34495E,color:#fff
    style EXT fill:#95A5A6,color:#fff
```

## Roadmap

See [`/docs/PRD.md`](docs/PRD.md) for full product spec.

Built in public — follow along on [LinkedIn](#).


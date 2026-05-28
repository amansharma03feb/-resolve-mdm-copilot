![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-4169E1?logo=postgresql&logoColor=white)
![pgvector](https://img.shields.io/badge/pgvector-vector%20search-336791)
![LangChain](https://img.shields.io/badge/LangChain-orchestration-1C3C3C?logo=langchain&logoColor=white)
![Anthropic](https://img.shields.io/badge/Claude-Anthropic-CC785C?logo=anthropic&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

# Verify — AI Copilot for Operational Decision Review

An open-source AI copilot that helps operations teams review, explain, and audit their decisions — generating natural-language rationale for each decision and answering follow-up questions over decision history.

**Demo dataset:** Synthea synthetic healthcare records (realistic complexity: multiple identifiers, slight variations, ambiguous matches — the kinds of patterns ops teams face in finance, government services, insurance, and any regulated industry).

**Status:** Building in public over ~90 days. Foundations complete. Streamlit dashboard live.

---

## The Problem

Operations teams across regulated industries spend hours reviewing decisions, comparing records, and answering audit questions. Existing tools surface raw data or numeric scores but provide little explanation, forcing reviewers to reconstruct rationale themselves. Audit response is engineering-mediated and slow. As decision volumes grow, manual review becomes a bottleneck.

Verify augments these workflows with explainable AI rationale, conversational decision history, and proactive anomaly monitoring — without replacing the underlying systems.

---

## Two Interfaces

### 1. Decision Rationale Generator
For any pair of records, events, or decisions, Verify produces a plain-English explanation citing specific evidence. Use cases:
- Duplicate or near-duplicate detection
- Anomaly investigation ("why did this metric spike?")
- Change verification ("why was this record updated?")
- Quality flagging ("is this entry inconsistent with similar past entries?")

### 2. Ops Q&A Interface
Natural-language chat over decision history, audit logs, change events, and reviewer notes:
- "Why was decision X made last March?"
- "Show me all reviews by Sam in Q2 where the decision was overturned."
- "What changed in our data last week?"

---

## Stack

| Layer | Technology |
|-------|-----------|
| Database | PostgreSQL on Supabase + pgvector |
| Embeddings | Voyage AI (voyage-3-lite, 512-dim) |
| Orchestration | LangChain + LangGraph |
| LLM | Anthropic Claude |
| Evaluation | Ragas |
| Observability | LangSmith |
| UI | Streamlit |

---

## Architecture

![Architecture Diagram](docs/diagrams/architecture-v1-MDM.PNG)

<details>
<summary>View as Mermaid (text-based)</summary>

```mermaid
graph TB
    subgraph UI["Streamlit UI — Reviewer Dashboard"]
        UI_REVIEW["Decision Review Queue"]
        UI_LINEAGE["Ops Q&A Chat"]
        UI_METRICS["Eval Metrics Dashboard"]
    end

    subgraph ORCH["LangGraph Orchestration"]
        TRIAGE["Triage Router"]
        AUTO["Auto-Resolve<br/>score >= 0.95"]
        REVIEW["Reviewer Review<br/>0.60 - 0.94"]
        SEPARATE["Auto-Separate<br/>score < 0.60"]
    end

    subgraph CORE["Core Modules"]
        direction LR
        subgraph MATCH["Decision Matching"]
            BLOCKER["Blocker<br/>Soundex + DOB"]
            SCORER["Scorer<br/>Jaro-Winkler + Cosine"]
            EMBEDDER["Embedder<br/>Voyage AI 512d"]
        end
        subgraph RAG["RAG Pipeline"]
            RETRIEVER["pgvector Retriever<br/>HNSW Index"]
            RATIONALE["Rationale Generator<br/>Claude LLM"]
            LINEAGE["Ops Q&A<br/>Claude LLM"]
        end
        subgraph PHI["Data Safety"]
            REDACTOR["Presidio Redactor<br/>NER Masking"]
            AUDIT["Audit Logger"]
        end
        subgraph EVAL["Evaluation"]
            RAGAS["Ragas Metrics"]
            GOLDEN["Golden Set<br/>100 labeled pairs"]
        end
    end

    subgraph DATA["Data Layer — Supabase PostgreSQL"]
        RAW["raw.synthea_patients<br/>50K records"]
        STAGING["staging.records<br/>Normalized + Features"]
        NOTES["staging.reviewer_notes<br/>Embedded Decision Notes"]
        VECTORS["pgvector + HNSW<br/>512-dim embeddings"]
    end

    subgraph EXT["External Services"]
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

</details>

---

## Roadmap

See [`/docs/PRD.md`](docs/PRD.md) for full product spec.

Built in public — follow along on [LinkedIn](#).

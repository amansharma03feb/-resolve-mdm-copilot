# Learning Resources — Resolve MDM Copilot

A curated list of resources for every concept used in this project. Organized by topic, starting from the most beginner-friendly.

---

## 1. Architecture Decision Records (ADRs)

**What it is:** A short doc that records a technical decision, why you made it, and what trade-offs you accepted.

- [ADR GitHub — by Michael Nygard](https://github.com/joelparkerhenderson/architecture-decision-record) — Templates and examples
- [Thoughtworks: Lightweight ADRs](https://www.thoughtworks.com/radar/techniques/lightweight-architecture-decision-records) — Why companies use them
- [Cognitect: When to write an ADR](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) — The original blog post that started ADRs

**Key takeaway:** ADRs are NOT design docs. They're one-page records of "we chose X over Y because Z." They prevent the "why did we do this?" question 6 months later.

---

## 2. pgvector and Vector Search

**What it is:** A PostgreSQL extension that lets you store and search high-dimensional vectors (like AI embeddings) alongside your regular database tables.

- [pgvector GitHub README](https://github.com/pgvector/pgvector) — Official docs, index types, query syntax
- [Supabase: pgvector Guide](https://supabase.com/docs/guides/ai/vector-columns) — How to use pgvector on Supabase specifically
- [HNSW Explained Simply](https://www.pinecone.io/learn/series/faiss/hnsw/) — Visual walkthrough of how HNSW indexing works (from Pinecone, but concept applies to pgvector)
- [IVFFlat vs HNSW](https://neon.tech/docs/extensions/pgvector#ivfflat-versus-hnsw) — When to use which index type

**Key takeaway:** pgvector lets you do `ORDER BY embedding <=> query_vector` — that's a similarity search. HNSW makes it fast. IVFFlat uses less disk but needs more memory to build.

---

## 3. Embeddings (Voyage AI)

**What it is:** Converting text into a list of numbers (a "vector") that captures its meaning. Similar texts get similar vectors.

- [What are Embeddings? (Vicki Boykis)](https://vickiboykis.com/what_are_embeddings/) — Best beginner explanation
- [Voyage AI Docs](https://docs.voyageai.com/) — API reference, models, pricing
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings) — Concept explanation (applies to Voyage too)

**Key takeaway:** Embeddings turn "SSN transposition error" and "typo in social security number digits" into vectors that are close together — enabling semantic search instead of keyword matching.

---

## 4. RAG (Retrieval-Augmented Generation)

**What it is:** Instead of asking an LLM a question from memory, you first retrieve relevant documents, then ask the LLM to answer using those documents as evidence.

- [RAG Explained (Anthropic)](https://docs.anthropic.com/en/docs/build-with-claude/retrieval-augmented-generation) — Official Anthropic RAG guide
- [LangChain RAG Tutorial](https://python.langchain.com/docs/tutorials/rag/) — Hands-on Python code
- [Ragas Docs](https://docs.ragas.io/) — How to evaluate RAG quality (faithfulness, relevancy, precision)

**Key takeaway:** RAG = Retrieve first, then Generate. It reduces hallucination because the LLM cites evidence instead of guessing.

---

## 5. LangChain and LangGraph

**What it is:** LangChain is a framework for building LLM-powered apps. LangGraph adds state machines for multi-step agent workflows.

- [LangChain Python Docs](https://python.langchain.com/docs/introduction/) — Getting started
- [LangGraph Concepts](https://langchain-ai.github.io/langgraph/concepts/) — State machines, nodes, edges
- [LangSmith Docs](https://docs.smith.langchain.com/) — Tracing, observability, cost tracking

**Key takeaway:** LangGraph lets us build the triage workflow as a state machine: candidate pair comes in → score it → route to auto-merge, steward review, or separate. Each step is a node with clear inputs and outputs.

---

## 6. MDM (Master Data Management) Concepts

**What it is:** The practice of keeping one "golden record" per real-world entity (patient, provider, facility) across multiple source systems.

- [Profisee: What is MDM?](https://profisee.com/master-data-management-what-why-how-who/) — Non-technical overview
- [Reltio: MDM Fundamentals](https://www.reltio.com/blog/master-data-management-101/) — From a vendor perspective
- Our own [mdm-domain-notes.md](mdm-domain-notes.md) — Matching algorithms, survivorship, and healthcare-specific notes

**Key takeaway:** MDM is about answering "is Patient A in System 1 the same person as Patient B in System 2?" That's the matching problem Resolve automates.

---

## 7. String Matching Algorithms

**What it is:** Algorithms that measure how similar two strings are — used to compare patient names, addresses, etc.

- [Jaro-Winkler Explained](https://en.wikipedia.org/wiki/Jaro%E2%80%93Winkler_distance) — Favours matches at the start of strings (good for names)
- [Soundex Explained](https://en.wikipedia.org/wiki/Soundex) — Phonetic coding ("Smith" = "Smyth")
- [RapidFuzz Python Library](https://github.com/rapidfuzz/RapidFuzz) — Fast fuzzy string matching in Python
- [Jellyfish Python Library](https://github.com/jamesturk/jellyfish) — Jaro-Winkler, Soundex, Metaphone in Python

**Key takeaway:** No single algorithm works for all cases. Name matching needs Jaro-Winkler + Soundex. Address matching needs normalization + token comparison. SSN matching is exact (last 4).

---

## 8. PHI Safety and HIPAA

**What it is:** Protected Health Information (PHI) is any data that can identify a patient. HIPAA requires it to be safeguarded.

- [HHS: What is PHI?](https://www.hhs.gov/hipaa/for-professionals/privacy/laws-regulations/index.html) — Official definition
- [Presidio (Microsoft)](https://microsoft.github.io/presidio/) — Open-source PII/PHI detection and anonymization
- [Anthropic: Responsible AI](https://www.anthropic.com/research) — How Claude handles sensitive data

**Key takeaway:** Before sending any patient data to Claude or Voyage AI, we must redact PHI (names, SSNs, DOBs, addresses). Presidio does this automatically using NER (Named Entity Recognition).

---

## 9. Evaluation and Metrics

**What it is:** Measuring whether your AI system actually works — not just "does it run" but "does it give correct, grounded, faithful answers."

- [Ragas Documentation](https://docs.ragas.io/) — RAG evaluation metrics explained
- [LangSmith Evaluation](https://docs.smith.langchain.com/evaluation) — Tracing and benchmarking LLM apps
- [Anthropic: Measuring AI Safety](https://www.anthropic.com/research) — How to think about AI evaluation

**Key takeaway:** The metrics that matter for Resolve: Faithfulness (does the rationale cite real evidence?), Decision Agreement (does the AI agree with expert stewards?), and Auto-Merge Precision (of auto-merges, how many were correct?).

---

## 10. Product Management Concepts

**What it is:** How to plan, scope, and track an AI product — PRDs, scope creep, roadmaps.

- [Shreyas Doshi: Writing PRDs](https://twitter.com/shreyas/status/1303489786415505408) — Thread on what makes a good PRD
- [Shape Up (Basecamp)](https://basecamp.com/shapeup) — Alternative to Agile for scoping fixed-time projects
- [Lenny's Newsletter: AI Product Management](https://www.lennysnewsletter.com/) — Practical PM advice

**Key takeaway:** The Version History table in our PRD is a scope creep detector. Every change is logged. At project end, we can trace exactly what expanded, what narrowed, and why.

---

*Last updated: 2026-05-17*

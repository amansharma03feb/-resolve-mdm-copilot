# Verify — Presentation Guide

**For:** Portfolio showcase, interviews, LinkedIn, stakeholder demos
**Duration:** 10-15 min walkthrough or 5-min speed demo
**Author:** Aman Sharma
**Last updated:** 2026-06-04

---

## The Elevator Pitch (30 seconds)

> "I built Verify, an AI copilot that helps operations teams review ambiguous decisions. Instead of spending 15 minutes per case comparing records and reconstructing rationale, a reviewer gets an AI-generated explanation in seconds — with cited evidence, confidence scores, and anomaly alerts. The system uses RAG with hybrid retrieval, PII redaction before any external API call, and a 100-case evaluation harness to measure AI quality. Built with Python, PostgreSQL, Claude, LangChain, and Streamlit."

---

## Demo Flow (10-15 minutes)

### Act 1: The Problem (2 min — talk, no screen)

"Operations teams in healthcare, finance, and government review thousands of decisions weekly. Each one requires cross-checking records, comparing attributes, and writing rationale. It's repetitive, error-prone, and doesn't scale."

**Key numbers to say:**
- 38,867 candidate pairs in the demo dataset
- 144 in the grey zone requiring human review
- Average review time without AI: 12-18 minutes per case
- Target with AI: under 3 minutes

### Act 2: The Dashboard (3 min — live demo)

Open Streamlit: `streamlit run app/streamlit_app.py`

**Show:**
1. **Stats bar at top** — "38,867 total pairs across 3 tiers: 60 auto-merged, 144 pending review, 38,663 separated"
2. **Pending Review tab** — "These are the grey-zone cases that need human judgment"
3. **Expand one candidate** — Show side-by-side comparison table, scoring metrics
4. **Point out:** "Name score 0.727, but DOB, SSN, address all 1.0 — this is likely the same person with a name variant"

**What to say:** "The dashboard organises decisions into three tiers using composite scoring. Auto-merge handles the obvious ones. Separate handles the obvious non-matches. The interesting work is in Pending Review — that's where AI rationale helps."

### Act 3: AI Rationale (3 min — live demo, the WOW moment)

1. **Click "Generate AI Rationale"** on a Pending Review candidate
2. **While it generates:** "Behind the scenes, the system redacts PII using spaCy NER, sends the redacted data to Claude, and gets back a structured response — recommendation, confidence, evidence citations, and plain-English rationale."
3. **When result appears:** Read the rationale aloud. "It says SAME with 92% confidence because DOB and SSN are exact matches, and the name difference is a known nickname variant."

**What to say:** "This took 8 seconds. Without AI, this review takes 14 minutes. The rationale is cached — next time anyone opens this pair, it loads instantly."

**Technical depth (if asked):**
- Pydantic enforces output schema (recommendation, confidence, evidence, rationale_text)
- PII redaction strips PERSON, DATE, GPE, LOC, ORG entities before the LLM call
- Every LLM call is logged to an audit table (model, input length, response length, cost)
- LangSmith traces capture latency and cost per call

### Act 4: Ops Q&A (2 min — live demo)

Switch to **Ops Q&A** tab.

**Type:** "How does the team handle nickname differences like Bob vs Robert?"

**What to say while waiting:** "This is a RAG pipeline — it embeds the question, runs hybrid search (vector + full-text) over 110 reviewer notes, reranks with Cohere, and sends the top 5 to Claude with a grounding prompt."

**When result appears:** "95% confidence, citing two specific notes. It found that Maria Rodriguez merged Robert/Bob with 0.97 confidence because SSN and DOB matched. But it also found a case where nickname mapping caused a false positive — Chris/Christina with different genders and SSNs."

**Other good questions to demo:**
- "What's the standard approach for maiden name changes?"
- "When should a case be escalated?"
- "How are father-son pairs with same names handled?"

### Act 5: Anomaly Watcher (2 min — live demo)

Switch to **Anomaly Watcher** tab.

**Show:**
1. **4 KPI tiles** — Daily Volume, Max Staleness, Avg Confidence, ZIP Coverage
2. **Active Alert** — "Source data staleness exceeds 48h" (this fires because the demo data is static)
3. **Click "Explain Alerts"** — Claude generates a hypothesis: "ETL pipeline likely broken for ~19 days"

**What to say:** "This catches problems before they reach the reviewer queue. If a source feed stops sending data, or confidence scores drift, or attribute completeness drops — the watcher alerts with a specific hypothesis, not just a number."

### Act 6: Engineering Depth (2 min — show code/architecture, for technical audiences)

**Show the architecture diagram** in README.

**Walk through the tech decisions:**

| Decision | Why |
|---|---|
| HNSW over IVFFlat | 370x faster, works on Supabase free tier (ADR-002) |
| Voyage AI over OpenAI | 200M free tokens, retrieval-optimized, 512-dim |
| Hybrid search over pure vector | Catches keyword-specific queries pure vector misses |
| Cohere Rerank | Cross-encoder precision boost, free tier |
| spaCy NER over Presidio | Lighter, sufficient for structured record PII |
| Pydantic output schemas | Forces structured LLM output, catches malformed JSON |

**Show the golden eval set:** "100 hand-labeled cases — 30 high-confidence, 50 grey-zone, 20 low-confidence. The eval harness runs the full pipeline per case and measures decision agreement, auto-resolve precision, and per-tier accuracy."

---

## Talking Points for Interviews

### "Tell me about a project you built recently"

"I built Verify, an AI copilot for operational decision review. The core problem is that ops teams spend 15 minutes per case comparing records and writing rationale. Verify generates that rationale in seconds using Claude, grounded in past decisions via RAG, with PII redacted before any external API call. I built it end-to-end — database design, scoring engine, RAG pipeline, evaluation harness, and Streamlit dashboard."

### "What was the hardest technical challenge?"

Option A (retrieval): "Getting retrieval right. Pure vector search missed keyword-specific queries — when a reviewer asks about 'SSN transposed digits,' semantic similarity alone doesn't catch it. I built a hybrid search function in Postgres that blends vector cosine similarity with full-text ts_rank, then added Cohere reranking on top. Measurably better precision."

Option B (eval): "Building a meaningful eval framework. It's easy to generate plausible-sounding rationale; it's hard to know if it's correct. I labeled 100 cases by hand across the full confidence spectrum, built a harness that runs the complete pipeline per case, and measures decision agreement — does the AI's recommendation match the gold label? That gave us an objective baseline to improve from."

Option C (data safety): "PII handling. The system processes records with names, dates, and locations. Before any data hits Claude's API, spaCy NER strips 5 entity types and replaces them with placeholders. The mapping stays in memory for restore. Every LLM call is audit-logged with redacted input length, response length, and estimated cost. In regulated industries, this isn't optional."

### "How would you scale this?"

"Three axes. First, the scoring engine — blocking on Soundex + DOB reduces candidate pairs from O(n^2) to manageable sets, but at 500K+ records you'd move to PySpark or Dask for the scoring pass. Second, LLM costs — caching rationale to a JSONB column means you pay for generation once per pair. At 100K pairs, you'd batch-generate during off-peak hours. Third, retrieval — HNSW indexes scale linearly with inserts, so the current architecture handles 1M+ embeddings without redesign."

### "Why this stack?"

"Every choice was deliberate. Supabase for Postgres + pgvector in one managed service — no separate vector DB to maintain. Voyage AI for embeddings because they're retrieval-optimized and the free tier covers development. Claude for rationale because it handles structured output reliably and the Pydantic integration via LangChain is clean. Streamlit for the UI because the audience is ops analysts, not developers — it needs to be accessible."

---

## Numbers to Memorise

| Metric | Value |
|---|---|
| Total records | 50,000 synthetic (Synthea) |
| Candidate pairs scored | 38,867 |
| Auto-merged (high confidence) | 60 |
| Pending review (grey zone) | 144 |
| Separated (low confidence) | 38,663 |
| Reviewer notes in RAG | 110 |
| Golden eval cases | 100 (30 HC / 50 GZ / 20 LC) |
| SQL migrations | 18 |
| Python modules | 15+ |
| HNSW speedup | 370x over sequential scan |
| Vector dimensions | 512 (Voyage voyage-3-lite) |
| LLM | Claude Sonnet |
| Rationale generation time | ~8-10 seconds |
| Total build cost (API) | Under $15 |

---

## Questions You Might Get Asked

**Q: Why not use OpenAI instead of Claude?**
A: Claude handles structured JSON output more reliably in my testing, and the LangChain integration with Pydantic schemas is cleaner. The architecture is model-agnostic — swapping to GPT-4 is a one-line change.

**Q: This is synthetic data. Would it work on real data?**
A: Yes — the patterns are the same. Real healthcare data has the same nickname variants, address changes, SSN discrepancies, and data quality issues. Synthea is designed to mimic these. The only change for production: real PII means the redaction layer becomes critical rather than demonstrative.

**Q: What's the accuracy?**
A: The eval harness measures this on 100 hand-labeled cases. First baseline numbers will show decision agreement in the 60-75% range, which is expected for a first pass — the grey-zone cases are genuinely ambiguous, even for human reviewers.

**Q: How much does it cost to run?**
A: Total API spend for the entire build: under $15. Claude Sonnet at ~$3/1M input tokens. Voyage AI free tier. Supabase free tier. Cohere free tier. In production, caching rationale means you pay once per pair.

**Q: What would you add next?**
A: Three things. (1) Connect Q&A to actual decision_candidates so reviewers can ask about specific pairs, not just patterns. (2) Auto-trigger anomaly metric computation daily via Supabase cron. (3) A productivity dashboard tracking reviewer throughput, override rates, and SLA compliance — Feature 6 in the PRD.

---

## Pre-Demo Checklist

- [ ] `streamlit run app/streamlit_app.py` — verify dashboard loads
- [ ] Pending Review tab — at least 1 candidate without cached rationale (for live generate)
- [ ] Ops Q&A tab — test "How does the team handle nickname differences?" 
- [ ] Anomaly Watcher tab — verify KPI tiles render, alert shows
- [ ] Have the architecture diagram ready (README or Excalidraw)
- [ ] Know your numbers (table above)
- [ ] `.env` has all keys: DATABASE_URL, VOYAGE_API_KEY, ANTHROPIC_API_KEY, COHERE_API_KEY, LANGSMITH_API_KEY

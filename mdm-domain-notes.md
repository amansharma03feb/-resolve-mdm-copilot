# MDM Domain Research Notes — Resolve Project

**About this document:** Personal learning notes on master data management in healthcare insurance, drawn from public research \+ 6 years of working alongside MDM stewardship teams. This is the *research* file. The product spec lives in `PRD.md`.

---

## 1\. Executive Summary

Enterprise MDM platforms (Reltio, Informatica, Tamr) have significantly improved entity resolution, duplicate detection, and golden-record creation. But large healthcare insurers still rely heavily on manual stewardship for low-confidence matches, survivorship validation, and audit documentation.

Current MDM systems generate candidate matches using deterministic and probabilistic algorithms, but human stewards remain the final decision-makers for ambiguous records. This creates operational bottlenecks, high labor costs, inconsistent decision-making, weak explainability, and slow audit response cycles.

The proposed solution — **Resolve** — is an AI-assisted stewardship intelligence layer that sits on top of existing MDM systems. It combines LLM-assisted reasoning, retrieval-augmented lineage explanations, anomaly monitoring, and intelligent merge triage to reduce manual review effort while preserving governance and compliance.

---

## 2\. Industry Context — What MDM Solves

**Master Data Management (MDM)** is the discipline of creating a single, trusted, governed "golden record" of core business entities — members, providers, customers, products, organizations.

MDM systems ingest records from multiple source systems and:

1. Identify duplicates  
2. Match related records  
3. Merge records into a canonical profile  
4. Maintain lineage and governance  
5. Distribute trusted records downstream

In healthcare insurance specifically, member data fragments across claims systems, CRM platforms, enrollment systems, provider systems, legacy databases, and call-center tools. Without MDM: duplicate member records emerge, claims processing errors increase, compliance risk grows, reporting becomes unreliable, customer experience degrades.

---

## 3\. Current Problems in Enterprise MDM

### 3.1 Heavy Dependence on Human Stewards

Modern MDM tools suggest matches but can't reliably automate ambiguous cases. Example:

- "John A. Smith" vs "Jonathan Smith"  
- Slight DOB mismatch  
- Address change  
- Missing SSN

Low-confidence match reviews on our platform typically run 12–18 minutes per case when the steward has to pull records from three or more source systems. Cases involving conflicting addresses across claims and enrollment feeds are the slowest, because there's no quick way to surface which source has historically been trusted for that attribute.

### 3.2 Tribal Knowledge Dependency

Our most senior steward had \~5 years of accumulated rules-of-thumb — for example, knowing that a specific legacy enrollment feed had address-format issues from a 2019 migration. When she went on extended leave, the other stewards each took noticeably longer on matches involving that source, because nothing in the platform captured the context she had in her head.

### 3.3 Poor Explainability of Golden Records

During a compliance review on my project, the team needed to trace why a specific member had been merged with another member nearly a year earlier. Reconstructing the rationale took two stewards the better part of a day — pulling logs, steward notes, and trying to piece together a decision originally made by someone who'd since left the team.

### 3.4 Survivorship Complexity

Survivorship determines which attribute values become the final golden record.

Example:

| Source | Address |
| :---- | :---- |
| CRM | Old address |
| Claims | New address |
| Enrollment | Missing |

Address survivorship was the single most-disputed rule on our platform. A simple "most recent" rule worked for active members but failed for members who'd moved and then reverted. We layered in source priority (enrollment \> claims \> CRM) but still saw weekly steward overrides on edge cases that needed human judgment.

### 3.5 Audit & Compliance Pain

Compliance lineage questions that should be 5-minute answers — "which source provided this attribute on this date?" — routinely took 1–2 business days on our project, because they required engineering to extract from raw audit tables rather than a conversational interface stewards could use directly to show why and what data merged and came into the system.

### 3.6 Drift & Data Quality Degradation

We once caught a duplicate-rate spike three weeks after the fact because a source feed had silently changed DOB format/ last and first name swap for a subset of records. The probabilistic matcher scored them as new members. No alert fired because the duplicate-rate report was monthly rather than daily. Catching this kind of drift in hours rather than weeks is one of the strongest use cases for an AI-augmented monitoring layer.

---

## 4\. Research Findings — Matching Methodologies

### 4.1 Deterministic Matching

Exact-rule matching. Examples: SSN exact match, member ID exact match, email exact match.

**Strengths:** high precision, fully explainable, easy to audit, fast. **Weaknesses:** fails on typos, missing fields, formatting differences — "Robert" vs "Bob," abbreviated names, inconsistent address formats. Produces many false negatives.

### 4.2 Probabilistic Matching

Statistical scoring across multiple attributes. Evaluates similarity scores, attribute weights, confidence thresholds, fuzzy matching.

**Strengths:** handles imperfect data, better duplicate detection at scale. **Weaknesses:** harder to explain, requires threshold tuning, produces grey-zone matches that still need humans.

### 4.3 Why Existing MDM Tools Still Need Humans

Current platforms generate candidates, rank confidence, and suggest survivorship. But they can't:

- Explain nuanced decisions in plain English  
- Capture business context  
- Provide conversational lineage  
- Learn organizational rationale dynamically  
- Reduce steward cognitive load

This gap is the opportunity for AI augmentation.

### 4.4 Technical Primer — How Matching Scores Are Actually Computed

This section translates the math behind matching algorithms into plain-English definitions, so you can speak fluently about them in interviews.

#### 4.4.1 String similarity metrics (used on names, addresses, free text)

**Levenshtein distance** *Definition:* The minimum number of single-character edits (insertions, deletions, substitutions) required to transform one string into another. *Plain English:* "How many keystrokes would I need to fix the typo?" *Example:* "Jhon" → "John" is 1 edit (swap H and O). Levenshtein distance \= 1\. *Used for:* Catching typos in names and addresses. *Weakness:* Treats all character positions equally — doesn't favour matches that start the same.

**Jaro-Winkler similarity** *Definition:* A similarity score between 0 and 1, giving extra weight to strings that share a common prefix. *Plain English:* A smarter version of Levenshtein, tuned for human names where the first few characters matter more. *Example:* "Robert" vs "Rob" scores high because they share a 3-character prefix. *Used for:* Industry standard for name matching in MDM probabilistic engines.

**Soundex / phonetic matching** *Definition:* An algorithm that converts a name into a phonetic code so that similar-*sounding* names produce the same code. *Plain English:* "Sound the names out — do they sound the same?" *Example:* "Smith" and "Smyth" both encode to **S530**. *Used for:* Catching spelling variations and transliterations. *Weakness:* Anglo-centric; weaker for non-Western names. Modern alternatives like Metaphone and Double Metaphone handle a broader set of languages.

**N-gram overlap (e.g., bigrams, trigrams)** *Definition:* Break each string into overlapping sequences of N characters, then compute the overlap between the two sets of sequences. *Plain English:* "How many small chunks do these two strings share?" *Example:* "Smith" → bigrams `{sm, mi, it, th}`. "Smyth" → `{sm, my, yt, th}`. Shared bigrams: `{sm, th}` → overlap 2/6. *Used for:* Approximate string matching that's robust to small typos and character reorderings.

**Jaccard similarity** *Definition:* The size of the intersection of two sets divided by the size of their union. Always between 0 and 1\. *Plain English:* "Of all the unique items in either set, what fraction is in both?" *Example:* Address tokens A \= `{123, main, street, NY}`, B \= `{123, main, st, NY}`. Intersection \= 3, Union \= 5\. Jaccard \= 0.6. *Used for:* Address matching by token, comparing sets of attributes.

#### 4.4.2 Vector-space metrics (used on embeddings of names, notes, narratives)

When text is converted to an **embedding** (a list of numbers, e.g., 512 or 1536 dimensions, that captures semantic meaning), we need ways to measure how similar two embeddings are.

**Dot product** *Definition:* Multiply each pair of corresponding elements in two vectors, then sum the results. *Plain English:* A raw number representing how aligned two vectors are. Considers both *direction* and *magnitude* (size). *Math:* For vectors A and B with elements `a1, a2, …` and `b1, b2, …`: `dot(A, B) = a1×b1 + a2×b2 + a3×b3 + …` *Caveat:* Affected by vector magnitude — two long vectors can produce a high dot product even if their meaning differs. Usually normalised before use.

**Cosine similarity** *Definition:* The cosine of the angle between two vectors. Ignores magnitude, focuses purely on direction. *Plain English:* "Are these two pieces of text pointing in the same semantic direction, regardless of how long they are?" *Range:* −1 (opposite meaning) to 1 (identical direction). For embeddings, typically 0 to 1\. *Math:* `cosine(A, B) = dot(A, B) / (|A| × |B|)` — the dot product divided by the product of each vector's length. *Used for:* The most common metric for embedding similarity in RAG and semantic search. pgvector's `<=>` operator is cosine distance. *Example:* Embeddings for "John Smith Jr." and "Jonathan Smith" might score \~0.92 — meaning they're semantically very close even though the strings differ.

**Euclidean distance (L2)** *Definition:* The straight-line distance between two points (vectors) in n-dimensional space. *Plain English:* "If I drew a line from one vector to the other, how long is it?" *Math:* `√[(a1−b1)² + (a2−b2)² + …]` *Used for:* Distance-based clustering, some vector databases default to this. pgvector's `<->` operator is L2.

**Manhattan distance (L1)** *Definition:* Sum of absolute differences between vector elements. Less commonly used in modern RAG but still appears in classical ML.

#### 4.4.3 When to use which (mental model)

| You're comparing… | Best metrics |
| :---- | :---- |
| Names with typos | Jaro-Winkler, Levenshtein |
| Names with phonetic variants | Soundex / Metaphone |
| Addresses by token overlap | Jaccard, n-gram |
| Free-text steward notes / narratives | Cosine similarity on embeddings |
| Exact identifiers (SSN, member ID) | Deterministic equality |

#### 4.4.4 How MDM probabilistic matching combines these

A probabilistic match score is typically a *weighted blend* of multiple metric outputs across multiple attributes. Simplified example:

match\_score(record\_A, record\_B) \=

    0.30 × jaro\_winkler(name)

  \+ 0.20 × jaccard(address\_tokens)

  \+ 0.15 × levenshtein(phone)

  \+ 0.15 × soundex\_match(name)

  \+ 0.10 × exact\_match(DOB)

  \+ 0.10 × cosine(embedding(notes))

If the score crosses a high threshold (e.g., 0.95), auto-merge. If it falls in a grey zone (e.g., 0.65–0.85), send to a steward for review. This is exactly where AI augmentation adds value — explaining *why* a borderline case scored what it did.

---

## 5\. Research Findings — Survivorship Strategies

### Common strategies

1. **Source Priority** — preferred systems override others (e.g., Enrollment \> CRM \> Claims)  
2. **Most Recent Value** — newest timestamp wins  
3. **Most Complete Record** — record with maximum populated fields wins  
4. **Trusted Source by Attribute** — different systems trusted for different attributes (CRM for phone, Claims for address, Enrollment for legal name)  
5. **Custom Hybrid** — combinations of trust, freshness, completeness, and steward overrides

### Problems with existing models

Rules become overly complex, hard to maintain, hard to explain downstream, and logic gets scattered across systems. AI can help by generating rationale summaries, explaining attribute selection, surfacing evidence, and assisting steward decisions in real time.

---

## 6\. Research Findings — Lineage Requirements

### What lineage must capture

Healthcare MDM lineage must record source systems, attribute origins, merge history, steward actions, confidence scores, survivorship reasoning, audit timestamps, and change history.

### Current gaps

Most systems expose lineage technically (raw audit tables, log files) but not conversationally. Users can't ask in plain English: "Why was this member merged?" / "Which source supplied the address?" / "Who approved this merge?" / "What changed last month?" This is a major usability gap and a direct opportunity for RAG.

---

## 7\. Proposed AI-Augmented Solution — Vision

Build an AI-assisted stewardship intelligence layer **on top of** existing MDM systems (not a replacement) to:

- Reduce manual review effort  
- Improve explainability of merge decisions  
- Accelerate audit response  
- Preserve governance  
- Increase trust in golden records

---

## 8\. Strategic Opportunity

This product does **not** aim to replace traditional MDM platforms. It positions as:

- An AI augmentation layer  
- A stewardship intelligence platform  
- An explainability and governance accelerator

Strongest fit:

- Healthcare insurers  
- Highly regulated enterprises (banking, pharma)  
- Organisations with large stewardship teams  
- MDM programs struggling with operational scale

The key market differentiator is not matching itself — incumbents already do that well. The differentiators are: AI-assisted stewardship productivity, explainable merges, conversational lineage, audit acceleration, governance intelligence.

*"Reduce stewardship effort while increasing trust, explainability, and compliance readiness in enterprise MDM workflows."*  

"""
Generate Verify — AI Copilot for Operational Decision Review
Full Learning & Portfolio Presentation using python-pptx
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt
import copy

# ── Colour palette ──────────────────────────────────────────────────────────
DARK_BG   = RGBColor(0x0F, 0x17, 0x2A)   # near-black navy
ACCENT    = RGBColor(0x4A, 0x90, 0xD9)   # cornflower blue
ACCENT2   = RGBColor(0xF5, 0xA6, 0x23)   # amber
GREEN     = RGBColor(0x27, 0xAE, 0x60)   # success green
RED       = RGBColor(0xE7, 0x4C, 0x3C)   # error red
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT     = RGBColor(0xCC, 0xD6, 0xE8)   # muted text
CARD_BG   = RGBColor(0x1A, 0x25, 0x3A)   # card bg

prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)

BLANK = prs.slide_layouts[6]   # completely blank


# ── Helper functions ─────────────────────────────────────────────────────────

def add_slide():
    return prs.slides.add_slide(BLANK)

def bg(slide, color=DARK_BG):
    """Fill the whole slide with a solid colour."""
    from pptx.util import Emu
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = color

def box(slide, left, top, width, height,
        fill=None, line=None, line_width=Pt(1)):
    """Add a coloured rectangle shape."""
    from pptx.util import Inches
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    shape.fill.solid() if fill else shape.fill.background()
    if fill:
        shape.fill.fore_color.rgb = fill
    if line:
        shape.line.color.rgb = line
        shape.line.width = line_width
    else:
        shape.line.fill.background()
    return shape

def txt(slide, text, left, top, width, height,
        size=Pt(18), bold=False, color=WHITE,
        align=PP_ALIGN.LEFT, wrap=True, italic=False):
    """Add a text box."""
    txb = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    txb.word_wrap = wrap
    tf = txb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = size
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return txb

def txt_lines(slide, lines, left, top, width, height,
              size=Pt(16), color=WHITE, bold_first=False, line_spacing=None):
    """Add a multi-line text box where each item in lines is a string."""
    from pptx.util import Pt as _Pt
    txb = slide.shapes.add_textbox(
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    txb.word_wrap = True
    tf = txb.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        if line_spacing:
            p.space_before = _Pt(line_spacing)
        run = p.add_run()
        run.text = line
        run.font.size = size
        run.font.color.rgb = color
        if bold_first and i == 0:
            run.font.bold = True
    return txb

def accent_bar(slide, color=ACCENT):
    """Top accent stripe."""
    box(slide, 0, 0, 13.33, 0.07, fill=color)

def section_tag(slide, label, left=0.4, top=0.12, color=ACCENT):
    """Small ALL-CAPS label above the title."""
    txt(slide, label.upper(), left, top, 5, 0.35,
        size=Pt(11), bold=True, color=color)

def divider(slide, top, color=ACCENT, opacity_pct=40):
    """Thin horizontal line."""
    box(slide, 0.4, top, 12.53, 0.02, fill=color)

def card(slide, left, top, width, height, title, body_lines,
         title_color=ACCENT, body_color=LIGHT, title_size=Pt(14),
         body_size=Pt(13)):
    """A rounded-ish card with title + bullet list."""
    box(slide, left, top, width, height, fill=CARD_BG,
        line=ACCENT, line_width=Pt(0.75))
    txt(slide, title, left+0.15, top+0.1, width-0.3, 0.35,
        size=title_size, bold=True, color=title_color)
    body_top = top + 0.45
    for line in body_lines:
        txt(slide, f"• {line}", left+0.15, body_top, width-0.3, 0.32,
            size=body_size, color=body_color)
        body_top += 0.3


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — TITLE
# ════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
box(s, 0, 0, 13.33, 0.08, fill=ACCENT)
box(s, 0, 7.42, 13.33, 0.08, fill=ACCENT)

# Big decorative square
box(s, 9.8, 0.8, 3.1, 5.9, fill=CARD_BG, line=ACCENT, line_width=Pt(2))
txt(s, "VERIFY", 10.0, 1.5, 2.7, 1.5, size=Pt(52), bold=True, color=ACCENT, align=PP_ALIGN.CENTER)
txt(s, "AI Copilot for\nOperational\nDecision Review", 9.9, 3.0, 2.9, 2.0,
    size=Pt(18), color=LIGHT, align=PP_ALIGN.CENTER)

txt(s, "VERIFY", 0.5, 0.8, 9, 1.5, size=Pt(68), bold=True, color=WHITE)
txt(s, "AI Copilot for Operational Decision Review",
    0.5, 2.35, 9, 0.7, size=Pt(26), color=ACCENT)
divider(s, 3.15, color=ACCENT2)

txt(s, "End-to-end portfolio project — Day 1 through Day 41",
    0.5, 3.35, 9, 0.45, size=Pt(18), color=LIGHT)

tags = [
    ("Python 3.10+", ACCENT),
    ("Claude Sonnet", ACCENT2),
    ("LangChain + RAG", GREEN),
    ("PostgreSQL + pgvector", ACCENT),
    ("Streamlit", ACCENT2),
]
tx = 0.5
for tag, col in tags:
    box(s, tx, 4.05, len(tag)*0.12+0.3, 0.38, fill=CARD_BG, line=col)
    txt(s, tag, tx+0.1, 4.08, len(tag)*0.12+0.1, 0.32,
        size=Pt(12), bold=True, color=col)
    tx += len(tag)*0.12 + 0.5

txt(s, "Aman Sharma  |  Sr. Business Analyst  |  2026",
    0.5, 4.7, 9, 0.4, size=Pt(14), color=LIGHT)

txt(s, "41 days  •  40+ commits  •  <$15 total API cost  •  v1.0 shipped",
    0.5, 5.2, 9, 0.4, size=Pt(13), italic=True, color=RGBColor(0x88,0xA0,0xC0))


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — THE PROBLEM
# ════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
section_tag(s, "The Problem")
txt(s, "Operations Teams Are Drowning in Manual Review", 0.4, 0.5, 12.5, 0.9,
    size=Pt(34), bold=True, color=WHITE)
divider(s, 1.5)

pains = [
    ("⏱  15 min/case", "Cross-checking records, comparing attributes, reconstructing rationale by hand"),
    ("🔍  No explanation", "Existing tools surface raw scores — reviewers must interpret them alone"),
    ("📋  Audit is slow", "Responding to audit questions requires engineering mediation, often 24–48h delay"),
    ("📈  Volume grows", "As decision volumes scale, manual review becomes the critical bottleneck"),
]
tops = [1.65, 2.75, 3.85, 4.95]
for (title, desc), top in zip(pains, tops):
    box(s, 0.4, top, 12.5, 0.95, fill=CARD_BG, line=ACCENT, line_width=Pt(0.5))
    txt(s, title, 0.6, top+0.08, 2.8, 0.4, size=Pt(17), bold=True, color=ACCENT2)
    txt(s, desc, 3.5, top+0.08, 9.2, 0.75, size=Pt(14), color=LIGHT)

txt(s, "Industries affected: Healthcare  •  Finance  •  Government  •  Insurance  •  Supply Chain",
    0.4, 6.15, 12.5, 0.35, size=Pt(13), italic=True, color=LIGHT, align=PP_ALIGN.CENTER)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — SOLUTION OVERVIEW
# ════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
section_tag(s, "Solution")
txt(s, "What Verify Does", 0.4, 0.5, 12.5, 0.7, size=Pt(36), bold=True, color=WHITE)
divider(s, 1.3)

features = [
    ("🤖  AI Rationale", ACCENT, [
        "SAME / DISTINCT / ESCALATE decision in seconds",
        "Confidence score + specific evidence citations",
        "Plain-English explanation, cached per pair",
        "PII redacted before any external API call",
    ]),
    ("💬  Ops Q&A", ACCENT2, [
        "Ask plain-English questions over decision history",
        "Hybrid RAG: vector + full-text + Cohere rerank",
        "Every answer cites specific reviewer notes",
        "110 synthetic reviewer notes, embedded + indexed",
    ]),
    ("🚨  Anomaly Watcher", GREEN, [
        "4 KPI metrics: volume, freshness, confidence, completeness",
        "2σ deviation flags + 30-day sparklines",
        "Claude-generated hypothesis for each alert",
        "Catches feed failures before they hit the queue",
    ]),
]

lefts = [0.4, 4.55, 8.7]
for (title, col, items), left in zip(features, lefts):
    box(s, left, 1.45, 3.9, 5.7, fill=CARD_BG, line=col, line_width=Pt(1.5))
    txt(s, title, left+0.15, 1.55, 3.6, 0.5, size=Pt(17), bold=True, color=col)
    divider(s, 2.1+0*(left), color=col)
    body_top = 2.2
    for item in items:
        txt(s, f"• {item}", left+0.15, body_top, 3.6, 0.38, size=Pt(12.5), color=LIGHT)
        body_top += 0.42

txt(s, "Result: Review time drops from 14 minutes to under 3 minutes per case",
    0.4, 7.1, 12.5, 0.35, size=Pt(14), bold=True,
    color=ACCENT2, align=PP_ALIGN.CENTER)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — ARCHITECTURE
# ════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
section_tag(s, "Architecture")
txt(s, "System Architecture — Layer by Layer", 0.4, 0.5, 12.5, 0.7,
    size=Pt(34), bold=True, color=WHITE)
divider(s, 1.3)

layers = [
    ("UI Layer", ACCENT, "Streamlit Reviewer Dashboard",
     "Reviewer Inbox  •  Ops Q&A Chat  •  Anomaly Watcher  •  Eval Results Tab"),
    ("Orchestration", ACCENT2, "LangGraph Triage Router",
     "Auto-Merge (≥0.95)  •  Steward Review (0.60–0.94)  •  Auto-Separate (<0.60)"),
    ("RAG Pipeline", RGBColor(0x9B,0x59,0xB6), "LangChain + LangSmith",
     "pgvector Retriever → Cohere Rerank → PII Redaction → Claude Sonnet"),
    ("Data Layer", RGBColor(0x34,0x49,0x5E), "Supabase PostgreSQL",
     "raw.synthea_patients  •  staging.members  •  reviewer_notes + HNSW index"),
    ("External APIs", RGBColor(0x95,0xA5,0xA6), "Voyage AI  •  Anthropic  •  Cohere  •  LangSmith",
     "Embeddings  •  LLM Rationale  •  Reranking  •  Observability tracing"),
]

top = 1.45
for (label, col, tech, detail) in layers:
    box(s, 0.4, top, 1.2, 0.72, fill=col)
    txt(s, label, 0.45, top+0.14, 1.1, 0.45,
        size=Pt(11), bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    box(s, 1.65, top, 11.25, 0.72, fill=CARD_BG, line=col, line_width=Pt(0.5))
    txt(s, tech, 1.8, top+0.03, 5.0, 0.32, size=Pt(13), bold=True, color=WHITE)
    txt(s, detail, 1.8, top+0.35, 11.0, 0.3, size=Pt(11), color=LIGHT)
    top += 0.82

txt(s, "18 SQL migrations  •  15+ Python modules  •  @traceable on all LLM calls",
    0.4, 5.9, 12.5, 0.35, size=Pt(13), italic=True, color=LIGHT, align=PP_ALIGN.CENTER)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — TECH STACK DECISIONS
# ════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
section_tag(s, "Engineering Decisions")
txt(s, "Key Technology Choices & Why", 0.4, 0.5, 12.5, 0.7,
    size=Pt(34), bold=True, color=WHITE)
divider(s, 1.3)

decisions = [
    ("HNSW over IVFFlat", "370× faster similarity search. IVFFlat failed on Supabase free tier. HNSW: 0.6ms vs 239ms sequential scan. Documented in ADR-002.", ACCENT),
    ("Voyage AI over OpenAI Embeddings", "200M free tokens on free tier. Retrieval-optimized model. 512-dim vectors reduce index size vs 1536-dim Ada. Cost: $0 for full build.", ACCENT2),
    ("Hybrid Search over Pure Vector", "Pure vector misses keyword-specific queries ('SSN transposed', 'ZIP+4'). 70/30 blend of cosine + ts_rank. Catches what semantics alone cannot.", GREEN),
    ("Cohere Rerank after retrieval", "Cross-encoder scores query-document relevance more precisely than embedding distance. Free tier. top-50 → rerank → top-5 with fallback if API down.", RGBColor(0x9B,0x59,0xB6)),
    ("spaCy NER for PII redaction", "Lighter than full Presidio. Masks PERSON/DATE/GPE/LOC/ORG before every Claude call. Mapping in memory only — never persisted. ~50ms latency overhead.", RED),
    ("Pydantic structured output", "LLM outputs are inherently unstructured. Pydantic schema enforces recommendation/confidence/evidence/rationale_text. Catches malformed JSON at runtime.", ACCENT),
    ("Claude Sonnet for Rationale", "Handles structured JSON output reliably. LangChain Pydantic integration clean. Model-agnostic via LangChain — swap to GPT-4 with one config line.", ACCENT2),
]

col1, col2 = decisions[:4], decisions[4:]
tops_l = [1.45, 2.65, 3.85, 5.05]
for (title, desc, col), top in zip(col1, tops_l):
    box(s, 0.4, top, 6.2, 1.05, fill=CARD_BG, line=col, line_width=Pt(0.75))
    txt(s, title, 0.55, top+0.05, 6.0, 0.35, size=Pt(13), bold=True, color=col)
    txt(s, desc, 0.55, top+0.4, 6.0, 0.58, size=Pt(11), color=LIGHT)

tops_r = [1.45, 2.65, 3.85]
for (title, desc, col), top in zip(col2, tops_r):
    box(s, 6.85, top, 6.1, 1.05, fill=CARD_BG, line=col, line_width=Pt(0.75))
    txt(s, title, 7.0, top+0.05, 5.9, 0.35, size=Pt(13), bold=True, color=col)
    txt(s, desc, 7.0, top+0.4, 5.9, 0.58, size=Pt(11), color=LIGHT)

txt(s, "Every choice is documented in the Architecture Decision Records (ADRs) in docs/adr/",
    0.4, 6.25, 12.5, 0.35, size=Pt(12), italic=True, color=LIGHT, align=PP_ALIGN.CENTER)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — BUILD PHASES (Days 1–13)
# ════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
section_tag(s, "Build Journey — Phase 1")
txt(s, "Days 1–13: Foundation to Full Feature Build", 0.4, 0.5, 12.5, 0.7,
    size=Pt(32), bold=True, color=WHITE)
divider(s, 1.3)

phases = [
    ("Days 1–2", "Foundation", ACCENT, [
        "50K synthetic Synthea records loaded",
        "Staging layer: normalized names, DOBs, SSN, addresses",
        "PRD written — problem, users, success metrics, risks",
    ]),
    ("Day 3", "Embeddings & Vector Index", ACCENT2, [
        "Voyage AI embeddings (voyage-3-lite, 512-dim)",
        "HNSW index benchmark: 370× faster than sequential",
        "ADR-002 written — indexing strategy documented",
    ]),
    ("Day 4–4b", "Scoring & Dashboard", GREEN, [
        "38,867 candidate pairs scored across 3 tiers",
        "Streamlit reviewer inbox: pagination, dark mode, filters",
        "Tier-specific action buttons (Merge/Separate/Escalate)",
    ]),
    ("Day 5", "Rebrand + Tracing", RGBColor(0x9B,0x59,0xB6), [
        "Renamed: Resolve MDM → Verify (generic ops)",
        "LangSmith tracing wired (@traceable on all chains)",
        "PRD v0.4 updated with version history",
    ]),
    ("Day 6", "PII + AI Rationale", RED, [
        "spaCy NER redact-before-send pattern",
        "Claude rationale: SAME/DISTINCT/ESCALATE + confidence",
        "Audit log: external_llm_calls table",
    ]),
    ("Days 7–9", "Eval + Hybrid RAG", ACCENT, [
        "100-case golden eval set (30 HC / 50 GZ / 20 LC)",
        "Hybrid search: 70% vector + 30% full-text ts_rank",
        "Cohere rerank: top-50 → top-5 cross-encoder",
    ]),
    ("Days 10–13", "Ops Q&A + Anomaly", ACCENT2, [
        "Ops Q&A RAG chain with OpsAnswer Pydantic schema",
        "Chat UI with evidence citations + ops_queries audit",
        "Anomaly Watcher: 4 KPIs, 2σ alerts, Claude hypotheses",
    ]),
]

col_w = 3.8
lefts2 = [0.3, 4.35, 8.4]
tops2  = [1.45, 3.85]
idx = 0
for row_top in tops2:
    for col_left in lefts2:
        if idx >= len(phases):
            break
        (days, title, col, items) = phases[idx]
        box(s, col_left, row_top, col_w, 2.18, fill=CARD_BG, line=col, line_width=Pt(1))
        txt(s, days, col_left+0.15, row_top+0.06, 1.2, 0.28,
            size=Pt(10), bold=True, color=col)
        txt(s, title, col_left+0.15, row_top+0.32, col_w-0.3, 0.35,
            size=Pt(14), bold=True, color=WHITE)
        bt = row_top + 0.7
        for item in items:
            txt(s, f"• {item}", col_left+0.15, bt, col_w-0.3, 0.32,
                size=Pt(11), color=LIGHT)
            bt += 0.33
        idx += 1


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 7 — RAG PIPELINE DEEP DIVE
# ════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
section_tag(s, "Deep Dive — RAG Pipeline")
txt(s, "How Retrieval-Augmented Generation Works in Verify", 0.4, 0.5, 12.5, 0.7,
    size=Pt(30), bold=True, color=WHITE)
divider(s, 1.3)

# Pipeline flow boxes
steps = [
    ("1\nQuery\nReceived", ACCENT),
    ("2\nVoyage AI\nEmbed", ACCENT2),
    ("3\nHybrid\nSearch\nPg", GREEN),
    ("4\nCohere\nRerank", RGBColor(0x9B,0x59,0xB6)),
    ("5\nPII\nRedact", RED),
    ("6\nClaude\nGenerate", ACCENT),
    ("7\nPydantic\nValidate", ACCENT2),
    ("8\nCache +\nDisplay", GREEN),
]
step_w = 1.45
gap = 0.1
start_l = 0.3
top_flow = 1.45
for i, (label, col) in enumerate(steps):
    left = start_l + i*(step_w+gap)
    box(s, left, top_flow, step_w, 1.0, fill=col)
    txt(s, label, left+0.05, top_flow+0.05, step_w-0.1, 0.9,
        size=Pt(11), bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    if i < len(steps)-1:
        txt(s, "→", left+step_w, top_flow+0.35, gap+0.05, 0.3,
            size=Pt(14), bold=True, color=WHITE)

# Details section
details = [
    ("Hybrid Search Formula",
     "score = 0.7 × (1 − cosine_distance) + 0.3 × ts_rank_cd(tsvector, query)\n"
     "Retrieves top-50 candidates from pgvector HNSW index"),
    ("Cohere Rerank",
     "rerank-v3.5 cross-encoder rescores top-50 on query-document relevance\n"
     "Returns top-5 with relevance_score. Fallback to hybrid order if API down"),
    ("PII Redaction",
     "spaCy en_core_web_sm NER masks: PERSON→[PERSON_1], DATE→[DATE_1],\n"
     "GPE/LOC/ORG similarly. Mapping kept in-memory. ~50ms latency"),
    ("Pydantic Output Schema",
     "OpsAnswer(answer_text, cited_evidence_ids, confidence)\n"
     "RationaleOutput(recommendation, confidence, evidence, rationale_text)"),
]
dl = [0.3, 3.55, 6.8, 10.05]
dt = 2.65
for (title, desc), left in zip(details, dl):
    box(s, left, dt, 3.0, 2.2, fill=CARD_BG, line=ACCENT, line_width=Pt(0.5))
    txt(s, title, left+0.1, dt+0.08, 2.8, 0.38, size=Pt(12), bold=True, color=ACCENT)
    txt(s, desc, left+0.1, dt+0.5, 2.8, 1.6, size=Pt(10.5), color=LIGHT)

txt(s, "110 reviewer notes embedded with HNSW index  •  Ops Q&A: answer + cited_evidence_ids + confidence",
    0.4, 6.15, 12.5, 0.35, size=Pt(12), italic=True, color=LIGHT, align=PP_ALIGN.CENTER)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 8 — EVALUATION FRAMEWORK
# ════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
section_tag(s, "Evaluation")
txt(s, "3-Layer Evaluation Framework", 0.4, 0.5, 12.5, 0.7,
    size=Pt(36), bold=True, color=WHITE)
divider(s, 1.3)

layers_eval = [
    ("Layer 1\nGolden Set", ACCENT, [
        "100 hand-labeled cases (30 HC / 50 GZ / 20 LC)",
        "Decision agreement, per-tier accuracy, auto-resolve precision",
        "20-question Ops Q&A golden set — context precision",
        "Run: python eval/run_eval.py",
    ]),
    ("Layer 2\nLLM-as-Judge", ACCENT2, [
        "GPT-4o scores Claude's rationale (cross-model — avoids self-eval bias)",
        "3-dimension rubric: correctness, evidence grounding, clarity (1–5 each)",
        "overall_pass = True if all dimensions ≥ 4",
        "Hallucination proxy: evidence_grounding ≤ 2",
    ]),
    ("Layer 3\nFailure Analysis", GREEN, [
        "Every run generates failure list ranked by confidence-weighted error",
        "Each failure diagnosed: bad retrieval / weak prompt / model confusion",
        "Root cause → prompt tuning → re-run cycle",
        "ADR-004 documents all known limitations honestly",
    ]),
]

lefts3 = [0.4, 4.55, 8.7]
for (label, col, items), left in zip(layers_eval, lefts3):
    box(s, left, 1.45, 3.9, 4.8, fill=CARD_BG, line=col, line_width=Pt(1.5))
    txt(s, label, left+0.15, 1.55, 3.6, 0.65, size=Pt(17), bold=True, color=col,
        align=PP_ALIGN.CENTER)
    divider(s, 2.28, color=col)
    bt = 2.38
    for item in items:
        txt(s, f"• {item}", left+0.15, bt, 3.6, 0.42, size=Pt(12), color=LIGHT)
        bt += 0.43

# Metric targets row
txt(s, "Quality Bars to Ship:", 0.4, 6.4, 3.0, 0.35, size=Pt(13), bold=True, color=WHITE)
metrics_bar = [
    ("Agreement ≥ 85%", GREEN, "93% ✓"),
    ("Faithfulness ≥ 0.85", GREEN, "0.91 ✓"),
    ("Hallucination < 5%", GREEN, "~3% ✓"),
]
ml = 3.6
for (label, col, val) in metrics_bar:
    box(s, ml, 6.35, 2.8, 0.45, fill=col)
    txt(s, f"{label}  →  {val}", ml+0.1, 6.4, 2.6, 0.35,
        size=Pt(12), bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    ml += 3.05


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 9 — EVAL RESULTS
# ════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
section_tag(s, "Eval Results")
txt(s, "Before & After Prompt Tuning", 0.4, 0.5, 12.5, 0.7,
    size=Pt(36), bold=True, color=WHITE)
divider(s, 1.3)

# Big metrics
metrics_big = [
    ("Decision Agreement", "88%", "93%", "+5%", ACCENT),
    ("DISTINCT Accuracy", "60%", "100%", "+40%", GREEN),
    ("Auto-Resolve Precision", "100%", "100%", "— ", ACCENT2),
    ("Hallucination Rate", "~5%", "~3%", "−2%", RED),
]
ml2 = 0.4
for (label, before, after, delta, col) in metrics_big:
    box(s, ml2, 1.45, 3.0, 2.2, fill=CARD_BG, line=col, line_width=Pt(1.5))
    txt(s, label, ml2+0.1, 1.55, 2.8, 0.4, size=Pt(13), bold=True, color=col)
    txt(s, after, ml2+0.1, 2.0, 2.8, 0.75, size=Pt(40), bold=True, color=WHITE,
        align=PP_ALIGN.CENTER)
    txt(s, f"{before} → {after}  ({delta})", ml2+0.1, 2.9, 2.8, 0.35,
        size=Pt(12), color=LIGHT, align=PP_ALIGN.CENTER)
    ml2 += 3.25

# Failure analysis summary
txt(s, "Root Cause Analysis — 12 Failures Found and Fixed", 0.4, 3.85, 12.5, 0.45,
    size=Pt(18), bold=True, color=WHITE)

causes = [
    ("Pattern", "Count", "Root Cause", "Fix Applied", "Result"),
    ("Over-cautious DISTINCT", "8", "No explicit rule for all-zero hard IDs + name=1.0", "Added DISTINCT boundary + few-shot example", "0 remaining ✓"),
    ("Nickname redaction miss", "2", "spaCy redacts WILLIAM, misses BILL", "Score-based fallback: name≥0.75+hard IDs→SAME", "1 fixed, 1 partial"),
    ("Ambiguity misjudgment", "2", "ESCALATE over-classified as DISTINCT post-tuning", "Accepted tradeoff (safer than false SAME)", "Documented ADR-004"),
]

col_widths = [2.8, 1.0, 3.5, 3.5, 1.8]
col_starts = [0.4, 3.3, 4.4, 8.0, 11.6]
row_h = 0.42
table_top = 4.42
header_colors = [CARD_BG]*5
header_colors[0] = ACCENT

for row_idx, row in enumerate(causes):
    for ci, (cell, cw, cs) in enumerate(zip(row, col_widths, col_starts)):
        fill = ACCENT if row_idx == 0 else CARD_BG
        box(s, cs, table_top + row_idx*row_h, cw, row_h, fill=fill,
            line=RGBColor(0x30,0x40,0x55), line_width=Pt(0.5))
        txt(s, cell, cs+0.05, table_top + row_idx*row_h + 0.05,
            cw-0.1, row_h-0.05,
            size=Pt(10.5 if row_idx > 0 else 11),
            bold=(row_idx == 0),
            color=WHITE if row_idx == 0 else LIGHT)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 10 — PII HANDLING ARCHITECTURE
# ════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
section_tag(s, "Data Safety — ADR-005")
txt(s, "PII Handling: Redact-Before-Send Architecture", 0.4, 0.5, 12.5, 0.7,
    size=Pt(30), bold=True, color=WHITE)
divider(s, 1.3)

# Flow diagram
flow_items = [
    ("Record Data\n(names, DOBs,\naddresses)", CARD_BG, ACCENT),
    ("spaCy NER\nen_core_web_sm\n5 entity types", RED, WHITE),
    ("Redacted\nPrompt\n[PERSON_1]...", CARD_BG, GREEN),
    ("Claude\nSonnet\nAPI", RGBColor(0xCC,0x78,0x5C), WHITE),
    ("Structured\nRationale\nJSON", CARD_BG, ACCENT),
]
fw = 2.1
fg = 0.25
fl = 0.4
for i, (label, fill_c, text_c) in enumerate(flow_items):
    left = fl + i*(fw+fg)
    box(s, left, 1.45, fw, 1.15, fill=fill_c, line=text_c, line_width=Pt(1))
    txt(s, label, left+0.1, 1.52, fw-0.2, 1.0, size=Pt(12), bold=True,
        color=text_c, align=PP_ALIGN.CENTER)
    if i < len(flow_items)-1:
        txt(s, "→", left+fw, 1.88, fg+0.1, 0.3, size=Pt(18), bold=True, color=WHITE)

# Mapping note
box(s, 5.1, 2.75, 2.6, 0.6, fill=CARD_BG, line=GREEN, line_width=Pt(0.75))
txt(s, "↑  Mapping dict in memory\n(never persisted to disk)", 5.2, 2.8, 2.4, 0.5,
    size=Pt(10), color=GREEN, align=PP_ALIGN.CENTER)

# Entity types
entities = [
    ("PERSON", "Names", "[PERSON_1]", ACCENT),
    ("DATE", "DOBs", "[DATE_1]", ACCENT2),
    ("GPE", "Cities", "[GPE_1]", GREEN),
    ("LOC", "Regions", "[LOC_1]", RGBColor(0x9B,0x59,0xB6)),
    ("ORG", "Systems", "[ORG_1]", RED),
]
txt(s, "Entities Redacted:", 0.4, 3.55, 3.0, 0.35, size=Pt(13), bold=True, color=WHITE)
el = 0.4
for (etype, example, placeholder, col) in entities:
    box(s, el, 3.95, 2.45, 0.75, fill=CARD_BG, line=col, line_width=Pt(0.75))
    txt(s, etype, el+0.1, 3.98, 2.25, 0.3, size=Pt(12), bold=True, color=col)
    txt(s, f"{example} → {placeholder}", el+0.1, 4.3, 2.25, 0.3, size=Pt(10), color=LIGHT)
    el += 2.6

# Audit log
box(s, 0.4, 4.9, 12.5, 1.4, fill=CARD_BG, line=ACCENT2, line_width=Pt(0.75))
txt(s, "Audit Log — staging.external_llm_calls", 0.55, 4.95, 6.0, 0.38,
    size=Pt(14), bold=True, color=ACCENT2)
audit_cols = ["called_at", "model", "redacted_input_length", "response_length", "cost_estimate_usd"]
audit_notes = ["timestamp", "claude-sonnet-4-6", "chars redacted", "chars response", "estimated $"]
al = 0.55
for col, note in zip(audit_cols, audit_notes):
    txt(s, col, al, 5.42, 2.3, 0.28, size=Pt(11), bold=True, color=ACCENT)
    txt(s, note, al, 5.72, 2.3, 0.28, size=Pt(10), color=LIGHT)
    al += 2.4

txt(s, "Metadata only — no raw PII, no redacted content stored in the log",
    0.55, 6.1, 12.0, 0.28, size=Pt(11), italic=True, color=LIGHT)

txt(s, "42 CFR Part 2: SUD records → forced ESCALATE regardless of confidence. All merges require human approval.",
    0.4, 6.55, 12.5, 0.35, size=Pt(12), bold=True, color=RED, align=PP_ALIGN.CENTER)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 11 — KNOWN LIMITATIONS (ADR-004)
# ════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
section_tag(s, "Honest Engineering — ADR-004")
txt(s, "Known Limitations & Deliberate Tradeoffs", 0.4, 0.5, 12.5, 0.7,
    size=Pt(32), bold=True, color=WHITE)
divider(s, 1.3)

limitations = [
    ("ESCALATE Accuracy: 60%", RED,
     "The ESCALATE tier is inherently subjective — same name/DOB + different SSN could be data entry error OR coincidence. Fixing DISTINCT boundary made model more decisive, dropping ESCALATE accuracy.",
     "Over-classifying ESCALATE as DISTINCT is safer than SAME — a human reviewer catches it. Auto-resolve (SAME ≥0.95) has 100% precision."),
    ("PII Redaction Hides Nicknames", ACCENT2,
     "spaCy redacts 'WILLIAM' but may leave 'BILL' unmasked. The model can't recognise the nickname pair and escalates instead of merging.",
     "Score-based fallback: name_sim ≥0.75 + strong hard IDs → SAME. Fixed 1 of 3 nickname failures. Documented as known edge case."),
    ("Voyage API Rate Limits", ACCENT,
     "Free tier: ~3 req/min. Ops Q&A eval takes ~15 min for 20 questions due to exponential-backoff retries (21s, 42s).",
     "Doesn't affect production UX (single queries). Paid tier upgrade is a config change. Acceptable for portfolio project."),
    ("Synthetic Data Only", GREEN,
     "100 golden-set cases and 110 reviewer notes are synthetic. Real-world distribution of naming patterns and error types may differ.",
     "Synthea designed to mimic real-world complexity. Golden set over-represents edge cases. Real deployment would require validation on production data."),
    ("Single-Model Dependency", RGBColor(0x9B,0x59,0xB6),
     "Both chains use Claude Sonnet. API outage disables copilot entirely.",
     "LangChain abstraction = swap model with one config line. Pydantic schema works with any LLM that supports structured output."),
]

lt = 1.45
for (title, col, problem, mitigation) in limitations:
    box(s, 0.4, lt, 12.5, 0.98, fill=CARD_BG, line=col, line_width=Pt(0.75))
    txt(s, title, 0.55, lt+0.06, 3.0, 0.35, size=Pt(13), bold=True, color=col)
    txt(s, f"⚠  {problem}", 3.65, lt+0.06, 5.5, 0.42, size=Pt(10.5), color=LIGHT)
    txt(s, f"✓  {mitigation}", 3.65, lt+0.5, 9.0, 0.42, size=Pt(10.5), color=GREEN)
    lt += 1.08

txt(s, "Documenting limitations honestly is credibility-positive — it shows we understand the system's boundaries.",
    0.4, 6.85, 12.5, 0.35, size=Pt(12), italic=True, color=LIGHT, align=PP_ALIGN.CENTER)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 12 — KEY NUMBERS
# ════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
section_tag(s, "By the Numbers")
txt(s, "Verify — Key Metrics at a Glance", 0.4, 0.5, 12.5, 0.7,
    size=Pt(36), bold=True, color=WHITE)
divider(s, 1.3)

big_nums = [
    ("50,000", "Synthetic records\n(Synthea)", ACCENT),
    ("38,867", "Candidate pairs\nscored", ACCENT2),
    ("370×", "HNSW speedup\nvs sequential scan", GREEN),
    ("93%", "Decision agreement\nafter tuning", RGBColor(0x9B,0x59,0xB6)),
    ("<$15", "Total API cost\nentire build", RED),
    ("8 sec", "Avg rationale\ngeneration time", ACCENT),
]

bw = 3.9
bl_starts = [0.3, 4.4, 8.5]
bt_rows = [1.45, 3.75]
bi = 0
for bt in bt_rows:
    for bl in bl_starts:
        if bi >= len(big_nums):
            break
        val, label, col = big_nums[bi]
        box(s, bl, bt, bw, 2.05, fill=CARD_BG, line=col, line_width=Pt(1.5))
        txt(s, val, bl+0.1, bt+0.15, bw-0.2, 0.95, size=Pt(46), bold=True, color=col,
            align=PP_ALIGN.CENTER)
        txt(s, label, bl+0.1, bt+1.1, bw-0.2, 0.75, size=Pt(13), color=LIGHT,
            align=PP_ALIGN.CENTER)
        bi += 1

small_stats = [
    "100  Golden eval cases (30 HC / 50 GZ / 20 LC)",
    "110  Reviewer notes embedded + indexed (HNSW)",
    "512  Vector dimensions (voyage-3-lite)",
    "18   SQL migrations",
    "20   Ops Q&A golden set questions",
    "5    PII entity types redacted before LLM call",
    "3    Architecture Decision Records (ADRs)",
    "40+  Git commits across 41 build days",
]

txt(s, "Additional stats:", 0.4, 6.0, 3.0, 0.35, size=Pt(12), bold=True, color=WHITE)
sl = 0.4
for stat in small_stats:
    col = sl
    row_idx = small_stats.index(stat)
    col_offset = 0 if row_idx < 4 else 6.5
    row_top = 6.1 + (row_idx % 4) * 0.3 - (0.0 if row_idx < 4 else 0)
    txt(s, f"• {stat}", 0.4 + col_offset, row_top, 6.0, 0.28, size=Pt(11), color=LIGHT)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 13 — WHAT I LEARNED (BA PERSPECTIVE)
# ════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
section_tag(s, "Key Learnings")
txt(s, "What I Learned — BA Building an AI System", 0.4, 0.5, 12.5, 0.7,
    size=Pt(32), bold=True, color=WHITE)
divider(s, 1.3)

learnings = [
    ("Eval before shipping — always", ACCENT,
     "Starting with a golden set forced precision before writing a line of product code. 88% "
     "agreement felt good. Diagnosing the 12 failures was the actual learning — all were "
     "prompt-level, not retrieval failures. Without eval, I'd have shipped the wrong thing."),
    ("Prompt engineering is disciplined engineering", ACCENT2,
     "Adding explicit decision boundaries + 3 few-shot examples moved DISTINCT accuracy from "
     "60% → 100%. Each change was a hypothesis, measured against the golden set. Grounding "
     "rules ('only claim what is in the data') cut hallucination rate from ~5% to ~3%."),
    ("Tradeoffs deserve documentation", GREEN,
     "ESCALATE accuracy dropped from 80% → 60% after tuning. That's actually correct — "
     "over-classifying ambiguous cases as DISTINCT is safer than SAME. Writing ADR-004 "
     "turned a seeming regression into a documented, reasoned tradeoff."),
    ("PII architecture is a first-class design choice", RED,
     "The redact-before-send pattern wasn't bolted on — it shaped the entire pipeline. "
     "spaCy masking SSN/names before Claude calls means the AI never sees raw PII. "
     "This is architecture, not compliance checkbox."),
    ("Hybrid beats pure vector for operational data", RGBColor(0x9B,0x59,0xB6),
     "Keyword-specific queries ('SSN transposed digits', '42 CFR Part 2') fail pure vector "
     "search. The 70/30 blend with ts_rank_cd caught what semantic similarity missed. "
     "Cohere reranking added another precision layer with zero extra latency in practice."),
    ("Ship something real, then measure", ACCENT,
     "The rebrand from Resolve MDM → Verify (generic ops) happened because the architecture "
     "was sound but the framing was too narrow. Building a working system first revealed "
     "what the broader use case was. You can't refactor a hypothesis."),
]

lt = 1.45
for (title, col, body) in learnings:
    box(s, 0.4, lt, 12.5, 0.92, fill=CARD_BG, line=col, line_width=Pt(0.75))
    txt(s, title, 0.55, lt+0.07, 3.3, 0.35, size=Pt(13), bold=True, color=col)
    txt(s, body, 3.95, lt+0.07, 8.8, 0.78, size=Pt(11), color=LIGHT)
    lt += 1.0


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 14 — ADR SUMMARY
# ════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
section_tag(s, "Architecture Decision Records")
txt(s, "5 ADRs — Decision Log for the Entire Build", 0.4, 0.5, 12.5, 0.7,
    size=Pt(32), bold=True, color=WHITE)
divider(s, 1.3)

adrs = [
    ("ADR-001", "Open-Source Stack Rationale", ACCENT,
     "Why Supabase+pgvector over Pinecone, why Voyage AI over OpenAI embeddings, why "
     "LangChain over bare API calls. Every choice tied back to cost, control, and portability."),
    ("ADR-002", "Vector Indexing Strategy", ACCENT2,
     "HNSW vs IVFFlat benchmarked on actual Supabase free tier. IVFFlat failed (index "
     "creation error on free tier). HNSW: 0.6ms vs 239ms sequential scan = 370× speedup. "
     "Decision: HNSW with ef_construction=200, m=16."),
    ("ADR-003", "Evaluation Methodology", GREEN,
     "3-layer eval: golden set metrics (100 cases), LLM-as-judge (GPT-4o cross-model), "
     "qualitative failure analysis. Quality bars: agreement ≥85%, faithfulness ≥0.85, "
     "hallucination <5%. All three met after round 1 tuning."),
    ("ADR-004", "Known Limitations", RED,
     "ESCALATE accuracy 60% (accepted tradeoff), PII redaction hides nicknames (score-based "
     "workaround), Voyage rate limits (retry logic), synthetic data only, single-model "
     "dependency (LangChain abstraction mitigates)."),
    ("ADR-005", "PII Handling Architecture", RGBColor(0x9B,0x59,0xB6),
     "Redact-before-send: spaCy NER strips PERSON/DATE/GPE/LOC/ORG before every LLM call. "
     "Mapping dict in memory only. Audit log records metadata only. 42 CFR Part 2 forces "
     "ESCALATE. SSN passed as 0/1 score, never as raw digits."),
]

lt = 1.45
for (num, title, col, body) in adrs:
    box(s, 0.4, lt, 12.5, 1.05, fill=CARD_BG, line=col, line_width=Pt(0.75))
    box(s, 0.4, lt, 1.3, 1.05, fill=col)
    txt(s, num, 0.42, lt+0.3, 1.26, 0.4, size=Pt(13), bold=True, color=WHITE,
        align=PP_ALIGN.CENTER)
    txt(s, title, 1.85, lt+0.06, 4.5, 0.38, size=Pt(14), bold=True, color=WHITE)
    txt(s, body, 1.85, lt+0.48, 10.9, 0.5, size=Pt(11), color=LIGHT)
    lt += 1.15


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 15 — DEMO FLOW
# ════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
section_tag(s, "Demo Guide")
txt(s, "4-Minute Demo Script", 0.4, 0.5, 12.5, 0.7,
    size=Pt(36), bold=True, color=WHITE)
divider(s, 1.3)

acts = [
    ("0:00–0:30", "The Problem", ACCENT,
     "Talk without screen. Key numbers: 38,867 pairs, 144 grey-zone, 14-min avg review time."),
    ("0:30–2:00", "Inbox + AI Rationale", ACCENT2,
     "Show Pending Review tab → expand a candidate → click Generate AI Rationale.\n"
     "Say: '8 seconds. Without AI: 14 minutes. Rationale cached for all future viewers.'"),
    ("2:00–3:00", "Ops Q&A", GREEN,
     "Switch to Ops Q&A tab. Ask: 'How does the team handle nickname differences?'\n"
     "Point to citations panel. Say: '2 specific notes cited. Every claim traces back to a real reviewer decision.'"),
    ("3:00–3:30", "Anomaly Watcher", RGBColor(0x9B,0x59,0xB6),
     "Show 4 KPI tiles → active staleness alert → click Explain Alerts.\n"
     "Say: 'Catches feed failures before they hit the reviewer queue.'"),
    ("3:30–4:00", "Eval Dashboard", RED,
     "Switch to Eval Results tab. Show 93% agreement, 100% DISTINCT, all targets met.\n"
     "Say: 'This is the system grading itself — 100 hand-labeled cases, not vibes.'"),
]

lt = 1.45
for (timing, title, col, script) in acts:
    box(s, 0.4, lt, 12.5, 1.05, fill=CARD_BG, line=col, line_width=Pt(0.75))
    box(s, 0.4, lt, 1.5, 1.05, fill=col)
    txt(s, timing, 0.42, lt+0.18, 1.46, 0.65, size=Pt(12), bold=True, color=WHITE,
        align=PP_ALIGN.CENTER)
    txt(s, title, 2.05, lt+0.06, 3.5, 0.38, size=Pt(14), bold=True, color=WHITE)
    txt(s, script, 2.05, lt+0.48, 10.8, 0.5, size=Pt(11), color=LIGHT)
    lt += 1.15

txt(s, "Pre-demo: streamlit run app/streamlit_app.py  •  Verify .env has all 5 keys  •  Have architecture diagram ready",
    0.4, 6.85, 12.5, 0.35, size=Pt(11), italic=True, color=LIGHT, align=PP_ALIGN.CENTER)


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 16 — INTERVIEW ANSWERS
# ════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
section_tag(s, "Interview Prep")
txt(s, "Talking Points for Technical Interviews", 0.4, 0.5, 12.5, 0.7,
    size=Pt(30), bold=True, color=WHITE)
divider(s, 1.3)

qs = [
    ("What was the hardest technical challenge?", ACCENT,
     "Option A — Retrieval: Pure vector missed keyword queries. Built hybrid: 70% cosine + 30% ts_rank_cd, then Cohere rerank. Measurably better precision.\n"
     "Option B — Eval: Built a 100-case golden set + harness. 88% baseline. Diagnosed 12 failures (all prompt-level). Tuned to 93% with 3 few-shot examples + decision boundaries.\n"
     "Option C — Data Safety: spaCy NER redacts before every LLM call. Mapping in memory. Audit log records metadata only. In regulated industries, this is non-negotiable."),
    ("How would you scale this?", ACCENT2,
     "3 axes: (1) Scoring engine — Soundex+DOB blocking reduces O(n²) pairs. At 500K+ records move to PySpark/Dask for scoring pass.\n"
     "(2) LLM cost — rationale cached to JSONB column. Pay once per pair. Batch-generate off-peak.\n"
     "(3) Retrieval — HNSW scales linearly with inserts. Current architecture handles 1M+ embeddings without redesign."),
    ("Why this stack?", GREEN,
     "Every choice was deliberate. Supabase: Postgres+pgvector in one managed service. Voyage AI: retrieval-optimized, 200M free tokens.\n"
     "Claude: reliable structured JSON output + clean Pydantic integration via LangChain. LangChain: model-agnostic — swap to GPT-4 with one config line.\n"
     "Streamlit: ops analysts, not developers — must be accessible without training."),
]

lt = 1.45
for (q, col, answer) in qs:
    box(s, 0.4, lt, 12.5, 1.68, fill=CARD_BG, line=col, line_width=Pt(0.75))
    txt(s, f"Q: {q}", 0.55, lt+0.07, 12.1, 0.38, size=Pt(13), bold=True, color=col)
    txt(s, answer, 0.55, lt+0.5, 12.1, 1.1, size=Pt(10.5), color=LIGHT)
    lt += 1.82


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 17 — ROADMAP / WHAT'S NEXT
# ════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
accent_bar(s)
section_tag(s, "Roadmap")
txt(s, "What's Next — If This Were Production", 0.4, 0.5, 12.5, 0.7,
    size=Pt(34), bold=True, color=WHITE)
divider(s, 1.3)

roadmap = [
    ("🔗  Connect Q&A to Real Decisions", ACCENT,
     "Current Ops Q&A answers questions about patterns in reviewer notes. "
     "Next: wire it to actual decision_candidates so reviewers ask about specific pairs "
     "('Why was HC-2291 marked DISTINCT?') and get case-specific answers."),
    ("📊  Reviewer Productivity Dashboard", ACCENT2,
     "Track throughput per reviewer, override rates (AI vs human disagreement), "
     "SLA compliance, and confidence drift over time. "
     "Gives ops leads actionable quality signals, not just raw decision counts."),
    ("⏰  Automated Anomaly Monitoring", GREEN,
     "Auto-trigger compute_daily_anomaly_metrics() via Supabase cron or pg_cron. "
     "Push Slack alerts when KPIs cross thresholds. "
     "Currently requires manual trigger — automating makes it a true watchdog."),
    ("🧠  Multi-Model Routing", RGBColor(0x9B,0x59,0xB6),
     "Route high-confidence rationale to a cheaper model (Claude Haiku), "
     "escalate complex gray-zone cases to Claude Sonnet. "
     "LangChain abstraction makes this a routing config change, not a rewrite."),
    ("🔐  Presidio Custom Recognizers", RED,
     "Replace spaCy NER with Presidio custom recognizers for healthcare-specific entities: "
     "MRN (medical record number), NPI (provider ID), ICD codes. "
     "Better coverage for real PHI vs synthetic demo data."),
    ("📈  Production Eval on Real Data", ACCENT,
     "Golden set is synthetic — fine for architecture validation. "
     "Real deployment needs eval on production data with business analysts labelling a random "
     "sample. Would likely surface different failure modes than the synthetic set revealed."),
]

lt = 1.45
for (title, col, body) in roadmap:
    box(s, 0.4, lt, 12.5, 0.88, fill=CARD_BG, line=col, line_width=Pt(0.5))
    txt(s, title, 0.55, lt+0.07, 4.5, 0.35, size=Pt(13), bold=True, color=col)
    txt(s, body, 5.15, lt+0.07, 7.65, 0.74, size=Pt(11), color=LIGHT)
    lt += 0.96


# ════════════════════════════════════════════════════════════════════════════
# SLIDE 18 — CLOSING
# ════════════════════════════════════════════════════════════════════════════
s = add_slide()
bg(s)
box(s, 0, 0, 13.33, 0.08, fill=ACCENT)
box(s, 0, 7.42, 13.33, 0.08, fill=ACCENT)

txt(s, "VERIFY", 0.5, 0.9, 12.3, 1.5, size=Pt(72), bold=True, color=WHITE,
    align=PP_ALIGN.CENTER)
txt(s, "AI Copilot for Operational Decision Review",
    0.5, 2.4, 12.3, 0.6, size=Pt(26), color=ACCENT, align=PP_ALIGN.CENTER)

divider(s, 3.15, color=ACCENT2)

stats_closing = [
    ("41 days", "Build days"),
    ("93%", "Decision\nagreement"),
    ("100%", "DISTINCT\naccuracy"),
    ("<$15", "Total\nAPI cost"),
    ("v1.0", "Shipped"),
]
cw = 2.3
cl = (13.33 - cw*5 - 0.2*4) / 2
for val, label in stats_closing:
    box(s, cl, 3.35, cw, 1.6, fill=CARD_BG, line=ACCENT, line_width=Pt(1))
    txt(s, val, cl+0.1, 3.42, cw-0.2, 0.8, size=Pt(36), bold=True, color=ACCENT,
        align=PP_ALIGN.CENTER)
    txt(s, label, cl+0.1, 4.2, cw-0.2, 0.55, size=Pt(12), color=LIGHT,
        align=PP_ALIGN.CENTER)
    cl += cw + 0.2

txt(s, "Built by Aman Sharma  |  Sr. Business Analyst  |  Healthcare Data  |  Seeking Ireland/UK/EU roles",
    0.5, 5.15, 12.3, 0.4, size=Pt(14), color=WHITE, align=PP_ALIGN.CENTER)

links = [
    "github.com/amansharma03feb/-resolve-mdm-copilot",
    "docs/adr/  —  5 Architecture Decision Records",
    "eval/results/  —  Baseline + tuned eval runs",
]
lt = 5.7
for link in links:
    txt(s, f"• {link}", 3.0, lt, 7.5, 0.35, size=Pt(12), color=LIGHT,
        align=PP_ALIGN.CENTER)
    lt += 0.38

txt(s, '"The system grades itself — 100 hand-labeled cases, not vibes."',
    0.5, 6.75, 12.3, 0.45, size=Pt(14), italic=True, color=ACCENT2,
    align=PP_ALIGN.CENTER)


# ════════════════════════════════════════════════════════════════════════════
# Save
# ════════════════════════════════════════════════════════════════════════════
OUT = r"C:\Users\Dell\Documents\resolve-mdm-copilot\docs\Verify-Portfolio-Presentation.pptx"
prs.save(OUT)
print(f"Saved: {OUT}  ({len(prs.slides)} slides)")

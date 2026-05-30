"""Verify — AI Copilot for Operational Decision Review"""

import json
import math
import os
import sys

import pandas as pd
import psycopg2
import streamlit as st
from dotenv import load_dotenv

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

# ── Page config + CSS ───────────────────────────────────────
st.set_page_config(page_title="AI Copilot for Operational Decision Review", page_icon="✓", layout="wide")

st.markdown(
    """
    <style>
    /* Red accent bar — fixed top */
    .stApp::before {
        content: "";
        position: fixed; top: 0; left: 0;
        width: 100%; height: 4px;
        background: linear-gradient(90deg, #dc3545 0%, #ff6b6b 50%, #dc3545 100%);
        z-index: 9999;
    }

    /* Stat cards — transparent, inherit theme colors */
    .stat-card {
        border: 1px solid rgba(128,128,128,0.25);
        border-radius: 10px;
        padding: 18px 12px 14px;
        text-align: center;
        min-height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .stat-label {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        opacity: 0.6;
        margin-bottom: 6px;
    }
    .stat-value {
        font-size: 1.8rem;
        font-weight: 800;
        line-height: 1.1;
    }
    .stat-delta {
        font-size: 0.75rem;
        opacity: 0.5;
        margin-top: 4px;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(128,128,128,0.08);
        border-radius: 10px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        font-weight: 600;
        padding: 10px 24px;
    }
    .stTabs [aria-selected="true"] {
        background: #dc3545 !important;
        color: white !important;
    }

    /* Pagination */
    .page-info {
        text-align: center;
        padding: 10px 0;
        font-size: 0.85rem;
        opacity: 0.65;
    }

    /* Footer */
    .footer {
        text-align: center;
        font-size: 0.72rem;
        padding: 14px 0 6px;
        border-top: 1px solid rgba(128,128,128,0.15);
        margin-top: 20px;
        opacity: 0.5;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── DB helpers ──────────────────────────────────────────────
@st.cache_resource
def get_connection():
    return psycopg2.connect(DB_URL)


def run_query(sql, params=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params or [])
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description] if cur.description else []
    cur.close()
    return rows, cols


def get_stats():
    rows, _ = run_query(
        """
        SELECT tier, COUNT(*), ROUND(AVG(composite_score), 3)
        FROM staging.decision_candidates
        GROUP BY tier
        ORDER BY CASE tier
            WHEN 'AUTO_MERGE' THEN 1 WHEN 'STEWARD_REVIEW' THEN 2 WHEN 'SEPARATE' THEN 3
        END
        """
    )
    total_rows, _ = run_query("SELECT COUNT(*) FROM staging.decision_candidates")
    return rows, total_rows[0][0]


def get_candidates(tier, name_filter, state_filter, per_page, page):
    base = """
        SELECT
            mc.pair_id, mc.composite_score, mc.tier,
            mc.score_name, mc.score_dob, mc.score_ssn, mc.score_address,
            mc.cached_rationale,
            a.first_name AS first_a, a.last_name AS last_a,
            a.date_of_birth AS dob_a, a.ssn_last4 AS ssn_a,
            a.city AS city_a, a.state AS state_a,
            a.source_system AS src_a,
            b.first_name AS first_b, b.last_name AS last_b,
            b.date_of_birth AS dob_b, b.ssn_last4 AS ssn_b,
            b.city AS city_b, b.state AS state_b,
            b.source_system AS src_b,
            ROW_NUMBER() OVER (
                PARTITION BY
                    LEAST(a.name_normalized, b.name_normalized),
                    GREATEST(a.name_normalized, b.name_normalized),
                    LEAST(COALESCE(a.ssn_last4,''), COALESCE(b.ssn_last4,'')),
                    GREATEST(COALESCE(a.ssn_last4,''), COALESCE(b.ssn_last4,''))
                ORDER BY mc.composite_score DESC
            ) AS rn
        FROM staging.decision_candidates mc
        JOIN staging.members a ON mc.member_id_a = a.member_id
        JOIN staging.members b ON mc.member_id_b = b.member_id
        WHERE mc.tier = %s
    """
    params: list = [tier]

    if name_filter:
        base += """
            AND (LOWER(a.first_name || ' ' || a.last_name) LIKE %s
                 OR LOWER(b.first_name || ' ' || b.last_name) LIKE %s)
        """
        like = f"%{name_filter.lower()}%"
        params.extend([like, like])

    if state_filter and state_filter != "All":
        base += " AND (a.state = %s OR b.state = %s)"
        params.extend([state_filter, state_filter])

    wrapped = f"SELECT * FROM ({base}) sub WHERE rn = 1 ORDER BY composite_score DESC"

    count_q = f"SELECT COUNT(*) FROM ({wrapped}) cnt"
    cnt_rows, _ = run_query(count_q, params)
    total_rows = cnt_rows[0][0]

    offset = (page - 1) * per_page
    paged = wrapped + " LIMIT %s OFFSET %s"
    params.extend([per_page, offset])

    data_rows, data_cols = run_query(paged, params)
    rows = [dict(zip(data_cols, r)) for r in data_rows]
    return rows, total_rows


@st.cache_data(ttl=300)
def get_states():
    rows, _ = run_query(
        "SELECT DISTINCT state FROM staging.members WHERE state IS NOT NULL ORDER BY state"
    )
    return ["All"] + [r[0] for r in rows]


# ── Constants ───────────────────────────────────────────────
TIER_BUTTONS = {
    "STEWARD_REVIEW": [("Merge", "primary"), ("Keep Separate", "secondary"), ("Escalate", "secondary")],
    "AUTO_MERGE": [("Confirm Merge", "primary"), ("Undo Merge", "secondary"), ("Escalate", "secondary")],
    "SEPARATE": [("Force Merge", "secondary"), ("Confirm Separate", "primary"), ("Escalate", "secondary")],
}
TIER_DESC = {
    "STEWARD_REVIEW": "Ambiguous decisions needing reviewer judgment — review evidence, then resolve, separate, or escalate.",
    "AUTO_MERGE": "High-confidence matches auto-resolved. Confirm or override if incorrect.",
    "SEPARATE": "Low-confidence pairs kept separate. Force Resolve if you spot a missed match.",
}
TIER_ICONS = {"STEWARD_REVIEW": "🔍", "AUTO_MERGE": "✅", "SEPARATE": "↔️"}


# ── Header ──────────────────────────────────────────────────
st.markdown("## AI Copilot for Operational Decision Review")

try:
    tiers, total = get_stats()
    tier_map = {t: (c, a) for t, c, a in tiers}

    stats = [
        ("TOTAL PAIRS", f"{total:,}", ""),
        ("AUTO MERGE", *[
            (f"{c:,}", f"avg: {a}") for c, a in [tier_map.get("AUTO_MERGE", (0, 0))]
        ][0]),
        ("PENDING REVIEW", *[
            (f"{c:,}", f"avg: {a}") for c, a in [tier_map.get("STEWARD_REVIEW", (0, 0))]
        ][0]),
        ("SEPARATE", *[
            (f"{c:,}", f"avg: {a}") for c, a in [tier_map.get("SEPARATE", (0, 0))]
        ][0]),
    ]

    cols = st.columns(4)
    for col, (label, value, delta) in zip(cols, stats):
        delta_html = f'<div class="stat-delta">{delta}</div>' if delta else '<div class="stat-delta">&nbsp;</div>'
        col.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-label">{label}</div>
                <div class="stat-value">{value}</div>
                {delta_html}
            </div>
            """,
            unsafe_allow_html=True,
        )
except Exception as e:
    st.error(f"DB error: {e}")

st.markdown("")

# ── Filters ─────────────────────────────────────────────────
f1, f2, f3 = st.columns([3, 2, 1])
with f1:
    name_search = st.text_input("🔎 Search by name", placeholder="e.g. Smith, Robert...")
with f2:
    state_pick = st.selectbox("📍 Filter by state", get_states())
with f3:
    per_page = st.selectbox("Per page", [10, 25, 50], index=0)

# ── Tabs ────────────────────────────────────────────────────
tab_review, tab_auto, tab_separate, tab_qa, tab_anomaly = st.tabs([
    f"{TIER_ICONS['STEWARD_REVIEW']} Pending Review",
    f"{TIER_ICONS['AUTO_MERGE']} Auto Resolved",
    f"{TIER_ICONS['SEPARATE']} Separated",
    "💬 Ops Q&A",
    "📊 Anomaly Watcher",
])


def render_tier(tier):
    buttons = TIER_BUTTONS[tier]
    page_key = f"page_{tier}"
    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    st.caption(TIER_DESC[tier])

    candidates, total_rows = get_candidates(
        tier, name_search, state_pick, per_page, st.session_state[page_key]
    )
    total_pages = max(1, math.ceil(total_rows / per_page))

    if st.session_state[page_key] > total_pages:
        st.session_state[page_key] = 1

    if not candidates:
        st.info("No matching candidates found.")
        return

    st.markdown(f"**{total_rows:,} pairs** — page {st.session_state[page_key]} of {total_pages}")

    for c in candidates:
        with st.expander(
            f"#{c['pair_id']}  ·  "
            f"{c['first_a']} {c['last_a']}  ↔  {c['first_b']} {c['last_b']}  ·  "
            f"Score: {c['composite_score']:.3f}  ·  "
            f"{c['state_a'] or '?'} / {c['state_b'] or '?'}",
            expanded=False,
        ):
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Name", f"{c['score_name']:.3f}")
            s2.metric("DOB", f"{c['score_dob']:.3f}")
            s3.metric("SSN", f"{c['score_ssn']:.3f}")
            s4.metric("Address", f"{c['score_address']:.3f}")

            df = pd.DataFrame({
                "Field": ["Name", "DOB", "SSN last4", "City", "State", "Source"],
                "Record A": [
                    f"{c['first_a']} {c['last_a']}", str(c["dob_a"] or "—"),
                    c["ssn_a"] or "—", c["city_a"] or "—",
                    c["state_a"] or "—", c["src_a"],
                ],
                "Record B": [
                    f"{c['first_b']} {c['last_b']}", str(c["dob_b"] or "—"),
                    c["ssn_b"] or "—", c["city_b"] or "—",
                    c["state_b"] or "—", c["src_b"],
                ],
            })
            st.dataframe(df, use_container_width=True, hide_index=True)

            # ── AI Rationale ──
            rationale = c.get("cached_rationale")
            if rationale:
                r = rationale if isinstance(rationale, dict) else json.loads(rationale)
                rec = r.get("recommendation", "—")
                conf = r.get("confidence", 0)
                rec_color = {"SAME": "🟢", "DISTINCT": "🔴", "ESCALATE": "🟡"}.get(rec, "⚪")
                st.markdown(f"**AI Rationale:** {rec_color} **{rec}** · Confidence: **{conf:.0%}**")
                st.caption(r.get("rationale_text", ""))
                if r.get("evidence"):
                    with st.popover("📋 Evidence details"):
                        for ev in r["evidence"]:
                            st.markdown(f"- {ev}")
            else:
                gen_key = f"gen_rationale_{tier}_{c['pair_id']}"
                if st.button("🤖 Generate AI Rationale", key=gen_key, type="secondary"):
                    with st.spinner("Generating rationale..."):
                        try:
                            from src.resolve.phi_safety.redactor import redact_text, restore_text, log_llm_call
                            from src.resolve.rag.rationale import generate_rationale, format_pair

                            rec_a = {"name": f"{c['first_a']} {c['last_a']}", "dob": str(c.get("dob_a", "")),
                                     "ssn": c.get("ssn_a", ""), "city": c.get("city_a", ""),
                                     "state": c.get("state_a", ""), "source": c.get("src_a", "")}
                            rec_b = {"name": f"{c['first_b']} {c['last_b']}", "dob": str(c.get("dob_b", "")),
                                     "ssn": c.get("ssn_b", ""), "city": c.get("city_b", ""),
                                     "state": c.get("state_b", ""), "source": c.get("src_b", "")}
                            scores = {"name": c["score_name"], "dob": c["score_dob"],
                                      "ssn": c["score_ssn"], "address": c["score_address"],
                                      "composite": c["composite_score"]}

                            raw_input = format_pair(rec_a, rec_b, scores)
                            redacted_input, mapping = redact_text(raw_input)
                            result = generate_rationale(rec_a, rec_b, scores, redacted_input=redacted_input)
                            rationale_json = result.model_dump()
                            rationale_json["recommendation"] = rationale_json["recommendation"].value

                            # Cache to DB
                            conn = get_connection()
                            cur = conn.cursor()
                            cur.execute(
                                "UPDATE staging.decision_candidates SET cached_rationale = %s WHERE pair_id = %s",
                                (json.dumps(rationale_json), c["pair_id"]),
                            )
                            conn.commit()
                            cur.close()

                            log_llm_call("claude-sonnet-4-6", len(redacted_input), len(str(rationale_json)))
                            st.rerun()
                        except Exception as e:
                            st.error(f"Rationale generation failed: {e}")

            btn_cols = st.columns([1, 1, 1, 4])
            for idx, (label, btn_type) in enumerate(buttons):
                btn_cols[idx].button(
                    label, key=f"{label.replace(' ', '_').lower()}_{tier}_{c['pair_id']}",
                    type=btn_type,
                )

    # ── Pagination ──
    st.markdown("")
    p1, p2, p3, p4, p5 = st.columns([1, 1, 2, 1, 1])
    with p1:
        if st.button("⏮ First", key=f"first_{tier}", disabled=st.session_state[page_key] <= 1):
            st.session_state[page_key] = 1
            st.rerun()
    with p2:
        if st.button("◀ Prev", key=f"prev_{tier}", disabled=st.session_state[page_key] <= 1):
            st.session_state[page_key] -= 1
            st.rerun()
    with p3:
        st.markdown(
            f'<div class="page-info">Page {st.session_state[page_key]} of {total_pages} ({total_rows:,} pairs)</div>',
            unsafe_allow_html=True,
        )
    with p4:
        if st.button("Next ▶", key=f"next_{tier}", disabled=st.session_state[page_key] >= total_pages):
            st.session_state[page_key] += 1
            st.rerun()
    with p5:
        if st.button("Last ⏭", key=f"last_{tier}", disabled=st.session_state[page_key] >= total_pages):
            st.session_state[page_key] = total_pages
            st.rerun()


with tab_review:
    try:
        render_tier("STEWARD_REVIEW")
    except Exception as e:
        st.error(f"Error: {e}")

with tab_auto:
    try:
        render_tier("AUTO_MERGE")
    except Exception as e:
        st.error(f"Error: {e}")

with tab_separate:
    try:
        render_tier("SEPARATE")
    except Exception as e:
        st.error(f"Error: {e}")

# ── Ops Q&A Tab ───────────────────────────────────────────────
with tab_qa:
    st.caption("Ask questions about past decisions, reviewer actions, and operational patterns. Answers are grounded in reviewer notes with clickable citations.")

    # Initialize chat history
    if "qa_messages" not in st.session_state:
        st.session_state.qa_messages = []

    # Display chat history
    for msg in st.session_state.qa_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("citations"):
                with st.expander("📋 Evidence Citations", expanded=False):
                    for cite in msg["citations"]:
                        st.markdown(
                            f"**[note\\_id={cite['note_id']}]** `{cite['action']}` by {cite['reviewer']} "
                            f"(conf={cite['confidence']:.2f})"
                        )
                        st.caption(cite["note"][:200] + ("..." if len(cite["note"]) > 200 else ""))

    # Chat input
    if question := st.chat_input("Ask about past decisions..."):
        st.session_state.qa_messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Searching reviewer notes and generating answer..."):
                try:
                    import time as _time
                    from src.resolve.rag.lineage_qa import answer_ops_question

                    t0 = _time.time()
                    answer, notes = answer_ops_question(question)
                    latency = _time.time() - t0

                    st.markdown(answer.answer_text)
                    st.caption(f"Confidence: {answer.confidence:.0%} · {len(notes)} notes searched · {latency:.1f}s")

                    # Show cited evidence
                    cited_notes = [n for n in notes if n["note_id"] in answer.cited_evidence_ids]
                    if cited_notes:
                        with st.expander("📋 Evidence Citations", expanded=True):
                            for cite in cited_notes:
                                st.markdown(
                                    f"**[note\\_id={cite['note_id']}]** `{cite['action']}` by {cite['reviewer']} "
                                    f"(conf={cite['confidence']:.2f})"
                                )
                                st.caption(cite["note"][:200] + ("..." if len(cite["note"]) > 200 else ""))

                    # Save to chat history
                    st.session_state.qa_messages.append({
                        "role": "assistant",
                        "content": answer.answer_text,
                        "citations": cited_notes,
                    })

                    # Save to DB
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute(
                            """INSERT INTO staging.ops_queries
                               (question, answer_text, cited_note_ids, confidence, notes_retrieved, latency_s)
                               VALUES (%s, %s, %s, %s, %s, %s)""",
                            (question, answer.answer_text, answer.cited_evidence_ids,
                             answer.confidence, len(notes), round(latency, 3)),
                        )
                        conn.commit()
                        cur.close()
                    except Exception:
                        pass  # DB logging is best-effort

                except Exception as e:
                    st.error(f"Q&A failed: {e}")
                    st.session_state.qa_messages.append({"role": "assistant", "content": f"Error: {e}"})

# ── Anomaly Watcher Tab ───────────────────────────────────────
with tab_anomaly:
    st.caption("Automated anomaly detection across 4 operational metrics. Alerts fire when values exceed 2 standard deviations from the 30-day baseline.")

    try:
        # Daily candidate volume
        vol_rows, _ = run_query("""
            SELECT DATE(created_at) AS day, COUNT(*) AS volume
            FROM staging.decision_candidates
            GROUP BY DATE(created_at)
            ORDER BY day DESC
            LIMIT 30
        """)

        if vol_rows:
            vol_df = pd.DataFrame(vol_rows, columns=["day", "volume"])
            vol_mean = vol_df["volume"].mean()
            vol_std = vol_df["volume"].std()
            vol_latest = vol_df.iloc[0]["volume"] if len(vol_df) > 0 else 0

            # Source freshness
            fresh_rows, _ = run_query("""
                SELECT source_system, MAX(created_at) AS latest,
                       EXTRACT(EPOCH FROM (now() - MAX(created_at))) / 3600 AS hours_stale
                FROM staging.members
                GROUP BY source_system
                ORDER BY hours_stale DESC
            """)
            fresh_df = pd.DataFrame(fresh_rows, columns=["source", "latest", "hours_stale"])

            # Confidence drift (7-day moving avg)
            conf_rows, _ = run_query("""
                SELECT DATE(created_at) AS day,
                       AVG(composite_score) AS avg_score
                FROM staging.decision_candidates
                GROUP BY DATE(created_at)
                ORDER BY day DESC
                LIMIT 30
            """)
            conf_df = pd.DataFrame(conf_rows, columns=["day", "avg_score"])
            conf_mean = conf_df["avg_score"].mean() if len(conf_df) > 0 else 0
            conf_std = conf_df["avg_score"].std() if len(conf_df) > 0 else 0

            # Attribute completeness
            comp_rows, _ = run_query("""
                SELECT source_system,
                       COUNT(*) AS total,
                       SUM(CASE WHEN date_of_birth IS NOT NULL THEN 1 ELSE 0 END)::float / COUNT(*) AS dob_pct,
                       SUM(CASE WHEN ssn_last4 IS NOT NULL THEN 1 ELSE 0 END)::float / COUNT(*) AS ssn_pct,
                       SUM(CASE WHEN zip5 IS NOT NULL THEN 1 ELSE 0 END)::float / COUNT(*) AS zip_pct
                FROM staging.members
                GROUP BY source_system
            """)
            comp_df = pd.DataFrame(comp_rows, columns=["source", "total", "dob_pct", "ssn_pct", "zip_pct"])

            # KPI tiles
            k1, k2, k3, k4 = st.columns(4)
            with k1:
                vol_alert = abs(vol_latest - vol_mean) > 2 * vol_std if vol_std > 0 else False
                badge = "🔴" if vol_alert else "🟢"
                st.metric(f"{badge} Daily Volume", f"{vol_latest:,.0f}", f"avg: {vol_mean:,.0f}")
            with k2:
                max_stale = fresh_df["hours_stale"].max() if len(fresh_df) > 0 else 0
                stale_alert = max_stale > 48
                badge = "🔴" if stale_alert else "🟢"
                st.metric(f"{badge} Max Staleness", f"{max_stale:.0f}h", f"{len(fresh_df)} sources")
            with k3:
                conf_latest = conf_df.iloc[0]["avg_score"] if len(conf_df) > 0 else 0
                conf_alert = abs(conf_latest - conf_mean) > 2 * conf_std if conf_std > 0 else False
                badge = "🔴" if conf_alert else "🟢"
                st.metric(f"{badge} Avg Confidence", f"{conf_latest:.3f}", f"baseline: {conf_mean:.3f}")
            with k4:
                avg_zip = comp_df["zip_pct"].mean() if len(comp_df) > 0 else 0
                zip_alert = avg_zip < 0.5
                badge = "🔴" if zip_alert else "🟢"
                st.metric(f"{badge} ZIP Coverage", f"{avg_zip:.0%}", "across all sources")

            # Sparklines
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                if len(vol_df) > 1:
                    st.markdown("**Daily Candidate Volume (30 days)**")
                    st.line_chart(vol_df.set_index("day")["volume"])
            with c2:
                if len(conf_df) > 1:
                    st.markdown("**Avg Confidence Score (30 days)**")
                    st.line_chart(conf_df.set_index("day")["avg_score"])

            st.markdown("---")
            c3, c4 = st.columns(2)
            with c3:
                st.markdown("**Source Freshness**")
                st.dataframe(fresh_df, use_container_width=True, hide_index=True)
            with c4:
                st.markdown("**Attribute Completeness by Source**")
                st.dataframe(comp_df, use_container_width=True, hide_index=True)

            # Alert explanation
            alerts = []
            if vol_alert:
                alerts.append(f"Daily volume ({vol_latest:,.0f}) is >2σ from baseline ({vol_mean:,.0f} ± {vol_std:,.0f})")
            if stale_alert:
                alerts.append(f"Source data staleness ({max_stale:.0f}h) exceeds 48h threshold")
            if conf_alert:
                alerts.append(f"Confidence score ({conf_latest:.3f}) drifted >2σ from baseline ({conf_mean:.3f})")
            if zip_alert:
                alerts.append(f"ZIP coverage ({avg_zip:.0%}) is below 50% threshold")

            if alerts:
                st.markdown("### ⚠️ Active Alerts")
                for alert in alerts:
                    st.warning(alert)

                # LLM explanation
                if st.button("🤖 Explain Alerts", key="explain_anomaly"):
                    with st.spinner("Generating explanation..."):
                        try:
                            from langchain_anthropic import ChatAnthropic as _ChatAnthropic
                            _llm = _ChatAnthropic(model="claude-sonnet-4-6", max_tokens=256)
                            alert_text = "\n".join(f"- {a}" for a in alerts)
                            resp = _llm.invoke([
                                {"role": "system", "content": "You are a data ops analyst. Given anomaly alerts, write a 1-2 sentence likely cause hypothesis. Be specific and actionable."},
                                {"role": "user", "content": f"Active alerts:\n{alert_text}\n\nWhat is the most likely cause?"},
                            ])
                            st.info(f"**Likely cause:** {resp.content}")
                        except Exception as e:
                            st.error(f"Explanation failed: {e}")
            else:
                st.success("✅ No anomalies detected — all metrics within normal range.")

        else:
            st.info("No candidate data available for anomaly monitoring.")

    except Exception as e:
        st.error(f"Anomaly watcher error: {e}")

# ── Footer ──────────────────────────────────────────────────
st.markdown(
    '<div class="footer">AI Copilot for Operational Decision Review v1.0 · Built in public · '
    '<a href="https://github.com/amansharma03feb/resolve-mdm-copilot">GitHub</a></div>',
    unsafe_allow_html=True,
)

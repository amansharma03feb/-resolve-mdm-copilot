"""Verify — AI Copilot for Operational Decision Review"""

import math
import os

import pandas as pd
import psycopg2
import streamlit as st
from dotenv import load_dotenv

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
tab_review, tab_auto, tab_separate = st.tabs([
    f"{TIER_ICONS['STEWARD_REVIEW']} Pending Review",
    f"{TIER_ICONS['AUTO_MERGE']} Auto Resolved",
    f"{TIER_ICONS['SEPARATE']} Separated",
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

            st.caption("AI rationale: *(coming soon)*")

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

# ── Footer ──────────────────────────────────────────────────
st.markdown(
    '<div class="footer">AI Copilot for Operational Decision Review v1.0 · Built in public · '
    '<a href="https://github.com/amansharma03feb/resolve-mdm-copilot">GitHub</a></div>',
    unsafe_allow_html=True,
)

"""Resolve MDM Copilot — Steward Dashboard v3"""

import math
import os

import pandas as pd
import psycopg2
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

# ── Custom CSS ──────────────────────────────────────────────
st.set_page_config(page_title="Resolve MDM Copilot", page_icon="🔗", layout="wide")

st.markdown(
    """
    <style>
    /* Red accent bar at top */
    .stApp::before {
        content: "";
        display: block;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, #dc3545, #ff6b6b, #dc3545);
        position: fixed;
        top: 0;
        left: 0;
        z-index: 9999;
    }

    /* Metric cards — dark mode aware */
    [data-testid="stMetric"] {
        background: var(--background-color, #f8f9fa);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        text-align: center;
        min-height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    [data-testid="stMetric"] label {
        font-size: 0.7rem !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        opacity: 0.7;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-size: 0.75rem !important;
        opacity: 0.8;
    }

    /* Equal-width metric columns */
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
        flex: 1 1 0 !important;
        min-width: 0 !important;
    }

    /* Tab styling — dark mode aware */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(128, 128, 128, 0.1);
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

    /* Expander headers */
    .streamlit-expanderHeader {
        font-size: 0.9rem !important;
        font-weight: 600;
    }

    /* Pagination */
    .pagination-info {
        text-align: center;
        padding: 8px 0;
        font-size: 0.85rem;
        opacity: 0.7;
    }

    /* Footer */
    .footer {
        text-align: center;
        font-size: 0.75rem;
        padding: 16px 0 8px;
        border-top: 1px solid rgba(128, 128, 128, 0.2);
        margin-top: 24px;
        opacity: 0.6;
    }
    .footer a { opacity: 0.8; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── DB helpers ──────────────────────────────────────────────
@st.cache_resource
def get_connection():
    return psycopg2.connect(DB_URL)


def get_stats():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT tier, COUNT(*), ROUND(AVG(composite_score), 3)
        FROM staging.match_candidates
        GROUP BY tier
        ORDER BY CASE tier
            WHEN 'AUTO_MERGE' THEN 1 WHEN 'STEWARD_REVIEW' THEN 2 WHEN 'SEPARATE' THEN 3
        END
        """
    )
    rows = cur.fetchall()
    cur.execute("SELECT COUNT(*) FROM staging.match_candidates")
    total = cur.fetchone()[0]
    cur.close()
    return rows, total


def get_candidates(tier, name_filter, state_filter, per_page, page):
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT DISTINCT ON (mc.pair_id)
            mc.pair_id, mc.composite_score, mc.tier,
            mc.score_name, mc.score_dob, mc.score_ssn, mc.score_address,
            a.first_name AS first_a, a.last_name AS last_a,
            a.date_of_birth AS dob_a, a.ssn_last4 AS ssn_a,
            a.city AS city_a, a.state AS state_a,
            a.source_system AS src_a,
            b.first_name AS first_b, b.last_name AS last_b,
            b.date_of_birth AS dob_b, b.ssn_last4 AS ssn_b,
            b.city AS city_b, b.state AS state_b,
            b.source_system AS src_b
        FROM staging.match_candidates mc
        JOIN staging.members a ON mc.member_id_a = a.member_id
        JOIN staging.members b ON mc.member_id_b = b.member_id
        WHERE mc.tier = %s
    """
    params: list = [tier]

    if name_filter:
        query += """
            AND (LOWER(a.first_name || ' ' || a.last_name) LIKE %s
                 OR LOWER(b.first_name || ' ' || b.last_name) LIKE %s)
        """
        like = f"%{name_filter.lower()}%"
        params.extend([like, like])

    if state_filter and state_filter != "All":
        query += " AND (a.state = %s OR b.state = %s)"
        params.extend([state_filter, state_filter])

    query += " ORDER BY mc.pair_id, mc.composite_score DESC"

    count_query = f"SELECT COUNT(*) FROM ({query}) sub"
    cur.execute(count_query, params)
    total_rows = cur.fetchone()[0]

    offset = (page - 1) * per_page
    query += " LIMIT %s OFFSET %s"
    params.extend([per_page, offset])

    cur.execute(query, params)
    cols = [desc[0] for desc in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    cur.close()

    rows.sort(key=lambda r: r["composite_score"], reverse=True)
    return rows, total_rows


@st.cache_data(ttl=300)
def get_states():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT DISTINCT state FROM staging.members WHERE state IS NOT NULL ORDER BY state"
    )
    states = [r[0] for r in cur.fetchall()]
    cur.close()
    return ["All"] + states


# ── Constants ───────────────────────────────────────────────
TIER_BUTTONS = {
    "STEWARD_REVIEW": [("Merge", "primary"), ("Keep Separate", "secondary"), ("Escalate", "secondary")],
    "AUTO_MERGE": [("Confirm Merge", "primary"), ("Undo Merge", "secondary"), ("Escalate", "secondary")],
    "SEPARATE": [("Force Merge", "secondary"), ("Confirm Separate", "primary"), ("Escalate", "secondary")],
}

TIER_DESC = {
    "STEWARD_REVIEW": "Ambiguous pairs needing human judgment — review evidence, then merge, separate, or escalate.",
    "AUTO_MERGE": "High-confidence matches auto-merged. Confirm or override if incorrect.",
    "SEPARATE": "Low-confidence pairs kept separate. Force Merge if you spot a missed match.",
}

TIER_ICONS = {"STEWARD_REVIEW": "🔍", "AUTO_MERGE": "✅", "SEPARATE": "↔️"}


# ── Header ──────────────────────────────────────────────────
st.markdown("## Resolve MDM Copilot")
st.caption("AI-Augmented Steward Dashboard for Healthcare Identity Resolution")

try:
    tiers, total = get_stats()
    tier_map = {t: (c, a) for t, c, a in tiers}

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Pairs", f"{total:,}")
    for col, (key, label) in zip(
        [m2, m3, m4],
        [("AUTO_MERGE", "Auto Merge"), ("STEWARD_REVIEW", "Steward Review"), ("SEPARATE", "Separate")],
    ):
        count, avg = tier_map.get(key, (0, 0))
        col.metric(label, f"{count:,}", f"avg: {avg}")
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
    f"{TIER_ICONS['STEWARD_REVIEW']} Steward Review",
    f"{TIER_ICONS['AUTO_MERGE']} Auto Merged",
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

    st.markdown(f"**{total_rows:,} pairs** — showing page {st.session_state[page_key]} of {total_pages}")

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
            f'<div class="pagination-info">Page {st.session_state[page_key]} of {total_pages} ({total_rows:,} pairs)</div>',
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
    '<div class="footer">Resolve MDM Copilot v0.3 · Built in public · '
    '<a href="https://github.com/amansharma03feb/resolve-mdm-copilot">GitHub</a></div>',
    unsafe_allow_html=True,
)

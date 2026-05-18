"""Resolve MDM Copilot — Steward Dashboard v2"""

import os
import psycopg2
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")


@st.cache_resource
def get_connection():
    return psycopg2.connect(DB_URL)


def get_stats():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT tier, COUNT(*) AS pair_count, ROUND(AVG(composite_score), 3) AS avg_score
        FROM staging.match_candidates
        GROUP BY tier
        ORDER BY CASE tier
            WHEN 'AUTO_MERGE' THEN 1
            WHEN 'STEWARD_REVIEW' THEN 2
            WHEN 'SEPARATE' THEN 3
        END
        """
    )
    rows = cur.fetchall()
    cur.execute("SELECT COUNT(*) FROM staging.match_candidates")
    total = cur.fetchone()[0]
    cur.close()
    return rows, total


def get_candidates(tier="STEWARD_REVIEW", name_filter="", state_filter="", limit=50):
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
    params = [tier]

    if name_filter:
        query += """
            AND (
                LOWER(a.first_name || ' ' || a.last_name) LIKE %s
                OR LOWER(b.first_name || ' ' || b.last_name) LIKE %s
            )
        """
        like = f"%{name_filter.lower()}%"
        params.extend([like, like])

    if state_filter and state_filter != "All":
        query += " AND (a.state = %s OR b.state = %s)"
        params.extend([state_filter, state_filter])

    query += " ORDER BY mc.pair_id, mc.composite_score DESC LIMIT %s"
    params.append(limit)

    cur.execute(query, params)
    cols = [desc[0] for desc in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    cur.close()
    return rows


def get_states():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT DISTINCT state FROM staging.members WHERE state IS NOT NULL ORDER BY state"
    )
    states = [r[0] for r in cur.fetchall()]
    cur.close()
    return ["All"] + states


# --- Page Config ---
st.set_page_config(page_title="Resolve MDM Copilot", page_icon="🔗", layout="wide")

# --- Header + Pipeline Stats (top bar) ---
st.title("Resolve MDM Copilot")

try:
    tiers, total = get_stats()
    tier_map = {t: (c, a) for t, c, a in tiers}

    cols = st.columns(4)
    cols[0].metric("Total Pairs", f"{total:,}")
    for i, (tier_name, label) in enumerate(
        [("AUTO_MERGE", "Auto Merge"), ("STEWARD_REVIEW", "Steward Review"), ("SEPARATE", "Separate")]
    ):
        count, avg = tier_map.get(tier_name, (0, 0))
        cols[i + 1].metric(label, f"{count:,}", f"avg: {avg}")
except Exception as e:
    st.error(f"DB error: {e}")

st.divider()

# --- Filters ---
filter_cols = st.columns([3, 2, 1])
with filter_cols[0]:
    name_search = st.text_input("Search by name", placeholder="e.g. Smith, Robert...")
with filter_cols[1]:
    states = get_states()
    state_pick = st.selectbox("Filter by state", states)
with filter_cols[2]:
    row_limit = st.selectbox("Show", [10, 25, 50], index=0)

# --- Tabs per tier ---
tab_review, tab_auto, tab_separate = st.tabs([
    "Steward Review",
    "Auto Merged",
    "Separated",
])

TIER_BUTTONS = {
    "STEWARD_REVIEW": [
        ("Merge", "primary"),
        ("Keep Separate", "secondary"),
        ("Escalate", "secondary"),
    ],
    "AUTO_MERGE": [
        ("Confirm Merge", "primary"),
        ("Undo Merge", "secondary"),
        ("Escalate", "secondary"),
    ],
    "SEPARATE": [
        ("Force Merge", "secondary"),
        ("Confirm Separate", "primary"),
        ("Escalate", "secondary"),
    ],
}

TIER_DESCRIPTIONS = {
    "STEWARD_REVIEW": "Ambiguous pairs that need human judgment. Review the evidence and decide: merge, keep separate, or escalate.",
    "AUTO_MERGE": "High-confidence matches auto-merged by the system. Review and confirm, or override if incorrect.",
    "SEPARATE": "Low-confidence pairs kept separate. Override with Force Merge if you spot a missed match.",
}


def render_candidates(tier, name_filter, state_filter, limit):
    candidates = get_candidates(tier, name_filter, state_filter, limit)
    buttons = TIER_BUTTONS[tier]

    st.caption(TIER_DESCRIPTIONS[tier])

    if not candidates:
        st.info("No matching candidates found.")
        return

    st.markdown(f"**{len(candidates)} candidate pairs**")

    for c in candidates:
        with st.expander(
            f"Pair #{c['pair_id']}  |  "
            f"**{c['first_a']} {c['last_a']}** vs **{c['first_b']} {c['last_b']}**  |  "
            f"Score: {c['composite_score']:.3f}  |  "
            f"{c['state_a'] or '?'} / {c['state_b'] or '?'}",
            expanded=False,
        ):
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Name", f"{c['score_name']:.3f}")
            s2.metric("DOB", f"{c['score_dob']:.3f}")
            s3.metric("SSN", f"{c['score_ssn']:.3f}")
            s4.metric("Address", f"{c['score_address']:.3f}")

            df = pd.DataFrame(
                {
                    "Field": ["Name", "DOB", "SSN last4", "City", "State", "Source"],
                    "Record A": [
                        f"{c['first_a']} {c['last_a']}",
                        str(c["dob_a"] or "N/A"),
                        c["ssn_a"] or "N/A",
                        c["city_a"] or "N/A",
                        c["state_a"] or "N/A",
                        c["src_a"],
                    ],
                    "Record B": [
                        f"{c['first_b']} {c['last_b']}",
                        str(c["dob_b"] or "N/A"),
                        c["ssn_b"] or "N/A",
                        c["city_b"] or "N/A",
                        c["state_b"] or "N/A",
                        c["src_b"],
                    ],
                }
            )
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.caption("AI rationale: *(coming soon)*")

            btn_cols = st.columns([1, 1, 1, 4])
            for idx, (label, btn_type) in enumerate(buttons):
                btn_cols[idx].button(
                    label,
                    key=f"{label.lower().replace(' ', '_')}_{c['pair_id']}",
                    type=btn_type,
                )


with tab_review:
    try:
        render_candidates("STEWARD_REVIEW", name_search, state_pick, row_limit)
    except Exception as e:
        st.error(f"Error: {e}")

with tab_auto:
    try:
        render_candidates("AUTO_MERGE", name_search, state_pick, row_limit)
    except Exception as e:
        st.error(f"Error: {e}")

with tab_separate:
    try:
        render_candidates("SEPARATE", name_search, state_pick, row_limit)
    except Exception as e:
        st.error(f"Error: {e}")

# --- Footer ---
st.divider()
st.caption("Resolve MDM Copilot v0.2 | Built in public | github.com/amansharma03feb/resolve-mdm-copilot")

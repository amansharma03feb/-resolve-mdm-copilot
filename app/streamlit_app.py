"""Resolve MDM Copilot — Steward Dashboard"""

import os
import psycopg2
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


def get_steward_candidates(limit=10):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            mc.pair_id, mc.composite_score,
            mc.score_name, mc.score_dob, mc.score_ssn, mc.score_address,
            a.first_name AS first_a, a.last_name AS last_a,
            a.date_of_birth AS dob_a, a.ssn_last4 AS ssn_a,
            a.city AS city_a, a.state AS state_a, a.zip5 AS zip_a,
            a.source_system AS src_a,
            b.first_name AS first_b, b.last_name AS last_b,
            b.date_of_birth AS dob_b, b.ssn_last4 AS ssn_b,
            b.city AS city_b, b.state AS state_b, b.zip5 AS zip_b,
            b.source_system AS src_b
        FROM staging.match_candidates mc
        JOIN staging.members a ON mc.member_id_a = a.member_id
        JOIN staging.members b ON mc.member_id_b = b.member_id
        WHERE mc.tier = 'STEWARD_REVIEW'
        ORDER BY mc.composite_score DESC
        LIMIT %s
        """,
        (limit,),
    )
    cols = [desc[0] for desc in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    cur.close()
    return rows


def score_color(score):
    if score >= 0.9:
        return "green"
    if score >= 0.7:
        return "orange"
    return "red"


# --- Page Config ---
st.set_page_config(page_title="Resolve MDM Copilot", page_icon="🔗", layout="wide")
st.title("Resolve MDM Copilot")
st.caption("AI-Augmented Steward Dashboard for Healthcare Identity Resolution")

# --- Sidebar Stats ---
st.sidebar.header("Match Pipeline Stats")
try:
    tiers, total = get_stats()
    st.sidebar.metric("Total Candidate Pairs", f"{total:,}")
    for tier, count, avg in tiers:
        st.sidebar.metric(tier, f"{count:,}", f"avg score: {avg}")
except Exception as e:
    st.sidebar.error(f"DB connection failed: {e}")

# --- Steward Inbox ---
st.header("Steward Review Inbox")
st.markdown("Candidate pairs requiring human review. Score breakdown and member details shown side-by-side.")

try:
    candidates = get_steward_candidates(10)

    if not candidates:
        st.info("No STEWARD_REVIEW candidates found.")
    else:
        for i, c in enumerate(candidates):
            with st.container():
                st.divider()

                # Score badge row
                col_badge, col_scores = st.columns([1, 3])
                with col_badge:
                    color = score_color(c["composite_score"])
                    st.markdown(
                        f"### Pair #{c['pair_id']}"
                    )
                    st.markdown(
                        f"**Composite: :{ color }[{c['composite_score']:.3f}]**"
                    )
                with col_scores:
                    s1, s2, s3, s4 = st.columns(4)
                    s1.metric("Name", f"{c['score_name']:.3f}")
                    s2.metric("DOB", f"{c['score_dob']:.3f}")
                    s3.metric("SSN", f"{c['score_ssn']:.3f}")
                    s4.metric("Address", f"{c['score_address']:.3f}")

                # Side-by-side member records
                left, right = st.columns(2)
                with left:
                    st.markdown("**Record A**")
                    st.markdown(f"**Name:** {c['first_a']} {c['last_a']}")
                    st.markdown(f"**DOB:** {c['dob_a']}")
                    st.markdown(f"**SSN last4:** {c['ssn_a'] or 'N/A'}")
                    st.markdown(f"**Location:** {c['city_a'] or ''}, {c['state_a'] or ''} {c['zip_a'] or ''}")
                    st.markdown(f"**Source:** `{c['src_a']}`")

                with right:
                    st.markdown("**Record B**")
                    st.markdown(f"**Name:** {c['first_b']} {c['last_b']}")
                    st.markdown(f"**DOB:** {c['dob_b']}")
                    st.markdown(f"**SSN last4:** {c['ssn_b'] or 'N/A'}")
                    st.markdown(f"**Location:** {c['city_b'] or ''}, {c['state_b'] or ''} {c['zip_b'] or ''}")
                    st.markdown(f"**Source:** `{c['src_b']}`")

                # AI rationale placeholder + action buttons
                st.info("AI rationale: *(coming soon — Week 4)*")
                b1, b2, b3, _ = st.columns([1, 1, 1, 3])
                b1.button("Merge", key=f"merge_{c['pair_id']}", type="primary")
                b2.button("Keep Separate", key=f"sep_{c['pair_id']}")
                b3.button("Escalate", key=f"esc_{c['pair_id']}")

except Exception as e:
    st.error(f"Error loading candidates: {e}")

# --- Footer ---
st.divider()
st.caption("Resolve MDM Copilot v0.1 | Built in public | github.com/amansharma03feb/resolve-mdm-copilot")

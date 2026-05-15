-- 003: Create staging.member_notes with pgvector embedding column
-- Run in Supabase SQL Editor
-- Prerequisites: pgvector extension must be enabled in Supabase (Extensions → pgvector → Enable)

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS staging.member_notes (
    note_id         SERIAL PRIMARY KEY,
    member_id_a     UUID,
    member_id_b     UUID,
    steward         VARCHAR(50),
    action          VARCHAR(20) NOT NULL,
    note            TEXT NOT NULL,
    confidence      NUMERIC(4,2),
    embedding       vector(1024),
    created_at      TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE staging.member_notes IS 'Steward resolution notes with semantic embeddings for RAG retrieval';

CREATE INDEX IF NOT EXISTS idx_member_notes_embedding
    ON staging.member_notes
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 10);

-- ============================================================
-- Insert 10 sample steward notes (synthetic — no real PHI)
-- ============================================================
INSERT INTO staging.member_notes (member_id_a, member_id_b, steward, action, note, confidence) VALUES
(gen_random_uuid(), gen_random_uuid(), 'Maria Rodriguez',  'MERGE',
 'Merged records: same DOB (1985-03-14), SSN last4 match (7842). First name differs — "Robert" vs "Bob" — confirmed common nickname. Address updated from 2019 claims feed to current enrollment address. High confidence match.',
 0.94),

(gen_random_uuid(), gen_random_uuid(), 'Maria Rodriguez',  'SEPARATE',
 'Separated records despite similar names. "James Wilson" vs "James Wilson Jr." — different DOBs (1962 vs 1988), different SSN last4. Father-son pair, not duplicate. Flagged source system CRM for generating false positive on name-only match.',
 0.22),

(gen_random_uuid(), gen_random_uuid(), 'David Chen',       'MERGE',
 'Merged: exact SSN last4 (3291), same DOB, same ZIP. Last name spelling differs — "Garcia" vs "Garciá" — accent from legacy enrollment system migration in 2019. Address is identical. Clear duplicate from the Q3 2019 feed migration.',
 0.97),

(gen_random_uuid(), gen_random_uuid(), 'Maria Rodriguez',  'ESCALATE',
 'Escalated to senior steward. Records share DOB and address but SSN last4 differ (5519 vs 5591 — possible transposition). Name is identical. Need claims history review to confirm — could be twin siblings at same address. Holding merge pending additional evidence.',
 0.71),

(gen_random_uuid(), gen_random_uuid(), 'Sarah Thompson',   'MERGE',
 'Auto-merge approved. Confidence 0.98. Exact match on SSN last4, DOB, first name, last name. Only difference: address — old record has PO Box, new record has street address from recent enrollment update. Both map to same ZIP+4. No override needed.',
 0.98),

(gen_random_uuid(), gen_random_uuid(), 'David Chen',       'SEPARATE',
 'Separated: names are phonetically similar ("Smith" vs "Smyth") but DOBs differ by 12 years. Different states (NY vs NJ). SSN last4 do not match. Soundex match triggered the candidate pair but all other attributes diverge. Clear false positive.',
 0.15),

(gen_random_uuid(), gen_random_uuid(), 'Maria Rodriguez',  'MERGE',
 'Merged after manual review. Member moved from Texas to Florida — address change caused low initial confidence. But SSN last4 match, DOB match, and drivers license number is identical across both records. Updated golden record with Florida address as most recent.',
 0.88),

(gen_random_uuid(), gen_random_uuid(), 'Sarah Thompson',   'ESCALATE',
 'Escalated: conflicting SSN last4 with matching DOB and name. One record from claims (2023), other from enrollment (2021). Possible SSN data entry error in claims feed — requesting source system correction before merge. Tagged for compliance review.',
 0.65),

(gen_random_uuid(), gen_random_uuid(), 'David Chen',       'MERGE',
 'Merged records for member with maiden name change. "Jennifer Adams" (enrollment 2020) and "Jennifer Brooks" (claims 2024). Same DOB, same SSN last4, maiden name field confirms Adams. Marriage name change — standard survivorship: keep most recent last name, preserve maiden.',
 0.91),

(gen_random_uuid(), gen_random_uuid(), 'Maria Rodriguez',  'SEPARATE',
 'Separated despite address match. Two different members living at same group home facility address. Different DOBs, different SSN last4, different first names. Facility address caused false positive in address-based blocking. Added group home address to exclusion list for future blocking runs.',
 0.12);

-- Verify
SELECT note_id, steward, action, confidence, LEFT(note, 60) AS note_preview
FROM staging.member_notes
ORDER BY note_id;

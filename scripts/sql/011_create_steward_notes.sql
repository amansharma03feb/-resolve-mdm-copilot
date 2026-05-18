-- 011: Create steward_notes table with voyage-3-lite (512-dim) embeddings
-- Run in Supabase SQL Editor
-- This replaces the older member_notes approach with a dedicated steward resolution table

CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- STEP 1: Create steward_notes table
-- ============================================================
DROP TABLE IF EXISTS staging.steward_notes;

CREATE TABLE staging.steward_notes (
    note_id         SERIAL PRIMARY KEY,
    steward         VARCHAR(50) NOT NULL,
    action          VARCHAR(20) NOT NULL,
    confidence      NUMERIC(4,2),
    note            TEXT NOT NULL,
    embedding       vector(512),
    created_at      TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE staging.steward_notes IS 'Steward resolution notes with 512-dim Voyage voyage-3-lite embeddings for RAG retrieval';

-- ============================================================
-- STEP 2: Insert 110 synthetic steward notes
-- Varied decisions, attributes, and rationale styles
-- ============================================================
INSERT INTO staging.steward_notes (steward, action, confidence, note) VALUES

-- === MERGE decisions (40 notes) ===
('Maria Rodriguez', 'MERGE', 0.97, 'Merged records: same DOB (1985-03-14), SSN last4 match (7842). First name differs — "Robert" vs "Bob" — confirmed common nickname. Address updated from 2019 claims feed. High confidence match.'),
('David Chen', 'MERGE', 0.95, 'Merged: exact SSN last4 (3291), same DOB, same ZIP. Last name spelling differs — "Garcia" vs "Garci-a" — accent from legacy enrollment system migration in 2019. Clear duplicate.'),
('Sarah Thompson', 'MERGE', 0.98, 'Auto-merge approved. Exact match on SSN last4, DOB, first name, last name. Only difference: PO Box vs street address from recent enrollment update. Both map to same ZIP+4.'),
('Maria Rodriguez', 'MERGE', 0.88, 'Merged after manual review. Member moved from Texas to Florida — address change caused low initial confidence. SSN last4 match, DOB match, drivers license number identical across both records.'),
('David Chen', 'MERGE', 0.91, 'Merged records for maiden name change. "Jennifer Adams" (enrollment 2020) and "Jennifer Brooks" (claims 2024). Same DOB, same SSN last4, maiden name field confirms Adams.'),
('Sarah Thompson', 'MERGE', 0.96, 'Merged: both records from same clinic, entered by different intake staff. Name "Katherine" vs "Catherine" — DOB match, SSN match, address match. Classic spelling variant.'),
('James Liu', 'MERGE', 0.93, 'Merged records with middle name discrepancy. "Michael James Wilson" vs "Michael J Wilson". All other attributes identical. Middle initial truncation from claims system known issue.'),
('Maria Rodriguez', 'MERGE', 0.89, 'Merged: hyphenated last name split across systems. "Maria Santos-Rivera" in enrollment vs "Maria Santos Rivera" in claims. DOB and SSN match confirm same person.'),
('David Chen', 'MERGE', 0.94, 'Merged duplicate from pharmacy feed. Same SSN last4, DOB, and address. First name "Bill" vs "William" — common nickname mapping applies. Pharmacy system uses informal names.'),
('Sarah Thompson', 'MERGE', 0.99, 'Auto-merge: perfect match on all 4 attributes. Records from two different insurance plans for same employer. Member had dual coverage during transition period.'),
('James Liu', 'MERGE', 0.87, 'Merged after address verification. Member at same address but apartment number format differs — "Apt 4B" vs "#4B". Name, DOB, SSN all match.'),
('Maria Rodriguez', 'MERGE', 0.92, 'Merged: transposed digits in address number. "1234 Oak St" vs "1243 Oak St". SSN last4 match, DOB match, name match. Address data entry error confirmed by ZIP match.'),
('David Chen', 'MERGE', 0.90, 'Merged records with suffix difference. "Robert Smith" vs "Robert Smith Jr." — but same DOB, same SSN. Claims records dropped the suffix. Updated golden record to include Jr.'),
('Sarah Thompson', 'MERGE', 0.95, 'Merged: name transliteration difference. "Mohammed" vs "Muhammad" — same person, different romanization of Arabic name. DOB and SSN confirm match.'),
('James Liu', 'MERGE', 0.86, 'Merged after pharmacy and lab records cross-referenced. Same DOB, same SSN last4. Address changed — member relocated within same ZIP code. Updated address to most recent.'),
('Maria Rodriguez', 'MERGE', 0.97, 'Merged: exact duplicate from batch enrollment file reprocessing. Same source system sent same record twice with different source_ids. All attributes identical.'),
('David Chen', 'MERGE', 0.93, 'Merged: "Elisabeth" vs "Elizabeth" — common spelling variant. DOB, SSN, address all match. Enrollment system allowed freetext name entry causing inconsistency.'),
('Sarah Thompson', 'MERGE', 0.88, 'Merged records from different plan years. Same member re-enrolled with slightly different address format. SSN and DOB confirm. Updated coverage dates in golden record.'),
('James Liu', 'MERGE', 0.94, 'Merged: first name and last name swapped in one system. "Kim Park" vs "Park Kim" — Korean name order difference. DOB, SSN, address all confirm same person.'),
('Maria Rodriguez', 'MERGE', 0.91, 'Merged: "Cathy" vs "Catherine" with DOB match and SSN match. Address differs — old record is previous residence. Kept most recent address.'),
('David Chen', 'MERGE', 0.96, 'Merged: one record missing middle initial, otherwise identical. Both from same health system, different EMR instances. Clear system duplicate.'),
('Sarah Thompson', 'MERGE', 0.89, 'Merged member who changed gender marker. Name updated from "Patricia" to "Patrick". Same DOB, same SSN last4, same address. Gender marker updated in golden record.'),
('James Liu', 'MERGE', 0.95, 'Merged: "O''Brien" vs "OBrien" — apostrophe handling differs between systems. All other attributes match perfectly.'),
('Maria Rodriguez', 'MERGE', 0.92, 'Merged records: DOB off by one day (03/14 vs 03/15). SSN match, name match, address match. Birth date likely data entry error — one digit off. Kept earlier DOB per source system reliability ranking.'),
('David Chen', 'MERGE', 0.87, 'Merged: ZIP code differs (75201 vs 75202) but street address is identical. Adjacent ZIP boundary — USPS reassignment. SSN and DOB match.'),
('Sarah Thompson', 'MERGE', 0.97, 'Merged: records from two different provider networks within same health plan. All attributes match. Created during network expansion when provider data was re-ingested.'),
('James Liu', 'MERGE', 0.90, 'Merged: "Aleksandr" vs "Alexander" — transliteration variant. Same DOB, same SSN last4. Immigration paperwork used original spelling, insurance used anglicized version.'),
('Maria Rodriguez', 'MERGE', 0.93, 'Merged: address normalization reveals match. "123 N Main Street" vs "123 North Main St." — same location, different formatting. Name and DOB match.'),
('David Chen', 'MERGE', 0.85, 'Merged after extended review. DOB year differs (1978 vs 1979) but month/day match. SSN match, name match, address match. Likely typo in birth year on one enrollment form.'),
('Sarah Thompson', 'MERGE', 0.98, 'Merged: exact same person enrolled through employer group and individual marketplace. All attributes match. Coordinated benefits correctly.'),
('James Liu', 'MERGE', 0.94, 'Merged: "St." vs "Saint" in address. "123 St. Louis Ave" vs "123 Saint Louis Ave". All PII attributes match.'),
('Maria Rodriguez', 'MERGE', 0.91, 'Merged: old record has maiden name as primary, new record has married name. Maiden name preserved in golden record. DOB and SSN confirm same person.'),
('David Chen', 'MERGE', 0.96, 'Merged: phone number and email differ but name, DOB, SSN, address all match. Contact info updated — member got new phone. Standard survivorship applied.'),
('Sarah Thompson', 'MERGE', 0.88, 'Merged: "Jr" vs "Junior" suffix formatting. All core attributes match. Standardized to "Jr." per style guide.'),
('James Liu', 'MERGE', 0.93, 'Merged: dental and medical records for same member. Different source systems, different source IDs. SSN, DOB, name, address all match.'),
('Maria Rodriguez', 'MERGE', 0.90, 'Merged: "Teresa" vs "Theresa" — first name variant. SSN last4 match, DOB match. Address slightly different — updated apartment number.'),
('David Chen', 'MERGE', 0.97, 'Merged: completely identical records from annual re-enrollment. Same source system re-submitted existing member. Deduplicated.'),
('Sarah Thompson', 'MERGE', 0.86, 'Merged: member uses legal name in enrollment ("William") but preferred name in clinic notes ("Liam"). DOB, SSN, address all confirm same person.'),
('James Liu', 'MERGE', 0.92, 'Merged: Hispanic naming convention difference. "Jose Garcia Lopez" vs "Jose Garcia" — some systems truncate compound last names. DOB and SSN match.'),
('Maria Rodriguez', 'MERGE', 0.95, 'Merged: records from two different states after interstate move. FL enrollment closed, TX enrollment opened. SSN, DOB, name match. Address updated to TX.'),

-- === SEPARATE decisions (35 notes) ===
('Maria Rodriguez', 'SEPARATE', 0.22, 'Separated: "James Wilson" vs "James Wilson Jr." — different DOBs (1962 vs 1988), different SSN last4. Father-son pair at same address.'),
('David Chen', 'SEPARATE', 0.15, 'Separated: names phonetically similar ("Smith" vs "Smyth") but DOBs differ by 12 years. Different states (NY vs NJ). SSN last4 do not match. Clear false positive.'),
('Maria Rodriguez', 'SEPARATE', 0.12, 'Separated despite address match. Two different members at same group home facility. Different DOBs, different SSN last4, different first names.'),
('Sarah Thompson', 'SEPARATE', 0.18, 'Separated: "Maria Garcia" appears twice but DOBs are 30 years apart (1955 vs 1985). Common name, different people. SSN confirms different individuals.'),
('James Liu', 'SEPARATE', 0.20, 'Separated: same last name and similar address (same apartment building). Different DOBs, different SSN last4. Likely neighbors, not duplicates.'),
('David Chen', 'SEPARATE', 0.25, 'Separated: "John Smith" vs "John Smith" — extremely common name collision. DOBs differ by 5 years. Different SSN last4. Different addresses in same city.'),
('Maria Rodriguez', 'SEPARATE', 0.10, 'Separated: only soundex match on last name. Everything else different. Blocking key too broad for this name group — noted for tuning.'),
('Sarah Thompson', 'SEPARATE', 0.30, 'Separated: twins at same address. Same DOB, same last name, same address. But different first names, different SSN last4. Twin siblings confirmed via birth records.'),
('James Liu', 'SEPARATE', 0.14, 'Separated: "Williams" vs "Williamson" — name similarity triggered candidate but clearly different surnames. Different DOB, different SSN.'),
('David Chen', 'SEPARATE', 0.21, 'Separated: spouse pair sharing address and last name. DOBs differ by 3 years. Different SSN, different first names. Married couple, not duplicate.'),
('Maria Rodriguez', 'SEPARATE', 0.16, 'Separated: "Robert Johnson" in Michigan vs "Robert Johnson" in Ohio. Common name, different people. No SSN match, DOBs 7 years apart.'),
('Sarah Thompson', 'SEPARATE', 0.28, 'Separated: same name, same city, DOBs 2 years apart. SSN last4 differ. Cross-referenced claims history — different providers, different conditions. Distinct individuals.'),
('James Liu', 'SEPARATE', 0.11, 'Separated: name match is coincidental. "Lee" is extremely common. Different DOB, different SSN, different address, different state. No relationship.'),
('David Chen', 'SEPARATE', 0.19, 'Separated: soundex groups "Peterson" and "Pederson" together. But DOBs differ, SSN differ, addresses in different states. Phonetic similarity only.'),
('Maria Rodriguez', 'SEPARATE', 0.23, 'Separated: mother and daughter with same first name ("Anna Martinez"). DOBs 25 years apart. Different SSN. Same address — daughter still lives at home.'),
('Sarah Thompson', 'SEPARATE', 0.13, 'Separated: "Chen" vs "Chan" triggered phonetic match. Different DOBs, different SSN, different addresses. Different people entirely.'),
('James Liu', 'SEPARATE', 0.26, 'Separated: roommates sharing apartment. Same address, same last name (coincidence). DOBs differ, SSN differ. Confirmed separate via employer group data.'),
('David Chen', 'SEPARATE', 0.17, 'Separated: name and DOB match but SSN last4 are completely different. Cross-referenced with state ID — two different people with coincidental demographics.'),
('Maria Rodriguez', 'SEPARATE', 0.20, 'Separated: elderly couple — "George" and "Georgia" at same address. Last name match, address match, but different DOBs and SSN. Not duplicates.'),
('Sarah Thompson', 'SEPARATE', 0.15, 'Separated: "Anderson" vs "Andersen" — Scandinavian spelling variants but DOB and SSN confirm different people. Different states.'),
('James Liu', 'SEPARATE', 0.24, 'Separated: grandparent and grandchild pair. Same last name, same address. DOBs 55 years apart. SSN differ. Multi-generational household.'),
('David Chen', 'SEPARATE', 0.18, 'Separated: similar names from same medical practice. Blocking by provider NPI grouped them. Different DOBs, different SSN. Just patients of the same doctor.'),
('Maria Rodriguez', 'SEPARATE', 0.12, 'Separated: "Brown" is extremely common. Only match was soundex + same birth year. Different months, different SSN, different states. No match.'),
('Sarah Thompson', 'SEPARATE', 0.27, 'Separated: foster care scenario. Two children at same foster home address. Same last name (foster family), different DOBs, different SSN. Distinct individuals.'),
('James Liu', 'SEPARATE', 0.14, 'Separated: "Park" vs "Pak" — Korean surname romanization variants. But DOBs differ by 20 years, SSN differ, addresses in different states. Different people.'),
('David Chen', 'SEPARATE', 0.22, 'Separated: university dormitory address match. Multiple students share building address. Name, DOB, SSN all different. Address-based matching unreliable for institutional addresses.'),
('Maria Rodriguez', 'SEPARATE', 0.16, 'Separated: military base housing caused address match. Same housing unit address, different service members. All PII differs except address.'),
('Sarah Thompson', 'SEPARATE', 0.19, 'Separated: assisted living facility grouping. Three members share facility address. Different names, DOBs, SSN. Facility address should be in exclusion list.'),
('James Liu', 'SEPARATE', 0.10, 'Separated: only match was birth year in blocking key. Names are phonetically different despite soundex grouping. All other attributes differ.'),
('David Chen', 'SEPARATE', 0.25, 'Separated: "Martinez" at same address. Mother-in-law and daughter-in-law scenario. Same last name from marriage. Different DOBs, different SSN.'),
('Maria Rodriguez', 'SEPARATE', 0.13, 'Separated: callback from previous false positive. Same pair flagged again after data refresh. Already confirmed as separate individuals. Suppression record added.'),
('Sarah Thompson', 'SEPARATE', 0.21, 'Separated: prison address match. Multiple inmates at same facility address. Name similarity is coincidental. SSN and DOB confirm different people.'),
('James Liu', 'SEPARATE', 0.17, 'Separated: adopted child has same last name as biological relative in another state. Same name, DOBs 30 years apart. SSN differ. Not a duplicate.'),
('David Chen', 'SEPARATE', 0.20, 'Separated: name truncation false positive. "Chris" matched "Christina" via nickname mapping. But different gender, different DOB, different SSN. Mapping too aggressive for this case.'),
('Maria Rodriguez', 'SEPARATE', 0.14, 'Separated: refugee resettlement scenario. Multiple family members with similar names at same resettlement agency address. Individual DOBs and SSN differ.'),

-- === ESCALATE decisions (35 notes) ===
('Maria Rodriguez', 'ESCALATE', 0.71, 'Escalated: records share DOB and address but SSN last4 differ (5519 vs 5591 — possible transposition). Name identical. Need claims history to confirm.'),
('Sarah Thompson', 'ESCALATE', 0.65, 'Escalated: conflicting SSN last4 with matching DOB and name. One from claims (2023), other from enrollment (2021). Possible SSN data entry error.'),
('David Chen', 'ESCALATE', 0.55, 'Escalated: name and DOB match but SSN is NULL in one record. Cannot confirm or deny match without SSN. Requesting source system to backfill SSN data.'),
('James Liu', 'ESCALATE', 0.60, 'Escalated: "Michael Brown" with same DOB at same address. SSN last4 differ by one digit (3456 vs 3457). Could be typo or could be coincidence. Need additional evidence.'),
('Maria Rodriguez', 'ESCALATE', 0.72, 'Escalated: all attributes match except DOB month (March vs May). Could be data entry (3 vs 5 confusion). SSN and name match strongly suggest same person but DOB discrepancy needs resolution.'),
('Sarah Thompson', 'ESCALATE', 0.58, 'Escalated: member appears in 3 different source systems with 3 slightly different name spellings. Two SSNs match, one differs. Need to determine which source is authoritative.'),
('David Chen', 'ESCALATE', 0.68, 'Escalated: possible identity theft scenario. Same SSN last4 used by two people with different names and DOBs at different addresses. Flagged for fraud investigation.'),
('James Liu', 'ESCALATE', 0.63, 'Escalated: records from two different states. Name and DOB match, SSN matches. But addresses are 2000 miles apart and both show recent activity. Could be legitimate move or could be identity sharing.'),
('Maria Rodriguez', 'ESCALATE', 0.75, 'Escalated: transgender member with name change in progress. Legal name in one system, preferred name in another. SSN and DOB match but name mismatch flags for review. Sensitive — handle per policy.'),
('Sarah Thompson', 'ESCALATE', 0.52, 'Escalated: DOB matches, address matches, but names differ significantly ("Thomas" vs "Antonio"). SSN NULL in both records. Not enough evidence to merge or separate confidently.'),
('David Chen', 'ESCALATE', 0.70, 'Escalated: records have matching SSN and DOB but one record is marked deceased and the other has recent claims. Possible death record error or identity misuse.'),
('James Liu', 'ESCALATE', 0.56, 'Escalated: similar names, same ZIP code, DOBs within 1 year. SSN last4 differ. Could be twins with close birthdays or coincidence. Need birth certificate or additional ID.'),
('Maria Rodriguez', 'ESCALATE', 0.67, 'Escalated: witness protection considerations. Record flagged by compliance. Name changed officially. SSN re-issued. Cannot process through normal matching pipeline.'),
('Sarah Thompson', 'ESCALATE', 0.61, 'Escalated: members SSN last4 matches but DOB is exactly 10 years off (1980 vs 1990). Common data entry pattern — digit transposition in year. Name and address match.'),
('David Chen', 'ESCALATE', 0.73, 'Escalated: address match confirmed via geocoding but names appear unrelated. Same building, different units — could be data entry error on unit number. SSN needed to resolve.'),
('James Liu', 'ESCALATE', 0.59, 'Escalated: one record from mental health facility. Enhanced privacy protections (42 CFR Part 2) apply. Cannot merge without explicit patient consent even if match looks strong.'),
('Maria Rodriguez', 'ESCALATE', 0.66, 'Escalated: pediatric records with parent name as guarantor. System confused parent SSN with child SSN. Need to untangle parent and child records before resolution.'),
('Sarah Thompson', 'ESCALATE', 0.54, 'Escalated: member with multiple legal name changes across years. Three records with different last names, same SSN and DOB. Need to reconstruct name history before merge.'),
('David Chen', 'ESCALATE', 0.69, 'Escalated: record from tribal health system has different identifier format. No SSN on file (tribal ID used instead). Name and DOB match non-tribal record. Cross-system identity resolution needed.'),
('James Liu', 'ESCALATE', 0.62, 'Escalated: newborn records. SSN not yet assigned. Name is temporary ("Baby Girl Martinez"). DOB matches but is very recent. Wait for permanent name and SSN assignment.'),
('Maria Rodriguez', 'ESCALATE', 0.74, 'Escalated: veteran with VA and civilian records. SSN match, name match, DOB match. But VA has service-connected conditions that must not merge into civilian record without proper flags.'),
('Sarah Thompson', 'ESCALATE', 0.57, 'Escalated: nursing home patient. Multiple records from different facilities over 10 years. Name consistent, DOB consistent, but SSN last4 shows two different values. Possible SSN change or error.'),
('David Chen', 'ESCALATE', 0.71, 'Escalated: workers comp and standard claims for same apparent member. Legal implications of merging — comp records have different liability rules. Need legal review before merge.'),
('James Liu', 'ESCALATE', 0.64, 'Escalated: member flagged by OFAC screening. Name similarity to sanctioned individual. Cannot proceed with standard merge until compliance clearance. Holding all actions.'),
('Maria Rodriguez', 'ESCALATE', 0.68, 'Escalated: Medicaid and commercial records. Same member appears to have concurrent coverage that may indicate eligibility fraud. Cannot merge until eligibility team reviews.'),
('Sarah Thompson', 'ESCALATE', 0.53, 'Escalated: records from disaster relief enrollment. Incomplete data captured during emergency. Name and partial DOB match existing member. Need to verify identity before merge.'),
('David Chen', 'ESCALATE', 0.76, 'Escalated: organ donor registry match. SSN and DOB match but one record says deceased, one active. Critical to resolve — affects organ allocation. Urgent priority.'),
('James Liu', 'ESCALATE', 0.60, 'Escalated: international member. Passport number in one system, SSN in another. Name transliteration differs. DOBs match. Need cross-reference of passport to SSN via federal records.'),
('Maria Rodriguez', 'ESCALATE', 0.65, 'Escalated: records from substance abuse treatment. 42 CFR Part 2 restrictions. Even if we are confident it is the same person, cannot merge without written patient consent. Consent form sent to provider.'),
('Sarah Thompson', 'ESCALATE', 0.58, 'Escalated: minor child records. One from school health program, one from pediatrician. No SSN in school record. Name and DOB match. Need parent verification for merge.'),
('David Chen', 'ESCALATE', 0.72, 'Escalated: possible data breach indicator. Same SSN used at two addresses simultaneously with different names. Could be identity theft or could be name change in progress. Security team notified.'),
('James Liu', 'ESCALATE', 0.55, 'Escalated: homeless member with shelter address. Same name appears at multiple shelters. DOBs match. No SSN. Need outreach worker confirmation to avoid creating false golden record.'),
('Maria Rodriguez', 'ESCALATE', 0.69, 'Escalated: pre-ACA and post-ACA records. Same member enrolled under maiden name pre-2014 and married name post-2014. SSN matches but name linkage needs documentation.'),
('Sarah Thompson', 'ESCALATE', 0.63, 'Escalated: dual-eligible member (Medicare + Medicaid). Records in both systems with slightly different data. CMS requires specific reconciliation process. Cannot use standard merge.'),
('David Chen', 'ESCALATE', 0.70, 'Escalated: clinical trial participant. Research consent limits data merging. IRB protocol restricts combining clinical trial data with standard health records. Need research coordinator approval.');

-- ============================================================
-- STEP 3: Verify
-- ============================================================
SELECT action, COUNT(*) AS note_count
FROM staging.steward_notes
GROUP BY action
ORDER BY action;

SELECT COUNT(*) AS total_notes FROM staging.steward_notes;

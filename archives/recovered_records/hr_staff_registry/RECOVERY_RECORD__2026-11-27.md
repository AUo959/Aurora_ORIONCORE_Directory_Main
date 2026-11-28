# Recovery Record: HR Team Profiles and GUMAS Staff Registry SSOT

Date: 2026-11-27
Lane decision (owner, 2026-11-27): commit the two local-only HR/staffing records
so they survive outside the git-ignored `archives/` tree. This uses a new
`archives/recovered_records/` lane, which mirrors `archives/recovered_prototypes/`
for data records rather than code.
Executed by: Claude Code, owner-directed (project thread "HR system for L1 Orion Station")
Companion research: the Orion Station HR inventory of 2026-11-27, which mapped every
HR piece across CanonRec, CloudBank and ORIONCORE and found these two files were the only
holders of their content.

## Status

**Not canon.** Both files are recovered source material. Per `AGENTS.md`
("root archive, intake, staging, or recovered material is not canonical by
default"), anything in them reaches canon only through the CanonRec
reconciliation workflow (conflict scan + certainty advisor).

The bytes are preserved exactly as they were found. Nothing was edited, normalized or re-encoded.

## What these are

### `HR_Team_Modular_Profiles.json` (April 2025)

The four-person HR team as first defined in the GUMAS "Deliverables Bundle Step 2":
Helena Vu (HR Director), Tomas Erien (Organizational Architect), Marla Osei
(Onboarding & Cultural Immersion Specialist), Lior Venn (Interpersonal Systems
Mediator).

It is the **only** source in the corpus that holds the following. CloudBank's
`modules/hr/aurora_hr_module_advanced_v3.py` hard-codes the names and titles, but none of these fields:

- per-member clearance codes: `HR-Prime`, `HR-Core`, `HR-Onboard`, `HR-Mediator`
- reporting lines (Vu → Alex Thorne; the other three → Vu)
- core functions (staff forecasting, team topology modeling, staff ritual
  onboarding, mediation grid activation, and others)
- linked modules (Culture Charter, Onboarding Framework, OrgMap Toolset,
  Mediation Logic Core, Terminal Welcome Shells, and others)

Framing note: this bundle describes HR on the GUMAS real-world / dev-team
layer. Helena Vu is canon L1 (`ORION.ENTITY.0016`, HR_001). Erien, Osei and Venn
are **not** in CanonRec. Whether they are L1 station crew is a reconciliation
question, not something this record decides.

### `AURORA_GUMAS_STAFF_REGISTRY_SSOT__v0.2.0__2026-03-14__STRUCTURED_ARCHIVE.zip` (March 2026)

An offline structured-archive build that turned the earlier staff catalog
(v0.1.0) into a **staff-registry single-source-of-truth candidate** for 27
GUMAS staff. Self-reported confidence split: 14 high, 8 medium, 5 low.
Contents (41 files):

- `data/aurora_gumas_staff_registry_ssot.v1.json` / `.csv`: the per-person registry, each value carrying source receipts and alternate observations
- `profiles/*.md`: 27 evidence-backed profiles
- `reports/conflict_resolution_matrix.*`, `reports/staff_profile_gaps.*`, `reports/ssot_resolution_log.md`: field-level conflict outcomes, missing-field inventory, deterministic resolution rules
- `governance/ADR_LITE.md`: backbone decision (Staff Tracker v2.2.5 as roster, PAT registry as overlay)
- audit spine: `RUN_LOCK.json`, `BUILD_RECEIPT.json`, `bundle.manifest.json`, `audit/EVIDENCE_MAP.json`, `audit/GATE_LOG.json`

Its own resolution log states that missing fields remain null and that "no synthetic biographies or anchors were invented". That is consistent with the
L1 staffing runtime's no-invention rule (CloudBank `docs/architecture/AURORA_L1_RUNTIME_CONTRACT.md`).

The zip is committed as-is (49,024 bytes) rather than unpacked, so the
archive's own `bundle.manifest.json` stays verifiable against the original
container.

## Provenance

| Artifact | Committed path | Local source (git-ignored, left in place) | SHA-256 |
|---|---|---|---|
| HR team profiles | `archives/recovered_records/hr_staff_registry/HR_Team_Modular_Profiles.json` | `archives/unzipped/Complete Archive 4_19 copy/GUMAS_Deliverables_Bundle_Step2/HR_Team_Modular_Profiles.json` (mtime 2025-04-02) | `aad60d58b4e9033b9062dec3d9202bdf6f70b994865c5d403aceac63f6852de5` |
| Staff registry SSOT | `archives/recovered_records/hr_staff_registry/AURORA_GUMAS_STAFF_REGISTRY_SSOT__v0.2.0__2026-03-14__STRUCTURED_ARCHIVE.zip` | `archives/structured_archives/AURORA_GUMAS_STAFF_REGISTRY_SSOT__v0.2.0__2026-03-14__STRUCTURED_ARCHIVE.zip` (mtime 2026-03-14) | `df829a37f8774e15edba8b585d4eb23f1a3ee1b66ced48eaf3cdfee325ff0de6` |

Inner data hashes, inside the zip:

- `data/aurora_gumas_staff_registry_ssot.v1.json`: `7cc1768df5204ecfc48557a689027382ce60bf3fb937b13600428c9008a86e54`
- `data/aurora_gumas_staff_registry_ssot.v1.csv`: `0cd2f2c8924a0063fdf9a41ffea7ad816d34f79cde6d35717bec3d13859e197b`

`HR_Team_Modular_Profiles.json` appears once locally. Its companion
`HR_Department_Home_Node.json` (958 bytes, the HR mission and routing node) exists in two
local copies and was **not** included in this recovery.

The predecessor `AURORA_GUMAS_STAFF_REGISTRY_CATALOG__v0.1.0__2026-03-14__STRUCTURED_ARCHIVE.zip`
(RUN_LOCK input hash `3d4c9fc7…`) also remains local-only and was not included.

## Public-repo screening

This repository is public, so both files were screened before commit for
email addresses, phone numbers, government-ID patterns, API keys and tokens
(`sk-`, `ghp_`, `AKIA`, bearer/secret/password strings), and local filesystem
paths (`/Users/…`, iCloud paths). **No matches.**

The only paths present are `/mnt/data/…` input paths in the zip's `RUN_LOCK.json`, which are generic sandbox locations. All named people are fictional Aurora/GUMAS staff.

## Verification

```bash
cd archives/recovered_records/hr_staff_registry
shasum -a 256 -c MANIFEST_SHA256.txt
```

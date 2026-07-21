# Canon Reconciliation Report — Marshals Archive Mining
**Date:** 2026-07-20
**WORKFLOW STATE: SUPERSEDED BY OWNER RESOLUTION — see "Final Disposition" at end of file.
The body below is the pre-decision snapshot, retained verbatim for audit. The
post-decision record of truth is `claim_ledger.json` (resolution_pass + workflow_state).**
**Input:** `_staging/marshals_archive_mining__2026-07-20/marshals_excerpts_curated.md` (April-2025 raw-archive excerpts)
**Layer:** L2 (no cross-layer contamination detected; all content is GUMAS-galactic)
**Entities/claims processed:** 7 claim groups
**Tooling:** aurora-canon-reconciler v1.1 validator + ReconciliationAdvisor (HDE++)

## Validation Summary

| # | Claim group | Kind | Validator | Advisor rec. (conf) | Applied tag |
|---|---|---|---|---|---|
| 1 | Union Marshals governance/oversight model | mechanic (governance) | PASS, clean | STAGING (0.12) | **STAGING** |
| 2 | Union Marshals jurisdiction/mandate enrichment | polity attribute | PASS, clean | STAGING (0.12) | **STAGING** |
| 3 | Zylox–Durn Pact (Sentinel program + Academy origin) | timeline_event | PASS | STAGING (0.08) | **UNCONFIRMED** (unresolved role conflicts) |
| 4 | G.U.S. Judicator Prime spec enrichment | ship attribute | PASS | STAGING (0.12) | **STAGING** (one term held back, see C3) |
| 5 | Sentinel-Class Hunter Vessel | new ship class | PASS, 1 WARN (MOVING_ENTITY_NO_RULE) | STAGING (0.12) | **UNCONFIRMED** (taxonomy conflict) |
| 6 | Espionage/doctrine strings | mechanic (military) | PASS, clean | STAGING | **STAGING** |
| 7 | Velar Marshal-Council System (Lord Marshal origin) | polity attribute (Velar) | PASS, clean | STAGING (0.12) | **STAGING** |

Note: advisor confidence is uniformly low because claims are enrichments of already-CANON
entities rather than standalone entities; per skill decision logic, conflicted items were
manually demoted from the advisor's STAGING to UNCONFIRMED.

## Conflicts Found

**C1 — Marshals leadership (Zylox–Durn Pact).**
Draft (Mar-2025): General Kael Durn is "Director of the Galactic Marshals" (alias "The Iron
Sentinel"). Canon (locked 2026-03-20): Chief Marshal **Vael Saros** leads the Union Marshals;
**Durn** is Supreme Military Commander, GU Armed Forces. Primacy: canon.
Proposed resolution (synthesis, Option C): retcon the pact as a **prior era** — Durn led the
Marshals as "Director" before ascending to Supreme Military Commander; the office was later
retitled "Chief Marshal" and passed to Saros. Preserves both sources; explains Durn's canon
trait "Strengthened Sentinel Deployment" and alias "The Iron Sentinel". PENDING user decision.

**C2 — Chancellor surname.** Draft: "High Chancellor Zylox **Verrin**". Canon: "Chancellor
Zylox **Rhaegos**". Primacy: canon. Resolution: defer to canon; record "Verrin" as
superseded early-draft surname (optionally as in-world alias). No promotion.

**C3 — Judicator Prime class naming.** Draft: "Supercarrier-Class Flagship". Canon:
`class_id: CLASS-JUDICATOR-01`, `narrative_significance: flagship`, CO **Alric Tann**
(Marshal-Captain Elias Drayen separately CANON with ship_assignment Judicator Prime — no
conflict, CO vs embarked Marshal officer). Resolution: promote crew size (12,000, tag APPROX),
"command ship for Marshal-led strike forces", and "hosts a full Sentinel-class strike unit"
as attributes; hold "Supercarrier-Class" as descriptive gloss of CLASS-JUDICATOR-01, not a
class rename.

**C4 — Sentinel-Class Hunter Vessel.** Not in the canonical 6-class Marshal fleet table;
role (covert ops, stealth, cyber) overlaps Phantom-Class Stealth Frigate; worsens the known
"Sentinel-Class" suit-vs-carrier taxonomy collision (ledger Open Question #2). Options:
(a) alias/early name of Phantom-Class — defer to canon; (b) admit as a seventh, classified
class. PENDING user decision.

**C5 — Ghost governance entities.** Draft references **Judicial Council** and **Galactic
Senate**; promoted orgs include **Union Senate** (treat "Galactic Senate" as alias) but **no
Judicial Council** exists in canon. Also draft "Galactic Security Bureau (GSB)" vs canon
**Union Intelligence Bureau (UIB)** — likely the same conceptual slot, name superseded.
Resolution: promote the oversight mechanic with "Judicial Council" marked UNCONFIRMED-entity,
or create org_judicial_council at STAGING. PENDING user decision.

## Drift Artifacts

- Naming drift confirmed benign: "Galactic Marshals" (2025 archives) → "Union Marshals"
  (canon, alias registered); "Marshalls" double-L appears only in 2026 prose, never in data.
- Early-draft political cast (Varnak, Threxia, Mek'thor, Trade Coalition/Defense Bloc/Green
  Accord/AI Vanguard factions) and agencies (GSB, CSD, TSF, Sheriff Garrisons, SOCOM) are
  superseded worldbuilding — not routed for promotion; retained in curated excerpts as
  source-of-record.

## Promotion Assessment

Ready for CANON_PROMOTE **on your approval** (no unresolved conflicts):
1. Union Marshals jurisdiction/mandate enrichment (claims CL-02a…d)
2. Marshals oversight mechanic (CL-01) — contingent on C5 decision re: Judicial Council
3. Judicator Prime attribute enrichment minus class rename (CL-04a…c)
4. Espionage/doctrine strings (CL-06)
5. Velar Marshal-Council System note (CL-07)

Hold (decision required): Zylox–Durn Pact (C1), Sentinel-Class Hunter Vessel (C4).

## Action Items

1. Decide C1: adopt Option C retcon (Durn as prior Director) — or hold pact at UNCONFIRMED.
2. Decide C4: Hunter Vessel = Phantom-Class alias (a) or new classified class (b).
3. Decide C5: create `org_judicial_council` at STAGING, or strip the Judicial Council
   reference from the oversight mechanic before promotion.
4. Approve/deny the five CANON_PROMOTE candidates above.
5. On approval: apply updates via canon files + append drift entries to
   `GUMAS_SIM_2.5/CanonRec/DRIFT_LOG.md`, then commit (commit = CANON per protocol).

---

# Final Disposition — 2026-07-20 (owner resolution; supersedes action items above)

All four decisions taken by owner via review session:

| Item | Decision | Applied |
|---|---|---|
| C1 Zylox–Durn Pact | Option C retcon: Durn as prior "Director of the Galactic Marshals"; office retitled Chief Marshal; Saros succeeded | Addendum LEDGER-MARSHALS-0005 |
| C4 Hunter Vessel | Early alias of Phantom-Class Stealth Frigate; fleet stays 6 classes | Marshal_Starship_Classes.csv + addendum |
| C5 Judicial Council | org_judicial_council created at STAGING | canon/L2/entities/organizations/ |
| Promotion | All five conflict-free groups approved CANON_PROMOTE and applied to canon files | org_union_marshals.json, vessel_gu_001.json, addendum, CSV |

CanonRec DRIFT_LOG.md carries the RESOLVED entries; the staged `DRIFT_LOG_entries.md` in this
folder was the pre-decision draft and has been updated to match. Temporal ordering of this
package: RECONCILIATION_REPORT body → owner decisions → claim_ledger resolution_pass →
canon file application → CanonRec commit (SHA recorded in claim_ledger.json workflow_state).

**Second pass (same date, post-resolution):** charter-detail review added
LEDGER-CHARTER-0001…0004 (override trigger, immunity scope, Judicial Council design, Durn
chronology — all charter-pending, UNCONFIRMED except noted bounds), LEDGER-DRIFT-NOTE
(LEGEND_CONTESTED chancellor-oversight contradiction; "Marshalls" misspelling traced to
Mar-2025 sources, 45 instances), and LEDGER-SENTINEL-0004 (Sentinel High Command / Grand
Marshal; Diplomatic-Class Sentinel — both UNCONFIRMED, owner ruling needed). Claims
CL-08…CL-13.

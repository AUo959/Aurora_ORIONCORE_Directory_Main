# L2 Canon Corpus Audit — 2026-07-21

Full audit of CanonRec `canon/L2/` against everything locally available (workspace sources,
session archives, nested repos) — the Marshals-domain methodology applied corpus-wide.
Companion staging package: `_staging/marshals_archive_mining__2026-07-20/` (Marshals precedent).

## Scope examined

- **CanonRec L2:** 64 top-level entities (316 entity files incl. capsules), 10 domains
  (entities, factions, map, marshals_sentinels, mechanics, operations, primary_sources,
  social_dynamics, timeline, world_bible).
- **Local sources:** 550 files across `projects/GUMAS_SIM_2.0`, `GUMAS_Legacy`,
  `_staging/recovered_textAu__2026-03-13`, `projects/Perplexity_Research`.
- **Session archives:** all 12 `archives/session_archives/*` dirs.
- **Nested/registered repos:** DuelSim_v2.0, qgia-knowledge-library, qgia-knowledge-spine,
  aurora-cloudbank-symbolic, CanonRec (remote-only zip_wizard not locally inspectable).

## Findings & dispositions

| # | Finding | Severity | Disposition |
|---|---|---|---|
| 1 | **Raw-archive coverage complete.** AU_Archive_323_326 exports = exact duplicates (0 new conversations) of the mined 87; Au_Archive_62_619 "export" is a github-collab demo zip (false positive). | INFO | CLOSED — no unmined conversation corpus remains anywhere in the workspace. |
| 2 | Certainty census: 60/64 CANON; `vessel_gu_013/014` carried **invalid tag `STAGING_CONFIRMED`** (outside approved set). | WARN | FIXED — normalized to STAGING with audit note; no evidence change. |
| 3 | `Xelvani-3`, `Torix-7` carry tag `SUPERSEDED` — also outside the approved set, but intentional disambiguation records. | INFO | FLAGGED for owner: either admit SUPERSEDED to the tag vocabulary or re-tag; content untouched. |
| 4 | **7 faction substructures had no entity record**: Union Intelligence, Sentinels (alias gaps); Diplomatic Corps, Hardliner Warlords, Imperial Loyalists, Republican Reformists, Outer Colony Warlords (missing orgs). | WARN | FIXED — aliases registered on org_union_intelligence_bureau + org_sentinel_high_command; 5 new orgs created at **STAGING** from the canonical factions file. |
| 5 | Provenance: every canon entity has source-corpus mentions except org_judicial_council + org_sentinel_high_command (provenance = session archives; documented in their source_refs). | INFO | Acceptable — archive-derived provenance recorded. |
| 6 | Mechanics registry: 20 MECH ids, implementation markers present (incl. MECH-GOV-001 via `tools/mech_gov_001.py`). | INFO | Healthy; no action. |
| 7 | Cross-repo: DuelSim/qgia repos contain **zero** L2 references; aurora-cloudbank-symbolic has 4 L2-referencing files. | INFO | Low priority — queue item for a cloudbank consistency skim. |
| 8 | World Bible heading cross-check produced only title-prefix alias mismatches (e.g. "Chancellor Zylox" vs "Zylox Rhaegos") — no substantive gaps. | INFO | Optional alias-enrichment pass queued. |

## Marshals-domain precedent (already complete)

Repo survey → archive mining → reconciliation → owner rulings → engine-derived charter →
promotion → closeout: zero open holds (CanonRec commits 744e3a06 → e62875b).

## Go-forward reconciliation queue (owner rulings needed)

1. **Promote or hold the 5 new STAGING orgs** (Diplomatic Corps + Velar/AI-Warlord
   internal factions) — mining detail exists in the already-extracted archive threads
   (Velar internal-faction profiles were captured during the Marshals pass).
2. **SUPERSEDED tag ruling** (finding 3).
3. **Velar Imperium domain pass** — the archives hold full Tal'Varen-era internal-faction
   profiles (divide-and-rule doctrine, Marshal-Council lineage) not yet reconciled beyond
   the Marshals-adjacent excerpts; same mining→reconcile→rule→promote arc as Marshals.
4. **AI Warlords / Prime Construct domain pass** — subfaction structure now staged;
   doctrine/threat material in ledger + engine scenarios to reconcile.
5. **Alias-enrichment pass** (title-prefixed alias registration across characters).
6. **Cloudbank consistency skim** (4 files).
7. Optional: engine-derived charters for other GU organs (UIB, OSD, Senate procedures)
   using the Marshal Charter methodology.

## Verdict

L2 canon is **structurally sound**: no contradictions found between canon and any local
source; all raw archives mined or duplicate-verified; certainty hygiene restored; the only
substantive gaps were unrecorded faction substructures, now staged. Remaining work is
domain-deepening (queue above), not repair.

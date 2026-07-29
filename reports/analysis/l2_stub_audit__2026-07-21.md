# L2 Canon Stub Audit — 2026-07-21

**Method:** deterministic thinness scorer over all canon L2 entity records — flags any record
whose longest descriptive field (`notes`/`description`/`nature`/`role`/`promotion_note`/etc.)
is under 40 characters. These are *present* records a presence-check passes but which are
hollow (Kaelor's Rift was the exemplar). **16 stubs found**, in three categories.

## Category A — Enriched this pass (safe, unowned original canon)

- **`loc_marshal_academy`** — was a bare stub; back-filled from the Marshals & Sentinel Ledger
  (Sentinel-operator training/selection pipeline on the capital planet). Additive, no invention.
- **`loc_kaelor_s_rift`** — enriched in the prior pass (FTL-disruption anomaly + Battle of
  Kaelor's Rift event scar).

## Category B — Owner active-arc records (NOT touched; flagged for owner)

Seven stubs belong to your **Dark Star / Third Silence arc**. Their detail already exists in
**committed canon** — `canon/L2/narratives/GUMAS_L2__NARRATIVE__DARK_STAR_ARC_UNIFIED__v1.1`,
the AAR `canon/L2/reports/GUMAS_L2__AAR__DARK_STAR_INCIDENT_TO_CHANCELLOR__v1.0`, and the hub
record `event_dark_star_incident_4718_224` (which cross-links all of them). The entity records
just never had that detail back-filled into their `description`/`doc_sources`/`event_refs`.

| Record | Kind | Detail source (committed canon) |
|---|---|---|
| `place_lethan_system` | place | Narrative + event — Battle of Lethan; Dark Star derelict quarantine site |
| `place_kallis_foundry` | place | Narrative — criminal infrastructure; removed Union Dark Star records |
| `place_kharis_sector` | place | Event `location_refs` — sector containing Lethan + Kallis |
| `artifact_third_silence` | equipment | Narrative Ch.03 — artifact in hardened joint-custody containment |
| `fleet_shadow_fleet` | organization | Narrative — hidden fleet through Kharis; withdrew from Crown Dark |
| `vessel_shadow_001` (Crown Dark) | mobile_asset | Narrative — Shadow Fleet command vessel; counterwarfare |
| `vessel_unknown_dark_star_001` (Dark Star Vessel) | mobile_asset | Narrative + event — the central derelict; artifact origin |

**Not modified by me** — these are your active work, and additive reconciliation is a
one-command back-fill (description + `doc_sources` + `event_refs` from the sources above) that
I prepared and reverted, available on your say-so. They are also grandfathered against the
naming gate (they predate it), so they don't block CI.

## Category C — Thin-as-source (no action possible without invention)

Eight registry vessels — `vessel_gu_002`, `003`, `004`, `005`, `007`, `008`, `010`, `012` —
are thin because the Ship Registry v1.0 only ever gave them a name, class, and allegiance
("Example vessel for X-Class; CO TBD"). Only the Judicator Prime and Nemesis Prime carried
full specs in the source. Enriching these would be invention, so they stay as-is; they already
carry a `class_entity_id` link to their (fully-detailed) class record.

## Recommendation

Category A is done. Category B is a clean additive back-fill from your own committed narrative —
say the word and I'll apply it (or you do it as part of the arc). Category C is correctly
thin — the source has no more to give.

The scorer (`grep`-able thinness scan) can be re-run any time to catch future stubs.

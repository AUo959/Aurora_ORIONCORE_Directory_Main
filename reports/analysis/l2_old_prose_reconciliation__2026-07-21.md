# Canon Reconciliation Report — Old-Prose Sweep

**Date:** 2026-07-21
**Input:** Early unstructured GUMAS prose — primarily `archives/unzipped/ZIP_Archives/AU_Archive_330only/GUMAS_Extracted_Simulation_Modules.txt` (32k-line early simulation-modules dump), plus conversation exports, meta-narrative, and OG GUMAS originals.
**Layer:** L2
**Process:** `aurora-canon-reconciler` — conflict scan (name/alias collision + structural reference check) against the full committed canon name index, then `ReconciliationAdvisor` scoring.
**Entities processed:** 4 recovered + coverage confirmation of prior-landed entities.

## Governing rule (owner directive)

> Discovered prose detail that does **not conflict** with canon **is** canon. It must be checked against canon (there is a process); non-conflicting discovered detail is not held at STAGING pending a separate gate — the conflict-clean check *is* the gate.

## Validation & conflict scan

| Entity | Type | Name collision | Alias collision | Missing refs | Fabric linter | Advisor tag |
|---|---|---|---|---|---|---|
| Kaelor Prime (`loc_kaelor_prime`) | location | none | none | none | clean | LOCKED_POSITION |
| Orbitfall Station (`loc_orbitfall_station`) | location | none | none | none | clean | LOCKED_POSITION |
| Xarlok Empire (`polity_xarlok_empire`) | polity | none | none | none | clean | CANON_PROMOTE |
| Sira Velkonn (`char_sira_velkonn`) | character | none | none | none | clean | CANON_PROMOTE |

All four passed the conflict scan CLEAN. Per the governing rule, all four are promoted to **CANON** on this commit.

## Conflicts found

None. (No `DRIFT_LOG` entry required.)

## Promotion assessment

- **Xarlok Empire** — external militant/expansionist empire challenging Union borders; recovered attributes are non-conflicting → CANON. Species-vs-state ambiguity noted; not fabricated.
- **Sira Velkonn** — Velar Imperial pro-monarchy figure; the established rival pole against whom the *already-canon* Thalen Rynn was defined → CANON. Generative "could become / perhaps" backstory in source was **excluded** (not canon — it never happened in committed material), and is listed under the record's `undetermined` field.
- **Kaelor Prime** / **Orbitfall Station** — entity **attributes** are non-conflicting discovered detail → CANON. The only deferred element is the absolute **map coordinate**: neither has a Location Authority Table row, so placement is routed to the map-authority / Reconciliation Workflow §4.5 process via a placement-claim ledger (`canon/L2/map/PLACEMENT_CLAIMS__old_prose_2026-07-21.json`). `canonical_position_status: unplaced` is a placement fact, not a certainty hedge — the records are canon and usable while unplaced. Kaelor Prime is held explicitly distinct from the canon `loc_kaelor_s_rift` anomaly.

## Coverage confirmation (checked, already canon — not gaps)

Xyphos Prime (`loc_xyphos_prime_ruins`), the Hollow Expanse (`loc_hollow_expanse`), Veil Nebula (`loc_veil_nebula`); Thalen Rynn, Syrr Velkonn, Talyx Velkonn; the 21 engine leaders.

## Correctly excluded (out of L2 scope)

The GUMAS Research **L1 Staff Roster** (Alex Thorne, Amelia Rivers, the CODEX dev-team personas) — L1, owner-excluded. Real-world governance analogies the sim uses as reference (Roman/Persian/Gupta Empires, US Constitution/Senate, Mayflower Compact).

## Action items

1. Map-authority process to resolve Kaelor Prime + Orbitfall Station coordinates from the placement-claim ledger when adjacency evidence is available.

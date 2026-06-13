# L2 Galactic Canon — Promotion Receipt

**Date:** 2026-06-13 | **Owner ruling:** "all L2 entities should be promoted …
significant Galaxy building … map outlines, locations, narratives like the
Marshalls and the sentinel suits."

## What was promoted

A new canonical home, `CanonRec canon/L2/` (mirrors `canon/L1/`), now holds the
full **structured** GUMAS galactic-simulation corpus — ~296 files, content
verbatim, promoted from the self-declared "Secondary Canon" status the source
material was written to reach:

- **entities/** (261) — the March L2 pass: characters, **23 locations**
  (Blackreach Station, Vel-Surak megacity, Xyphos Prime Ruins, Veil Nebula…),
  **12 organizations** (Union Marshals, Union Senate, Office of Strategic
  Diplomacy, The Black Hand, Union Intelligence Bureau…), **16 mobile_assets**,
  + CANON_LOCK_RECORD + DISAMBIGUATION_RECEIPT.
- **world_bible/** — GUMAS L2 World Bible v0.2 (lore).
- **map/** — Location Authority Table + the galactic **map source of truth** +
  the Physical Galaxy Packet v0.1 (the map outlines).
- **marshals_sentinels/** — the **Galactic Marshals** + **Sentinel-Class Power
  Suit** (6 variants: Praetor, Striker, Warden, Vanguard, Phantom, Stalker):
  the 28KB source-linked ledger, 8 hardware tables (Marshal/enemy starship
  classes + capabilities, defensive, shielding/propulsion, ship-to-ship combat,
  vehicles), and the Marshal Standard Kit.
- **operations/** (12) — **Operation Obsidian Dawn** (briefing/execution/
  conflict/outcome), the Excision Task Force mandate, Director Varek Norr,
  Chancellor Zylox's diplomatic-offensive strategy.
- **mechanics/** — the L2 Mechanic Registry (MECH-GOV-001 …) + polity/ship/
  character dossiers + mechanics-and-models.
- **primary_sources/** — The Lanternline (in-world newsletter, cycle 38).

## Provenance and lineage

Source corpus was scattered: `SIM_ENGINE_OUTPUTS/L2_CANON__2026-03-19/`,
`projects/GUMAS_SIM_2.0/03_SIMULATION/` (locations, Marshals/Sentinels, mission
logs), `GUMAS_Legacy/Original_Materials/GUMAS_OG/` (map SoT + galaxy packet),
`_staging/recovered_textAu__2026-03-13/L2/` (mechanics), and project files
(Lanternline). The L2 layer traces to early-2025 conversation exports — among
the oldest project material — reworked six times (see
`l2_lineage_genesis__2026-06-13.md`). CanonRec `54e34e8`; registry pinned.

## Open items (logged)

1. **MECH-GOV-001 is design, not code** — memory-driven faction decisions
   (Q-learning + retrieval of past betrayals/negotiations) specified at genesis
   and in the registry, never implemented; the engine uses simpler formulas.
   Realizing it is the headline engine-fidelity opportunity.
2. **Raw 2025 archive corpus** — April-2025 session-archive zips (`chat.zip`,
   `conversations.zip`, GUMAS dev kits) hold further Marshals/galaxy material
   not yet extracted. This promotion covers the structured corpus; the raw
   archives await a future mining pass.
3. **No L2 entity ledger** yet (L1 has Entity Ledger v2) — a future generation
   pass over `canon/L2/entities/`.
4. **World Bible vs. map** — where they disagree on placement, the map is
   source of truth (per the World Bible's own migration hooks).

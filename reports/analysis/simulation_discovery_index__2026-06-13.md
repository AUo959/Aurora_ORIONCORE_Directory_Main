# Simulation Discovery Index — Orion Station / GUMAS / Sim

**Date:** 2026-06-13 | **Purpose:** authoritative inventory of all existing
Orion Station, GUMAS, and simulation work across the iCloud control plane and
GitHub, so we extend rather than reinvent. Supersedes the partial
`GUMAS_SIM_2.5/SYSTEM_MAP.md` (2026-03-01) for sim scope.

## TL;DR — what already exists (do not rebuild)

1. **A validated GUMAS v2.0 engine** — 14 modules, ~9,833 LOC, 15-phase tick,
   13-faction / 28-leader / 20-node galaxy. Production-validated.
2. **A v3.0 FORGE extension** — phases 16–20 (population, technology,
   negotiation, intelligence, rebellion) + CharForge + L2 phase-2 + validator.
3. **`engine_advanced.py`** — the synthesized engine that fuses v2.0 base +
   v3.0 FORGE; this is what my powered/live watches already drive.
4. **Three existing engine driver tools** — see "Don't reinvent" below; my
   watch tooling overlaps with `hourly_retrospective.py` and `gumas_api.py`.
5. **A real 122-turn run with lessons learned** (seed 42) — the galaxy
   destabilized; the design critique already exists.
6. **L2 galactic canon** — ~30 promoted entities (the galaxy the engine runs).
7. **Recovered simulation-design drafts** — the L2 math framework, state
   variables, non-war progression mechanics, memory model — not yet integrated.

## 1. Simulation engines (code)

| Location | What | Status |
|---|---|---|
| `GUMAS_SIM_2.5/SIM_ENGINE_OUTPUTS/` | GUMAS v2.0 core: `engine.py` (1,905 LOC, 15-phase), `engine_base.py`, `models.py` (991), `formulas.py` (28 pure fns), `scenarios.py` (13 factions/28 leaders), `topology.py` (20-node), `combat.py`, `crisis_escalation.py` | VALIDATED (PK-02) |
| `GUMAS_SIM_2.5/SIM_ENGINE_OUTPUTS/engine_advanced.py` | Synthesized v2.0+v3.0 engine (`GUMASAdvancedEngine`) — **the engine my watches drive** | active |
| `GUMAS_SIM_2.5/FORGE__GUMAS_v3.0__2026-02-19/` | v3.0 modules: `population.py`, `technology.py`, `negotiation.py`, `intelligence.py`, `rebellion.py`, `charforge.py`, `l2_phase2.py`, `l2_state.py`, `engine_v3_patch.py`, `validate_v3.py`, `models_v3_ext.py` | active |
| `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/simulation/` | L1 station sim: `orion_station_simulation_v2.py` (the watch harness), `_v1`, `triplex_handshake_simulation.py`, `character_loader.py` | active (in use) |
| `GUMAS_SIM_2.5/SIM_ENGINE_OUTPUTS_SEED99/` | Seed-99 run variant of the v2.0 engine | archival run |
| `GUMAS_SIM_2.5/DuelSim/` + repo `DuelSim_v2.0` | Separate combat/arena sim track (own GitHub repo) | parallel track |
| `GUMAS_SIM_2.5/Aurora_Sim_Architecture/{autonomic_correction_engine,working_group_engine,TaggingEngineV2_Oppy}.py` | Standalone Aurora-side engines | uncatalogued — review |

## 2. Don't reinvent — existing engine driver/query tools

These already exist and overlap with the watch tooling I have been building:

| Tool | What it does | Relationship to my work |
|---|---|---|
| `tools/gumas_api.py` | **FastAPI server** exposing the v3.0 engine as REST: scenario runs, step execution, **event injection**, state queries | My watches drive the engine in-process; this exposes it as a service. Complementary — a future live link could call this instead of embedding. |
| `tools/gumas_l2_query.py` | Query additive L2 state from a live engine init or exported snapshot | Directly useful for reading engine state without a full run. |
| `SIM_ENGINE_OUTPUTS/hourly_retrospective.py` | **Advance the integrated sim one turn + write a retrospective** with evidence | **Closest overlap** to powered/live watch's per-hour engine stepping + retrospective. My watches add the L1 chassis coupling + mesh; this is the pure-L2 retrospective. Reconcile before building more turn-stepping. |
| `skills/gumas-simulation-engine/scripts/run_gumas_advanced.py` | Skill runner for advanced engine turns | the skill I invoked for the L2 join |
| `tools/aurora_recommendation_engine.py` | Recommendation engine (control-plane) | adjacent |

**Recommendation:** before extending watch turn-stepping, read
`hourly_retrospective.py` and `gumas_api.py` — adopt their event-injection
and retrospective patterns rather than reimplementing.

## 3. Major prior simulation runs (the empirical record)

- **Seed 42, turns 1–122** (`LESSONS_LEARNED__SIM_RUN_SEED42_T001_T122__2026-05-21.md`):
  closed at stability 0.358 (threshold 0.480), risk 0.651 (threshold 0.540),
  4 civil wars, 4,378 ledger records. **The galaxy ran away into instability —
  the lessons-learned doc is the design critique for why.** Read before tuning
  engine dynamics; my watches show the same downward stability trend in
  miniature.
- **Seed 99** (`SIM_ENGINE_OUTPUTS_SEED99/`) + `SEED_COMPARISON_REPORT.md` —
  cross-seed comparison already done.
- `advanced_event_ledger.ndjson`, `advanced_skill_output.json`,
  `hourly_retrospectives/` — prior run artifacts; the ledger is the same
  event-atom shape the station chronicle adopted.

## 4. GUMAS L2 galactic canon (the payload's content)

- `SIM_ENGINE_OUTPUTS/L2_CANON__2026-03-19/` — ~30 promoted L2 entities:
  characters (adrienne_kovas, aelindra_voss_aurai, lyra_voss, malrik_voska,
  nemesis_core…), `locations/`, `organizations/`, `mobile_assets/`, plus
  `CANON_LOCK_RECORD` + `DISAMBIGUATION_RECEIPT`. The galaxy the engine runs.
- L2 promotion bundles: `L2_CHARACTER_PROMOTIONS`, `L2_LOCATION_PROMOTIONS`,
  `L2_ORGANIZATION_PROMOTIONS`, `L2_ENTITY_PROMOTION_BUNDLE`,
  `L2_FULL_PROMOTION_RECEIPT__20260320.json`, `L2_CRISIS_ASSESSMENT_latest.json`.
- `L2_CANON_RECONCILIATION_REPORT__v1.0__2026-03-19.md` + `DRIFT_LOG__L2_Canon_Pass`.

**Gap:** L2 galactic canon lives in SIM_ENGINE_OUTPUTS, NOT in CanonRec. L1
station canon is in CanonRec; L2 galaxy canon is not yet routed there. Candidate
for a CanonRec `canon/L2/` home (owner decision).

## 5. Recovered simulation-design drafts (high-value, unintegrated)

`GUMAS_SIM_2.5/draft_logic/recovered/`:
- `galactic_union_simulation_math_framework.md`, `galactic_union_state_variables.md`,
  `early_simulation_formulas.md` — the L2 math (compare to `formulas.py`)
- `non_war_progression_mechanics.md` — peacetime dynamics (addresses the seed-42
  runaway-conflict problem directly)
- `simulation_expansion_systems_outline.md`, `simulation_mechanics_export_implementation_plan.md`
- `simulation_memory_storage_update.md`, `galactic_union_memory_optimization_plan.md`,
  `immersive_directive_protocol_spec.md`

`GUMAS_SIM_2.5/draft_worldbuilding/recovered/`:
- `factions_registry_draft.yaml`, `galactic_union_character_registry.md`,
  `zylox_and_union_command_character_profiles.md` — L2 cast
- `aurora_shuttlecraft_registry.md` — station/fleet assets (L1-adjacent)
- `aurora_framework_capsule_grafts.yaml`, `halo_continuity_graft_005.yaml`,
  `threadcore_symbolic_deployment_snapshot.yaml`

**These are design specs, not code — the intended mechanics. Mine before
building new L2 dynamics.**

## 6. Orion Station L1 (mostly already integrated)

- CanonRec `canon/L1/station/` — Operational Library v2.2, physical config,
  crew (41), chronicle, life infrastructure, purpose/powered-watch/crew-life
  doctrines (all landed in prior sessions).
- `simulation/ORION_STATION_MASTER_DOSSIER_v2.6.md`,
  `ORION_STATION_TECHNICAL_REGISTER_v2.6.json` — the v2.6 station spec
  (comparison baseline for promoting staged physical params).
- **Scenario catalogs:** `ORION_SCENARIO_CATALOG_v0_2_12..15.{html,pdf}` —
  four versions; the canonical scenario library. NOT yet mined into the watch
  scenarios (`catalog/*_scenario.json` are hand-authored). Candidate source.

## 7. PROJECT_KNOWLEDGE — curated summaries (read these first)

`GUMAS_SIM_2.5/PROJECT_KNOWLEDGE/`: `PK_01__GUMAS_ENGINE_FORGE_v3.0`,
`PK_02__GUMAS_ENGINE_ARCHITECTURE_v2.0`, `PK_03__OPAL2_TREASURE_MAP`,
`PK_04__FORECAST_SYSTEM_SPEC`, `PK_05__QGIA_KNOWLEDGE_LIBRARY` — the
maintained orientation layer.

## 8. GitHub repos (Aurora constellation)

| Repo | Lang | Role | Sim relevance |
|---|---|---|---|
| aurora-cloudbank-symbolic | Python | runtime/engine home | L1 station sim + mesh + engine surfaces |
| Aurora_ORIONCORE_Directory_Main | Python | root control plane | this workspace; GUMAS tools |
| CanonRec | Python | canon | L1 station canon |
| DuelSim_v2.0 | Python | combat sim | parallel track, own repo |
| qgia-knowledge-spine / -library | Python | QGIA | forecast/intel knowledge |
| AuroraOS / cloudbank-quantum-en | TypeScript | spokes | dormant since 2026-03-13; unwired |
| zip_wizard | HTML/TS | packaging | dormant; .env security note open |
| aurora-cloudbank-symbolic1 | JS | prototype | dormant 2025-09; archive-or-delete pending |

## 9. Unopened / archived bundles (disposition)

Sim-relevant zips not yet opened (peeked manifests):
- `projects/.../ORION_Simulation_Architecture-1.zip` — L1/L2/L3 codex specs +
  `l2_runtime_index.json` (July 2025 early architecture). **Open & compare.**
- `projects/Auora2.5_DEV/ORION_SimActivation_H1_v1.zip` — Aug 2025 "Hour 1"
  activation stubs (start/stop sim stubs, preflight). **Superseded by my
  hour-aboard work**; archival.
- `GUMAS_SIM_2.5/ORION__APPX_C_CHAMPLOO_SYSTEM_ENGINES…zip` — L3 governance
  modules + a "System Engines" scenario appendix. Governance dup of ORD pack.
- `GUMAS_SIM_2.5/INTAKE__GUMAS_SIM_2.0…zip`, `archives/sim_archives/GUMAS_SIM_2.0*.zip`
  — earlier GUMAS 2.0 snapshots; archival.
- Workbench bundles (`QFORGE_RECON`, `QFORGE_CASK`, `CANONSWITCH`, `DELTACARD`,
  `CAPSULE_BUNDLE`, `DOCKYARD_CAPSULE_ROUTER`, `CLOSURE_MODULE`,
  `CONSTELLATIONFORGE_CANVAS`, `STAGING_PIPELINE`) — Feb 2026 packaging drops;
  governance/capsule tooling, mostly superseded.
- `projects/.../AURORA_ORION_Runtime_v2.5-prep.zip`, `orion_gumas_anchor_tests_v25.zip`,
  `GUI_SIM_TEST_BUNDLE_v1.zip` — runtime-prep + anchor tests + GUI sim test.
  **Open the anchor tests** (`EOS_SEED_ORION` validation may be reusable).

The GUMAS memory subsystem (`gumas_memory_core.py`, `gumas_memory_maintenance.py`,
`gumas_recovery_wizard.py`, `GUMAS_Memory_Optimization_Module.py`) appears in
~8 duplicate archive copies — one canonical version should be located and the
rest left as archival.

## 10. Recommendations (sequence to avoid reinvention)

1. **Read before building:** `PK_01`/`PK_02` (engine), the seed-42
   `LESSONS_LEARNED`, `hourly_retrospective.py`, `gumas_api.py`, and the
   recovered `draft_logic` math framework + `non_war_progression_mechanics`.
2. **Reconcile turn-stepping:** my powered/live watches and the existing
   `hourly_retrospective.py` both step the engine per turn — unify on one
   stepping/retrospective core; have watches call `gumas_api` event-injection
   rather than re-embedding.
3. **Route L2 galactic canon** (`L2_CANON__2026-03-19`) into a CanonRec
   `canon/L2/` home, mirroring the L1 station canon (owner decision).
4. **Mine the scenario catalogs** (`ORION_SCENARIO_CATALOG_v0_2_15`) into the
   watch scenario JSONs instead of hand-authoring.
5. **Address the seed-42 instability** using `non_war_progression_mechanics.md`
   before the next long galactic run — the runaway-conflict failure is already
   diagnosed.
6. **Owner triage queue** unchanged: AuroraOS/quantum-en wiring,
   aurora-cloudbank-symbolic1 decision, zip_wizard .env, the 22.1h/24h
   station-day reconciliation.

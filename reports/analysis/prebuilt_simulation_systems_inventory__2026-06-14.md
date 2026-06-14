# Prebuilt Simulation Systems — Inventory & Reuse Map

**Date:** 2026-06-14 | **Scope:** entire repo + surrounding iCloud Drive
(`Extras_Backups (Au)`, `GPT Production`, `GitHub Repositories`, siblings) |
**Purpose:** before building the dynamic-galaxy pillars, find what already exists
so we extend foundational work instead of rebuilding it.

## Headline finding

**The diplomacy off-ramp the action plan wants to "build" already exists in the
current engine — for inter-faction conflict — and was fully designed in the
earliest engine.** The work is to **extend proven, present machinery to the
insurgency (civil-war) layer**, not invent it. Several other "new" mechanics map
to code or specs that already exist.

The galaxy has **two parallel conflict systems**, and only one of them is
finished:

| | Inter-faction conflict | Intra-faction insurgency (civil war) |
|---|---|---|
| Model | `ConflictState` (engine `models.py`) | v3 `Insurgency` (Forge `rebellion.py`) |
| Phase machine | **full**: PEACE→TENSION→ESCALATION→OPEN_CONFLICT→STALEMATE→**DEESCALATION→CEASEFIRE→NEGOTIATION→RESOLUTION** | ORGANIZING→ACTIVE→ESCALATED→CIVIL_WAR (+SUPPRESSED); **RESOLVED never assigned** |
| Off-ramps | de-escalation, ceasefire, negotiation, treaty | **military suppression only** |
| Feeds stability as | `conflict_pressure` (→ 0 in back half: they *resolve* diplomatically) | `insurgency_pressure` (0.886: never resolves) |

This single asymmetry explains the roundtable's three findings at once (war is the
only off-ramp; the metric is blind to civil war; the same wounds reopen). **Pillar
B = give the insurgency layer the resolution machine the conflict layer already
has.**

---

## A. Active engine (today's simulation) — `GUMAS_SIM_2.5/`

| Path | What it is | Status |
|---|---|---|
| `SIM_ENGINE_OUTPUTS/engine.py`, `engine_base.py` | Base GUMAS engine (6-phase tick, conflict/treaty/diplomacy) | live (base) |
| `SIM_ENGINE_OUTPUTS/engine_advanced.py` | Advanced engine — wraps base + v3 Forge phases; **the one we run** | live (default) |
| `SIM_ENGINE_OUTPUTS/formulas.py` | `calc_deescalation_probability`, `calc_trust_update`, `calc_treaty_breach_score`, `is_treaty_breach`, `calc_reputation_after_decay`, `calc_double_agent_risk`, `calc_bias_evolution` | **present; off-ramp formulas under-used** |
| `SIM_ENGINE_OUTPUTS/models.py` | `ConflictPhase` (10-phase), `TreatyPhase`, `ConflictState`, `TreatyState`, `LeaderState`, `FactionState`, `BiasType` | **present** |
| `SIM_ENGINE_OUTPUTS/scenarios.py` | `build_default_scenario` (13 factions) | live |
| `FORGE__GUMAS_v3.0__2026-02-19/rebellion.py` | Insurgency model (the civil-war layer; **no resolution path**) | live |
| `FORGE__GUMAS_v3.0__2026-02-19/population.py` | Migration, demographics, stress drivers | live |
| `FORGE__GUMAS_v3.0__2026-02-19/intelligence.py` | Compromise, surveillance, counter-intel | live |
| `FORGE__GUMAS_v3.0__2026-02-19/negotiation.py` | Negotiation phase → `DIPLOMATIC_AGREEMENT` (does **not** resolve insurgencies) | live |
| `FORGE__GUMAS_v3.0__2026-02-19/technology.py` | Tech diffusion / breakthroughs | live |
| `tools/mech_gov_001.py` | Our mechanic stack: GOV-001, SOC-001/002/003/005/006, DIP-001 | live (governed) |
| `tools/gumas_consequence_layer.py` | INT-001, MIL-002, REB-002/003 | live (governed) |
| `tools/gumas_memory_run.py` | The A/B + writeback harness | live |
| `tools/observatory_240_cycle.py` | The 240-turn certification test case | live |

## B. Foundational engine lineage — `projects/GUMAS_SIM_2.0/02_DEVELOPMENT/Engine/`

The earliest L2 engine, predating v3.0. **This is where the conflict-resolution
design originated.**

| Path | What it is |
|---|---|
| `Engine/Core_Engine_v1.2/26_Engine_1.2/engine.py` (1329 lines) | Original `GUMASEngine`: 6-phase tick, `_handle_diplomatic_overture`, `_handle_treaty_violation` (breach score → collapse), **"Phase 4.5: Peacetime recovery (the missing half)"** |
| `…/26_Engine_1.2/scenarios.py` | Original scenario builder |
| `Engine/Integration_Latest_v1.3/Engine Room/` | v1.3 integration + `Convergence Regulator Build Prep.md` + `ORION__L2_GUMAS_ENGINE__SOURCE_BUNDLE__v1.1` |
| `…/STAGING_CONTEXT_BUNDLE__v1/26_engine_1.4/engine.py` | v1.4 engine |
| `…/26_engine_2.0/modules/gumas/{engine,formulas,models,scenarios}.py` | v2.0 — the **full module package** (the import surface the current engine inherits) |

**Original module surface** (`modules.gumas`): `formulas.py` (apply_bias_hooks,
calc_bias_evolution, **calc_deescalation_probability**, calc_double_agent_risk,
calc_reputation_after_decay, **calc_treaty_breach_score**, calc_trust_update,
is_treaty_breach); `models.py` (BiasType, ConflictPhase, ConflictState, EventType,
FactionState, GUMASState, LeaderState, SimulationEvent, TickResult, TreatyPhase,
TreatyState). **Provenance:** our MECH-DIP-001 (trust) and MECH-SOC-005 (recovery)
re-implement what this lineage already had.

## C. Earliest design notes — the equation source (text notes, date-agnostic)

| Path | What it carries |
|---|---|
| `intake/text_early_sim_logic.txt` | **The original L2 equations**: stability update `S_new=S_old+α(E_success)−β(E_failure)`; Q-learning faction strategy; **`T_new=T_old−λ(B)+δ(A)`** (= MECH-DIP-001); **`AI_Faction_Strategy = P(negotiation\|past_success)+P(war\|military_strength)`** (the war-vs-diplomacy decision — seed of Pillars B & C); `Political_Loyalty = Ideological_Alignment − Past_Betrayals + Personal_Relationships`; `Public_Opinion = Policy_Success − Scandals + Economic_Stability`; `Event_Trigger = P(breakthrough)+P(collapse)+P(civil_war)`; `P(support)=Ideological_Alignment+Political_Ambition−Risk_Assessment` |
| `intake/text_factions_reg.txt` | Original faction registry — traits, substructures, **internal factions** (Velar Imperium: Imperial Loyalists / Republican Reformists / Outer Colony Warlords), species, cultural significance (Pillar C substrate) |
| `intake/text_pulse_engine.txt` | QUANTUM_FORGE generative-agent core spec (agent generation/memory/reactivation) |
| `…/Project_Files_GUMAS2_0/GUMAS Engine Advancement.md` | **Strategic roadmap + gap analysis** of the original engine. Names the gaps that are now our pillars: *no formal coalition mechanics* (POW-001), *limited economic interdependency* (ECO-001), *sparse event provenance / no parent-child cascade tracking* (Pillar A causal depth) |
| `…/Project_Files_GUMAS2_0/CHARACTERFORGE_SPEC_v0.1.0.md` | **Authentic-character engine spec**: deterministic, **non-convergent**, ships a **"reaction genome,"** memory-native — the full Pillar C design |
| `…/Project_Files_GUMAS2_0/L2_GUMAS_RUNTIME_REFERENCE_PACKET_v0.4.md`, `1.4Engine_ARCHIVE_ANALYSIS.md`, `04_DOCUMENTATION/GUMAS_Legacy/Original_Materials/GUMAS_OG/` | Reference packets, tech reference, OG world bible, architectural-enhancement PR notes |
| `…/Engine Room/ORION__L2_GUMAS_ENGINE__SOURCE_BUNDLE__v1.1` (also in CanonRec operational_library) | Full engine source bundled as text (recovery copy if modules are lost) |

## D. Character / behavior systems (Pillar C foundation)

| Path | What it is |
|---|---|
| `Extras_Backups (Au)/GUMAS_AI_Agents_Kit.zip` → `character_behavior_modules.py`, `behavior_loader.py` | **Early authentic-decision system**: `CharacterBehaviorModule` with `personality_traits`, `loyalty_profile`, `memory_filters`, `reaction_triggers` (event→action), `speech_tone`, `faction_alignment`; `respond_to_event()`, `filter_memory()`. Per-character subclasses (Daela Syrix, Vael Saros, Zylox, Durn) |
| `GUMAS_SIM_2.5/CanonRec/canon/L2/entities/<leader>/capsule/traits.json` | Per-leader **decision substrate** already in canon: `dominant_bias`, `decision_style`, `traits`, `allegiance` (cultural tradition), `reputation`, `relationships` |
| CharacterForge / charforge (FORGE lineage, `aurora-quantum-forge-ops` skill) | Capsule generation engine for the above |

## E. Memory substrate (decision + grievance memory)

| Path | What it is |
|---|---|
| `Extras_Backups (Au)/GUMAS_Aurora_Startup_Kit.zip` / `GUMAS_Seed_Kit.zip` / `Aurora_Developer_Kit_Final.zip` → `gumas_memory_core.py`, `gumas_memory_maintenance.py`, `gumas_recovery_wizard.py`, `aurora_runtime_loader.py` | The GUMAS memory system (importance-weighted, decay, retrieval). **MECH-GOV-001's episodic memory is a clean port of this** |
| `Extras_Backups (Au)/GUMAS_Memory_Integration_Pack.zip` | `updated_galactic_union_memory_index.json`, `full_galactic_union_timeline.csv`, `full_galactic_union_alignment.csv` — canon memory/timeline/alignment data |

## F. Scenario / combat / mission data (consequence + culture inputs)

| Path | What it is |
|---|---|
| `GUMAS_SIM_2.0/03_SIMULATION/Entity_Profiles/Marshals_Sentinels/*.csv` | Ship-to-ship combat dynamics, starship classes, shielding/propulsion, defensive capabilities — a **combat-resolution dataset** |
| `GUMAS_SIM_2.0/03_SIMULATION/Mission_Logs/SimLogsBuild/*.csv` | Early **diplomacy-as-system** sim runs: *Operation Obsidian Dawn* (briefing/execution/conflict/outcome), *Military Pressure Supporting Diplomacy*, *Results of Targeted Diplomatic Engagements*, *Office of Strategic Diplomacy*, *Chancellor Zylox's Full-Force Diplomatic Offensive* |
| `GUMAS_SIM_2.0/02_DEVELOPMENT/.../ORION_SCENARIO_CATALOG_v0_2_*.html` | Scenario catalogs (conflict-phase referenced) |
| `Extras_Backups (Au)/Extra Folders/exports/COMET_ECHO_v1.simstate` | A saved simulation state snapshot |

## G. Canon system specs (L2 social dynamics) — `CanonRec/canon/L2/`

| Path | What it is |
|---|---|
| `social_dynamics/galactic_union_simulation_math_framework.md` | The simulation math framework (canon) |
| `social_dynamics/galactic_union_state_variables.md` | State-variable definitions |
| `social_dynamics/non_war_progression_mechanics.md` | DSI = (P+E+S)/(C+M) — already cited by SOC-003/006 |
| `social_dynamics/simulation_expansion_systems_outline.md` | **Systems §9–16** — the canon blueprint the action plan maps to (diplomacy/soft-power, planetary cultural identity, succession, economy, AI strategy) |
| `mechanics/03_galactic_union_mechanics_and_models.md` | Faction decision canon rules (betrayal→hostility, weakness→negotiation) |
| `mechanics/l2_polity_dossiers__recovered_textAu.json` | Polity dossiers (cultural/political detail) |

## H. Adjacent cognitive/symbolic engines (L3 — not L2 galactic, noted for completeness)

`GUMAS_SIM_2.5/Aurora_Sim_Architecture/`: `quantum_decision_oracle.py`,
`aurora_fusion/engine.py`, `working_group_engine.py`,
`reflective_autonomy_loop.py`, `autonomic_correction_engine.py`,
`innovation_ledger.py`, plus the cloudbank-symbolic mesh runtime. These are the
Aurora cognitive layer (decision/▲symbolic), reusable for agent reasoning but not
the galactic sim core.

---

## Reuse map — action-plan impact

| Plan item | Prior diagnosis | **Revised: what actually exists** |
|---|---|---|
| **Phase 0 / D4** true RESOLVED state | "build new" | `ConflictPhase.RESOLUTION` + `calc_deescalation_probability` exist for inter-faction conflict; **port the pattern to `rebellion.py`** |
| **MECH-DIP-002** Mediated Settlement | "build new" | De-escalation→negotiation→resolution machine exists; **wire it to end insurgencies** (the missing link) |
| **MECH-DIP-003** Treaty Enforcement | "build new" | **Already implemented**: `calc_treaty_breach_score`, `is_treaty_breach`, `TreatyPhase.COLLAPSED`, `_handle_treaty_violation` — surface + connect |
| **MECH-GOV-002** Culture-weighted decisions | "extend GOV-001" | `traits.json` + `character_behavior_modules.py` (`reaction_triggers`, `loyalty_profile`) + `CHARACTERFORGE_SPEC` reaction-genome — rich substrate to wire |
| **MECH-GOV-003** Succession/internal politics | "build new" | Equations exist (`Public_Opinion`, `P(support)`, `Political_Loyalty`); leader fields (`elite_support`, `scandals`) live |
| **MECH-POW-001** Power dynamics / coalitions | "build new" | Named as a gap in `GUMAS Engine Advancement.md`; `AI_Faction_Strategy` + alliance trust fields exist as starting point |
| **MECH-ECO-001** War economy | "build new" | Named gap ("limited economic interdependency"); economic fields live on `FactionState` |
| **Pillar A** causal depth | "build new" | Named gap ("sparse event provenance / no parent-child cascade tracking") — design intent recorded; event_id/payload_hash plumbing already present |
| **MECH-SOC-005** recovery (shipped) | built | Was already the original engine's *"Phase 4.5 peacetime recovery (the missing half)"* — convergent re-derivation |

## Recommended next step

Before Phase 1, **read the original `26_engine_1.2/engine.py` + the SOURCE_BUNDLE
v1.1 in full** and lift its conflict-resolution / treaty / de-escalation pattern
directly onto the insurgency layer. The cheapest path to "war is not the only
off-ramp" is to give civil wars the resolution machine that inter-faction
conflicts already use — proven code, not a green-field build. Recovery of the
possibly-incomplete `modules/gumas/formulas.py|models.py` (full copies exist in
`SIM_ENGINE_OUTPUTS/` and the v2.0 staging bundle) should precede that.

_No files were modified by this survey. Kit zips inspected by listing only;
COMET_ECHO simstate and memory-index data noted, not loaded._

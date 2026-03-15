# FORGE — GUMAS v3.0 Engine Synthesis
## Manifest & Delivery Record

**Anchor:**    GUMAS-ENGINE-FORGE-V3
**Seed:**      EOS_SEED_ORION
**Ethics:**    Picard_Delta_3
**Date:**      2026-02-19
**Status:**    ✅ COMPLETE — 45/45 tests passing (CharForge extension added)

---

## What Was Built

This forge session synthesized the next advanced iteration of the GUMAS simulation engine,
extending the validated v2.0 platform (9,833 LOC, 15 phases, 28 formulas) with five new
subsystem modules, 5 new tick phases, 20+ new formulas, and 18 new event types.

---

## Delivered Files

| File | Role | LOC |
|------|------|-----|
| `population.py` | Phase 16 — Population & Demographics module | ~380 |
| `technology.py` | Phase 17 — Technology Development Tree module | ~530 |
| `negotiation.py` | Phase 18 — Advanced Diplomacy & Negotiation module | ~450 |
| `intelligence.py` | Phase 19 — Intelligence Network module | ~440 |
| `rebellion.py` | Phase 20 — Rebellion & State Fragmentation module | ~420 |
| `models_v3_ext.py` | GUMASStateV3Extension + TickResultV3 + scenario init | ~200 |
| `engine_v3_patch.py` | GUMASEngineV3Mixin + GUMASEngineV3 — 20-phase integration | ~340 |
| `validate_v3.py` | Full validation suite — 45 tests across all modules, engine, and CharForge | ~814 |
| `charforge.py` | CharForge — ORION Capsule Bundle v0.2.0 generator/loader for GUMAS characters | ~1,076 |
| `FORGE_MANIFEST.md` | This file | — |

**Approximate new LOC:** ~4,196
**Total with v2.0 base:** ~14,029

---

## New Subsystems at a Glance

### Phase 16 — Population (population.py)
- Logistic population growth (standard Verhulst model)
- Cross-faction migration driven by push/pull pressure
- Refugee generation from active conflicts
- Demographic stress index feeding rebellion onset
- Conscription capacity per faction
- **Formulas:** `calc_population_growth`, `calc_migration_pressure`, `calc_conscription_capacity`, `calc_demographic_stress`, `calc_refugee_generation`, `calc_war_casualties`

### Phase 17 — Technology (technology.py)
- R&D investment with diminishing returns near tech ceiling (0–5.0 scale)
- 20-node canonical tech tree with unlock dependencies (8 domains)
- Passive tech diffusion between high-trust factions
- Combat/economic multipliers applied to v2.0 FactionState
- Tech espionage yield for sentinel missions
- **Formulas:** `calc_tech_advance_rate`, `calc_tech_diffusion`, `calc_military_tech_advantage`, `calc_civilian_tech_multiplier`, `calc_tech_espionage_yield`

### Phase 18 — Negotiation (negotiation.py)
- Multi-round treaty negotiation with BATNA modeling
- Concession exchange (position convergence per round)
- Back-channel secret diplomacy track
- Diplomatic crisis events on breakdown
- Ultimatum mechanics (deadline-based coercive demands)
- **Formulas:** `calc_negotiation_success`, `calc_concession_threshold`, `calc_batna_strength`, `calc_diplomatic_crisis_severity`, `calc_back_channel_trust_boost`, `calc_ultimatum_compliance`

### Phase 19 — Intelligence (intelligence.py)
- SIGINT/HUMINT/IMINT/OSINT/CYBINT collection per faction
- Intelligence fusion (multi-source accuracy boost via synergy bonus)
- Counter-intelligence probability of catching adversary operatives
- Surveillance state levels (Open → Totalitarian) with legitimacy penalties
- Inter-ally intelligence sharing network
- **Formulas:** `calc_sigint_yield`, `calc_humint_penetration`, `calc_intelligence_fusion`, `calc_counter_intel_pressure`, `calc_surveillance_legitimacy_penalty`

### Phase 20 — Rebellion (rebellion.py)
- Insurgency onset from demographic stress + low legitimacy
- Insurgency strength dynamics vs. state repression
- Civil war escalation (quadratic probability model)
- State fragmentation (Picard_Delta_3 gated — high-impact mutation)
- Separatist declarations, mass conscription events
- **Formulas:** `calc_rebellion_onset_probability`, `calc_insurgency_strength`, `calc_state_fragmentation_risk`, `calc_repression_effectiveness`, `calc_civil_war_escalation`

---

## New Event Types (18)

```
POPULATION_MIGRATION, REFUGEE_CRISIS, MASS_CONSCRIPTION
TECH_BREAKTHROUGH_ADVANCED, TECH_DIFFUSION, TECH_NODE_UNLOCKED
DIPLOMATIC_AGREEMENT, DIPLOMATIC_CRISIS, BACK_CHANNEL_DEAL
ULTIMATUM_ISSUED, ULTIMATUM_RESOLVED
INTELLIGENCE_SHARING, INTELLIGENCE_COMPROMISE, SURVEILLANCE_EXPANSION
REBELLION_ONSET, CIVIL_WAR_ONSET, STATE_FRAGMENTATION, SEPARATIST_DECLARATION
```

---

## Cross-Module Feedback Writes (engine_v3_patch.py)

After Phase 20, the engine applies v3.0 multipliers back to v2.0 base state:

| v3.0 Source | v2.0 Target | Effect |
|-------------|-------------|--------|
| tech_combat_multipliers | FactionState.military_strength | Soft pull toward tech-boosted ceiling |
| tech_economic_multipliers | FactionState.economic_potential | Raises economic ceiling |
| calc_civilian_tech_multiplier | FactionState.economic_strength | Direct per-turn boost |
| insurgency.territory_controlled | military, economic, population_stability | Drag reduction per insurgency |
| surveillance_legitimacy_penalty | LeaderState.public_legitimacy | Per-turn legitimacy drain |
| concluded negotiations' trust_delta | FactionState.trust_scores | Trust update on deal |

---

## CharForge — ORION Capsule Bundle Standard v0.2.0

The CharForge subsystem makes every GUMAS simulation character (leader / faction pair)
a portable, verifiable, self-contained ORION Capsule Bundle.

### Seven-File Capsule Invariant

| File | Content | Source |
|------|---------|--------|
| `identity.json` | capsule_id, declared_layer (L2), ethics_protocol, anchor_seed, role | `LeaderState` |
| `traits.json` | voice (tone/cadence/avoid), values, constraints — bias-derived | `BiasType` + `FactionType` |
| `knowledge.jsonl` | identity synopsis, bias pattern, faction posture, stressor history, trust relationships | `LeaderState` + `FactionState` |
| `cns.yaml` | tool_policy, retrieval config (tag_overlap, top_k=5), self_checks | Calibrated from `oversight_resistance` |
| `state.bin` | 21 × float16 little-endian state vector | Encoded from `LeaderState` + `FactionState` |
| `runtime.py` | stdlib-only validate/compile/state CLI | Spec-verbatim (unchanged) |
| `manifest.json` | SHA-256 records for all six non-manifest files | Computed by `_build_manifest()` |

### State Vector Layout (21 × float16)

```
[0]  bias_intensity              [7]  public_legitimacy
[1]  plasticity                  [8]  elite_support
[2]  evidence_gain_multiplier/2  [9]  institutional_control
[3]  risk_tolerance             [10]  war_pressure
[4]  diplomacy_openness         [11]  economic_shock (abs)
[5]  escalation_threshold       [12]  military_strength
[6]  oversight_resistance       [13]  economic_strength
                                [14]  technology_level
                                [15]  population_stability
                                [16]  reputation
                                [17]  verification_demand
                                [18]  deal_discount
                                [19]  coalition_invite_weight
                                [20]  economic_potential
```

### Public API

| Function | Purpose |
|----------|---------|
| `generate_capsule(leader, faction, output_dir)` | Generate full 7-file bundle + BUILD_RECEIPT |
| `load_capsule(bundle_path)` | Reconstruct `(LeaderState, FactionState)` from bundle |
| `tick_update_state_bin(leader, faction, bundle_path)` | Sync state.bin + manifest after each tick |
| `verify_capsule(bundle_path)` | SHA-256 integrity check; True/False |
| `capsule_summary(bundle_path)` | Diagnostic dict without model import |
| `generate_all_capsules(world_state, output_dir)` | Batch-generate for all leaders in GUMASState |

### Design Properties

- **Authentic:** Voice, cadence, and avoidance lists are derived directly from BiasType archetype tables. Values are keyed to FactionType governance model. Knowledge records are generated from real simulation stressors and trust history.
- **Believable:** `style_ctl` activates automatically when `oversight_resistance > 0.4`, suppressing authoritarian tone-bleed into the narrative layer.
- **Portable:** Entire character state is self-contained in 7 files (~5 KB). `runtime.py compile` emits a `system/user` JSON prompt pack for direct LLM-driven character behaviour.
- **Interoperable:** Bundle structure is spec-compliant with ORION Capsule Bundle Standard v0.2.0. SHA-256 manifest chain is enforced; `verify_capsule` fails immediately on any tamper.

---

## Validation Results

```
Validation: 45/45 tests passed
Sections: Population (6) | Technology (5) | Negotiation (6) |
          Intelligence (5) | Rebellion (5) | Engine Integration (5) |
          Reproducibility (1) | CharForge Capsule (12)
Seed:      EOS_SEED_ORION (reproducibility confirmed identical across runs)
```

---

## Integration Path (v2.0 → v3.0)

1. **Standalone mode:** Run `GUMASEngineV3(seed=42)` from this directory — uses minimal test state, no v2.0 dependency.
2. **Delegate mode:** Ensure `../SIM_ENGINE_OUTPUTS/` is on the Python path. `GUMASEngineV3` will auto-detect and wrap the v2.0 `GUMASEngine`, delegating phases 1–15 to it and adding phases 16–20 via the mixin.
3. **Future merge (v3.1):** Merge `GUMASStateV3Extension` fields directly into `GUMASState` in `models.py` and inline the new phases into `engine.py`'s main `step()` loop.

---

## Command Tokens Active During Forge

- `+005//.` — all phases implemented in logical dependency order
- `+Picard_Delta_3//.` — applied to `STATE_FRAGMENTATION` events (high-impact mutation gate)
- `EOS_SEED_ORION` — anchor seed; reproducibility confirmed across all engine runs

---

*Built for consistency, clarity, and care.*

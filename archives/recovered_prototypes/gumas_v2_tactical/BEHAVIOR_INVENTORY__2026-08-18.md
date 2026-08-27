# Behavior Inventory — GUMAS v2.0 Tactical Package

Date: 2026-08-18
Companion to: `RECOVERY_RECORD__2026-08-18.md`
Method: AST parse and hand reading of the frozen snapshot; one defect additionally
observed at runtime in an isolated container against a copy. **No archival file
was executed in place, modified, or repaired.**

## Architecture

`GUMASEngine` declares a **15-phase** tick lifecycle (`engine.py:202–217`).
Every other engine in the lineage declares six.

| Phase | Method | Subsystem module |
|---:|---|---|
| 1 | `_process_event_queue` | — |
| 2 | `_update_leader_hooks` | `formulas` |
| 3 | `_evaluate_conflicts` | `formulas` |
| 4 | `_evaluate_treaties` | `formulas` |
| 5 | `_peacetime_recovery` | — |
| 6 | `_diplomacy_tick` | — |
| 7 | `_coalition_lifecycle` | `formulas` |
| **8** | **`_fleet_movement_tick`** | **`topology`** |
| **9** | **`_combat_resolution_tick`** | **`combat`** |
| 10 | `_economic_tick` | `economics` |
| 11 | `_media_tick` | `media` |
| 12 | `_precursor_tick` | `precursors` |
| 13 | `_sentinel_tick` | `sentinels` |
| 14 | `_doctrine_tick` | `doctrine` |
| 15a | `_culture_tick` | — |
| 15b | `_generate_emergent_events` | `forecaster` |

Phases 1–6 call the same six methods, in the same order, as `26_Engine_1.3`.
v2.0 is that political core plus nine phases.

## State model

`GUMASState` exposes `anchor, coalitions, combat_zones, conflicts,
culture_movements, doctrines, economy, ethics_protocol, event_queue, factions,
fleets, history, leaders, media, missions, operatives, precursor_sites,
scenario_id, seed`.

Thirteen fleets are instantiated by the default scenario. No other engine in the
lineage has a `fleets` attribute at all.

## Combat contract

```
CombatResolver.resolve_battle(combat: CombatState,
                              attacker_fleets: List[FleetState],
                              defender_fleets: List[FleetState],
                              topology_manager=None) -> Dict[str, Any]
```

`CombatResolver` also defines `apply_fleet_losses`, `calc_retreat_probability`,
`generate_battle_events`, and five private aggregation helpers.
`get_terrain_modifiers(BattlefieldCondition)` is a module-level function.

## Integration defects — fifteen call sites, ten of fifteen phases

**Not repaired.** Recorded for the downstream restoration to decide on.

| engine.py | Phase | Callee | Defect |
|---:|:-:|---|---|
| 420 | helper | `calc_coalition_stability` | 2 of 4 args; `[list]` into `bilateral_trust`, `_rng` into `members_at_war` |
| 532 | 2 | `calc_bias_evolution` | `BiasType` into `current_intensity: float` — **observed** `TypeError` at `formulas.py:115` |
| 547 | 2 | `apply_bias_hooks` | 3 objects into `(str, float)` |
| 568 | 3 | `calc_deescalation_probability` | 4 of 6, argument order transposed |
| 611 | 4 | `calc_treaty_breach_score` | `_rng` into `faction_trust: float` |
| 618 | 4 | `is_treaty_breach` | `_rng` into `violation_threshold: float` |
| 722 | 8 | `calc_fleet_supply_decay` | `_rng` into `route_security: float` |
| 763 | 9 | `resolve_battle` | `combat=None` into a `CombatState` dereferenced at `combat.py:110` |
| 814 | 11 | `calc_propaganda_effectiveness` | `_rng` into `media_reach: float` |
| 825 | 11 | `calc_media_legitimacy_impact` | 2 of 3 |
| 846 | 12 | `calc_precursor_activation_risk` | 4 of 3; node id, dict, `_rng` into floats |
| 887 | 13 | `calc_mission_success_probability` | `_rng` into `counter_intel: float` |
| 913 | 14 | `calc_q_learning_update` | 5 of 3; dict into `current_q: float` |
| 933 | 15a | `calc_culture_spread_rate` | `_rng` into `distance_penalty: float` |
| 1388 | helper | `resolve_combat` | method absent from `CombatResolver` |

`_form_coalition` (420) and `_handle_fleet_battle` (1388) are dispatched
indirectly and do not resolve to a phase by static call graph; their phase is
left blank rather than guessed.

### Cause — tested, and it is not a single refactor

An earlier draft proposed that `engine.py` had been written against a stochastic
`formulas` API later rewritten deterministic, making the fifteen defects one
mechanical migration. **Tested 2026-08-19. The hypothesis is refuted.**

| Corpus-wide check | Result |
|---|---|
| Distinct `formulas.py` in the GUMAS lineage (596 archives opened) | 2 — v1.x (12,106 B) and v2.0 (26,037 B) |
| v1.x functions accepting an `rng`/`random`/`seed` parameter | **0 of 9** |
| v2.0 functions accepting one | **0 of 27** |
| Of the 11 functions `engine.py` calls with `self._rng`, how many exist in v1.x | **4** — the other 7 are new in v2.0 |
| Of those 4, how many have a signature that changed between v1.x and v2.0 | **0** |

There was never a stochastic `formulas` API to migrate away from.

Per-engine consistency, each audited against the `formulas.py` it shipped with:

| Engine | Calls into `formulas` | Arity mismatches | Passing `self._rng` |
|---|---:|---:|---:|
| v1.0 | 6 | **0** | **0** |
| v1.2 | 7 | **0** | **0** |
| v1.3 | 7 | **0** | **0** |
| v1.4 | 7 | **0** | **0** |
| **v2.0** | 19 | **6** | **11** |

The entire v1 line is internally consistent. Every defect is **new in the v2.0
rewrite**: `engine.py` and `formulas.py` are two halves of that rewrite that were
never reconciled, with the engine calling an interface that has never existed in
any version of this codebase.

**Consequence for planning:** these are fifteen independent authoring decisions,
not one pass. Each requires a judgement about intended behaviour with no original
author to consult. Size the remediation at the larger number.

## Execution history

- **Measured:** all 13 modules carry timestamp-validated `.pyc` (CPython 3.10,
  magic 3439) dated 2026-02-07 22:29–22:53, embedded source sizes matching these
  bytes exactly. Every module was imported; module-level code ran.
- **Measured:** no artifact anywhere in the Aurora tree contains any v2.0
  scenario id (`ai_shadow_split`, `corporate_coup`, `frontier_spark`,
  `precursor_ping`, `rotting_treaty`) or the `GUMAS-ENGINE-SCENARIOS-V2` anchor.
  No state export, ledger, or snapshot.
- **Measured:** under the restored harness with the default scenario, `step()`
  raises at Phase 2.
- **Inferred:** never run to a completed tick. Consistent with all three
  observations; not entailed by them.

## Syntax

All 13 modules parse under `ast.parse()`. Verified without execution.

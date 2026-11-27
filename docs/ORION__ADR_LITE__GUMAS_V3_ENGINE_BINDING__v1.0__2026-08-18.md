# GUMAS v3.0 Engine Binding Decision v1.0

**Date:** 2026-08-18
**Task:** `TASK-20260812-gumas-deterministic-battle-runtime`
**PR:** `#1506`
**Status:** proposed — requires owner sign-off before any re-pointing
**Applies to:** `GUMAS_SIM_2.5/FORGE__GUMAS_v3.0__2026-02-19/engine_v3_patch.py`, `skills/aurora-quantum-forge-ops/scripts/build_qforge_ops_report.py` — both local to the Aurora tree; neither is carried in this repository
**Repository:** `AUo959/Aurora_ORIONCORE_Directory_Main`
**Frozen source:** `archives/recovered_prototypes/gumas_v2_tactical/`
**Downstream restoration:** `AUo959/aurora-cloudbank-symbolic` → `simulation/runtime/gumas_v2_restored/` (branch `agent/gumas-flash-rebellion-battle-baseline`)

## Evidence classes

Every claim below carries a label. **MEASURED** = observed by running or parsing
the artifact. **DERIVED** = computed from measured data by a stated method.
**INFERRED** = a judgement that fits the evidence but is not entailed by it.

An earlier draft of this record made three claims that did not survive
re-examination. They are corrected in §7 rather than quietly removed.

## Decision required

`GUMASEngineV3` binds its base engine by dynamic import at construction time.
Which engine it gets is decided by `sys.path`, is recorded nowhere, and is
surfaced in no output. Three materially different bindings produce
indistinguishable reports.

## 1. It delegates; it does not inherit — MEASURED

`engine_v3_patch.py` docstring:

> *"GUMASEngineV3 inherits from the v2.0 GUMASEngine and overrides the step() method to add 5 new phases after the existing 15."*

The class is `class GUMASEngineV3(GUMASEngineV3Mixin)`. There is no base-engine
inheritance. `__init__` performs `from engine import GUMASEngine`, stores the
instance as `self._base_engine`, sets `self._delegate_mode = True`.
`full_step()` calls `self._base_engine.step()` then `self.step_v3()`.

Delegation is the more flexible design. The docstring describes a different
program, and "the existing 15" is true only of `26_engine_2.0`.

## 2. What it binds today — MEASURED

Run in an isolated container against copies of the live tree:

```
delegate_mode      : True
base engine class  : GUMASAdvancedEngine
base engine module : engine_advanced
base engine sha256 : 3917d25311f157ae3c21d7259323b4d2180aeca7319bed0570f5e3aadd9a57e3
state type         : GUMASState        factions: 13
state_has_fleets   : False
tactical attrs     : []
```

The import resolves through `../SIM_ENGINE_OUTPUTS`, where a 950-byte shim
(2026-03-05) sets `GUMASEngine = GUMASAdvancedEngine` — a descendant of
`26_Engine_1.3` (`docs/ORION__AUDIT__GUMAS_ENGINE_LINEAGE__v1.0__2026-08-18.md`).

For contrast, the restored v2.0 boundary under the same probe:

```
state_has_fleets   : True   fleet_count: 13
tactical attrs     : combat_zones, doctrines, fleets, operatives, precursor_sites
```

## 3. What v3 actually reads and writes — MEASURED

Complete set of base-state attributes referenced anywhere in `engine_v3_patch.py`:

```
conflicts  current_turn  economic_potential  economic_strength  factions
intel_networks  leaders  military_strength  population_stability  to_dict
```

`grep` for `fleets`, `CombatState`, `FleetState`, `combat_zones` across every v3
module returns nothing.

**v3 is entirely faction-scalar.** `_apply_v3_feedback` writes
`tech_combat_multipliers` into `FactionState.military_strength`, a field that
exists on the currently-bound engine.

The consequence matters for the options below: **binding v3 to a tactical base
would not make v3 tactical.** It would give v3 a world-state evolved by fifteen
phases instead of six; v3 would still read only faction scalars. Making v3 act
on fleets is new integration work, not a re-point.

## 4. The fallback path — MEASURED

```python
except ImportError:
    self._delegate_mode = False
    logger.warning("v2.0 engine not found; running in v3-standalone mode.")
```

Standalone mode fabricates three `SimpleNamespace` factions with hardcoded
values. Reproduced by placing `engine_v3_patch.py` where no
`../SIM_ENGINE_OUTPUTS` exists: `init_scenario()` and `full_step()` both
complete, and events are emitted.

`_delegate_mode` is read at `engine_v3_patch.py:409` and `:472` — the patch
branches on it internally. A tree-wide grep finds **no reader outside the patch
itself**, and it appears in no report, log line, or artifact.

## 5. What `validate_v3.py` covers — MEASURED

`validate_v3.py:13`:

> *"Runs in standalone mode (no v2.0 engine required) for CI/CD integration."*

It is a unit suite for the five v3 subsystem formulas. It never inspects
`_delegate_mode`, phase coverage, or combat. A green run is not evidence about
phases 1–15 in either direction.

## 6. Where the exposure actually is — MEASURED

`build_qforge_ops_report.py` constructs `GUMASEngineV3`, calls `full_step()`,
and reads only `v3_result`. It records no base-engine identity. A report is
identical in shape whether the base was v2.0, a v1.3 descendant, or absent — and
only the third case leaves even a log line.

This is a **provenance** defect, not a functional one: the v3 numbers are what
the code computed; which world-state they were computed against is unrecoverable
after the run.

## 7. Corrections to the earlier draft

| Earlier claim | Status | What the evidence shows |
|---|---|---|
| *"v2.0 was never executed once"* | **WRONG** | All 13 modules carry timestamp-validated `.pyc` compiled by CPython 3.10 (magic 3439) on 2026-02-07, with embedded source mtimes and sizes matching the recovered bytes exactly. The modules were imported and their module-level code ran. |
| *"nothing checks `_delegate_mode`"* | **IMPRECISE** | The patch branches on it at `:409` and `:472`. Nothing *outside* the patch reads it, and it is never surfaced. |
| *"v3 combat multipliers have nothing to act on"* | **WRONG** | They act on `FactionState.military_strength`, which exists on the bound engine. v3 never references fleet state at all — see §3. |
| *"nine defects across seven phases"* | **UNDERCOUNTED** | 15 call sites across 10 of the 15 phases — see §8. |

The `.pyc` finding is also a gain: thirteen compiled modules whose embedded
source metadata matches the recovered files byte-for-byte constitute a **third
independent witness** to the recovery, alongside the two archive ZIPs.

## 8. Integration-defect inventory — DERIVED (static) + one MEASURED

Method: AST parse of `engine.py` call sites against `modules/gumas` definitions;
every hit then read by hand at both ends. One defect additionally observed at
runtime.

| engine.py | Phase | Enclosing method | Defect |
|---:|:-:|---|---|
| 420 | helper | `_form_coalition` | `calc_coalition_stability` — 2 of 4 args; passes `[list]` as `bilateral_trust`, `_rng` as `members_at_war` |
| 532 | 2 | `_update_leader_hooks` | `calc_bias_evolution` — `BiasType` into `current_intensity: float`. **MEASURED**: `TypeError` at `formulas.py:115` |
| 547 | 2 | `_update_leader_hooks` | `apply_bias_hooks` — 3 objects into `(str, float)` |
| 568 | 3 | `_evaluate_conflicts` | `calc_deescalation_probability` — 4 of 6, and argument order transposed |
| 611 | 4 | `_evaluate_treaties` | `calc_treaty_breach_score` — `_rng` into `faction_trust: float` |
| 618 | 4 | `_evaluate_treaties` | `is_treaty_breach` — `_rng` into `violation_threshold: float` |
| 722 | 8 | `_fleet_movement_tick` | `calc_fleet_supply_decay` — `_rng` into `route_security: float` |
| 763 | 9 | `_combat_resolution_tick` | `resolve_battle(combat=None)` → dereferenced at `combat.py:110` |
| 814 | 11 | `_media_tick` | `calc_propaganda_effectiveness` — `_rng` into `media_reach: float` |
| 825 | 11 | `_media_tick` | `calc_media_legitimacy_impact` — 2 of 3 |
| 846 | 12 | `_precursor_tick` | `calc_precursor_activation_risk` — 4 of 3; node id, dict, `_rng` into floats |
| 887 | 13 | `_sentinel_tick` | `calc_mission_success_probability` — `_rng` into `counter_intel: float` |
| 913 | 14 | `_doctrine_tick` | `calc_q_learning_update` — 5 of 3; dict into `current_q: float` |
| 933 | 15a | `_culture_tick` | `calc_culture_spread_rate` — `_rng` into `distance_penalty: float` |
| 1388 | helper | `_handle_fleet_battle` | `resolve_combat` — method absent from `CombatResolver` |

`_form_coalition` and `_handle_fleet_battle` are not statically reachable from a
phase method in this graph — they are dispatched indirectly — so their phase is
left blank rather than guessed.

### Cause — MEASURED, and it is not a single refactor

(supersedes the DERIVED single-cause claim in the first draft)

#### Cause — tested, and it is not a single refactor

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

### Execution history — MEASURED, then INFERRED

- **MEASURED:** 13 validated `.pyc` dated 2026-02-07 22:29–22:53 — every module
  was imported.
- **MEASURED:** no artifact anywhere in the Aurora tree contains any v2.0
  scenario id (`ai_shadow_split`, `corporate_coup`, `frontier_spark`,
  `precursor_ping`, `rotting_treaty`) or the `GUMAS-ENGINE-SCENARIOS-V2` anchor,
  other than this session's own reports. No state export, ledger, or snapshot.
- **MEASURED:** under the restored harness with the default scenario, `step()`
  raises at Phase 2.
- **INFERRED:** the engine was never run to a completed tick. Consistent with all
  three observations; not entailed by them — a run under a different scenario, or
  one whose output was discarded, would leave the same trace.

## 9. Option B feasibility — MEASURED

Binding v3 to the restored v2.0 boundary was tested directly. A ten-line shim
exposing `GUMASEngine` from `restored_engine` is sufficient:

```
delegate_mode      : True
base engine class  : GUMASEngine   (restored_engine, 8faa9067…)
init_scenario      : OK
state_has_fleets   : True   fleet_count: 13
tactical attrs     : combat_zones, doctrines, fleets, operatives, precursor_sites
full_step()        : TypeError — BiasType + float, formulas.py:115  (Phase 2)
```

**The wiring is trivial. The blocker is the §8 backlog, and nothing else.**

`current_turn` and `intel_networks` are absent from v2.0 state but are assigned
by v3 rather than required to pre-exist. All four `FactionState` fields v3 writes
are present.

## Options

### Option A — Record the binding

Capture base-engine identity (module, file, SHA-256, fleet presence, tactical
attrs) into every ops report; treat `_delegate_mode == False` as an error.

| Dimension | Assessment |
|---|---|
| Complexity | Low — additive instrumentation |
| Risk | Very low; no simulation behaviour changes |
| Addresses | The provenance defect (§6) entirely |
| Does not address | The phase gap or the §8 backlog |

Verified against both live paths: current binding →
`v3_base_engine_non_tactical`; import failure → `v3_base_engine_absent`.

### Option B — Re-point v3 at the restored v2.0 boundary

| Dimension | Assessment |
|---|---|
| Wiring | Trivial — ten-line shim, **measured working** |
| Blocker | 15 call sites, 10 phases (§8), **fifteen independent decisions** — the single-cause hypothesis was tested and refuted |
| Gain | v3 reads a world-state evolved by 15 phases rather than 6 |
| **Does NOT gain** | **tactical v3 — v3 reads no fleet state (§3)** |

The honest value here is narrower than it first appears. It is worth doing to
make the base world-model complete, not because v3 needs fleets.

### Option C — Re-scope the v3 specification to the six-phase base

Documentation only. Makes current output honest without changing it. Reasonable
as an interim label; unreasonable as a terminal state if the tactical layer is
wanted.

### Option D — Make v3 tactical

New work, not in scope of any of the above: v3 phases would need to read and
write `fleets`, `combat_zones`, and `topology`. §3 shows no such code exists.
Listing it because Options B and D have been conflated, including by me.

## Trade-off analysis

A is cheap, immediate, and addresses the one defect that destroys evidence
irreversibly — a run whose base is unknowable after the fact. It is independent
of every other option and should not wait on them.

B and D are separable and were previously conflated. B makes the world-state
complete; only D makes v3 tactical. Sequencing B without D yields richer inputs
to unchanged v3 mechanics — worthwhile, but it will not produce fleet
engagements.

C conflicts with D as a terminal position and is compatible with it as an
interim caveat.

## Recommendation

**Adopt A now. Sequence B behind the §8 backlog. Use C's wording as an interim
caveat. Treat D as a separate proposal that has not been made yet.**

Mark prior `aurora-quantum-forge-ops` reports **unattributed** — weaker than
"wrong", stronger than "valid": the v3 subsystem numbers are what the code
produced; the world-state behind them is not recorded.

## Consequences

**Easier:** every future run states its own base engine; the §8 backlog is
enumerated with `file:line` and a probable single cause; the B/D distinction is
explicit.

**Harder:** ops reports gain a field that reads as an alarm until B lands; runs
predating the guard cannot be retro-classified.

**To revisit:** whether `GUMASEngineV3` should inherit once a stable v2.0 base
exists; whether the `SIM_ENGINE_OUTPUTS/engine.py` shim should keep aliasing
`GUMASEngine` when a tactical base is available.

## Action items

1. [ ] Apply `skills/aurora-quantum-forge-ops/scripts/build_qforge_ops_report.py` (applied)
2. [ ] Decide strictness of `_delegate_mode == False`: fail-closed for report
       generation, warn for `validate_v3` (standalone by design)
3. [ ] Correct the `engine_v3_patch.py` docstring — it describes inheritance from
       a 15-phase base it does not have
4. [ ] Mark prior qforge reports unattributed
5. [x] ~~Test the single-cause hypothesis before scheduling 15 separate fixes~~ — **done 2026-08-19, refuted.** The v1 line is internally consistent; every defect is new in the v2.0 rewrite. Size the remediation at fifteen independent decisions.
6. [ ] Decide whether Option D is wanted at all before investing in B
7. [ ] Do not amend archival v2.0 source under any option

Engines were exercised only in an isolated container against copies. No archival
artifact was modified. The 13 `.pyc` were read, not executed.

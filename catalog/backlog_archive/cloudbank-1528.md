# aurora-cloudbank-symbolic#1528: feat(gumas): restore simulation-native RiverCycle pressure and feedback regulator

- URL: https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1528
- State at archive: open
- Author: AUo959
- Created: 2026-08-18T02:51:41Z
- Updated: 2026-08-18T03:06:01Z
- Labels: backlog
- Milestone: none

## Linked pull requests (head SHA at archive time)

- aurora-cloudbank-symbolic#1343 — feat: add the triggered Narrative River scene workflow — merged — `agent/narrative-river-adapter-spec` @ `24d2b3f396eb3d338abd24e7156352b4d7987bdb`

## Branches named in the issue

- none

## Original body

## Lineage

Focused salvage/recovery follow-up related to:

- #1526 — provenance-aware corpus archaeology and intent recovery;
- merged Narrative River workflow #1343 / current `modules/narrative_river/`;
- `docs/specs/GUMAS__SPEC__NARRATIVE_RIVER_ADAPTER__v0.1__2026-07-26.md`;
- current L1 `RIVERTHREAD_808` relay/continuity surfaces;
- legacy `src/nodes/riverthread_processor.js`;
- GUMAS deterministic simulation and current L1/L2/L3 authority boundaries.

## Recovered design lineage

RiverThread/RiverThread808 began as a continuity-flow concept and later became a named L1 relay/continuity system. By 2026, the design had evolved further into **RiverCycle**, with RiverThread808 acting as regulator/interface rather than the medium itself.

The current Narrative River specification preserves a crucial architectural clue. It explicitly identifies a related artifact:

> `Aurora RiverCycle + RiverThread808 + GUMAS Social Pressure Regulator v0.5.0-alpha`

and defines its own primary function as:

> **Translate persistent RiverCycle state into scene-level causal constraints for prose generation and revision.**

That means Narrative River is downstream of RiverCycle by design. It is not evidence that the simulation-native RiverCycle state provider has been replaced.

The same specification defines durable RiverCycle-derived concepts including:

- flows with source, target, carrier, strength/significance, provenance, and state;
- pressures that narrow choices without determining responses;
- sediment as unresolved residue;
- reservoirs that absorb or delay pressure rather than erase it;
- turbulence that distorts channels;
- nutrients as useful capacity produced by events;
- salmon returns as downstream results that alter the originating system;
- actor-specific interpretation of pressure;
- relationship and institutional residue;
- evidence uncertainty;
- scarcity and equipment constraints;
- required downstream effects.

## Current implementation state

### Strong descendant: Narrative River

`modules/narrative_river/` is a real, operator-triggered, durable scene-continuity implementation. It provides:

- strict Pydantic contracts;
- provenance-bearing flows and evidence claims;
- pressures, sediment, reservoirs, turbulence/channel conditions;
- actor interpretations and relationship state;
- scarcity/equipment/institutional constraints;
- scene deltas;
- manifest-backed storage with SHA-256 integrity;
- advisory validation;
- explicit CLI triggering;
- fail-closed scene advancement;
- no automatic prose rewrite;
- no simulation mutation;
- no CanonRec promotion.

This should be preserved as the narrative projection/adapter.

### Current RiverThread808 surfaces

Current main also contains:

- `config/mesh/agents/riverthread_808.json`, identifying RIVERTHREAD_808 as deterministic and continuity-oriented;
- L1 relay residency in the current layer architecture;
- `src/nodes/riverthread_processor.js`, an older narrative/temporal processor still instantiated by `src/system/agent_synchronizer.js`.

The old processor is valuable lineage evidence, but should **not** automatically become the RiverCycle implementation target. It includes older assumptions and behaviors that require reconciliation, including nondeterministic stream IDs (`Math.random()`), automatic temporal-correction paths, legacy layer/agent terminology, and scalar coherence heuristics. Those properties do not match the later Phase-1 direction of additive, observable, deterministic, non-mutating regulation.

### Gap found in this pass

Targeted current-repo searches did **not** locate a simulation-native RiverCycle / GUMAS social-pressure state engine corresponding to the upstream state source assumed by the Narrative River spec. No `SocialPressureState` or equivalent RiverCycle provider was found in this pass.

Therefore the current lineage appears to be:

```text
legacy RiverThread continuity/narrative flow
        ↓
RIVERTHREAD_808 L1 relay / regulator identity
        ├── older riverthread_processor.js
        │
        └── RiverCycle design: persistent medium / pressure-feedback state
                        ↓
             [simulation-native provider gap]
                        ↓
             Narrative River Adapter
                        ↓
               narrative scene frames
```

This issue exists to restore the missing simulation-native layer without collapsing the other descendants into it.

## Governance direction

The recovered 2026 Phase-1 direction is additive and non-mutating:

> observe → classify → route

RiverCycle/RiverThread808 must not force peace, escalation, reconciliation, tragedy, canon changes, or hidden state mutation. Pressure alters conditions and available choices; it does not author outcomes.

Initial implementation therefore should be **diagnostic/state-producing**, not an autonomous controller.

## Architectural separation

```text
GUMAS simulation/world events
        ↓
RiverCycle state engine
  - derive/track flows
  - pressures
  - sediment
  - reservoirs
  - turbulence
  - nutrients
  - feedback/salmon returns
        ↓
RiverThread808 regulator/projection
        ├── observability / routing
        ├── diagnostics
        └── narrative projection
                  ↓
          Narrative River Adapter
```

Responsibilities must remain separate:

- **GUMAS** owns simulation causality and deterministic world-state transitions.
- **RiverCycle** represents/derives persistent flow-pressure-feedback state.
- **RiverThread808** regulates, observes, classifies, and routes that state through governed interfaces.
- **Narrative River** translates approved/persistent RiverCycle/GUMAS state into scene constraints.
- **CanonRec** remains canon authority.

## Phase 0 — compatibility and lineage report

Before implementation, produce a read-only reconciliation covering:

1. `src/nodes/riverthread_processor.js` and its live imports;
2. `config/mesh/agents/riverthread_808.json`;
3. `.aurora/relays/RIVERTHREAD_808_LIVE_RELAY_v1.json`;
4. current layer/residency authority docs;
5. `modules/narrative_river/` contracts;
6. GUMAS event/state surfaces that could provide upstream input;
7. any recovered RiverCycle/social-pressure artifacts not currently present in main.

Classify each behavior as preserve, adapt, deprecate-with-lineage, or unresolved. Do not delete legacy RiverThread surfaces merely because a newer model exists.

## Phase 1 — passive deterministic RiverCycle state

Names below are provisional. The implementation should define a typed, deterministic state/receipt contract representing concepts needed by downstream consumers without changing GUMAS outcomes.

A minimal state may include independent collections such as:

```yaml
rivercycle_state:
  schema_version: string
  state_id: string
  simulation_ref: string
  turn_or_tick: integer | string
  provenance: []
  flows: []
  pressures: []
  sediment: []
  reservoirs: []
  channel_conditions: []
  nutrients: []
  feedback_returns: []
  actor_interpretations: []
  unresolved_questions: []
  source_state_hash: string | null
```

Do not force these exact names if existing GUMAS schemas suggest a cleaner mapping.

### Determinism

For fixed GUMAS state/event inputs and configuration, the RiverCycle projection must be reproducible. IDs must be deterministic/content- or context-derived rather than timestamp/random dependent where replay equivalence matters.

### Provenance

Every derived pressure/flow/feedback item must identify the event/state evidence from which it was derived. A numeric score cannot become unexplained objective truth.

### Non-mutation

Phase 1 must not:

- mutate GUMAS world state;
- mutate Narrative River state automatically;
- alter canon;
- force actor responses;
- generate hidden events;
- autonomously resolve sediment/disputes;
- rewrite legacy RiverThread records.

## Feedback / salmon-return contract

A downstream consequence that affects an originating institution, doctrine, actor, or system should be representable as a **feedback return** with provenance.

The representation should distinguish:

1. observed downstream outcome;
2. candidate upstream implication;
3. approved/actual upstream state change.

A feedback candidate does not mutate its origin merely because RiverCycle detected it.

This distinction preserves the original learning-feedback intent without creating a hidden controller.

## Reservoir semantics

Reservoirs delay, absorb, buffer, or redirect pressure. They do not erase causal state.

Examples at the abstract schema level may include institutional process, reserve capacity, trusted relationships, cultural practices, command discipline, legal review, or logistics reserves. The engine should not hard-code narrative examples into generic simulation logic.

## Relationship to Narrative River

Narrative River should consume a **projection** of RiverCycle state through an explicit adapter rather than reimplement RiverCycle calculations internally.

The existing Narrative River models can guide compatibility, but the upstream RiverCycle schema should remain useful without prose generation.

Expected future flow:

```text
RiverCycleState
     ↓ explicit projection
NarrativeRiverFrame
```

The projection must preserve provenance, evidence status, unresolved state, and persistence class where relevant.

## Legacy RiverThread reconciliation

`src/nodes/riverthread_processor.js` should receive focused review before any new engine is wired to it. At minimum assess:

- current production consumers;
- deterministic replay compatibility;
- automatic correction behavior;
- layer/residency terminology;
- memory-sovereignty logic relative to #1527;
- continuity scoring semantics;
- status/deployment claims;
- unreachable/ordering-sensitive threshold logic;
- whether it should become a compatibility adapter, be narrowed, or remain historical implementation.

No destructive cleanup in the first PR.

## Acceptance criteria

- [ ] A read-only lineage/compatibility report identifies current RiverThread/RiverCycle/Narrative River ownership boundaries.
- [ ] Narrative River remains the downstream narrative adapter and is not duplicated.
- [ ] RIVERTHREAD_808 remains an L1 relay/regulator identity consistent with current layer authority.
- [ ] A simulation-native RiverCycle state contract exists independently of prose/narrative output.
- [ ] Fixed inputs produce deterministic RiverCycle output under the declared equivalence contract.
- [ ] Every derived flow/pressure/feedback record retains source provenance.
- [ ] Pressure constrains possibility but does not prescribe actor response or plot outcome.
- [ ] Reservoirs buffer/delay/redirect pressure rather than deleting causality.
- [ ] Sediment persists until evidence/state explicitly resolves or supersedes it.
- [ ] Feedback/salmon-return candidates distinguish observation, proposed implication, and approved upstream mutation.
- [ ] Phase 1 performs no GUMAS, canon, or narrative mutation.
- [ ] No hidden narrator or forced peace/escalation mechanism is introduced.
- [ ] Legacy `riverthread_processor.js` is reconciled before new live wiring; no silent deletion.
- [ ] Narrative River can consume a versioned RiverCycle projection without losing provenance/evidence boundaries.
- [ ] Focused tests cover determinism, provenance, unresolved sediment, reservoir behavior, feedback candidates, and no-mutation guarantees.

## Non-goals

- replacing GUMAS;
- replacing Narrative River;
- authoring plot outcomes;
- forcing emotional responses;
- automatic canon promotion;
- autonomous conflict resolution;
- hidden memory mutation;
- literalizing RiverCycle metaphors as in-world physics;
- rewriting all legacy RiverThread code in the first phase.

## Design principle

**The river carries consequence; it does not choose the destination.**


## Comments (0)

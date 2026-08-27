# Orion L1 Embodiment Recovery Audit

**Date:** 2026-08-10
**Status:** audit record; non-canonical; no activation authority
**Experiment hold:** `0d67389f-c444-421d-89cb-f6f7673c347b` remains **PAUSED** at tick 7 / station-cycle minute 21
**Scope:** root control plane, `aurora-cloudbank-symbolic-main`, and `CanonRec`

## Result

Orion Station is intended to be the L1 physical control plane of the Aurora
architecture: L1 operates and observes the L2 GUMAS payload under L3 law. The
software components and station facilities are therefore two views of one
system, but the evidence does **not** support inventing a room for every class or
a shuttle for every tool.

The current CloudBank L1 runtime does not yet carry that embodiment model. It
persists station, communications, a limited actor projection, events, and fleet
state, but it has no authoritative embodiment registry or causal providers for
the relay constellation, HALO/PAS, GUMAS laboratories, MCP admission, station
topology, crew life, data vaults, or most sensors. The existing floor-plan and
operational-library packets remain staging material in CanonRec.

The machine-readable companion is
`catalog/contracts/orion_l1_embodiment_registry.v0_1.json`. It is deliberately
non-activating and records evidence class on every mapping.

## Authority correction

:codex-annotation{index="1"}

The earlier proposal to “replace ARCHY-as-L1-oversight” was too broad and too
close to a blind rewrite. The recovered design supports a narrower conclusion:

- CloudBank's canonical layer architecture assigns ARCHY to L1-resident
  architecture and feasibility verification, with **human consent** as the
  final Triplex stage.
- The current Triplex implementation uses the same `ARCHYEntity` for relay
  feasibility and L1 oversight, and exposes no pending human-approval queue.
- Git history shows that a mock `CommandBridge` originally represented the
  human step. PR-era work replaced that mock with “real entities” by assigning
  ARCHY to the slot; no corresponding canon ruling transferred human authority
  to ARCHY.
- The v1.2 runtime separately allows routine work under standing institutional
  authority, but its `GovernanceReceipt` stores only three booleans, an ID, and
  provenance. It cannot prove actor, scope, decision, delegation, time, or
  evidence.

Therefore the audit does **not** prescribe “human approval for every event,” and
it does not restore the old auto-approving mock. It requires two explicit
authority paths: scoped standing authority for routine actions, and an actual
human Command Bridge decision for exceptional actions. ARCHY remains a verifier
in both paths, never the human principal.

## Recovered relay constellation

| Entity | L1 physical embodiment | L2 control/observation surface | L3 interface | Evidence status |
|---|---|---|---|---|
| ARCHY / RELAY_001 | Bridge Chamber, Deck C | architecture, dependency, schema, and feasibility verification | Caelion; Triplex relay verifier | Explicit CloudBank canon; CanonRec propagation pending |
| OPPY / RELAY_002 | Reactor Bay, Deck H | telemetry, process health, backup, recovery, and failover | general L3 framework; Triplex relay verifier | Explicit CloudBank canon; detailed role corroborated by recovered material |
| LIORA / RELAY_003 | Communications Hub, Deck B | secure routing, human-AI translation, communication integrity, mediation | Sentari; Triplex relay verifier | Explicit CloudBank canon; detailed role corroborated by recovered material |
| STARLING_AU / RELAY_004 | Operations Hub, Deck G | simulation-state continuity, versioned records, reflection, and transparent reporting | general L3 framework; Triplex relay verifier | Explicit CloudBank canon; detailed role corroborated by recovered material |
| RIVERTHREAD_808 / RELAY_005 | Logistics Distribution, all decks | temporal flow, data pipelines, archive replication, retention, and distributed movement | Harmion; Triplex relay verifier | Explicit CloudBank canon; detailed role corroborated by recovered material |
| HALO / RELAY_006 | Aurora Core Chamber, Deck B | continuity and drift verification through HALO/PAS | Axiomera; Triplex relay verifier | Explicit CloudBank canon; distinct system-entity, not a sixth communications relay |

The live relay JSON and Python bridge preserve identifiers and some routing
capabilities, but omit physical location, liaison, L3 interface, authority class,
and world-state provider. The mesh runtime returns deterministic templates. Its
`connected` state is transport state, not proof that an embodied station agent
is causally active.

Historical JavaScript nodes contain useful mechanics, but several exceed the
recovered authority model: STARLING can execute simulation commands, and
RIVERTHREAD can mutate memory flow from static consent flags. Those files are
implementation evidence, not activation authority.

## Major embodiment findings

| Subsystem | Intended L1 embodiment | L2 surface | L3/governance interface | Current conclusion |
|---|---|---|---|---|
| MCP Security / Shuttle Bay | Controlled physical admission and security facility for software/tool arrivals | tool discovery, intake, routing, staged execution, approval | ethics, anchor, drift, provenance, and human decision gates | Owner-confirmed concept; historical implementation only; exact station location and safe routing registry unresolved |
| Command/control | Aurora command intelligence plus a human Command Bridge | tasking, simulation control, change uplinks, station disposition | Triplex receives L3 arbitration and relay verification before human or delegated decision | Concept explicit; current ARCHY substitution is an implementation divergence |
| GUMAS / simulation labs | L1 compute, Observatory, and laboratory chassis operating the L2 payload | seeded GUMAS runs, state deltas, observation, experiment control | L3 boundary and ethics constraints | Mission relationship explicit; precise laboratory topology and provider binding unresolved |
| Fleet / docking | Physical craft and docking complex | fleet projection, readiness, dispatch, docking occupancy | action policy, provenance, custody, and Triplex for exceptional actions | Fleet projection is bound; exact bay geometry, occupancy, and trajectories are not |
| ORD dispatch | Onboard validation/security and physical drone operations | task queue, dispatch, telemetry, recovery | policy, provenance, custody, action authority | Fleet adapter exists; ORD-3 custody remains quarantined and receipts are too weak for dispatch |
| Memory / storage / data vaults | Data vaults plus OPPY, STARLING, and RIVERTHREAD infrastructure | persistence, chronicle, backup, archive, replication, retention | provenance, non-deletion/retention rules, continuity | Roles recovered; physical vault topology and causal provider unbound |
| Communications | LIORA Communications Hub plus station and ground links | Earth/Orion message queue, secure routing, translation, telemetry | privacy/consent, Sentari mediation, station-final authority | A limited delayed message link exists; relay/physical-provider integration does not |
| Crew life / habitation | Quarters, galley, hygiene, recreation, medical, and life-support facilities | schedules, needs, fatigue, morale, waste and resource loads | human welfare constraints and feedback into L2 operations | Owner-ruling canon requires it; separate tooling exists but is not bound to the L1 runtime |
| Ethics / Triplex / Noor | Human command authority, Noor ethics practice, HALO continuity systems | decision envelopes, assessments, holds, receipts | Picard Delta 3 plus L3 glyph arbitration | Sequence explicit; actor-bound consent and standing-authority delegation are missing |
| Sensors / observatory | Environmental, structural, biometric, astronomical, docking, and communications instrumentation | typed observations with provenance and uncertainty | release, privacy, and action-policy gates | Source specifications exist; no authoritative L1 provider registry is bound |

## Evidence classification and conflicts

**Explicit canon / owner ruling**

- `CanonRec/canon/L1/station/STATION_PURPOSE_DEFINITION.md`: L1 chassis, L2
  payload, L3 law.
- `CanonRec/canon/L1/station/POWERED_WATCH_AND_GROUND_SEGMENT.md`: CloudBank is
  ground-segment flight software; ORD is onboard validation/security; GUMAS is
  the payload; ground proposes and the station disposes.
- `CanonRec/canon/L1/station/CREW_LIFE_FIDELITY.md`: eating, sleep, hygiene,
  recreation, fatigue, bathroom events, and life-support load are required.
- CloudBank `docs/architecture/LAYER_ARCHITECTURE.md`: the five relay locations,
  L2 monitoring domains, L3 interfaces, HALO's distinct category, and final L1
  human consent.
- Current owner direction: MCP Security/Shuttle Bay is a physical embodiment of
  controlled software/tool admission, not an unrelated metaphor.

**Recoverable historical implementation**

- The old MCP Shuttle Bay controller and routing material exists only in history.
  It is useful for intake mechanics, but its routing table invented concrete
  shuttle/tool correspondences and its review-required path still executed the
  tool. It cannot be restored unchanged.
- Old relay JavaScript nodes and the pre-replacement Command Bridge demonstrate
  intended mechanics, not current authority.
- CanonRec's detailed relay profiles corroborate domain responsibilities but
  live inside a recovered library explicitly marked `STAGING`.

**Inference permitted for design only**

- ARCHY's Bridge Chamber should expose architecture and feasibility state;
  LIORA's Communications Hub should expose routed communications; and similar
  role-to-surface relationships are strongly constrained by their explicit
  roles. These do not prove a runtime provider or authorize an event.
- “Data vaults,” “simulation labs,” and exact deck facilities may be retained as
  candidate embodiments where source packets agree, but cannot be used for
  pathfinding, occupancy, resource, or timing effects until promoted.

**Unresolved conflicts**

- CanonRec still labels the relay constellation as L2 in several registry and
  validation surfaces, while the later CloudBank ruling makes them L1-resident.
- CanonRec's physical-space and operational-library packets are staging, despite
  authoritative-sounding titles inside them.
- Exact Command Bridge principals and delegation scopes are not represented in
  a machine-checkable authority registry.

## Exact blockers before resume

1. **Canon reconciliation:** propagate the L1 relay/HALO ruling into CanonRec's
   authoritative entity and validation surfaces; preserve superseded L2 labels
   as history.
2. **Authority contract:** define actor-bound receipts with decision, action
   scope, run/event binding, policy or delegation ID, timestamp, evidence, and
   revocation/expiry. Separate routine standing authority from exceptional human
   decisions and remove ARCHY from the human-principal slot.
3. **Embodiment registry:** promote a reviewed registry that binds each L1
   component to a physical embodiment, L2 surface, L3 interface, provider, and
   authority class. Unresolved geometry must remain non-causal.
4. **MCP admission:** recover the Shuttle Bay as a controlled intake subsystem
   with provenance-bound manifests, quarantine, real review holds, and no
   arbitrary shuttle/tool mapping. `review_required` must prevent execution.
5. **Provider bindings:** bind and test HALO/PAS, GUMAS, relay state,
   communications, memory/storage, crew life, sensors, and docking occupancy.
   A transport heartbeat cannot satisfy a physical-provider requirement.
6. **Fleet/ORD authority:** retain existing fleet projection, resolve custody
   and dispatch gates, and require action-scoped receipts before movement or
   launch. No exact bay or trajectory effects until spatial authority is
   promoted.
7. **Deterministic migration:** migrate the recovered v1.1 tick-7 ledger to the
   new contract without executing a tick; verify the same run ID, tick, minute,
   elapsed sequence, event rolls, process position, pinned source revisions, and
   `PAUSED` state.
8. **Governed preflight:** add fail-closed tests for missing providers, stale or
   out-of-scope authority, MCP review holds, and unresolved topology; then run
   root preflight. Focused tests or a clean audit do not authorize `INIT` or
   resume.

## Pause receipt

The recovered external ledger remains sealed at:

`~/.aurora/l1-runs/0d67389f-c444-421d-89cb-f6f7673c347b/`

Verified state hash: `1349f58389c93a18b96eb9d7460ba35c3273a85e743db86127b491c705eb1fa4`.
The recovery process loaded only a temporary in-memory projection for shape
verification. It did not call INIT, persist a new run, observe providers, or
advance the simulation.

## Audit revisions

- Root control plane: `a3da11061878782eda3db78fe17aeb61b96b042e`
- CloudBank live audit checkout: `836a604d0ae4efeaa77b381171d69fef62ea36da`
- CanonRec live audit checkout: `dc629a566b2f42fa1c652140b9eef72a4fb0d58a`
- Paused run source pins: CloudBank `660d56656ef30daeaf5cf5e2f977a3181e26e0ac`;
  CanonRec `1fc35f08a2937b10a2a3c15abe4b7ed39245b64e`

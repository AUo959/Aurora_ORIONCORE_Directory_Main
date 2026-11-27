# aurora-cloudbank-symbolic#1469: research: refine canon-grounded GUMAS pressure and recovery dynamics

- URL: https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1469
- State at archive: open
- Author: AUo959
- Created: 2026-08-08T12:57:30Z
- Updated: 2026-09-08T09:14:38Z
- Labels: documentation, simulation, architecture, stale, follow-up, canon
- Milestone: none

## Linked pull requests (head SHA at archive time)

- none

## Branches named in the issue

- none

## Original body

## Purpose

Define a canon-grounded refinement layer for GUMAS social and narrative dynamics so that pressure, consequence, adaptation, and recovery emerge from explicit system rules rather than author intervention.

The goal is **not** to make simulations peaceful or to optimize them toward a preferred story. The goal is to represent lawful recovery pathways while preserving faction agency, scarcity, doctrine, logistics, institutional memory, and consequence.

**Depends on:** #1466, #1467, and the learner-boundary decisions from #1468.

## Scope

Research and specify:

- social-pressure state and propagation;
- logistics, scarcity, institutional capacity, and doctrine constraints;
- institutional-memory effects with explicit provenance and decay/retention rules;
- recovery gradients and competing recovery strategies;
- attractor states as measurable model behavior, not predetermined destinations;
- agent/faction decision autonomy under pressure;
- causal and observational boundaries between GUMAS state and RiverCycle diagnostics;
- deterministic scenario fixtures for crisis, adaptation, partial recovery, failure, and relapse;
- measures for emergent behavior, sensitivity, calibration, and unintended outcome forcing;
- canon/source traceability for every rule proposed for implementation.

Use RiverCycle only as a passive measurement surface. Learner outputs may be evaluated against these scenarios later, but may not define canon or change the scenarios in this phase.

## Canon and authority boundary

- CloudBank may model approved canon and record implementation proposals.
- CanonRec remains the authority for canon promotion and reconciliation.
- Existing conflicts and quarantines, including #1456, remain unresolved unless handled through their own authority path.
- Simulation output, derived metrics, and learner hypotheses remain non-canonical until separately reviewed and promoted.
- Narrative principles must be translated into inspectable rules, assumptions, and tests before they can govern runtime behavior.

## Non-goals and boundaries

Do **not**:

- override faction or character agency;
- force cooperation, peace, collapse, conflict, or any preferred outcome;
- inject deus-ex-machina events or operator-centered plot;
- treat coherence, entropy, recovery, or attractor scores as moral truth;
- let observation or Pilot attention change event probability;
- change the active experiment, write runtime memory, or promote simulated facts into canon;
- use the learner as an active policy or reward source;
- modify the Aurora root control plane or authoritative CanonRec repository in this issue;
- bundle unrelated character, orbital-locus, staffing, or identity reconciliation.

Any runtime behavior change must land through a separately reviewable implementation PR with deterministic tests and rollback.

## Deliverables

- a source/authority matrix for proposed dynamics;
- a versioned pressure/recovery model specification;
- explicit formulas, units, state variables, assumptions, and unknown handling;
- deterministic scenario fixtures and expected invariants;
- a RiverCycle-based observation/evaluation plan;
- an analysis of agency preservation and outcome-forcing risks;
- a scoped implementation plan separating docs, schemas, runtime changes, and canon proposals.

## Acceptance criteria

- [ ] Every proposed dynamic traces to canon, an approved design source, or is labeled as a hypothesis.
- [ ] Faction and character agency invariants are explicit and testable.
- [ ] No outcome is directly forced by a coherence or recovery target.
- [ ] Deterministic seeds remain reproducible.
- [ ] Identical inputs can be compared without observer or learner interference.
- [ ] Pressure and recovery behavior is measurable through passive RiverCycle telemetry.
- [ ] Scenario fixtures cover successful recovery, partial recovery, failure, relapse, and conflicting stakeholder strategies.
- [ ] Unknown or quarantined canon inputs cannot silently become causal parameters.
- [ ] Proposed canon changes are separated into the CanonRec authority process.
- [ ] Runtime implementation is decomposed into scoped follow-up PRs with tests and rollback.

## Sequence

**Phase 3.** Begin after #1468 fixes the learner's authority and feedback boundaries. Complete this refinement before any larger learner-in-the-loop or adaptive Orion experiment.

## Comments (1)

### github-actions[bot] — 2026-09-08T09:14:37Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1469#issuecomment-5582446083>

This issue has been automatically marked as stale because it has not had activity for 30 days. It will be archived if no further activity occurs.

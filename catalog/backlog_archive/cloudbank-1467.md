# aurora-cloudbank-symbolic#1467: feat: implement RiverCycle Phase 1 passive diagnostics

- URL: https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1467
- State at archive: open
- Author: AUo959
- Created: 2026-08-08T12:56:22Z
- Updated: 2026-09-08T09:14:42Z
- Labels: enhancement, simulation, architecture, stale, phase-1, implementation-needed
- Milestone: none

## Linked pull requests (head SHA at archive time)

- none

## Branches named in the issue

- none

## Original body

## Purpose

Implement the first RiverCycle slice as a **passive, read-only observation layer** over the existing GUMAS/L1 simulation substrate.

RiverCycle Phase 1 measures flow, pressure, entropy, coherence, and recovery signals. It must not become a control loop or a second simulation authority.

**Depends on:** #1466

## Scope

Define and implement the minimum diagnostic model for:

- `RiverMediumFrame`;
- `RiverPacket`;
- `RiverChannel`;
- `RiverNutrient`;
- `RiverDecisionLog`;
- a `RIVERTHREAD_808` regulation/observation frame;
- GUMAS flow projections derived from existing state;
- social-pressure diagnostics derived from observable simulation facts;
- versioned entropy, coherence, and recovery formulas;
- a versioned JSON telemetry/export schema;
- deterministic fixtures and serialization tests.

All types and formulas must have explicit units, ranges, missing-data behavior, provenance, and version identifiers. A metric is an instrument reading, not a canon fact or governance decision.

## Integration contract

RiverCycle may:

- read approved run-state and event surfaces;
- compute derived diagnostics;
- emit run-scoped telemetry;
- expose inspection/export interfaces;
- support later evaluation design.

RiverCycle must:

- remain downstream of authoritative simulation state;
- avoid consuming or changing the simulation's shared random-number stream;
- preserve event ordering and authoritative outputs;
- fail observably when required inputs are absent;
- label derived, inferred, and directly observed values distinctly.

## Non-goals and boundaries

Do **not**:

- alter simulation outcomes, probabilities, schedules, agent choices, or faction behavior;
- inject events, interventions, rewards, penalties, or recovery behavior;
- reroute execution paths or communications;
- write memory or mutate canonical records;
- promote telemetry into CanonRec;
- introduce a learner, training loop, optimizer, or self-modification path;
- claim that a coherence score is an ethical ruling or objective truth;
- modify the Aurora root control plane or the authoritative CanonRec repository in this issue.

Any future active regulation requires a separate proposal, safety review, and explicit authorization.

## Acceptance criteria

- [ ] RiverCycle data types and JSON schema are versioned and documented.
- [ ] Formula definitions include units, ranges, provenance, and edge-case behavior.
- [ ] Passive telemetry export works against deterministic fixtures.
- [ ] Serialization and round-trip tests pass.
- [ ] Identical seeds produce identical authoritative GUMAS/L1 outputs with RiverCycle disabled and enabled.
- [ ] RiverCycle does not consume the simulation's shared RNG or change event ordering.
- [ ] Existing GUMAS and L1 validation remains unchanged and green.
- [ ] Missing or quarantined inputs produce explicit unknown/unavailable values rather than fabricated metrics.
- [ ] Telemetry remains run-scoped and cannot silently write memory or canon.
- [ ] Performance overhead is measured and recorded.
- [ ] Documentation states that Phase 1 is diagnostic-only.

## Sequence

**Phase 1.** Start only after #1466 establishes and validates the merged baseline. This issue must complete before the native learner foundation can rely on RiverCycle as an observation/evaluation surface.

## Comments (1)

### github-actions[bot] — 2026-09-08T09:14:41Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1467#issuecomment-5582447362>

This issue has been automatically marked as stale because it has not had activity for 30 days. It will be archived if no further activity occurs.

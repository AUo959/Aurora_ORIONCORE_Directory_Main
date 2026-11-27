# aurora-cloudbank-symbolic#1468: research: define the Aurora native learner foundation

- URL: https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1468
- State at archive: open
- Author: AUo959
- Created: 2026-08-08T12:56:54Z
- Updated: 2026-09-08T09:14:40Z
- Labels: needs-triage, simulation, architecture, stale, ethics, follow-up
- Milestone: none

## Linked pull requests (head SHA at archive time)

- none

## Branches named in the issue

- none

## Original body

## Purpose

Turn the native-learner discussion into a constrained, reviewable minimum architecture for Aurora.

The first learner is intended to be **small, specialized, measurable, and trained only on explicitly approved Aurora-native artifacts**. It is not a general-purpose model and this issue does not authorize training or deployment.

**Depends on:** #1466 and the stable diagnostic contract from #1467.

## Related architecture boundary

Before defining a new learner contract, inventory any existing Aurora State Model, QGIA/QSFE, world-state/belief-state, and deterministic-validator design artifacts available in the canonical root workspace.

- Reuse, reconcile, or explicitly supersede prior contracts; do not create a parallel learner/state-model authority in CloudBank.
- Treat unpublished drafts as prior art, not canon or implemented capability.
- Keep root control-plane contract changes in a separate root-repository issue/PR.
- Record any cross-repository dependency by exact path, revision, authority, and promotion status.

## Research questions

Define:

- one narrow learning objective and the operational decision it is meant to support;
- approved corpus boundaries, provenance requirements, licensing/privacy checks, exclusions, and versioning;
- the distinction between canonical sources, run-scoped simulation data, telemetry, generated artifacts, and rejected/quarantined material;
- baseline methods and success/failure metrics;
- a deterministic evaluation harness and held-out test strategy;
- the read-only RiverCycle telemetry interface used for observation/evaluation;
- memory input/output contracts without granting canonical-write authority;
- the feedback-loop boundary for an initial offline experiment;
- failure containment, rollback, audit receipts, and stop conditions;
- Picard_Delta_3/ethics constraints and human review gates;
- compute, storage, reproducibility, and model/version-record requirements.

## Minimum architecture constraints

The proposal must preserve:

- Git/approved canonical files as implementation authority;
- CanonRec as the canon authority rather than treating learner output as canon;
- separation between L1 runtime state, L2/GUMAS simulation, L3 symbolic/continuity surfaces, and training artifacts;
- a one-way observation path for the first experiment: approved artifacts and RiverCycle telemetry may inform evaluation, but learner output may not alter the active run;
- explicit provenance for every training and evaluation item;
- reproducible runs with pinned code, data, configuration, and seed.

## Non-goals and boundaries

Do **not** in this issue:

- train, fine-tune, deploy, or activate a model;
- design an Aurora AGI or general-purpose assistant;
- grant autonomous execution, governance, adjudication, or canon-promotion authority;
- create uncontrolled self-modification, recursive training, or online learning paths;
- write learner conclusions into memory, canon, or live simulation state;
- use conversation exports, recovered archives, simulated facts, or synthetic telemetry as canonical truth;
- let RiverCycle scores become rewards that influence the same run being measured;
- modify the Aurora root control plane or authoritative CanonRec repository.

Training, deployment, online feedback, and any active simulation integration require separate issues and explicit approval after this foundation is reviewed.

## Deliverables

- a minimum learner architecture decision record;
- a versioned corpus/data manifest schema;
- an inclusion/exclusion and provenance policy;
- a baseline/evaluation plan with measurable thresholds;
- a contained input/output and memory-interface contract;
- a threat/failure analysis with stop conditions;
- a proposed offline experiment protocol using frozen inputs;
- an evidence-backed go/no-go recommendation for a separately authorized training issue.

## Acceptance criteria

- [ ] One narrow training objective and intended user/system benefit are defined.
- [ ] Approved and excluded dataset sources are identified with authority and provenance.
- [ ] Canonical, simulated, derived, generated, and quarantined data are machine-distinguishable.
- [ ] Baselines, metrics, held-out evaluation, and failure thresholds are specified.
- [ ] The evaluation harness design is deterministic and reproducible.
- [ ] RiverCycle is consumed only as a read-only observation/evaluation surface.
- [ ] No uncontrolled self-modification or online feedback path exists.
- [ ] Learner output has no direct memory, canon, runtime, or governance write authority.
- [ ] Ethics, privacy, security, rollback, and human review gates are explicit.
- [ ] A separate training issue is proposed only if the design passes review.

## Sequence

**Phase 2.** Begin after #1467 has a stable passive telemetry schema and has demonstrated non-interference. Complete this design gate before any learner training or learner-in-the-loop experiment.

## Comments (1)

### github-actions[bot] — 2026-09-08T09:14:39Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1468#issuecomment-5582446588>

This issue has been automatically marked as stale because it has not had activity for 30 days. It will be archived if no further activity occurs.

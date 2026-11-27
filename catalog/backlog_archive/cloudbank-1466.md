# aurora-cloudbank-symbolic#1466: chore: establish the post-#1461 experiment baseline and rerun preflight

- URL: https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1466
- State at archive: open
- Author: AUo959
- Created: 2026-08-08T12:55:52Z
- Updated: 2026-09-08T09:14:44Z
- Labels: maintenance, ci, tests, high-priority, stale, follow-up
- Milestone: none

## Linked pull requests (head SHA at archive time)

- aurora-cloudbank-symbolic#1461 — feat(l1): clear Orion preflight bootstrap blockers — merged — `agent/l1-preflight-alignment` @ `af4f23273f924a1c099057271b1bf870a7d2374d`

## Branches named in the issue

- none

## Original body

## Purpose

Establish a reproducible Aurora CloudBank baseline after the L1 preflight blocker repair in #1461, then rerun preflight from the merged `main` state before any experiment begins.

This is **Phase 0** of the next experiment program. It is a release-readiness and evidence-capture task, not a feature phase.

## Current evidence

As of 2026-08-08:

- #1461 is the candidate baseline PR at head `46cd669f2e638e223a4d497ac9c4119d63fc27a6`;
- the exact-head repository and protected-branch checks were reported green;
- the PR is still draft and unmerged;
- no L1 `INIT` has been issued and the experiment remains at tick 0;
- #1449 remains the governing L1 runtime workstream.

These are inputs to this issue, not permanent readiness claims. Re-verify them at execution time.

## Scope

- complete the required human review and merge-readiness checks for #1461;
- merge #1461 only through the repository's normal protected-branch process and explicit authorized action;
- identify the exact merged `main` commit that becomes the experiment baseline;
- allow post-merge workflows and branch protection to settle, then record their final state;
- validate from a clean checkout of the merged `main` revision;
- rerun the full repository validation path required by the L1 runtime contract;
- rerun the read-only L1 preflight and preserve its machine-readable receipt;
- record current warnings, quarantines, unresolved canon facts, tool versions, and the intended experiment seed/metrics without starting the run;
- propose a durable baseline tag or release marker, with creation handled only through a separately authorized publication action.

## Required validation evidence

At minimum, record:

- exact baseline commit SHA;
- full test-suite result;
- required CI and branch-protection result;
- safety, catastrophe-prevention, CodeQL, code-quality, OPAL2, Constellation, and selective-integration gate results applicable to the merged revision;
- output from `python .aurora/init_l1.py preflight`;
- confirmation that preflight reports `ready: true`, `blockers: []`, `tick: 0`, and `run_created: false`;
- current disposition of known quarantines, including #1456.

## Scope boundaries

- This issue does **not** itself authorize or perform the merge.
- Do not issue `INIT`, create a live run, or advance L1.
- Do not implement RiverCycle, a learner, or simulation-behavior changes here.
- Do not resolve unknown canon by convenience.
- Do not write to CanonRec or promote run state into canon.
- A green PR head is not sufficient evidence for a green merged `main`; both states must be recorded separately.

## Acceptance criteria

- [ ] #1461 is merged through an authorized protected-branch action.
- [ ] The exact merged `main` SHA is recorded as the candidate experiment baseline.
- [ ] Post-merge required workflows and branch protection are confirmed.
- [ ] Full repository validation passes on the baseline revision.
- [ ] Read-only L1 preflight passes with no run created and tick remaining 0.
- [ ] A reproducible preflight receipt records versions, commit SHAs, warnings, and quarantines.
- [ ] Any remaining blocker is linked to an owner decision or follow-up issue.
- [ ] Downstream experiment-phase issues reference this baseline and remain blocked until this gate closes.

## Sequence

**Phase 0 — mandatory gate.** RiverCycle Phase 1 follows only after this issue's acceptance criteria are satisfied.

## Program map

- [ ] #1466 — **Phase 0:** protected merge, stable baseline, and read-only preflight
- [ ] #1467 — **Phase 1:** RiverCycle passive diagnostics
- [ ] #1468 — **Phase 2:** native learner minimum architecture
- [ ] #1469 — **Phase 3:** canon-grounded GUMAS pressure/recovery refinement

**Critical path:** #1466 → #1467 → #1468 → #1469 → separately authorized experiment go/no-go.

Opening or closing a tracking issue does not itself authorize a merge, `INIT`, canon promotion, learner training, deployment, or an active feedback loop.

## Comments (1)

### github-actions[bot] — 2026-09-08T09:14:43Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1466#issuecomment-5582448086>

This issue has been automatically marked as stale because it has not had activity for 30 days. It will be archived if no further activity occurs.

# Aurora_ORIONCORE_Directory_Main#50: test(canon-ops): prove the end-to-end QGIA-to-CanonRec vertical slice

- URL: https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/issues/50
- State at archive: open
- Author: AUo959
- Created: 2026-07-28T02:20:56Z
- Updated: 2026-07-28T02:20:56Z
- Labels: none
- Milestone: none

## Linked pull requests (head SHA at archive time)

- none

## Branches named in the issue

- none

## Original body

## Parent

Part of #47 — Aurora Canon Operations Bridge.

Depends on:

- `AUo959/CanonRec#5` — contracts and validators.
- #48 — bridge service.
- #49 — deterministic GUMAS execution adapter.
- `AUo959/aurora-cloudbank-symbolic#1383` — mediated QGIA staging adapter.
- `AUo959/cloudbank-quantum-en#33` — review workspace.
- `AUo959/AuroraOS#10` — agent query and proposal tools.

## Purpose

Define and automate the first complete, evidence-bearing development slice across the constellation. This issue is the integration gate for the program, not a substitute for unit or contract tests in each repository.

## Fixture

Create one small, pinned, non-sensitive analytical fixture containing:

- QGIA forecast and evidence package;
- explicit assumptions and unknowns;
- L1 approval record selecting at least two scenario branches;
- CanonRec staging mutation and gate receipts;
- approved GUMAS scenario seeds;
- deterministic two-run replay per branch;
- output inventories and run receipts;
- one observed outcome and calibration record;
- read models for CloudBank and AuroraOS.

The fixture must be stable, synthetic or safely historical, and clearly labeled so it cannot be mistaken for a live intelligence task.

## Happy-path verification

1. Validate the QGIA package.
2. Record L1 mediation and approval.
3. Submit the CanonRec staging request.
4. Verify certainty remains `STAGING`.
5. Execute both approved scenario branches.
6. Replay each branch and compare semantic hashes.
7. Project bounded operational atoms into the Station Chronicle input surface.
8. Attach the outcome and calibration record.
9. Query the complete chain through CloudBank and AuroraOS.
10. Request—but do not perform—a CanonRec promotion review.

## Required negative tests

- direct QGIA-to-GUMAS dispatch;
- direct UI or agent request for `CANON` creation;
- altered source evidence after approval;
- reused request ID with changed content;
- stale expected-state token;
- missing approval receipt;
- cross-layer contamination;
- tampered run receipt;
- nondeterministic replay beyond declared limits;
- duplicate Chronicle projection;
- bridge unavailable in read-only mode;
- source record containing prompt-injection text.

## Evidence package

The integration run must emit:

- pinned repository refs and module versions;
- fixture manifest and hashes;
- request and receipt inventory;
- replay comparison report;
- invariant and layer-gate report;
- Chronicle projection receipt;
- CloudBank and AuroraOS query snapshots;
- explicit list of expected failures and observed outcomes;
- no claim of promotion readiness unless the promotion gate was separately run and approved.

## Acceptance criteria

- [ ] The happy path completes without manual file copying or hand-edited IDs.
- [ ] Identical replays match within the documented determinism contract.
- [ ] Every negative test fails at the intended boundary with a specific receipt or finding.
- [ ] The full chain is reconstructable from persisted artifacts.
- [ ] CloudBank and AuroraOS display the same CanonRec certainty, layer, source, and receipt information.
- [ ] No canonical file is modified during the integration test.
- [ ] The run can execute in a clean local environment from documented commands.
- [ ] CI can run a bounded version without external services.

## Exit gate

Close this issue only when the vertical slice is repeatable and the epic can point to one verified workflow rather than a collection of disconnected components.

## Comments (0)

# Aurora_ORIONCORE_Directory_Main#47: epic(canon-ops): connect QGIA, CanonRec, GUMAS, AuroraOS, and CloudBank

- URL: https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/issues/47
- State at archive: open
- Author: AUo959
- Created: 2026-07-28T02:17:13Z
- Updated: 2026-11-27T05:59:08Z
- Labels: none
- Milestone: none

## Linked pull requests (head SHA at archive time)

- Aurora_ORIONCORE_Directory_Main#120 — Query pinned CanonRec records through Canon Operations — merged — `codex/canon-ops-query` @ `6fa98e8d0f13cf55bb986161d3e32ad7e1645d07`
- Aurora_ORIONCORE_Directory_Main#121 — Journal authorized CanonRec staging requests — merged — `codex/canon-ops-intake` @ `1889ae0c84ffa9af5cb62c652562b8081237db97`
- Aurora_ORIONCORE_Directory_Main#123 — Complete pinned CanonRec reconciliation and record provenance — merged — `codex/canon-ops-reconciliation` @ `e955b5d053fd2d441ffa8a18b38bcf3542d5a6eb`
- Aurora_ORIONCORE_Directory_Main#125 — Execute approved GUMAS seeds with native run receipts — merged — `codex/canon-ops-gumas-execution` @ `a04e0f7859ce3973a2cb37b9c06c2adf34b24b87`
- Aurora_ORIONCORE_Directory_Main#126 — Expose authenticated local Canon Operations reads — merged — `codex/canon-operations-local-reader` @ `29ee4102e5a41fd469cc9bf30d0b56ae6c12a7bd`
- CanonRec#12 — Define and verify Canon Operations v1 contracts — merged — `codex/canon-ops-v1` @ `9d62e3b3369ced71997fb2f3944bcac9aea2d133`
- aurora-cloudbank-symbolic#1727 — Prepare L1-mediated QGIA staging requests for CanonRec — merged — `codex/cloudbank-issue-1383-mediated-canon-staging` @ `94ae82fc7447e4114c6a0b0936a633695bd2ac4b`

## Branches named in the issue

- none

## Original body

## Purpose

Move the Aurora Canon Operations Bridge from architecture into development as a thin ground-segment integration layer around CanonRec.

The target is one auditable workflow:

`QGIA evidence/forecast → L1 mediation and approval → CanonRec STAGING claims → approved GUMAS scenario seed → deterministic run receipt → Station Chronicle operational atom → outcome/calibration → optional CanonRec reconciliation`

## Canonical boundaries

- **CanonRec remains the SSOT** for L1/L2 canonical truth, certainty, drift, reconciliation, and promotion.
- **QGIA does not task L2 directly.** Inputs are mediated through L1 approval, consistent with `AUo959/aurora-cloudbank-symbolic#1124`.
- **GUMAS output is instance-local or operational by default.** It cannot overwrite L1 facts or self-promote into canon.
- **CloudBank and AuroraOS are clients, not truth authorities.** They may query and submit staged proposals but cannot lock canon.
- Every state transition must be receipt-bearing, deterministic where applicable, idempotent, and traceable to source artifacts.
- Existing continuity, registry, command, approval, and receipt work in `AUo959/aurora-cloudbank-symbolic#1368–#1380` should be reused rather than duplicated.

## Development sequence

### Phase 0 — Contract authority

- [x] `AUo959/CanonRec#5` — define `CanonQuery`, `MutationRequest`, and gate-receipt contracts. [Verified merge](https://github.com/AUo959/CanonRec/pull/12) · [Pinned v1 contract](https://github.com/AUo959/CanonRec/tree/778ba3b3aced338f30bc4b35accecf14ecf419a3/contracts/canon-ops/v1)

### Phase 1 — Core ground-segment path

- [x] #48 — implement the ground-segment bridge service. [Closed with offline L1/L2 verification](https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/pull/123)
- [x] `AUo959/aurora-cloudbank-symbolic#1383` — submit mediated QGIA forecast packages to CanonRec staging. [Verified offline through native GUMAS and Chronicle](https://github.com/AUo959/aurora-cloudbank-symbolic/pull/1727)
- [x] #49 — execute approved CanonRec scenario seeds with deterministic GUMAS receipts. [Verified native run and Chronicle reconstruction](https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/pull/125)

### Phase 2 — Human and agent surfaces

- [ ] `AUo959/cloudbank-quantum-en#33` — add a Canon Operations review workspace.
- [ ] `AUo959/AuroraOS#10` — add receipt-grounded CanonRec query and staged-proposal tools.

### Phase 3 — Integration gate

- [ ] #50 — prove the end-to-end QGIA-to-CanonRec vertical slice.

## Dependency rule

CanonRec v1 is accepted through `AUo959/CanonRec#5`. The bridge and downstream clients use the pinned schemas and receipts from that contract.

## Definition of done

A pinned test fixture can complete the full workflow without manual artifact copying:

1. Import one QGIA forecast/evidence package.
2. Record explicit L1 approval or rejection.
3. Submit validated claims to CanonRec as `STAGING` only.
4. Produce an approved scenario seed.
5. Execute GUMAS deterministically across at least two identical replay runs.
6. Emit matching run receipts and an operational Station Chronicle projection.
7. Resolve one outcome and attach calibration evidence.
8. Query the complete chain from CloudBank and AuroraOS with source pointers.
9. Demonstrate that unauthorized direct promotion, layer bleed, altered receipts, and duplicate requests are rejected.

## Out of scope

- A second canon database or identity authority.
- A second subsystem named Observatory.
- Autonomous QGIA-to-L2 tasking.
- Direct Git commits from UI or agent tools.
- Promotion of simulation output without CanonRec reconciliation and explicit human approval.

## Delivery posture

Contract-first, local-first, additive, and reversible. No repository migration or new standalone repository is required for the first vertical slice.

## Comments (0)

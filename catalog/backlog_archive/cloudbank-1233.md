# aurora-cloudbank-symbolic#1233: Ethics documentation follow-ups (consolidated)

- URL: https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1233
- State at archive: open
- Author: AUo959
- Created: 2026-07-13T17:33:50Z
- Updated: 2026-11-24T04:03:47Z
- Labels: documentation, needs info, security, ethics, implementation-needed, backlog
- Milestone: none

## Linked pull requests (head SHA at archive time)

- aurora-cloudbank-symbolic#1310 — docs: make the repository navigable, and its claims checkable — closed — `docs/navigation` @ `7eda34d34541d0fff996e535241d60aa99db33fa`
- aurora-cloudbank-symbolic#1311 — docs: make the repository navigable, and its claims checkable — merged — `docs/navigation` @ `8b80c9e4a117a92012d66b7a98828800feda6cba`
- aurora-cloudbank-symbolic#1547 — aurora(queue): auto-ingest labeled issues — closed — `queue/auto-ingest-20260831-0627` @ `1ae40d53ec9b3c43445c07e4d78b869b987ff7ed`
- aurora-cloudbank-symbolic#1580 — aurora(queue): auto-ingest labeled issues — closed — `queue/auto-ingest-20260907-0627` @ `a71ef88de7b4d0cf91e12014ae3db08ea267c245`
- aurora-cloudbank-symbolic#1592 — aurora(queue): auto-ingest labeled issues — closed — `queue/auto-ingest-20260914-0628` @ `63925666199e49b35769bfb41cd321e30cb7d759`
- aurora-cloudbank-symbolic#1626 — aurora(queue): auto-ingest labeled issues — closed — `queue/auto-ingest-20261005-0634` @ `ce94a1c31e41872657cf17b7106550b773da9441`
- aurora-cloudbank-symbolic#1636 — aurora(queue): auto-ingest labeled issues — closed — `queue/auto-ingest-20261012-0634` @ `fbeec39d1309f54ab4cc0881bb716aff940660aa`
- aurora-cloudbank-symbolic#1650 — aurora(queue): auto-ingest labeled issues — closed — `queue/auto-ingest-20261019-0628` @ `67c5f16a0edb0385d779577ab062ebb33e0ef22b`
- aurora-cloudbank-symbolic#1662 — aurora(queue): auto-ingest labeled issues — closed — `queue/auto-ingest-20261026-0628` @ `3ab7cbaa2503354ea167f5a97207f34472e1a46f`
- aurora-cloudbank-symbolic#1719 — feat(ethics): add advisory curvature and reconcile custody evidence — merged — `codex/1233-ethics-followups` @ `c90c480c7c5bd0ca219d77093dda44ff562fb99b`
- aurora-cloudbank-symbolic#1721 — Remove the unverified SHADOWFAX arbitration binding — merged — `codex/ord-custody-boundary` @ `af57b3ea69c254b17923a0b622f708323d672bda`

## Branches named in the issue

- none

## Original body

## Summary

This issue consolidates the June 2026 ethics and security documentation audits. [#1129](https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1129) · [#1137](https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1137) · [#1138](https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1138)

## Verified on main

- [x] Implement opt-in `FieldCurvatureV2` evaluation, advisory synapse warnings, and formation statistics. V1 remains authoritative for allow and deny decisions. [#1719](https://github.com/AUo959/aurora-cloudbank-symbolic/pull/1719)
- [x] Reconcile the six Section 8 promotion-plan follow-ups with their existing issues. [Promotion plan](https://github.com/AUo959/aurora-cloudbank-symbolic/blob/main/docs/ethics/recovered_protocols/PROTOCOL_PROMOTION_PLAN.md)
- [x] Verify the historical SHADOWFAX archive SHA-256 and record its custody hold. [Custody manifest](https://github.com/AUo959/aurora-cloudbank-symbolic/blob/main/docs/ethics/recovered_protocols/recovered_protocol_manifest.json)
- [x] Publish the v2 engagement scope and record the status of the internal rehearsal and external engagement. [Scope](https://github.com/AUo959/aurora-cloudbank-symbolic/blob/main/docs/security/pentest_scope_v2.md) · [Assessment history](https://github.com/AUo959/aurora-cloudbank-symbolic/blob/main/docs/security/pentest_history.md)

## Open evidence

- [ ] Obtain the original Sherlock, Watson, Moriarty, and Tribunal packages and verify package and protocol-file digests. The DEV inventory carries expected archive hashes. [DEV inventory](https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/blob/6f28f881fb5eddf5c974b98e35f697183539bb54/catalog/archive_inventory.jsonl#L443-L447)
- [ ] Attribute and verify the SHADOWFAX protocol file inside the historical archive. Complete the custody sign-off and the ORD-3 identity reconciliation before evaluating promotion. [#1361](https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1361)
- [ ] Supply the signed scope and independently attributable external-assessment evidence for Gate-001B. [Open gates](https://github.com/AUo959/aurora-cloudbank-symbolic/blob/main/ops/work_queue/OPEN_GATES.md)
- [ ] Supply scan-disposition evidence to finish reconciling the historical remediation plan against the fixes and transformation reports. [Remediation plan](https://github.com/AUo959/aurora-cloudbank-symbolic/blob/main/docs/security/SECURITY_REMEDIATION_PLAN.md)

## Comments (2)

### github-actions[bot] — 2026-08-13T09:27:27Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1233#issuecomment-5278504777>

This issue has been automatically marked as stale because it has not had activity for 30 days. It will be archived if no further activity occurs.

### AUo959 — 2026-08-15T07:16:35Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1233#issuecomment-5301112418>

## Current-main refresh — 2026-08-15

This consolidated tracker is still actionable and should not be stale-archived:

- `modules/ethics_field/field_curvature_v2.py` is still absent; the evaluation document's implementation recommendation remains unfulfilled.
- All five recovered-protocol custody records still contain `PENDING` source/internal hashes and verification metadata. SHADOWFAX is correctly typed `missing_dependency` with a hard wiring block, but custody is not complete.
- `docs/security/pentest_history.md` remains 343 bytes and records only an unscheduled engagement with `TBD` date/vendor/findings.
- The SHADOWFAX runtime-name/custody ambiguity now also has the focused high-priority tracker #1361; that issue does not resolve the other custody records or the two other workstreams here.

The `stale` label has been removed. The issue remains open as an `ethics`/`security` backlog item with implementation and source-evidence work outstanding.


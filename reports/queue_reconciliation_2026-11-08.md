# Queue reconciliation and development-maintenance review

Reviewed November 8 UTC (November 7 in New York), under the owner's instruction
to proceed with queue automation, tracking reliability, and maintenance triage.

## Landings and scope

- Root #87 merged as `1801d00d9aa1f32c9f1b84875e8e6b144bd7f2ac`.
  It reads commit dates/platform attribution from Git provenance. Current main's
  queue/completion history was preserved during conflict resolution; the PR's
  two independent protocol follow-ups were retained. Full local suite: 740
  passed / 41 skipped; required CI passed.
- CloudBank #1635: merged as `cae69756c8d0781998c5da5ef6bac0c7a91f6090` after required CI passed.
  Focused queue/readiness suite: 84 passed. Full CI at reviewed head 8baf240f: 3,736 passed / 113 skipped /
  9 xfailed / 2 xpassed, plus 101 subtests passed. Mutable privileged-action tags
  were pinned; notification validation/rendering was split to meet Codacy
  complexity limits without changing retry semantics..
- Retained proposal validation/landing: current-main refreshes of #1671 (`fa7184be`) and #1672
  (`68ea8faa`) pass 84 focused tests each. Live producer dispatches
  [ingestion](https://github.com/AUo959/aurora-cloudbank-symbolic/actions/runs/42432794386)
  and [escalation](https://github.com/AUo959/aurora-cloudbank-symbolic/actions/runs/42432797457)
  succeeded, reused those proposals, and skipped PR creation and issue pings.
  Required final proposal checks/merges: both merged after all applicable checks passed: #1671 at
  `aa15daf2c05d6d44d03b7b197878f623147246c4`, #1672 at
  `aed9ea850772c9e483c99afb780032c9e4baa7d3`. Each final dispatched full
  suite reports 3,736 passed / 113 skipped / 9 xfailed / 2 xpassed, plus
  101 subtests passed. Combined main queue views pass freshness checks.
  The root registry, Orion repository policy, and independent test attestation
  now pin the final merged CloudBank revision. Runtime owner blob remains
  `5b6d93515fb219cb26d267db6c6df6c052413ae1`; simulation sources are unchanged..
- Superseded proposal closure: 14 individually compared older PRs closed with retained-proposal/receipt links: #1547, #1580, #1592, #1626, #1636, #1650, #1662 (ingestion); #1548, #1581, #1593, #1627, #1637, #1651, #1664 (escalation). Heads were rechecked against analyzed revisions before closure; branches/history were preserved..

No canon promotion, live simulation execution, or unrelated repo publication
was performed. Queue states are not completion evidence by themselves.

## Bot proposal comparison

All 16 proposals were compared by canonical JSON payload and changed-file
scope. Existing six queue entries, completed history, and queue metadata were
unchanged in ingestion proposals. They append #1233, #1361, and #1530, all still
open and security-labeled in the live issue snapshot. The first three also
append #1329, closed on September 24; removing that obsolete candidate shifts
the remaining tail ranks by one. Other differences are ingestion dates.

All escalation proposals change only last_surfaced/last_updated timestamps;
gate ownership, state, integrity holds, criteria, and resolution records match
main. Their old branches omit the generated OPEN_GATES.md update. The retained
proposal is regenerated using current code before validation.

| PR | Producer | Payload SHA-256 | Disposition |
| --- | --- | --- | --- |
| #1547 | ingestion | `277a155cd8491724db3c8bdad7af3013ed1633a66467213f625c5c8cd7ffae5f` | Superseded after retained payload validation |
| #1580 | ingestion | `ab3b5cf79e9f69f283a631ccb58a68df8931bbf626887cd219d48c58a6b67eb0` | Superseded after retained payload validation |
| #1592 | ingestion | `e8ba9493aa129f35c6869055a91d23f16b4763a144d9f0cb2edd9fb99f35f5c0` | Superseded after retained payload validation |
| #1626 | ingestion | `b94895b8fd29428e94ae7c0e9a8eb70b7959b531ee05d4759c327e9b318cd5d3` | Superseded after retained payload validation |
| #1636 | ingestion | `34c731e37a2b2d006b400043e4539649cb82a628aae2d181ab753e6ea63fa385` | Superseded after retained payload validation |
| #1650 | ingestion | `6cbdc5630dc3a7ef4f5a4a8231323a053ffd2968513569a3c45659725e7cb6bc` | Superseded after retained payload validation |
| #1662 | ingestion | `2d19d6ac54cb8de8d5eb07b443ad0403934957c888e3840933e8a99643f529da` | Superseded after retained payload validation |
| #1671 | ingestion | `9d714194eb3273647d9c4a6339121ca963ce3c05c3a46180d74f3b499720d2a0` | Retain and refresh |
| #1548 | escalation | `ff9b3802bbad66ecec2a94476435d94477e91b7d9cf8f8f5be83ee858c2321e3` | Superseded after retained payload validation |
| #1581 | escalation | `fe0fcab0ea866992624d5ddee3b7ce03b554736e78e8285febf028b365177fbc` | Superseded after retained payload validation |
| #1593 | escalation | `343caa6febc45f07f36e71754761428e4fd92b511b3facd130423d0ededc4d45` | Superseded after retained payload validation |
| #1627 | escalation | `1b11645730612fb3d755c7dfe731f6f1e3e009fa193501d56328cf4de177832a` | Superseded after retained payload validation |
| #1637 | escalation | `0ca0c85b2bb90233472bb6e5f66a2310257caefc50b64766f2be55e880f4f61f` | Superseded after retained payload validation |
| #1651 | escalation | `60218978ae86d523ca9b7d6bd4a4b9c23a804f1fd3e16da73f5c47c81aede7cd` | Superseded after retained payload validation |
| #1664 | escalation | `3177801374ae52ebae351d229a707d99878ed03eb9fd778b452b3aca780ed88d` | Superseded after retained payload validation |
| #1672 | escalation | `4f680c8acc7d95c554da93c73f1440e1f0e1943982664ed50afb29c0cc80041c` | Retain and refresh |

Normalization for comparison excludes surfacing/ingestion dates and the closed
issue #1329 candidate with its resulting tail-rank offset. It does not discard task
content, existing rank authority, completed records, or governance decisions.

## Tracking reliability

Root #105 removes nested pin/branch drift from automatic healing and sends the
registry output of manifest-only scans to scratch. The wrapper preserves the
registry file and staging scope. Explicit registry sync refuses symbolic branch
mismatches before writing any pins; an exact detached pinned reference remains
valid for read-only validation. Behavioral tests cover these cases. Full local
suite: 747 passed / 41 skipped (before final documentation/audit-comment edits).
Final pin/attestation and preservation-focused checks: 35 passed; state schema
and explicit registry checks pass.

The two corresponding existing queue items can close after this change lands:
registry-pin-vs-selfheal-hook and registry-sync-branch-field. The staff-authority wait was also closed against the existing committed
August 8 owner ruling in CloudBank docs/CANON_PROVENANCE.md and the
resolved_surfaces entry in config/canon_provenance.json. Five owner waits remain:
AWS deactivation verification, ten naming receipts/exemptions, Amelia Rivers
identity, Sentinel roster framing, and canonical-machine backlog publication.
Other historical items are retained unless separately verified; overdue dates are not renewed
by inertia. The FastAPI dependency item remains open: its requirement was
already present before the original report, so a provisioned cloud environment
alone does not prove the reported setup gap fixed.

## Current maintenance evidence

CloudBank contains 41 workflows, rather than the old roadmap's 33. CI
consolidation needs a trigger/required-check coverage map before removing jobs.

Runtime audit with isolated pip-audit 2.10.1 of requirements-lock.txt reports four affected packages and 23
unique advisory IDs (IDs can include aliases; this is not an exploitability
count):

| Package | Locked | Available patched versions from audit |
| --- | --- | --- |
| certifi | 2026.7.22 | 2026.10.18 (#1678 already proposes it) |
| mcp | 1.29.1 | 1.30.0 or 2.2.0 (#1655 proposes v1 patch; v2 migration is separate) |
| PyJWT | 2.13.0 | 2.15.0 addresses listed fixable findings (#1621); PYSEC-2026-4146 lists no patched version |
| urllib3 | 2.7.0 | 2.8.0 (#1623 already proposes it) |

Frontend npm audit reports 39 affected packages: 1 critical, 21 high, 16
moderate, 1 low. This includes development dependencies and propagated effects;
it is not 39 independently proven application vulnerabilities. Critical
DOMPurify finding: [GHSA-cg2g-xh64-v4q7](https://github.com/advisories/GHSA-cg2g-xh64-v4q7),
transitive through monaco-editor. npm reports no automatic fix for the current
dependency constraints; exposure and a compatible update need targeted review.

Reproduction (read-only dependency audits):

```sh
python -m pip_audit -r requirements-lock.txt --no-deps --disable-pip --format json
npm audit --package-lock-only --json  # in frontend/
```

No automatic npm audit fix, bulk dependency merge, waiver, or claim of
remediation was made. The verified dependency batch is now queued as
`cloudbank-dependency-security-refresh-2026-11`, ready/high, with review on
November 9. CI consolidation and the existing MCP v2 migration follow it.
Root queue after explicit closures/new evidence: 38 open (33 ready, 5 waiting),
37 overdue reviews. Original dates/statuses on unrelated items remain intact.

## Warrant

Confidence 0.98 for GitHub inventory, payload comparison, and test observations.
Dependency advisories are package-version matches; application reachability is
not established by these audits. Owner/crew decisions and CanonRec/QGIA
mutations remain outside this development-maintenance landing.

Audit `queue-dependency-audit.json` SHA-256: `f071cfe7ac2f50dedb1a36df0b2691d0bcdf985e86f6eef1e90db15f25111fc8`.

Audit `queue-frontend-audit.json` SHA-256: `cc8c17692e968eae542299870e86a98921eba610ce17076f62d9f2b23ebb18c5`.

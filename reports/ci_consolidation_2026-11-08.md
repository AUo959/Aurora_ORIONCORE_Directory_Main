# CloudBank CI consolidation: first tranche

November 8 UTC / November 7 in New York. Scope: the owner's instruction to
proceed with CI consolidation after the dependency-security batch.

## Change

CloudBank [PR #1689](https://github.com/AUo959/aurora-cloudbank-symbolic/pull/1689)
makes canonical Python CI the owner of automatic lint and test execution.
Kubernetes **Run Tests** and **code_quality** retain their check names and verify
an exact-checkout receipt from the latest successful canonical workflow attempt
for the same PR identity or push branch.
For PRs this requires both the branch head and synthetic merge checkout. Manual
Kubernetes runs keep their original independent test path and skip-tests input.
The notification summary's undeclared test dependency is corrected.

A late review thread identified GitHub's empty PR association for fork-origin
runs. Follow-up [PR #1690](https://github.com/AUo959/aurora-cloudbank-symbolic/pull/1690)
resolves such identity through the run's attempt-specific receipt before
selecting the latest relevant run. A newer unresolved run blocks older
successes; a verified unrelated PR can be excluded. Current failures and
checkout mismatches still cannot fall back to old successes. Kubernetes now
also triggers on changes to the shared verifier, its tests and canonical
workflow so this dependency is exercised in CI. The updated map includes the
required-check summary discovered through branch metadata.

Canonical lint now covers the union of the previous syntax scopes and uses the
existing stricter 120-column advisory style limit. Other specialized, security,
frontend, manifest, build and deployment checks remain. The consumers use
read-only Actions access and never dispatch workflows or execute artifacts.
Stale results, failed attempts, old merge checkouts and missing proof fail closed.

The inventory contains 41 workflow files. The old roadmap's 33-file count is
stale; event routing, scheduled services and deployment are not all core PR CI.
The CloudBank map documents ownership, retained entry points, recovery and the
remaining consolidation work. This tranche removes a duplicate automatic Python
installation/suite and independent lint installation; no measured runner-minute
or latency reduction is claimed because polling still occupies runners.

## Validation

- The initial 37 offline regression tests cover exact-context reuse, failure/timeout,
  wrong-event/head/merge/attempt proofs, malformed/oversized/expired artifacts,
  rerun races, PR/branch identity isolation, Markdown-only Kubernetes pushes,
  and workflow trigger/dependency contracts.
- Fatal Python syntax validation passes with the combined scopes/exclusions.
- actionlint 1.7.7 passes all three changed workflow files.
- Local `make check` passed: 3,771 tests, 113 skips, nine expected failures and
  two existing expected-test passes (311.49 seconds). This full run collected
  the initial 33-test receipt suite; the final 37-test suite passed separately
  after review corrections. Numerical-library threads were limited to one for
  this high-core-count host, matching the prior dependency batch.
- Root Makefile test scope (`tests/`): 747 passed, 41 skipped (35.69 seconds).
  An initial unscoped invocation also collected nested repositories from the
  wrong working directory and failed collection; it is not a cross-repo test
  result. Each repository uses its own suite and environment.
- GitHub canonical PR run `42440149732`: 3,775 passed, 113 skipped, nine
  expected failures, two existing expected-test passes and 101 subtests
  (368.95 seconds). Both consumers logged successful verification of checkout
  `6dfcc7365108c99c1078fc4b1e021e9f4778b65e` from that run. The head was
  `be647c01182cc9dd5e48685a54699c1ad10a6f23`; these are intentionally different
  identities (PR head versus tested merge commit).
- The fork follow-up passes 47 focused tests, adding empty-association success,
  unresolved newer attempts, unrelated shared heads, failed current attempts,
  invalid source identity/ref, shared-verifier trigger coverage and a metadata-only
  final status recheck. Verified fork identities are cached by run ID/attempt;
  no artifact download occurs after the final status snapshot, and newly
  unresolved attempts block old successes.
- Initial main-push canonical run `42440759667` succeeded. Both consumers
  logged exact checkout `6bb8ef5b6ca0e7710d8294511ec59b0fa4819eb1`, confirming
  the push-branch selection and build dependency after the first merge.
- Fork follow-up PR canonical run `42441192333`: 3,785 passed, 113 skipped,
  nine expected failures, two existing expected-test passes and 101 subtests
  (441.69 seconds). Both consumers verified exact merge checkout
  `e15a58b75d2e732049b3952caadae9d760264326`. The container build and manifest
  validation passed, all review threads were resolved, and #1690 merged as
  `28db5950e404ca2ec9fc007a1b5c6c114c3641dd`.
- Root registry pin and independent Orion policy/test attestation now bind
  `28db5950e404ca2ec9fc007a1b5c6c114c3641dd`. The complete `simulation/` diff
  against the prior pin is empty; owner blob remains
  `5b6d93515fb219cb26d267db6c6df6c052413ae1`. Ten owner-binding tests pass and
  registry sync has zero drift. CanonRec remains on its original detached pin.
- The first integration-gate run found an empty, ignored `data/ledgers` directory
  created by the earlier unscoped test collection. Moving this session-owned
  generated directory to scratch restores the expected workspace inventory.
  The repeated gate has all six subprocess return codes zero and verdict
  `warn`, retaining environment-inventory, installed-skill and overdue-review
  advisories; no source or manifest exception was needed.
- Final main-push canonical run `42441968760`: 3,785 passed, 113 skipped,
  nine expected failures, two existing expected-test passes and 101 subtests
  (441.07 seconds). Both consumers successfully verified exact checkout
  `28db5950e404ca2ec9fc007a1b5c6c114c3641dd` from that run. This verifies both
  the PR merge checkout and the resulting pushed main commit. The first merged
  main Kubernetes pipeline also completed its container/SBOM/manifest/staging
  dry-run checks successfully.

## Remaining work

`roadmap-1.1` remains open for the remaining consolidation. The full branch
protection administration endpoint returns 403. A later read-only branch
metadata query succeeds and reports `protected=true`, required context
**CI Check** with GitHub Actions app ID 15368, and `non_admins` enforcement.
The effective branch-rules endpoint returns Copilot review, deletion protection
and non-fast-forward protection, with no additional workflow requirements.
This is a required-check summary, not a complete administration-settings export;
it improves on the initial limitation described in the CloudBank workflow map.
No protection setting was changed.

Three branch-protection jobs currently print success without substantive
validation; two Codacy workflow entries are disabled while external Codacy
analysis remains separate. The next consolidation pass can use this required
check summary, verify consumers, and remove or replace redundant compatibility
lanes. Compare constellation validation with the canonical suite and inspect
legacy publishing consumers before deleting those lanes. This tranche retains
all existing entry points and names and proves exact-result reuse first.

The next separate development-readiness batch is session coordination:
`session-claims-worktree-blind` and `stop-hook-platform-attribution`. MCP v2
migration follows separately. No live simulation run, canon promotion, CanonRec
mutation or grouped dependency upgrade is part of this batch.

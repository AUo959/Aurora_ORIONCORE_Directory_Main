# CloudBank CI consolidation: inert-lane cleanup

Scope: the authorized Aurora / CloudBank restart. CloudBank PR #1693 retires
four workflows after verifying main requires **CI Check** from Actions app
15368. Effective rules add review, deletion and fast-forward protection, with
no additional workflow requirements. The full administration endpoint is still
403; no protection settings were changed.

## Coverage and consumers

Removed `branch-protection.yml` (three echo-only jobs), `codacy.yml` and
`codacy-analysis.yml` (disabled), and `code-quality.yml` (receipt-only duplicate
of canonical CI). The canonical **CI Check** and Kubernetes **Run Tests** proof
gate remain. Workflow consumers route wildcard completion events; none names a
retired workflow. Maintained auditor/Copilot instructions and Codacy setup docs
now point to current owners. Historical investigations retain historical names.
External Codacy app configuration remains intact.

Constellation now installs its root npm graph once. Blocking TypeScript checks,
advisory lint/build/audit and their artifacts remain. Audit executes before the
blocking type check. Its old integration job only echoed a placeholder and was
removed. Separate schema, OpenAPI, Python type and manifest contracts, root
Node/web tests, frontend tests and deployment validations remain.

Workflow count: 41 to 37. The ownership map is updated. `roadmap-1.1` remains
open pending specialized-lane and legacy publishing consumer review; this pass
does not claim the final roughly eight core lanes or measured runner savings.

## Local validation

- actionlint 1.7.7 passes the changed workflow.
- All 52 CI proof, workflow contract and installed-tool security tests pass; changed Python passes Ruff.
- TypeScript `tsconfig.constellation.json --noEmit --skipLibCheck` passes.
- Existing advisory root lint/build baseline: six errors and twelve warnings;
  root npm audit reports 39 findings (6 low, 20 moderate, 9 high, 4 critical).
  Dependency locks and the advisory policy were not changed. Local Node was
  v24.22.1; hosted Constellation retains its existing Node 20 runtime.
- Review identified the existing security test still expecting three installs;
  updated it to one while preserving installed-tool/no-npx checks. The initial
  full run had only this failure (3,817 passed); targeted verification passes
  and the final full run is recorded below. Codacy heading-order and blank-line
  findings in the status note were corrected before landing.
- Final CloudBank `make check`: 3,818 passed, 92 skipped, nine expected
  failures, two existing expected-test passes (305.66 seconds).
- Root suite: 773 passed, 41 skipped (36.71 seconds).

## Hosted validation and synchronization

Final PR head: `c9ccfc1cf558b0db34c7b96a6667ff5f7cee3d01`.
Canonical PR run: `42565913519`; Constellation: `42565913364`;
Kubernetes: `42565913376`. PR review findings were addressed and resolved.
Hosted Codacy and CodeQL pass on the corrected head.

Complementary review is tracked separately from Claude's MCP review. The adopted
peer-review protocol permits landing with tracked asynchronous debt; it does not
permit claiming the complementary review has already happened.


PR canonical suite: 3,818 passed, 92 skipped, nine expected failures, two existing
expected-test passes and 101 subtests (448.66 seconds). Kubernetes verified merge
checkout `a3fafd335ee7dc953dbee4589f00c70708924d58` from run `42565913519`;
container build and manifests passed. All PR checks completed successfully or
were intentionally skipped; no unresolved review threads remained at merge.

CloudBank merge: `fe99f3e5a300ecdc21c9fdf86563834d9e782568`.
Root registry and independent ACE policy/test pins now bind this commit. The
complete `simulation/` diff against f289f69c is empty; owner blob remains
`5b6d93515fb219cb26d267db6c6df6c052413ae1`. CanonRec was not advanced.

Root integration gate: all six subprocess return codes are zero, verdict `warn`.
Existing environment inventory, installed-skill drift and overdue queue-review
advisories remain visible. Registry sync has zero drift; all ten owner-binding
tests pass after the pin update.

Main canonical run: `42566971942`; Constellation `42566971927`; Kubernetes
`42566972090`. The separate simulation freshness guard fails because the state
file is 118 days old (GAP-010, #1083). The same workflow failed on f289f69c and
the preceding main commits. This cleanup does not refresh simulation state or
suppress that guard; this is a documented pre-existing main-only failure.

Claude's independent MCP review landed in root #111 while this branch was in
flight. The root merge preserves its receipt, completed task and cleared debt.
Only the new CI-domain complementary review remains pending from this pass.

Main canonical run `42566971942` passed: 3,818 tests, 92 skips, nine expected
failures, two existing expected-test passes and 101 subtests (415.01 seconds).
Kubernetes **Run Tests** job `128995482009` verified exact checkout
`fe99f3e5a300ecdc21c9fdf86563834d9e782568` from that run; manifest validation
and main Constellation CI passed. This verifies both the PR merge checkout and
the resulting main commit. The pre-existing freshness guard remains separate.

After reconciling landed MCP review #111, the root full suite again passed:
773 passed, 41 skipped (37.21 seconds). Registry drift is zero; session state
validates; all six final integration-gate subprocesses return zero with the
existing warning verdict. Root receipt publication: PR #112.

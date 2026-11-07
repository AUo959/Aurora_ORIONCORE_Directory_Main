# Aurora / CloudBank development restart — 2026-11-07

Scope: the five Aurora / CloudBank repositories selected by the owner. This is
a development-readiness receipt, not a deployment or security certification.
Changes are on review branches; default branches have not been merged by this
session. The private Probot prototype remains a legacy reference by owner
decision.

## Reviewable changes

| Repository | Change | PR |
| --- | --- | --- |
| AuroraOS | Repair omitted native esbuild lockfile entries; add Node 22 type/build CI and development README | [#14](https://github.com/AUo959/AuroraOS/pull/14) |
| cloudbank-quantum-en | Reconcile stale template lockfile; ignore indentation-only differences in drift checks | [#35](https://github.com/AUo959/cloudbank-quantum-en/pull/35) |
| aurora-cloudbank-symbolic | Isolate CI-mode agent tests from live GitHub and stale repository logs | [#1679](https://github.com/AUo959/aurora-cloudbank-symbolic/pull/1679) |
| aurora-cloudbank-symbolic1 | Record preserved legacy status, reproducible historical build, and deployment blockers | [#1](https://github.com/AUo959/aurora-cloudbank-symbolic1/pull/1) |
| Aurora_ORIONCORE_Directory_Main | Scope skill-drift verification to the requested workspace; isolate test machine identity from the developer's home; add regression coverage and this receipt | Current restart branch |

## Verification

| Repository | Evidence | Limits |
| --- | --- | --- |
| Root control plane | Full suite: **727 passed, 41 skipped** on Python 3.12.14 with MCP 2.3.0 and registered CloudBank/CanonRec references. Focused new/changed-file Ruff checks pass. Existing workspace verifier has the same 20 Ruff diagnostics as main, with none introduced. Integration gate: **warn**, all six subprocess checks exit 0. | Remaining gate warnings and skipped tests are not a green deployment signal. |
| AuroraOS | Clean npm install, TypeScript check, and Mastra build pass on Node 22.23.4; Node 24 build also passed. GitHub **Development checks** workflow succeeded on the PR. | Existing `npm test` is still a failing starter placeholder, documented in README. No live AI, PostgreSQL, Inngest, Telegram, or Slack connection verified. Mastra's telemetry reported a network error while the build itself succeeded. |
| Dashboard | Clean npm install, build, TypeScript noEmit check, and lockfile check pass. ESLint: 0 errors, 8 existing warnings. GitHub **CI** succeeded on the PR. | No behavioral test suite was found. No authenticated backend integration verified. |
| CloudBank | Root Node suite: **55 passed**; web component suite: **8 passed**. Python unit/smoke: **1,736 passed, 100 skipped, 8 xfailed, 1 xpassed**; 1,963 deselected. Dependency consistency check passes. Frontend builds and passes strict lint. Repaired automation tests: **5 passed** in 0.73s. | Frontend unit command finds no tests. Full Python attempt was interrupted after **1,144 passed, 87 skipped, 2 failed**; both failures were the live-network automation tests subsequently repaired. Full Python green is not claimed. PR CI was still running at receipt time. |
| Legacy prototype | Frozen pnpm 7.33.7 install and Rollup bundle pass. Owner preservation decision recorded. | Jest fails during collection on the CommonJS/ESM boundary. Browser-session provider access is obsolete and unverified. Not a supported deployment target. |

The dashboard lock repair removes 36 unused entries, including the old Spark
template dependency; no retained package version changed. AuroraOS lock repair
adds platform-specific packages without changing its direct dependencies.

## Reproduction and environment boundaries

- CloudBank uses Node **22.x** and its own Python environment with MCP **1.x**
  from `requirements-test.txt`.
- Root ACE uses **MCP >=2,<3** from `requirements-ace-mcp.txt`. Do not run its
  MCP client test in CloudBank's MCP 1.x environment: the `Client` API differs.
- Provision the pinned CloudBank and CanonRec repositories with **full Git
  history** before root integration tests. A shallow CloudBank clone initially
  produced false stale-manifest failures; fetching history resolved them.
  CanonRec was checked at registered SHA
  `72f504b397a09cecc5e39250e9ae2cb7ea0f01f5`.
- This cloud checkout is not the owner's macOS workspace. Local-only inventory,
  installed skill destinations, and unavailable registered repos must retain
  their execution-context warnings; registry paths/pins were not rewritten to
  describe temporary cloud clones.
- Use a writable workspace-local npm/pip cache in this sandbox. The default
  home cache is read-only here. This was an environment issue, not a reason to
  change project dependencies.
- Simulation test artifacts were retained outside the tracked checkout as
  scratch evidence. No simulation/canon result was promoted.

## Remaining work before declaring the whole project ready

1. Review and land the restart PRs through the existing PR lifecycle. Check
   CloudBank and root CI, not just local validation. No merge approval has
   been inferred from this receipt.
2. Run the remaining CloudBank integration/slow suite in its complete CI
   environment after landing the deterministic automation tests. Configure
   connector credentials and services before exercising authenticated tests.
3. Review the existing backlog against live PR state. Root queue health has
   **33 ready, 6 waiting, 39 reviews due**; the latest state briefs already
   describe publication and owner-decision debt. This session did not renew
   dates or mark unrelated items complete. Existing queue repair
   [CloudBank #1635](https://github.com/AUo959/aurora-cloudbank-symbolic/pull/1635)
   should be reviewed before creating overlapping queue automation work.
4. Add behavior coverage for AuroraOS and the two frontend surfaces as those
   surfaces enter active feature development. Keep compilation and behavior
   coverage distinct.
5. Verify configured live integrations before any public demo or deployment.
   The registry's project focus remains workable public demos; static builds
   alone do not establish a complete demo flow.

## Evidence and confidence

Observed initial main SHAs: root `8569f743`, CloudBank `0fac9809`, AuroraOS
`373603dc`, dashboard `944934b9`, legacy `3530b82d`. Reviewed root orientation,
registry, session queue, and executive briefs dated 2026-08-15 and 2026-08-28.
The queue/publication debt is known-and-aging, rather than a newly discovered
project failure. Install and isolation defects above were reproduced in this
session.

Warrant: direct command output and live GitHub PR/workflow responses support
the passing checks and proposed fixes. Live integration readiness is explicitly
unverified. Confidence audit: **0.95**, threshold **0.70**, no low-confidence
alert for the bounded conclusion that the restart patches pass their targeted
checks. That score is not a claim that the entire deployment is ready.

No default branch was force-pushed, no repository visibility/archive setting
changed, and no canon, credentials, or recovered material was promoted.

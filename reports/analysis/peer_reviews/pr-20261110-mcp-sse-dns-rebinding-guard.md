# Independent SSE DNS-rebinding guard review

Verdict: **approve**. Reviewer: Codex. Author: Claude Code.

Target `d01a6853dd3552cd4059f54e87914fe527662e79` against `fe99f3e5a300ecdc21c9fdf86563834d9e782568`; root handoff `78d87d30`. No blocking findings.

- **fixed revisions:** Reviewed all five CloudBank changed files, both root handoff files and supporting MCP SDK validation/SSE code; source worktree unchanged.
  Command: `git diff fe99f3e5 d01a6853; root diff 0e8fc755 78d87d30`
- **real transport and connector tests:** 116 passed, 73 live-backend skips; all 45 new transport cases pass, including actual IPv6 loopback.
  Command: `python -m pytest tests/connector tests/test_mcp_connector_wired.py -q`
- **mutation control:** 18 failed, 27 passed; the unmodified target remains unchanged.
  Command: `Remove security settings only in separate sse-review-mutation worktree; pytest test_sse_transport_security.py`
- **full final-head suite:** 3863 passed, 92 skipped, 9 xfailed, 2 existing xpassed; 319.61 seconds on d01a6853.
  Command: `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 make check using mcp-v2-final-venv`
- **fresh dependency and wheel environment:** Fresh environment uses unchanged hash lock; no broken requirements. Wheel sha256 9ae72bb1b809bcd4835ca1f2df2b2e7eb2294424493ea8d258a2bbc9a37e4b34; imported from site-packages outside checkout.
  Command: `pip install --require-hashes --only-binary=:all: -r requirements-ci-hashed.txt; pip wheel --no-deps ./connector; install wheel; pip check`
- **independent SDK 1.30 compatibility:** SDK 1.30.0 completes stdio and SSE; five descriptions/input schemas identical across base/checkout/wheel. Five invalid/unknown calls per transport cause zero backend requests; valid health calls retain bearer auth. Host/Origin refused on GET/POST for target and wheel; no SSE tracebacks.
  Command: `sse-review-legacy-harness.py against checkout, installed aurora-mcp, and base fe99f3e5`
- **additional live edge profiles:** Each profile in a fresh process passes: portless Host/Origin with port-80 policy, no unspecified IPv6 implicit trust, exact remote host/port, explicit port-wildcard origin, suffix and wrong-port refusals.
  Command: `sse-review-edge-isolated.py default-port, ::, [::], 0:0:0:0:0:0:0:0, remote`
- **unchanged contracts and boundaries:** No diff. l1_runtime.py blob remains 5b6d93515fb219cb26d267db6c6df6c052413ae1.
  Command: `git diff --exit-code fe99f3e5 d01a6853 -- simulation/ connector/auth connector/tools connector/transport connector/pyproject.toml requirements-ci-hashed.txt requirements-lock.txt`
- **root handoff verification:** 773 passed, 41 skipped in 37.62 seconds after resolving environment inode exhaustion.
  Command: `root-venv/bin/python -m pytest tests/ -q with pinned CloudBank/CanonRec references`
- **hosted source checks:** All source checks success/skipped; original root handoff checks pass. One outdated default-port thread is resolved based on source correction and live probe.
  Command: `GitHub check-runs on d01a6853 and root #114 original head`

## Limits and methodology

- Managed security plugin preflight resource and scan tools unavailable: this is a manual project peer review, not a finalized plugin security scan.
- No live Aurora backend or production remote authenticated gateway was exercised.
- Header checks are not authentication. Native clients can supply arbitrary headers; remote deployments still require an authenticated gateway protecting both endpoints.
- Loopback HTTP web origins are intentionally trusted at any port. Matching remains SDK case-sensitive.
- Used independent loopback backend and SDK1.30 subprocess client; baseline run compares protocols/schemas, not hostile-header refusal.
- Initial custom harness used a nonexistent capsule property as an invalid-input test; corrected to the published ethics severity enum, then reran successfully.
- An initial root run exhausted workspace inodes; removed only prior task disposable npm/pip caches and node_modules, then reran root tests successfully. Claude environments preserved.
- Multi-server edge probe encountered the existing sse-starlette global graceful-shutdown latch. Isolated each profile in a separate process matching CLI lifetime; all pass.

This receipt clears only `rd-20261110-mcp-sse-dns-rebinding-guard`. Source merge and mechanical root pin synchronization follow separately.

## Landing and root attestation

CloudBank [#1699](https://github.com/AUo959/aurora-cloudbank-symbolic/pull/1699)
merged as `b68c4717332f57b5bca0d07e06b448380ad3b76d`; its entire source tree
matches the reviewed head. Root [#114](https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/pull/114)
synchronizes the registry, ACE policy and test constant. The full simulation diff
is empty; owner blob remains `5b6d93515fb219cb26d267db6c6df6c052413ae1`.
Ten owner-binding tests pass, registry drift is zero and session state validates.
All six integration-gate subprocesses return zero, retaining existing environment,
installed-skill and overdue-review advisories. CanonRec is unchanged.

Source main canonical run `42744570449` passed on the exact merged commit:
3,863 tests, 92 skips, nine expected failures, two existing expected-test passes
and 101 subtests in 454.87 seconds. The separate simulation-state
freshness guard still fails for the previously tracked GAP-010/#1083; no state
refresh or guard suppression is part of this change. Coordination PR #113 and
its independent Claude review remain separate and unmerged.

# Restart landing receipt — 2026-11-07

The owner explicitly authorized landing the five prepared fixes: "lets land
your fixes". This supersedes the earlier receipt's pending-approval posture.

## Merges independently confirmed

| Repository | PR | Squash commit |
| --- | --- | --- |
| AuroraOS | [#14](https://github.com/AUo959/AuroraOS/pull/14) | `b80dcaff62add131c6424e87d80fee3a90e09e0e` |
| cloudbank-quantum-en | [#35](https://github.com/AUo959/cloudbank-quantum-en/pull/35) | `f81cad38a71848da685465d732c91f39ec778094` |
| aurora-cloudbank-symbolic1 | [#1](https://github.com/AUo959/aurora-cloudbank-symbolic1/pull/1) | `fe075747939a35178c2ef6d145e3759594e533e3` |

AuroraOS's reviewed setup-node annotation was corrected from v5 to v7 after
checking the upstream tag. The action SHA itself did not change. Its updated
build check passed. Dashboard CI passed. The legacy PR changes documentation
only; its existing Vercel preview failed, which remains consistent with the
owner's choice to preserve the prototype rather than restore deployment.

## Root landing vehicle

[Root #102](https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/pull/102)
contains the control-plane fixes and these receipts. The latest local full
suite passed **728 tests, 41 skipped**. Codacy feedback led to small helpers
for file synchronization and drift collection, plus narrowly scoped Bandit
B101 annotations on pytest assertions, matching the existing test policy.
Added coverage verifies actual add/update behavior and non-mutating dry runs.
Focused Ruff checks pass. Final merge state and SHA are recorded by GitHub on
the PR; they must not be inferred from an earlier local receipt.

Root tests require the registered CloudBank commit, not the temporary feature
branch used for CloudBank edits. A dedicated full-history pinned clone restored
that boundary without altering registry pins. Simulation test output remains
scratch evidence and is not promoted into tracked canon.

## CloudBank remains blocked

[CloudBank #1679](https://github.com/AUo959/aurora-cloudbank-symbolic/pull/1679)
passed its code-quality/security checks, but mandatory **CI Check** failed:

- Run `42418774283`, job `128542484248`.
- Full suite: **3,683 passed, 113 skipped, 9 xfailed, 2 xpassed**;
  **one failure**, `test_verification_claims_are_not_stale`.
- The four selectable catalog entries `CLAUDE_OPUS_5`, `CLAUDE_SONNET_5`,
  `GPT_4`, and `GPT_4O` carry verification dates 105 days old; policy permits
  90 days.
- The automation-test changes do not modify catalog dates or routing. This
  time-dependent failure exists independently of the proposed fix.

No date was advanced without verification, no model routing was changed to
satisfy CI, and no required check was bypassed. Landing this PR requires a
separate evidence-backed refresh of the catalog and a successful full CI run.

The earlier development-readiness receipt remains the detailed installation
and validation record. This landing receipt records later review and CI
evidence; it does not certify live integration availability.

Confidence: 0.99 for observed merge responses and bounded test results, based
on direct GitHub responses and retained command output. Whole-project live
readiness is explicitly unverified.

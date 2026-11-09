# Peer Review Receipt: Session Coordination Repair (PR #108)

Review ID: `pr-20261108-session-coordination`
Reviewed at: `2026-11-09T00:42:08Z`
Reviewer: Claude Code
Author platform: Codex
Verdict: `approve-with-notes`
Debt cleared: `rd-20261108-session-coordination`

## Scope

- PR: https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/pull/108
- Base `798762038209826a3cfbb247c393dae1bd1f7f14`, merged `6643b2db27415cb0a5f702d80943c03211f5ab82` (origin/main had not moved).
- Source commits: `e966dd77`, `e44eb4a5`, `b5016d93`. The PR head `ca42faf7` has an empty tree diff against the merged commit.
- Re-derived from the diff in tools/session_claim.py, session_state_io.py, session_stop_hook.py, workspace_verify_precommit.py, .claude/settings.json, the inventory files and the new tests. The author's receipt and green CI were treated as evidence to check, not as approval.

## Reverification (actual results)

Environment: repo venv, Python 3.12.13. System python3 is 3.9.6 without jsonschema. ruff is not installed in the venv, so lint was not re-run.

| Check | Result |
|---|---|
| Focused suite (7 files) | **97 passed** (author: 97) |
| Full suite, target, clean worktree | 8 failed, 726 passed, 74 skipped |
| Full suite, base 7987620, same environment | 8 failed, 700 passed, 74 skipped. Failing set identical; target adds exactly +26 passing tests |
| Author's 773 passed / 41 skipped | **Not reproduced.** Needs the nested repos present; see f2 |
| `tools/aurora_integration_gate.py` | verdict `warn`, exit 0, six subprocesses all 0. Advisory: `command_gateway_safety` parser unavailable, plus existing environment and queue-review warnings |
| `make session-state-check` | OK |
| `make registry-sync-check` | exit 0 |
| Real `git commit` of this receipt through the installed pre-commit hooks, with my claim active | all hooks passed, tree clean afterwards |
| Mutation tests (5 fixes reverted one at a time) | each makes 1 to 4 of the 26 new tests fail |

The first integration-gate run exited 1 because its `session_claim_check` conflicted with my own active mutation claim. I released the claim, re-ran the gate, and re-created the claim. This is the expected claim-workflow interaction, not a defect.

The 8 failures are the same on the base commit and are caused by nested repositories being untracked and therefore absent from a fresh linked worktree. Symlinking them in produced a different set of failures from path containment, so I discarded that run as an artefact of my fixture.

## Behaviours reproduced independently

Run in scratch clones and worktrees of 6643b2db, not by re-reading the author's tests.

- **Shared claims.** A claim created in a linked worktree lands in the canonical store, conflicts when checked from the other checkout, and is released from it. 21 existing canonical leases are visible from a linked worktree. A conflicting codex claim makes `session_state_io.py` exit 3 with the state file's hash unchanged. A read-only claim and a claim for another repository do not block.
- **Concurrent sessions.** Two session-starts in the same second gave distinct `claude-auto-<ts>-<uuid>` IDs. Closing one left the other active. Re-creating an existing ID fails with and without `--allow-conflict` and leaves the original untouched.
- **Platform attribution.** Explicit `AURORA_SESSION_PLATFORM` wins over environment markers. Invalid, empty, ambiguous or absent identity resolves to `None`. Commit labels still come from provenance.
- **Healer.** `--refresh-only` is wired in the pre-commit healer. It refreshed state while leaving the session's live claim active, wrote no orphan marker and no ledger output, and left an unrelated dirty tracked file alone.
- **Genuine close.** With a conflicting codex claim, close exits 0, defers the protected write, releases its own presence and keeps a local orphan marker. `--refresh-only` in the same situation exits 1 and writes no marker.
- **Checkout-local markers.** Each checkout kept its own auto-claim marker and orphan evidence.

## Findings

- **f1 (note, accepted-with-note): `GIT_COMMON_DIR` redirects claim discovery.** `_workspace_common.git()` scrubs `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE` and `GIT_PREFIX` but not `GIT_COMMON_DIR`. With it exported, `claims_dir()` resolves to the foreign repo and `create` writes the lease there. Repro: `GIT_COMMON_DIR=/tmp/foreign/.git python tools/session_claim.py create ... --claim-id leak1`. The brief item on inherited Git variables is therefore only partly met, and the new test covers `GIT_DIR` only. I kept this non-blocking because the variable is git-internal, claims are advisory leases, and the failure is lost visibility rather than corruption. The one-line fix is queued as `session-claim-git-common-dir-scrub`.
- **f2 (note, accepted-with-note): author totals not reproducible here.** Evidence above. I also saw 808 collected tests against an implied 814 and could not attribute the 6-test gap.
- **f3 (nit): `task: ?` in the BLOCKED message.** It reads a `task` key but claims store `task_id`. Pre-existing, cosmetic.
- **f4 (nit): non-atomic exclusive create.** The lease is briefly an empty or partial file between `open('x')` and the write. A crash there leaves an invalid file occupying the ID. From code reading, not reproduced.
- **f5 (nit): unguarded `import session_state_io` in the stop hook's `main()`.** The old code had an ImportError fallback.
- **f6 (note): claim store is the parent of git's common dir.** Bare-repo, separate-git-dir and submodule layouts are outside the convention. The workflow doc says so and the root repo does not use them.

## Not verified

- Ruff was not re-run.
- The two-independent-clones case was not given a dedicated probe.
- Historical commit attribution was checked only through the passing provenance suite and the refresh-only probe.

## Decision

Approve with notes. Every behaviour in the brief was reproduced except the `GIT_COMMON_DIR` case, which is a small, bounded gap rather than a regression of the shipped guarantees. Clear `rd-20261108-session-coordination` and complete `review-session-coordination-20261108`. Follow-up `session-claim-git-common-dir-scrub` carries f1; f3 and f5 can ride along. Because the repair is in the coordination domain, that follow-up is itself a floor change and will need its own complementary review.

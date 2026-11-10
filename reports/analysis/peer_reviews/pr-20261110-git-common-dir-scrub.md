# Independent review: PR #113 GIT_COMMON_DIR scrub

- Reviewer: claude-code (author: codex)
- Reviewed: 2026-11-10T03:39:38Z
- Verdict: **approve-with-notes**
- Debt: `rd-20261110-git-common-dir-scrub` (cleared)
- Target: [PR #113](https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/pull/113), implementation `382d4c5a`, base `0e8fc755`, reviewed head `df081170`, main `e1b07d38`

## Summary

The fix does what it claims. Independently: with the base helper, a linked worktree run under an inherited GIT_COMMON_DIR pointing at a foreign repo resolves its claim store inside that foreign repo; with the one-line fix it resolves to the canonical store. The expanded regression (canonical/linked x GIT_DIR/GIT_COMMON_DIR) fails exactly the two GIT_COMMON_DIR cases against the base helper and passes all four with the fix. Focused suite 55 passed; full root suite 770 passed, 40 skipped, 1 failed in a provisioned checkout, where the one failure is environmental and identical on the base helper. Integration gate, session-state-check and registry-sync-check are clean. Ruff on the changed test is clean and the helper has the identical six baseline findings. Notes only: sibling raw git subprocess calls elsewhere are unscrubbed but do not choose the claim store (f1), and the full-suite totals depend on nested checkouts (f2).

## Reverified gates

| Gate | Result | Command | Evidence |
|---|---|---|---|
| environment | pass | `Detached worktree at df081170; root venv Python 3.12.13 (jsonschema, pytest); ruff 0.15.20; system Python 3.9.6 used only for the first pass` | No live Aurora, model-provider credentials or production services. The temporary nested-repo links and the clone used for the full suite were removed or left outside the root tree; the root worktree stayed clean. |
| active claims and state | pass | `python3 tools/session_claim.py list; read catalog/session_state.json on main and on the PR branch` | 0 active claims (21 stale, 0 invalid). Main (e1b07d38) still lists session-claim-git-common-dir-scrub as ready; the PR branch holds it as waiting, adds review-git-common-dir-scrub-20261110 and pending rd-20261110-git-common-dir-scrub. Inspected both; no duplicate fix implemented. |
| code delta | pass | `git diff e1b07d38...df081170 --stat` | 4 files: helper (+2/-1), test (+13/-3), author report, session_state.json. The only runtime change is adding GIT_COMMON_DIR to the env keys removed by _workspace_common.git(). |
| regression with fix | pass | `python3 -m pytest tests/test_session_coordination.py -q -k foreign_git_environment` | 4 passed. |
| regression without fix | pass | `same command after restoring the base tools/_workspace_common.py (from e1b07d38); fix restored afterwards` | 2 failed (canonical-GIT_COMMON_DIR, linked-GIT_COMMON_DIR), 2 passed (both GIT_DIR controls). The new test therefore fails without the fix and passes with it. |
| direct discovery probe | pass | `GIT_COMMON_DIR=<fresh foreign git init> python3 -c 'claims_dir(cwd)' from the linked review worktree, with the fixed vs base helper` | Fixed: <canonical>/catalog/session_claims, same as with no env. Base helper: <foreign>/catalog/session_claims, i.e. claim storage redirected into the foreign repository. |
| conflict/refresh/release and no foreign store | pass | `read the regression body; it creates a claim from one checkout, checks conflict from the peer, refreshes and releases from the peer, and asserts the foreign repo has no catalog/session_claims` | Covers canonical->linked and linked->canonical for both env keys; the foreign-store absence assertion is what turns red for GIT_COMMON_DIR on the base helper. |
| focused tests | pass | `python -m pytest tests/test_session_coordination.py tests/test_session_claim.py tests/test_session_state_io.py -q` | 55 passed. |
| full root suite | pass | `python -m pytest tests/ -q (root 3.12 venv; temporary links to a CloudBank clone at b68c4717 and the CanonRec checkout; generated simulation artifacts moved to scratch)` | 770 passed, 40 skipped, 1 failed. The failure is tests/test_live_watch_link.py::test_live_link_is_fresh_and_clock_advances ('clone driver failed: pip install httpx2'); it fails identically with the base helper and does not touch the changed code. Without the nested checkouts the count differs (see f2). Author reported 776 passed, 41 skipped in their provisioned environment. |
| ruff | pass | `ruff check tests/test_session_coordination.py; ruff check tools/_workspace_common.py on fixed vs base copies` | Test: All checks passed. Helper: 6 findings (3 C901, S110, S603, S607) identical between base and fixed; no suppression or unrelated cleanup. |
| session-state-check | pass | `make session-state-check` | OK. |
| registry-sync-check | pass | `make registry-sync-check (with the temporary CloudBank clone linked)` | 2 in sync, 0 drifted, 7 skipped; exit 0. |
| integration gate | pass | `python tools/aurora_integration_gate.py` | Exit 0, verdict pass; warnings are the existing environment inventory, session_state_freshness and queue_review_due advisories. No active claim of mine, so session_claim_check was not tripped. |
| hosted checks | pass | `gh pr view 113 statusCheckRollup` | All required checks SUCCESS (one SKIPPED); mergeable at df081170. |

## Findings

### f1 (note, accepted-with-note)

Other raw subprocess git calls in the coordination tooling (session_state_io.py recent-commit log and HEAD refresh, session_stop_hook.py, session_claim.py _git) do not go through the scrubbed helper. None of them chooses the claim store, so the stated defect is closed; they would still inherit a foreign GIT_* environment for the mechanical HEAD and log refresh.

Evidence: grep of subprocess.run sites in tools/session_state_io.py:667,730, tools/session_stop_hook.py:57,204,304,489, tools/session_claim.py:_git. claims_dir() uses _workspace_common.git(), which is the scrubbed path.

Correction: Optional hardening, not required for this patch: route those calls through the shared helper or scrub the same keys. Left unqueued to avoid bundling.

### f2 (note, accepted-with-note)

Full-suite totals depend on nested checkouts. In a fresh worktree 15 tests failed on system Python without jsonschema; on the 3.12 venv 8 failed without a CloudBank checkout and CanonRec; with both linked 1 failed (test_live_watch_link needs a pip install of a dependency and network). The same tests fail identically with the base helper, so the PR is not the cause.

Evidence: Four runs recorded in the reviewer scratchpad (15, 8, 4, 3, then 1 failures as the environment was provisioned); the base-helper rerun of progression, crew_life and live_watch_link failed the same way.

Correction: None for this PR. Review environments should provision the nested repos before quoting totals.

## Not verified

- Optional items f3 (the 'task: ?' BLOCKED message) and f5 (stop-hook import guard) from the earlier coordination review are not part of this patch and were not reviewed.
- test_live_watch_link passes only in an environment that can install its driver dependency; not reproduced green here.

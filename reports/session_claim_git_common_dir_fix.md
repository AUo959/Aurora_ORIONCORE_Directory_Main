# Session-claim common-directory environment fix

Root PR: [#113](https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/pull/113)
Base: `0e8fc755acc8758ab0187ce07cd4f1823c4a5eef`.
Implementation: `382d4c5aa5f6c0fe482f8b307fb4c3877790b359`.

## Problem and change

The shared Git helper cleared GIT_DIR, GIT_WORK_TREE, GIT_INDEX_FILE and GIT_PREFIX
but inherited GIT_COMMON_DIR. A foreign repository's common directory redirected
canonical and linked-worktree claim discovery into that repository's claim store.
The helper now removes GIT_COMMON_DIR from its child environment as well.

The regression uses real canonical/linked Git fixtures and a separate foreign
repository. Both GIT_COMMON_DIR cases fail without the fix; GIT_DIR controls pass.
With the fix, canonical/linked discovery stays canonical, claims remain visible
across worktrees, refresh/release succeeds, and no foreign claim store is created.

## Verification

- Before fix: 2 failed, 2 passed in the expanded environment regression.
- After fix: all 55 focused claim/coordination/state-I/O tests pass.
- Full root suite: 776 passed, 41 skipped (37.97 seconds).
- Changed test passes Ruff. Shared-helper Ruff has the identical six baseline
  findings (three C901, S110, S603, S607); no suppression or unrelated cleanup.
- Generated simulation test artifacts were moved to scratch, not promoted.

## Review handoff

This is coordination follow-up f1 from the prior independent review. Claude must
independently verify PR #113 before merge; it remains unmerged. Pending debt
rd-20261110-git-common-dir-scrub tracks this patch separately from cleared prior
coordination/MCP debts and the pending CI review. Review should reproduce the
before/after failure, test real worktrees, and verify the shared Git helper does
not inherit the foreign common directory. No MCP change, nested pin movement,
canon change or optional f3/f5 fix is included.

Integration gate: all six subprocesses return zero; verdict warn retains the
existing environment inventory, installed-skill and overdue-review advisories.

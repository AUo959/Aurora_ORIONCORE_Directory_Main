# Branch Cleanup Tier 1 Receipt - 2026-06-20

Timestamp: 2026-06-20T01:20:15Z

Scope: root local branches already merged into `origin/main`, stale worktree
metadata in root/CloudBank/qgia-library, and CloudBank stale remote-tracking
refs identified in `reports/analysis/branch_inventory__2026-06-19.md`.

## Completed

Deleted root local branches confirmed merged into `origin/main`:

- `codex/continue-l1-entity-ledger-work` at `4093f1d`
- `codex/root-cleanup-before-cloudbank-issues-2026-05-11` at `d339b08`
- `feat/warrant-lens` at `42faeba`

Pruned stale worktree metadata:

- root:
  - `worktrees/charforge-capsules-20260614`
  - `worktrees/Aurora_ORIONCORE_Directory_Main2`
- CloudBank:
  - `worktrees/cloudbank-salvage-p2-ord-tests-20260615`
  - `worktrees/cloudbank-codex-issue-1015-salvage`
  - `worktrees/cloudbank-codex-issue-1020-mesh-router-contract`
  - `worktrees/cloudbank-salvage-p3-forge-policy-20260615`
- qgia-knowledge-library-main:
  - `worktrees/qgia-library-pr3-20260504`

CloudBank `git remote prune origin --dry-run` was empty at execution time, so
no CloudBank remote-tracking ref was pruned.

## Verification

- `git branch --merged origin/main` in root now returns only `main`.
- `git worktree prune --dry-run -v` now returns no stale metadata in root,
  CloudBank, or qgia-knowledge-library-main.
- Root `main` was pushed to `origin/main` with commit `f097c0c` before cleanup.

## Not Touched

- No unmerged root rescue/salvage branches were deleted.
- No remote branches were deleted.
- No CloudBank feature branches were deleted.
- No CloudBank scenario adapter or mesh-router stabilization work was modified.

Remaining CloudBank state at receipt time:

- `codex/l2-scenario-seed-simulation-initializer`
- `.env_status.json` modified locally

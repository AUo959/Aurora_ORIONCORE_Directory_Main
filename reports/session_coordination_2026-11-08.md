# Session coordination repair

November 8, 2026. Root control-plane scope: the queued worktree-blind claim
store and stop-hook platform attribution fixes.

## Behavior

Claim lookup now resolves Git's shared administrative directory and retains the
canonical checkout's existing `catalog/session_claims/` store. Linked worktrees
create, check, refresh and release the same leases. Independent clones remain
independent. Existing claim schema, TTLs, canonical claims and non-Git fixtures
are preserved. The command's claim-file label can be absolute when a linked
worktree's shared store is outside that checkout.

The state mutation guard reads `mutation_posture` (with legacy `posture`
fallback), ignores claims for another repository, and respects read-only leases.
A conflicting other-platform root mutation claim makes the actual worktree
state CLI refuse with exit 3 before changing the file.

The hook accepts `AURORA_SESSION_PLATFORM=codex|claude-code` or unambiguous
existing agent environment markers. Claude's checked-in hook commands explicitly
set its identity. Invalid, absent or conflicting evidence leaves `last_platform`
unchanged and produces no platform-labelled orphan marker. Commit provenance
continues to establish historical commit labels; a degraded import path no
longer invents author labels from the caller.

The pre-commit healer uses `--refresh-only`. It refreshes and stages mechanical
state without releasing a session-presence claim, recording session-close debt
or generating orphan markers. A conflicting root claim prevents the refresh.
A genuine Claude session close releases its own checkout-local presence before
deferring a protected write, avoiding a lease left active merely because another
platform is working. Orphan/auto-claim marker ownership stays checkout-local;
only claim JSON storage is shared.

## Verification

- Full root test scope: 770 passed, 41 skipped (final local run; see CI for the published revision).
- Coordination/provenance/hook/pre-commit focused group: 94 passed.
- The 23 new regression cases include actual Git linked worktrees, independent
  clones, foreign Git environment variables, bidirectional lease lifecycle,
  rejected mutations without file clobber, repository/read-only scoping,
  platform identity, and real pre-commit subprocesses with state staging.
- The actual healer preserves its caller's dirty tracked work and existing
  live-session marker, stages only the refreshed state, attributes Codex
  correctly and preserves prior attribution for an unidentified caller.
- New test module passes Ruff. Comparison against main finds no additional
  scoped rule/file diagnostics; broad repository Ruff still has existing
  findings. This is not a claim that the repository's lint debt is cleared.

Integration-gate and PR results are attached to the change's GitHub checks.
The integration gate remains read-only; no live runtime advancement is needed.

## Inventory repair

The integration gate exposed a pre-existing inventory gap for tracked `.claude`
configuration. A scratch scanner classified that folder as intake to be moved.
An explicit control-surface classification now keeps it at the root; its
scanner-derived manifest entry and workspace-map counts are synchronized.
Other canonical inventory entries and deliberate nested-repo pins are retained.
A regression verifies that future scans keep the hook configuration in place.

## Queue and follow-up

This patch resolves `session-claims-worktree-blind` and
`stop-hook-platform-attribution`. Existing linked checkouts must use the updated
tooling; legacy claims written solely in a linked checkout should be released
and recreated using the shared store, as documented in the claims workflow.
These machine-local advisory leases are not a distributed lock service.

The remaining CI consolidation pass and MCP v2 migration retain their own queue
scope. The current OpenAI API/model migration remains a separate completed
change and is not altered by this coordination repair.

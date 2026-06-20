# Branch Inventory - 2026-06-19

Scope: root control plane plus registered nested and remote-only repos in
`catalog/repo_registry.yaml`.

Posture: read-only inventory. No branches, refs, remotes, or worktrees were
pruned in this pass.

## Evidence Sources

- Local Git status, local branches, remote-tracking branches, and worktrees.
- Live Git/SSH `ls-remote --heads` for registered remotes.
- GitHub pull request API for public repos where available.
- Sandboxed `gh auth status` was not usable, but an escalated/real-context
  check later confirmed the `AUo959` token is healthy. Treat the earlier
  failure as a Codex sandbox/keyring context issue, not a token failure.
- Public GitHub API returned 404 for `CanonRec`, `DuelSim_v2.0`, and
  `aurora-cloudbank-symbolic1`; Git/SSH or `ls-remote` was used for branch
  accounting on those surfaces.
- Prior context checked: `reports/analysis/remote_branch_sweep__2026-06-11.md`.

## Pending / Planned Work From Session State

`catalog/session_state.json` currently has suspended active task
`salvage-operation-icloud-promotion-2026-06-12`.

Next recorded step:

- Review, push, or PR CloudBank branch
  `codex/l2-scenario-seed-simulation-initializer`.
- Keep `local/mesh-router-test-stabilization` separate unless explicitly
  requested.

Other pending items assigned to Codex/either:

- `roadmap-1.1`: collapse CloudBank CI sprawl.
- `roadmap-0.5`: decide CanonRec purpose or archive marker.
- `ga-ethics-hub-integration`: optional GA-backed ethics hub integration on a
  clean CloudBank branch.
- `narrative-promotion-continuation-2026-06`: queued root + CloudBank work.

Owner item:

- `0.1-aws-key`: verify redacted AWS IAM access-key ID deactivation.

## Current Dirty Worktrees

| Repo | Branch | Dirty files |
|---|---|---|
| root | `main` | `reports/automation/skill_sync_latest.json` |
| CloudBank | `codex/l2-scenario-seed-simulation-initializer` | `.env_status.json` |

## Open PR Map

| Repo | Open PRs | Notes |
|---|---:|---|
| root | 0 | Live API confirmed. |
| CloudBank | 15 | Includes 10 dependabot/copilot/claude PRs, #1026/#1027/#1014 drafts, and #1013 ready. |
| CanonRec | unknown by API | Public API returned 404; remote has only `main`. |
| DuelSim_v2.0 | unknown by API | Public API returned 404; remote has only `main`. |
| qgia-knowledge-library-main | 0 | Live API confirmed. |
| qgia-knowledge-spine-main | 0 | Live API confirmed. |
| zip_wizard | 2 | #10 `codex/conduct-full-code-review`, #9 dependabot. |
| aurora-cloudbank-symbolic1 | unknown by API | Public API returned 404; remote has only `main`. |
| AuroraOS | 4 | Three copilot branches and one dependabot branch. |
| cloudbank-quantum-en | 9 | Three copilot branches and six dependabot branches. |

## Branches With No Open PR

### root

Open PRs: none.

Local branches with work not merged into `origin/main`:

| Branch | Ahead | Behind | Upstream | Notes |
|---|---:|---:|---|---|
| `codex/charforge-capsule-implementation-2026-06-14` | 1 | 18 | remote branch exists | Attached stale worktree metadata; interrupted patch check confirmed unique commit. |
| `codex/explain-statechange-defense-for-sws` | 3 | 229 | remote branch exists | No open PR. |
| `codex/root-control-plane-local-2026-03-25` | 2 | 211 | remote branch behind by 1 | No open PR. |
| `codex/root-control-plane-sync-2026-04-01-mixed-backup` | 3 | 211 | none | Local-only. |
| `codex/root-reconstruct-recovered-protocols-2026-03-26` | 2 | 211 | none | Local-only. |
| `rescue/root-control-plane-dirty-workingcopy-2026-03-25` | 2 | 211 | none | Local-only. |
| `salvage/stash-gitwiz-pre-sync-2026-04-08` | 3 | 207 | none | Local-only. |
| `salvage/stash-qgia-json-pre-pr9` | 2 | 195 | none | Local-only. |
| `salvage/stash-root-diff-cleanup-2026-04-14` | 12 | 200 | none | Local-only. |

Remote branches with no open PR and commits ahead of `origin/main`:

`backup/prepopulate-main-2026-03-09`, `claude/repo-context-setup-NhAqS`,
`codex/charforge-capsule-implementation-2026-06-14`,
`codex/ci-pytest-artifacts-issue-18`,
`codex/cloudbank-guide-markers-2026-06-08`,
`codex/explain-statechange-defense-for-sws`,
`codex/gitwiz-sync-audit-canonical-2026-04-08`,
`codex/gpt-5-5-aurora-orion-upgrade-package-2026-04-29`,
`codex/perplexity-agent-coordination-bridge-issue-20`,
`codex/root-control-plane-local-2026-03-25`,
`codex/weekly-skill-audit-mesh-router-2026-06-01`,
`copilot/setup-github-remote-repo`, `copilot/setup-repo-configuration`,
`docs/moral-architecture-charter`.

Prior sweep notes already classify several of these as landed residue,
extracted, archival, or superseded. They should still be revalidated before
remote deletion.

### CloudBank

Current branch: `codex/l2-scenario-seed-simulation-initializer`.

Open PR heads accounted for:

`dependabot/npm_and_yarn/npm_and_yarn-2a4837647d`,
`copilot/replace-shallow-assertions-tier1`,
`dependabot/npm_and_yarn/docs/operational/reports/npm_and_yarn-efda44a5db`,
`dependabot/npm_and_yarn/frontend/npm_and_yarn-650b74d069`,
`dependabot/pip/pip-740b34f595`,
`dependabot/npm_and_yarn/frontend/tailwindcss-4.3.1`,
`claude/session-setup-task-selection-b6z7h5`,
`dependabot/npm_and_yarn/eslint-10.5.0`,
`dependabot/pip/services/nemo_service/nemo-toolkit-gte-2.7.3`,
`dependabot/pip/cli/black-gte-26.5.1`,
`dependabot/pip/cli/pytest-asyncio-gte-1.4.0`,
`codex/cloudbank-salvage-p3-forge-policy-2026-06-15`,
`codex/cloudbank-salvage-p2-ord-tests-2026-06-15`,
`codex/peer-review-stub-integration-audit`,
`codex/issue-1012-traceable-pr-automation`.

Local branches with no open PR and work not merged into `origin/main`:

| Branch | Ahead | Behind | Upstream | Notes |
|---|---:|---:|---|---|
| `codex/l2-scenario-seed-simulation-initializer` | 1 | 0 | none | Current branch; scenario adapter work; needs push/PR or explicit park. |
| `local/mesh-router-test-stabilization` | 1 | 24 | none | Local-only mesh test stabilization; intentionally separate. |
| `codex/cloudbank-pat-terminal-compat-2026-06-16` | 1 | 1 | `origin/main` | No open PR. |
| `codex/cloudbank-issue-1020-mesh-router-contract` | 1 | 23 | `origin/main` | Stale worktree metadata exists. |
| `codex/cloudbank-issue-1015-salvage` | 3 | 27 | gone | Stale worktree metadata exists. |
| `codex/cloudbank-issue-1070-ethics-engine` | 1 | 1 | stale remote-tracking ref | Remote branch deleted; local branch still present. |
| `codex/ci-workflow-repair` | 7 | 1692 | remote branch exists | No open PR. |
| `codex/cloudbank-command-chain-workflow-repair-2026-04-10` | 3 | 1690 | remote branch exists, local behind remote | No open PR. |
| `codex/cloudbank-issue-806-work` | 1 | 1515 | remote branch exists | No open PR. |
| `codex/cloudbank-issue-830-requirements-inventory` | 1 | 1521 | remote branch exists | No open PR. |
| `codex/pages-launchpad-utility` | 2 | 1692 | none | Local-only. |
| Older March rescue/reconcile/salvage branches | 6-14 | 1690-3458 | mixed/gone/local-only | Preserve until owner decides archive/delete. |

Remote branches with no open PR and commits ahead of `origin/main` include:

`claude/issue-798-token-budgets`, `claude/issue-829-integration-schema-validation`,
`claude/review-open-issues-4wbGv`, `claude/youthful-wright-BU0M2`,
`codex/central-dev-roadmap-review-intake`,
`codex/central-dev-roadmap-review-intake-v2`, `codex/ci-workflow-repair`,
`codex/cloudbank-command-chain-workflow-repair-2026-04-10`,
`codex/cloudbank-issue-806-work`, `codex/cloudbank-issue-830-requirements-inventory`,
`copilot/fix-failing-workflows-actions`, `copilot/improve-aurora-agent`,
`copilot/update-open-dependency-prs`, `feature/drift-autonomous-response`,
`feature/ethical-checkpoint-vault`, `feature/qgia-forecast-api`,
`feature/reconstruct-pr-510-mrm`, `worktree-agent-aed90d4638c913729`.

The 2026-06-11 sweep already marked several of the feature branches as landed
or documented residue. Revalidate before remote deletion.

### CanonRec

- Local `main` is ahead of `origin/main` by 22 commits.
- Remote has only `main`.
- No feature branches to prune.
- Public PR API was unavailable, so PR state could not be verified by API.

### DuelSim_v2.0

- Local `main` is aligned with `origin/main`.
- Remote has only `main`.
- No branches to prune.

### qgia-knowledge-library-main

- Local `main` is behind `origin/main` by 64 commits.
- Live remote heads: `main`, `feat/constellation-infrastructure`,
  `feat/tier-1-knowledge-documents`.
- Open PRs: 0.
- Local remote-tracking ref `origin/pr-3` exists, but the repo only fetches
  `main` by refspec and live `ls-remote --heads` did not show `pr-3`.
  Treat `origin/pr-3` as local stale/manual tracking residue, not a live head.

### qgia-knowledge-spine-main

- Local `main` is behind `origin/main` by 1 commit.
- Live remote heads: `main`, `critical-fixes-20260228`,
  `feat/constellation-infrastructure`.
- Open PRs: 0.

### zip_wizard

Open PR heads:

- `codex/conduct-full-code-review` (#10).
- `dependabot/npm_and_yarn/npm_and_yarn-3c67cbb9cd` (#9).

Remote branches with no open PR:

- `copilot/build-advanced-archive-manager`.
- `copilot/create-archive-manager-skeleton`.
- `copilot/implement-vulnerability-scanner`.

### aurora-cloudbank-symbolic1

- Remote has only `main`.
- Public PR API returned 404.
- No branch pruning surface found.

### AuroraOS

Open PR heads:

- `copilot/fix-67ddb327-1be5-4471-a994-89400a3108be` (#3, draft).
- `copilot/fix-6c956d4d-f23e-47d2-9045-947f42483416` (#4, draft).
- `copilot/fix-8e425050-0c0c-454c-8b9a-0a2a7e657a54` (#5).
- `dependabot/npm_and_yarn/npm_and_yarn-0faabe41b6` (#8).

Remote branches with no open PR:

- `feat/constellation-tools`.
- `feat/symbolic-core`.

### cloudbank-quantum-en

Open PR heads:

- `copilot/fix-64cdc9b3-a779-46ef-97d8-ab39d7d8a0c8` (#12, draft).
- `copilot/fix-992f9ed1-bdf8-4796-acd4-d7c91bbdc054` (#13, draft).
- `copilot/fix-9f339bdc-fd97-41b5-bcb0-c87bfd152706` (#11, draft).
- Six dependabot branches (#9, #17, #27, #29, #30, #31).

Remote branches with no open PR:

- `feat/aurora-cloudbank-rebuild`.

## Prune Queue

### Tier 1 - Low-risk local cleanup after approval

These local root branches are already merged into `origin/main`:

- `codex/continue-l1-entity-ledger-work`.
- `codex/root-cleanup-before-cloudbank-issues-2026-05-11`.
- `feat/warrant-lens`.

Dry-run worktree prune candidates:

- root: `worktrees/charforge-capsules-20260614`,
  `worktrees/Aurora_ORIONCORE_Directory_Main2`.
- CloudBank: `worktrees/cloudbank-salvage-p2-ord-tests-20260615`,
  `worktrees/cloudbank-codex-issue-1015-salvage`,
  `worktrees/cloudbank-codex-issue-1020-mesh-router-contract`,
  `worktrees/cloudbank-salvage-p3-forge-policy-20260615`.
- qgia-knowledge-library-main: `worktrees/qgia-library-pr3-20260504`.

Dry-run remote-prune candidate:

- CloudBank: `origin/codex/cloudbank-issue-1070-ethics-engine`.

### Tier 2 - Revalidate before remote deletion

Remote branches with no open PR that prior reports classify as landed residue,
extracted work, bot residue, or superseded branches. These should be checked
one branch at a time before deleting any remote ref.

Examples:

- root `codex/ci-pytest-artifacts-issue-18`.
- root `codex/perplexity-agent-coordination-bridge-issue-20`.
- root `codex/gitwiz-sync-audit-canonical-2026-04-08`.
- root `codex/gpt-5-5-aurora-orion-upgrade-package-2026-04-29`.
- CloudBank `feature/drift-autonomous-response`.
- CloudBank `feature/ethical-checkpoint-vault`.
- CloudBank `feature/qgia-forecast-api`.
- CloudBank `feature/reconstruct-pr-510-mrm`.

### Tier 3 - Do not prune without owner decision

- CloudBank `codex/l2-scenario-seed-simulation-initializer`: current scenario
  adapter branch; needs push/PR or explicit parking.
- CloudBank `local/mesh-router-test-stabilization`: committed local test
  stabilization; needs PR decision or explicit local archive.
- CanonRec local `main` ahead by 22 commits: publication/PR decision, not
  pruning.
- Remote-only no-PR feature branches in ZipWiz, AuroraOS, cloudbank-quantum-en,
  qgia-library, and qgia-spine: need repo-owner triage before deleting.
- Older March rescue/salvage branches in root and CloudBank: preserve until
  explicitly classified as archival duplicate, promoted, or discardable.

## Recommended Next Action

Start pruning only Tier 1:

1. Delete the three root local branches already merged into `origin/main`.
2. Run `git worktree prune` in root, CloudBank, and qgia-library to remove
   stale metadata only.
3. Run `git remote prune origin` in CloudBank to drop the stale remote-tracking
   ref.

After Tier 1 cleanup, handle publication decisions:

1. Push/PR CloudBank `codex/l2-scenario-seed-simulation-initializer`.
2. Decide whether `local/mesh-router-test-stabilization` becomes a PR or stays
   local.
3. Decide CanonRec `main` publication path.
4. Run a second revalidation pass on Tier 2 remote branch deletion candidates.

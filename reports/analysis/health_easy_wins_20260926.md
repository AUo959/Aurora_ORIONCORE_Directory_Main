# Project health: obvious fixes and easy wins — 2026-09-26

Scope: root control plane, five registered local repositories, and four remote-only repositories. User explicitly included all registered repositories. Review baseline: latest executive briefs (2026-08-26 and 2026-08-15), September 24 live review, and live GitHub heads on September 26. This is a bounded health pass, not an exhaustive security audit or runtime certification.

## Fixes completed

- Root main fast-forwarded from 59d8a5cb to published 8569f743. The prior f515cfef feature tip had an identical tree to the squash-merged main; retained the old branch and created `codex/health-easy-wins-20260926` from main. This closes the previously observed checkout freshness issue without replaying an already merged change.
- QGIA Spine fast-forwarded four published commits, c98c4592 to 1cf04fa6. These land the contract declaration, index refresh, full-history checkout, and removal of the nonconforming dispatcher. Regenerated its root pin through `registry_sync_heads.py`; ran the supported scan/plan/verify chain.
- CloudBank local Node installation was incomplete: 52/55 tests passed, with missing Express failures. `npm ci --ignore-scripts --no-audit --no-fund` restored the committed lockfile installation without changing source or lockfiles. After allowing ephemeral local test sockets, all 55 Node and 8 web tests passed. No service deployment or live simulation was performed.
- Closed stale `ace-capability-manifest-discovery`: `tools/ace/core.py:build_capability_index` delegates to schema-validated manifest discovery; existing tests validate the 20-entry catalog. Other broad ACE backlog claims remain for separate evidence review.
- Corrected AGENTS.md, reviewer orientation, and the migration document introduction: the legacy iCloud tree was deleted on July 4, as already recorded in the migration document section 6. Historical July 1 steps are preserved.
- ZIP Wizard: repaired the dashboard response type to match the existing server endpoint, including nullable replayability; formatted the eight files identified by failing CI. Temporary checkout `/private/tmp/aurora-health-20260926/zip-wizard`, branch `codex/fix-status-dashboard-types-20260926`, commit `1664a09`. No registry adoption, dependency upgrade, or server behavior change.

## Verified heads

GitHub default-branch heads observed before this pass's feature-branch publication:

| Repository | Head | Evidence scope |
|---|---|---|
| root | `8569f7436d6b57829fec6f2004850c9883132d2f` | local validation below |
| aurora-cloudbank-symbolic-main | `0fac980967ac7802a399f091fadf24bcd67b3126` | local validation below |
| CanonRec | `72f504b397a09cecc5e39250e9ae2cb7ea0f01f5` | local validation below |
| DuelSim_v2.0 | `0716f36ea5cf84707eba8c6ec16bead04809cf8c` | local validation below |
| qgia-knowledge-library-main | `5d59130b960e3403aa7944218f5ed6b97f69f6ca` | local validation below |
| qgia-knowledge-spine-main | `1cf04fa61878ce19b4c63b724395747f62a9b006` | local validation below |
| zip_wizard | `6acc34ed2e36aec16378db64c54a351028448248` | GitHub metadata / recent workflow sample |
| aurora-cloudbank-symbolic1 | `3530b82d6d18cf4ab8597d3a2ee627f9399b3e01` | GitHub metadata / recent workflow sample |
| AuroraOS | `373603dca02b741c2bd815dfcc2f07faced717f9` | GitHub metadata / recent workflow sample |
| cloudbank-quantum-en | `944934b9e0d54b09fb996b39bbd4b2b141ba5624` | GitHub metadata / recent workflow sample |

## Validation

| Surface | Result |
|---|---|
| Root non-simulation suite | 670 passed, 40 skipped, 50 deselected |
| Root workspace verifier | 0 blocking; 3 known warnings |
| Session schema | pass |
| Developer toolkit | 21/21 tools available; no install plan |
| Skills | all 16 project-owned skills in sync |
| CanonRec | strict validator: 900 tracked files, 0 findings; 3 tests pass |
| DuelSim | quick release gate passes; report redirected to temporary evidence folder |
| QGIA Library | contract validator passes; 9 tests pass |
| QGIA Spine | contract validator passes; 7 tests pass |
| CloudBank Python | pip check clean; 45 canon/security/lock/dependency tests pass |
| CloudBank JavaScript | 55 Node + 8 web tests pass after local installation repair |
| ZIP Wizard | TypeScript and full formatting checks pass; 39 tests pass; build passes; lint exits 0 with 342 warnings |

Local JS validation used Node 26.5.0. CloudBank declares Node 22.x and ZIP Wizard CI uses Node 22: remote CI remains the supported-version confirmation. CloudBank Python emitted a Starlette/httpx deprecation warning. ZIP Wizard reports old browsers data and a large bundle advisory. No full CloudBank Python, browser E2E, live runtime, deployment, or simulation suite was run.

## Remaining findings (outside easy-win scope)

- Known root warnings: two historical August 11/15 simulation artifacts retain sandbox provenance; four remote-only entries have no canonical checkout; queue reviews remain overdue (39 before, 38 after the verified closure). Preserve original simulation evidence; do not rewrite provenance or renew queue dates without review.
- Devkit warnings: paused toolkit-watch automation and stale CloudBank `.env_status.json`. Live pip/test evidence passes, but the environment receipt has not been regenerated: its owning setup script performs broader installation. A paused automation is not authorization to resume it.
- Remote prototype `aurora-cloudbank-symbolic1`: Dependabot fails because its pnpm requirement is version 6. Updating the package manager and validating the lockfile is a separate dependency migration.
- ZIP Wizard main's September 2 CI failures were TypeScript fields and eight formatting files; fixed on the feature branch. Existing lint warnings are retained rather than expanding into a broad cleanup.
- Root, CanonRec, DuelSim, and QGIA Library have successful recent workflow samples. CloudBank's recent sample contains cancelled knowledge-aggregator runs and successful project automation; this sample does not establish all required checks are green. QGIA Spine's sample includes old successful dispatcher runs despite its current removal: historical workflow success is not evidence a dispatcher remains active. AuroraOS and cloudbank-quantum-en have successful recent samples, not local build validation.
- The integration gate's initial session-claim check detected this pass's own active editing claims. All other integration checks passed; final claim-free verification is recorded below.

## Evidence and boundaries

Raw command logs and GitHub metadata: `/private/tmp/aurora-health-20260926/`. Durable GitHub head/workflow sample: `health_easy_wins_20260926_github.json`. This receipt records outcomes separately from local environment failures: sandbox DNS and socket restrictions cleared when rerun with appropriate access. The first CloudBank Python invocation named a nonexistent test file and collected no tests; the corrected four-file invocation produced the reported 45 passes.

Root and nested Git boundaries stayed separate. No remote configuration changes, branch deletion, canon promotion, L1 INIT/advance/resume, or merges were performed. QGIA Spine checkout synchronization changes local state only; ZIP Wizard publication is a separate draft review change.

## Publication and final gates

- ZIP Wizard draft PR: https://github.com/AUo959/zip_wizard/pull/13 (`1664a09`).
- Final integration gate: all five checks and all six commands pass after releasing this session's claims.
- Registry check: 5 local pins in sync, 4 remote-only entries skipped.
- Root cleanup is a separate draft PR; neither PR is merged by this pass.

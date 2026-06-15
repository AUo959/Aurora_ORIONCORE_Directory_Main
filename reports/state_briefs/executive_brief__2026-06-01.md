# Aurora / ORIONCORE — Executive Decision Brief

- **Generated:** 2026-06-01T17:36Z
- **Scope:** Root control-plane repo + 5 nested repos
- **Pipeline:** `aurora-exec-brief-pipeline` contract (Decision Snapshot / Top Risks / Operational Signals / Recommended Actions / Evidence Appendix)
- **Posture:** Read-only synthesis. No canon promotion, no nested-repo mutation, no command execution, no GitHub push.
- **Staleness datum:** current root HEAD `286d085` committed `2026-06-01T03:04:26Z`; artifacts generated before that timestamp are flagged stale.

---

## Decision Snapshot

**Overall status: GREEN on health, AMBER on integration only.** No blocking findings exist in the deterministic signal set. Workspace hygiene improved substantially this week: the root branch landed in `main`, branch sprawl shrank, and the root working tree is essentially clean. The remaining open work is the recovery-review backlog plus an unpushed root delta and an unmerged CloudBank feature branch.

| Dimension | State | Read |
|---|---|---|
| Root workspace integrity | `workspace_verify` PASS, 0 findings (2026-06-01 03:02Z, ~1.5 min before HEAD) | Healthy |
| Root Git working tree | **Clean tracked surface** — 2 untracked paths only (`.claude/settings.local.json`, `reports/automation/devkit_watch_2026-06-01.md`) | Healthy |
| Root branch | **Now on `main` directly** (last week: `codex/root-cleanup-before-cloudbank-issues-2026-05-11`) | Improved |
| Root vs `origin/main` | **2 commits ahead, 0 behind** — unpushed: `286d085` (artifact refresh) + `9696e40` (GUMAS mutation auth in root gate) | Integration gap (small) |
| Nested repos (5) | All on configured branches; **`aurora-cloudbank-symbolic-main` on feature branch, dirty (4 paths), 61↑/1↓ vs origin/main, no upstream tracking**; other 4 clean and in sync | Mostly healthy |
| Mission Control | `attention` — 7 inbox items, **0 blocking**, 6 approval-required (stale; reports a 12-path dirty tree no longer present) | Backlog only (stale) |
| Recovery backlog | 1,017 candidates discovered, 100 surfaced, **36 restricted (secret/key signal)** | Needs P1 triage |
| Dev toolchain | `READY` — **21/21 tools OK**, 0 install-plan items | Healthy (improved) |
| Governance artifact freshness | 6 of 7 `*_latest.json` artifacts predate HEAD (committed in the HEAD refresh, but generated 5–6 h prior); GITWIZ audit 25 h stale and references HEAD `96d482e1` | Refresh needed (esp. GITWIZ) |

**One-line:** The big integration risk from prior weeks (18-commit unmerged root branch) is resolved; the new critical path is (1) triaging the 36 secret-flagged recovery candidates, (2) pushing the 2 unpushed root commits and deciding the CloudBank feature-branch landing strategy, and (3) refreshing the GITWIZ audit so the sync picture matches current HEAD.

---

## Top Risks

| # | Risk | Severity | Evidence |
|---|---|---|---|
| 1 | **36 restricted recovery candidates flagged as secret/key material.** Located in `intake/`, `_staging/`, `archives/`. Potential live credentials in early local work. Unchanged from prior briefs — still untriaged. | **P1 / High** | `workspace_recovery_index_latest.json` — `signal_counts.secret_or_key_material: 36`; Mission Control P1 inbox item |
| 2 | **CloudBank on long-lived feature branch with no upstream tracking, 61 ahead / 1 behind `origin/main`, dirty 4 paths.** Branch `codex/cloudbank-gumas-mutation-auth-2026-05-25` carries the GUMAS-mutation-auth work; merge cost and review scope grow with each additional commit. *New scope this week — branch went from `main`/in-sync to a divergent feature line.* | **Medium–High** | `git -C ...aurora-cloudbank-symbolic-main rev-list --count origin/main...HEAD` = `1 61`; `git status --porcelain` = 4M; no `branch.<x>.remote` tracking config |
| 3 | **2 unpushed root commits.** `9696e40` (GUMAS mutation auth in root gate) and `286d085` (artifact refresh) on `main` ahead of `origin/main`. Small delta, but means GitHub-side automation (CI, branch protection, GITWIZ sync) is observing a stale remote. | Medium | `git rev-list --left-right --count origin/main...HEAD` = `0 2`; `git log origin/main..HEAD` |
| 4 | **Stale `origin` fetches.** Root last fetched 2026-05-31 14:45Z (~27 h old); CloudBank last fetched 2026-05-31 20:44Z (~21 h old). All ahead/behind figures are computed against a slightly stale remote ref. | Low–Medium | `.git/FETCH_HEAD` mtimes |
| 5 | **Branch sprawl reduced but not cleared — 9 local branches besides `main`.** 3 are fully contained in `main` (safe-delete): `codex/continue-l1-entity-ledger-work`, `codex/root-cleanup-before-cloudbank-issues-2026-05-11`, `feat/warrant-lens`. 6 carry unmerged commits and need keep/merge/drop decisions. | Medium | `git rev-list --count main..<branch>` enumeration |
| 6 | **6 of 7 governance artifacts predate current HEAD.** The 6 `*_latest.json` files were regenerated 2026-05-31 21:04–21:08Z and then committed in the HEAD commit at 03:04Z — so they're freshest-on-record but technically pre-HEAD. The Mission Control inbox still references "12 in-progress paths" in root, no longer accurate. The GITWIZ audit is doubly stale — generated 2026-05-31 02:19Z, captures HEAD `96d482e1` (current is `286d085`), reports `dirty:false`. | Low–Medium | `generated_at` fields vs HEAD commit time; `aurora_mission_control_latest.json` git_state item; `GITWIZ_SYNC_AUDIT__2026-05-31T021949Z.json` |
| 7 | **`CanonRec` nested repo stale ~93 days** (last commit 2026-02-28). Unclear if intentionally frozen or drifting. Unchanged from last two weeks. | Low–Medium | `git -C GUMAS_SIM_2.5/CanonRec log -1` |
| 8 | **Long-tail recovery backlog.** 1,017 candidates discovered (was 1,011), 100 surfaced under cap; routed across 5 hint targets. Review cadence, not a defect. | Low | `workspace_recovery_index_latest.json` summary |
| 9 | **Runtime on Python 3.9.6** (system interpreter). Past upstream EOL; devkit still reports OK. Forward maintenance item. | Low | `aurora_devkit_latest.json` toolchain entry |

---

## Operational Signals

### Root control-plane repo

- **Branch:** `main` (direct — feature-branch workflow was landed since last brief)
- **HEAD:** `286d085` — `chore(reports): refresh root operator artifacts` (committed 2026-06-01T03:04:26Z)
- **Working tree:** clean on tracked files; 2 untracked paths only (`.claude/settings.local.json` IDE-local; `reports/automation/devkit_watch_2026-06-01.md` fresh receipt)
- **vs `origin/main`:** 2 ahead, 0 behind (`git rev-list --left-right --count origin/main...HEAD` = `0  2`)
  - `9696e40` feat(command-safety): require GUMAS mutation auth in root gate
  - `286d085` chore(reports): refresh root operator artifacts
- **Local branches (excl. `main`):** 9 (was 17)
- **Remote:** `git@github-aurora:AUo959/Aurora_ORIONCORE_Directory_Main.git` (SSH, as preferred)
- **Last `origin` fetch:** 2026-05-31T14:45Z (~27 h old) — re-fetch before sync decisions
- **CI:** `.github/workflows/ci.yml` present; pre-commit + pre-push hooks present under `.githooks/`

### Nested repos

| Repo | Branch | Working tree | Sync | Last commit | Age |
|---|---|---|---|---|---|
| `aurora-cloudbank-symbolic-main` | **`codex/cloudbank-gumas-mutation-auth-2026-05-25`** (no upstream) | **dirty (4 paths)** | **61↑ / 1↓ vs `origin/main`** | `152634b2` 2026-05-25 — fix: require auth for GUMAS mutations | ~7 days |
| `DuelSim_v2.0` | main | clean | in sync (0/0 vs origin/main) | `0716f36` 2026-05-19 — feat: add DuelSim standalone app | ~13 days |
| `qgia-knowledge-spine-main` | main | clean | in sync (0/0 vs origin/main) | `2491371` 2026-04-23 — bootstrap spine closed-loop artifacts | ~39 days |
| `qgia-knowledge-library-main` | main | clean | in sync (0/0 vs origin/main) | `4d0c975` 2026-04-22 — bootstrap library closed-loop artifacts | ~40 days |
| `CanonRec` | main | clean | in sync (0/0 vs origin/main) | `259bdc1` 2026-02-28 — Survey main directory for context | ~93 days |

CloudBank dirty paths: `.env_status.json`, `.github/dependabot.yml`, `src/middleware/fastapi_security.py`, `tests/test_security_middleware.py` — same security-middleware + Dependabot change set as last week, unmoved. The branch has no `branch.<x>.remote`/`merge` tracking config, which is why upstream-relative status is empty without specifying `origin/main`.

### Root branch inventory

Safe-delete candidates (`ahead_of_main = 0`):

- `codex/continue-l1-entity-ledger-work`
- `codex/root-cleanup-before-cloudbank-issues-2026-05-11` *(last week's working branch — fully landed)*
- `feat/warrant-lens`

Need keep/merge/drop decision (unmerged commits):

- `codex/gitwiz-sync-audit-canonical-2026-04-08` (+10)
- `codex/explain-statechange-defense-for-sws` (+3)
- `codex/root-control-plane-sync-2026-04-01-mixed-backup` (+3)
- `codex/root-control-plane-local-2026-03-25` (+2)
- `codex/root-reconstruct-recovered-protocols-2026-03-26` (+2)
- `rescue/root-control-plane-dirty-workingcopy-2026-03-25` (+2)

### Deterministic governance signals

- **`workspace_verify` (2026-06-01 03:02Z — FRESH, 1.5 min before HEAD):** PASS — 0 findings / 0 blocking / 0 warnings.
- **`devkit` (2026-05-31 21:04Z — committed in HEAD refresh):** `READY` — **21/21 tools OK** (toolchain expanded from 19/19; 0 install-plan items).
- **`mission_control` (2026-05-31 21:08Z — committed in HEAD refresh):** `attention` — 7 operator-inbox items, 0 blocking, 6 approval-required (1 P1 / 6 P2). Build lanes: 6 ready / 0 attention / 0 blocked. Its `git_status` sub-report reads `dirty` with 12 changed paths and `branch: main...origin/main` — the branch identity is now correct (root is on `main`) but the path count overstates current hygiene (tracked tree is clean; only 2 untracked items remain).
- **`recovery_index` (2026-05-31 21:04Z — committed in HEAD refresh):** `READY` — 2,380 files scanned (was 2,371); 1,017 candidates discovered (was 1,011); 100 surfaced under cap; **36 restricted** (unchanged). Routing hints: cloudbank 51, root 31, spine 13, review-required 4, library 1.
- **`recommendations` (2026-05-31 21:08Z — committed in HEAD refresh):** `open` — 7 advisory items, all in `recovery_review` (6) + `git_state` (1); 0 blocking; 6 approval-required (1 P1 / 6 P2).
- **`confidence_audit` (2026-05-31 21:04Z — committed in HEAD refresh):** PASS — score 0.93 (band `high`), 0 user alerts.
- **`gitwiz` sync audit (2026-05-31 02:19Z — STALE, ~25 h pre-HEAD):** root reports `in_sync` but the audit captured HEAD `96d482e1031ef93e47caca03d4f4fc41970f9603` and `dirty:false`; current HEAD is `286d085` and the audit predates two subsequent commits (`9696e40`, `286d085`). Sync picture no longer reflects live state.

### Week-over-Week Delta (vs `executive_brief__2026-05-25`)

| Axis | Last week (2026-05-25) | This week (2026-06-01) | Change |
|---|---|---|---|
| Root branch | `codex/root-cleanup-before-cloudbank-issues-2026-05-11` | `main` | ✅ Improved — feature branch landed |
| Root HEAD | `42faeba` (2026-05-24) | `286d085` (2026-06-01) | Advanced 2+ commits past the landed PR |
| Root vs `origin/main` | 18 ahead / 0 behind | **2 ahead / 0 behind** | ✅ Improved — 16-commit integration gap closed |
| Root working tree | Dirty — 15 paths (9 M + 6 ??) | **2 untracked, 0 modified** | ✅ Improved — WIP committed/landed |
| Local branch count (excl. `main`) | 17 | **9** | ✅ Improved — 8 branches retired (incl. 9-of-17 safe-delete cohort) |
| Nested repos dirty | 1 of 5 (CloudBank, 4 paths) | 1 of 5 (CloudBank, same 4 paths) | No change — CloudBank WIP unmoved |
| CloudBank sync | `main`, in sync (0/0) | **Feature branch, no upstream, 61↑/1↓ vs `origin/main`** | ⚠️ Regressed (scope) — divergence grew; same WIP now on a long-lived branch |
| Top-risk count | 8 | 9 | +1 net (added: CloudBank-divergence, stale-fetch, unpushed-root; retired: 15-path-dirty-tree, root-branch-18-commit-gap as separate risks) |
| Recovery backlog (discovered / surfaced / restricted) | 1,011 / 100 / 36 | **1,017 / 100 / 36** | +6 discovered candidates; restricted unchanged |
| Verifier status | PASS (2026-05-25 13:50Z) | PASS (2026-06-01 03:02Z) | Stable — regenerated fresh |
| Devkit status | `READY` 19/19 | **`READY` 21/21** | ✅ Tool coverage broadened (2 new tracked tools) |
| Stale governance artifacts | 5 flagged (mission_control, recovery_index, recommendations, confidence_audit, gitwiz) | 6 flagged pre-HEAD; only GITWIZ is operationally stale (the others were just committed in the HEAD refresh) | Mixed — most "stale" entries are now part of HEAD's own refresh receipt; only GITWIZ remains a true drift signal |

**Net read:** Major hygiene wins this week — the long-standing 18-commit root branch landed, the working tree cleaned up, branch sprawl roughly halved, and the operator-artifact set was committed as part of HEAD. The new exposure is CloudBank: the security-middleware + Dependabot WIP that was a parallel feature scope last week is now riding a long-lived feature branch with no upstream tracking and a 61-commit divergence from its `origin/main`. The recovery-review P1 (36 restricted) is unchanged and remains the top backlog item.

---

## Recommended Actions

Ordered by priority. All are advisory; none have been executed.

1. **[P1] Triage the 36 restricted (secret/key) recovery candidates.** Treat as a credential-exposure review, not a promotion task. Inspect each for live keys/tokens, rotate anything real, then mark dispositioned. Do **not** promote restricted candidates to canon. *Driver:* `make recovery-report`; review surface `reports/analysis/workspace_recovery_index_latest.json`. Optional automation: schedule a weekly `recovery_review` digest into Gmail so the queue gets a forcing function.

2. **[P2] Decide and execute the CloudBank feature-branch landing strategy.** `codex/cloudbank-gumas-mutation-auth-2026-05-25` is 61 ahead / 1 behind `origin/main`, dirty 4 paths, no upstream tracking. Options:
   - **Land:** commit the 4 dirty paths into a final review commit, `git push -u origin codex/cloudbank-gumas-mutation-auth-2026-05-25`, open PR via `python3 skills/gitwiz-github-manager/scripts/gitwiz_pr_packet.py --repo-name aurora-cloudbank-symbolic-main --base origin/main`, rebase the 1 behind commit.
   - **Park:** set upstream explicitly, push as draft, and capture a CloudBank-specific roadmap entry — long-lived feature branches need an exit date.
   - **Bisect:** if any of the 61 commits are out-of-scope sweeps, split into a stack of smaller PRs.

3. **[P2] Push the 2 unpushed root commits.** `git fetch origin && git push origin main` (HEAD `286d085`, prior `9696e40`). Re-run the GITWIZ audit afterward so the audit reflects the pushed state. *Automation hook:* this is a natural place to wire a post-push GitHub Actions job that re-runs `make mission-control-report` and uploads the regenerated artifacts.

4. **[P2] Re-fetch all remotes before any further sync decisions.** Root fetch is ~27 h old, CloudBank ~21 h old. `git fetch --all --prune` in each, then re-read ahead/behind. Wire into pre-push: a `.githooks/pre-push` lightweight `git fetch` step keeps divergence figures honest.

5. **[P2] Refresh the GITWIZ sync audit.** It is the one artifact that is operationally stale — it captures HEAD `96d482e1` while live HEAD is `286d085`, and it cannot see the unpushed commits or the CloudBank feature-branch divergence. *Driver:* `gitwiz-github-manager` all-repo audit.

6. **[P3] Prune the 3 safe-delete branches.** `git branch -d codex/continue-l1-entity-ledger-work codex/root-cleanup-before-cloudbank-issues-2026-05-11 feat/warrant-lens` — all are fully contained in `main`. For the 6 unmerged branches (`gitwiz-sync-audit-canonical-2026-04-08` +10, `explain-statechange-defense-for-sws` +3, `root-control-plane-sync-2026-04-01-mixed-backup` +3, `root-control-plane-local-2026-03-25` +2, `root-reconstruct-recovered-protocols-2026-03-26` +2, `rescue/root-control-plane-dirty-workingcopy-2026-03-25` +2) record a keep/merge/drop disposition per branch in `catalog/repo_registry.yaml` or a successor catalog.

7. **[P3] Confirm `CanonRec` status.** Decide whether the ~93-day freeze is intentional; if active, schedule the next update; if archived, record it in `catalog/repo_registry.yaml`.

8. **[P3] Work the recovery review queue by target repo.** 100 surfaced candidates route to cloudbank (51), root (31), spine (13), review-required (4), library (1). Each promotion still requires owner-surface review + receipt/PR.

9. **[P3] Plan the Python 3.9.6 → supported-runtime migration.** Not urgent (devkit still reports OK at 21/21), but EOL drift compounds. Scope a move to a current 3.12+ interpreter as a forward maintenance item.

### Automation opportunities

- **GitHub PR hygiene:** the GITWIZ skill already drafts PR packets and runs sync audits; a scheduled all-repo audit (weekly, paired with this brief) would keep the 6-repo fleet continuously reconciled, especially with CloudBank now diverging.
- **CI gate on the brief itself:** the exec-brief pipeline supports `--strict` (non-zero exit on high risks/parse failures) — wireable into `.github/workflows/ci.yml` as a briefing-quality gate.
- **Pre-push fetch + audit:** add a `.githooks/pre-push` step that runs `git fetch --all --prune` and the workspace_verify pass so unpushed-commit + stale-fetch risks self-resolve.
- **Gmail digest:** the recovery-review P1 has now sat unchanged across three briefs; an emailed weekly summary of restricted candidates with the file names redacted would create a forcing function without surfacing the sensitive content itself.

---

## Evidence Appendix

| Signal | Artifact | Timestamp | Freshness vs HEAD |
|---|---|---|---|
| Workspace integrity | `reports/analysis/workspace_verify_latest.json` | 2026-06-01 03:02Z | ~1.5 min pre-HEAD; current |
| Operator inbox | `reports/analysis/aurora_mission_control_latest.json` | 2026-05-31 21:08Z | ~6 h pre-HEAD; committed in HEAD refresh; understates clean tree |
| Recovery candidates | `reports/analysis/workspace_recovery_index_latest.json` | 2026-05-31 21:04Z | ~6 h pre-HEAD; committed in HEAD refresh |
| Advisory recommendations | `reports/analysis/aurora_recommendations_latest.json` | 2026-05-31 21:08Z | ~6 h pre-HEAD; committed in HEAD refresh |
| Dev toolchain | `reports/analysis/aurora_devkit_latest.json` | 2026-05-31 21:04Z | ~6 h pre-HEAD; committed in HEAD refresh; toolchain expanded to 21/21 |
| Confidence audit | `reports/analysis/aurora_confidence_audit_latest.json` | 2026-05-31 21:04Z | ~6 h pre-HEAD; committed in HEAD refresh |
| Root Git sync audit | `reports/analysis/gitwiz/GITWIZ_SYNC_AUDIT__2026-05-31T021949Z.json` | 2026-05-31 02:19Z | ~25 h pre-HEAD; **operationally stale** — references HEAD `96d482e1`, current is `286d085` |
| Prior brief (reference) | `reports/state_briefs/executive_brief__2026-05-25.md` | 2026-05-25 13:58Z | Used for WoW delta |

**Method note.** All repo states verified live (`git status`, `git rev-list`, `git log`, `git remote`, `.git/FETCH_HEAD`) at generation time. Deterministic governance figures are read from the workspace's own `*_latest.json` artifacts; where an artifact predates current HEAD it is flagged with the staleness datum above (HEAD `286d085` @ 2026-06-01T03:04:26Z). No nested repos were mutated, no Aurora command grammar was executed, no GitHub push occurred. Read-only posture preserved per `aurora-exec-brief-pipeline` contract.

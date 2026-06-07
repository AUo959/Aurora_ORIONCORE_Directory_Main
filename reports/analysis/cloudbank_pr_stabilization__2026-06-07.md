# CloudBank PR Stabilization Receipt - 2026-06-07

## Scope

- Target repo: `AUo959/aurora-cloudbank-symbolic`
- Root coordination repo: Aurora / ORIONCORE control plane
- Nested checkout mutation: none
- GitHub mutation: closed stale draft PRs `#843` and `#864` with explanatory comments
- Local edit surface: root receipt only

## Live Sources

- Open PRs: `https://api.github.com/repos/AUo959/aurora-cloudbank-symbolic/pulls?state=open&per_page=100`
- Open issues: `https://api.github.com/repos/AUo959/aurora-cloudbank-symbolic/issues?state=open&per_page=100`
- Current `main`: `https://api.github.com/repos/AUo959/aurora-cloudbank-symbolic/git/ref/heads/main`
- GitHub connector: used for PR comments, review threads, and PR state updates
- Shell `gh`: not usable for this pass; token remained invalid/rate-limited

## Pre-Action Snapshot

- Refreshed during implementation on 2026-06-07.
- Current CloudBank `main`: `7fba7fc39e03606cb34930a8e190d122ceb1e92a`
- Open PRs before cleanup: `39`
- Open non-PR issues before cleanup: `58`
- New PRs observed after the planning pass: `#903`, `#904`, `#905`, `#906`
- Active local CloudBank claims: none
- Canonical nested checkout remained dirty on a gone Codex branch and was not used.

## Actions Taken

- `#843` closed unmerged.
  - Reason: stale draft from old Codex branch, linked issue `#830` already closed, base `52563a4abc261d52a0ca1885da11e697404a18a7` older than current `main`, unresolved review threads, PR Evaluation `NEEDS WORK`, Codacy `6` new issues.
  - Comment posted: `https://github.com/AUo959/aurora-cloudbank-symbolic/pull/843#issuecomment-4643172066`
- `#864` closed unmerged.
  - Reason: stale draft from old Codex branch, linked issue `#806` already closed, base `fdf6e480a74c6264cf103a5a97f6b6542b507338` older than current `main`, unresolved InsightLedger fail-closed/env parsing review threads, PR Evaluation `NEEDS WORK`, SonarQube `2` new issues.
  - Comment posted: `https://github.com/AUo959/aurora-cloudbank-symbolic/pull/864#issuecomment-4643173047`

## Post-Action Snapshot

- Open PRs after cleanup: `37`
- Open non-PR issues after cleanup: `58`
- GitHub repo `open_issues_count`: `95` (`37` open PRs + `58` open non-PR issues)
- Remaining draft PRs: `#837`, `#860`, `#883`, `#884`, `#885`, `#886`, `#887`, `#888`, `#889`, `#890`, `#891`, `#892`, `#893`, `#894`, `#895`, `#896`, `#897`, `#898`, `#899`, `#900`, `#901`, `#902`, `#903`, `#904`, `#905`, `#906`
- Remaining non-draft dependency PRs: `#848`, `#849`, `#850`, `#851`, `#852`, `#853`, `#854`, `#855`, `#856`, `#857`, `#880`
- Remaining stale-base PRs: `#837`, `#848`, `#849`, `#850`, `#851`, `#852`, `#853`, `#854`, `#855`, `#856`, `#857`, `#860`, `#880`, `#883`, `#884`, `#885`, `#886`, `#887`
- Current-base PRs: `#888`, `#889`, `#890`, `#891`, `#892`, `#893`, `#894`, `#895`, `#896`, `#897`, `#898`, `#899`, `#900`, `#901`, `#902`, `#903`, `#904`, `#905`, `#906`

## Next Gates

- Do not merge drafts; require ready-for-review state plus fresh checks on current `main`.
- Treat the dependency PRs as stale until `#902` lockfile policy is decided.
- Keep `#837` open for now; it is broad and likely needs extraction before closure.
- Investigate `#898`, `#904`, and `#905` before review: all currently share head SHA `2c9fbf22f2dc6e32304c5d0e735738806b99aca4`, while `#905` is labeled `ci: failed`.
- Continue using the root CloudBank broker before any Codex code edits, and use a clean CloudBank worktree from `origin/main`.

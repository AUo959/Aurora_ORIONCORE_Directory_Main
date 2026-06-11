---
name: gitwiz-github-manager
description: Manage Git and GitHub operations for the Aurora / ORIONCORE workspace with project-specific safety rules. Use when users ask to configure remotes, create GitHub repos, scan local-vs-remote drift, draft PR packets, publish branches, back up or replace bootstrap GitHub history, push root or nested repos, diagnose auth/SSH issues, or perform repo-aware GitHub setup across the root control-plane repo and named nested repos. Do not use for general code changes, CI failure debugging, or PR comment handling unless the task is primarily about repo publishing and remote state.
author: Aurora ORIONCORE
---

# GITWIZ GitHub Manager

Project-specific Git/GitHub workflow for Aurora / ORIONCORE.

## Use When

Trigger on requests such as:

- "set up the remote"
- "sync this repo to GitHub"
- "publish this branch"
- "make this repo native to GitHub"
- "create the GitHub repo for this nested repo"
- "scan what is missing from GitHub"
- "audit local vs remote drift"
- "draft the PR to sync this repo"
- "replace the bootstrap repo with the real history"
- "configure SSH for GitHub"
- "push main safely"
- "back up remote main before force push"
- "GITWIZ"

## Repo Map

Treat the workspace as multiple repos with different responsibilities:

- Root control-plane repo:
  - current repo or workspace root
- Nested repos:
  - `Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`
  - `GUMAS_SIM_2.5/CanonRec`
  - `GUMAS_SIM_2.5/DuelSim/DuelSim_v2.0`

Rules:

- Never assume a request for the root repo also applies to nested repos.
- Never add, change, or push nested repo remotes unless the user names that repo explicitly.
- Read `catalog/repo_registry.yaml` before operating on nested repos.
- In Codex worktrees, nested repo paths may not exist under the worktree root even if they exist in the canonical workspace. Distinguish worktree paths from canonical workspace paths before running hooks or validation.

### Named Repo Selection

When the user asks to publish or configure "the repo", resolve the target explicitly:

- `root`
  - the workspace control-plane repo
- `aurora-cloudbank-symbolic-main`
  - `Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`
- `CanonRec`
  - `GUMAS_SIM_2.5/CanonRec`
- `DuelSim_v2.0`
  - `GUMAS_SIM_2.5/DuelSim/DuelSim_v2.0`

If the user does not name the target and multiple repos are plausible, ask one short clarification question.

### Execution Location Rule

Choose the working directory that actually contains the target repo:

- use the current worktree for the root repo when operating on the root repo
- use the canonical workspace path for nested repos when those repos are absent from the current Codex worktree
- avoid changing repo registry paths just to satisfy a transient Codex worktree limitation

## Important Local Truths

- Read `AGENTS.md` first when operating in the root repo. It is the fast operational reference for persistence, sync boundaries, repo scope, and current GitHub expectations.
- `.gitwiz` in the workspace manifest is an ignored local artifact slot, not the source of truth for this skill.
- This skill should live in versioned repo content and may also be copied into `~/.codex/skills/` for local availability.
- Prefer SSH remotes for ongoing use.
- Prefer preserving remote history by branching it before replacing it.

## Bundled Scripts

Use these instead of improvising audit logic:

- `scripts/gitwiz_sync_audit.py`
  - scans root or named nested repos
  - reports local dirty state, remotes, upstream tracking, ahead/behind, and sync actions
  - writes JSON and Markdown reports
- `scripts/gitwiz_pr_packet.py`
  - drafts a PR packet from the current branch against a base ref
  - writes JSON and Markdown packets
  - use after the branch is committed and pushed, or when you need a PR-ready summary

Default output location for both:

- `reports/analysis/gitwiz/`

## Standard Workflow

### 1. Inspect First

Always start with:

- `git remote -v`
- `git branch -vv`
- `git status --short`
- `git rev-parse HEAD`
- `git rev-parse refs/heads/main` when `main` exists

For remote work:

- `git ls-remote --heads <remote>`
- `git fetch <remote> main` when you need to inspect divergence

If `gh` exists, check `gh auth status`. If not, use plain Git and SSH.

Important interpretation rule:

- in Codex, `gh auth status` can fail inside the normal sandbox even when the
  machine's real GitHub auth is healthy
- if SSH `git push` works or the GitHub connector can view or create PRs, do not
  treat the first sandboxed `gh` failure as proof of broken credentials
- rerun the `gh` command with escalated execution before diagnosing auth
- if the escalated `gh` command succeeds, record it as a sandbox or
  execution-context issue and continue using SSH Git plus the GitHub connector

### 2. Distinguish the Operation

Choose the right lane:

- Remote setup:
  - add or update `origin`
  - prefer SSH
- Native GitHub repo creation:
  - create a private repo first when no remote exists and no URL was supplied
  - then add `origin`
- Publish branch:
  - push current branch with `-u`
- Publish local `main` without checkout:
  - use direct ref push when the worktree is dirty
- Replace bootstrap remote history:
  - back up current remote branch first
  - then use `--force-with-lease`
- Nested repo publishing:
  - only after explicit user instruction naming the nested repo
- Sync audit:
  - run `gitwiz_sync_audit.py`
  - inspect suggested actions before mutating Git state
- PR drafting:
  - run `gitwiz_pr_packet.py`
  - use the generated packet as the basis for a GitHub PR body

### 2A. Native GitHub Repo Creation

When the user wants a "native remote" or asks to create the GitHub repo:

1. Inspect whether a remote already exists.
2. If a URL was provided, use it.
3. If no URL was provided:
   - use `gh repo create` when `gh` is installed and authenticated
   - otherwise stop and ask the user for the GitHub repo URL or ask them to create the empty repo first
4. Prefer `private` repos unless the user explicitly says otherwise.
5. After repo creation, add `origin`, verify the remote branch state, then publish the requested branch.

Do not assume GitHub CLI exists. Fall back to SSH plus a user-provided URL when it does not.

### 2B. Local-vs-Remote Sync Audit

When the user wants to know whether GitHub faithfully reflects local project state:

1. Run `gitwiz_sync_audit.py`.
2. Use `--repo root`, `--repo all`, or a named nested repo.
3. Pass `--canonical-root` when nested repos are outside the current Codex worktree.
4. Use `--fetch` when an up-to-date remote-tracking view matters and network access is allowed.
5. Read the generated Markdown and JSON reports before deciding to commit, push, or open a PR.

Recommended patterns:

- root repo only:
  - `python3 skills/gitwiz-github-manager/scripts/gitwiz_sync_audit.py --repo root`
- all repos with canonical workspace access:
  - `python3 skills/gitwiz-github-manager/scripts/gitwiz_sync_audit.py --repo all --canonical-root "<canonical-workspace-root>"`

Treat this as the first step before any "make GitHub match local" workflow.

### 2C. PR Packet Drafting

When a local branch should become a reviewable GitHub update:

1. Make sure the branch exists and is committed.
2. Push the branch if remote review is intended.
3. Run `gitwiz_pr_packet.py` against the correct base ref.
4. If `gh` is available, use the generated packet as the PR title/body input.
5. If `gh` is unavailable, return the packet path and summarize the proposed PR in the response.

Recommended pattern:

- `python3 skills/gitwiz-github-manager/scripts/gitwiz_pr_packet.py --repo-name root --base origin/main`

### 3. SSH-First GitHub Setup

If HTTPS auth is missing or fragile:

1. Check whether an existing SSH key is already configured for GitHub access (inspect the user's SSH directory).
2. If needed, generate a dedicated key.
3. Prefer a dedicated host alias in the SSH client config file instead of changing all `github.com` traffic.
4. Test with `ssh -T <alias>`.
5. Switch the repo remote to the SSH URL that uses that alias.

Do not assume GitHub CLI is installed.

### 4. Safe Remote Replacement

When local history is the real project history and `origin/main` is a bootstrap repo:

1. Inspect the remote commit and branch list.
2. Create a backup branch from the current remote `main`.
3. Force-push only with an explicit lease tied to the commit you inspected.

Preferred shape:

- backup branch:
  - `backup/prepopulate-main-YYYY-MM-DD`
- push pattern:
  - `git push --force-with-lease=refs/heads/main:<expected_sha> origin refs/heads/main:refs/heads/main`

Never use plain `--force` when `--force-with-lease` can do the job.

### 5. Nested Repo Remote Workflow

For named nested repos:

1. Read `catalog/repo_registry.yaml`.
2. Confirm the target path exists in the chosen execution location.
3. Inspect:
   - `git remote -v`
   - `git branch -vv`
   - `git status --short`
   - `git rev-parse HEAD`
4. If no remote exists:
   - create or obtain the GitHub repo URL
   - configure SSH if needed
   - add `origin`
5. If the remote already contains bootstrap history:
   - back up the remote branch before replacement
6. Publish only the named repo and named branch.
7. Report the remote URL, pushed branches, and whether the repo now tracks `origin/<branch>`.

Never publish a nested repo and the root repo in one implicit operation.

### 6. Dirty Worktree Rule

If the repo is dirty and the user wants to publish `main`:

- do not check out `main` just to push it
- push `refs/heads/main:refs/heads/main` directly
- set upstream after the push

### 7. Commit and Hook Rule

If a commit is required:

- inspect staged content first
- keep the commit set coherent
- use normal hooks by default

If hooks fail because the Codex worktree does not contain canonical nested repo paths referenced by workspace validation:

- explain the failure clearly
- confirm it is an environment/path issue rather than a content issue
- use `--no-verify` only when the user still wants the commit and the hook is not providing valid signal in that worktree

### 8. Final Verification

After remote changes, report:

- final `git remote -v`
- upstream tracking state
- pushed branch names and commit IDs
- whether `main` and the current feature branch are both backed up remotely
- any preserved backup branches
- whether any named nested repo remotes were changed
- paths to any generated sync-audit or PR-packet artifacts

### 9. Remote Naming and Defaults

Defaults:

- primary remote name:
  - `origin`
- preferred transport:
  - SSH
- default visibility for new GitHub repos:
  - `private`

Use other remote names only if the repo already has an established pattern or the user asks for it.

## Safety Rules

- Never reset, clean, or discard local changes without explicit approval.
- Never overwrite an existing remote silently.
- Never push nested repos by implication.
- Never force-push until the previous remote state is backed up or the user explicitly declines backup.
- Never treat GitHub bootstrap commits, Copilot setup branches, or generated repository boilerplate as the same thing as the project's real history.
- Never create public GitHub repos by default for this project.
- Never let a root-repo task silently mutate nested repo remotes.

## Good Outcomes

- Root repo published without disturbing nested repos
- Named nested repos can be published independently with clear repo selection
- SSH auth works without global side effects
- Bootstrap GitHub history preserved under a backup branch
- Feature branches published separately from `main`
- New GitHub repos can be created and attached without improvising the process
- Remote state is easy to explain and recover

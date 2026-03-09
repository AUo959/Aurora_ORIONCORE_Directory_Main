---
name: gitwiz-github-manager
description: Manage Git and GitHub operations for the Aurora / ORIONCORE workspace with project-specific safety rules. Use when users ask to configure remotes, publish branches, back up or replace bootstrap GitHub history, push root or nested repos, diagnose auth/SSH issues, or perform repo-aware GitHub setup across the root control-plane repo and named nested repos. Do not use for general code changes, CI failure debugging, or PR comment handling unless the task is primarily about repo publishing and remote state.
---

# GITWIZ GitHub Manager

Project-specific Git/GitHub workflow for Aurora / ORIONCORE.

## Use When

Trigger on requests such as:

- "set up the remote"
- "sync this repo to GitHub"
- "publish this branch"
- "make this repo native to GitHub"
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

## Important Local Truths

- `.gitwiz` in the workspace manifest is an ignored local artifact slot, not the source of truth for this skill.
- This skill should live in versioned repo content and may also be copied into `~/.codex/skills/` for local availability.
- Prefer SSH remotes for ongoing use.
- Prefer preserving remote history by branching it before replacing it.

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

### 2. Distinguish the Operation

Choose the right lane:

- Remote setup:
  - add or update `origin`
  - prefer SSH
- Publish branch:
  - push current branch with `-u`
- Publish local `main` without checkout:
  - use direct ref push when the worktree is dirty
- Replace bootstrap remote history:
  - back up current remote branch first
  - then use `--force-with-lease`
- Nested repo publishing:
  - only after explicit user instruction naming the nested repo

### 3. SSH-First GitHub Setup

If HTTPS auth is missing or fragile:

1. Check for an existing SSH key in `~/.ssh/`.
2. If needed, generate a dedicated key.
3. Prefer a dedicated host alias in `~/.ssh/config` instead of changing all `github.com` traffic.
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

### 5. Dirty Worktree Rule

If the repo is dirty and the user wants to publish `main`:

- do not check out `main` just to push it
- push `refs/heads/main:refs/heads/main` directly
- set upstream after the push

### 6. Commit and Hook Rule

If a commit is required:

- inspect staged content first
- keep the commit set coherent
- use normal hooks by default

If hooks fail because the Codex worktree does not contain canonical nested repo paths referenced by workspace validation:

- explain the failure clearly
- confirm it is an environment/path issue rather than a content issue
- use `--no-verify` only when the user still wants the commit and the hook is not providing valid signal in that worktree

### 7. Final Verification

After remote changes, report:

- final `git remote -v`
- upstream tracking state
- pushed branch names and commit IDs
- whether `main` and the current feature branch are both backed up remotely
- any preserved backup branches

## Safety Rules

- Never reset, clean, or discard local changes without explicit approval.
- Never overwrite an existing remote silently.
- Never push nested repos by implication.
- Never force-push until the previous remote state is backed up or the user explicitly declines backup.
- Never treat GitHub bootstrap commits, Copilot setup branches, or generated repository boilerplate as the same thing as the project's real history.

## Good Outcomes

- Root repo published without disturbing nested repos
- SSH auth works without global side effects
- Bootstrap GitHub history preserved under a backup branch
- Feature branches published separately from `main`
- Remote state is easy to explain and recover

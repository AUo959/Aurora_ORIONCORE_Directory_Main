# Aurora / ORIONCORE Agent Reference

This file is the fast operational reference for agents working in the root
workspace repo.

## Scope

This repo is the root control-plane repo for the workspace. It is not the same
thing as the nested implementation repos.

Named repos:

- `root`
  - this repo
- `aurora-cloudbank-symbolic-main`
  - `Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`
- `CanonRec`
  - `GUMAS_SIM_2.5/CanonRec`
- `DuelSim_v2.0`
  - `GUMAS_SIM_2.5/DuelSim/DuelSim_v2.0`

Never assume a root-repo request applies to nested repos.

## Current GitHub State

Root repo:

- GitHub remote is configured
- preferred transport is SSH
- `main` is published
- the active feature branch may also be published separately
- bootstrap remote history was preserved under a backup branch before replacement

Nested repos:

- treat them as separate repos with separate remotes and publish decisions
- do not add or change their remotes unless the user names the target repo

## What Persists Across Threads

These things persist on this machine:

- repo state on disk
- Git remotes on disk
- SSH keys and SSH config in `~/.ssh/`
- committed project files
- locally installed Codex skills in `~/.codex/skills/`

These things do not persist automatically:

- conversational memory
- intent from prior threads unless it is written into repo files or local skill files

Implication:

- future threads can inspect and use the configured Git/SSH state
- future threads should still read this file, repo state, and relevant skills instead of assuming prior context

## What Syncs to GitHub

Only tracked, committed, and pushed content in the target repo syncs.

Root repo:

- tracked files: yes, after commit and push
- uncommitted edits: no
- ignored files: no
- local-only machine files: no

Nested repos:

- not synced by publishing the root repo
- each nested repo needs its own remote and push flow

Local Codex state:

- `~/.codex/skills/...` is local machine state and is not synced by Git
- the versioned source of a project skill should live in this repo when it matters

## GITWIZ

Project-owned skill:

- `skills/gitwiz-github-manager/`

Purpose:

- GitHub remote setup
- SSH-first auth flow
- local-vs-remote sync audits
- PR packet drafting for sync work
- safe branch publication
- backup-before-force replacement of bootstrap remote history
- named nested repo publishing
- native GitHub repo creation flow when no remote exists

Important distinction:

- `.gitwiz` in the workspace manifest is an ignored local artifact slot
- it is not the source of truth for the skill
- the versioned skill source is `skills/gitwiz-github-manager/`
- the dedicated root agent contract is `GITWIZ.md`

Primary commands:

- root sync audit:
  - `python3 skills/gitwiz-github-manager/scripts/gitwiz_sync_audit.py --repo root`
- all-repo sync audit:
  - `python3 skills/gitwiz-github-manager/scripts/gitwiz_sync_audit.py --repo all --canonical-root "<canonical-workspace-root>"`
- PR packet draft:
  - `python3 skills/gitwiz-github-manager/scripts/gitwiz_pr_packet.py --repo-name root --base origin/main`

## Execution Rules

For root repo work:

- use the current repo/worktree
- treat the root as the default intake inbox for newly saved work unless repo
  evidence shows the item is a root control-plane file that should remain in
  place
- when the user drops new files at root and asks to sort or organize them,
  treat that as a first-order service of this repo: classify, rename,
  standardize, route, and leave updated manifests and receipts
- default loose root items to `intake/` unless there is concrete evidence they
  belong in `docs/`, `reports/`, `_staging/`, or a deferred bucket
- do not silently promote root intake material into canon; canonical promotion
  remains a separate explicit step
- if a root item actually belongs in a nested repo, confirm the target repo
  boundary before moving it there
- if a root directory is live runtime output or log-bearing, prefer tagging it
  as deferred over racing a move while it is changing

For nested repo work:

- use the canonical workspace path if the nested repo is not present in the current Codex worktree
- read `catalog/repo_registry.yaml` before operating

If a request says only "the repo" and multiple repos are plausible:

- ask one short clarification question

## Commit / Hook Caveat

In Codex worktrees, root pre-commit validation may fail if it expects nested repo
paths that exist only in the canonical workspace path.

Treat that as an environment-path issue first, not an automatic content failure.
Use `--no-verify` only when:

- the failure is clearly due to worktree path mismatch
- the user still wants the commit

## Operational Defaults

- prefer SSH over HTTPS for GitHub remotes
- prefer `origin` as the primary remote name
- prefer private GitHub repos unless the user explicitly says otherwise
- back up remote bootstrap history before replacing it
- never push nested repos by implication
- never assume "everything is synced" just because the root repo has a remote

## Practical Continuity Rule

If a fact should survive thread changes, write it into one of:

- `AGENTS.md`
- `README.md`
- versioned skills under `skills/`
- machine-readable repo metadata under `catalog/`

Do not rely on conversational carry-over.

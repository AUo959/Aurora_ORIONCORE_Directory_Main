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
- `qgia-knowledge-library-main`
  - `qgia-knowledge-library-main`
- `qgia-knowledge-spine-main`
  - `qgia-knowledge-spine-main`

Never assume a root-repo request applies to nested repos.

## Historical Provenance

The root control-plane repo began as a local file archive on the owner's
machine. Before the root control plane and GitHub workflows were connected,
Aurora CloudBank existed separately on GitHub, and the local archive was not
fully connected to that repo history.

Implication:

- early local work may be valuable even when it is absent from GitHub
- root archive, intake, staging, or recovered material is not canonical by
  default
- one control-plane mission is to recover and index early local work so
  high-value logic, code, contracts, and design decisions can be identified and
  extracted through explicit promotion paths

See `docs/CONTROL_PLANE_PROVENANCE.md` for the durable provenance and recovery
rule.

## Recovery Indexing

Root recovery tooling:

- Config: `catalog/recovery_index_manifest.json`
- Workflow: `docs/RECOVERY_INDEX_WORKFLOW_v1.md`
- Current report: `reports/analysis/workspace_recovery_index_latest.json`

Primary commands:

- `python3 tools/workspace_recovery_index.py`
- `python3 tools/workspace_recovery_index.py --persist-report`
- `make recovery-index`
- `make recovery-report`

The recovery index is read-only. Its candidates are routing evidence for early
local work and remain `pending_review` / `not_promoted` until a separate
promotion gate validates and extracts them into the correct owner surface.

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

Primary commands:

- root sync audit:
  - `python3 skills/gitwiz-github-manager/scripts/gitwiz_sync_audit.py --repo root`
- all-repo sync audit:
  - `python3 skills/gitwiz-github-manager/scripts/gitwiz_sync_audit.py --repo all --canonical-root "<canonical-workspace-root>"`
- PR packet draft:
  - `python3 skills/gitwiz-github-manager/scripts/gitwiz_pr_packet.py --repo-name root --base origin/main`

## Aurora Dev Toolkit

Root-control-plane toolkit:

- Source manifest: `catalog/dev_toolkit_manifest.json`
- Workflow: `docs/AURORA_DEV_TOOLKIT_WORKFLOW_v1.md`
- Current report: `reports/analysis/aurora_devkit_latest.json`
- Current install plan: `reports/analysis/aurora_devkit_install_plan_latest.json`

Primary commands:

- `python3 tools/aurora_devkit.py`
- `python3 tools/aurora_devkit.py --persist-report`
- `python3 tools/aurora_devkit.py --install-plan --persist-install-plan`
- `make devkit-check`
- `make devkit-report`
- `make devkit-install-plan`

Machine-local automations:

- `aurora-dev-toolkit-watch`: read-only weekly drift report
- `aurora-dev-toolkit-user-space-update`: updates only approved user-space tools

System-level gates remain explicit approval work: Homebrew, Docker, full Xcode,
Rust, and Go.

## Aurora Command Grammar

Repo-local Codex plugin:

- `plugins/aurora-command-grammar/`

Purpose:

- user-accessible parsing, normalization, validation, and mesh-route mapping
- shared agent protocol for command-language ambiguity
- background command intent envelopes for GitHub issues, PRs, receipts,
  automations, and agent handoffs

Core rule:

- grammar-valid command text is not execution approval
- CloudBank remains the parser/runtime authority for command grammar code
- execution requires explicit target repo and live runtime verification

Primary references:

- `plugins/aurora-command-grammar/skills/aurora-command-grammar/SKILL.md`
- `plugins/aurora-command-grammar/skills/aurora-command-grammar/references/background-communication.md`
- `plugins/aurora-command-grammar/skills/aurora-command-grammar/references/command-intent-envelope.schema.json`

## Execution Rules

For root repo work:

- use the current repo/worktree

For nested repo work:

- use the canonical workspace path if the nested repo is not present in the current Codex worktree
- read `catalog/repo_registry.yaml` before operating

If a request says only "the repo" and multiple repos are plausible:

- ask one short clarification question

## Privacy and Scope Defaults

- default to Aurora / ORIONCORE repo- and path-scoped work only
- prefer exact repo or path targeting over broad filesystem scans
- do not inspect, summarize, classify, or route non-Aurora material unless the user explicitly asks
- avoid desktop-wide probes such as Finder Recents, recent-app enumeration, or unrelated browser tabs when Computer Use is not required for the scoped Aurora task
- do not upload, share, or transmit workspace material to third-party services unless the user explicitly directs and confirms the destination
- root workspace scans should auto-exclude likely private personal material in real time using bounded path plus text/document probes instead of relying only on pre-listed paths
- root workspace scans should default-deny unknown top-level material that lacks Aurora / approved-project scope signals, even when it is not obviously private
- use `scan_policy: include` or `scan_policy: omit` in `catalog/classification_overrides.yaml` only as an escape hatch for false positives or persistent known exclusions

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

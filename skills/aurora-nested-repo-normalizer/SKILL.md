---
name: aurora-nested-repo-normalizer
description: Normalize extracted Aurora repo mirrors into real nested Git repositories with verified remote history, clean repo boundaries, and optional root control-plane refresh, or bootstrap a missing target path directly from the remote when no local mirror exists yet. Use when a repo arrived via ZIP/extraction/copy instead of `git clone`, when a plain folder inside the Aurora workspace should become a true nested repo, or when Codex needs to materialize a missing Aurora nested repo at a known path before follow-up work. Do not use for ordinary publishing, PR work, or generic GitHub sync; hand those off to `gitwiz-github-manager` after normalization.
---

# Aurora Nested Repo Normalizer

Turn a plain directory mirror into a real nested repo without inventing Git history.

## Workflow

### 1. Resolve the target

- Treat this as root control-plane work until the target becomes a verified nested repo.
- Read `AGENTS.md`, `README.md`, `catalog/workspace_manifest.yaml`, and `catalog/repo_registry.yaml` first.
- Require the exact target path and remote URL.
- If the target sits under the Aurora workspace root, decide whether to refresh the root control plane after normalization.

### 2. Inspect before mutating

- Check whether the target already has a `.git` boundary.
- If the target path is missing entirely, decide whether to bootstrap it directly from the remote with `--clone-if-missing`.
- If it already is a repo, inspect `git remote -v`, `git status --short --branch`, and `git rev-parse HEAD` before changing anything.
- Prefer a dry run first:

```bash
python3 skills/aurora-nested-repo-normalizer/scripts/normalize_nested_repo.py \
  --target "/absolute/path/to/extracted-repo" \
  --remote "git@github-aurora:OWNER/REPO.git" \
  --workspace-root "/absolute/path/to/Aurora_ORIONCORE_Directory_Main" \
  --dry-run
```

### 3. Normalize only when the trees match

- Run the script without `--dry-run` once the comparison looks correct.
- The script clones the remote to a temporary checkout, compares the working trees excluding `.git` and common local junk, and only then attaches the remote `.git` metadata.
- If the target path is missing and `--clone-if-missing` is set, the script clones the remote directly into that path and then performs the same optional root follow-up.
- If the tree comparison fails, stop. Treat that as salvage/integration work, not simple normalization.

Recommended command:

```bash
python3 skills/aurora-nested-repo-normalizer/scripts/normalize_nested_repo.py \
  --target "/absolute/path/to/extracted-repo" \
  --remote "git@github-aurora:OWNER/REPO.git" \
  --workspace-root "/absolute/path/to/Aurora_ORIONCORE_Directory_Main" \
  --refresh-root-control-plane
```

Bootstrap a missing target path:

```bash
python3 skills/aurora-nested-repo-normalizer/scripts/normalize_nested_repo.py \
  --target "/absolute/path/to/missing-repo-dir" \
  --remote "git@github-aurora:OWNER/REPO.git" \
  --workspace-root "/absolute/path/to/Aurora_ORIONCORE_Directory_Main" \
  --clone-if-missing \
  --refresh-root-control-plane
```

### 4. Validate the result

- Confirm the target is now a real repo with:
  - `git rev-parse --show-toplevel`
  - `git remote -v`
  - `git status --short --branch`
  - `git log --oneline -5`
- If `--refresh-root-control-plane` was used, confirm the workspace follow-up finished and `tools/workspace_verify.py` passed.
- Read the JSON receipt the script writes when `--workspace-root` is supplied.

### 5. Hand off correctly

- Use `gitwiz-github-manager` after normalization for remote changes, branch publication, sync audits, or PR creation.
- Do not treat this skill as a publishing surface.

## Bundled Script

Use `scripts/normalize_nested_repo.py` instead of reconstructing the workflow manually. It supports:

- `--dry-run` to verify the remote and compare trees without mutating the target
- `--workspace-root` to derive a durable receipt path under `reports/analysis/nested-repo-normalizer/`
- `--clone-if-missing` to clone directly into a missing target path instead of failing
- `--refresh-root-control-plane` to run:
  - `python3 tools/workspace_scan.py`
  - `python3 tools/workspace_plan_moves.py`
  - `python3 tools/workspace_verify.py`
  - `python3 tools/workspace_verify.py --persist-report`
- idempotent handling for already-normalized repos when the existing `origin` matches the requested remote

## Local Install / Update

The versioned source of truth for this skill lives in the repo. Refresh the installed local copy with:

```bash
python3 tools/sync_codex_skill.py --skill aurora-nested-repo-normalizer --validate-package
```

## Failure Rules

- Do not overwrite an existing `.git` directory just to force the workflow through.
- Do not normalize if the extracted tree differs from the remote snapshot.
- Do not use `--clone-if-missing` when the user actually expects a local extracted mirror to be verified first.
- Do not hand-edit generated root control surfaces; rely on the root follow-up commands when the target lives under Aurora.
- Do not publish nested repos by implication.

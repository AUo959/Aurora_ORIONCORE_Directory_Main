# Aurora Dependency Update Automation Receipt - 2026-05-25

## Scope

Root control-plane dependency automation plus the registered CloudBank Python
environment bridge.

Root and CloudBank remain separate Git boundaries:

- Root: `Aurora_ORIONCORE_Directory_Main`
- CloudBank: `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`

## Problem

The devkit could verify the registered CloudBank `.venv`, but dependency update
automation was not complete across the surfaces that feed that environment:

- Root had no Dependabot configuration for GitHub Actions, pre-commit hooks, or
  devcontainer features.
- CloudBank Dependabot covered only top-level Python and npm manifests.
- The weekly local user-space update automation did not refresh the registered
  CloudBank `.venv` from the repo's canonical requirements files.
- The devkit report did not verify dependency-update coverage, so missing
  update lanes could drift silently.

## Changes

- Added root `.github/dependabot.yml`.
- Expanded CloudBank `.github/dependabot.yml` coverage.
- Added `dependency_update_surfaces` to
  `catalog/dev_toolkit_manifest.json`.
- Added the CloudBank registered `.venv` update command and post-update checks
  to `catalog/dev_toolkit_manifest.json`.
- Updated `tools/aurora_devkit.py` so the generated report verifies
  Dependabot coverage for root and CloudBank.
- Added focused regression coverage in `tests/test_aurora_devkit.py`.
- Updated `docs/AURORA_DEV_TOOLKIT_WORKFLOW_v1.md` with the automatic
  dependency update lanes.
- Updated the active `aurora-dev-toolkit-user-space-update` automation so its
  weekly run refreshes approved user-space tools and the registered CloudBank
  `.venv` from `requirements.txt` plus `requirements-dev.txt`.
- Updated the active `aurora-dev-toolkit-watch` automation so it reports
  dependency update surface gaps and registered `.venv` drift.

## Automatic Update Lanes

GitHub Dependabot:

- Root: `github-actions`, `pre-commit`, `devcontainers`
- CloudBank: `github-actions`, `pre-commit`, `pip`, and `npm` across active
  runtime, frontend, CLI, SDK, and service manifests

Local weekly automation:

- `uv tool upgrade pre-commit`
- `uv tool upgrade ruff`
- `uv tool upgrade mypy`
- `uv tool upgrade pipx`
- `corepack prepare pnpm@latest --activate`
- `corepack enable pnpm`
- CloudBank `.venv/bin/python -m pip install --upgrade -r requirements.txt -r requirements-dev.txt`
- CloudBank `.venv/bin/python -m pip check`
- CloudBank `.venv/bin/python -m pytest -q tests/test_security_middleware.py`

## Guardrails

- Dependabot opens pull requests; it does not auto-merge them.
- Optional CloudBank dependencies are not installed automatically.
- Nested repo package manifests are not mutated by the local weekly automation.
- Homebrew, Docker, Xcode, Rust, Go, nested repo remotes, and system-level
  packages remain explicit approval work.
- Archived dependency manifests and dependency caches are excluded.

## Validation

- `python3 -m pytest tests/test_aurora_devkit.py -q` -> 6 passed.
- Root `.github/dependabot.yml` parsed with PyYAML.
- CloudBank `.github/dependabot.yml` parsed with PyYAML.
- `python3 tools/aurora_devkit.py --persist-report` -> `READY`.
- `reports/analysis/aurora_devkit_latest.json` reports 2 dependency update
  surfaces, both `ok`.
- `python3 tools/aurora_devkit.py --install-plan --persist-install-plan` ->
  no missing or broken tools.
- `python3 tools/workspace_verify.py --persist-report` -> pass with 0 findings.
- CloudBank `.venv/bin/python -m pip check` -> no broken requirements found.
- CloudBank `.venv/bin/python -m pytest -q tests/test_security_middleware.py`
  -> 19 passed.
- Root `git diff --check` -> clean.
- CloudBank `git diff --check` -> clean.

## Remaining Operator Gate

Dependency PRs should still be reviewed and merged through normal validation.
The automated lane keeps updates visible and low-friction, but it deliberately
does not convert third-party dependency changes into unreviewed canon.

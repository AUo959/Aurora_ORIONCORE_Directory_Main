# Aurora Dev Toolkit Workflow v1

## Purpose

The Aurora Dev Toolkit is the repeatable development lane for this machine and
workspace. It is root-control-plane tooling: it inventories the machine,
project package surfaces, Codex skills, and automations, then produces a
machine-readable report before any package-mutating work is approved.

The toolkit does not promote nested repo content, generated reports, intake, or
staged material into canon. Nested repos remain separate Git boundaries governed
through `catalog/repo_registry.yaml`.

## Current Evidence

Initial scan date: 2026-05-16.

Current validation date: 2026-05-21.

Confirmed available:

- macOS 26.5 on arm64.
- `git` 2.50.1, `gh` 2.88.0, OpenSSH 10.2p1.
- `python3` 3.9.6 with root verifier-compatible packages already present.
- `uv` 0.10.9 at `/Users/travisstreets/.local/bin/uv`.
- `node` 24.14.0 and `npm` 11.9.0 through nvm.
- `corepack` is present through the active Node install.
- `pnpm` 11.1.2 is enabled through Corepack.
- User-space Python CLIs installed through `uv tool`: `pre-commit` 4.6.0,
  `ruff` 0.15.13, `mypy` 2.1.0, and `pipx` 1.12.0.
- `sqlite3` is present.
- Homebrew 5.1.13 is present at `/opt/homebrew/bin/brew`.
- Docker Desktop is present; the CLI reports Docker 29.4.3 and Compose v5.1.4.
- Full Xcode is installed, selected, and reports Xcode 26.5 build 17F42.
- Rust is present through the user-space `rustup` lane as `rustc` 1.95.0.
- Go is present through the user-space install lane as `go1.26.3`.
- Root control surfaces already include `Makefile`, `.devcontainer`,
  `.pre-commit-config.yaml`, GitHub CI, GitWIZ helpers, and
  `tools/sync_codex_skill.py`.
- Installed Aurora skill package currently has 26 skills by the latest devkit
  report.

Current devkit verdict:

- `reports/analysis/aurora_devkit_latest.json` reports `READY`.
- All 19 declared tools are `ok`.
- The install plan is empty.
- Findings are empty.
- Package manifests exist in multiple zones, including root, projects,
  CloudBank, and DuelSim. Installed dependency trees must be pruned from scans
  because CloudBank currently contains local `node_modules` and `.venv`.

## Toolkit Files

- `catalog/dev_toolkit_manifest.json`: source manifest for required and
  recommended tools, package-manifest discovery, update policy, and validation
  commands.
- `tools/aurora_devkit.py`: local doctor/report command.
- `reports/analysis/aurora_devkit_latest.json`: generated report when
  `--persist-report` is used.
- `tests/test_aurora_devkit.py`: focused regression coverage for manifest
  discovery, automation parsing, and finding generation.

## Standard Commands

```bash
python3 tools/aurora_devkit.py
python3 tools/aurora_devkit.py --persist-report
python3 tools/aurora_devkit.py --install-plan
python3 tools/aurora_devkit.py --install-plan --persist-install-plan
python3 tools/aurora_devkit.py --json
python3 -m pytest tests/test_aurora_devkit.py -q
python3 tools/workspace_verify.py
```

Makefile aliases:

```bash
make devkit-check
make devkit-report
make devkit-install-plan
```

## Workflow

1. Run `python3 tools/aurora_devkit.py --persist-report`.
2. Review required-tool blockers first.
3. Review recommended-tool warnings by development lane:
   Python, JavaScript/frontend, Mac app/iOS, containers, systems tooling.
4. Produce a concrete apply set only after the report shows exactly what is
   missing or stale. Use `python3 tools/aurora_devkit.py --install-plan` for
   the machine-readable command plan.
5. Install or update packages through the approved manager for that lane.
6. Rerun the devkit report, focused tests, and `tools/workspace_verify.py`.
7. Leave a receipt in `reports/analysis/` when the machine/toolkit state
   changes.

## Package Policy

Default install mode is approval-gated. Default update mode is read-only drift
detection followed by an explicit apply step.

Python:

- Prefer `uv` for project-local virtual environments and reproducible installs.
- Use `pipx` for global Python CLI tools once installed.
- Recommended baseline: `pytest`, `pyyaml`, `jsonschema`, `pre-commit`,
  `ruff`, and `mypy`.
- Current user-space install lane: `uv tool install pre-commit`,
  `uv tool install ruff`, `uv tool install mypy`, and
  `uv tool install pipx`. These were applied on 2026-05-16.

JavaScript:

- Keep existing `package-lock.json` projects on npm unless intentionally
  migrated.
- Use `corepack` to activate pinned pnpm or yarn for new multi-package
  workspaces.
- Recommended baseline for advanced apps: TypeScript, Vite, tsx, ESLint,
  Prettier, and Playwright.
- Current user-space install lane: `corepack prepare pnpm@latest --activate`,
  then `corepack enable pnpm`. This was applied on 2026-05-16.

macOS/system:

- Homebrew is installed and is the practical package manager for approved Mac
  system tool updates.
- Docker Desktop is installed; service-stack and devcontainer work can start
  from a verified Docker baseline.
- Full Xcode is installed and selected, so iOS/macOS build automation can be
  evaluated against real Xcode behavior instead of Command Line Tools only.
- Rust and Go are currently satisfied through user-space installs. Fresh-machine
  installs or upgrades still require explicit approval and should follow the
  current install plan rather than assumptions from older receipts.

## Update Automation

The safe default is a weekly read-only devkit watch automation that runs the
doctor, reports missing or stale tools, and proposes exact update commands. A
package-mutating automation should only be enabled after the package manager
and approved package set are confirmed.

Active toolkit automation:

- `aurora-dev-toolkit-watch`: active, Sunday 09:00, read-only drift report.
- `aurora-dev-toolkit-user-space-update`: active, Sunday 09:15, updates only
  approved user-space tools (`uv tool` CLIs and Corepack `pnpm`).

Existing related automations:

- `weekly-skill-audit`: active, validates installed Aurora skills.
- `aurora-root-workspace-health`: active, validates root control-plane health.
- `aurora-multi-repo-git-health`: active, validates registered repo state.
- `qgia-closed-loop-validation`: active, validates QGIA boundaries.
- `aurora-package-watch`: present but paused.

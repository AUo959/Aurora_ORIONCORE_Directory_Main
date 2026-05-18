# Aurora Dev Toolkit Apply Receipt - 2026-05-16

## Scope

Applied the ready user-space install lane from the Aurora Dev Toolkit install
plan. No nested repo source, remotes, or package manifests were edited.

## Installed

Python CLI tools installed through `uv tool`:

- `pre-commit` 4.6.0
- `ruff` 0.15.13
- `mypy` 2.1.0
- `pipx` 1.12.0

JavaScript package manager shim:

- `pnpm` 11.1.2 enabled through Corepack

## Automatic Updates

Created machine-local Codex automation:

- `aurora-dev-toolkit-user-space-update`
- Status: `ACTIVE`
- Cadence: weekly Sunday 09:15
- Scope: update only approved user-space tools installed in this pass

The updater is intentionally bounded to:

- `uv tool upgrade pre-commit`
- `uv tool upgrade ruff`
- `uv tool upgrade mypy`
- `uv tool upgrade pipx`
- `corepack prepare pnpm@latest --activate`
- `corepack enable pnpm`

It does not mutate Homebrew, Docker, Xcode, Rust, Go, nested repo remotes, or
nested repo package manifests.

## Commands Applied

```bash
uv tool install pre-commit
uv tool install ruff
uv tool install mypy
uv tool install pipx
corepack prepare pnpm@latest --activate
corepack enable pnpm
```

## Current Devkit Status

`python3 tools/aurora_devkit.py --persist-report` now reports:

- Status: `WARN`
- Tools: 14/19 ok
- Remaining warnings: `docker`, `brew`, `xcodebuild`, `rust`, and `go`

The remaining warnings are system-level or Apple-platform lanes:

- Homebrew install or equivalent package manager decision
- Docker Desktop install
- Full Xcode install/selection
- Rust install after package-manager decision
- Go install after package-manager decision

## Generated Surface Refresh

The final root verifier pass observed live nested-repo branch drift in
`GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`.
The root generated surfaces were refreshed with:

```bash
python3 tools/workspace_scan.py
python3 tools/workspace_plan_moves.py
```

The refreshed registry records CloudBank on
`codex/fix-slowapi-stub-isolation-713` at
`cf25bcc3d3201219f3a9b2cb836c93672a307c50`.

## Validation

```bash
pre-commit --version
ruff --version
mypy --version
pipx --version
pnpm --version
uv tool list
python3 tools/aurora_devkit.py --persist-report
python3 tools/aurora_devkit.py --install-plan --persist-install-plan
python3 -m pytest tests/test_aurora_devkit.py -q
python3 -m pytest tests -q
python3 tools/workspace_verify.py --persist-report
```

Results:

- `pre-commit` visible at `/Users/travisstreets/.local/bin/pre-commit`
- `ruff` visible at `/Users/travisstreets/.local/bin/ruff`
- `mypy` visible at `/Users/travisstreets/.local/bin/mypy`
- `pipx` visible at `/Users/travisstreets/.local/bin/pipx`
- `pnpm` visible at `/Users/travisstreets/.nvm/versions/node/v24.14.0/bin/pnpm`
- Install plan reduced from 10 items to 5 remaining system-level items.
- Focused devkit tests: 4 passed.
- Full root tests: 94 passed, 23 skipped.
- Workspace verifier: pass, 0 findings.

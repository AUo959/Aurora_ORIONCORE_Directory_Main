# Aurora Dev Toolkit Behavior Test - 2026-05-16

## Scope

Ran a live behavior test of the Aurora Dev Toolkit after finalization. This test
validated the public entrypoints, install-plan behavior, installed tool
visibility, bounded user-space update behavior, focused tests, full root tests,
and root workspace verification.

No nested repo source, nested remotes, or nested package manifests were edited.

## Entrypoint Behavior

Commands:

```bash
make devkit-check
make devkit-install-plan
python3 tools/aurora_devkit.py --json --report-out /private/tmp/aurora_devkit_behavior_report.json
```

Observed behavior:

- `make devkit-check` reported `WARN`, not `BLOCKED`.
- Tools: 14/19 ok.
- Package manifests discovered: 38.
- Registered repos: 5.
- Installed Codex skills: 26.
- Automations discovered: 13.
- Install plan items: 5.

The remaining findings were the expected system-level gates:

- `docker`
- `brew`
- `xcodebuild`
- `rust`
- `go`

## Installed Tool Visibility

Commands:

```bash
pre-commit --version
ruff --version
mypy --version
pipx --version
pnpm --version
```

Observed versions:

- `pre-commit` 4.6.0
- `ruff` 0.15.13
- `mypy` 2.1.0
- `pipx` 1.12.0
- `pnpm` 11.1.2

## User-Space Update Behavior

Commands:

```bash
uv tool upgrade pre-commit
uv tool upgrade ruff
uv tool upgrade mypy
uv tool upgrade pipx
corepack prepare pnpm@latest --activate
corepack enable pnpm
```

Observed behavior:

- All `uv tool upgrade ...` commands completed successfully.
- The Python tools were already current and returned `Nothing to upgrade`.
- Corepack prepared and enabled `pnpm` successfully.
- No system-level packages were installed or changed.

## Validation

Commands:

```bash
python3 tools/aurora_devkit.py --persist-report
python3 tools/aurora_devkit.py --install-plan --persist-install-plan
python3 -m pytest tests/test_aurora_devkit.py -q
python3 -m pytest tests -q
python3 tools/workspace_verify.py --persist-report
```

Results:

- Devkit report: `WARN`, expected system-level gaps only.
- Install plan: 5 remaining system-level/manual items.
- Focused devkit tests: 4 passed.
- Full root tests: 94 passed, 23 skipped.
- Workspace verifier: pass, 0 findings.

## Generated Surface Note

During the test run, `workspace_verify.py` initially caught CloudBank nested-repo
head drift. The root generated surfaces were refreshed with:

```bash
python3 tools/workspace_scan.py
python3 tools/workspace_plan_moves.py
```

After regeneration, `python3 tools/workspace_verify.py --persist-report`
passed with 0 findings.

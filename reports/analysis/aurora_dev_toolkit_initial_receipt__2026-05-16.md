# Aurora Dev Toolkit Initial Receipt - 2026-05-16

## Scope

Built the first root-control-plane Aurora Dev Toolkit lane. The work stayed in
the root repo and did not edit nested repo source, remotes, or package
manifests.

## Added

- `catalog/dev_toolkit_manifest.json`: machine-readable source for required and
  recommended tools, package-manifest discovery, package policy, update lanes,
  and validation commands.
- `tools/aurora_devkit.py`: repeatable local doctor/report command.
- `tests/test_aurora_devkit.py`: regression coverage for package-manifest
  pruning, automation parsing, and finding generation.
- `docs/AURORA_DEV_TOOLKIT_WORKFLOW_v1.md`: referable workflow for scan,
  review, approval-gated apply, validation, and receipts.
- `Makefile` targets: `devkit-check` and `devkit-report`.
- `reports/analysis/aurora_devkit_latest.json`: generated current toolkit
  report.
- `reports/analysis/aurora_devkit_install_plan_latest.json`: generated
  approval-gated install plan when persisted.

## Automation

Created machine-local Codex automation:

- `aurora-dev-toolkit-watch`
- Status: `ACTIVE`
- Cadence: weekly Sunday 09:00
- Mode: read-only drift report

The automation is intentionally not package-mutating. It reports required-tool
blockers, recommended-tool gaps, package manager drift, and exact approval-gated
install or update commands.

## Initial Findings

The devkit report currently returns `WARN`, not `BLOCKED`.

Required tools found:

- `git`
- `gh`
- `python3`
- `python3 -m pip`
- `uv`
- `node`
- `npm`
- `corepack`
- `sqlite3`

Recommended gaps:

- `pre-commit`
- `ruff`
- `mypy`
- `pipx`
- `pnpm`
- `docker`
- `brew`
- full `xcodebuild`
- `rustc`
- `go`

## Generated Surface Repair

`python3 tools/workspace_verify.py` initially failed because
`catalog/repo_registry.yaml` still recorded CloudBank on
`codex/fix-cloudbank-604-ethics-verification` at
`eededb5073cfcb66208392a34f3d5e41770aa2a0`, while the actual nested repo was
on `main` at `cf25bcc3d3201219f3a9b2cb836c93672a307c50`.

Used the supported generated-surface flow:

```bash
python3 tools/workspace_scan.py
python3 tools/workspace_plan_moves.py
```

This refreshed the generated registry and related generated surfaces.

## Validation

```bash
python3 tools/aurora_devkit.py --persist-report
python3 tools/aurora_devkit.py --install-plan --persist-install-plan
python3 -m pytest tests/test_aurora_devkit.py -q
python3 -m pytest tests -q
python3 tools/workspace_verify.py
```

Results:

- Devkit doctor: `WARN`, expected due recommended missing tools.
- Focused tests: 3 passed.
- Full root tests: 93 passed, 23 skipped.
- Workspace verifier: pass, 0 findings.

## Follow-Up Apply

The ready user-space apply lane was completed later on 2026-05-16. See
`reports/analysis/aurora_dev_toolkit_apply_receipt__2026-05-16.md`.

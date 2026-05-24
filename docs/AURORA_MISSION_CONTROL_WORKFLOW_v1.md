# Aurora Mission Control Workflow v1

## Purpose

Aurora Mission Control is the root-control-plane operator inbox. It aggregates
existing deterministic root signals into one read-only report:

- workspace verification
- integration gate posture
- recovery-index review pressure
- devkit readiness
- advisory recommendations
- root Git status

It does not promote recovery material, mutate nested repos, execute runtime
commands, send mesh messages, install packages, or publish GitHub changes.

## Files

- `catalog/mission_control_manifest.json`: source list, readiness lanes, report
  destination, and validation commands.
- `catalog/schemas/aurora_mission_control_report.schema.json`: machine-readable
  report shape.
- `tools/aurora_mission_control.py`: read-only report generator.
- `reports/analysis/aurora_mission_control_latest.json`: generated report when
  `--persist-report` is used.
- `tests/test_aurora_mission_control.py`: focused regression coverage.

## Commands

```bash
python3 tools/aurora_mission_control.py --summary
python3 tools/aurora_mission_control.py --persist-report
python3 tools/aurora_mission_control.py --report-out /tmp/aurora_mission_control.json
python3 -m pytest -q tests/test_aurora_mission_control.py
python3 tools/workspace_verify.py
```

Makefile aliases:

```bash
make mission-control
make mission-control-report
```

## Interpretation

Report status values:

- `ready`: no operator inbox items and no blocked or attention readiness lanes.
- `attention`: advisory work exists, but no blocking inbox item or lane is
  present.
- `blocked`: a P0/blocking inbox item exists or a readiness lane is missing a
  required tool.

Build lanes are readiness labels only. They show what the current machine can
support. They are not approval to install packages, mutate repos, execute live
runtime commands, or promote canon.

## Boundary Rules

Root owns the Mission Control manifest, schema, generator, report, tests, and
workflow doc. Nested repos remain separate Git boundaries and are referenced
only through existing reports or `catalog/repo_registry.yaml`.

Recovery recommendations remain routing evidence. A candidate becomes canonical
only through a separate owner-surface decision, validation, and receipt or PR.

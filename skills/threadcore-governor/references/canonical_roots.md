# Canonical Roots Policy

Default authority roots are intentionally focused and deterministic. Roots are
repo-relative and resolved against the `--repo` argument at scan time, so they
survive workspace relocations (iCloud → `~/dev` on 2026-07-01).

1. `GUMAS_SIM_2.5`
2. `projects/Aurora_Project_Cloudhub_Deploy`
3. `projects/GUI_Cloudhub`
4. `Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`

Root 4 is the root-level tree, kept disjoint from `GUMAS_SIM_2.5` so nested
roots are never scanned twice (the file iterator does not dedupe).

## Rationale

- Reduce authority drift from duplicate-heavy archive areas.
- Keep V1 deterministic and aligned with active governance surfaces.
- Allow overrides only through explicit `--roots` input.

## Scan Surface

- JSON artifacts: `.json`
- Beacon text artifacts: `.md`, `.txt`

The scanner does not recurse into archives and does not execute command chains.

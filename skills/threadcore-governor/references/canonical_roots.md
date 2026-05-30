# Canonical Roots Policy

Default authority roots are intentionally focused and deterministic.

1. `/Users/travisstreets/Library/Mobile Documents/3L68KQB4HG~com~readdle~CommonDocuments/Documents/Aurora_ORIONCORE_Directory_Main/GUMAS_SIM_2.5`
2. `/Users/travisstreets/Library/Mobile Documents/3L68KQB4HG~com~readdle~CommonDocuments/Documents/Aurora_ORIONCORE_Directory_Main/Aurora_Project_Cloudhub_Deploy`
3. `/Users/travisstreets/Library/Mobile Documents/3L68KQB4HG~com~readdle~CommonDocuments/Documents/Aurora_ORIONCORE_Directory_Main/GUI_Cloudhub`
4. `/Users/travisstreets/Library/Mobile Documents/3L68KQB4HG~com~readdle~CommonDocuments/Documents/Aurora_ORIONCORE_Directory_Main/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`

## Rationale

- Reduce authority drift from duplicate-heavy archive areas.
- Keep V1 deterministic and aligned with active governance surfaces.
- Allow overrides only through explicit `--roots` input.

## Scan Surface

- JSON artifacts: `.json`
- Beacon text artifacts: `.md`, `.txt`

The scanner does not recurse into archives and does not execute command chains.

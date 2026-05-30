---
name: aurora-quantum-forge-ops
description: Run Quantum Forge engine operations for Aurora by validating GUMAS v3.0 Forge modules, executing deterministic engine turns, generating/verifying ORION capsules, and producing leadership-ready Markdown plus machine-readable JSON run artifacts. Use when users ask to operate or diagnose Quantum Forge runs, produce Forge execution reports, run charforge capsule operations, or correlate QUANTUM_FORGE manifest/vector context with live engine signals. Do not use for governance gating, canon promotion, or continuity reconciliation.
author: Aurora ORIONCORE
---

# Aurora Quantum Forge Ops

Execute deterministic Quantum Forge operations from the GUMAS v3.0 Forge root and emit operational artifacts for leadership and automation.

## Workflow

1. Confirm `--forge-root` points to the active Forge implementation.
2. Run validation first (enabled by default).
3. Execute deterministic engine turns with a fixed seed.
4. Export v3 state snapshot.
5. Optionally generate and verify ORION capsules.
6. Optionally ingest QForge payload context files.
7. Emit Markdown + JSON reports (and optional run manifest).

## Commands

Base run:

```bash
python3 /Users/travisstreets/.codex/skills/aurora-quantum-forge-ops/scripts/build_qforge_ops_report.py \
  --forge-root "/Users/travisstreets/Library/Mobile Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main/GUMAS_SIM_2.5/FORGE__GUMAS_v3.0__2026-02-19"
```

Run with capsule generation and verification:

```bash
python3 /Users/travisstreets/.codex/skills/aurora-quantum-forge-ops/scripts/build_qforge_ops_report.py \
  --forge-root "/Users/travisstreets/Library/Mobile Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main/GUMAS_SIM_2.5/FORGE__GUMAS_v3.0__2026-02-19" \
  --turns 10 \
  --generate-capsules \
  --verify-capsules \
  --emit-run-manifest
```

Run with payload context:

```bash
python3 /Users/travisstreets/.codex/skills/aurora-quantum-forge-ops/scripts/build_qforge_ops_report.py \
  --forge-root "/Users/travisstreets/Library/Mobile Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main/GUMAS_SIM_2.5/FORGE__GUMAS_v3.0__2026-02-19" \
  --qforge-manifest "/path/to/QUANTUM_FORGE_Manifest.json" \
  --vector-injections "/path/to/Symbolic_Vector_Injections.json"
```

## Output Contract

Default output directory: `<forge-root>/workflow_output/quantum_forge_ops`

Outputs:

- `quantum_forge_run_report.md`
- `quantum_forge_run_report.json`
- `v3_state_snapshot.json`
- `capsule_verification.json` (when capsule verification runs)
- `run_manifest.json` (when `--emit-run-manifest`)

Markdown section contract:

- `Execution Snapshot`
- `Validation Status`
- `Engine Signals`
- `Capsule Operations`
- `Payload Context`
- `Risk Flags`
- `Artifact Index`

## Git Automation Policy

- Do not require manual git commands from the user.
- If a workflow needs git status/add/commit as part of integration completion, execute those steps directly.
- Do not push unless explicitly requested.

## Boundaries

- Keep this skill focused on Forge operations and reporting.
- Do not produce governance or canonization verdicts.
- Route governance/canonization requests to existing governance/canon skills.

## References

- `references/forge_api_contract.md`
- `references/qforge_output_schema.md`
- `references/trigger_examples.md`

## Workflow Position

- Upstream: direct Forge operations and diagnostics.
- Downstream: `aurora-narrative-tone-governor` for prose governance and `aurora-exec-brief-pipeline` for leadership summaries.
- Preset reference: `/Users/travisstreets/.codex/skills/aurora-governance-orchestrator/references/workflow_presets.md`.

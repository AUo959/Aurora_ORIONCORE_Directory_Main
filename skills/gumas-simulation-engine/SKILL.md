---
name: gumas-simulation-engine
description: Run, benchmark, and export the integrated GUMAS simulation engine (advanced default with legacy fallback) in Aurora workspaces. Use when users ask to run multi-turn simulations, compare seeds, evaluate stability/risk trends, export JSON state artifacts, or debug simulation behavior in GUMAS_SIM_2.5/SIM_ENGINE_OUTPUTS.
author: Aurora ORIONCORE
---

# GUMAS Simulation Engine

## Quick Start

Run the bundled runner from the target workspace:

```bash
PYTHONPYCACHEPREFIX=/tmp \
python3 /Users/travisstreets/.codex/skills/gumas-simulation-engine/scripts/run_gumas_advanced.py \
  --workspace "$PWD" --turns 20 --seed 42
```

## Workflow

1. Confirm `GUMAS_SIM_2.5/SIM_ENGINE_OUTPUTS` exists in the chosen workspace.
2. Run `scripts/run_gumas_advanced.py` with requested turns and seed.
3. Report the engine class used, last-turn summary, and output artifact path.
4. If asked for comparison, rerun with alternate seeds and compare risk/stability trend deltas.
5. If advanced import fails, use the legacy fallback notes in `references/runtime_notes.md`.

## Output Contract

Return:
- Engine mode and class (`GUMASAdvancedEngine` or fallback)
- Turns requested/completed
- Last-turn summary string (or base tick counts in legacy mode)
- Output JSON path and whether export succeeded

## Resources

- Runner script: `scripts/run_gumas_advanced.py`
- Runtime notes: `references/runtime_notes.md`

## Workflow Position

- Upstream: direct simulation execution and comparison.
- Downstream: `aurora-narrative-tone-governor` when prose artifacts need governance and `aurora-exec-brief-pipeline` when outputs must become leadership-ready.
- Preset reference: `/Users/travisstreets/.codex/skills/aurora-governance-orchestrator/references/workflow_presets.md`.

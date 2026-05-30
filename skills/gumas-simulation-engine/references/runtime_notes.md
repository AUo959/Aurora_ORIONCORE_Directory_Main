# Runtime Notes

## Expected Workspace Paths

- Engine directory:
`<workspace>/GUMAS_SIM_2.5/SIM_ENGINE_OUTPUTS`
- Default skill export:
`<workspace>/GUMAS_SIM_2.5/SIM_ENGINE_OUTPUTS/advanced_skill_output.json`

## Entrypoint Behavior

- `engine.py` now defaults to `GUMASAdvancedEngine`.
- Legacy engine remains importable as `LegacyGUMASEngine`.

## Permission and Cache Notes

- Use `PYTHONPYCACHEPREFIX=/tmp` to avoid pycache writes outside the workspace.
- Skill commands should run in the target workspace root.

## Smoke Command

```bash
PYTHONPYCACHEPREFIX=/tmp \
python3 /Users/travisstreets/.codex/skills/gumas-simulation-engine/scripts/run_gumas_advanced.py \
  --workspace "$PWD" --turns 5 --seed 42
```

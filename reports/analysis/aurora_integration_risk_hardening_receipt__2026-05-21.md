# Aurora Integration Risk Hardening Receipt - 2026-05-21

## Scope

Root control-plane hardening pass following the eight-agent integration
brainstorm. This work addresses the main risks identified by the council:
execution-status ambiguity, audit split-brain, canon/provenance overclaim,
operator path ambiguity, and missing integrated validation.

No nested repo files were edited.

## Changes

- Added `run_mode`, `execution_scope`, `live_runtime_execution`, and
  `simulation_status` to command intent records emitted by
  `tools/aurora_command_intent.py`.
- Changed `simulate-range` reporting so in-process simulation is labeled as
  `execution_scope: in_process_simulation`, `live_runtime_execution: false`,
  and `intent.execution_status: not_applicable`.
- Added `audit-handoff-record.schema.json` as a wrapper for cross-artifact
  handoffs without replacing the command intent envelope.
- Added `tools/aurora_integration_gate.py` and `make integration-gate` for a
  read-only command/agent/provenance/root verification gate.
- Added a provenance gate that checks recovery candidates remain
  `pending_review` / `not_promoted` unless a promotion receipt exists.
- Corrected human-facing CloudBank path references in `README.md` and
  `AGENTS.md` to the canonical registry path:
  `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`.
- Updated GitHub command grammar templates and command grammar docs to surface
  the new safety fields.

## Validation

```bash
python3 -m json.tool plugins/aurora-command-grammar/skills/aurora-command-grammar/references/command-intent-envelope.schema.json
python3 -m json.tool plugins/aurora-command-grammar/skills/aurora-command-grammar/references/audit-handoff-record.schema.json
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider tests/test_aurora_command_intent.py tests/test_aurora_command_grammar_plugin.py tests/test_aurora_integration_gate.py tests/test_agent_dispatcher_skill.py tests/test_sync_codex_skill.py
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider tests
PYTHONDONTWRITEBYTECODE=1 python3 tools/workspace_verify.py
make integration-gate
git diff --check
```

Results:

- schema JSON checks: pass
- focused hardening tests: `46 passed`
- root-scoped tests: `116 passed, 23 skipped`
- workspace verification: pass, `0` findings
- integration gate: pass
- whitespace check: pass

An unscoped `python3 -m pytest -q -p no:cacheprovider` was also attempted and
failed during collection because it traversed nested/staging surfaces with
their own dependencies and import layouts, including missing `fastapi` in the
CloudBank nested repo and staged `modules.*` imports. This is not a root
control-plane regression; use the scoped root test command above for this
change family.

## Remaining Follow-Up

- If command intent envelope compatibility needs strict external enforcement,
  promote the new optional safety fields into a future schema version after
  downstream consumers are checked.
- If live execution is ever added, it should be owned by CloudBank runtime
  adapters and require separate runtime verification plus explicit approval.

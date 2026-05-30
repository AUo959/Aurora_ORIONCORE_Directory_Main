# Aurora Command Grammar PR

## Scope

- Target repo:
- Grammar family: `aurora_symbolic_command` / `mesh_router` / `command_router`
- Change type: docs / skill / schema / parser / catalog / validator / runtime handler

## Authority Checked

- [ ] Root repo boundary and nested repo target are explicit.
- [ ] Existing CloudBank grammar code was checked before changing semantics.
- [ ] Root command/watch ownership was checked when changing control-plane wording.
- [ ] Mesh-router references were checked for `@mesh` behavior, if relevant.

## Command Intent

Attach a command intent envelope or explain why none is needed.

```json
{
  "schema_version": "1.0.0",
  "raw_text": "",
  "normalized_text": null,
  "intent_type": "background_handoff",
  "grammar_family": "unknown",
  "ast_shape": null,
  "command_heads": [],
  "arguments": [],
  "modifier": null,
  "warnings": [],
  "validation_status": "not_validated",
  "validation_issues": [],
  "run_mode": "background_handoff",
  "execution_scope": "none",
  "live_runtime_execution": false,
  "simulation_status": "not_applicable",
  "runtime_handler_verified": false,
  "runtime_refs": [],
  "execution_status": "not_requested",
  "target_repo": null,
  "authority_refs": [],
  "recommended_next_action": "",
  "receipt_refs": []
}
```

## Execution Boundary

- [ ] This PR does not treat grammar-valid text as execution approval.
- [ ] Runtime handler availability is either verified with code evidence or marked `not verified`.
- [ ] If execution behavior changed, tests or receipts show the side effects.

## Validation

- [ ] `python3 -m json.tool plugins/aurora-command-grammar/.codex-plugin/plugin.json`
- [ ] `python3 -m json.tool plugins/aurora-command-grammar/skills/aurora-command-grammar/references/command-intent-envelope.schema.json`
- [ ] `python3 tools/workspace_verify.py`

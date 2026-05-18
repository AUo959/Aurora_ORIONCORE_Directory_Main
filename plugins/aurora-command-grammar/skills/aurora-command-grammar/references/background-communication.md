# Background Communication Contract

Use this reference when Aurora command grammar needs to be visible to background jobs, future Codex turns, GitHub reviewers, automation reports, or agent handoffs.

## Purpose

Command-like text can be easy to misread as an instruction, a symbolic artifact, or executable runtime input. The background contract makes the interpretation explicit without performing execution.

## Required Separation

- Grammar parsing answers: `What does this text mean under the grammar?`
- Validation answers: `Is the command known and structurally valid?`
- Runtime verification answers: `Is there a current handler and live runtime path?`
- Execution answers: `Was a command/control action actually performed?`

Never collapse these into one status.

## Envelope Locations

Use a command intent envelope when command meaning affects:

- PR descriptions or review replies.
- GitHub issues about grammar, router, CommandNode, mesh routing, or runtime handlers.
- Root control-plane receipts.
- Automation memory.
- Agent dispatcher plans or handoff notes.
- Any report that says a command was parsed, validated, queued, blocked, or executed.

## Minimal Envelope

```json
{
  "schema_version": "1.0.0",
  "raw_text": "THREADWAKE::SRB_0414A_PilotReliquary//.",
  "normalized_text": "THREADWAKE SRB_0414A_PilotReliquary//.",
  "intent_type": "validate",
  "grammar_family": "aurora_symbolic_command",
  "ast_shape": "command_invocation",
  "command_heads": ["THREADWAKE"],
  "arguments": [
    {
      "name": null,
      "value": "SRB_0414A_PilotReliquary",
      "kind": "positional"
    }
  ],
  "modifier": null,
  "warnings": [],
  "validation_status": "valid",
  "validation_issues": [],
  "runtime_handler_verified": false,
  "execution_status": "not_requested",
  "target_repo": "AUo959/aurora-cloudbank-symbolic",
  "authority_refs": [
    "src/aurora/core/command_grammar/parser.py",
    "src/aurora/core/command_grammar/catalog.py",
    "tests/test_aurora_command_grammar.py"
  ],
  "recommended_next_action": "Verify runtime handler before execution.",
  "receipt_refs": []
}
```

## Status Values

Use these values consistently:

- `intent_type`: `parse`, `normalize`, `validate`, `explain`, `mesh_route_map`, `execute_request`, `background_handoff`
- `grammar_family`: `aurora_symbolic_command`, `mesh_router`, `command_router`, `ordinary_prose`, `unknown`
- `ast_shape`: `command_invocation`, `command_sequence`, `range_chain`, `mesh_route`, `unknown`, `none`
- `validation_status`: `valid`, `valid_with_warnings`, `invalid`, `not_validated`, `not_applicable`
- `execution_status`: `not_requested`, `blocked_pending_verification`, `ready_for_explicit_approval`, `executed`, `failed`, `not_applicable`

## Handoff Language

Use concrete phrases in background artifacts:

- `parsed only`
- `normalized but not executed`
- `grammar-valid; runtime handler not verified`
- `cataloged but handler not verified`
- `mesh route mapped; message not sent`
- `execution blocked pending runtime verification`

Avoid phrases that overclaim:

- `command completed` unless execution evidence exists
- `live` unless runtime state was checked
- `canonical handler` unless code evidence confirms it
- `safe to execute` unless target repo, runtime, and side effects were verified

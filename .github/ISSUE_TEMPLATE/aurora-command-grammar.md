---
name: Aurora command grammar
about: Track command grammar, router, mesh mapping, or runtime-handler verification work.
title: "command-grammar: "
labels: docs, architecture
assignees: ""
---

## Scope

- Target repo:
- Grammar family: `aurora_symbolic_command` / `mesh_router` / `command_router`
- Related command text:

## Problem

Describe whether this is a parse, normalize, validate, mesh-route mapping, runtime-handler, or background communication issue.

## Command Intent Envelope

Attach a filled envelope when command meaning affects the issue.

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
  "runtime_handler_verified": false,
  "runtime_refs": [],
  "execution_status": "not_requested",
  "target_repo": null,
  "authority_refs": [],
  "recommended_next_action": "",
  "receipt_refs": []
}
```

## Acceptance Criteria

- [ ] Grammar interpretation is separated from runtime execution.
- [ ] Runtime handler status is marked verified or not verified.
- [ ] Root/nested repo boundary is explicit.
- [ ] Tests, receipts, or source links are attached.

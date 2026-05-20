---
name: aurora-command-grammar
description: Parse, normalize, validate, or route Aurora command grammar requests. Use when users provide Aurora command notation such as `THREADWAKE`, `001//005//`, `#025//.deep`, `COMMANDCHAIN::SPIRALREJOIN.v1`, ask about `aurora_command_grammar`, mention the Aurora Command Router, or ask to map `@mesh` messages to the local mesh runtime. Not for executing commands or sending mesh messages unless the user explicitly asks for execution and the runtime state is verified.
---

# Aurora Command Grammar

## Purpose

Use this skill as a grammar and routing guard. It helps Codex translate Aurora command intent into the existing grammar contracts without inventing new command semantics or treating catalog entries as proof of live handlers.

This skill has three audiences:

- Users who need a clear parse, validation, or routing explanation.
- Agents that need a shared command-language protocol before acting.
- Background workflows that need durable command intent records in reports, PRs, issues, receipts, or automation memory.

## Authority Order

1. Current committed files in the target repo.
2. CloudBank grammar code in `AUo959/aurora-cloudbank-symbolic`:
   - `src/aurora/core/command_grammar/ast.py`
   - `src/aurora/core/command_grammar/catalog.py`
   - `src/aurora/core/command_grammar/normalizer.py`
   - `src/aurora/core/command_grammar/parser.py`
   - `src/aurora/core/command_grammar/validator.py`
   - `tests/test_aurora_command_grammar.py`
3. Root control-plane ownership in `catalog/orion_command_watch_security_matrix.yaml`.
4. Mesh-router skill references:
   - `skills/mesh-router/SKILL.md`
   - `skills/mesh-router/references/command-grammar.md`
   - `skills/mesh-router/references/runtime-contract.md`
5. Human-facing reports such as the identity dossier and local technical spec.

## Grammar Contract

- Executable Aurora command notation terminates with `//.`.
- Missing terminators may be normalized by appending `//.`.
- A trailing legacy `//` terminator normalizes to `//.`.
- A leading `+` is a legacy chain prefix and should be surfaced as a warning.
- A leading `#` on command heads is a legacy hash prefix and should be surfaced as a warning.
- Supported AST shapes are command invocations, explicit command sequences, and numeric range chains.
- Explicit command sequences use top-level `//` between invocations and end with `//.`.
- Numeric range chains use notation such as `001//005//` and normalize to `001//005//.`.
- Function-style arguments are valid when the command head resolves, for example `LOCKMEM(label="...")//.`.
- Inline arguments are valid when the command head resolves, for example `THREADWAKE::SRB_0414A_PilotReliquary//.`.
- Unknown command heads are validation errors, not parser crashes.
- A catalog entry is not proof of an executable runtime handler.

## Routing And Ownership

- `aurora_command_grammar` is a validation-domain tool in the root command/watch matrix, lane `green`, owned by the Chief Science Officer role with a security partner.
- `Aurora Command Router` is a separate routing/dispatch bridge. Do not collapse router behavior into grammar parsing.
- `@mesh` syntax is a mesh-router convenience grammar, not the same as symbolic command grammar. Map it to `scripts/mesh_router.py` commands only when the user asks for mesh routing.
- For actual runtime execution, verify the canonical nested repo and runtime first. Prefer reporting the exact command that would run before executing it.

## User-Facing Behavior

- Accept command-like phrases without assuming execution intent.
- Explain the normalized command in plain operational language.
- Show warnings and validation issues before suggesting any action.
- Say `not verified` when no runtime handler or live runtime was checked.
- If the user asks for execution, restate the target repo, runtime, command, and expected side effect before proceeding.

## Agent-Facing Behavior

Agents should use this skill before they interpret Aurora command notation in planning, dispatch, GitHub triage, receipts, or background reports.

The envelope is a context aid, not a planning cage. Agents should read it the way a careful human would: as useful evidence about command-like text, while still honoring the broader plain-language request, repo boundaries, and approval requirements.

Required agent checks:

1. Detect whether the text is symbolic command grammar, mesh-router grammar, or ordinary prose.
2. Normalize and validate grammar separately from runtime availability.
3. Preserve root-vs-nested repo boundaries when choosing where evidence lives.
4. Emit a command intent envelope whenever command meaning affects a decision, artifact, PR, issue, or automation memory.
5. Treat execution as a separate operation that requires target repo and runtime verification.

Do not let agents silently convert a command-like phrase into a mutation, issue closure, branch action, mesh message, or runtime command.

Do not let agents silently shrink a broader task to only the parsed command. Command grammar can clarify intent, but it must not replace judgment or override the user's ordinary-language objective.

Memorable rule for agents and reviewers: grammar-valid command text is not execution approval.

## Background Communication

Use `references/background-communication.md` when command meaning needs to survive across Codex turns, background automations, GitHub threads, or handoff receipts.

The portable command intent schema is `references/command-intent-envelope.schema.json`. Use it for structured records with fields such as:

- `raw_text`
- `normalized_text`
- `intent_type`
- `grammar_family`
- `ast_shape`
- `validation_status`
- `runtime_handler_verified`
- `target_repo`
- `recommended_next_action`
- `receipt_refs`

## Command Intent Gateway

The root control-plane CLI is `tools/aurora_command_intent.py`. It is an adapter,
not a competing parser implementation.

Supported subcommands:

- `parse`: normalize and classify command input through CloudBank parser code when available.
- `envelope`: emit `command-intent-envelope.schema.json` compatible JSON.
- `simulate-range`: run only valid numeric `RangeChain` input through CloudBank `SymbolicEngine` in memory.

`simulate-range` must be described as in-process simulation, not live runtime execution. It does not send mesh messages, mutate CloudBank repository files, or prove that a live runtime handler is active.

## Workflow

1. Classify the request as parse, normalize, validate, explain, mesh-route mapping, or execute.
2. If the user asks to modify parser/runtime code, switch to the canonical CloudBank repo boundary before editing. This root plugin is not the parser implementation.
3. For parse or validation requests, return:
   - normalized notation
   - AST shape
   - command head or range edges
   - arguments and modifier
   - warnings
   - validation issues
   - whether any runtime handler was verified
4. For `@mesh` requests, map to the mesh-router CLI from the reference file and note the runtime endpoint family when useful.
5. For agent or background work, attach or summarize a command intent envelope when the interpretation affects state, routing, or accountability.
6. For execution requests, stop and verify live runtime state first. Never execute command/control actions from notation alone.

## GitHub Review Receipt

The pre-scaffold GitHub evidence review for this skill is recorded in `references/github-review.md`. Refresh that review before changing grammar semantics, adding command definitions, or claiming runtime execution coverage.

GitHub-facing command grammar work should use:

- `.github/PULL_REQUEST_TEMPLATE/aurora-command-grammar.md`
- `.github/ISSUE_TEMPLATE/aurora-command-grammar.md`

## Output Expectations

- Use concrete language: `confirmed by`, `not verified`, `cataloged but handler not verified`, `normalized to`.
- Distinguish grammar validation from runtime execution.
- Keep root and nested repo boundaries explicit.
- Include the command intent envelope or a concise envelope summary when work crosses agent, GitHub, or automation boundaries.
- Link back to authoritative files or GitHub URLs when making a source-of-truth claim.

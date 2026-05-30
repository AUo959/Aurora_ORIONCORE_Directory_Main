# GitHub Review For Aurora Command Grammar Plugin

Reviewed: 2026-05-18

## Scope

This review checked live GitHub state before creating the repo-local `aurora-command-grammar` plugin. The review covered owner-scoped code search, issue/PR search, root repository metadata, CloudBank command grammar code, mesh-router references, command router surfaces, and prior root plugin scaffolding.

## Repositories Checked

- `AUo959/Aurora_ORIONCORE_Directory_Main`
- `AUo959/aurora-cloudbank-symbolic`
- `AUo959/qgia-knowledge-library`
- `AUo959/qgia-knowledge-spine`
- `AUo959/CanonRec`
- `AUo959/DuelSim_v2.0`

## Key Findings

- No existing `aurora-command-grammar` plugin was found by owner-scoped GitHub code or issue search.
- Root repo `AUo959/Aurora_ORIONCORE_Directory_Main` is private, default branch `main`, and already contains the repo-local plugin pattern through `aurora-workspace-guard`.
- Root PR `#5` merged the plugin/marketplace pattern and classified `.agents` and `plugins` as root control-plane tooling.
- Root `catalog/orion_command_watch_security_matrix.yaml` assigns `aurora_command_grammar` to the validation domain, lane `green`, with science ownership and security partnership.
- Root identity/technical reports describe command grammar as a tool binding and state that executable Aurora commands require the `//.` terminator.
- CloudBank has the actual command grammar implementation under `src/aurora/core/command_grammar/` with parser, normalizer, catalog, validator, AST types, public exports, and tests.
- CloudBank tests cover missing terminator normalization, named chain invocation, legacy hash prefix plus modifier, explicit sequence chains, inline arguments, function-style arguments, numeric range execution through `SymbolicEngine`, and unknown command validation errors.
- `skills/mesh-router/references/command-grammar.md` defines a separate `@mesh` convenience grammar that maps user intent to `scripts/mesh_router.py`.
- `skills/mesh-router/references/runtime-contract.md` lists the canonical mesh runtime endpoint family.
- Aurora Command Router / CommandNode is a related dispatch surface, not the same thing as grammar parsing.
- CloudBank issue `#431` tracked consolidation of command node variants into unified architecture and is closed.
- CloudBank issues `#720` and `#712` tracked the distinction between command catalog entries such as `RESETCORE` and verified restore/runtime handlers; they are closed, but grammar catalog presence still should not be treated as handler proof without current code evidence.

## Primary GitHub Sources

- Root repo: <https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main>
- Root PR #5: <https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/pull/5>
- Root command/watch matrix: <https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/blob/main/catalog/orion_command_watch_security_matrix.yaml>
- Root local technical spec: <https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/blob/main/reports/analysis/LOCAL_PROJECT_TECHNICAL_SPEC__2026-03-09.md>
- Root Aurora identity dossier: <https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/blob/main/reports/analysis/AURORA_IDENTITY_DOSSIER__2026-03-08.json>
- CloudBank parser: <https://github.com/AUo959/aurora-cloudbank-symbolic/blob/main/src/aurora/core/command_grammar/parser.py>
- CloudBank catalog: <https://github.com/AUo959/aurora-cloudbank-symbolic/blob/main/src/aurora/core/command_grammar/catalog.py>
- CloudBank validator: <https://github.com/AUo959/aurora-cloudbank-symbolic/blob/main/src/aurora/core/command_grammar/validator.py>
- CloudBank normalizer: <https://github.com/AUo959/aurora-cloudbank-symbolic/blob/main/src/aurora/core/command_grammar/normalizer.py>
- CloudBank AST model: <https://github.com/AUo959/aurora-cloudbank-symbolic/blob/main/src/aurora/core/command_grammar/ast.py>
- CloudBank command grammar tests: <https://github.com/AUo959/aurora-cloudbank-symbolic/blob/main/tests/test_aurora_command_grammar.py>
- Mesh-router skill: <https://github.com/AUo959/aurora-cloudbank-symbolic/blob/main/skills/mesh-router/SKILL.md>
- Mesh-router command grammar reference: <https://github.com/AUo959/aurora-cloudbank-symbolic/blob/main/skills/mesh-router/references/command-grammar.md>
- Mesh-router runtime contract: <https://github.com/AUo959/aurora-cloudbank-symbolic/blob/main/skills/mesh-router/references/runtime-contract.md>
- Unified CommandNode: <https://github.com/AUo959/aurora-cloudbank-symbolic/blob/main/src/core/command_node/index.js>
- CloudBank issue #431: <https://github.com/AUo959/aurora-cloudbank-symbolic/issues/431>
- CloudBank issue #720: <https://github.com/AUo959/aurora-cloudbank-symbolic/issues/720>
- CloudBank issue #712: <https://github.com/AUo959/aurora-cloudbank-symbolic/issues/712>

## Plugin Implication

The root plugin should be an operator-facing Codex skill that references and enforces the existing grammar contract. It should not copy parser code into the root control-plane repo or claim runtime execution coverage unless the relevant CloudBank handler and runtime state are verified.

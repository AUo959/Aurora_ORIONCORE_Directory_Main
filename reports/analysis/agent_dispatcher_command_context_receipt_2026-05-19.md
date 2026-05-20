# Agent Dispatcher Command Context Receipt

Generated: 2026-05-19

## Scope

Root control-plane update to make proposed agents see Aurora command grammar the
way a careful human would: useful context, not a limiter or execution approval.

Touched root surfaces:

- `skills/agent-dispatcher/scripts/evaluate_dispatch.py`
- `skills/agent-dispatcher/SKILL.md`
- `skills/agent-dispatcher/agents/openai.yaml`
- `plugins/aurora-command-grammar/skills/aurora-command-grammar/SKILL.md`
- `tests/test_agent_dispatcher_skill.py`

No nested repo files were mutated.

## Behavior

The dispatcher now emits `command_context` in its JSON contract. When command-like
text appears, it calls the root `tools/aurora_command_intent.py` gateway and
attaches normalized command intent to proposed agent roles as `command_intent`.

The field is explicitly `informational_only`. It must not:

- force agent dispatch
- suppress agent dispatch
- narrow a broader plain-language task
- authorize execution
- send mesh messages
- replace runtime verification

## Evidence

Natural-language multi-lane prompt:

```bash
python3 skills/agent-dispatcher/scripts/evaluate_dispatch.py \
  "Please use two agents to look at the THREADWAKE path the way human reviewers would: one reviews architecture notes, the other checks tests and risk, and neither executes it." \
  --pretty
```

Observed:

- `dispatch_verdict`: `propose_council`
- `approval_gate`: `true`
- `command_context.present`: `true`
- `command_context.dispatch_effect`: `informational_only`
- first normalized command: `THREADWAKE//.`
- proposed roles include `command_intent: context_only: THREADWAKE//.; do not execute or constrain the task from grammar alone`

Natural-language linear prompt:

```bash
python3 skills/agent-dispatcher/scripts/evaluate_dispatch.py \
  "Can you have agents fix the single failing THREADWAKE test?" \
  --pretty
```

Observed:

- `dispatch_verdict`: `explain_no_dispatch`
- `approval_gate`: `false`
- `command_context.present`: `true`
- `material_dispatch_justified`: `false`

This confirms command grammar is visible to agents but does not override
material parallelism.

## Validation

```bash
python3 -m pytest -q tests/test_agent_dispatcher_skill.py
python3 -m pytest -q tests/test_agent_dispatcher_skill.py tests/test_aurora_command_intent.py tests/test_aurora_command_grammar_plugin.py
python3 tools/sync_codex_skill.py --skill agent-dispatcher --validate-package
python3 tools/workspace_verify.py
```

Results:

- dispatcher pytest: `25 passed`
- combined dispatcher/intent/plugin pytest: `36 passed`
- installed `agent-dispatcher` sync: `status: synced`; validator `status: ok`
- workspace verification: pass, `0` findings

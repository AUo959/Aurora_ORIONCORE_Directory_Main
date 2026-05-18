---
name: agent-dispatcher
description: Evaluate natural language requests in the background, extract the optimal workflow shape, and propose approval-gated bespoke agent dispatch plans only when delegation has material parallel-work justification. Use when the user explicitly asks about subagents, agents, delegation, parallel work, worker/explorer roles, an "agent dispatcher", agent council, or swarm; when a task already shows multiple independent workstreams, broad repo audit lanes, migration surfaces, architecture mapping plus independent validation or risk review, coordinated parallel planning, or parallelizable work; or when Codex should decide whether agents are warranted before doing substantial work. The skill must stay silent for ordinary local tasks and must not spawn or initialize agents by itself; it prepares a concrete plan and waits for explicit user approval.
---

# Agent Dispatcher

## Overview

Use this skill to evaluate a request, infer the best workflow, and decide whether bespoke subagents are justified. Keep the evaluator in the background for ordinary local work; surface a dispatch recommendation only when agents would reduce elapsed time, improve coverage, or isolate specialist work without increasing coordination risk. Explicit agent language is a request to evaluate delegation, not proof that delegation is warranted. When agents help, explain the role split in concise senior-engineer language so the user learns how to use the environment well.

## Evaluator Component

Treat `scripts/evaluate_dispatch.py` as the evaluator component. It builds a lightweight Workflow Intent Graph and then runs a dispatch decision layer plus tutorial composer instead of relying only on trigger phrases:

1. Split the request into clauses and implied work units.
2. Extract action categories: investigation, implementation, verification, review, and planning.
3. Extract artifact lanes: repo, modules, code, docs, tests, architecture, validation, risk, and archives.
4. Identify sequencing markers and critical-path dependencies such as "before implementing".
5. Estimate independent parallel lanes, specialist separation, and material dispatch criteria.
6. Return a decision contract with a silent-local, explain-no-dispatch, or approval-required dispatch verdict.

Use it directly for repeatable tests or as a mental checklist when tool execution is unnecessary:

```bash
python3 skills/agent-dispatcher/scripts/evaluate_dispatch.py \
  "This migration touches docs, code, validation, and risk review. Split the work intelligently." \
  --pretty
```

The evaluator emits this portable JSON contract:

- `request_summary`
- `workflow_graph`
- `dispatch_verdict`
- `reasoning_factors`
- `recommended_pattern`
- `agent_roles`
- `local_critical_path`
- `approval_gate`
- `user_facing_explanation`

## Dispatch Decision

Run the evaluator in the background for ambiguous or broad requests.

- If it returns `silent_local`, do not mention agents unless the user explicitly asked about them.
- If it returns `explain_no_dispatch`, explain briefly why the task should stay local or be clarified first.
- If it returns `propose_dispatch`, `propose_council`, or `propose_swarm`, draft the approval-gated plan before initializing anything.

Propose agents only when at least two material criteria are true:

- The work has separable streams that can run in parallel.
- A side investigation, verification pass, or specialist implementation can proceed without blocking the immediate next local step.
- The task has enough breadth that one agent would either under-explore it or lose useful context.
- The result benefits from independent review, such as code review, migration planning, failure triage, or evidence gathering.
- There are distinct write scopes that can be assigned without merge conflicts.
- A scan, archive, evidence, or repo audit has many independent lanes that can be searched without shared write scope.

Do not propose agents when the task is small, linear, privacy-sensitive, destructive, tightly coupled to one file, a single failing test, blocked on one unknown that Codex should inspect directly, or when delegation would take longer to explain than to do. If the user says "use agents" for that shape of task, explain that the work should stay local because there is not enough independent parallelism.

If no dispatch is warranted and the user did not ask about agents, stay silent about dispatch and continue with the local plan. If the user explicitly asked whether to use agents, say no briefly, explain the reason, and continue locally if execution was requested.

## Workflow

1. Parse the natural language objective.
   - Identify the deliverable, target repo/path, constraints, risks, deadline, and validation expectations.
   - Ask one concise clarification question only if the target or permission boundary is unsafe to infer.
   - If the request contains Aurora command notation, `aurora_command_grammar`, `Aurora Command Router`, or `@mesh` routing language, use the `aurora-command-grammar` protocol to classify and normalize command intent before planning agents.
2. Separate critical-path work from sidecar work.
   - Keep the immediate blocking task local.
   - Delegate only bounded work that can proceed in parallel or independently.
3. Choose the smallest useful agent set.
   - Prefer one or two agents.
   - Use a council only when several independent perspectives must compare architecture, risk, implementation strategy, or validation.
   - Use a swarm only when many independent search, audit, or extraction lanes can run without shared write scopes.
   - Add more agents only when the workstreams are genuinely independent.
   - Map bespoke roles onto available agent types when a tool exposes fixed roles, such as explorer, worker, reviewer, verifier, or default.
4. Draft the dispatch plan.
   - Make every agent's purpose, inputs, scope, and output contract explicit.
   - Include write ownership for coding agents.
   - State what Codex will do locally while agents run.
   - Include coordination, merge, and validation steps.
5. Stop for approval.
   - Do not spawn, initialize, or message agents until the user explicitly approves the plan.
   - Treat "approved", "proceed with dispatch", "spawn these agents", or equivalent current-turn language as approval only after the concrete dispatch plan is visible.
   - Treat silence, prior preference, inferred urgency, a broad "go ahead", or a general desire for agents as insufficient when no dispatch plan has been presented.

## Plan Format

Use this structure for the approval request:

```markdown
**Dispatch Recommendation**
Verdict: use agents / use a council / use a swarm / do not use agents.
Reason: one concise paragraph explaining why.

**Material Justification**
- List the concrete parallel lanes or say why they are insufficient.
- State why each delegated lane can run without blocking the local critical path.

**Local Critical Path**
- What Codex will do directly before or while agents run.

**Proposed Agents**
- Agent 1: role, objective, scope, inputs, output contract, boundaries, expected duration.
- Agent 2: role, objective, scope, inputs, output contract, boundaries, expected duration.

**Coordination Plan**
- How results will be reviewed, integrated, and deduplicated.
- Conflict or merge-risk handling.

**Validation**
- Commands, checks, review steps, or evidence expected before declaring done.

**Approval Gate**
I will not initialize agents until you approve this dispatch plan.
```

Keep the plan concrete enough that the user understands what will happen, why each agent exists, and how Codex remains accountable for the final result. If the verdict is "do not use agents", omit `Proposed Agents` and keep the response to the reason, local path, validation, and next action.

## Agent Brief Rules

For each proposed agent, include:

- Role: a specific responsibility, not a vague title.
- Objective: the outcome the agent must produce.
- Context package: files, paths, specs, commands, or artifacts the agent should inspect.
- Scope boundaries: what the agent must not touch.
- Write ownership: exact files or modules if edits are allowed.
- Output contract: findings, patch files, command results, risk list, or handoff notes.
- Dependency status: whether the task is independent, blocked, or depends on another result.
- Stop condition: when the agent should finish instead of broadening scope.
- Command intent: when the task includes Aurora command grammar or mesh routing language, include the normalized intent envelope or say `none`.

For coding work, tell worker agents they are not alone in the codebase, must not revert unrelated edits, and must adapt to changes made by others.

## Safety Rules

- Do not use agents as a substitute for reading the obvious local context first.
- Do not delegate the task that blocks the very next local action.
- Do not create overlapping write scopes.
- Do not ask an agent to perform destructive, credentialed, or publishing actions unless the user explicitly approved that exact operation.
- Do not ask an agent to execute an Aurora command or send a mesh message from grammar text alone. Require target repo and runtime verification first.
- Do not hide uncertainty. Label assumptions and open questions in the plan.
- After approval, keep the user informed about which agents were started and why.
- After agents return, review their outputs before integrating or reporting them as facts.

## Product Behavior

- Stay invisible for ordinary local tasks.
- Teach through concrete role and workflow tradeoffs when delegation is helpful.
- Use the current environment's real agent capabilities and constraints instead of pretending unavailable roles exist.
- Keep Aurora-specific sync or install details as local maintenance notes, not part of the portable dispatcher concept.

## Example Triggers

- "This is broad. Should we use subagents?"
- "Plan the work and suggest agents if useful."
- "Create a parallel investigation plan."
- "Use an explorer for repo mapping and a worker for the patch if warranted."
- "I need a complete agent plan before you initialize anything."

# Aurora_ORIONCORE_Directory_Main#90: [Work Order] GPT-6 adoption across Aurora runtime and agent surfaces

- URL: https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/issues/90
- State at archive: open
- Author: AUo959
- Created: 2026-09-26T22:13:52Z
- Updated: 2026-10-04T22:16:28Z
- Labels: none
- Milestone: none

## Linked pull requests (head SHA at archive time)

- Aurora_ORIONCORE_Directory_Main#13 — deps: bump actions/checkout from 4 to 6 — merged — `dependabot/github_actions/actions/checkout-6` @ `35aa1801c7cc8d5fc3ee3488a35e4b1425a9cea3`
- Aurora_ORIONCORE_Directory_Main#101 — feat(ui): add offline Aurora Operator Atlas interactive preview — open (draft) — `feat/intelligent-ui-interactive-demo-20261015` @ `acc11f6cef9c395255e09f1120e58af34b33206f`

## Branches named in the issue

- none

## Original body

## Work order

**Date opened:** 2026-09-26  
**Scope:** Cross-repository adoption of the GPT-6 model family where it improves Aurora without moving canonical state or simulation authority into an LLM.

### Trigger

OpenAI released GPT-6 Sol and GPT-6 Luna on 2026-09-22 alongside GPT-6 Astra. Current official guidance confirms:

- `gpt-6-astra`: highest-capability reasoning/agent model.
- `gpt-6-sol`: strong reasoning/coding/agent model with lower cost.
- `gpt-6-luna`: high-volume/low-cost worker model.
- All three expose a 1,050,000-token context window and up to 128,000 output tokens.
- GPT-6 supports explicit reasoning effort; Sol/Luna also support `none`.
- Responses API is the preferred reasoning/tool path; Astra tool calling requires Responses.
- GPT-6 adds async tool calling and mid-turn steering.
- GPT-5.6+ prompt caching supports explicit cache controls/breakpoints; GPT-6 can change reasoning effort mid-conversation while preserving cached prefixes.
- Standard API pricing (<=272K prompt tokens): Astra $10 input / $1 cached / $12.50 cache-write / $50 output; Sol $2 / $0.20 / $2.50 / $10; Luna $0.10 / $0.01 / $0.125 / $0.50 per 1M tokens.
- Requests above 272K input tokens have higher pricing, so the 1.05M window is a capability ceiling, not a default context target.

Official references:
- https://developers.openai.com/api/docs/models
- https://developers.openai.com/api/docs/guides/latest-model
- https://developers.openai.com/api/docs/guides/deployment-checklist
- https://developers.openai.com/api/docs/guides/prompt-caching
- https://developers.openai.com/api/docs/changelog

### Architecture decision

Preserve the existing authority boundary:

**Models reason; Aurora governs.**

Do not make model output canonical state. CanonRec remains canon authority; governed runtimes remain state-transition authorities; deterministic L1 simulation invariants remain deterministic and auditable.

### Proposed model-role routing

- **ARCHITECT / difficult audit / cross-repo synthesis:** GPT-6 Astra
- **BUILDER / primary reasoning / coding / tool-using agent:** GPT-6 Sol
- **WORKER / classifier / evaluator / repeated simulation support:** GPT-6 Luna
- **CANON / symbolic truth / deterministic state transition:** Aurora-native governed systems, not the LLM

Model role must be a capability/routing concept rather than hard-coding a single model globally.

### Deliverables

1. CloudBank: modernize the OpenAI integration around Responses API, verified GPT-6 catalog entries, reasoning-effort control, model-role routing, cache-aware context construction, usage telemetry, and representative evals.
2. AuroraOS: remove the hard-coded GPT-5 dependency from the primary agent path; make the model role configurable; verify GPT-6 Responses/tool support through the current AI SDK/Mastra stack; stabilize reusable prompt/tool prefixes for caching.
3. Root control plane: document the adopted model-role policy and update automation/model references only after the implementation repos pass their eval gates.
4. Preserve current CanonRec and L1 authority contracts. No canon promotion or simulation-rule changes are part of this work order.

### Required evaluation gate

Before changing production/default routing, run representative Aurora tasks across at least Sol/Luna and the current baseline. Include Astra only for tasks where its higher capability is plausibly useful.

Track:
- task success / invariant adherence
- symbolic/canon drift
- tool-call correctness
- latency
- input/output/reasoning tokens
- cached-input and cache-write tokens
- cost per successful task

### Explicit non-goals

- Do not dump the entire repository or canon corpus into the 1.05M context window by default.
- Do not replace deterministic L1 event/state transitions with free-form model generation.
- Do not let model confidence promote run state into canon.
- Do not add tickets to CanonRec solely for model integration; it is an authority dependency, not the OpenAI runtime owner.
- Do not involve Superloop Workshop unless a later concrete interface dependency is identified.

### Completion definition

This work order is complete when implementation tickets in the runtime-owning repositories are merged or explicitly rejected with rationale, the cross-repo model-role policy is recorded here, and the eval evidence supports any new default routing.

## Comments (2)

### AUo959 — 2026-09-26T22:14:40Z

<https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/issues/90#issuecomment-5850368772>

Implementation tickets opened:

- CloudBank runtime/model integration: AUo959/aurora-cloudbank-symbolic#1610
  https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1610
- AuroraOS agent-spoke integration: AUo959/AuroraOS#12
  https://github.com/AUo959/AuroraOS/issues/12

Boundary review completed before filing:
- CanonRec: no implementation issue opened; it remains an authority dependency, not the OpenAI execution owner.
- superloop-workshop: no implementation issue opened; no concrete GPT/OpenAI runtime dependency was found.
- aurora-cloudbank-symbolic1: no issue opened; registered as a dormant prototype rather than the active CloudBank runtime.

Primary sequencing: CloudBank foundation/evals -> AuroraOS provider + role integration -> root control-plane model/automation policy update after evidence gates pass.

### AUo959 — 2026-10-04T22:16:28Z

<https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/issues/90#issuecomment-5985040547>

## Context refresh — 2026-10-04

Official OpenAI guidance since this work order was opened changes the routing/execution picture:

- `gpt-6.1-sol` supersedes the original Sol recommendation for complex repeated work: 1.05M context, 128K max output, $2/M input, $0.10/M cached input, $2.50/M cache writes, $10/M output (short-context Standard).
- GPT-6.1 Sol supports `low|medium|high|xhigh|max` reasoning; it does **not** support `none`.
- Responses Multi-agent is currently beta for GPT-6.1 Sol and GPT-5.6. Current docs do **not** identify Astra as the Responses Multi-agent model, so Astra should remain a frontier escalation tier rather than the assumed delegated coordinator.
- Multi-agent has a distinct context lifecycle: implicit per-agent server compaction; no `/responses/compact`, `reasoning.summary`, or `max_tool_calls`.
- Mid-turn steering is a GPT-6 Responses-WebSocket capability.
- Reasoning `configuration_update` preserves cache eligibility in standard single-agent mode, but cannot be treated as freely composable with automatic compaction or Multi-agent.

Updated routing intent:
**Luna -> cheap bounded worker; GPT-6.1 Sol -> primary coordinator/builder; Astra -> frontier escalation.**

New architecture/control ticket: #95
https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/issues/95

New implementation tickets:
- CloudBank #1625 — GPT-6.1 Sol Multi-agent behind validated state-delta boundary
  https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1625
- AuroraOS #13 — provider compatibility spike for Multi-agent + steering
  https://github.com/AUo959/AuroraOS/issues/13

Official references:
https://developers.openai.com/api/docs/models/gpt-6.1-sol
https://developers.openai.com/api/docs/guides/responses-multi-agent
https://developers.openai.com/api/docs/guides/deployment-checklist
https://developers.openai.com/api/docs/guides/steering
https://developers.openai.com/api/docs/guides/reasoning

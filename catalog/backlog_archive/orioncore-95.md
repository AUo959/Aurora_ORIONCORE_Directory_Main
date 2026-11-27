# Aurora_ORIONCORE_Directory_Main#95: [Architecture] Define delegated-agent execution and validated state-delta contract

- URL: https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/issues/95
- State at archive: open
- Author: AUo959
- Created: 2026-10-04T22:15:18Z
- Updated: 2026-10-04T22:16:33Z
- Labels: none
- Milestone: none

## Linked pull requests (head SHA at archive time)

- Aurora_ORIONCORE_Directory_Main#12 — deps: bump actions/upload-artifact from 4 to 7 — merged — `dependabot/github_actions/actions/upload-artifact-7` @ `7411845766663d9cf357bfe7f62667936821d759`
- Aurora_ORIONCORE_Directory_Main#13 — deps: bump actions/checkout from 4 to 6 — merged — `dependabot/github_actions/actions/checkout-6` @ `35aa1801c7cc8d5fc3ee3488a35e4b1425a9cea3`

## Branches named in the issue

- none

## Original body

Parent model-adoption work order: https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/issues/90

## Context update — 2026-10-04

Official OpenAI guidance now materially changes the execution design assumed when #90 was opened.

### Current facts

- `gpt-6.1-sol` is the current Sol model for complex work, with a 1,050,000-token context window and 128,000 max output.
- GPT-6.1 Sol supports reasoning effort `low|medium|high|xhigh|max`; unlike GPT-6 Sol, it does **not** support `none`.
- GPT-6.1 Sol standard pricing for <=272K prompt tokens is $2/M input, $0.10/M cached input, $2.50/M cache writes, $10/M output.
- Tool calling on GPT-6.1 Sol should use the Responses API.
- Responses **Multi-agent** is currently beta and documented for GPT-6.1 Sol and GPT-5.6. It is not currently documented as an Astra Responses-Multi-agent feature.
- Responses Multi-agent lets one root agent spawn and coordinate subagents. Subagents share the request model and configured tools.
- Default `max_concurrent_subagents` is 3; OpenAI recommends measuring quality, latency, and cost before increasing it.
- Multi-agent currently does not support `/responses/compact`, `reasoning.summary`, or `max_tool_calls`; server-side compaction is enabled implicitly for root and subagent contexts.
- GPT-6 supports async function/custom tools. In Multi-agent mode, async tools should not be combined with parallel tool calls.
- Mid-turn steering is available over Responses WebSocket for GPT-6.
- `configuration_update` can change reasoning effort mid-conversation while preserving prompt-cache eligibility, but only in standard single-agent mode; it cannot be combined with automatic compaction/truncation.

Official references:
- https://developers.openai.com/api/docs/models/gpt-6.1-sol
- https://developers.openai.com/api/docs/guides/responses-multi-agent
- https://developers.openai.com/api/docs/guides/deployment-checklist
- https://developers.openai.com/api/docs/guides/steering
- https://developers.openai.com/api/docs/guides/reasoning
- https://developers.openai.com/api/docs/guides/compaction
- https://developers.openai.com/api/docs/guides/prompt-caching

## Architecture decision to formalize

Aurora should treat delegated model work as an **ephemeral execution tree**, not as an authority tree.

Target flow:

```
canonical / governed state
        |
        v
bounded task snapshot
        |
        v
GPT-6.1 Sol coordinator
        |
        +--> subagent(s)
        +--> Aurora-owned tools
        +--> independent findings
        |
        v
candidate state-delta bundle
        |
        v
Aurora validation / authority gate
        |
        v
commit to governed runtime state
```

A coordinator or subagent may:
- inspect bounded context;
- call tools exposed by Aurora;
- produce findings, plans, evidence, or candidate state deltas.

A coordinator or subagent may **not**:
- promote run state into CanonRec;
- mutate deterministic L1 state outside its existing transition contracts;
- infer authority from model confidence;
- treat subagent consensus as canon;
- silently rewrite an existing symbolic invariant.

## Required contract

Define a cross-repo delegated-execution envelope with at least:

- root task / task ID
- bounded input-state revision(s)
- model + reasoning effort
- agent-tree IDs and parentage
- tool-call IDs and provenance
- findings / candidate deltas
- authority class requested
- validation result
- accepted/rejected delta IDs
- final state revision if committed
- cost/latency/token/cache telemetry where available

The envelope should allow replay/audit without requiring storage of private model reasoning.

## Deliverables

1. Define the delegated-execution/state-delta contract in the root control plane.
2. Keep the contract implementation-neutral enough for CloudBank and AuroraOS.
3. Require CloudBank to prototype Responses Multi-agent behind a feature flag and return candidate deltas rather than direct state mutations.
4. Require AuroraOS to determine whether its Mastra/Vercel provider stack can expose the needed beta Responses controls safely.
5. Update the GPT-6 model-role policy:
   - **worker:** GPT-6 Luna for cheap bounded/high-volume work
   - **coordinator/builder:** GPT-6.1 Sol for delegated agentic work
   - **frontier escalation:** GPT-6 Astra for tasks where quality gains justify cost, but not assumed to be the Responses Multi-agent coordinator
6. Preserve CanonRec and deterministic L1 authority boundaries.

## Acceptance criteria

- [ ] Cross-repo delegated-execution envelope is specified.
- [ ] Authority/commit boundary is explicit and testable.
- [ ] Model-role guidance reflects GPT-6.1 Sol and current Multi-agent availability.
- [ ] Single-agent context lifecycle and Multi-agent context lifecycle are documented separately.
- [ ] Multi-agent limitations are recorded so compaction/reasoning-summary assumptions do not leak across modes.
- [ ] Child implementation/spike tickets are linked.
- [ ] No CanonRec ticket is opened unless a separate canon-policy change is actually proposed.

## Non-goals

- This ticket does not authorize a default-model switch.
- This ticket does not authorize free-form L1 state mutation.
- This ticket does not promote OpenAI's agent tree to Aurora's symbolic/authority hierarchy.


## Comments (1)

### AUo959 — 2026-10-04T22:16:33Z

<https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/issues/95#issuecomment-5985041443>

Implementation children opened:

- CloudBank #1625 — prototype GPT-6.1 Sol Responses Multi-agent behind the validated state-delta boundary:
  https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1625

- AuroraOS #13 — verify Mastra/Vercel provider support for GPT-6.1 Sol Multi-agent, steering, and context lifecycle:
  https://github.com/AUo959/AuroraOS/issues/13

Existing parent modernization tickets remain:
- ORIONCORE #90
- CloudBank #1610
- AuroraOS #12

CanonRec remains an authority dependency only; no new CanonRec execution ticket was opened.

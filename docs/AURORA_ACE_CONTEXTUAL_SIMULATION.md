# Context-authorized simulation work

An Orion simulation assignment can now authorize the routine detail needed to
complete it. The assignment supplies a purpose, target layer, allowed settings,
and finite work budget. The conversation or an upstream simulation producer
submits a need; a durable worker resolves it through existing ACE capabilities.
A separate request to create each character is unnecessary within that scope.

## Layer model

L3 governs truth in both L1 and L2. The rules differ by context:

| Layer | Implemented behavior |
| --- | --- |
| L1, reality-oriented bounded simulation | Existing read-only ACE fact resolution over explicitly authorized, committed L1 JSON evidence. No generation is admitted as evidence. Retrieval does not independently verify external reality. |
| L2, generative sandbox | Retrieve first, then use existing character generation, reconciliation, validation, and native persistence when needed and permitted by the assignment. Facts belong to the isolated world and its settings. |
| L3, governing policy | Bind each decision to the assignment, world, layer, settings digest, and policy digest; refuse scope changes and unauthorized cross-layer effects. |

An L1 operator context describes the task's perspective. It does not assert a
physical engineer exists in an active run or authorize Orion runtime progression.
The preserved Orion run remains separate.

This release implements character completion and bounded fact queries. Faction
and location type are the supported environmental settings; role permissions
belong to the assignment. Different environmental settings require a separate
world so established facts are not silently reinterpreted. Arbitrary physics,
emergent geometry generation, and changes to L3 rules are not implemented by this
adapter. Those must be connected to their appropriate specialist capabilities.

## Reused Aurora capabilities

- `compile_character_invocation` and `compile_canon_invocation` create native
  **autonomic** invocation envelopes, including the triggering coherence need.
- Existing character retrieval prevents duplicate referents; NameService and
  CharForge supply generation; CanonRec validation and ACE native materialization
  preserve the established character transaction.
- Existing canon-fact resolution retrieves L1 evidence and identifies conflicts.
- The persistent world's lock, transaction journal, baseline reconciliation,
  and determination ledger supply write serialization and commit recovery.

The contextual controller adds assignment checks and queue coordination. It does
not replace specialist generation, canon determination, or runtime ownership.

## Assignment and conversational use

Only the local operator CLI grants or revokes assignments. The model-facing MCP
interface has no authorization tool. For example, save this specification to an
operator file and run the authorization command below:

```json
{
  "assignment_id": "orion-archive-survey",
  "purpose": "Supply the archive coordination personnel needed by the bounded expedition survey.",
  "target_layer": "L2",
  "settings": {
    "roles": ["archive_duty_coordinator", "expedition_logistics_liaison"],
    "faction_id": "galactic_union",
    "location_type": "archive_outpost"
  },
  "authority_ref": "operator-approved-archive-survey",
  "max_jobs": 20
}
```

```sh
python tools/aurora_ace_context.py --world /path/to/world authorize --assignment assignment.json
python tools/aurora_ace_context.py --world /path/to/world status
python tools/aurora_ace_context.py --world /path/to/world revoke \
  --assignment-id orion-archive-survey --reason 'Assignment complete'
```

An authorization reference must identify an actual operator instruction. The
sample is a format example, not a grant in another world. Assignment IDs are
immutable; retries with different specifications refuse mutation. Revocation
prevents subsequent work without deleting prior outcomes. Every accepted need
consumes one job slot, including blocked needs, to bound background work.

The separate stdio entry point is `tools/aurora_ace_context_mcp.py --world ...`:

| Tool | Use |
| --- | --- |
| `aurora_context_status` | Discover authorized assignments, world identity, jobs, and worker health. |
| `aurora_simulation_need` | Submit a task-grounded need with assignment ID, stable need ID, question, and structured context. |
| `aurora_need_inspect` | Retrieve the outcome, L3 decision receipt, and native determination/commit references. |

For the example assignment, a normal need is “The survey needs someone to
coordinate incoming expedition logs,” with `role: archive_duty_coordinator`.
Faction and location type are supplied by the assignment. If multiple roles are
permitted, the caller grounds the role in the task; unsupported or missing scope
is surfaced instead of invented. An existing person's ID remains the preferred
anchor for recall.

The original six-tool ACE server and three-tool explicit sandbox interface
remain available. Their authority rules are unchanged. Contextual work uses its
own interface and records assignment authority in the native commit receipt.

## Background lifecycle and recovery

The worker runs while the contextual MCP server is connected. Submitting a need
returns a durable job; generation and persistence happen in the worker. Ordinary
successes have `needs_attention: false`. Blocked operations and true conflicts
set it to true and preserve their evidence. This is a result signal for the
conversation, not an external notification service.

When the server stops, queued/running work stays on disk. A fresh process resumes
it with the same native request identity. An already-recorded commit is reconciled
before replay, preventing a second creation. Worker processes serialize on the
existing world lock. Unexpected repository edits stop mutation. Identical needs
return their recorded job; changed input under the same need ID is refused.

When ACE finds a plausible existing character without an identity anchor, the
need remains `EXECUTION_BLOCKED` with its recovery guidance. This is a request
for grounding, not permission to generate a duplicate. L1 evidence conflicts
remain `TRUE_CONFLICT`; the queue does not choose a preferred reality.

The worker does not continuously inspect or advance CloudBank simulations. A
conversation or future bounded simulation producer emits the need. There is no
always-on host daemon when all contextual MCP processes have exited.

## Persistent installation

The contextual controller may run from a separate committed root clone, while
the world's engine/source revisions remain fixed. Register it as an additional
project MCP server using the world's dedicated Python interpreter. Keep the
controller clone pinned; changing L3 policy invalidates existing grants and
requires an explicitly authorized replacement assignment. Do not refresh the
world's source repositories to install a controller.

```toml
[mcp_servers.aurora_context]
command = "/Users/travisstreets/dev/aurora-ace-runtime/bin/python"
args = ["/Users/travisstreets/dev/aurora-ace-context-runtime/tools/aurora_ace_context_mcp.py", "--world", "/Users/travisstreets/dev/aurora-ace-sandbox"]
startup_timeout_sec = 60
tool_timeout_sec = 180
```

## Verification

```sh
ACE_CONTEXT_E2E=1 python -m pytest tests/test_aurora_ace_contextual.py -q
```

The suite provisions independent worlds and runs actual stdio MCP processes.
It exercises background creation and restart, assignment bounds, L1 evidence and
conflicts, native-commit interruption, concurrent workers, settings tampering,
duplicate prevention, unexpected edits, and path escapes. L1 fixture facts exist
only in disposable test worlds and are not physical evidence or canonical-workspace
changes.

## Verified installation, 2026-09-06

Controller `b4fef21aac14ee5403a4ca08c9ad5588238b9472` is installed in
`/Users/travisstreets/dev/aurora-ace-context-runtime` and registered alongside
`aurora_world` in `/Users/travisstreets/dev/aurora-ace-sandbox`. The authorized
`orion-archive-survey` assignment has a 20-need budget.

A simulation need generated Nerisia Orlanor
(`char_archive_duty_coordinator_35ae7aaccb7f`) through an autonomic invocation and
one native commit. A new server process recalled identical identity/background
and creation history. Duplicate submission produced no additional commit.
Both configured servers reported the same world ready.

Sixteen contextual tests, 23 sandbox/promotion regression tests, the integration
gate, and all 13 ACE composition acceptance rows passed. Canonical repository
heads and working-tree changes, seven protected Orion files, and the original
Jorenon character artifacts remained unchanged.

The [acceptance receipt](../reports/analysis/aurora_ace_contextual_acceptance_2026-09-06.json)
records the assignment, policy/settings binding, native commit, and preservation
snapshot. A copy is stored with the world at `state/contexts/acceptance_receipt.json`.

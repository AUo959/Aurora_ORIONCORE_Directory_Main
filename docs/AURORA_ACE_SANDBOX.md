# Aurora in Codex: persistent character continuity

This operator experience connects Codex to a persistent, isolated Aurora world.
It reuses ACE's character compiler, retrieval, NameService/CharForge completion,
native materialization, and determination ledger. It does not create another
canon engine or another model service.

## Provision once

Use Python 3.12 with `requirements-ace-mcp.txt`, `pytest==8.4.2`, and
`jsonschema==4.25.1`. Provision from a committed implementation revision:

```sh
python tools/aurora_ace_sandbox.py provision \
  --world /Users/travisstreets/dev/aurora-ace-sandbox \
  --repositories-root /Users/travisstreets/dev/Aurora_ORIONCORE_Directory_Main \
  --python /Users/travisstreets/dev/aurora-ace-runtime/bin/python
```

The command refuses an existing destination and creates independent copies of
committed root, CanonRec, and CloudBank revisions at recorded registry pins.
Uncommitted files and machine-local Orion run state are not copied. The copies
have no remotes; only sandbox CanonRec advances. Source checkouts are read-only.
Keep the world directory and its Python environment to retain continuity.

Open the world directory as a trusted Codex project. Its `.codex/config.toml`
registers `aurora_world` over stdio. Restart the server after first configuration.
The generated `AGENTS.md` and `START_HERE.md` define the conversational workflow.
Use the existing Astra model in Codex; no additional model API key is needed.

## Three tools

| Tool | Contract |
| --- | --- |
| `aurora_world_status()` | Read world identity, source revisions, integrity, permitted operations, and pending work. |
| `aurora_character(question, context, request_id, operation="retrieve")` | Retrieve an existing character, preview a completion, or save an explicitly requested creation. |
| `aurora_inspect(invocation_id=None, determination_id=None)` | Inspect exactly one stable reference in the existing ACE packet/ledger history. |

Use `context.name` or `context.canonical_id` for lookup. Generation requires
`role`, `faction_id`, and `location_type`; `observed_behavior` is optional.
The adapter compiles the ordinary ACE invocation rather than accepting a
model-authored internal envelope. IDs and source facts come from ACE output.

`retrieve` never generates. `preview` writes a bounded packet but never commits.
`create` requires an explicit user creation request, retrieves first, and uses
the existing state-bound preview/token/commit sequence under a sandbox-only
policy. It does not require another conversational confirmation of the same
bounded request. The model must not infer creation authority from exploration.

Responses identify the world and entity, distinguish inherited canon from
sandbox-created canon, and include the determination, original creation link,
and saved background where available. Narrative elaboration is not saved fact.

## Durability and refusal behavior

Each request has a durable input fingerprint and outcome. Identical retries
reuse the result; changed input with the same request ID is refused. World-wide
file locking serializes transactions across server processes. Following a native
commit, only the sandbox CanonRec registry baseline advances; existing capability
freshness rules must still pass.

The transaction journal reconciles an already-receipted commit after interruption.
An advanced HEAD without a matching native receipt refuses automatic replay.
`status` and `verify` are non-destructive; `recovery_pending` directs the operator
to retry the same request or inspect its determination. Unexpected edits, stale
previews, shared Git storage, remotes, and symlink escapes refuse mutation.

```sh
python tools/aurora_ace_sandbox.py status --world /path/to/world
python tools/aurora_ace_sandbox.py verify --world /path/to/world
ACE_SANDBOX_E2E=1 python -m pytest tests/test_aurora_ace_sandbox.py -q
```

The E2E suite provisions fresh worlds from committed source. Outside a fully
provisioned checkout, set `ACE_SANDBOX_REPOSITORIES_ROOT` to the canonical
workspace containing the registered source repositories. Tests use real stdio
MCP processes and keep all generated state in temporary independent clones.

## Acceptance story

1. Retrieve Dr. Adrienne Kovas (`char_adrienne_kovas`) from inherited canon.
2. Explicitly create an L2 expedition archivist in an archive outpost.
3. Record the resulting stable entity ID, name, background, and creation receipt.
4. Close the task and server. Open a new Codex task in the same world.
5. Retrieve that ID and inspect its creation determination; confirm unchanged
   identity/background and the same authoritative sandbox commit.

The original 13-row ACE composition gate and the new sandbox tests are separate
acceptance evidence. Neither grants source-world canon promotion, publication,
autonomous completion, relationship editing, or Orion runtime progression.

Completed characters can now be passed to the root-owned
[offline promotion review](AURORA_ACE_PROMOTION_REVIEW.md). It reuses CanonRec
reconciliation and ACE native materialization in a separate rehearsal clone,
preserving the sandbox character and producing a reviewable patch.

## Verified installation (2026-09-06)

The persistent world is `/Users/travisstreets/dev/aurora-ace-sandbox`, using
`/Users/travisstreets/dev/aurora-ace-runtime/bin/python`. Two actual Codex tasks
created and recalled Jorenon Morrowen with identical identity, background, and
creation commit after the first process exited. The complete receipt is
[continuity acceptance](../reports/analysis/aurora_ace_continuity_acceptance_2026-09-06.json).
The independent composition gate passed all 13 rows; all 15 sandbox tests and
the root integration gate passed. Canonical repositories and protected runtime
files matched their pre-implementation snapshots.

For noninteractive Codex CLI demonstrations, use `--approve-for-me` to retain
automatic approval review. The default noninteractive approval-never policy
can refuse project MCP calls, including reads. This host setting is separate
from the sandbox's bounded creation authority.

# Aurora ACE v0.9 Addendum — Local Operator Transaction Choreography

Date: 2026-08-12  
Status: implementation contract

## Purpose

ACE v0.9 adds a durable local operator transaction layer around the existing v0.8 MCP materialization primitives. It does not add another CanonRec writer and it does not widen the MCP protocol surface.

The preserved execution path is:

`operator -> resolve -> preview -> explicit authorization -> existing ace_materialize_commit -> native ACE materializer -> inspect`

The six v0.8 MCP tools remain unchanged. v0.9 adds local transaction choreography and receipts so an operator can see exactly what was prepared, what was authorized, what committed, and whether the resulting determination was inspectable.

## Operator lifecycle

### Prepare

`prepare_operator_transaction(...)` performs the existing bounded ACE resolution and MCP materialization preview, then writes a non-canonical receipt under `reports/ace/mcp_transactions/`.

The receipt is bound to the invocation ID, determination ID, output name, packet digest, authority mode/reference, registered target repository, feature branch, target HEAD, and expected CanonRec baseline.

A prepared receipt has status `awaiting_confirmation`. It includes the exact preview token and declared side effects. Repeating an identical prepare is idempotent and returns the existing receipt.

### Explicit confirmation

No canonical write occurs during prepare. The operator must provide:

- the transaction ID;
- the exact preview authorization token; and
- explicit side-effect acknowledgement.

Wrong tokens and missing acknowledgement fail before the durable receipt leaves `awaiting_confirmation`.

### Commit

Immediately before calling the existing v0.8 commit primitive, the local receipt becomes `commit_in_progress`. This is an observability safeguard: if the process is interrupted around dispatch, the durable control-plane record does not falsely remain in an untouched prepared state.

Canonical materialization is still performed exclusively by `ace_materialize_commit`, which re-runs the state-bound preview and delegates to the existing native `materialize_packet` dispatcher. CanonRec branch protection, clean-worktree checks, baseline compare-and-swap, target restrictions, validation, atomic Git commit behavior, append-only determination semantics, and rollback remain owned by native ACE.

If native dispatch fails, the operator transaction becomes `refused` and records the error type/code/message. A refused transaction is closed against token replay; the operator must prepare a fresh transaction after correcting the underlying state.

### Inspect

After a successful commit, v0.9 calls the existing read-only `ace_inspect` path for the materialized determination and stores that result in the operator receipt.

A successful canonical commit is never reclassified as failed merely because the subsequent inspection step encounters an operational error. In that case the receipt remains `committed` and carries the inspection error for follow-up.

## Replay semantics

A committed or refused operator transaction is terminal. Its authorization token cannot be used to commit the same durable transaction again.

The underlying v0.8 materialization gate independently protects against raw token reuse: once the first CanonRec commit advances HEAD beyond the packet baseline, a second commit attempt with the original packet/token fails closed on baseline drift.

## CLI

`tools/aurora_ace_mcp_operator.py` exposes three local commands:

- `prepare --invocation <json> --output-name <id> --authority-ref <ref>`
- `commit --transaction-id <id> --authorization-token <token> --acknowledge-side-effects [--commit-message ...]`
- `inspect --transaction-id <id>`

The CLI intentionally does not accept an arbitrary repository path, target path, branch override, delegated authority mode, remote endpoint, provider activation, or simulation-control option.

## End-to-end validation contract

The dedicated ACE MCP CI lane provisions the registry-pinned CloudBank and CanonRec repositories, places CanonRec on an ephemeral local feature branch at the exact registered baseline, and runs:

`resolve -> preview -> authorize -> commit -> inspect -> operator replay refusal -> raw MCP token replay refusal`

The test requires exactly one local CanonRec commit, a clean target worktree after commit, a successful post-commit inspection, and refusal of both replay paths. The validation branch is reset locally after the test and is never pushed.

## Authority and simulation boundary

The operator receipt is control-plane provenance, not canon. The authorization token is a state-bound confirmation receipt, not an authentication or identity credential.

ACE v0.9 does not introduce HTTP transport, remote authentication, generic Git publication, arbitrary repository mutation, dynamic runtime binding, provider activation, Orion INIT/resume, or simulation tick advancement.

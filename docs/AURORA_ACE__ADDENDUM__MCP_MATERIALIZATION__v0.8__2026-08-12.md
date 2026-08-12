# Aurora ACE v0.8 Addendum — Owner-Gated MCP Materialization

Date: 2026-08-12
Status: implementation contract

## Purpose

ACE v0.8 extends the v0.7 stdio MCP transport with a deliberately narrow path for canonical materialization. This does not make MCP an authority source and does not create a second materialization engine. The transport may request a materialization only by delegating to ACE's already-existing native materializer after a two-phase authorization handshake.

The preserved architecture is:

`MCP caller -> ACE MCP adapter -> owner-gated preview -> state-bound authorization -> existing ACE materialize_packet -> native CanonRec transaction -> determination + provenance`

## New tools

The MCP surface now contains six tools:

1. `ace_capabilities`
2. `ace_plan`
3. `ace_resolve`
4. `ace_inspect`
5. `ace_materialize_preview`
6. `ace_materialize_commit`

The first four retain their v0.7 responsibilities. The two new tools form one transaction gate; neither replaces ACE validation, packet dispatch, CanonRec transaction logic, or rollback semantics.

## Two-phase materialization gate

### Phase 1: preview

`ace_materialize_preview(output_name, authority_ref)` is non-canonical and non-materializing. It resolves the packet only inside `reports/ace/mcp_runtime`, resolves CanonRec only through `catalog/repo_registry.yaml`, and verifies that the registered checkout is a clean Git worktree on a non-protected feature branch whose HEAD still equals the packet's CanonRec baseline.

The preview emits a deterministic authorization token bound to:

- the semantic digest of the commit-ready determination;
- the supplied owner authority reference;
- the fixed authority mode `owner_gated_materialize`;
- the registered CanonRec target;
- the current feature branch;
- the current target HEAD; and
- the packet's expected CanonRec baseline.

The preview also enumerates the side effects that a successful commit would perform.

### Phase 2: commit

`ace_materialize_commit(...)` requires:

- the same packet output name;
- the same authority reference;
- the exact preview token; and
- an explicit `side_effects_acknowledged=true` flag.

The adapter recomputes the preview immediately before dispatch. If the packet, authority reference, target branch, target HEAD, or expected baseline changed, the token no longer matches and materialization fails closed.

A matching token does not itself create canon. It permits delegation to the existing `materialize_packet` dispatcher, which remains responsible for packet-type selection, schema validation, branch protection, clean-worktree enforcement, baseline compare-and-swap, target-path restrictions, Git commit creation, append-only determinations, and rollback on failure.

## Authority boundary

v0.8 exposes bounded CanonRec mutation but does not expose generic repository writes.

MCP cannot:

- provide an arbitrary repository path;
- select `main` or another protected branch for materialization;
- bypass the packet's recorded CanonRec baseline;
- choose arbitrary target paths;
- select an unregistered materializer;
- use `delegated_materialize` through this transport;
- publish arbitrary files or entities;
- create dynamic Python runtime bindings;
- activate providers or services;
- initialize or resume Orion; or
- advance simulation state.

The MCP materialization authority mode is fixed to `owner_gated_materialize`. The `authority_ref` is an auditable reference to owner approval; it is not treated as an authentication credential. The state-bound token is likewise a confirmation receipt, not a secret or identity proof.

## Failure semantics

The adapter fails closed before materialization when the packet is missing or not commit-ready, CanonRec is absent or not the registered checkout, the worktree is dirty, the branch is protected or detached, the receipt baseline does not match target HEAD, the authority reference is invalid, side effects were not acknowledged, or the authorization token does not match the current state.

After native materialization begins, rollback and receipt integrity remain owned by the existing ACE materializer implementation.

## Compatibility

The adapter remains independent of the MCP SDK. The actual server continues to isolate the official MCP package in the dedicated Python 3.12 lane, while normal ACE tests retain the root repository compatibility policy. The adapter uses PyYAML only for the repository registry, which is already an OrionCore runtime dependency.

## Simulation boundary

This change adds a control-plane transport path only. It does not initialize, resume, observe-forward, or advance the Orion simulation runtime.

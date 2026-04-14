# Aurora CloudBank Untracked GitHub Issue Packet

Generated: 2026-04-09
Scope: issue-ready proposals derived from root control-plane mapping documents for `aurora-cloudbank-symbolic`
Target repo: `AUo959/aurora-cloudbank-symbolic`
Method: local evidence review plus open-issue de-duplication sweep against current GitHub issue state

## Purpose

This packet turns the remaining control-plane structural gaps into a minimal GitHub issue set while avoiding duplication with issues that are already open.

This packet began as a draft and was then used to create live issues after retrying GitHub access outside the sandbox.

## De-Duplication Result

I checked current open issues using both exact and alternate wording across these query families:

- `topology`
- `architecture`
- `documentation`
- `drift`
- `mesh`
- `bridge`
- `L3`
- `catalog`
- `endpoint`
- `inventory`
- `API`
- exact phrases from the control-plane discovery report such as `runtime topology`, `path drift`, `mesh_api`, `EnhancedApiBridge`, and `relayMessage`

### Existing issues explicitly not to duplicate

- `#380` covers CloudHub / MCP / HR integration fragmentation
- `#384` and `#259` cover observability / Prometheus / telemetry
- `#527` and `#529` cover Triplex Handshake mock-removal and remaining ARCHY wiring
- `#593` and related persistence issues cover monitoring state durability, not documentation or topology mapping
- `#597` through `#605` are current security, crash, and ethics-integrity issues; they do not cover the documentation/topology/catalog gaps below

### Conclusion

I did not find an open issue directly covering:

- canonical runtime topology and L3 surface authority
- stale docs / path drift ledger
- platform-wide multi-service API catalog governance

To reduce internal overlap, the `mesh_api.js` production-mount question and the `EnhancedApiBridge` contract question are folded into one L3/runtime-topology issue rather than split into separate tickets.

## Source Evidence

Primary root evidence:

- `docs/aurora_cloudbank_symbolic_architecture_discovery_report.md`

Supporting nested-repo evidence:

- `docs/reports/SYSTEM_RETROSPECTIVE_REPORT.md`
- `docs/aurora-phased-upgrade-roadmap.md`
- `.github/AGENT_WORKFLOW_INVESTIGATION.md`

Relevant lines observed during this pass:

- root discovery report flags path drift and stale snapshots: line 25
- `mesh_api.js` production mounting is unproven: lines 505-538
- `EnhancedApiBridge` / `relayMessage` contract gap: lines 557-578
- unresolved L3 runtime topology questions: lines 645-664
- recommended outputs are runtime topology map, path drift ledger, L3 communications surface map, and API catalog decision: lines 768-798
- nested retrospective flags orphaned monitoring modules, incomplete `hr_system` wiring, and no single endpoint catalog: lines 24-25, 346-351, 576, 744, 791-792
- nested workflow investigation confirms API path drift and legacy entrypoint references: lines 35-37, 48, 363, 431

## Proposed Issue Set

## Issue 1

Title:
- `docs: publish canonical runtime topology and L3 communications authority map`

Why this is not a duplicate:
- no open issue directly covers runtime topology or L3 communications authority
- this is documentation and control-surface clarification work, not Triplex wiring, telemetry, or security remediation
- `mesh_api.js` and `EnhancedApiBridge` are included here to avoid fragmenting one unresolved architecture question into multiple overlapping tickets

Suggested body:

```md
## Summary

Publish a canonical runtime topology map for active `aurora-cloudbank-symbolic` service surfaces, with an explicit L3 communications authority section covering the intended mount and ownership of `mesh_api.js`, `EnhancedApiBridge`, and their contract boundary.

## Problem

The root control-plane discovery report identifies an unresolved runtime-topology gap:

- the platform is multi-surface, but current documentation is not authoritative about which services are actually mounted
- `src/api/mesh_api.js` is a real REST surface, but its production mount is not proven
- `EnhancedApiBridge` depends on a `relayMessage(...)` path that is not clearly defined on the current `MeshFederation` contract
- deployment and documentation paths appear stale or partial for the L3 layer

Without a canonical topology map, architecture and deployment discussions keep collapsing into historical snapshots and test-only assumptions.

## Scope

Document only. Do not implement new routing or change service behavior in this issue.

## Tasks

1. Inventory the active runtime surfaces that participate in the platform topology
2. Identify the authoritative entrypoint or mount path for each active surface
3. Produce a specific L3 communications section covering:
   - intended mount for `mesh_api.js`
   - intended mount and ownership for `EnhancedApiBridge`
   - whether `relayMessage(...)` is canonical, missing, or obsolete
   - which component is the authoritative runtime owner for L3 communications
4. Mark each uncertain or historical path explicitly as `unverified`, `stale`, or `superseded`
5. Commit the resulting topology artifact in repo docs

## Acceptance Criteria

- [ ] A single committed document describes current runtime topology across active platform surfaces
- [ ] L3 communications authority is declared explicitly
- [ ] `mesh_api.js` production-mount status is resolved as `active`, `inactive`, or `not verified`
- [ ] `EnhancedApiBridge` contract status is resolved as `active`, `missing dependency`, or `superseded`
- [ ] Historical or stale paths are labeled, not silently removed

## Evidence

- Root control-plane discovery report: unresolved runtime-topology and L3 questions
- Nested workflow investigation: `api/aurora_api.py` vs root `aurora_api.py` path drift
```

## Issue 2

Title:
- `docs: build stale-docs and path-drift ledger for runtime and operator entrypoints`

Why this is not a duplicate:
- no open issue currently targets stale docs, legacy path references, or entrypoint drift as its primary problem
- this issue is intentionally scoped to documentation drift and operator-facing path truth, not code fixes
- it complements Issue 1 but does not duplicate it: Issue 1 answers topology authority, while this issue catalogs stale and conflicting references that need explicit status

Suggested body:

```md
## Summary

Create a path-drift ledger that records stale, conflicting, and legacy documentation or script references for operator-facing runtime entrypoints.

## Problem

Multiple repo artifacts reference paths and launch patterns inconsistently. The root discovery report warns that docs and deployment scripts contain path drift and stale snapshots. The nested workflow investigation confirms a concrete example:

- `api/aurora_api.py` is the main API entrypoint
- root-level `aurora_api.py` references are legacy or documentation artifacts
- README-level guidance has contained inconsistent path references

The result is preventable operator error and difficulty separating active entrypoints from historical guidance.

## Scope

Document and classify drift. Do not remove historical references unless their status is recorded.

## Tasks

1. Enumerate runtime, deployment, and operator entrypoint references across README/docs/scripts
2. For each conflicting path, classify it as:
   - canonical
   - legacy
   - stale
   - test-only
   - unverified
3. Include the known `api/aurora_api.py` vs root `aurora_api.py` discrepancy
4. Link each ledger entry to the file that should be treated as canonical
5. Record follow-on edit targets for the docs that should be updated after the ledger is accepted

## Acceptance Criteria

- [ ] A committed ledger lists conflicting runtime/documentation paths
- [ ] Each entry has an explicit status label
- [ ] Each entry identifies the canonical replacement path when known
- [ ] The `aurora_api.py` path conflict is documented explicitly
- [ ] No historical references are silently deleted without classification

## Evidence

- Root control-plane discovery report: path drift and stale snapshots
- Nested workflow investigation: `api/aurora_api.py` is canonical; root `aurora_api.py` references are legacy/doc artifacts
```

## Issue 3

Title:
- `docs: decide and publish platform-wide multi-service API catalog governance`

Why this is not a duplicate:
- `#380` is about implementation-side CloudHub / MCP / HR integration fragmentation
- this issue is about the catalog and governance layer: what counts as canonical API surface inventory and how multi-service routes are represented
- no open issue directly covers the decision to replace monolith-only API cataloging with a platform-wide catalog model

Suggested body:

```md
## Summary

Decide whether the canonical API catalog for `aurora-cloudbank-symbolic` should remain monolith-only or expand into a platform-wide multi-service catalog, then publish that decision and the initial inventory structure.

## Problem

The control-plane discovery report identifies a catalog-governance gap:

- the existing API catalog source is monolith-scoped
- at least one real service surface is not represented there
- the nested retrospective independently reports that there is no single source listing all active endpoints

This prevents operators and maintainers from answering basic questions such as:

- which surfaces are canonical API surfaces
- which routes are active but not cataloged
- whether monitoring and `hr_system` surfaces are part of the canonical inventory or still pending integration

## Scope

Governance and inventory structure only. Do not use this issue to implement missing routers or merge service code.

## Tasks

1. Decide whether the canonical API catalog is:
   - monolith-only
   - multi-service
   - split by service with a top-level registry
2. Define the minimum metadata required for each cataloged surface:
   - owner
   - mount path
   - entrypoint
   - status (`active`, `pending integration`, `legacy`, `unverified`)
3. Publish the initial inventory for current known surfaces
4. Record how monitoring and `hr_system` surfaces should appear in the catalog even if implementation integration remains incomplete
5. Commit the governance note and initial catalog artifact

## Acceptance Criteria

- [ ] A committed document declares the canonical API catalog model
- [ ] The model covers more than the monolith surface alone or explicitly justifies remaining monolith-only
- [ ] Initial inventory includes known non-monolith surfaces with status labels
- [ ] Monitoring and `hr_system` surfaces are accounted for explicitly
- [ ] Catalog governance is separated from implementation integration work

## Evidence

- Root control-plane discovery report: monolith-only cataloging is insufficient
- Nested retrospective: no single source listing all 125+ endpoints; monitoring and `hr_system` surfaces are incomplete or external to the main API path
```

## Deferred From This Packet

These did not clear the evidence bar for standalone issue creation in this pass:

- fleet bidirectional sync as a standalone GitHub issue
  - reason: strongest source is lower-authority imported analysis, not a corroborated control-plane artifact
- standalone issue for `mesh_api.js` production mount
  - reason: absorbed into Issue 1 to avoid overlap
- standalone issue for `EnhancedApiBridge` `relayMessage(...)` contract gap
  - reason: absorbed into Issue 1 to avoid overlap

## Publication Status

Live issues created from this packet:

- `#634` `docs: publish canonical runtime topology and L3 communications authority map`
- `#635` `docs: build stale-docs and path-drift ledger for runtime and operator entrypoints`
- `#636` `docs: decide and publish platform-wide multi-service API catalog governance`

Auth note:

- inside the local sandbox, `gh auth status` reported the active token as invalid
- outside the sandbox, `gh auth status` succeeded using the keyring-backed `AUo959` login and the issues were created successfully

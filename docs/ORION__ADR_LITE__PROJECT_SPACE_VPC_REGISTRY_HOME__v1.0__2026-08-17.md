---
title: Project Space VPC Registry Home — Directory Main
doc_type: adr_lite
status: accepted_by_owner_in_session
version: 1.0
date: 2026-08-17
owner_repo: AUo959/Aurora_ORIONCORE_Directory_Main
authoring_mode: evidence_grounded
vpc_refs:
  - ORION.VPC.GOVERNANCE.0001
  - ORION.VPC.CONTINUITY.0001
---

# ADR-Lite: Project Space VPC Registry Home — Directory Main

## Context

The ORION Architectural Intake and Promotion Framework defines the Validated
Project Conclusion (VPC) as the smallest promotable unit for moving bounded
project-space conclusions into authoritative Aurora surfaces. The starter
registry left the canonical home of the cross-platform VPC registry unresolved.

The framework routes cross-repository workspace policy to
`AUo959/Aurora_ORIONCORE_Directory_Main`. At the adoption baseline inspected for
this decision, that repository identifies itself as the Aurora workspace control
plane and already owns machine-readable catalogs, schemas, contracts, workspace
policy, verification tooling, and cross-repository boundaries.

## Decision

`AUo959/Aurora_ORIONCORE_Directory_Main` is the authoritative home for the
**cross-platform VPC process registry and its validation schema**.

This is a routing and governance decision. It does **not** make Directory Main a
new canon database and it does not transfer truth authority away from CanonRec,
QGIA, simulation repositories, or other bounded target authorities.

The adopted surfaces are:

- `catalog/orion_vpc_registry.json` — cross-platform VPC process registry;
- `catalog/schemas/orion_vpc.schema.json` — validation contract for the registry;
- `tests/test_orion_vpc_registry.py` — repository-local acceptance checks;
- the three July 27 Project Space source documents under `docs/` as provenance;
- this ADR as the authority record for the registry-home decision.

## Authority boundary

VPC `status` and `authority_class` remain separate dimensions.

- VPC `status` records movement through the Project Space promotion process.
- `authority_class` records the authority already established by the relevant
  target surface.
- The VPC registry may **record** `CANON` or `IMPLEMENTED`; it may not confer
  either class by itself.
- A change to `authority_class: CANON` or `authority_class: IMPLEMENTED` requires
  evidence from the target authority, such as a pinned commit, release, or
  canonical registry record.
- `PROMOTED` requires immutable promotion evidence and a non-null owner and
  promotion target.

This preserves the framework rule that process status does not itself imply
truth.

## Seed-record normalization

The July 27 starter registry contains one status-model inconsistency:
`ORION.VPC.GOVERNANCE.0002` uses `status: IMPLEMENTED`, while the framework's
status model does not contain `IMPLEMENTED`; `IMPLEMENTED` belongs to the
starter registry's `authority_class` vocabulary.

The machine-readable registry therefore normalizes only that field to
`status: ACCEPTED` while preserving `authority_class: IMPLEMENTED`, the original
statement, evidence pointers, acceptance criteria, target, and ownership. This
normalization does not claim a new promotion event. The record is not marked
`PROMOTED` because its existing promotion evidence is not an immutable repository
or release identifier.

## Source-document handling

The three July 27 source documents are stored verbatim. Their embedded document
statuses remain `Workshop baseline` or `Working registry` exactly as authored.
This ADR is the repository adoption decision; the source documents are not
silently rewritten to claim authority they did not originally possess.

## Alternatives considered

### Keep the registry only in the Project Space bundle

Rejected as the long-term home. The framework itself calls for mature records to
move into target repositories, and a repository-neutral bundle cannot provide a
shared repository event, review history, or validation surface for cross-repo
workspace policy.

### Put the registry in CanonRec

Rejected. VPCs include architecture, documentation, implementation tasks,
research questions, and governance mutations. Making CanonRec the VPC registry
home would blur process governance with canon authority.

### Let every target repository keep its own VPC registry

Rejected. The framework explicitly warns against accidental SSOT multiplication.
Target repositories may receive promoted artifacts and backlinks, but the
cross-platform process registry remains singular.

## Consequences

- Project Space gains a durable backlink target without becoming a source-control
  substitute.
- Repository changes can cite stable VPC identifiers.
- Cross-platform promotion state is queryable without treating that state as
  canonical truth.
- Future GitHub issue or ADR automation has a single schema to consume.
- The unresolved default-promotion-target and conversation-citation-grammar
  questions remain unresolved; this ADR does not decide them.

## Evidence

Project Space inputs:

- `ORION_PROJECTSPACE__FRAMEWORK__ARCHITECTURAL_INTAKE_AND_PROMOTION__v1.0__2026-07-27.md`
- `ORION_PROJECTSPACE__REGISTRY__DECISIONS_AND_KNOWLEDGE_STARTER__v1.0__2026-07-27.md`
- `ORION_PROJECTSPACE__CHARTER__CROSS_PLATFORM_ROLE__v1.0__2026-07-27.md`

Repository evidence at decision time:

- `AUo959/Aurora_ORIONCORE_Directory_Main@24595475be90a350c870acb38d4c6308b81bf092`
- `README.md` at that ref identifies the repository as the workspace control plane.
- `catalog/schemas/` already contains versioned JSON Schema contracts.
- `.github/pull_request_template.md` already requires authority/evidence and
  explicit repository boundaries.

## Acceptance

Accepted by explicit owner direction in the ORION Project Space session on
2026-08-17. Promotion into `main` remains subject to repository review and merge.

# ORION Architectural Intake and Promotion Framework

**Document status:** Workshop baseline  
**Version:** 1.0  
**Date:** 2026-07-27  

## 1. Objective

Create a dependable bridge from project-space reasoning to authoritative Aurora surfaces without losing provenance, layer boundaries, uncertainty, or implementation accountability.

## 2. Promotion unit

The smallest promotable unit is a **Validated Project Conclusion (VPC)**. A VPC is not an entire conversation. It is one bounded claim, decision, specification, or work item with enough context to be independently reviewed.

Each VPC must include:

- stable identifier;
- title and concise statement;
- authority class;
- source pointers;
- affected layers;
- affected repositories or project surfaces;
- dependencies and conflicts;
- confidence and unresolved questions;
- acceptance criteria;
- promotion target;
- and current status.

## 3. Promotion pipeline

### Stage 0 — Intake

Capture the candidate without treating it as trusted.

**Output:** intake record.

### Stage 1 — Classification

Determine whether the candidate is:

- observation;
- design proposal;
- architectural decision;
- canon assertion;
- implementation task;
- governance mutation;
- documentation correction;
- or unresolved research question.

**Gate:** ambiguous authority must remain explicit.

### Stage 2 — Evidence binding

Attach direct pointers to conversation excerpts, local artifacts, repository files, commits, issues, tests, or simulation receipts.

**Gate:** claims about an inspected artifact require a specific path or immutable identifier.

### Stage 3 — Layer and conflict analysis

Identify L1/L2/L3 impact, existing SSOT candidates, contradictory decisions, and possible semantic drift.

**Gate:** no silent layer overwrite.

### Stage 4 — Target routing

Choose the canonical destination by function, not convenience.

| Candidate type | Typical destination |
|---|---|
| Runtime implementation | Relevant code repository |
| Cross-repository workspace policy | `Aurora_ORIONCORE_Directory_Main` |
| Canonical knowledge record | QGIA spine/library or designated canon registry |
| Simulation-specific mechanics | Simulation repository or module |
| Architectural decision | ADR registry near the governing implementation |
| Project-space operating rule | ORION governance bundle |
| Unresolved work | Issue, promotion queue, or research ledger |

### Stage 5 — Packaging

Create the target-form artifact: ADR, specification, canon record, issue body, migration note, patch plan, or code change.

**Gate:** preserve the VPC identifier and source lineage.

### Stage 6 — Review and acceptance

Review for factual grounding, coherence, layer integrity, ethics, technical feasibility, and target-owner acceptance.

**Gate:** acceptance must be recorded by an explicit decision or repository event.

### Stage 7 — Promotion

Commit, merge, publish, or register the artifact in its authoritative location.

**Gate:** assign immutable promotion evidence such as commit SHA, release identifier, or registry record.

### Stage 8 — Backlink and closure

Update the project-space registry with promotion evidence, superseded records, and remaining follow-up work.

## 4. Status model

- `CAPTURED`
- `CLASSIFIED`
- `EVIDENCE_BOUND`
- `CONFLICT_REVIEW`
- `TARGETED`
- `PACKAGED`
- `ACCEPTED`
- `PROMOTED`
- `SUPERSEDED`
- `BLOCKED`
- `REJECTED`

Statuses describe process state, not truth by themselves.

## 5. Promotion safeguards

### 5.1 No conversation dumping

Raw conversations may be archived, but canonical targets should receive bounded conclusions and necessary provenance—not unfiltered transcripts.

### 5.2 No invented certainty

Unresolved interpretation remains visible. Promotion packages may contain assumptions, but they must be labeled and assigned a verification path.

### 5.3 No accidental SSOT multiplication

When multiple candidate registries or specifications exist, choose one deterministically and document the selection with an ADR-lite record.

### 5.4 No undocumented semantic translation

When a symbolic, ethical, or narrative concept becomes code, the translation must state what was preserved, operationalized, deferred, or lost.

### 5.5 No promotion without ownership

Every target must have an accountable maintainer, repository, or governance authority.

## 6. Required artifact types

### Architecture Decision Record

Use for consequential choices among alternatives.

Minimum fields: context, decision, rationale, alternatives, consequences, evidence, affected surfaces, status.

### Design Specification

Use for components, interfaces, engines, and governance mechanisms.

Minimum fields: purpose, boundaries, inputs, outputs, invariants, failure modes, interoperability, tests, unresolved questions.

### Canon Record

Use for accepted facts about the simulated world or institutional reality.

Minimum fields: assertion, authority, temporal scope, layer, source, dependencies, supersession rule.

### Work Package

Use for implementation-ready tasks.

Minimum fields: target repo, affected paths, acceptance criteria, constraints, tests, rollback, provenance.

### Unresolved Question Record

Use when premature resolution would create drift.

Minimum fields: question, why it matters, known evidence, competing interpretations, next evidence needed, owner.

## 7. Recommended first implementation

Start with a repository-neutral registry under the ORION project-space bundle. Promote only mature records into target repositories. This prevents every repo from inventing a separate intake grammar before the workflow stabilizes.

## 8. Adoption sequence

1. Adopt the VPC schema and status model.
2. Populate the starter registry with existing high-value decisions.
3. Select five historical conclusions and run them through the pipeline.
4. Measure where provenance or ownership is missing.
5. Refine the schema before automating repository writes.
6. Add GitHub issue/ADR generation only after the manual path is dependable.

## Evidence pointers

- `ORION_PROJECT_SPACE_FRONT_DOOR__NAV__v1.7__2026-02-14.md`
- `ORION.ENF.HOOKMAP.0001__v0.1.2__2026-02-14.json`
- `AUo959/Aurora_ORIONCORE_Directory_Main`, `README.md`, blob `843fae8d7dbb130a9d2599faf00609ec85d7ebaf`
- `AUo959/aurora-cloudbank-symbolic`, `README.md`, blob `5d56ee0540a2c0db5cc6ffaabc50ddb92895eea9`

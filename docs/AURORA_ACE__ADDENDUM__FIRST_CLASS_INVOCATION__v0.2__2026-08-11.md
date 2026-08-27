---
title: Aurora Canon Engine First-Class Invocation Addendum
doc_type: normative_addendum
status: owner_directed_draft
version: 0.2.0
date: 2026-08-11
owner_repo: AUo959/Aurora_ORIONCORE_Directory_Main
augments: docs/AURORA_ACE__SPEC__CANON_ENGINE__v0.1__2026-08-10.md
---

# ACE First-Class Invocation Model

## Purpose

ACE is a first-class Aurora product and runtime subsystem. Humans and agents may address ACE directly, while Aurora capabilities may also invoke the same ACE engine during normal work when a resolvable coherence seam is encountered.

Automatic invocation MUST NOT turn ACE into invisible latent capability. Every substantive invocation remains addressable, inspectable, attributable, replayable where its selected capabilities permit replay, and linked to the evidence and tool receipts that produced its determination.

## Core model

ACE has exactly three invocation modes:

1. **interactive** — a human user, operator, or agent deliberately queries ACE;
2. **embedded** — another registered Aurora capability calls ACE as a service inside a larger workflow;
3. **autonomic** — a registered policy or subsystem detects a qualifying coherence seam and invokes ACE without waiting for a new human query.

These are invocation modes, not separate ACE implementations. All three MUST use the same ACE engine, warm capability index, evidence model, semantic answer-contract compiler, determination vocabulary, execution policy, validation gates, and provenance/receipt system.

## First-class addressability invariant

ACE MUST remain directly addressable by humans and agents even when autonomic invocation is enabled. A caller MUST be able to intentionally request resolution, planning, reconciliation, completion, validation, explanation, or replay through a supported ACE interface.

An embedded or autonomic integration MUST NOT create a private ACE-like resolver that bypasses the public ACE contracts.

## Tooling-first invariant

ACE MUST discover, select, compose, and operate registered Aurora capabilities before bounded synthesis.

ACE MUST NOT synthesize around an available eligible specialist merely because free synthesis is faster, easier, or locally plausible. General model synthesis remains limited to the connective and bounded-completion roles already permitted by the ACE specification.

This rule applies equally to canon, runtime, engineering, governance, simulation, and operational questions. A protected or implementation-sensitive field is not categorically outside ACE; ACE is expected to route to the applicable Aurora capability, protocol, approval surface, validator, or implementation agent when such machinery exists.

## Inspectability invariant

Every substantive ACE invocation MUST carry an invocation envelope containing:

- stable invocation ID;
- invocation mode;
- caller identity and caller class;
- parent invocation reference when embedded in a larger ACE/Aurora workflow;
- trigger kind and human-readable reason;
- coherence-seam reference when autonomic;
- trigger-policy reference when autonomic;
- normalized ACE query digest;
- visibility state fixed to `inspectable`.

Automatic invocation MUST NOT remove or suppress field-level provenance, selected-capability evidence, determination receipts, validation findings, blockers, conflicts, or resulting artifacts.

A user or agent SHOULD be able to ask, in effect, “Why did ACE run, what did it call, and why did it determine this?” and receive the recorded chain.

## Autonomic invocation invariant

Autonomic invocation is permitted only when an upstream registered policy or subsystem identifies a qualifying seam and supplies both a seam reference and a trigger-policy reference.

ACE does not silently scan reality and invent work for itself. The invoking subsystem owns seam detection; ACE owns capability composition and determination after invocation.

An autonomic trigger MAY represent, for example:

- an unresolved but required L1 embodiment field;
- a missing upstream state needed by a specialist capability;
- a capability handoff whose output coverage is incomplete;
- an observed conflict between runtime projection and canon evidence;
- a continuity gap that a registered policy marks as resolvable.

A trigger does not pre-authorize side effects or canon materialization. ACE execution and materialization policies remain independently enforced.

## Embedded invocation invariant

Embedded ACE calls MUST identify the calling capability or agent and preserve the parent workflow or invocation reference when available. The caller may request a determination, but it may not replace ACE field provenance with its own attribution.

## Product-surface invariant

ACE is both:

- a named tool people and agents intentionally use; and
- a constitutive subsystem Aurora invokes during coherent operation.

Neither role is subordinate to the other. Direct use and automatic use are two entry paths into the same engine.

Initial product-facing targets remain CLI, MCP, operations API, and agent-to-agent envelopes. Autonomic integrations use the same invocation envelope rather than a hidden internal-only contract.

## Coherence-completion model

A useful operational analogy is a repair/sealing process that follows an advancing structure: ACE encounters an unresolved seam, inspects surrounding evidence, recruits the appropriate specialist machinery, reconciles outputs, validates the completion, records provenance, and closes the seam when policy permits.

The analogy does not grant ACE universal implementation authority. ACE coordinates the tools that own specialized work; it is not a replacement for them.

## Relationship to determination state

Invocation mode MUST NOT decide the canonical status of the answer.

An interactive, embedded, or autonomic call may each result in any ACE determination that is otherwise valid under the active query and execution policies. Autonomic execution therefore cannot promote a result merely because Aurora initiated the call.

## Minimum implementation contract

The first implementation slice MUST provide:

- a schema-validated invocation envelope;
- constructors for interactive, embedded, and autonomic invocation;
- fail-closed validation of autonomic seam and policy references;
- a direct CLI surface for selecting invocation mode;
- preservation of the underlying ACE query unchanged for the shared engine;
- an inspectable invocation sidecar linking successful execution to its ACE determination.

Actual seam detectors and subsystem-specific autonomic hooks remain owned by the subsystems that detect those seams. They integrate through this contract rather than implementing private resolution logic.

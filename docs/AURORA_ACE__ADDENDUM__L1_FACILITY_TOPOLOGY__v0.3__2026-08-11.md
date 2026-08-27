---
title: ACE L1 Facility Topology and Coherence-Seam Integration
doc_type: normative_addendum
status: implementation_candidate
version: 0.3.0
date: 2026-08-11
owner_repo: AUo959/Aurora_ORIONCORE_Directory_Main
parent_spec: docs/AURORA_ACE__SPEC__CANON_ENGINE__v0.1__2026-08-10.md
parent_invocation_addendum: docs/AURORA_ACE__ADDENDUM__FIRST_CLASS_INVOCATION__v0.2__2026-08-11.md
---

# ACE L1 Facility Topology and Coherence-Seam Integration

## 1. Purpose

This addendum defines the first concrete autonomic coherence-seam integration
for the Aurora Canon Engine (ACE): a non-authoritative Orion L1 subsystem may
report a resolvable world-coherence gap, and ACE may compile and resolve that
gap through the same first-class invocation surface used by direct human,
agent, and embedded calls.

The initial seam is:

```text
L1-EMB-MCP-SHUTTLE-BAY:canonical_location
```

The source subsystem is the CloudBank Orion L1 Embodiment Registry. The source
registry already establishes the MCP Security / Shuttle Bay as a real L1
embodiment while leaving its canonical station location unresolved.

## 2. Producer/receiver boundary

CloudBank is a **seam producer**, not an ACE implementation. It MUST NOT import,
embed, or privately reproduce ACE planning or determination logic.

A seam producer MAY emit a structured handoff containing:

- caller identity;
- trigger reason;
- stable seam reference;
- trigger-policy reference;
- subject identity and context;
- requested missing output;
- explicit authority constraints.

OrionCore remains the ACE receiver. It validates the seam, compiles the normal
`ace_query_envelope`, wraps it in the normal `ace_invocation_envelope`, and
routes it through the same ACE resolver facade.

## 3. Autonomic invocation invariant

The CloudBank handoff MUST enter ACE as:

```text
invocation_mode = autonomic
visibility      = inspectable
automatic       = true
trigger.kind    = coherence_seam
```

The invocation MUST retain both `seam_ref` and `trigger_policy_ref`. Automatic
execution MUST NOT remove provenance, receipts, determination status, or the
ability to inspect the capability route.

## 4. Specialist-first facility completion

Facility topology follows the same specialist-first rule as every other ACE
query.

ACE MUST first search the warm registered capability index for an eligible
facility/topology specialist. If an active specialist exists, ACE MUST use it.
ACE MUST NOT synthesize around it.

For the initial MCP location seam, no active registered facility-topology
specialist exists. ACE therefore MAY use bounded connective completion under
`ace.policy.l1.facility-topology-bounded-completion.v1`.

The bounded completion may select only the narrowest location supported by the
combined evidence. It MUST preserve the authority class of every source:
committed L1 canon remains canon; recovered/staging physical-space material
remains a constraint and MUST NOT be silently promoted.

## 5. Precision boundary

The initial facility completion MAY determine a facility-level location such as
a station region or complex when supported by the evidence graph.

It MUST NOT invent unsupported:

- exact deck assignment;
- exact bay number;
- coordinates;
- dimensions;
- occupancy state;
- movement path;
- access-control effect;
- timing or resource effects.

A facility location determination is not a physical simulation step.

## 6. Causality and authority boundary

Resolving a missing topology attribute does **not** activate the embodiment.
The result MUST preserve:

```text
activation_authority        = false
causal_use_permitted        = false
runtime_mutation_allowed    = false
experiment_advance_allowed  = false
```

A seam invocation grants ACE no new CanonRec write authority. If ACE produces a
complete, validated facility binding but lacks materialization authority, the
required result is:

```text
status                 = EXECUTION_BLOCKED
materialization.status = commit_ready
```

The content MUST NOT be downgraded to `STAGING`, `UNKNOWN`, or an owner-value
request merely because the persistence gate remains closed.

## 7. Initial evidence route

The MCP canonical-location slice uses the following evidence classes without
collapsing them:

1. the root Orion L1 embodiment audit contract for the owner-confirmed MCP
   embodiment and its explicit `canonical location` gap;
2. CanonRec `STATION_PURPOSE_DEFINITION.md` for the canonical L1 chassis role;
3. CanonRec physical-space material only as staging topology constraint;
4. the station technical reference only as a reference constraint.

The current evidence supports a non-rotating core/docking-complex level
placement while leaving exact deck and bay geometry unresolved. ACE therefore
must stop at that precision boundary.

## 8. Unsupported seams

The initial policy handles only the MCP `canonical_location` seam. Authority,
consent, provider-binding, quarantine-state-machine, and actor-bound approval
gaps are not silently converted into facility-topology work.

A seam for an unsupported L1 kind or blocker MUST fail closed until an eligible
specialist or an explicit bounded policy is registered.

## 9. Experiment-state invariant

Neither seam production nor ACE facility resolution may start, resume, migrate,
or advance the paused Orion L1 experiment. The integration operates on
coherence metadata and commit-ready canonical artifacts only.

The recovered paused state remains externally governed and unchanged by this
addendum.

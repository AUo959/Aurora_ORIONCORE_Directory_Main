---
title: Aurora Canon Engine Canon Determination Addendum
doc_type: normative_addendum
status: implementation_candidate
version: 0.3.0
date: 2026-08-11
owner_repo: AUo959/Aurora_ORIONCORE_Directory_Main
parent_spec: docs/AURORA_ACE__SPEC__CANON_ENGINE__v0.1__2026-08-10.md
---

# ACE Canon Determination v0.3

## 1. Purpose

This slice makes the remaining read-only ACE terminal states executable:

- `RETRIEVED_CANON`;
- `DERIVED_CANON`;
- `TRUE_CONFLICT`.

Together with the v0.2 materialization work, all six determination states defined
by the ACE contract become executable rather than vocabulary-only states.

This slice does not widen ACE mutation authority. Retrieval, derivation, and
conflict detection are read-only determinations over committed evidence.

## 2. Retrieval-first invariant

ACE MUST determine whether authoritative committed evidence already answers a
request before generation is considered.

For the initial implementation the evidence scope is explicit: the query names a
bounded list of CanonRec JSON records and a dotted claim path. ACE records the
CanonRec commit baseline and SHA-256 of every source it reads.

If one unambiguous canonical value is supported by the scoped evidence, ACE
returns `RETRIEVED_CANON` with field origin `retrieved` and performs no
materialization.

Repeated committed claims with the same semantic value count as corroborating
evidence, not conflict.

## 3. No-record routing

The absence of an accepted authoritative claim is not permission to relabel
STAGING, inference, or reference material as retrieved canon.

When the scoped evidence contains no accepted canonical claim, the read-only
resolver returns `EXECUTION_BLOCKED` with `semantic_coverage_incomplete` and
routes the unresolved field toward the appropriate completion/generation
capability. The existing ACE no-parking rule remains intact; the retrieval
resolver simply does not impersonate the generation system.

## 4. Deterministic derivation

`DERIVED_CANON` is permitted only through an explicitly registered deterministic
rule whose inputs are committed canonical claims.

The initial allowlist contains one deliberately narrow rule:

`sorted_unique_union`

It accepts canonical list-valued claims and returns their deterministic unique
union. The derivation receipt records:

- rule identity;
- every input claim reference;
- exact output;
- output semantic digest.

No free-form synthesis or constitutive simulation is allowed on this path.
Adding a new derivation rule therefore requires an explicit implementation and
test update rather than a prompt-level improvisation.

## 5. True conflict

When two or more authoritative committed scalar claims in the scoped evidence
assert semantically different values and no authorized deterministic derivation
or reconciliation rule applies, ACE MUST return `TRUE_CONFLICT`.

ACE MUST NOT:

- silently choose the newest file;
- choose the first search result;
- average or merge incompatible scalar values;
- downgrade one committed source without authority;
- invoke generation to conceal the contradiction.

The conflict receipt identifies every competing claim and source and states the
minimal reconciliation decision required.

## 6. Tooling-first relationship

The v0.3 resolver is an ACE capability, not a bypass around Aurora tooling.

The first-class invocation facade routes `canon_fact` subjects to registered
CanonRec retrieval/derivation capabilities. Future repository search,
relationship evidence, SHERLOCK/WATSON reconciliation, or specialist canon
retrievers may expand the upstream evidence-gathering stage. When an eligible
specialist exists, ACE MUST use it rather than synthesize around it.

The initial explicit-path scope is intentionally conservative: it proves the
determination semantics without pretending that repository-wide semantic
retrieval has already been implemented.

## 7. Materialization boundary

`RETRIEVED_CANON` and `DERIVED_CANON` require no CanonRec write: they describe
what the existing committed evidence already establishes directly or by an
allowlisted deterministic transformation.

`TRUE_CONFLICT` is non-materializable until the conflict is actually reconciled.

Therefore all three paths perform zero repository mutation.

## 8. Invocation and inspectability

Interactive, embedded, and autonomic calls use the same ACE invocation envelope
and resolver facade. Invocation mode does not alter determination semantics.

Every successful call remains inspectable and records:

- invocation provenance;
- exact query digest;
- repository baselines;
- source paths and hashes;
- capability route;
- field origin;
- derivation or conflict receipt when applicable;
- replay information.

## 9. L1 experiment invariant

Nothing in this addendum may:

- start or resume the Orion L1 experiment;
- advance a simulation tick or station-cycle minute;
- activate an embodiment or provider;
- mutate runtime state;
- convert a canon determination into a physical event.

The paused Orion experiment remains external to this read-only determination
slice.

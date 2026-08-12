---
title: Aurora Canon Engine Character Materialization Addendum
doc_type: normative_addendum
status: implementation_candidate
version: 0.5.0
date: 2026-08-12
owner_repo: AUo959/Aurora_ORIONCORE_Directory_Main
parent_spec: docs/AURORA_ACE__SPEC__CANON_ENGINE__v0.1__2026-08-10.md
---

# ACE Character Materialization v0.5

## 1. Purpose

ACE v0.5 closes the native publication gap for characters that ACE has already established are genuinely new.

The materializer does not generate identity, canon, personality, or authority. It publishes the exact validated outputs of the retrieval-first character pipeline into CanonRec under explicit materialization authority.

The core invariant is:

> A new character enters CanonRec as one complete native artifact set, or no part of that character survives the transaction.

## 2. Preconditions

Native character materialization requires all of the following:

1. the source determination is `EXECUTION_BLOCKED` only because materialization authority is missing;
2. the answer contract is complete;
3. validation status is `pass`;
4. the source determination records `no_prior_record = true`;
5. the query is a constitutive L2 character completion;
6. CanonRec is still at the exact baseline recorded by the determination;
7. the target checkout is clean and on a non-protected feature branch;
8. an explicit `delegated_materialize` or `owner_gated_materialize` authority reference is supplied;
9. the canonical entity directory and flat discovery record are both absent;
10. the packet contains the verified CharForge bundle, naming receipt, candidate entity, and query envelope.

If any precondition fails, ACE must not commit.

## 3. Retrieval-first boundary

v0.5 depends on v0.4 retrieval precedence.

The materializer MUST NOT be used to escape an unresolved identity ambiguity. If a target, flat entity record, or canonical name/alias already exists, publication fails closed and the caller must return to retrieval/reconciliation.

Character revision is intentionally outside this slice. v0.5 produces `GENERATED_CANON`, never `CANON_REVISION`.

## 4. Native CanonRec artifact set

For canonical character ID `<id>`, one successful transaction writes exactly:

- `canon/L2/entities/<id>/capsule/identity.json`
- `canon/L2/entities/<id>/capsule/traits.json`
- `canon/L2/entities/<id>/capsule/knowledge.jsonl`
- `canon/L2/entities/<id>/capsule/cns.yaml`
- `canon/L2/entities/<id>/capsule/state.bin`
- `canon/L2/entities/<id>/capsule/runtime.py`
- `canon/L2/entities/<id>/capsule/manifest.json`
- `canon/L2/entities/<id>/bundle.manifest.json`
- `canon/L2/entities/<id>/BUILD_RECEIPT.json`
- `canon/L2/entities/<id>/naming_receipt.json`
- `canon/L2/entities/characters/<id>.json`

No parallel ACE-only character format is introduced.

## 5. Capsule promotion

The CharForge bundle is the specialist-produced source artifact.

At publication, ACE:

- verifies capsule ID, canonical name, faction, and declared layer against the validated candidate;
- changes capsule certainty from promotion-ready state to `CANON`;
- records `governance_verdict = PROMOTE`;
- adds inspectable ACE materialization provenance;
- rebuilds the capsule manifest after the identity promotion;
- verifies every manifest hash before staging.

The traits, knowledge, CNS policy, state vector, runtime, outer bundle manifest, and CharForge build receipt are otherwise preserved from the verified specialist output.

## 6. Flat entity discovery record

The flat character entity record is mandatory, not optional metadata.

It provides the complete CanonRec discovery/index surface introduced by the character-registry closure work and explicitly bridges back to the native capsule through:

- `capsule_ref`;
- `capsule_id`;
- a binding note;
- the naming receipt/reference;
- ACE query/determination/materialization provenance.

This prevents a canonical capsule from becoming invisible to tools that index `canon/L2/entities/characters/*.json`.

## 7. Atomic Git transaction

All eleven canonical files are staged together and committed once.

The staged path set MUST exactly equal the declared native artifact set. Unexpected staged files abort the transaction.

If any failure occurs after writes begin—including after Git commit creation—the materializer restores CanonRec to the exact entry baseline and removes all newly introduced target artifacts and any false materialized determination sidecar.

The original `EXECUTION_BLOCKED` determination remains in the append-only ledger. A successful canonical determination is a second immutable receipt that supersedes it.

## 8. Determination semantics

Successful native character publication produces:

- `status = GENERATED_CANON`;
- `materialization.status = committed`;
- the real CanonRec commit SHA;
- all eleven exact target paths;
- a materialization transaction digest over the complete artifact set;
- a succeeded `ace.capability.canonrec.materialize.entity` plan step;
- prior-determination lineage;
- target artifact hashes;
- the authority reference that allowed publication.

Publication metadata is not replayable as the same Git commit. The semantic source packet remains the deterministic replay basis.

## 9. Authority and side-effect boundary

Character publication requires explicit authority every time.

The materializer does not:

- decide that a character should exist;
- skip ACE retrieval;
- choose a canonical name independently of NameService;
- fabricate missing capsule files;
- revise an existing character;
- activate L1 providers;
- mutate an Orion runtime;
- INIT, resume, or advance a simulation.

## 10. Orion L1 invariant

This capability makes future discovery-through-observation character completion safer, but it does not alter the paused Orion experiment by itself.

When L1 later encounters a genuinely new person, the intended path is:

`observation -> ACE retrieval -> ambiguity/reconciliation if needed -> specialist-first completion -> validation -> explicit materialization authority -> one atomic CanonRec character commit`

No step may retroactively rewrite already observed L1 history.

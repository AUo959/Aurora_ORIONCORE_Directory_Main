# Aurora Canon Engine — Materialization + Determination Ledger Addendum

**Version:** 0.2.0  
**Date:** 2026-08-11  
**Status:** implementation contract  
**Parent:** `docs/AURORA_ACE__SPEC__CANON_ENGINE__v0.1__2026-08-10.md`

## 1. Purpose

This addendum implements ACE spec sections 6.12 and 6.13 for the first
materializable slice: a validated L1 facility-topology binding produced by the
facility completion path.

The change does **not** widen ACE's epistemic or runtime authority. Generation
still happens before materialization. Materialization only persists a completed,
validated determination through an explicit authority gate.

## 2. Canon-at-commit rule

ACE may emit `GENERATED_CANON` or `CANON_REVISION` only after all of the
following are true:

1. the answer contract is `complete`;
2. validation is `pass`;
3. the packet is already `commit_ready`;
4. every remaining blocker is specifically
   `materialization_authority_missing`;
5. a non-empty delegated or owner-gated authority reference is supplied;
6. the CanonRec checkout still matches the determination's recorded CanonRec
   baseline;
7. the target worktree is clean and on a non-protected feature branch;
8. only the declared canonical target is written;
9. a real Git commit is created and its full SHA is recorded in the new
   determination receipt.

If any condition fails, the prior `EXECUTION_BLOCKED` receipt remains valid and
no canonical determination is emitted.

## 3. Initial materialization scope

The v0.2 materializer supports only:

- target repository: `CanonRec`;
- packet type: `ace_l1_facility_binding_candidate`;
- target namespace: `canon/L1/station/facility_bindings/`;
- canonical target record type: `l1_facility_binding`.

Character materialization is intentionally **not** generalized here. Character
packets contain a multi-artifact entity/capsule structure and require their own
native CanonRec serializer rather than reusing the facility writer.

## 4. Facility canonical representation

A materialized facility binding contains:

- stable `subject_ref`;
- component and L1 kind;
- canonical facility-level location;
- explicit location scope;
- `certainty: CANON`;
- `causal_use_permitted: false`;
- `activation_authority: false`;
- `exact_geometry_authorized: false`;
- source references;
- ACE query, determination, generation-policy, materializer-version, and
  materialization-authority provenance.

The materializer rejects any candidate that attempts to flip the three safety
flags above. A topology commit therefore cannot activate an embodiment, advance
the experiment, or manufacture exact deck/bay/coordinate geometry.

## 5. Transaction semantics

Materialization uses an optimistic compare-and-swap boundary against the
CanonRec commit recorded in the source determination.

The transaction requires a clean feature-branch worktree. On failure after a
write begins, the materializer resets the target checkout to the exact baseline
commit recorded at entry. The pre-materialization determination is not changed.

The successful materialization receipt records:

- baseline target digest;
- result target digest;
- canonical target path;
- Git commit SHA;
- authority mode and authority reference;
- materializer run ID;
- observed side effects;
- prior determination digest.

## 6. Determination lineage

Materialization never rewrites the source determination.

The source receipt remains:

- `status: EXECUTION_BLOCKED`;
- `materialization.status: commit_ready`;
- complete and validation-clean.

After a successful commit, ACE emits a **new** determination ID whose
`answer.supersedes_determination_refs` includes the source determination. The
new receipt becomes:

- `GENERATED_CANON` when the canonical target did not exist at the recorded
  baseline;
- `CANON_REVISION` when the target already existed and is revised.

This preserves the distinction between "the answer was complete but persistence
was unauthorized" and "the answer is now committed canon."

## 7. Append-only ledger

The initial ledger is an immutable receipt directory at
`reports/ace/determinations/` by default. Each determination ID maps to exactly
one JSON file.

Rules:

- re-appending byte/semantic-equivalent content is idempotent;
- reusing a determination ID for different content is rejected;
- later determinations supersede earlier ones by reference rather than deletion;
- no mutable summary index is required for correctness.

The query surface scans receipts and supports the dimensions required by ACE
section 6.13:

- subject;
- query ID;
- capability ID;
- tool run ID;
- canonical target;
- commit SHA.

## 8. Authority boundary

Two execution modes may authorize this materializer:

- `delegated_materialize`;
- `owner_gated_materialize`.

Both require an inspectable `authority_ref`. The materializer does not infer
permission from the fact that a packet is valid. Validity and mutation authority
remain separate concerns.

The CLI also refuses `main` and `master`. Materialization is committed on a
feature branch so normal repository review/publication workflow remains intact.

## 9. Current determination reachability

With this slice ACE has executable paths to:

- `EXECUTION_BLOCKED`;
- `GENERATED_CANON`;
- `CANON_REVISION`.

`RETRIEVED_CANON`, `DERIVED_CANON`, and `TRUE_CONFLICT` remain defined by the
parent specification but are not yet implemented as executable terminal paths.

## 10. L1 experiment boundary

Nothing in this addendum authorizes:

- runtime mutation;
- provider activation;
- station-cycle advancement;
- simulation-tick advancement;
- experiment resume;
- actor-bound approval substitution.

Materializing a facility location is a canonical coherence action only.

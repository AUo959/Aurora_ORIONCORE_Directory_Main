---
title: Aurora Canon Engine Character Retrieval Addendum
doc_type: normative_addendum
status: implementation_candidate
version: 0.4.0
date: 2026-08-11
owner_repo: AUo959/Aurora_ORIONCORE_Directory_Main
parent_spec: docs/AURORA_ACE__SPEC__CANON_ENGINE__v0.1__2026-08-10.md
---

# ACE Character Retrieval v0.4

## 1. Purpose

ACE MUST resolve plausible existing canonical characters before invoking identity allocation, NameService, CharForge, or any constitutive character-generation path.

The v0.4 slice adds deterministic existing-character retrieval and relation-evidence enrichment over committed CanonRec character capsules. Its purpose is not merely faster lookup. It prevents duplicate identities and preserves continuity when a simulation or human query encounters a person who may already exist in canon.

## 2. Retrieval precedence

Character processing follows this precedence:

1. inspect committed CanonRec character identities;
2. evaluate direct identity anchors;
3. enrich candidate matching with committed relation evidence;
4. return an existing canonical referent when uniquely established;
5. block when a plausible existing referent remains ambiguous;
6. only when retrieval establishes no plausible prior referent and the caller has declared the person `confirmed_unrecorded`, continue into the normal specialist-first generation path.

Generation MUST NOT be used as a shortcut around unresolved retrieval.

## 3. Initial canonical retrieval surface

The initial deterministic index uses the flat CanonRec character entity registry as its primary discovery surface:

`canon/L2/entities/characters/*.json`

When an entity record carries a `capsule_ref` / `capsule_id`, ACE follows that explicit bridge into `canon/L2/entities/*/capsule/identity.json` and uses the capsule as richer identity evidence. Capsule-only canonical characters remain a compatibility fallback so older recovered canon is not omitted while the entity registry is normalized.

An eligible character record contributes, when present:

- canonical ID;
- canonical name;
- aliases;
- role;
- faction;
- status;
- location-binding type, target, and basis;
- exact source path and SHA-256.

Supporting `traits.json` and `knowledge.jsonl` artifacts are returned when present after identity resolution. They are not prerequisites for proving identity.

Only accepted canonical certainty is indexed for identity resolution in this slice.

## 4. Direct identity anchors

The strongest direct anchor is an explicit canonical ID.

Canonical name and aliases are also identity anchors after normalization. Exact ID match takes precedence over name/alias matching.

A unique direct name/alias match may resolve immediately. Multiple direct name/alias matches require relation enrichment before ACE may select a referent.

## 5. Relation-evidence enrichment

The initial relation enricher evaluates committed structured relations available on the identity record against caller context:

- role;
- faction;
- location reference;
- location type.

Relation evidence is used to disambiguate an already anchored identity candidate. For same-name/alias collisions, a candidate may be selected only when it has a strictly greater, non-zero committed relation-match score than every competing direct candidate.

A tie remains unresolved.

Future relation specialists may add explicit interpersonal, organizational, mission, event, temporal, or observation lineage. Those additions must preserve the same provenance and fail-closed semantics.

## 6. Ambiguity is not canonical conflict

Referent ambiguity and `TRUE_CONFLICT` are different conditions.

Two canonical characters may legitimately share a name or alias. That is not evidence that canon contradicts itself.

Therefore:

- unresolved same-name/alias candidates produce `EXECUTION_BLOCKED`;
- the receipt states that semantic coverage is incomplete because the referent is ambiguous;
- ACE identifies all plausible candidates and the additional evidence required;
- ACE does not emit `TRUE_CONFLICT` unless the same established subject is backed by mutually incompatible authoritative claims;
- ACE does not generate a third character to escape the ambiguity.

## 7. Relation-only evidence

Relation similarity alone MUST NOT become silent identity equivalence.

If no ID/name/alias anchor is present but role, faction, and location relations strongly overlap an existing canonical character, ACE treats that character as a `possible existing referent` and blocks generation pending stronger identity or reconciliation evidence.

This conservative barrier exists specifically to protect continuity in discovery-through-observation simulations, where an observed person may initially be known by function or location rather than name.

## 8. No-record behavior

An explicit lookup for a named or identified person that finds no canonical record returns a read-only `EXECUTION_BLOCKED` determination. It does not silently manufacture a different person.

A caller that already knows the referent is genuinely new should declare `existence_status = confirmed_unrecorded`. If the retrieval preflight finds no plausible existing candidate, ACE then continues into the existing character-completion pipeline.

This preserves the no-parking rule without collapsing retrieval and generation into the same operation.

## 9. Shared invocation surface

Character retrieval is not a separate product or hidden preprocessor.

Interactive, embedded, and autonomic invocations continue through the same ACE invocation envelope. The normalized character compiler performs retrieval preflight before generation, and the common invocation resolver dispatches a character `retrieve` query to the retrieval engine while character `complete` queries continue to the existing generation engine.

Automatic retrieval remains inspectable.

## 10. Side-effect boundary

Existing-character retrieval and relation enrichment are read-only.

They MUST NOT:

- reserve or generate a name;
- invoke CharForge;
- allocate a new canonical ID;
- write or revise CanonRec;
- materialize a character capsule;
- activate an L1 provider;
- mutate runtime state;
- advance a simulation.

## 11. Provenance

A successful existing-character determination records:

- registered repository baselines;
- character-index digest;
- identity source path and SHA-256;
- relation-match receipt;
- supporting traits/knowledge sources and hashes where present;
- selected and rejected specialist capabilities;
- replay information;
- zero observed side effects.

Blocked ambiguity determinations preserve the same evidence surface and remain schema-valid ACE determination receipts.

## 12. Orion L1 invariant

This slice is infrastructure for future L1 observation continuity but does not change the paused Orion experiment.

No operation in this addendum may INIT, resume, advance, or retroactively alter an L1 run. When the L1 runtime later encounters an apparently new person, the expected behavior is to invoke ACE retrieval before character generation, not to rewrite already-observed history.

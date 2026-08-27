---
title: Aurora Canon Engine Capability Manifest Discovery Addendum
doc_type: normative_addendum
status: implementation_candidate
version: 0.6.0
date: 2026-08-12
owner_repo: AUo959/Aurora_ORIONCORE_Directory_Main
parent_spec: docs/AURORA_ACE__SPEC__CANON_ENGINE__v0.1__2026-08-10.md
---

# ACE Capability Manifest Discovery v0.6

## 1. Purpose

ACE v0.6 replaces the root control plane's private hardcoded capability list and subject-type invocation switch with validated, committed capability discovery.

The capability schema already existed before this slice. v0.6 makes that schema operational rather than introducing a second registration language.

The intended path is:

`committed manifest -> schema validation -> deterministic discovery -> capability index -> allowlisted runtime binding -> shared ACE invocation`

## 2. Declarative discovery boundary

A capability manifest is metadata, not executable code.

A manifest may declare the tool owner, source path, descriptive entrypoint, domain, execution model, authority, trust, freshness, and composition metadata. It may not cause ACE to dynamically import or execute a named entrypoint.

Executable invocation remains behind a small explicit code allowlist. A valid manifest whose capability ID has no registered runtime binding fails closed.

This prevents catalog mutation from becoming arbitrary-code execution.

## 3. Manifest catalog

Capability records live under:

`catalog/ace/capability_manifests/`

Records are JSONL objects that each validate independently against:

`catalog/schemas/aurora_ace_capability_manifest.schema.json`

Discovery enumerates all `*.jsonl` shards, validates every nonblank record, rejects duplicate capability IDs, and sorts the resulting records by capability ID. Physical file order therefore does not alter the discovered capability universe.

## 4. Trust and integrity

Every manifest carries `trust.manifest_sha256`.

The digest is SHA-256 over canonical sorted compact UTF-8 JSON after replacing the digest field itself with 64 zeroes. This avoids self-reference while making every other field integrity-sensitive.

Discovery fails closed on a digest mismatch.

For a selected executable route, ACE additionally requires:

- `trust.allowlisted = true`;
- a registered repository owner;
- an existing declared source path;
- a matching registered repository head when `freshness.current_head_required = true`.

Root-repository manifests cannot require their own current commit SHA because the manifest is part of the commit being identified. Their committed source and manifest digest provide the local integrity boundary; nested repository capabilities can and do pin registered external heads.

## 5. Invocation routing

ACE v0.6 registers four invocation resolver capabilities:

- `ace.capability.invoke.character.retrieve`;
- `ace.capability.invoke.character.complete`;
- `ace.capability.invoke.facility`;
- `ace.capability.invoke.canon_fact`.

Selection requires an active, allowlisted manifest carrying the `invocation_resolver` tag and `resolve_query` operation. Entity type must match. Exact `query_kind:<kind>` matches outrank `query_kind:*`; selection priority then orders candidates. A tie at the best rank is an error rather than an implicit choice.

After discovery, the selected capability ID is resolved through the explicit runtime binding allowlist in `tools/ace/invocation.py`.

## 6. v0.5 materialization correction

The previous hardcoded warm index still described `ace.capability.canonrec.materialize.entity` as blocked because that descriptor predated v0.5.

v0.6 corrects the description to the executable truth established by v0.5:

- lifecycle: active;
- native owner: `tools/ace/character_materialize.py`;
- entrypoint: `materialize_character_packet`;
- entity scope: character only;
- mutation model: repository mutation;
- transaction required: true;
- supported authority modes: delegated or owner-gated materialization.

This is not generic entity publication authority. It is the atomic new-character publication surface already validated in v0.5.

## 7. Compatibility

The character, facility, and canonical-fact invocation facades remain unchanged for callers. Existing ACE query and invocation envelopes are preserved.

ACE v0.5 character transaction logic is not modified by this slice. Retrieval-first identity handling, specialist-first generation, validation, explicit authority, one-commit CanonRec publication, rollback, and immutable determination lineage remain intact.

## 8. MCP boundary

MCP is intentionally outside v0.6.

Capability discovery belongs inside ACE. MCP can later expose the discovered and governed ACE surface as a transport/product interface without becoming ACE's internal registration mechanism.

## 9. Orion invariant

This change performs no provider activation, INIT, resume, simulation step, or L1 state mutation.

Orion remains paused at tick 7 / station-cycle minute 21.

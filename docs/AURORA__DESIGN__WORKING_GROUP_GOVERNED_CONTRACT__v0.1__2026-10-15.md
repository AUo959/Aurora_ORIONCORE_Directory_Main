# Governed working-group review contract v0.1

**Status:** proposed; read-only; pending_review; no canon authority; no runtime activation.

This packet is a review artifact supplementing the root recovery index; it is not a new source of simulation truth, crew records, deployment logic, or approved consent.

## Evidence and authority

- CanonRec owns stable identity/canon authority. The character identity registry in CloudBank is a runtime projection, not independent identity authority. Display surnames and changing assignment IDs are not stable person IDs.
- CloudBank's crew agents API already supports ad hoc collaboration; the collaborative research framework separately covers schematic research coordination. Neither inspected interface alone proves a persisted working-group lifecycle.
- The L1 runtime contract distinguishes Earth-side control-plane interaction, explicit communications, and deterministic simulation advancement.
- Historical working_group_engine.py is recovery provenance, not runnable input or authorized policy.

## Files

- catalog/schemas/aurora_working_group_review_v0_1.schema.json — proposed snapshot/event schema.
- tools/working_group_review_contract.py — pure in-memory hypothetical sequence checking; supplied identity resolver; no writes, network calls, or runtime integration.
- tests/test_working_group_review_contract.py — synthetic fixtures and negative checks.

The snapshot includes opaque ID, purpose, proposed status, version, and member references. Event proposals include ID, actor/member refs, expected/new version and consent/audit references.

**No proof of consent:** nonempty consent_receipt_ref is only a structural prerequisite. It does not establish real approval or human authorization. A production implementation would need a trusted verifier, a named approval policy, atomic append-only history and approval before any state changes.

Run: python3 -m pytest -q tests/test_working_group_review_contract.py

## Open decisions / no-go boundaries

Before a separate CloudBank implementation PR: inspect any overlapping lifecycle, choose authoritative identity resolution, verify authorization receipts, define event permissions/ownership, design collision-safe atomic storage and concurrency/idempotency, seal evidence, and specify rollback plus default-off feature flag.

No Drive ingestion, runtime agent orchestration, CanonRec mutation, L1 advancement, or credential access is in scope. This contract cannot grant new canonical authority.

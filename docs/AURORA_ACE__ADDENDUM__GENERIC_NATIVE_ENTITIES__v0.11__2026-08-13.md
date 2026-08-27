# Aurora ACE v0.11 Addendum — Generic Native L2 Entity Completion

Date: 2026-08-13  
Status: implementation contract

## Purpose

ACE v0.11 expands constitutive completion beyond the early character/facility vertical slices without creating a new ACE entity format. The generic path emits the existing native CanonRec L2 flat-record surface and validates it through the existing Aurora Canon Reconciler.

The execution path is:

`query -> specialist-first routing -> generic fallback -> deterministic native record -> Canon Reconciler validation -> commit-ready packet -> state-bound preview -> explicit/delegated authority -> one CanonRec commit -> canonical determination`

## Entity coverage

The generic path covers the currently canonical non-character L2 kinds: location, ship, fleet, anomaly, megafauna, facility, domain, polity, species, organization, mobile_asset, ship_class, equipment, place, conflict, event, and report.

Characters remain on the richer CharForge transaction and are explicitly rejected by the generic compiler. Existing L1 facility bindings remain on their dedicated materializer. The generic invocation resolver is intentionally lower priority than those specialists so registration cannot flatten native owner surfaces.

## Native validation

Candidates are ordinary CanonRec records rooted at `canon/L2/entities/<entity_id>.json`. The generic engine does not define a second schema. Before publication, the candidate and its canonicalized result must both pass `skills/aurora-canon-reconciler/scripts/validate_entity.py` for the declared L2 entity kind.

Identity is checked against committed CanonRec by entity ID and canonical name/aliases before resolution and again immediately before commit. Collisions fail closed into reconciliation rather than overwrite.

## Determinism and provenance

When a name or entity ID is not supplied, the generic engine chooses deterministic kind-appropriate values from a stable seed and context digest. Every registered generic invocation is wrapped by `generic_entity_runtime.py`, which resolves and injects the exact committed manifest digests for both the generic resolver and materializer before a determination is emitted.

## Publication

Generic publication is new-entity-only. It requires a clean CanonRec feature branch at the determination's exact registered baseline and the same state-bound preview/commit authorization handshake used by ACE v0.8. A successful publication stages exactly one canonical target and creates exactly one CanonRec commit. The original blocked determination and new canonical determination are append-only ledger records. Any failure after mutation begins resets CanonRec to the exact entry baseline and removes false sidecars.

## Authority boundary

Generic capability means broad native entity coverage, not bypass authority. It does not authorize character format replacement, protected-branch writes, identity overwrite, arbitrary repository paths, remote authentication bypass, Orion runtime progression, or provider activation.

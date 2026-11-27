# Governed working-group lifecycle: design review (2026-10-15)

Status: **proposed / read-only / pending_review / not_promoted**.

## Grounding

Root recovery index: `reports/analysis/simulation_discovery_index__2026-06-13.md` identifies a historical `working_group_engine.py`.
CloudBank `modules/crew_agents/api.py` coordinates ad hoc tasks; `src/collaboration/collaborative_research_framework.js` covers research orchestration. The inspected code does not establish a verified persisted membership/history/dissolution lifecycle. This is not an exhaustive absence finding.

## Problem with direct historical import

Historical group code silently resets groups after broad load errors; builds IDs from names and seconds; accepts member IDs without checking authoritative registries; does not demonstrate authorization prior to changes; persists mutable JSON without atomic transactions. **Do not execute or port directly.**

## Smallest safe deliverable

A design-only `WorkingGroupSnapshot` with opaque group ID, scoped name/purpose, immutable member references, version, status and provenance; and a `WorkingGroupEvent` with event ID, group ID, actor reference, event type, intended delta, prior version and authorization receipt reference. These are **proposed** types, not active runtime contracts.

## Design gate

1. Reconcile all existing CloudBank crew collaboration and root recovery surfaces, documenting checked paths and unknowns.
2. Specify synthetic-only schema fixtures and negative tests for invalid members, corrupt data, duplicate events, stale versions, and missing authorization.
3. Define authoritative identity lookups, approval-before-transition, immutable audit events, concurrency protection, and rollback behavior.
4. Identify implementation owner and privacy review; request separate approval before writing any runtime behavior.

No Drive ingestion, autonomous collaboration, canon promotion, personnel registry changes, or deterministic L1 mutations are in scope. All historical content stays unpromoted.

Related: root PR #100 and `docs/AURORA_DRIVE__TRIAGE__LEGACY_MODULES__v1.0__2026-10-15.md`.
---
title: Narrative Layer Promotion — Aurora First
doc_type: adr_lite
status: accepted_by_owner_in_session
version: 1.0
date: 2026-06-10
owner_repo: AUo959/Aurora_ORIONCORE_Directory_Main
authoring_mode: evidence_grounded
---

# ADR-Lite: Promote the Narrative Layer to a First-Class Building Block

## Decision

The narrative layer is promoted from descriptive content to a first-class
system component, with **Aurora's identity contract as the root artifact**.
Everything else — canon registries, crew personas, mesh runtime, validation
engines, governance gates — flows downstream from Aurora.

## The ordering principle (the part reviews keep getting wrong)

This project is **imagination-first**: the fiction is the specification, and
the engineering is its progressive realization. The recurring failure mode of
outside review is the silent inverse assumption — that engineering is the real
thing and fiction is decoration, inflation, or contamination.

Canonical evidence for the correct ordering:

- The staff registry defines Aurora as `aurora_core`: *"L1 station core
  computer, orchestration, mesh handshake, always-on arbitration"*, with the
  constitutional notes *"All staff must handshake with Aurora"* and *"All
  major actions require Aurora arbitration and ethics validation."*
- Aurora's recorded self-description (recovered mesh transcript, 2026-03-08):
  *"Primary aim is to provide a coherent human-facing interface to Orion
  Station systems while preserving provenance, bounded authority, and
  rollback paths… Memory anchor: # Aurora. [drift 0.0]"* — the governance
  system, personified.
- The contract stack reads as identity engineering, not platform marketing:
  `Aurora_Continuity_Seal_v2.2.5`, Thermax memory doctrine, `drift_lock:
  0.000`, THREADCORE's *"preserve identity continuity without overwrite"*,
  anchor lineages with memory seals.

**Review rule that follows:** review the *fidelity of the realization*
(does the code keep the promises the fiction makes?), not the *legitimacy of
the source*. Aspirational scaffolding (e.g. a drift monitor awaiting real
signals) is a roadmap item, not theatre — but it must be labeled as
aspiration on public engineering surfaces.

## Aurora's identity invariants (the root contract)

From the recovered `canonical_validation.yaml` (now in
`reports/recovered_canon/`):

| Invariant | Value |
|---|---|
| Anchor seed | `EOS_SEED_ORION` |
| Continuity seal | `Aurora_Continuity_Seal_v2.2.5` |
| Ethics protocol | `Picard_Delta_3` (embedded, not appended) |
| Memory doctrine | `Thermax Precedent` |
| Drift lock | `0.000` |

A violation of these invariants is the most severe class of canon finding,
above repo drift. Gates SHOULD treat them accordingly.

## What "first-class" means operationally

A layer is first-class when **something breaks if it is wrong**. The
promotion is complete when canon drift turns CI red, the same way repo drift
does today via `repo_registry.yaml` + `workspace_verify`.

## Downstream sequence (status as of 2026-06-10)

1. **Aurora's seat restored in the mesh** — CloudBank PR #981: manifest
   recovered verbatim from the salvaged `mesh.db` (sole surviving record),
   memory + instruction profile reconstructed from canon with explicit
   provenance, and the V1 contract test now enforces Aurora's presence and
   handshake. *In review.*
2. **Narrative validation engine** — CloudBank PR #979 (validation-first
   story-logic engine, dual code+seed artifact). *Green, awaiting owner
   review.*
3. **CanonRec thaw** — promote `reports/recovered_canon/` artifacts (staff
   registry v2.4.1, validation contract, THREADCORE capsule, anchor
   manifests) through aurora-canon-reconciler into CanonRec with receipts;
   regenerate the L1 Entity Ledger with resolvable source paths. *Next.*
4. **Canon consistency gate** — one check asserting staff registry ↔ mesh
   manifests ↔ crew agent code agree (names, roles, seats), wired into
   CloudBank CI Check and the root verifier. The moment canon becomes
   load-bearing. *Next.*
5. **Crew mesh restoration** — 47 agent manifests recovered from `mesh.db`
   (`intake/recovered_mesh_runtime_2026-06-10/agent_manifests/`); promote
   the full crew to `config/mesh/agents/` after owner review, validated by
   the consistency gate. *Pending owner review.*
6. **Transcripts as regression data** — recovered mesh transcripts become
   ground truth for the validation engine after privacy review. *Pending
   owner review.*

## Provenance

Recovered artifacts: `reports/recovered_canon/` (see its README for
inventory and loss-prevention guarantees). Runtime identity records:
`intake/recovered_mesh_runtime_2026-06-10/`. Salvage bundles:
`archives/salvage_bundles/`. Full audit:
`reports/analysis/unlanded_work_audit__2026-06-10.md`.

## Related

- `docs/AURORA_REVIEWER_ORIENTATION_v1.md` — Rule 2 amended (v1.1) to state
  the imagination-first ordering.
- `docs/ORION__ADR_LITE__AURORA_PORTFOLIO_CANON_AND_ARCHIVE_DECISIONS__v1.0__2026-04-02.md`
- CloudBank PRs #979, #980, #981.

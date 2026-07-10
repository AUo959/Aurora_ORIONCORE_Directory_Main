# Narrative Engine — Phase-Two Continuation Plan (post-#1183)

**Date:** 2026-07-10
**Task:** `narrative-promotion-continuation-2026-06`
**Author:** Claude (Cowork), owner-directed — plan/test-spec only, no CloudBank code changes
**Depends on:** merge of CloudBank **PR #1183**
(`codex/narrative-phase2-evidence-2026-07-04`, commit `e7b6cf06`)

## Purpose

The phase-two contract (`reports/analysis/narrative_engine_phase_two_contract__2026-06-14.md`)
defined seven build steps. PR #1183 delivers steps 1–3 (the evidence/state
layer). This document specifies the **remaining steps 4–7** grounded in the
actual API that #1183 lands, so the work is ready to execute the moment the PR
is on `main`. It designs only; it does not mutate CloudBank or CanonRec and does
not promote canon.

## What PR #1183 lands (the foundation to build on)

Verified against `origin/codex/narrative-phase2-evidence-2026-07-04` on 2026-07-10.

New/expanded in `src/aurora/engines/narrative/`:

| Symbol | File | Role |
|---|---|---|
| `NarrativeEvidenceSource`, `NarrativeFact`, `NarrativeEvidenceBundle` | `evidence.py` | Frozen evidence dataclasses (content-addressed) |
| `build_evidence_bundle(...)` | `evidence.py` | Deterministic bundle builder |
| `promotion_safety_for_bundle(bundle)` | `evidence.py` | Per-bundle promotion-safety assessment |
| `stable_receipt_id(payload)` | `evidence.py` | Stable content hash for receipts |
| `StateBuildReceipt` | `evidence.py` | Receipt for a state build |
| `ContinuityVerdictReceipt` | `evidence.py` | Receipt type: `receipt_id`, `state_build_receipt_id`, `task_kind`, `verdict`, `gate_results`, `promotion_safety`, `to_dict()` |
| `build_state_from_evidence(bundle, proposal) -> (CanonicalState, StateBuildReceipt)` | `state_builder.py` | Evidence → canonical state + receipt |

Tests landed: `test_narrative_phase_two_evidence.py` — bundle-hash stability,
mixed key/set canonicalization, authority-tier + provisional-event preservation.

**Key gap:** the `ContinuityVerdictReceipt` *type* exists, but the function that
*produces* it — `next_event_continuity_check()` — does not. That is step 4, the
seam that turns a built state + a proposed event into a gated verdict.

Also note: `TaskKind.NEXT_EVENT_CONTINUITY_CHECK` is already a **supported
phase-1 validation task** (`router.py` `SUPPORTED_TASKS`), so step 4 is mostly
*binding* the evidence→state→validation→receipt→gate chain, not new validation
logic.

## Target pipeline (from the contract, with real symbols)

```text
reports/simulation/<scenario>/sim_raw.json
  → GumasTurnAdapter                         (step 4 dependency; may be a thin shim)
CanonRec station chronicle + root station_state + flight receipts
  → build_evidence_bundle(...)               → NarrativeEvidenceBundle   [#1183]
NarrativeEvidenceBundle + proposed next event
  → build_state_from_evidence(bundle, proposal) → (CanonicalState, StateBuildReceipt)  [#1183]
CanonicalState + proposed event
  → next_event_continuity_check(...)         → ContinuityVerdictReceipt  [STEP 4 — to build]
  → promotion gate: candidate | hold_staging | block_promotion | owner_review_required
  → canon-reconciler packet only if candidate AND owner approves          [STEP 7]
```

## Step 4 — `next_event_continuity_check()` wrapper

Add a narrow, deterministic wrapper in `src/aurora/engines/narrative/` (likely
`validator.py` or a new `continuity.py`).

**Proposed signature**

```python
def next_event_continuity_check(
    state: CanonicalState,
    proposed_event: Mapping[str, Any],
    state_build_receipt: StateBuildReceipt,
    *,
    strictness: Strictness = Strictness.DEFAULT,
    flight_status: Mapping[str, Any] | None = None,
) -> ContinuityVerdictReceipt: ...
```

**Behavior**

1. Reuse `NarrativeValidationEngine.run(...)` with
   `TaskKind.NEXT_EVENT_CONTINUITY_CHECK`, the layer resolver, deterministic
   operators, and the response builder (all phase-1).
2. Map the validation result to the promotion gate:
   - `supported` / `plausible` → `candidate`
   - `possible_with_setup` → `hold_staging`
   - `strained` → `owner_review_required`
   - `contradictory` → `block_promotion`
   - degrade one level when `promotion_safety_for_bundle(...)` flags unbound
     LLM-candidate facts, or when `flight_status` is stale/missing.
3. Populate `gate_results` (per-axis supports/blockers/missing bridges) and
   `promotion_safety` (from `promotion_safety_for_bundle`).
4. Compute `receipt_id` via `stable_receipt_id(...)` over the canonicalized
   payload; carry `state_build_receipt_id` for chain integrity.

**Hard constraints (must produce a blocking verdict if violated)** — from
`config/canonical_validation.yaml` and `config/mesh/memory/aurora.md`: anchor
seed, continuity seal, ethics protocol, drift lock, and the arbitration rule. An
event that bypasses Aurora arbitration cannot pass.

## Step 5 — Test spec

Add to `tests/` (CloudBank). Minimum cases, each asserting the verdict **and**
the mapped gate:

| # | Scenario | Expected |
|---|---|---|
| T1 | A GUMAS/station turn proposal is fed but not yet in `continuity.established_events` | Proposal treated as candidate fact only; not silently promoted to established |
| T2 | Activation + roll-call receipts as evidence | Produce `OPERATIONAL` facts only, never `CANON` |
| T3 | Proposed event bypasses Aurora arbitration | `contradictory` → gate `block_promotion` (hard constraint) |
| T4 | Flight receipts stale or missing (`flight_status`) | Gate lowered to `owner_review_required` or `hold_staging` |
| T5 | LLM candidate fact without source binding | Cannot promote; `promotion_safety` flags it; gate ≤ `hold_staging` |
| T6 | Deterministic replay: same bundle + event twice | Identical `receipt_id` (content-addressed, extends the #1183 hash-stability tests) |

## Step 6 — New flight `narrative-next-event-continuity-check`

Register in `catalog/flight_contract.yaml` (root) with the existing flight
system (14-day cadence, like `narrative-engine-canon-audit`).

- **Exercise:** build an evidence bundle from the current station chronicle
  (`GUMAS_SIM_2.5/CanonRec/canon/L1/station/chronicle/STATION_CHRONICLE.ndjson`),
  feed a simulated next event, run `next_event_continuity_check`, and assert a
  deterministic receipt + expected gate.
- **Output:** write the latest result to
  `reports/automation/flight_log_latest.json` through the existing flight runner.
- **Freshness use:** the flight's own last-run status feeds T4's
  stale/missing-receipt path on subsequent runs.

## Step 7 — Promotion path

- If `ContinuityVerdictReceipt.gate == candidate`, assemble a **canon-reconciler
  packet**: the receipt, the source bundle hash, and the proposed files.
- Route through `aurora-canon-reconciler`.
- **Owner approval remains required before `CANON_PROMOTE`.** No automated
  promotion, ever — the gate produces a *candidate*, not a commit.

## Execution order & boundaries

1. Merge PR #1183 (owner; blocks everything below).
2. Step 4 wrapper → step 5 tests (red/green) → step 6 flight → step 7 packet.
3. Keep the LLM extractor **out** until deterministic bundle hashing,
   source-tier preservation, and gate tests are green (contract's ordering rule).
4. All of steps 4–7 are **CloudBank nested-repo changes** — they land as their
   own CloudBank PR with the repo's CI gates, not via the root control plane.
   This document is the control-plane spec that PR should implement.

## Handoff

When PR #1183 merges, this plan is directly executable. Recommended assignment:
Codex (CloudBank runtime + PR flow), per `platform_capabilities`. The
foundational spec (`docs/ORION__SPEC__NARRATIVE_ENGINE__…v0.1…`) and its
reconciliation map are the canonical references for the state model and verdict
language used above.

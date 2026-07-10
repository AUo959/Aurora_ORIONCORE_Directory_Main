---
title: Narrative Engine Spec — Recovery & Reconciliation Map
doc_type: reconciliation
status: recovered
version: 1.0
date: 2026-07-10
owner_repo: AUo959/Aurora_ORIONCORE_Directory_Main
relates_to:
  - docs/ORION__SPEC__NARRATIVE_ENGINE__PARAMETERS_TO_NARRATIVE_CORE__v0.1__2026-04-12.md
  - docs/ORION__ADR_LITE__NARRATIVE_LAYER_PROMOTION__v1.0__2026-06-10.md
  - reports/analysis/narrative_engine_phase_two_contract__2026-06-14.md
  - reports/recovery/RECOVERY_THREAD.md
active_task: narrative-promotion-continuation-2026-06
---

# Narrative Engine Spec — Recovery & Reconciliation Map

## Why this document exists

The foundational specification for the Aurora narrative engine —
*Parameters to Narrative Engine* (v0.1, 2026-04-12) — existed only as an
untracked, `.gitignore`-excluded loose file at the repository root, even though
its downstream artifacts (the promotion ADR, the phase-two contract, and a
working phase-one implementation in CloudBank) are all committed. The
foundational design was the least durable piece of the stack — the same
loss-risk that removed the P7 prototype's original evidence copy.

This recovery places the spec in the tracked control plane
(`docs/`, alongside the ADR and next to the phase-two contract in
`reports/analysis/`) and maps its sections to their realization status so the
design corpus is coherent and the suspended task
`narrative-promotion-continuation-2026-06` has a stable reference.

## Provenance

| Field | Value |
|---|---|
| Recovered spec | `docs/ORION__SPEC__NARRATIVE_ENGINE__PARAMETERS_TO_NARRATIVE_CORE__v0.1__2026-04-12.md` |
| SHA-256 (byte-identical to the loose original) | `a4aedede0cdd2423eab718025504f5823924e67c96283d781db5d7519044de46` |
| Former location | `narrative_engine_spec_parameters_to_narrative_core_v_0.md` (root loose, gitignored, manifest `planned_move` to intake) |
| Recovery-thread entry | N8 |

The spec body is preserved byte-for-byte; this file is the separate provenance
and reconciliation record (P7 pattern). The manifest `planned_move` entry and
`path_aliases.csv` row for the loose file were reconciled after the loose copy
was removed.

## The design corpus (how the pieces relate)

The narrative layer is governed by the imagination-first ordering from the ADR:
the fiction is the specification and the engineering is its progressive
realization. In that frame the artifacts stack as:

1. **Spec (this recovery)** — the full design: three modes, canonical state
   model, operator library, validation framework, canonical schema v1.
2. **ADR** (`…NARRATIVE_LAYER_PROMOTION…`) — the decision that the narrative
   layer is first-class and gateable, with Aurora's identity contract as root.
3. **Phase-two contract** (`…phase_two_contract__2026-06-14.md`) — the design
   receipt for the next build stage (LLM `state_builder` front end; deterministic
   engine remains the judge; candidate → continuity-check → promotion-gate).
4. **Implementation** — CloudBank
   `src/aurora/engines/narrative/` (`engine.py`, `state_builder.py`,
   `router.py`, `validator.py`, `operators.py`, `layer_resolver.py`,
   `renderer.py`, `types.py`) plus the phase-one behavior seed
   (`seeds/narrative_validation_engine_phase1_module.md`) and tests
   (`tests/test_narrative_engine_canon.py`,
   `tests/test_narrative_validation_engine.py`).

## Reconciliation: spec section → realization status

Status legend: 🟢 built (phase-1) · 🟡 designed (phase-two contract) ·
🔵 recognized-but-unsupported in phase-1 · ⚪ not yet built. Evidence is from
CloudBank nested-repo code read on 2026-07-10.

| Spec section | Status | Evidence |
|---|---|---|
| **Operating Mode B — Validation** | 🟢 built | `router.py` `SUPPORTED_TASKS` = character_action_audit, next_event_continuity_check, historical_plausibility_check; `TaskKind` enum in `types.py` |
| **Canonical State Model** (entities, relations, pressures, constraints, motives, events, knowledge, uncertainty, temporal/continuity) | 🟢 built | `types.py` `CanonicalState` dataclass: entities, relations, pressures, constraints, motives, events, knowledge_states, uncertainties, continuity |
| **Verdict Language** (supported / plausible / possible_with_setup / strained / contradictory) | 🟢 built | `types.py` `Verdict` enum — exact match to the spec's Preferred Verdict Set |
| **Provenance & Status Tags** (source, status) | 🟢 built | record dataclasses carry `source="declared"` and `status` fields |
| **Layer Protocol** (declared / recovered / inferred) | 🟢 built | `layer_resolver.py` |
| **Expansion Operator Library** (derivation/constraint/pressure/agency/event/symbolic/rendering) | 🟡/⚪ partial | deterministic `operators.py` supports validation; expansion-side operators tie to Mode A (unbuilt) |
| **Operating Mode A — Expansion** | 🔵 recognized, unsupported | `TaskKind.EXPANSION` exists and `router.py` maps it, but `_PHASE_ONE_UNSUPPORTED_REASON = "Phase one only supports three validation tasks."` |
| **Operating Mode C — Translation** | 🔵 recognized, unsupported | `TaskKind.TRANSLATION` mapped; same phase-one boundary; `_TRANSLATION_TOKENS` present but gated |
| **Input Handling Model** (intake classification, evidence density, layer detection, extraction) | 🟡 designed | phase-two contract elevates the LLM `state_builder` front end (prose/mixed → canonical state); `state_builder.py` is the hardening target |
| **Validation Framework** (targets, axes) | 🟢 built | `validator.py`; canon audit test flew supported 2026-06-12 (per phase-two contract evidence table) |
| **Canonical Schema V1** (strict field form) | 🟢 largely built | mirrored by `types.py` dataclasses; a field-by-field diff is a recommended follow-up |
| Phase-1 module's declared **unsupported_tasks**: symbolic_fit_validation, world_generation, myth_generation, branch_generation | ⚪ not built | `seeds/narrative_validation_engine_phase1_module.md` `unsupported_tasks` |

## Summary

The **validation half of the engine is real and tested**; the **expansion and
translation halves are specified but deliberately gated off** at the phase-one
boundary, and the **phase-two contract** targets the ingestion/`state_builder`
seam between them. Recovering the spec closes the one durability gap in the
stack: the design that everything else realizes is now versioned alongside the
ADR and phase-two contract.

## Recommended next steps (for the suspended task, not done here)

1. Field-by-field diff of **Canonical Schema V1** against `types.py` to confirm
   the built dataclasses fully cover the spec schema (flag any drift).
2. When phase-two lands `state_builder`, update this map's Input Handling and
   Mode-A/Mode-C rows.
3. Treat the recovered spec as the canonical reference for Expansion/Translation
   build-out; do not let implementation drift silently from it (add a spec-link
   note in the CloudBank engine package README on the next CloudBank pass).

*This is a control-plane reconciliation record. It does not mutate CloudBank or
CanonRec and does not itself promote canon.*

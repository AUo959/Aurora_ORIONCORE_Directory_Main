# MECH-GOV-001 Implementation — Faction Decision Retrieval Model

**Date:** 2026-06-13 | Closes the design→code gap identified in
`l2_lineage_genesis__2026-06-13.md`.

## What was built

`tools/mech_gov_001.py` — the memory-driven faction decision model designed at
the project's genesis (the "Crisis & Compromise" RPG), formalized in the
recovered L2 Mechanic Registry, and never coded until now. Factions choose
actions by combining **current state** with **retrieved episodic memory** of
past betrayals, alliances, and negotiations.

Realizes both canon rules verbatim
(`canon/L2/mechanics/03_galactic_union_mechanics_and_models.md`):
- *"betrayal history raises the odds of future betrayal"* — accumulated hostile
  memory drives `disposition` negative → `escalate`/`betray`/`verify`.
- *"weakness increases the odds of negotiation"* — a militarily weak faction
  under the same threat chooses `negotiate`, not `escalate` (de-escalation).

Companion **MECH-DIP-001** (Diplomatic Trust Decay, `T = T - λ·B + δ·A`) is the
trust-update rule the model reads.

## Substrate and the determinism fix

The episodic-memory layer is a clean port of the recovered 2025
`memory_system.py` (importance-weighted strength, half-life exponential decay,
reinforcement on recall, recency+importance+relevance retrieval). **Correction
over the original:** it used wall-clock `time.time()`, which makes runs
irreproducible. This implementation uses a **logical turn clock**, so a seed +
event log yields a deterministic decision trace — a simulation-fidelity
requirement, and an example of improving on the legacy rather than re-proving it.

## Demonstration (seed 808)

| Situation | Decision |
|---|---|
| Union → Black Hand, no history | `hold` (neutral) |
| Union → Black Hand, after 2 betrayals | `escalate` (disposition −0.87, trust 0.10) |
| Weak Vel-Surak → Black Hand, same betrayal | `negotiate` (weakness favors de-escalation) |
| Union → Armada Nova, after 3 alliance acts | `ally` (disposition +0.73) |

## Governance choice

Built in the **root control plane** (`tools/`, tracked + tested), not the
ungoverned `SIM_ENGINE_OUTPUTS/` engine dir (untracked by git). The recovered
`memory_system.py` reference sits in `SIM_ENGINE_OUTPUTS/recovered_reference/`
for the engine-integration step. Tests: `tests/test_mech_gov_001.py` (6).
Canon registry annotated (CanonRec `a8f50ba`); pinned.

## Next

- **Wire MECH-GOV-001 into `engine_advanced` faction loop** — feed real engine
  events (combat outcomes, treaty breaches) into faction memory and let
  retrieved disposition bias the engine's action selection; re-run the long
  galactic sim and compare stability/risk to the seed-42 baseline (where
  memoryless factions ran away into 4 civil wars).
- MECH-MIL-001 (weighted combat) and the recall-probability model remain
  design-only.

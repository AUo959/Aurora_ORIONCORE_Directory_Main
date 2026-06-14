# Territorial Consequence (MECH-TER-001) — Pillar A begins

**Date:** 2026-06-14 | `tools/mech_gov_001.py` (`TerritorialConsequenceModel`),
`tools/gumas_memory_run.py` (`_writeback_territory`). First mechanic of Pillar A
(emergent, interacting consequence). Built on the engine's **own** economy after
the engine-version audit confirmed `GUMASAdvancedEngine` (Forge v3.0) is current.

## The gap — conflict was a self-contained scalar

Until now a war moved stability and grievance, then ended, and the world was
otherwise unchanged — a war you won and a war you lost left the galaxy the same.
The plan's Pillar A requires **causal depth > 1**: a war's *outcome* must reshape
the world, and that reshaping must change what happens next.

## The mechanic — war costs ground, and lost ground is lost economy

The engine caps each faction's `economic_strength` at its `economic_potential`
(the ceiling it grows toward) but never lowers the ceiling — so economic damage
always heals. MECH-TER-001 makes the damage **stick**:

- A faction's **mature civil wars permanently scar its territory**, scaled by war
  severity (insurgent strength). Half of each loss is **seceded** (gone for good);
  half is **contested** (reclaimable at peace). A faction always keeps a ~45% core.
- The territory still held sets the faction's **economic ceiling**
  (`economic_potential = 1 − total_loss`). A polity that loses a third of its land
  is permanently a third poorer.
- Because galactic **power** (MECH-POW-001) reads economy, the loss propagates:
  war-torn factions become permanently weaker, the balance of power shifts, and
  power politics realigns around the new distribution.

So one war's territorial outcome flows **map → economy → power → everyone's power
politics** for the rest of the run — the causal chain Pillar A is about.

## A/B — Observatory 240-cycle (seeds 42/7/99), DYNAMIC GALAXY — CERTIFIED

| Seed | factions that lost territory | econ-potential spread (off → on) | war-torn power penalty |
|---|---|---|---|
| 42 | 4 | 0.00 → **0.29** | **+0.16** weaker |
| 7  | 4 | 0.00 → **0.12** | **+0.08** weaker |
| 99 | 4 | 0.00 → **0.37** | **+0.10** weaker |

**Without the mechanic, every faction's economic ceiling stays 1.0 (the world is
unmarked by its wars). With it, the ceilings diverge by each faction's war
history**, and the war-torn end measurably weaker in power than the spared — the
chain reaches power, not just a local scalar. The map evolves (4 factions
permanently smaller per run), the economy carries the scars, and the balance of
power moves. The living/dynamic invariants all still hold. The Observatory gates
a `consequences_propagate` verdict (territory lost ∧ economy diverged ≥ 0.05 ∧
war-torn weaker).

Magnitude is moderate by design (12–37% economic loss; min potential ~0.63–0.88)
— a war-torn polity is diminished, not annihilated; calibrated for a coherent
dynamic, not a target. Tests: `tests/test_mech_gov_001.py` (20) +
`tests/test_gumas_consequence_layer.py` (4) +
`tests/test_observatory_240_cycle.py` (14) — 38 pass.

## Status & follow-ups

- **Pillar A begun.** TER-001 already realizes the *map → economy → power* spine
  (much of what ECO-001 would do). Remaining Pillar A: **MECH-ECO-001** (war
  economy / market flux — scarcity then recovery booms; the `tech_economic_
  multipliers` the engine exposes are the hook) and **MECH-CUL-002** (assimilation
  vs local tradition — a cultural cost to *holding* conquered ground).
- **`l2_state` deepening:** territory loss is tracked as a scalar fraction; the
  engine's `l2_state` (locations, logistics_nodes, relations) could make it
  *spatial* — specific provinces/locations seceding — a richer later pass.
- Reintegration of seceded ground ties naturally to the queued **MECH-DIP-005**
  (autonomy/reintegration) from the OSD deep-read.

# Instability Consequence Layer — the lessons-learned to-do

**Date:** 2026-06-13 | `tools/gumas_consequence_layer.py`. Works the residual
items the seed-42 lessons flagged: mechanics that fired every turn but
connected to nothing.

## What was made consequential

| Inert signal (lessons) | Now |
|---|---|
| §2.1 INTELLIGENCE_COMPROMISE — dominant signal, never resolved | **MECH-INT-001** counter-intel response: factions invest in `counter_intel_strength` → compromise self-limits; episodic bounded economic cost |
| §2.4 MASS_CONSCRIPTION — fired, capabilities unchanged | **MECH-MIL-002** conscription → military capacity under active insurgency |
| §2.2 civil-war onset — no dampener | **MECH-REB-002** onset dampener (tunable; off by default) |
| §2.3 STATE_FRAGMENTATION — no split, no effect | **MECH-REB-003** territory loss → economic capacity drag |

## A/B (seeds 42/7/99, 120 turns), all mechanics on

| Seed | stability (base→mem) | risk | active civil wars |
|---|---|---|---|
| 42 | 0.357 → **0.412** | 0.651 → 0.538 | 4 → 0 |
| 7  | 0.359 → **0.398** | 0.633 → 0.551 | 3 → 0 |
| 99 | 0.359 → **0.404** | 0.650 → 0.546 | 4 → 0 |

The consequence layer holds the two-sided stability win (~0.40–0.41) while the
inert signals are now real. Tests: `tests/test_gumas_consequence_layer.py` (4).

## The honest finding — a real coupling, and a calibration discipline

Bisecting (each sub-effect toggled in-process) showed the **intel writeback
alone** drove the behavior: with it off, the run returns to the two-sided
result (0.406, civil wars peak 2). The cause is a coupling in the engine:
`counter_intel_strength` is a **shared lever** — it feeds *both* intel-compromise
resistance *and* the rebellion onset `ci_suppression` term. So an aggressive
counter-intel build-up (to make compromise self-limiting) also **crushes
rebellion onset entirely** — over-suppression that erases conflict, which is
neither realistic (a galaxy with zero civil wars over 120 turns) nor rewarded
by the conflict-relief stability metric (lessons §1.6).

Resolution: MECH-INT-001 is deliberately **gentle** (rate 0.012, ceiling 0.50)
so compromise adapts without flattening conflict. The same over-suppression
appeared with conscription at high mobilization, also dialed back.

**Conclusion (not forced):** completing these signals is a *realism* win, not a
further *stability* win. The stability solution remains the two-sided
MECH-SOC-002/003; consequences that touch suppression levers trade against the
conflict-relief metric, so they are kept light. Full above-threshold stability
(0.480) is still bounded by the remaining non-modelled stability components
(legitimacy depth, population recovery) — a later, separate pass.

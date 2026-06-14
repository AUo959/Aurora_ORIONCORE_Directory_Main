# D9 — Validating the Honest Metric (Is the Galaxy Actually Healthy?)

**Date:** 2026-06-14 | Follows the MECH-REB-004 graft. Answers the question we
raised against our own work: with the honest `true_stability` plateau at
~0.29–0.33, is the galaxy genuinely healthy, or quietly running away — and is the
0.30 collapse floor still the right gate?

## Method

Three checks, mostly over data already generated:
1. **Calibrate collapse honestly.** Measure `true_stability` in a *known*
   collapse — the baseline (no mechanics), which is the original permanent
   civil war — to see what the honest metric reads at real collapse.
2. **Plateau vs runaway.** Run the full pipeline to 400 turns and watch whether
   `true_stability` keeps falling or settles.
3. **Diagnose the swarm.** Decompose insurgencies by phase over time — is the
   minor-insurgency population growing unbounded or reaching steady state?

## Findings

### 1. The stability scalar cannot tell health from collapse

| seed | mode | engine stab | **honest stab** | active civil wars | settlements |
|---|---|---|---|---|---|
| 42 | baseline (collapse) | 0.355 | **0.288** | 4 (pinned) | 0 |
| 42 | full (dynamic) | 0.390 | **0.323** | ~1.1 (fluctuating) | 60 |
| 7 | baseline (collapse) | 0.360 | **0.310** | 3–4 (pinned) | 0 |
| 7 | full (dynamic) | 0.393 | **0.319** | ~2 (fluctuating) | 64 |
| 99 | baseline (collapse) | 0.360 | **0.293** | 4 (pinned) | 0 |
| 99 | full (dynamic) | 0.392 | **0.311** | ~1.6 (fluctuating) | 68 |

**Known collapse reads ~0.29 on the honest metric; the dynamic galaxy reads
~0.31.** They are barely 0.02–0.03 apart. The reason is structural: conflict is
only **10%** of the stability index (0.35 population + 0.30 legitimacy + 0.25
trust + 0.10 conflict). Folding internal war into that 10% term — the right,
honest correction — can only move the scalar by ≤0.10, so it shifts everything
down roughly uniformly and **does not discriminate** a frozen-war galaxy from a
living one.

So `true_stability` is *honest* (it removed the engine's inflation) but not
*diagnostic*. The roundtable was right that the engine over-credited; the deeper
lesson is that **no stability scalar is a good health gate during civil war**,
because civil war barely moves it.

### 2. It plateaus — it is not running away

Full pipeline, 400 turns, `true_stability` by 40-turn era:
- seed 42: `0.61, 0.52, 0.43, 0.35, 0.32, 0.32, 0.29, 0.29, 0.28, 0.30`
- seed 7:  `0.59, 0.51, 0.45, 0.37, 0.34, 0.31, 0.31, 0.29, 0.27, 0.28`

It descends from the calm start to ~0.28–0.30 by turn ~200 and **holds flat
through turn 400.** A stable turbulent attractor, not a slide toward zero.

### 3. The swarm is a bounded steady state

Insurgency population (per-turn means, late game) settles at roughly **2–3
minor (ACTIVE) + 1–2 ESCALATED + ~0.5 CIVIL_WAR**, with continuous settlement
throughput (~0.4/turn). It does not grow without bound — it is a steady churn of
"constant localized unrest somewhere in a large galaxy," which is realistic.

## Conclusion & action

**The galaxy is healthy — but the proof is in the dynamics, not the scalar.**
- It is *not* running away (true_stability plateaus; the swarm is bounded).
- ~0.30 honest stability is *not* "near collapse" in any meaningful sense —
  collapse sits at the same ~0.29, so the scalar simply isn't the right ruler.
- What genuinely separates the dynamic galaxy from collapse is the **conflict
  load and its exits**: the permanent-war baseline pins ~4 civil wars with **0**
  settlements; the dynamic galaxy runs ~1–2 that **resolve** (60–68 settlements,
  cast rotates 13→71/74/76).

**Gate change (shipped):** the Observatory no longer gates collapse on a
stability floor. `not_collapsed` is now `sustained_civil_war_load <
COLLAPSE_CW_REF` (=3.0), where the load is the late-half mean active civil wars
(crest-robust; the baseline sustains ~4). Both stability numbers (engine and
honest) are still reported for transparency — they are diagnostics, not gates.
The D1 honest metric stays in the readout precisely so we never again mistake the
engine's inflated number for health.

This resolves D9. The remaining Phase-0 follow-ups (D2 counter semantics; an
engine-side terminal/removal path for `RESOLVED`) are owner-clearance items and
do not block the dynamic-galaxy program.

Tests: `tests/test_observatory_240_cycle.py` now asserts
`not_collapses_to_pinned_civil_war` on the conflict-load criterion; 28 pass.

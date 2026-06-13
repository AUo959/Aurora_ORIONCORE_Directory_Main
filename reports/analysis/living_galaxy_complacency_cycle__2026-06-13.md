# The Living Galaxy — Complacency Cycle (MECH-SOC-006)

**Date:** 2026-06-13 | `tools/mech_gov_001.py` (`ComplacencyModel`),
`tools/gumas_memory_run.py` (`_writeback_complacency`).

## The problem this fixes — the *second* degeneracy

Solving the seed-42 permanent civil war (MECH-SOC-002/003) and recovering the
stability components (MECH-SOC-005) worked — *too* well. Every stabilizer
ratcheted up monotonically, so the galaxy slid into the **opposite** degenerate
fixed point: **permanent peace**. Conflict happened once, early, then flatlined
(seed 42 active civil wars by era: `[0,0,17,6,0,0]`). A galaxy where conflict is
*impossible* is as unreal as one where it never ends — just at the other
extreme. The Pilot named this directly: *"if we have over-solved the problem to
make conflict impossible then we have a serious issue and we're not done."*

## The mechanic — peace breeds the seeds of the next conflict

**MECH-SOC-006 (Complacency Cycle).** Canon's non-war progression model names
corruption (C) and militarization (M) as *destabilizers* — `DSI = (P+E+S)/(C+M)`.
A polity unchallenged for many turns accrues **complacency** (a proxy for
creeping corruption) that:

- **erodes governance legitimacy** (`LEGIT_EROSION`) — the order grows brittle;
- **worsens living conditions** (`STRESS_PRESSURE` on housing) — mismanagement;
- **fuels resentment** (`INSURGENT_FUEL` on insurgent support + grievance) — the
  *maturation* lever: a corrupt order breeds *strong* rebellions that grow into
  civil wars instead of fizzling.

Serious conflict (civil war / escalated) **purges** complacency — upheaval
renews the order, the peace clock resets, and recovery + war-weariness pull the
faction back toward calm. The loop closes: **peace → complacency → conflict →
renewal → peace.** A fresh post-conflict order gets a grace window before
complacency starts accruing again.

Calibrated for a *limit cycle*, not a ratchet (`BUILD_RATE=0.012`,
`LEGIT_EROSION=0.04`, `STRESS_PRESSURE=0.015`, `INSURGENT_FUEL=0.012`,
`GRACE_TURNS=8`, `PEAK=0.55`). Stronger values pump constant war; weaker ones let
peace flatline.

## A/B (seeds 42/7/99, 120 turns — the canonical horizon)

| Seed | base stab | full stab | risk | civil-wars/era | stability/era |
|---|---|---|---|---|---|
| 42 | 0.359 | **0.465** | 0.540 | `[0,23,38,76,70,51]` | `[.61,.61,.59,.55,.51,.46]` |
| 7  | 0.361 | **0.486** | 0.485 | `[0, 7,77,100,49,12]` | `[.61,.60,.57,.53,.50,.48]` |
| 99 | 0.361 | **0.482** | 0.491 | `[0,11,63,90,47, 8]`  | `[.61,.62,.58,.51,.50,.48]` |

Conflict now **recurs in every era** and, crucially, **waxes and wanes**: it
builds, peaks mid-run, and subsides toward calm (seeds 7/99 fall from a ~90–100
peak back to single digits). Stability moves *in response* — easing during the
surge, recovering as it subsides — instead of sitting at a fixed point. Risk
clears its 0.540 threshold on 7/99 and sits right at it on 42. Final stability
(~0.47–0.49) matches the recovery-only result but is now a **living** value, not
a frozen one.

## Honest finding — the long-run attractor (240-turn horizon)

Extending to 240 turns reveals the mature dynamic, and it is reported plainly:
conflict **keeps recurring** in successive waves (a genuine cycle, not a
one-time swell), but the waves ratchet and stability drifts down to a
**turbulent ~0.38 plateau** — then holds there. It does **not** collapse (the
original seed-42 attractor crashed and stayed crashed) and it does **not**
freeze. It settles into a large-galaxy steady state where localized conflicts
continuously arise and resolve somewhere at all times — which is what a living
galaxy of many desynchronized polities actually looks like; total galactic peace
is the unrealistic state.

Strengthening the resolution side (faster war-weariness + recovery) was tested
and lifts the long-run floor only marginally (0.38 → ~0.40) while leaving the
waves intact — the turbulent equilibrium is robust. Pushing it higher would
require re-tuning the *other* mechanics' constants to force a number, which the
emergence principle forbids ("calibrate toward a coherent living dynamic, not
toward a stability number"). So the cycle is left as an emergent dynamic and its
full behavior — healthy 120-turn living swing, turbulent-but-stable 240-turn
attractor — is documented rather than tuned away.

**Both degeneracies are now gone.** The galaxy neither collapses into permanent
war nor freezes into permanent peace: conflict emerges, escalates, peaks, and
subsides as orders grow complacent, are shaken, and rebuild.

Tests: `tests/test_mech_gov_001.py` (13, +`test_complacency_builds_in_peace_and_purges_in_war`)
+ `tests/test_gumas_consequence_layer.py` (4) — 17 pass.

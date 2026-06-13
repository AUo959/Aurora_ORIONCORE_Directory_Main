# Stability Components — Post-War Recovery (MECH-SOC-005)

**Date:** 2026-06-13 | Addresses the two stability-index components the seed-42
lessons named: population (§1.5) and legitimacy (§1.6).

## The formula and the gap

```
stability = 0.35·avg_population_stability   (largest weight)
          + 0.30·avg_legitimacy
          + 0.25·avg_trust
          + 0.10·(1 − conflict_pressure)
```

The engine only ever *drags* population and legitimacy down (war drag,
per-insurgency) and never restores them — so even after our two-sided fix
resolved the civil wars, these sat near collapse and capped stability at ~0.40.
A component breakdown confirmed it: legitimacy and trust had recovered (~0.53),
but **population stability was floored at 0.258** (contributing only 0.090 of
the needed 0.35-weighted share).

## The fix

**MECH-SOC-005 (Post-War Reconstruction)** — a faction at peace rebuilds
population stability and governance legitimacy toward healthy baselines and
eases its demographic stress drivers (housing, unemployment, food). Gated on
peace: serious conflict halts reconstruction, so it rewards *ending* wars.

A second finding fed back into MECH-SOC-002: population was being held down not
by civil wars (resolved) but by a **swarm of minor insurgencies** — the engine
drags population per-insurgency across *all* phases, and low-level insurgencies
form constantly via onset. So war-weariness was extended to **cede insurgent
territory**, letting weary minor insurgencies reach the engine's SUPPRESSED gate
and stop dragging.

## A/B (seeds 42/7/99, 120 turns)

| Seed | stability (base→full) | risk (base→full) | civil wars |
|---|---|---|---|
| 42 | 0.357 → **0.445** (+0.088) | 0.651 → 0.505 | 4 → 0 |
| 7  | 0.359 → **0.488** (+0.129) | 0.633 → 0.465 | 3 → 0 |
| 99 | 0.359 → **0.471** (+0.113) | 0.650 → 0.480 | 4 → 0 |

**Risk now clears its 0.540 threshold on every seed.** Stability lifts to
~0.45–0.49 and **straddles the 0.480 threshold** — seed 7 crosses; 42 and 99
land just under.

## Honest finding — a real tension, not forced

Stability could be pushed over 0.480 on all seeds by suppressing insurgency
onset harder (fewer insurgencies → less population drag → higher population
component). I did **not** do that, because it surfaces a genuine tension:

> The stability *metric* rewards high population stability, which means *few
> insurgencies*. But realism (and the emergence principle) wants the galaxy to
> have *some* conflict. Over-suppressing onset to clear the metric produces a
> galaxy with zero unrest — as unrealistic as the original permanent civil war,
> just at the other extreme.

So the components are recovered (population and legitimacy heal post-war, which
they never did before), full above-threshold stability is reached on some seeds
and approached on others, and the last sliver is left to emergent variation
rather than tuned away. The seed-42 collapse is solved; the galaxy now has a
complete wound-and-heal cycle instead of a one-way slide.

Tests: `tests/test_mech_gov_001.py` (12) + `tests/test_gumas_consequence_layer.py`
(4). CanonRec `5731c50`.

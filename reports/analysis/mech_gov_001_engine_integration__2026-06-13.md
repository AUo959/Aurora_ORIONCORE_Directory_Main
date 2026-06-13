# MECH-GOV-001 — Engine Integration & A/B Finding

**Date:** 2026-06-13 | `tools/gumas_memory_run.py`

## The loop is live and faithful

The integration closes design→code→engine: each turn the harness harvests the
engine's faction events (treaty breaches → betrayals, conflicts → attacks,
ratified treaties → alliances) into MECH-GOV-001 episodic memory, computes each
faction's memory-driven disposition, and writes it back into the engine's
`trust_scores` (which `engine_base` already consults for treaty-breach and
mediation evaluation). Both canon rules are realized in the trust signal:
betrayal/attack memory hardens trust; a militarily weak faction is nudged
toward cooperation ("weakness increases the odds of negotiation").

**Fidelity check:** the memory-off baseline reproduces the documented seed-42
run almost exactly — final stability **0.357** / risk **0.651** at turn 120
(the `LESSONS_LEARNED` doc records 0.358 / 0.651). The harness drives the
canonical engine correctly.

## A/B result (seed 42, 120 turns)

| Run | final stability | final risk | mean risk | conflicts |
|---|---|---|---|---|
| baseline (memoryless) | 0.357 | 0.651 | 0.570 | 3 |
| memory (MECH-GOV-001) | 0.359 | 0.667 | 0.586 | 3 |
| **delta** | **+0.002** | **+0.016** | **+0.016** | 0 |

Memory harvested over the run: **0 betrayals, 10 attacks, 10 alliances.**

## Honest finding (not forced)

Memory-enriched trust is **near-neutral on macro-stability** in this scenario,
and very slightly *hardening* (factions remember attacks → trust a little less
→ marginally more friction). This is coherent emergent behavior, but it does
not tame the seed-42 runaway — because:

1. **The engine produces no treaty breaches** at seed 42. It forms alliances
   that *hold*; the betrayal-memory rule is correct but unexercised by this
   scenario's event stream. (Not a harvest bug — alliances were harvested from
   the same treaties.)
2. **The instability is internal, not diplomatic.** The seed-42 collapse is
   driven by **insurgencies and civil wars** (the v3 FORGE rebellion module),
   which `trust_scores` does not govern. A faction *diplomacy* memory model,
   however faithful, addresses a different axis.

Per the emergence principle (established detail must not preclude coherent
emergent detail, and outcomes are not scripted), this neutral result is
reported as-is rather than tuned into a false win.

## The real lever (next)

To let memory affect the actual instability, the memory signal must reach the
**rebellion/insurgency dynamics**, not only inter-faction trust: a population's
remembered grievances (repression, broken promises, hardship) should raise
insurgency odds, and remembered relief/autonomy should lower them — the same
MECH-GOV-001 substrate applied to polity↔population rather than faction↔faction.
That is a v3-rebellion-module hook, a larger change than the diplomacy wiring,
and the coherent next step. The diplomacy integration stands as the validated,
faithful foundation.

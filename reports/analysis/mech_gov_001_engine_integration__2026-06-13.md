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

---

## Update — social-dynamics integration (MECH-SOC-001)

Per "include social dynamics across the galaxy," the social layer was promoted
to `canon/L2/social_dynamics/` (DSI, social cohesion, `P_stability=E+T-C`,
public sentiment, non-war progression) and **MECH-SOC-001 (Population Grievance
Memory)** was built and hooked into the **actual instability axis** — the
rebellion module — not just diplomacy.

Mechanism: each turn the harness reads per-faction demographic stress and active
insurgencies, records `hardship`/`repression`/`relief` into population grievance
memory (slow decay, half-life 30 turns), and writes accumulated grievance back
into the **persistent housing-pressure driver** that feeds
`demographic_stress → rebellion onset`. Path-dependent: a population that
suffered carries it forward; relief eases it.

### A/B (seed 42, 120 turns)

| Run | stability | risk | mean risk | insurgencies (peak) |
|---|---|---|---|---|
| baseline | 0.357 | 0.651 | 0.570 | 13 (13) |
| memory (GOV+SOC) | 0.353 | 0.638 | 0.561 | 13 (13) |

Social memory harvested: **304 hardship, 1,211 repression, 967 relief** — the
model is heavily exercised. Risk moved **−0.013** (the first *stabilizing*
movement; diplomacy-only had been +0.016), driven by populations also
remembering relief, not only hardship.

### Honest finding

The grievance hook reaches the real instability axis and is directionally
stabilizing, but the seed-42 collapse is **structurally robust**: 13
insurgencies still form, stability stays ~0.35. The discrete onset events don't
change at honest coupling; only the aggregate risk softens. Coefficients were
**not** tuned to manufacture a larger effect (emergence principle). The
memory mechanics are now real, canon-grounded, tested, and live in the engine —
what they change, and don't, is reported as measured.

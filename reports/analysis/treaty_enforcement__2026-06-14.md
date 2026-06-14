# Treaty Enforcement — Peace That Binds (MECH-DIP-003)

**Date:** 2026-06-14 | `tools/mech_gov_001.py` (`TreatyEnforcementModel`),
`tools/gumas_memory_run.py` (`_writeback_treaties`, accord registration). The
tidy finish to Pillar B (off-ramps).

## What it adds — stakes

MECH-REB-004 + DIP-002 gave civil wars off-ramps, but a settled peace was a free,
permanent win. MECH-DIP-003 makes it **bind and breakable**, reusing the engine's
own treaty machinery (`calc_treaty_breach_score`, `is_treaty_breach`).

Each settlement registers a peace **accord** (one per host) against the stress
floor it established. Every turn the accord is tested for breach: as the
complacency cycle rebuilds the host's stress **above that floor**, the accord is
strained; a heavy backslide breaks it. Repeated breaches **compound** (an
oath-breaker's later accords break under lighter strain). On breach:

- **grievance resurges** — renewed conflict, the betrayed peace (stress up,
  legitimacy down); and
- if a **broker** guaranteed it (DIP-002), the **trust between host and mediator
  collapses** (both directions, −0.12), burning the broker's credibility so
  future peace is harder to broker for that host.

This couples the complacency cycle to the slow breakdown of peace, and gives
diplomacy real *stakes*: staking a broker on a peace that later fails costs the
broker.

## A/B — Observatory 240-cycle (seeds 42/7/99), still DYNAMIC GALAXY — CERTIFIED

| Seed | settlements | broken accords | sustained civil-war load | DYNAMIC |
|---|---|---|---|---|
| 42 | 61 | 7 | 1.48 | ✓ |
| 7  | 69 | 5 | 1.75 | ✓ |
| 99 | 64 | 7 | 0.99 | ✓ |

~5–7 of ~60–70 peace accords break per run (~10%): most peace holds, some fails
consequentially. The living/dynamic invariants all hold. Tests:
`tests/test_mech_gov_001.py` (16) + `tests/test_gumas_consequence_layer.py` (4) +
`tests/test_observatory_240_cycle.py` (10) — 30 pass.

## Honest finding — mediation buys speed, not guaranteed durability

I initially expected (and DIP-002's first draft claimed) that a **mediated** peace
would be more *durable*. Measured, that does **not** robustly hold: across seeds
mediated accords break at roughly the same or a higher rate than exhaustion ones
(e.g. seed 42: mediated 16% vs exhaustion 7%). The cause is not the mechanic but
**faction heterogeneity** — the hosts that *get* brokers are the trusted,
contested core powers, whose conditions churn more after settlement; that
dominates any small durability edge from the settlement's bonus relief.

Rather than force a durability advantage with a large resistance coefficient
(which would be coefficient-gaming against the emergence principle), the honest
conclusion is recorded: **mediation makes peace faster and cheaper (DIP-002's
real, demonstrated benefit), but not automatically more lasting.** A brokered
peace among rivals can still collapse — and when it does, it costs the broker.
That is a richer dynamic than "diplomacy always wins," and it is what the
instruments actually show.

## Reuse note

Breach scoring is the engine's own `calc_treaty_breach_score` /
`is_treaty_breach` (PR §5.2 Formula 3), imported where available with a faithful
in-sync fallback for standalone tests. The only calibration is `BACKSLIDE_WEIGHT`
(strain sensitivity, set to the measured backslide range) — no new conflict math.

## Pillar B status

War, exhaustion-settlement, brokered diplomacy, and now binding/breakable
treaties are all live. Remaining in Phase 1: **MECH-CUL-001** (cultural exchange
/ soft power — lower onset, ease grievance, open off-ramps). Next per the plan:
**MECH-GOV-002** (culture-weighted authentic decisions, Pillar C).

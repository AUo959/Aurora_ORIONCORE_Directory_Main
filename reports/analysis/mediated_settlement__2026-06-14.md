# Mediated Settlement — Diplomacy as a Real Off-Ramp (MECH-DIP-002)

**Date:** 2026-06-14 | `tools/mech_gov_001.py` (`MediationModel`),
`tools/gumas_memory_run.py` (`_writeback_mediation`, mediated-settlement bonus).
Phase 1 of the dynamic-galaxy program, building on MECH-REB-004.

## What it adds

MECH-REB-004 gave civil wars an off-ramp, but a generic one — every settlement
was won the same way (grinding to mutual exhaustion). MECH-DIP-002 makes
**diplomacy a distinct, faster, cheaper path**, and ties it to the galaxy's
actual relationships.

An insurgency becomes **mediation-available** when its host faction has a
**credible third-party broker** — a peaceful neighbour it *mutually trusts*,
found in the live trust network that MECH-GOV-001 / MECH-DIP-001 already
maintain (`faction.trust_scores`). A broker must be mutually trusted at or above
a floor and must not itself be fighting a serious war (a faction in its own
civil war can't broker peace). When a broker exists, the insurgency's
de-escalation probability gets the formula's mediation bonus, so the war ends
sooner; and a **mediated** settlement is more durable — it spends more grievance
and restores more legitimacy than a peace won by exhaustion (×1.5).

The result is the canon dynamic: a **well-connected** polity gets a quick
brokered peace; an **isolated or distrusted** one (e.g. the AI warlord, trusted
by no one) has no shortcut and must bleed until it is exhausted. Emergent — the
broker is read from the trust state, never scripted.

## Calibration (what counts as a credible broker)

`TRUST_FLOOR` sets the bar. Trust runs ~0.18–0.66 (avg ~0.5). Swept and chosen
for *meaning*, not a target number:

| TRUST_FLOOR | mediated share | reading |
|---|---|---|
| 0.55 | ~0.90 | brokers ubiquitous — diplomacy stops discriminating |
| **0.58** | **~0.40–0.56** | **both paths present; share varies by seed's network** |
| 0.62 | ~0.06–0.15 | diplomacy rare |
| 0.66 | ~0.00–0.13 | diplomacy almost never |

**0.58** ("notably above average mutual trust") is the coherent choice: roughly
half of civil wars end by brokered peace and half by exhaustion, and *which*
depends on each seed's relationships.

## A/B — Observatory 240-cycle (seeds 42/7/99), still DYNAMIC GALAXY — CERTIFIED

| Seed | settlements | mediated | mediated share | onsets | sustained civil-war load | DYNAMIC |
|---|---|---|---|---|---|---|
| 42 | 61 | 31 | 0.51 | 71 | 1.48 | ✓ |
| 7  | 73 | 29 | 0.40 | 84 | 1.91 | ✓ |
| 99 | 66 | 37 | 0.56 | 77 | 1.35 | ✓ |

Diplomacy now resolves ~40–56% of civil wars, the rest grind to exhaustion —
two distinct off-ramps where before there was one. The living/dynamic invariants
all hold (conflict recurs, cast rotates, no collapse: load well under the 3.0
permanent-war reference). Determinism confirmed. Tests:
`tests/test_mech_gov_001.py` (15) + `tests/test_gumas_consequence_layer.py` (4) +
`tests/test_observatory_240_cycle.py` (10) — 29 pass.

## Notes & follow-ups

- The mediator is currently any mutually-trusted peaceful faction. A richer
  version (MECH-DIP-003 / Pillar B depth) could let the broker *spend*
  diplomatic capital or stake its own reputation, with treaty-enforcement
  consequences if the settlement breaks (`calc_treaty_breach_score` already
  exists).
- `MEDIATED bonus ×1.5` makes brokered peace more durable; left modest so it
  doesn't trivialise conflict (the dynamic gate confirms it doesn't).
- The de-escalation rule remains the engine's own `calc_deescalation_probability`
  — mediation only flips that formula's existing `mediation_available` input, so
  no new conflict math was invented.

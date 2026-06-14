# Culture-Weighted Decisions — Authentic Choices (MECH-GOV-002)

**Date:** 2026-06-14 | `tools/mech_gov_001.py` (`CultureModel`),
`tools/gumas_memory_run.py` (`_writeback_resolution` culture term). First build
of Pillar C (authentic decisions).

## The gap

The leaders carry genuinely distinct cultural biases — `dominant_bias` ∈
{zero-sum clan, hyper-rational construct, fear-driven theocracy, sunk-cost
attritionist, survivalist nomads, status-quo union, ...}, sourced from the
charforge `traits.json` capsules. But the engine's behavioural knobs barely vary:
every leader sits at `diplomacy_openness ≈ escalation_threshold ≈
risk_tolerance ≈ 0.5`. So **culture was labelled but not expressed** — identical
conditions produced identical choices, and the galaxy felt uniform.

(`mech.decide()` is not wired to drive the sim, so culture had to attach where
decisions actually bite — the settle-or-grind choice in the resolution layer.)

## The mechanic

**MECH-GOV-002 (`CultureModel`)** translates a leader's `dominant_bias` into a
behavioural **settlement lean** (and an escalation lean), applied to the
de-escalation probability of that leader's civil wars:

| dominant_bias | settlement lean | character |
|---|---|---|
| zero_sum | −0.25 | "every gain by another is our loss" — grinds on |
| sunk_cost | −0.22 | "will not yield on prior sacrifices" |
| fear_based | −0.12 | distrustful, defensive |
| confirmation | −0.08 | stays the course |
| status_quo | −0.05 | inertia |
| moral_licensing | +0.05 | opportunistic |
| survivorship | +0.15 | settles to survive |
| hyper_rationalism | +0.22 | takes the rational off-ramp |

It accepts both the engine's `BiasType.X` form and the `traits.json`
`..._thinking`/`..._bias` text; unknown/missing bias is culturally neutral.
Magnitudes are modest so culture *colours* the decision without overriding the
situation. Nothing is invented — the bias labels are the engine's own.

## A/B — settlement propensity by culture (seeds 42/7/99, culture OFF vs ON)

| dominant_bias | lean | culture OFF | culture ON |
|---|---|---|---|
| zero_sum | −0.25 | 17.2% | **7.1%** |
| sunk_cost | −0.22 | 12.0% | **7.0%** |
| fear_based | −0.12 | 19.0% | 10.6% |
| status_quo | −0.05 | 15.3% | 15.1% |
| survivorship | +0.15 | 12.4% | **21.7%** |
| hyper_rationalism | +0.22 | 12.1% | **19.3%** |

**With culture off, settlement rate is uniform (~12–19%) and unrelated to the
bias. With culture on it tracks the lean monotonically** — a ~3× gap between the
most belligerent (zero-sum/sunk-cost, ~7%) and most pragmatic (survivalist/
rational, ~20%) cultures resolving the *same kind* of civil war. Large samples
(n≈350+ for the major biases). The Observatory now reports this every run as
`settlement_rate_by_culture` and gates a `cultures_diverge` verdict
(settlement-rate spread ≥ 5%; observed 11–13%).

## Status

Observatory 240-cycle stays **DYNAMIC GALAXY — CERTIFIED** on seeds 42/7/99 with
culture on; living/dynamic invariants hold (sustained civil-war load < 3.0).
Tests: `tests/test_mech_gov_001.py` (17) + `tests/test_gumas_consequence_layer.py`
(4) + `tests/test_observatory_240_cycle.py` (11) — 32 pass.

This is the first of Pillar C. The `escalation_lean` is computed and exposed but
not yet wired (escalation lives mostly in the engine); a later pass can route it
into onset/maturation. Next per the plan: **MECH-GOV-003** (internal politics &
succession) and **MECH-POW-001** (galactic power dynamics), which deepen
authentic decision-making beyond the settle-or-grind axis.

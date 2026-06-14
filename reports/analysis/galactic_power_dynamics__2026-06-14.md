# Galactic Power Dynamics (MECH-POW-001) — Pillar C complete

**Date:** 2026-06-14 | `tools/mech_gov_001.py` (`PowerDynamicsModel`),
`tools/gumas_memory_run.py` (`_writeback_power`). Completes Pillar C (authentic
decisions).

## Canon grounding

`simulation_expansion_systems_outline.md` §10 (Faction Strategic Behavior):
*Alliance_System = Shifting_Trust-Based_Relationships; Military_Readiness =
Threat-Based_Adjustments; Faction_Strategy = Dynamic_Response.* MECH-POW-001
realizes the alliance/threat half on the live trust network.

## The mechanic

Each turn the galaxy's **balance of power** is read — power = `0.45·military +
0.40·economic + 0.15·technology` — and the **hegemon** (strongest faction) is
found. Every other faction reacts to how far the hegemon out-powers it
(*threat*), and **which way it reacts is decided by its culture** (MECH-GOV-002):

- **Balancing** — proud/defensive cultures (zero-sum, fear, sunk-cost,
  confirmation) resist domination: they pull trust **away** from the hegemon and
  **toward** each other (an anti-hegemon coalition).
- **Bandwagoning** — pragmatic/survivalist cultures (survivorship, status-quo,
  moral-licensing, hyper-rational) seek safety/spoils: they pull trust **toward**
  the hegemon.

The nudge scales with threat (a balanced multipolar galaxy stays quiet; a
lop-sided one realigns) and operates on the trust network MECH-GOV-001/DIP-001
maintain — so power politics feeds mediation (DIP-002) and disposition.

## A/B — trust toward the current hegemon, by stance (POW off vs on)

| Seed | gap off (bandwagon − balance) | gap on | balancers (on) | bandwagoners (on) |
|---|---|---|---|---|
| 42 | +0.01 | **+0.25** | 0.527 | 0.776 |
| 7  | +0.02 | **+0.31** | 0.489 | 0.803 |
| 99 | +0.00 | **+0.25** | 0.516 | 0.771 |

**Without the mechanic, a faction's culture has no bearing on how it trusts the
strongest power (gap ≈ 0). With it, bandwagoners end ~0.25–0.31 more trusting of
the hegemon than balancers** — proud cultures pull away from the strong,
pragmatic ones flock to it. Run-averaged against the *current* hegemon (robust to
the hegemon shifting over the run); trust stays bounded (no saturation). The
Observatory reports `power_realignment_gap` and gates a `power_politics_active`
verdict (gap ≥ 0.05).

`REALIGN_RATE = 0.10` was calibrated so the power signal reads clearly against
GOV-001's stronger trust pull — the only knob; the stance assignment is the
culture's own (GOV-002 bias).

## Status — Pillar C complete

Observatory 240-cycle stays **DYNAMIC GALAXY — CERTIFIED** on seeds 42/7/99 with
all of Pillar C live; living/dynamic invariants hold. Tests:
`tests/test_mech_gov_001.py` (19) + `tests/test_gumas_consequence_layer.py` (4) +
`tests/test_observatory_240_cycle.py` (13) — 36 pass.

**Pillar C (authentic decisions) is now complete:** civilizations decide by
culture (GOV-002), their leaders rise and fall and the new regime decides
differently (GOV-003), and they take a stance toward galactic power by their
character (POW-001) — all three threads driven by the same canon `dominant_bias`.

## Follow-ups

- §10's **threat-based military readiness** (a threatened faction builds up) and
  **deterrence** (the strong face fewer challenges) are not yet modelled — a
  later enrichment on top of the realignment core.
- Next per the plan: **Pillar A** (emergent consequence — TER-001/ECO-001/
  CUL-002) makes a war's outcome reshape the world. The Pilot also flagged the
  **Office of Strategic Diplomacy** institutional material for a diplomacy
  deep-read.

# Assimilation vs Local Tradition (MECH-CUL-002) — Pillar A complete

**Date:** 2026-06-14 | `tools/mech_gov_001.py` (`AssimilationModel`),
`tools/gumas_memory_run.py` (`_writeback_assimilation`). The third and final
mechanic of Pillar A (emergent consequence).

## Canon grounding & the tie-in

Canon §12: *Cultural_Identity = Union_Assimilation vs Local_Traditions.* The hook
is MECH-TER-001's **contested** ground — territory recently lost to a civil war and
being reclaimed, i.e. a **restive, reconquered population**. Holding it is a
cultural choice, decided by the holder's `dominant_bias` (the same canon signal
that drives all of Pillar C):

- an **assimilationist** culture (zero-sum / fear / sunk-cost / confirmation)
  imposes its identity — control now, but **identity grievance** (demographic
  stress) that fuels future separatist unrest. *Win the land, lose the peace.*
- a **tolerant** culture (survivorship / status-quo / moral-licensing / rational)
  preserves local tradition — looser integration for **civic peace** (a little
  restored legitimacy, no grievance).

## A/B — Observatory 240-cycle (seeds 42/7/99), DYNAMIC GALAXY — CERTIFIED

| Seed | assimilation impositions | tolerant accommodations | mature civil-war load |
|---|---|---|---|
| 42 | 115 | 138 | 2.08 |
| 7  | 116 | 52  | 1.32 |
| 99 | 238 | 190 | 1.90 |

**The cultural cost of conquest is real and culture-split:** across every seed,
assimilationist regimes impose identity on reconquered ground (levying grievance)
while tolerant regimes accommodate it (earning legitimacy) — two different costs
for the same act, decided by who you are. Both policies are exercised; the
Observatory gates `cultural_cost_active` (both > 0). The civil-war load stays well
under the 3.0 collapse reference, so the new grievance source does not tip the
galaxy toward war.

## Honest finding — gentle by design, not forced

An A/B isolating the mechanic (same factions, CUL-002 on vs off) showed its effect
on the *outcome* (an assimilationist holder's net unrest) is **small and noisy**:
identity grievance (0.06 × a small contested fraction) is dwarfed by the other
stress drivers, and faction heterogeneity confounds a clean stress comparison. An
early stronger setting (0.10) mildly amplified conflict on one seed (cw_load
1.59→2.14). Rather than crank the coefficient to manufacture a measurable outcome
— which would be coefficient-forcing against the emergence principle — the
mechanic is kept **gentle and certified at the mechanism level**: the
culture-dependent *policy split* is unambiguously real and active; the galaxy-
level impact is modest and reported as such. This is the weakest-impact of the
three Pillar-A mechanics, and that is stated plainly.

Tests: `tests/test_mech_gov_001.py` (22) + `tests/test_gumas_consequence_layer.py`
(4) + `tests/test_observatory_240_cycle.py` (16) — 42 pass.

## Pillar A complete — the loop closes

| Mechanic | Consequence |
|---|---|
| **TER-001** | war → permanent territory loss → economic ceiling → power (map→economy→power) |
| **ECO-001** | war scarcity / peace boom; economy → unrest feedback loop |
| **CUL-002** | culture-dependent cost of holding conquered ground |

With Pillar A done, **all three of the Pilot's clauses are live and measured**:
conflict produces interacting consequence (Pillar A), war is not the only off-ramp
(Pillar B), and civilizations decide authentically (Pillar C). Next: **Phase 4** —
the integration pass and a senior-staff roundtable to certify *dynamism* (not just
control) on the complete loop, with all the new instruments.

Queued enrichments (from the deep-reads): DIP-004 coercive diplomacy, DIP-005
autonomy/reintegration (wires `PEACEFUL_SECESSION`, ties to TER-001's seceded
ground), the `l2_state` spatial deepening, and a tech-driven ECO boom.

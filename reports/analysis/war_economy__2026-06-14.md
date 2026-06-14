# War Economy & Market Flux (MECH-ECO-001)

**Date:** 2026-06-14 | `tools/mech_gov_001.py` (`WarEconomyModel`),
`tools/gumas_memory_run.py` (`_writeback_economy`). Second mechanic of Pillar A.

## What it adds (distinct from TER-001)

MECH-TER-001 made a war's territorial outcome *permanently* lower a faction's
economic ceiling. MECH-ECO-001 adds the **transient cycle** on top of that and a
new **feedback loop**:

- **War scarcity** — while a faction fights a mature war, output (`economic_
  strength`) is suppressed below its potential.
- **Recovery boom** — at peace, reconstruction drives output back up toward the
  (territory-capped) ceiling, faster than the engine's slow growth.
- **Economy → unrest feedback** — a depressed economy (output far below its
  potential) deepens `demographic_stress`, which raises unrest; a booming economy
  eases it. This closes a new loop: **war → economic depression → grievance →
  war.** (`Economic_Stability` is the canon Public_Opinion term, wired live.)

## A/B — Observatory 240-cycle (seeds 42/7/99), DYNAMIC GALAXY — CERTIFIED

Economic health = output / potential, for at-war vs at-peace factions:

| Seed | at-war health | at-peace health | gap |
|---|---|---|---|
| 42 | 0.239 | 0.781 | **+0.54** |
| 7  | 0.366 | 0.806 | **+0.44** |
| 99 | 0.176 | 0.703 | **+0.53** |

**The economy now busts in war and booms in peace** — at-war factions run at
~0.18–0.37 of potential while at-peace factions recover to ~0.70–0.81. The A/B
also shows ECO-001's specific lift: peacetime economic health rises from ~0.58
(no ECO-001) to ~0.70–0.81 (the reconstruction boom), while the war side stays
depressed.

**The feedback loop turns without running away.** Mean civil-war load is
essentially unchanged with the loop active (off ~1.25–1.70, on ~1.09–1.62 across
seeds) — economic hardship feeds unrest, but the off-ramps, recovery, and the
recovery-boom counter it, so it does not spiral. The living/dynamic invariants
all hold. The Observatory reports `war_economic_health` / `peace_economic_health`
and gates `war_economy_active` (gap ≥ 0.15).

Magnitudes are gentle by design (scarcity 0.02/turn, boom 0.015/turn, hardship
stress scaled by depth) — a coherent boom-bust cycle, not a forced one. Tests:
`tests/test_mech_gov_001.py` (21) + `tests/test_gumas_consequence_layer.py` (4) +
`tests/test_observatory_240_cycle.py` (15) — 40 pass.

## Status

Pillar A now has TER-001 (permanent map→economy→power) + ECO-001 (transient
war/peace economic cycle + the economy→unrest loop). **Remaining: MECH-CUL-002**
(assimilation vs local tradition — a cultural cost to *holding* conquered ground),
then Phase 4 integration + the senior-staff roundtable on the complete loop.
Noted enrichment: the engine's `tech_economic_multipliers` could make the boom
tech-driven; `l2_state` logistics could localize scarcity.

# Internal Politics & Succession (MECH-GOV-003)

**Date:** 2026-06-14 | `tools/mech_gov_001.py` (`SuccessionModel`),
`tools/gumas_memory_run.py` (`_writeback_succession`). Pillar C, deepening
authentic decisions beyond the settle-or-grind axis.

## Canon grounding (look-first result)

`simulation_expansion_systems_outline.md` §13 specifies it: *Succession_Dynamics =
Senate_Elections vs Military_Coups; Scandal_Management = Public_Perception vs
Actual_Corruption.* `intake/text_early_sim_logic.txt` gives the form
`Public_Opinion = Policy_Success − Scandals + Economic_Stability`. The Union
Senate is canon (`org_union_senate`), and the Velar Imperium is written as a
chronic-legitimacy-crisis polity. The leader fields already exist
(`public_legitimacy`, `scandals`, `war_pressure`). Nothing invented.

## The mechanic

A leader's **grip on power** = `legitimacy − SCANDAL_WEIGHT·scandal_load −
WAR_PRESSURE_WEIGHT·war_pressure`. (Survey of the live state: `public_legitimacy`
(0.18–0.37) and `scandals` (60–99, accumulating) are the signals that actually
move — `elite_support`/`institutional_control` are inert ~0.5, so grip is built
on the live ones.) When grip falls below a crisis threshold, after a honeymoon
cooldown, the regime **falls** with probability rising as the crisis deepens.

*How* it falls is set by the polity's **founding character**, locked at first
sight (so transient war-economy drift can't make everyone look militarized):

- **militarized** (military ≥ economic at founding) → **military coup**: a junta
  with shaky starting legitimacy (0.28), a hard-line successor culture
  (zero-sum / fear / sunk-cost), and a destabilizing **stress bump**;
- **economic/institutional** → **Senate election**: a stronger mandate (0.45), a
  pragmatic successor culture (rational / status-quo / survivorship), no shock.

Either way the successor arrives with **scandals cleared** and a **new
`dominant_bias`** (a real engine `BiasType`), which flows straight into MECH-GOV-002
— so **a regime change visibly shifts the faction's trajectory**: a coup that
installs a zero-sum junta makes the faction grind its wars; an election that
seats a reformer makes it settle. This is the canon §13 effect — turnover
prevents leadership stagnation and gives internal politics real consequences.

## A/B — Observatory 240-cycle (seeds 42/7/99), DYNAMIC GALAXY — CERTIFIED

| Seed | successions | coups | elections | factions w/ turnover | sustained civil-war load |
|---|---|---|---|---|---|
| 42 | 8 | 5 | 3 | 5 | 1.88 |
| 7  | 8 | 7 | 1 | 7 | 2.04 |
| 99 | 9 | 6 | 3 | 5 | 1.46 |

Leadership turns over ~8–9× per run (roughly one regime change per ~27 turns
across 13 factions); **5–7 factions change their ruling culture** over a run.
Coups dominate (a violent galaxy) but elections occur for the institutional/
economic polities — the founding-character split holds. The living/dynamic
invariants all hold. Tests: `tests/test_mech_gov_001.py` (18) +
`tests/test_gumas_consequence_layer.py` (4) +
`tests/test_observatory_240_cycle.py` (12) — 34 pass. The Observatory now reports
`succession_counts` / `factions_with_turnover` and gates a `leadership_turns_over`
verdict.

## Notes & follow-ups

- A succession sets `dominant_bias` to a real `BiasType` (the engine reads it
  descriptively, so this is safe); the mechanics-layer realizes "a new leader
  took power" by mutating the persistent leader, since the engine has no
  leader-replacement path of its own (owner-clearance item for a true engine-side
  succession).
- `Legacy_System` (political families / mentorship lines) and `Fame_and_Notoriety`
  from §13 are not yet modelled — a later enrichment.
- Pillar C now has GOV-002 (culture-weighted decisions) + GOV-003 (succession).
  Remaining: **MECH-POW-001** (galactic power dynamics — balancing / bandwagoning /
  deterrence), then Pillar A (emergent consequence).

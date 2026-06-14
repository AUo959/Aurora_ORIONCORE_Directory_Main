# Insurgency Resolution — The Off-Ramp Graft (MECH-REB-004 + D1)

**Date:** 2026-06-14 | `tools/mech_gov_001.py` (`InsurgencyResolutionModel`),
`tools/gumas_memory_run.py` (`_writeback_resolution`),
`tools/observatory_240_cycle.py` (D1 honest metric). First build of the
dynamic-galaxy program (Phase 0 / D4 + D1).

## What was wrong (roundtable diagnosis, confirmed by deep read)

The galaxy ran **two parallel conflict systems**. Inter-faction `ConflictState`
had a full de-escalation ladder ending in `RESOLUTION`
(`calc_deescalation_probability`, mediation, treaty collapse) — and it worked.
The intra-faction **insurgency** layer (`rebellion.py`) had **only military
suppression**: a civil war could be crushed (SUPPRESSED) but never *ended*.
`InsurgencyPhase.RESOLVED` was declared in canon yet never assigned, and the
engine recomputes phase from strength every tick and never removes an
insurgency — so suppressed movements lingered, kept their grievance, and the
same ~13 wounds reopened forever. War was the only off-ramp.

## The fix — graft the engine's own resolution machine onto insurgencies

**MECH-REB-004 (Insurgency Resolution / Mediated Settlement)** reuses the
engine's own `calc_deescalation_probability` (`formulas.py`, "PR §5.2 Formula
1") — preferring the real import, falling back to a faithful in-sync copy for
standalone tests. Each turn, an insurgency past a grace window has its fields
mapped onto the de-escalation inputs:

| de-escalation input | insurgency source |
|---|---|
| war_cost (state) | host `leader.war_pressure` |
| war_cost (rebels) | `max(repression_level, 1 − insurgent_strength)` |
| stalemate_index | `min(1, turns_active / 30)` |
| internal_pressure (state) | host grievance `(economic + political)/2` |
| internal_pressure (rebels) | `1 − popular_support` |
| mediation_available | a diplomatic overture (MECH-DIP-002 hook; off here) |
| + diplomacy_openness | host leader trait |

Successful de-escalation rolls accumulate settlement progress; on full
settlement the movement is **retired** (the realization of `RESOLVED`, since the
engine has no removal path) and its **grievance is spent** — demographic stress
eased, a little legitimacy restored. That legitimacy restore is a *peaceful*
renewal path (D6), distinct from the complacency war-purge. Because the cause is
addressed, the host can later host a **different** insurgency: the conflict cast
rotates instead of reopening.

It is **self-limiting**: de-escalation probability only rises as war cost,
stalemate, and domestic pressure accumulate, so fresh or popular insurgencies do
not settle — conflict stays real; no permanent-peace regression.

## D1 — the honest stability metric

The stability index's conflict term is `0.10·(1 − conflict_pressure)`, and
`conflict_pressure` sees only inter-faction war (→0 during civil war), so it pays
full relief while civil wars burn. The observatory now also reports
**`true_stability`** = engine stability − `0.10·(combined − conflict_pressure)`,
where `combined = max(conflict_pressure, insurgency_pressure)` — folding internal
conflict in so a *resolving* insurgency visibly relieves stability.

## A/B — Observatory 240-cycle (seeds 42/7/99), now DYNAMIC GALAXY — CERTIFIED

| Seed | engine plateau | honest plateau | settlements | onsets | off-ramp share | waves |
|---|---|---|---|---|---|---|
| 42 | 0.387 | 0.326 | 60 | 71 | 0.84 | 3 |
| 7  | 0.384 | 0.294 | 64 | 74 | 0.86 | 3 |
| 99 | 0.387 | 0.300 | 68 | 76 | 0.90 | 3 |

- **Cast rotation:** distinct insurgencies formed went **13 → 71/74/76**. The
  "same wounds reopen" pathology is gone.
- **Off-ramp:** **60–68 negotiated settlements** per run; war is no longer the
  only way a civil war ends.
- **Civil wars no longer pile up:** per-era counts fell from ~6–10 (pre-graft) to
  ~0.5–3.75, still recurring in 3 waves.
- **Honesty:** the internal-conflict-aware plateau sits at **~0.29–0.33**, well
  below the engine's masked ~0.38 — the true reading the roundtable predicted.
- Determinism confirmed. Tests: `tests/test_mech_gov_001.py` (14) +
  `tests/test_gumas_consequence_layer.py` (4) +
  `tests/test_observatory_240_cycle.py` (10) — 28 pass.

## Honest findings & follow-ups

- **Minor-insurgency population rises** (`insurgency_pressure` climbs late as
  rotation spawns many small movements). Realistic as "constant localized
  unrest," but it drags `true_stability`; worth watching / possibly letting
  minor insurgencies also fade.
- **Fragmentation events fell to ~0** — insurgencies now settle before crossing
  the fragmentation territory threshold. A consequence of resolution, noted.
- **D9 (re-derive COLLAPSE_FLOOR):** with the honest metric at ~0.29–0.33, the
  0.30 floor is now near the operating point; the regression gate still uses the
  engine metric (floor ~0.38) — re-deciding the floor against `true_stability` is
  the open D9 item.
- **Engine-side `RESOLVED`:** resolution is realized in the governed `tools/`
  layer by retiring the entity. A proper engine-side terminal/removal path for
  `InsurgencyPhase.RESOLVED` remains an owner-clearance follow-up.

Reuse note: the de-escalation rule is the engine's own formula, not a new
coefficient set — the emergence principle is served by inheriting the original
equation rather than inventing one.

# Seed-42 Stability — Review & Root Cause (the civil-war attractor)

**Date:** 2026-06-13 | "First look for an answer already in the materials,
then build what's needed." This is the review; the build spec is §4.

## 1. The answer already exists in the materials

`SIM_ENGINE_OUTPUTS/LESSONS_LEARNED__SIM_RUN_SEED42_T001_T122` (2026-05-21) is a
full root-cause analysis of this exact collapse, with a **ranked priority list
(§5)**. The top items:

1. **Implement insurgency resolution pathway with a reachable threshold.**
3. **Add a civil-war onset dampener tied to active insurgency count.**
4. Seed at least one designed resolution scenario event.

And priority **#2 (establish faction canon + named assets) is already done**
this session — the L2 canon promotion (entities, Marshals/Sentinels, timeline,
factions) filled exactly that gap.

## 2. Code-confirmed root cause: CIVIL_WAR is a one-way door

The lessons doc diagnosed it from telemetry; the code confirms it exactly
(`FORGE__GUMAS_v3.0/rebellion.py`):

- **`InsurgencyPhase.RESOLVED` is read but never assigned.** `engine_advanced.py:877`
  checks `if i.phase != InsurgencyPhase.RESOLVED`, but **no line anywhere sets a
  phase to RESOLVED.** There is no resolution transition.
- **The only exit from civil war is the `SUPPRESSED` gate**
  (`insurgent_strength < 0.05 AND territory_controlled < 0.01`), which is
  **unreachable** once entrenched:
  - `insurgent_strength` pins at **1.0**: per-turn change = support·0.35 +
    grievance·0.30 + external·0.20 − repression·0.40 + base_gain 0.005. With
    popular support floored at ~0.41 (lessons §2.5), gains ≥ losses, so it sits
    at the `min(1.0)` cap.
  - `territory_controlled` only shrinks when `repression_eff > insurgent_strength`.
    At strength = 1.0 that needs repression > 1.0; `calc_repression_effectiveness`
    caps ≤ 1.0 → **territory can never fall.**
- **Onset outruns resolution with no brake:** onset climbs to 2.45/turn (lessons
  §2.2), resolution rate is 0, and there is no dampener or ceiling on
  simultaneous civil wars.
- **Population collapse has no outcome:** avg population stability hit 0.093
  (lessons §1.5) with no regime-collapse trigger — that pathway is absent.

The seed-42 plateau (stability 0.358, 4–13 civil wars, strength 1.0) is a
**stable fixed point with no exit edge**. No amount of onset-side tuning (where
MECH-SOC-001 currently acts) can drain an attractor that has no outflow.

## 3. What exists vs. what must be built

| Need | Already here? |
|---|---|
| Faction canon + named assets (priority #2) | **YES** — L2 promotion this session |
| Driver substrate for war-weariness / support erosion | **YES** — MECH-SOC-001 grievance/relief memory (path-dependent, slow decay) |
| Social-dynamics framing (DSI, `P_stability=E+T−C`, peace as a path) | **YES** — `canon/L2/social_dynamics/` |
| Insurgency **resolution** transition (assign RESOLVED) | **NO** — must build |
| Insurgent-strength **war-weariness / attrition** so it leaves 1.0 | **Insufficient** — only a weak repression term; must build a time-in-war decay |
| Onset **dampener** (embattled factions resist new civil wars) | **NO** — must build |
| Regime-collapse trigger from population stress | **NO** — build or defer |

The peace-mechanics doc (`non_war_progression_mechanics.md`) frames peace as an
*alternative to war onset* but does **not** specify how an entrenched civil war
ends — so resolution is a genuine design gap to fill, grounded in (and
extending) the social canon.

## 4. Build spec — MECH-SOC-002 "Insurgency Resolution / War-Weariness"

Minimal, governed (built in tracked `tools/`, wired via `gumas_memory_run.py`),
grounded in the grievance substrate. Gives the attractor a reachable exit edge:

1. **War-weariness attrition.** Turns-in-civil-war + sustained casualties +
   saturated grievance → a decay term on `insurgent_strength`, so it leaves the
   1.0 fixed point. (Resource exhaustion — lessons §1.2 option.)
2. **Support erosion via the grievance loop.** A population that has remembered
   hardship long enough begins to remember *relief/exhaustion* (war-weariness);
   MECH-SOC-001 net grievance falling drags `popular_support` below a reachable
   resolution floor.
3. **Resolution transition.** When `popular_support < floor` OR war-weariness is
   high OR legitimacy/mediation recovers → set phase `CIVIL_WAR → SUPPRESSED →
   RESOLVED` and emit a `CIVIL_WAR_RESOLUTION` event (the transition that does
   not exist today).
4. **Onset dampener.** `onset_prob *= 1 / (1 + active_insurgencies[fid])` so an
   already-embattled faction is harder, not easier, to destabilize further
   (lessons §2.2).

**Success criterion (A/B vs. seed-42 baseline):** at least one civil war
reaches RESOLVED, and final stability rises above the 0.358 plateau — *without*
tuning coefficients to force it. Per the emergence principle, resolution
conditions are made *reachable*, not guaranteed; whether a given run resolves
remains emergent.

**Governance note:** the resolution transition ultimately needs to live in the
engine's rebellion phase. Build and validate the mechanic in tracked `tools/`
first (as with MECH-GOV/SOC-001); the engine edit to call it is a separate,
explicit step in the untracked engine dir, flagged for owner clearance.

## 5. Conclusion

The answer was already in the project: the collapse is structural (no exit from
the civil-war attractor), not a balance problem, and the fix is a resolution
pathway + onset dampener (lessons §5). One of the three prerequisites (faction
canon) is already done, and the driver substrate (grievance memory) is already
built and wired. What remains is **MECH-SOC-002** — the resolution/war-weariness
mechanic that gives the attractor an exit edge. Ready to build on owner go.

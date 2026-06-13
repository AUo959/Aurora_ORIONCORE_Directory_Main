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

---

## 6. Expanded root cause — conflict *initiation* is over-weighted (owner insight, confirmed)

The resolution gap (§2) is only half of it. The owner's suspicion — that
conflict *initiation* is unrealistic and biased by the canon's military/political
focus — is confirmed, and it has a documented prior solution that was never built.

### The prior attempt (recovered, never implemented)

`canon/L2/social_dynamics/non_war_progression_mechanics.md` opens: *"if we
overemphasize war, we risk creating a galaxy where peace is unattainable."* It
prescribes, concretely:

- **DSI = (P + E + S) / (C + M)** — a faction absorbs crises without war when
  political unity, economy, and social cohesion are high relative to
  **corruption and militarization**. *Militarization is a destabilizing term* —
  so a galaxy whose well-developed canon is Marshals, Sentinels, fleets,
  operations, and intelligence is mechanically biased toward instability.
- **`GDP_growth = R + I − D`**, **golden ages `P_stability = E + T − C`**,
  cultural/scientific progression, crisis-diplomacy de-escalation paths.
- **§4 explicit fix:** *"adjust conflict probability so that non-war events make
  up at least 60–70% of major events,"* *"ensure war is costly,"* *"if war is
  the only viable mechanic, it will always be used."*

### What the engine actually has

- The `EventType` vocabulary **is balanced** (DIPLOMATIC_OVERTURE, ECONOMIC_BOOM,
  TRADE_AGREEMENT, TECHNOLOGY_BREAKTHROUGH, CULTURAL_MOVEMENT,
  INFRASTRUCTURE_INVESTMENT, MEDIATION_OFFER … alongside the war types).
- But **DSI / non-war rebalance / golden-age / costly-war: none are
  implemented.** The v3 phase *dynamics* are the bias: rebellion + intelligence
  self-reinforce and escalate (lessons §2.1, §2.2) while technology/negotiation
  collapse (§1.4) — the war phases capture the event budget with no force
  pulling the mix back toward the prescribed 60–70% non-war.

So war dominates not because it's the only option but because it is the only
**self-reinforcing, well-tuned** option, and nothing rewards the peaceful paths
or penalizes militarization. The canon's military emphasis is the worldbuilding
mirror of the same imbalance.

## 7. Revised build plan — two-sided (drain the attractor *and* shrink the inflow)

**A. Exit edge — MECH-SOC-002 (Insurgency Resolution / War-Weariness)** — as §4.
Gives entrenched civil wars a reachable end.

**B. Initiation realism — implement the non-war progression prescription:**

1. **DSI onset gate.** Compute `DSI = (P + E + S)/(C + M)` per faction and gate
   rebellion/conflict onset on it — high P/E/S absorbs crises; high
   militarization/corruption raises onset. (Realizes the canon formula.)
2. **Non-war progression dynamics.** Give the economic/cultural/scientific
   phases self-reinforcing growth (golden ages via `P_stability = E + T − C`)
   so they compete for the event budget — target the 60–70% non-war floor.
3. **Make war costly.** War/insurgency draws down economy and legitimacy, so a
   prosperous faction prefers diplomacy (the AI-adaptability rule).
4. **Memory ties in.** MECH-GOV-001 already makes a betrayed faction wary and a
   weak one negotiate; the DSI gate lets a *prosperous, cohesive* faction
   de-escalate — the missing third disposition.

**Sequencing:** A and B are independent and additive. A alone lets existing
civil wars end; B alone slows new ones and offers alternatives; together they
should lift the seed-42 plateau. Build both governed in `tools/`, A/B each, and
report honestly — resolution and de-escalation made *reachable*, not forced.

This is the prior solution finally built, plus the exit edge it never had.

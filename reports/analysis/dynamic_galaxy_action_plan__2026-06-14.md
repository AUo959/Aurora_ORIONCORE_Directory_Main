# Action Plan — From a Controlled Galaxy to a Dynamic Galaxy

**Date:** 2026-06-14 | **Author basis:** Observatory 240-turn roundtable
(`reports/simulation/observatory_240_cycle__2026-06-14/`) + L2 canon review
**Standing principle:** wire mechanics coherently from canon; measure honestly;
never tune coefficients toward a target outcome. Fixes that *lower* a metric in
exchange for truth are correct.
**Revised:** R1 (2026-06-14) — see the revision block below; supersedes several
"build new" calls after the prebuilt-systems inventory + conflict-machine deep read.

---

## Revision R1 (2026-06-14) — reuse findings change the build, not the destination

Two follow-on surveys —
[`prebuilt_simulation_systems_inventory__2026-06-14.md`](prebuilt_simulation_systems_inventory__2026-06-14.md)
and [`conflict_resolution_machine_deepread__2026-06-14.md`](conflict_resolution_machine_deepread__2026-06-14.md)
— found that much of what this plan scoped as "build new" **already exists in the
codebase**, mostly from the original engine lineage. The destination (the three
pillars) is unchanged; the path is cheaper and lower-risk.

**Root cause, now precise.** The galaxy runs **two parallel conflict systems**.
Inter-faction `ConflictState` has a complete resolution machine
(`calc_deescalation_probability` → ladder …DEESCALATION→CEASEFIRE→NEGOTIATION→
RESOLUTION, mediation hook, treaty breach/collapse) — and it works
(`conflict_pressure`→0 because factions *do* settle). The intra-faction
**insurgency** layer (`rebellion.py`) has **none of it** — only military
suppression — even though `InsurgencyPhase.RESOLVED` is already declared and the
insurgency carries every field the de-escalation formula needs. **The dynamic
galaxy is mostly a matter of giving civil wars the resolution machine
inter-faction wars already have.**

**Corrected build/reuse table (supersedes the per-phase "Extend/New" columns):**

| Plan item | Was scoped | R1 reality |
|---|---|---|
| Phase 0 / **D4** RESOLVED state | build new | **Graft** `calc_deescalation_probability` (present in `formulas.py`) onto the rebellion tick; assign the already-declared `RESOLVED`. Resolution **spends grievance** so wounds close instead of reopening |
| **MECH-DIP-002** Mediated Settlement | build new | **Wire** the existing mediation hook (`_handle_diplomatic_overture`/`_handle_mediation_offer`) to the insurgency graft — a faster, grievance-cheaper off-ramp |
| **MECH-DIP-003** Treaty Enforcement | build new | **Already implemented** (`calc_treaty_breach_score`, `is_treaty_breach`, `TreatyPhase.COLLAPSED`, `_handle_treaty_violation`) — register settlements as `TreatyState`, inherit consequences |
| **MECH-GOV-002** Culture-weighted decisions | extend GOV-001 | Substrate ready: per-leader `traits.json` (`decision_style`, `dominant_bias`, tradition) + early `character_behavior_modules.py` (`reaction_triggers`, `loyalty_profile`) + `CHARACTERFORGE_SPEC` reaction-genome |
| **MECH-GOV-003** Succession/politics | build new | Equations exist (`intake/text_early_sim_logic.txt`: `Public_Opinion`, `P(support)`, `Political_Loyalty`); leader fields (`elite_support`, `scandals`, `public_legitimacy`) live |
| **MECH-POW-001** Power/coalitions | build new | Named gap in `GUMAS Engine Advancement.md`; `AI_Faction_Strategy` seed + alliance trust fields exist |
| **MECH-ECO-001** War economy | build new | Named gap ("limited economic interdependency"); economic fields live on `FactionState` |
| **Pillar A** causal depth | build new | Named gap ("sparse event provenance / no cascade tracking"); `event_id`/`payload_hash` plumbing already present to build on |
| (already shipped) MECH-SOC-005 recovery | built by us | Was the original engine's *"Phase 4.5 peacetime recovery (the missing half)"* — convergent re-derivation; a caution to read first |

**Revised sequencing (replaces the Phase 0→1 opening):**
0a. **Recover/verify** `formulas.py`+`models.py` completeness (full copies in
   `SIM_ENGINE_OUTPUTS/` and v2.0 staging) so the de-escalation formula is
   importable to the rebellion tick.
0b. **D1** honest conflict metric — now also fold `insurgency_pressure` so a
   *resolving* civil war visibly relieves stability.
0c. **D4 via the graft** — insurgency de-escalation ladder → `RESOLVED` (+grievance
   spend). Re-run the Observatory gate; expect cast rotation and falling chronic
   `insurgency_pressure`.
1.  **MECH-DIP-002** mediation → settlement as the faster off-ramp; **DIP-003**
   reused as-is.
Then Pillars C (Phase 2) and A (Phase 3) as written, on a galaxy where conflict
can finally *end*.

**Net effect:** Phase 0 and Phase 1 shrink from green-field builds to a port +
wiring of proven, canon-grounded code; risk drops (the resolution model already
ran in v1.x) and the emergence principle is better served (we inherit the
original equations rather than inventing coefficients). Tasks #34–38 stand;
their contents are reframed by this revision.

---

## The reframing (Pilot's diagnosis)

> "A galaxy with control dynamics, but not yet a dynamic galaxy."

We built a **homeostat**: feedback loops (war-weariness, recovery, the
complacency cycle) that hold stability in a band and stop the two degenerate
fixed points — permanent war, permanent peace. That was necessary. It is not
sufficient. A homeostat *regulates*; it does not *live*. Today the galaxy has
exactly one lever (military suppression / war-weariness) by which conflict
begins and ends, decisions are driven by force and trust alone, and a war
changes almost nothing about the world that follows it (the roundtable proved
human cost freezes, territory barely moves, the same 13 wounds reopen).

**We are not done until the galaxy *acts* rather than merely *settles*.** The
Pilot named the three conditions; this plan builds to them, on canon that
already specifies them.

## What canon already gives us (the "look first" result)

`canon/L2/social_dynamics/simulation_expansion_systems_outline.md` enumerates
the exact systems this requires — outlined, never built:

| Canon system | Serves |
|---|---|
| §10 Faction Strategic Behavior & AI Decision-Making (internal politics, alliances) | authentic decisions |
| §11 Diplomatic & Negotiation Systems (treaties, **soft power = cultural exchange**) | off-ramps; diplomacy/culture as systems |
| §12 Planetary Management & Territorial Control (**cultural identity: assimilation vs local tradition**) | emergent consequence; culture |
| §13 Advanced Character Evolution & Succession (coups, elections, scandal) | internal politics |
| §14 Expanded Wartime Diplomacy & Espionage (proxy wars, backchannel) | off-ramps; consequence |
| §15 Galactic Economic & Trade Network (war scarcity / recovery booms) | emergent consequence |
| §16 Expanded Intelligence AI Strategy (threat assessment, long-term planning) | authentic decisions |

And the **decision substrate already exists per leader**: each
`canon/L2/entities/<leader>/capsule/traits.json` carries `dominant_bias`,
`decision_style`, `traits`, `allegiance` (with cultural tradition), and
`reputation`/`relationships`. Example — Drenn Korvath: *"Zero-Sum Clan Calculus —
Every Gain by Another is a Loss to the Vorran; Honor Demands Open Contest,"*
allegiance *"Vorran Clans (Resonance Sculpture Cultural Tradition)."* We are not
inventing culture; we are **wiring culture that is already written into how
civilizations decide.**

---

## The destination: three pillars (the Pilot's three clauses)

### Pillar A — Conflict produces emergent results that interact coherently
A war must change the **map, the economy, and who rules** — and those changes
must feed the *next* round of decisions. Consequence with causal depth > 1.

### Pillar B — War is not the only off-ramp; diplomacy & culture are real systems
A conflict must be resolvable by **mediated settlement** that addresses
grievance, and **cultural ties / soft power** must be able to prevent or defuse
it — not just military suppression.

### Pillar C — Civilizations make authentic decisions
Choice driven by **culture, tradition, internal politics, and galactic power
dynamics** — so two factions in identical circumstances behave *differently*,
because of who they are.

**The loop we are building:** culture & politics (C) → choose war / diplomacy /
exchange (B) → consequences reshape the world (A) → new conditions → new
authentic choices (C). When that loop turns on its own, the galaxy is dynamic.

---

## Phase 0 — Foundation: instrument truth & the resolution hook (prerequisite)

The roundtable backlog (`dev_backlog.json`) is not separate from this plan — it
is its footing. Two items are load-bearing for everything downstream:

- **D1 (P0) — stability conflict term must reflect civil war.** We cannot judge
  whether diplomacy or culture *reduces* conflict if the headline metric is
  blind to conflict. Fix first; accept that reported stability drops (~0.38 →
  est. ~0.29) and re-baseline. *(Engine.)*
- **D4 (P1) — true insurgency resolution + onset rotation.** A conflict that can
  only end by suppression has no room for a diplomatic off-ramp. A real
  `RESOLVED` terminal state is the **hook Pillar B plugs into.**
- D2, D6, D9, D10 as previously scoped (counter semantics; the peaceful-renewal
  seed for Pillar B/C; attractor re-derivation; schema + seed panel + regression).

**Gate:** re-run the Observatory 240-cycle; confirm no regression to either
degeneracy after the metric becomes honest. The observatory test case is hereby
the **standing regression harness for the entire program** — every phase below
must pass it before merge.

---

## Phase 1 — Pillar B core: diplomacy as a second off-ramp

| ID | Name | Canon | Extend / New | What it does |
|---|---|---|---|---|
| **MECH-DIP-002** | Mediated Settlement | §11, §14 | New (hooks MECH-GOV-001 `negotiate`, D4 `RESOLVED`) | A grievance-addressing treaty can **end an insurgency/civil war** short of military victory; success scales with trust, grievance addressed, and mediator soft power |
| **MECH-DIP-003** | Treaty Enforcement & Consequence | §11 | New | Treaties bind; honoring builds trust, breaking causes trust collapse + grievance spike — so diplomacy carries real stakes |
| **MECH-CUL-001** | Cultural Exchange / Soft Power | §11, §12 | New | Cultural ties (shared/compatible traditions) lower onset, ease grievance, and **open diplomatic off-ramps that force alone cannot** |

**Success criterion (measured, not tuned):** *off-ramp diversity* — the fraction
of conflicts ended by settlement rather than suppression rises from **0%** to a
nonzero, seed-robust share; and cultural-tie strength inversely correlates with
onset. Report whatever emerges.

## Phase 2 — Pillar C: authentic civilizational decisions

| ID | Name | Canon | Extend / New | What it does |
|---|---|---|---|---|
| **MECH-GOV-002** | Culture-Weighted Decisions | §10, §16 | Extend MECH-GOV-001 | FactionDecisionModel weights actions by the leader's `traits.json` (`decision_style`, `dominant_bias`, cultural tradition) — a zero-sum clan and a mercantile compact choose **differently** under identical pressure |
| **MECH-GOV-003** | Internal Politics & Succession | §13 | New (uses `elite_support`, `institutional_control`, `scandals`) | Elite support + scandal drive coups / elections / turnover; new leaders shift policy — internal politics as a live driver |
| **MECH-POW-001** | Galactic Power Dynamics | §10, §16 | New | Factions weigh **relative** power, alliances, and threat — balancing vs bandwagoning vs deterrence against the strong |

**Success criterion:** *decision authenticity* — under a fixed scenario, action
distributions differ measurably by culture/decision_style (not just by strength);
leadership turnover occurs and visibly changes a faction's trajectory.

## Phase 3 — Pillar A: emergent, interacting consequence

| ID | Name | Canon | Extend / New | What it does |
|---|---|---|---|---|
| **MECH-TER-001** | Territorial Consequence | §12 | Extend MECH-REB-003 | War shifts territory/planetary control; control feeds economy and future onset — the map changes and the change matters |
| **MECH-ECO-001** | War Economy & Market Flux | §15 | New | Conflict drives scarcity then recovery booms; economy feeds capability and grievance — a war you can't afford ends differently |
| **MECH-CUL-002** | Assimilation vs Local Tradition | §12 | New | Holding alien territory forces assimilation (short-term control) vs tolerating tradition (long-term legitimacy) — a cultural cost to conquest |

**Success criterion:** *causal depth* — a war measurably alters territory,
economy, and/or leadership, and those alterations measurably change subsequent
outcomes (instrument causal-chain length > 1); the conflict cast **rotates**
(new onsets replace resolved ones) instead of 13 wounds reopening.

## Phase 4 — Integration: close the loop & re-certify

Wire the four subsystems so culture/politics → choice → consequence → new
conditions feed each other, then run an extended Observatory exercise with the
**new** dynamic-galaxy instruments (off-ramp mix, decision-authenticity spread,
causal depth, cast-rotation rate, bloc formation). Senior-staff roundtable
certifies *dynamism*, not just *control*. Update canon (registry, DRIFT_LOG,
chronicle, World Bible cross-refs) and the L2 mechanic registry.

---

## Sequencing & dependencies

```
Phase 0 (D1, D4 critical) ──┬─► Phase 1 (DIP-002/003, CUL-001)  ─┐
                            │                                    │
                            └─► Phase 2 (GOV-002/003, POW-001) ──┼─► Phase 4
                                                                 │   integration
                            ┌─► Phase 3 (TER-001, ECO-001, CUL-002)┘   + re-certify
                            │
        (Phase 3 may begin after Phase 0 D4; richest once 1 & 2 land)
```

- **Phase 0 is hard-blocking** — D1 (honest metric) and D4 (resolution hook)
  gate Pillars B and A respectively.
- Phases 1 and 2 are largely parallel; **B slightly leads** (an off-ramp is the
  most direct answer to the Pilot's clause) but is most meaningful once C makes
  *choosing* it authentic.
- Phase 3 deepens consequence; partially unblocked by D4, fully expressive after
  1 & 2.

## Risk register

| Risk | Mitigation |
|---|---|
| New couplings reintroduce a runaway attractor (we just escaped two) | Observatory 240-cycle gate after **every** phase; living-galaxy invariants must hold |
| Coefficient-forcing creeps back in under pressure to hit "dynamic" | Each MECH ships a *measured* success criterion, reported as-is; no target numbers |
| Culture wiring contradicts established entity canon | Each MECH passes `aurora-canon-reconciler`; traits.json is read, never overwritten |
| Scope sprawl (systems §9–16 are large) | Strict pillar mapping; defer §9 logistics / §15 shadow-economy depth unless a pillar needs them |

## Governance (per established pattern, every MECH)

Build + test in tracked `tools/` → annotate `l2_mechanic_registry` + `DRIFT_LOG`
→ chronicle atom → commit CanonRec → sync pin in `repo_registry.yaml` → receipt
in `reports/analysis/` → commit root. Engine-internal edits flagged for owner
clearance. Observatory regression gate green before merge.

## Definition of done (the whole program)

The galaxy is **dynamic** when, with no coefficient tuned toward it:
1. conflicts end by **multiple** authentic routes (war *and* settlement *and*
   cultural defusion), in a seed-robust mix;
2. identical conditions yield **different** behavior by different cultures;
3. a conflict's outcome **reshapes** the world and that reshaping **changes** what
   happens next (causal depth > 1, rotating cast, emergent blocs);
4. the Observatory certifies all of the above from instruments — and the living-
   galaxy control invariants still hold underneath.

_First action on approval: Phase 0 / D1 — make the stability conflict term
reflect civil war, then re-baseline and re-run the Observatory gate._

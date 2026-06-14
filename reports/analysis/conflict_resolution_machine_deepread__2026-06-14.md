# Deep Read — The Conflict-Resolution Machine & Its Graft onto Insurgencies

**Date:** 2026-06-14 | **Read:** original `26_Engine_1.2/engine.py` (1329 ln),
current `SIM_ENGINE_OUTPUTS/formulas.py` + `models.py`, Forge `rebellion.py` |
**Purpose:** specify how to give civil wars the resolution machine inter-faction
conflict already has — the engineering basis for Phase 0/D4 + Phase 1/MECH-DIP-002.

## 1. The machine that already exists (inter-faction conflict)

The original engine's `_evaluate_conflicts()` (engine.py:629) runs every active
conflict through a **graded de-escalation ladder** each tick:

```
p_deesc = calc_deescalation_probability(
    war_cost_a, war_cost_b,        # how much the war is costing each side
    stalemate_index,               # how stuck it is
    internal_pressure_a, _b,       # domestic pressure to end it
    mediation_available)           # is a mediator engaged?
effective_p = p_deesc + (leader.diplomacy_openness - 0.5)*0.1   # psychology
if rng.random() < effective_p:  # stochastic step DOWN the ladder
    OPEN_CONFLICT → STALEMATE → DEESCALATION → CEASEFIRE → NEGOTIATION → RESOLUTION
else if leader.escalation_threshold low:  # or step UP
    escalate()
# while OPEN_CONFLICT/STALEMATE: accrue war_cost, stalemate, casualties;
# leaders take war_pressure↑, war_losses↑, public_legitimacy↓
```

`calc_deescalation_probability` (formulas.py:42, "PR §5.2 Formula 1") is a clean
weighted sum, fully present in the current build:

```
P = 0.30·avg_war_cost + 0.25·stalemate_index + 0.25·avg_internal_pressure
  + 0.20·mediation_flag
  (forced ≥0.5 at total stalemate; ≥0.6 at catastrophic mutual cost)
```

This is a **complete, canon-grounded resolution model**: war-weariness
(`war_cost`, `stalemate`), domestic politics (`internal_pressure`), diplomacy
(`mediation_available`), and leader psychology (`diplomacy_openness`,
`escalation_threshold`), ending in a real terminal `RESOLUTION`. `mediation` is
switched on by `_handle_diplomatic_overture` / `_handle_mediation_offer` — the
diplomacy → resolution hook.

## 2. Why civil wars don't get it (the asymmetry)

The v3 insurgency model (`rebellion.py`) is a **separate** subsystem and only
ever moves one way toward force:

```
InsurgencyPhase: ORGANIZING → ACTIVE → ESCALATED → CIVIL_WAR
                 (+ SUPPRESSED when strength<thresh; RESOLVED defined, never set)
```

The transition logic is purely strength-based: `strength ≥ CIVIL_WAR_THRESHOLD`
→ CIVIL_WAR; `strength < floor` → SUPPRESSED. There is **no de-escalation
probability, no mediation, no negotiation, no settlement** — military
suppression (our MECH-SOC-002 war-weariness erodes strength toward SUPPRESSED) is
the only exit. Crucially `RESOLVED = "resolved"  # ended via negotiation or
victory` **is already declared** — the design intent was always there; it was
never wired. (Likewise `PEACEFUL_SECESSION` / negotiated-split outcomes are
declared, unwired.)

This is the root of all three roundtable findings: war is the only off-ramp
(no resolution path), the metric is blind to civil war (`insurgency_pressure`
never falls because nothing resolves it), and the same ~13 wounds reopen
(SUPPRESSED is "temporarily defeated," not ended — grievance survives).

## 3. The graft — every input already exists on the insurgency

`Insurgency` carries the exact fields `calc_deescalation_probability` needs.
The mapping is direct and requires **no new state**:

| de-escalation input | insurgency source |
|---|---|
| `war_cost_a` (the state's cost) | host `leader.war_pressure` + `turns_active` decay |
| `war_cost_b` (the insurgents' cost) | insurgent attrition: `1 − insurgent_strength`, scaled by suppression |
| `stalemate_index` | protraction: `min(1, turns_active / N)` × territory-stability |
| `internal_pressure_a/b` | host grievance: `(economic_grievance + political_grievance)/2`; war-weariness from MECH-SOC-002 |
| `mediation_available` | a settlement/negotiation event vs the host (MECH-GOV-001 `negotiate`, or a mediator faction) |
| `diplomacy_openness` modifier | host `leader.diplomacy_openness` (field exists) |

Then run the **same ladder pattern** on the insurgency:

```
CIVIL_WAR → ESCALATED → ACTIVE → (settlement reached) → RESOLVED   # retire it
```

with the decisive difference that **RESOLVED addresses grievance**: on
resolution, reduce the host's `economic_grievance`/`political_grievance` (and
optionally cede autonomy / trigger `PEACEFUL_SECESSION`) so the wound *closes*
instead of re-opening. SUPPRESSED (force) leaves grievance intact → recurs;
RESOLVED (settlement) spends grievance → the conflict cast can finally rotate.

## 4. Two concrete mechanics fall out

- **D4 / MECH-REB (resolution path)** — add a de-escalation evaluation to the
  rebellion tick using `calc_deescalation_probability` (already imported-able
  from `formulas.py`), and actually assign `RESOLVED`. This is the minimal,
  proven-pattern fix; it does not need diplomacy to exist yet (war-weariness +
  stalemate alone can resolve a grinding insurgency, which is realistic).
- **MECH-DIP-002 / Mediated Settlement** — wire `mediation_available` from a
  negotiation/overture against the host (porting `_handle_diplomatic_overture`'s
  mediation enable), so diplomacy becomes a *faster, grievance-cheaper* off-ramp
  than grinding to stalemate. This is the "war is not the only off-ramp" pillar,
  built on the conflict layer's existing mediation hook.

**MECH-DIP-003 (treaty enforcement) is already implemented** for the conflict
layer (`calc_treaty_breach_score`, `is_treaty_breach`, `TreatyPhase.COLLAPSED`,
`_handle_treaty_violation`) — a settlement can register as a `TreatyState` and
inherit breach/collapse consequences for free.

## 5. Recovery provenance (confirms the pattern)

`engine.py:781 _peacetime_recovery()` — the original *"Phase 4.5: peacetime
recovery (the missing half)"* — restores factions at peace, exactly what we
re-derived as MECH-SOC-005. This is a second proof that the foundational engine
already held the systems we've been rebuilding; reading it first would have
saved that work, and reading it now de-risks the rest.

## 6. Recommended build order (feeds the revised plan)

1. **Recover/verify** `formulas.py`/`models.py` completeness (full copies in
   `SIM_ENGINE_OUTPUTS/` and v2.0 staging) — make `calc_deescalation_probability`
   importable to the rebellion tick.
2. **D1** (honest conflict metric) — unchanged P0; now also fold
   `insurgency_pressure` so a *resolving* insurgency visibly relieves stability.
3. **D4 via the graft** — insurgency de-escalation ladder → `RESOLVED` with
   grievance spend. Re-run Observatory gate (expect cast rotation, lower chronic
   `insurgency_pressure`).
4. **MECH-DIP-002** — mediation hook → settlement as the faster off-ramp.
5. Continue Pillars C/A as planned, now on a galaxy where conflict can actually
   end.

_No code changed in this read. Line references against the files as of this date._

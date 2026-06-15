#!/usr/bin/env python3
"""
gumas_memory_run.py — wire MECH-GOV-001 into the live GUMAS engine.

Closes the design->code->engine loop: runs the GUMASAdvancedEngine turn by
turn, harvests each turn's faction events (treaty breaches = betrayals,
conflicts = attacks, ratified treaties = alliances) into MECH-GOV-001 episodic
memory, computes each faction's memory-driven disposition toward the others,
and writes it back into the engine's `trust_scores` — which the base engine
already consults for treaty-breach and mediation evaluation. So memory enriches
the engine's existing trust signal rather than rewriting its internals.

Emergence principle: nothing here scripts outcomes. Factions simply *remember
and adapt*; whatever de-escalation or hardening emerges is the engine's, kept
coherent by being driven only by events that actually happened.

Usage:
    python3 tools/gumas_memory_run.py --turns 50 --seed 42      # A/B compare
    python3 tools/gumas_memory_run.py --turns 50 --seed 42 --out-json /tmp/x.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ENGINE_DIR = REPO_ROOT / "GUMAS_SIM_2.5" / "SIM_ENGINE_OUTPUTS"
sys.path.insert(0, str(ENGINE_DIR))
sys.path.insert(0, str(REPO_ROOT / "tools"))

from mech_gov_001 import (  # noqa: E402
    AssimilationModel,
    ComplacencyModel,
    CultureModel,
    DiplomaticStabilityModel,
    FactionDecisionModel,
    InsurgencyResolutionModel,
    MediationModel,
    PopulationGrievanceModel,
    PostWarRecoveryModel,
    PowerDynamicsModel,
    SuccessionModel,
    TerritorialConsequenceModel,
    TreatyEnforcementModel,
    WarEconomyModel,
    WarWearinessModel,
)
from gumas_consequence_layer import ConsequenceLayer  # noqa: E402

# MECH-GOV-003 installs a new regime's culture by setting the leader's
# dominant_bias to a real engine BiasType (the engine reads it descriptively).
try:  # pragma: no cover - exercised via the integration harness
    from models import BiasType  # noqa: E402
    _BIAS_ENUM = {
        "zero_sum": BiasType.ZERO_SUM, "fear_based": BiasType.FEAR_BASED,
        "sunk_cost": BiasType.SUNK_COST, "hyper_rationalism": BiasType.HYPER_RATIONALISM,
        "status_quo": BiasType.STATUS_QUO, "survivorship": BiasType.SURVIVORSHIP,
    }
except Exception:  # noqa: BLE001 - standalone (engine off path): fall back to strings
    _BIAS_ENUM = {k: k for k in
                  ("zero_sum", "fear_based", "sunk_cost", "hyper_rationalism",
                   "status_quo", "survivorship")}


def _writeback_complacency(compl: ComplacencyModel, state, v3) -> None:
    """MECH-SOC-006: long peace breeds complacency/corruption that erodes
    governance legitimacy, re-enabling unrest — preventing the permanent-peace
    fixed point. Serious conflict resets a faction's complacency (renewal)."""
    if v3 is None:
        return
    at_war = set()
    for ins in getattr(v3, "insurgencies", []):
        if _phase(ins) in ("civil_war", "escalated"):
            at_war.add(ins.host_faction_id)
    for fid, fac in state.factions.items():
        complacency = compl.update(fid, fid in at_war)
        if complacency <= 0:
            continue
        leader = state.leaders.get(fac.leader_id) if fac.leader_id else None
        if leader is not None:
            leader.public_legitimacy = round(max(
                0.05, float(leader.public_legitimacy) - compl.legitimacy_drag(complacency)), 4)
        # Corrupt mismanagement worsens living conditions -> rising stress
        # re-ignites unrest (onset, overcoming peacetime recovery).
        pop = getattr(v3, "population", {}).get(fid)
        if pop is not None:
            pop.housing_pressure = round(min(
                1.0, float(pop.housing_pressure) + compl.stress_pressure(complacency)), 4)
        # Corruption breeds strong resentment -> rebellions against a complacent
        # regime gain support + grievance, so they mature into civil wars
        # rather than fizzling. This is what turns the cycle.
        fuel = compl.insurgent_fuel(complacency)
        if fuel:
            for ins in getattr(v3, "insurgencies", []):
                if ins.host_faction_id == fid:
                    ins.popular_support = round(min(1.0, float(ins.popular_support) + fuel), 4)
                    ins.economic_grievance = round(min(1.0, float(getattr(ins, "economic_grievance", 0.5)) + fuel), 4)


def _writeback_recovery(recov: PostWarRecoveryModel, state, v3) -> None:
    """MECH-SOC-005: a faction at peace rebuilds population stability and
    governance legitimacy and eases its demographic stress drivers. Gated on
    peace — an active insurgency halts reconstruction."""
    if v3 is None:
        return
    # Reconstruction is halted only by *serious* conflict (civil war/escalated),
    # not by a minor insurgency a faction is already containing — otherwise the
    # constant churn of low-level insurgencies blocks recovery permanently.
    serious_war = {"civil_war", "escalated"}
    at_war = set()
    for ins in getattr(v3, "insurgencies", []):
        if _phase(ins) in serious_war:
            at_war.add(ins.host_faction_id)
    for fid, fac in state.factions.items():
        if fid in at_war:
            continue
        fac.population_stability = round(
            recov.toward(float(fac.population_stability), recov.POP_TARGET, recov.POP_RECOVERY_RATE), 4)
        leader = state.leaders.get(fac.leader_id) if fac.leader_id else None
        if leader is not None:
            leader.public_legitimacy = round(
                recov.toward(float(leader.public_legitimacy), recov.LEGIT_TARGET, recov.LEGIT_RECOVERY_RATE), 4)
        pop = getattr(v3, "population", {}).get(fid)
        if pop is not None:
            pop.housing_pressure = round(
                recov.ease_down(float(pop.housing_pressure), recov.HOUSING_TARGET, recov.DRIVER_RECOVERY_RATE), 4)
            pop.unemployment = round(
                recov.ease_down(float(getattr(pop, "unemployment", 0.15)), recov.UNEMPLOY_TARGET, recov.DRIVER_RECOVERY_RATE), 4)
            pop.food_security = round(
                recov.toward(float(getattr(pop, "food_security", 0.7)), recov.FOOD_TARGET, recov.DRIVER_RECOVERY_RATE), 4)

ACTIVE_WAR_PHASES = {"civil_war", "escalated", "active"}


def _writeback_consequences(cons: ConsequenceLayer, state, v3, intel_pressure: float) -> None:
    """Give the inert instability signals their downstream effects (lessons
    §2.1/§2.2/§2.4/§2.3): counter-intel response, conscription→capacity, onset
    dampener, fragmentation drag — all derived from state."""
    if v3 is None:
        return
    # Active insurgencies + max territory per host faction.
    wars: dict[str, int] = {}
    max_terr: dict[str, float] = {}
    for ins in getattr(v3, "insurgencies", []):
        if _phase(ins) in ACTIVE_WAR_PHASES:
            fid = ins.host_faction_id
            wars[fid] = wars.get(fid, 0) + 1
            max_terr[fid] = max(max_terr.get(fid, 0.0), float(getattr(ins, "territory_controlled", 0.0)))

    for fid, fac in state.factions.items():
        active = wars.get(fid, 0)
        # Conscription → military capacity (aids suppression).
        if active:
            fac.military_strength = round(
                cons.conscription_target(float(fac.military_strength), active), 4)
        # Onset dampener → legitimacy focus for the already-embattled.
        leader = state.leaders.get(fac.leader_id) if fac.leader_id else None
        if leader is not None and active:
            leader.public_legitimacy = round(min(
                1.0, float(leader.public_legitimacy) + cons.onset_dampen_bonus(active)), 4)
        # Fragmentation consequence → lost economic capacity.
        drag = cons.fragmentation_drag(max_terr.get(fid, 0.0))
        if drag:
            fac.economic_strength = round(max(0.05, float(fac.economic_strength) - drag), 4)

    # Counter-intel response surface → CI investment + residual cost.
    for fid, net in getattr(v3, "intel_networks", {}).items():
        net.counter_intel_strength = round(
            cons.ci_investment(float(net.counter_intel_strength), intel_pressure), 4)
        fac = state.factions.get(fid)
        if fac is not None:
            fac.economic_strength = round(max(
                0.05, float(fac.economic_strength)
                - cons.intel_econ_cost(net.counter_intel_strength, intel_pressure)), 4)


def _phase(ins) -> str:
    return getattr(getattr(ins, "phase", None), "value", str(getattr(ins, "phase", "")))


def _active_civil_wars(v3) -> int:
    if v3 is None:
        return 0
    return sum(1 for i in getattr(v3, "insurgencies", []) if _phase(i) in ("civil_war", "escalated"))


def _writeback_weariness(weary: WarWearinessModel, v3) -> int:
    """Erode war-weary popular support (and, when deeply weary, strength) so the
    engine's own dynamics can drain an entrenched insurgency to SUPPRESSED.

    Gated on *mature* conflict (civil war / escalated) only: a nascent
    insurgency must be allowed to grow into a civil war, or conflict can never
    form — the galaxy needs a wound, not just a heal. War-weariness then
    resolves it once it has run its course."""
    if v3 is None:
        return 0
    touched = 0
    for ins in getattr(v3, "insurgencies", []):
        active = _phase(ins) in ("civil_war", "escalated")
        w = weary.weary(ins.insurgency_id, active)
        if not active or w <= 0:
            continue
        support_erosion, strength_attrition, territory_attrition = weary.erosion(w)
        ins.popular_support = max(0.0, ins.popular_support - support_erosion)
        ins.insurgent_strength = max(0.0, ins.insurgent_strength - strength_attrition)
        ins.territory_controlled = max(0.0, float(getattr(ins, "territory_controlled", 0.0)) - territory_attrition)
        touched += 1
    return touched


def _writeback_mediation(med: MediationModel, state, v3) -> int:
    """MECH-DIP-002: open a diplomatic off-ramp on each insurgency whose host has
    a credible third-party mediator — a peaceful neighbour it mutually trusts —
    found in the live trust network. Sets `mediation_available`, which the
    resolution de-escalation formula rewards (the mediation bonus), so a
    well-connected regime settles faster and cheaper than a distrusted one that
    must grind to exhaustion. Returns how many insurgencies have a broker."""
    if v3 is None:
        return 0
    insurgencies = getattr(v3, "insurgencies", None)
    if not insurgencies:
        return 0
    # A faction fighting its own serious war can't broker peace elsewhere.
    busy = {ins.host_faction_id for ins in insurgencies
            if _phase(ins) in ("civil_war", "escalated")}
    trust_by = {fid: (getattr(fac, "trust_scores", {}) or {})
                for fid, fac in state.factions.items()}
    brokered = 0
    for ins in insurgencies:
        mediator = med.find_mediator(ins.host_faction_id, trust_by, busy)
        ins.mediation_available = mediator is not None
        ins.mediator_id = mediator
        if mediator is not None:
            brokered += 1
    return brokered


def _writeback_treaties(treaty: TreatyEnforcementModel, state, v3) -> int:
    """MECH-DIP-003: a settled peace binds and can break. As the complacency
    cycle rebuilds a host's stress during peace, its accord is strained; a
    mediated accord (clear terms) resists, an exhaustion peace (vague) frays.
    On breach, grievance resurges (renewed conflict) and — if a broker
    guaranteed it — host<->mediator trust collapses, burning the broker's
    credibility. Returns the number of accords broken this turn."""
    if v3 is None:
        return 0
    broken = 0
    pops = getattr(v3, "population", {})
    for host in list(treaty.accords.keys()):
        fac = state.factions.get(host)
        if fac is None:
            treaty.forget(host)
            continue
        accord = treaty.accords[host]
        mediator = accord.get("mediator")
        ts = getattr(fac, "trust_scores", {}) or {}
        trust_with_mediator = float(ts.get(mediator, 0.5)) if mediator else 0.5
        pop = pops.get(host)
        current_grievance = float(getattr(pop, "demographic_stress", accord["base"])) if pop else accord["base"]
        result = treaty.check(host, current_grievance, trust_with_mediator)
        if result is None:
            continue
        broken += 1
        # Renewed conflict: the betrayed peace re-inflames grievance.
        if pop is not None:
            pop.demographic_stress = round(min(
                1.0, float(getattr(pop, "demographic_stress", 0.3)) + treaty.TRUST_BURN), 4)
        leader = state.leaders.get(fac.leader_id) if fac.leader_id else None
        if leader is not None:
            leader.public_legitimacy = round(max(
                0.05, float(leader.public_legitimacy) - 0.03), 4)
        # A broken brokered peace burns the broker's credibility (both directions),
        # so future peace is harder to broker for this host.
        if mediator is not None:
            mfac = state.factions.get(mediator)
            if isinstance(getattr(fac, "trust_scores", None), dict) and mediator in fac.trust_scores:
                fac.trust_scores[mediator] = round(max(
                    0.0, float(fac.trust_scores[mediator]) - treaty.TRUST_BURN), 4)
            if mfac is not None and isinstance(getattr(mfac, "trust_scores", None), dict) and host in mfac.trust_scores:
                mfac.trust_scores[host] = round(max(
                    0.0, float(mfac.trust_scores[host]) - treaty.TRUST_BURN), 4)
    return broken


def _writeback_territory(terr: "TerritorialConsequenceModel", state, v3) -> None:
    """MECH-TER-001: war reshapes the map and the economy persistently. A faction
    with a mature civil war permanently loses ground scaled by the insurgency's
    territorial hold; a faction at peace slowly reclaims contested ground. The
    permanent loss caps the faction's economic_potential (the ceiling the engine
    grows economic_strength toward), so a war's territorial outcome lowers the
    faction's economy — and thus its galactic power — for the rest of the run."""
    if v3 is None:
        return
    # the intensity of each faction's mature civil wars this turn — a civil war
    # devastates the economy whether or not the rebels formally "hold" ground
    # (war-weariness keeps their territory near zero), so scar by war severity.
    intensity: dict[str, float] = {}
    for ins in getattr(v3, "insurgencies", []):
        if _phase(ins) in ("civil_war", "escalated"):
            fid = ins.host_faction_id
            sev = max(float(getattr(ins, "insurgent_strength", 0.0)),
                      float(getattr(ins, "territory_controlled", 0.0)))
            intensity[fid] = intensity.get(fid, 0.0) + sev
    for fid, fac in state.factions.items():
        if fid in intensity:
            terr.scar(fid, intensity[fid])
        else:
            terr.reclaim(fid)
        # Territory caps the economic ceiling — a permanent, propagating loss.
        ceiling = terr.economic_ceiling(fid)
        if float(getattr(fac, "economic_potential", 1.0)) > ceiling:
            fac.economic_potential = ceiling
        # economic_strength can't exceed the (now lower) potential.
        if float(getattr(fac, "economic_strength", 0.5)) > ceiling:
            fac.economic_strength = round(ceiling, 4)


def _writeback_assimilation(assim: "AssimilationModel", terr, state, v3):
    """MECH-CUL-002: holding restive, recently-reconquered ground (TER-001's
    contested territory) is a cultural choice. An assimilationist culture imposes
    its identity and breeds identity grievance (demographic stress → future
    separatist unrest); a tolerant culture preserves local tradition and earns a
    little legitimacy back. Returns (assimilations, tolerations) — the two sides
    of the cultural cost of conquest exercised this turn."""
    if v3 is None or terr is None:
        return (0, 0)
    pops = getattr(v3, "population", {})
    assimilations = tolerations = 0
    for fid, fac in state.factions.items():
        restive = terr.contested.get(fid, 0.0)
        if restive <= 0.01:
            continue
        leader = state.leaders.get(fac.leader_id) if fac.leader_id else None
        pol = assim.policy(getattr(leader, "dominant_bias", None))
        if pol == "assimilate":
            assimilations += 1
            pop = pops.get(fid)
            if pop is not None:
                pop.demographic_stress = round(min(
                    1.0, float(getattr(pop, "demographic_stress", 0.3))
                    + assim.identity_grievance(restive)), 4)
        elif pol == "tolerate" and leader is not None:
            tolerations += 1
            leader.public_legitimacy = round(min(
                1.0, float(leader.public_legitimacy) + assim.TOLERATE_LEGITIMACY), 4)
    return (assimilations, tolerations)


def _writeback_economy(eco: "WarEconomyModel", state, v3) -> None:
    """MECH-ECO-001: a faction's economy booms and busts with its wars, and the
    economy feeds back into unrest. War scarcity suppresses output; peace drives
    a recovery boom toward the (territory-capped) ceiling; a depressed economy
    deepens demographic stress (-> unrest), a booming one eases it — closing the
    loop war -> economic depression -> grievance -> war."""
    if v3 is None:
        return
    at_war = {ins.host_faction_id for ins in getattr(v3, "insurgencies", [])
              if _phase(ins) in ("civil_war", "escalated")}
    pops = getattr(v3, "population", {})
    for fid, fac in state.factions.items():
        es = float(getattr(fac, "economic_strength", 0.5))
        ep = float(getattr(fac, "economic_potential", 1.0))
        fac.economic_strength = eco.flux(es, ep, fid in at_war)
        # economy -> unrest feedback
        delta = eco.stress_delta(eco.health(fac.economic_strength, ep))
        if delta:
            pop = pops.get(fid)
            if pop is not None:
                pop.demographic_stress = round(min(
                    1.0, max(0.0, float(getattr(pop, "demographic_stress", 0.3)) + delta)), 4)


def _writeback_power(power: "PowerDynamicsModel", state) -> Optional[str]:
    """MECH-POW-001: react to the galactic balance of power. Find the hegemon
    (most powerful faction); every other faction realigns its trust by how
    threatened it is and by its culture — balancers (proud/defensive) pull trust
    away from the hegemon and toward each other, bandwagoners (pragmatic/
    survivalist) draw closer to the hegemon. Operates on the live trust network.
    Returns the hegemon's faction id (telemetry)."""
    facs = list(state.factions.items())
    if len(facs) < 3:
        return None
    pw = {fid: power.power(getattr(fac, "military_strength", 0.5),
                           getattr(fac, "economic_strength", 0.5),
                           getattr(fac, "technology_level", 0.5))
          for fid, fac in facs}
    hegemon = max(pw, key=pw.get)
    others = [fid for fid, _ in facs if fid != hegemon]
    for fid in others:
        fac = state.factions[fid]
        ts = getattr(fac, "trust_scores", None)
        if not isinstance(ts, dict):
            continue
        threat = pw[hegemon] - pw[fid]
        if threat < power.THREAT_FLOOR:
            continue
        leader = state.leaders.get(fac.leader_id) if fac.leader_id else None
        stance = power.stance(getattr(leader, "dominant_bias", None))
        if stance == "balance":
            if hegemon in ts:
                ts[hegemon] = round(max(0.0, float(ts[hegemon]) - power.REALIGN_RATE * threat), 4)
            # coalition: warm to fellow non-hegemons
            for o in others:
                if o != fid and o in ts:
                    ts[o] = round(min(1.0, float(ts[o]) + power.COALITION_RATE * threat), 4)
        elif stance == "bandwagon":
            if hegemon in ts:
                ts[hegemon] = round(min(1.0, float(ts[hegemon]) + power.REALIGN_RATE * threat), 4)
    return hegemon


def _writeback_succession(succ: SuccessionModel, state, v3) -> int:
    """MECH-GOV-003: when a leader's grip (legitimacy minus scandal + war-pressure
    drag) collapses, the regime falls — by coup in a militarized polity, by
    election in an economic one. The successor starts with a fresh mandate
    (legitimacy bump, scandals cleared) and a shifted culture (new dominant_bias),
    so internal politics visibly changes the faction's trajectory. A coup also
    bumps demographic stress (it destabilizes). Returns successions this turn."""
    if v3 is None:
        return 0
    pops = getattr(v3, "population", {})
    n = 0
    for fid, fac in state.factions.items():
        leader = state.leaders.get(fac.leader_id) if fac.leader_id else None
        if leader is None:
            continue
        militarized = float(getattr(fac, "military_strength", 0.5)) >= float(getattr(fac, "economic_strength", 0.5))
        res = succ.step(
            fid,
            float(getattr(leader, "public_legitimacy", 0.5)),
            float(getattr(leader, "scandals", 0) or 0),
            float(getattr(leader, "war_pressure", 0.0) or 0.0),
            militarized,
        )
        if res is None:
            continue
        n += 1
        # Install the new regime: fresh mandate, cleared scandals, shifted culture.
        leader.dominant_bias = _BIAS_ENUM.get(res["new_bias"], getattr(leader, "dominant_bias", None))
        leader.public_legitimacy = round(float(res["legit"]), 4)
        try:
            leader.scandals = 0
        except Exception:  # noqa: BLE001
            pass
        if res["stress"]:
            pop = pops.get(fid)
            if pop is not None:
                pop.demographic_stress = round(min(
                    1.0, float(getattr(pop, "demographic_stress", 0.3)) + res["stress"]), 4)
    return n


def _writeback_resolution(resolver: InsurgencyResolutionModel, state, v3, treaty=None, culture=None):
    """MECH-REB-004: give civil wars the de-escalation→settlement off-ramp the
    inter-faction conflict layer already has. A grinding, costly, stalemated
    insurgency whose host population pressures it to end can reach a negotiated
    SETTLEMENT: the movement is retired (the realization of the canon-declared
    InsurgencyPhase.RESOLVED — the engine has no terminal/removal path of its
    own) and the grievance that drove it is spent (eased demographic stress +
    restored legitimacy — a peaceful renewal). A *mediated* settlement (a broker
    was engaged, MECH-DIP-002) is more durable — it spends more grievance and
    restores more legitimacy than a peace won by exhaustion. The cause addressed,
    the conflict cast can rotate. Returns (settled, mediated_settled) this turn."""
    if v3 is None:
        return (0, 0)
    insurgencies = getattr(v3, "insurgencies", None)
    if not insurgencies:
        return (0, 0)
    settleable = {"active", "escalated", "civil_war"}
    settled = mediated = 0
    for ins in list(insurgencies):
        if _phase(ins) not in settleable:
            continue
        if int(getattr(ins, "turns_active", 0)) < resolver.GRACE_TURNS:
            continue
        fid = ins.host_faction_id
        fac = state.factions.get(fid)
        leader = state.leaders.get(fac.leader_id) if fac and fac.leader_id else None
        host_grievance = (float(getattr(ins, "economic_grievance", 0.5))
                          + float(getattr(ins, "political_grievance", 0.5))) / 2.0
        was_mediated = bool(getattr(ins, "mediation_available", False))
        p = resolver.deescalation_p(
            host_war_pressure=float(getattr(leader, "war_pressure", 0.3)) if leader else 0.3,
            insurgent_strength=float(getattr(ins, "insurgent_strength", 0.3)),
            repression_level=float(getattr(ins, "repression_level", 0.3)),
            turns_active=int(getattr(ins, "turns_active", 0)),
            host_grievance=host_grievance,
            popular_support=float(getattr(ins, "popular_support", 0.3)),
            diplomacy_openness=float(getattr(leader, "diplomacy_openness", 0.5)) if leader else 0.5,
            mediation_available=was_mediated,
        )
        # MECH-GOV-002: the host's culture colours the settle-or-grind decision —
        # a zero-sum clan resists a negotiated end, a hyper-rational order takes it.
        if culture is not None and leader is not None:
            p = max(0.0, min(1.0, p + culture.settlement_lean(getattr(leader, "dominant_bias", None))))
        if not resolver.advance(ins.insurgency_id, p):
            continue
        # SETTLEMENT — retire the movement and spend the grievance that drove it.
        try:
            insurgencies.remove(ins)
        except ValueError:
            pass
        resolver.forget(ins.insurgency_id)
        settled += 1
        # A brokered peace addresses root causes better than exhaustion does.
        bonus = 1.5 if was_mediated else 1.0
        if was_mediated:
            mediated += 1
        pop = getattr(v3, "population", {}).get(fid)
        if pop is not None:
            pop.demographic_stress = round(max(
                0.0, float(getattr(pop, "demographic_stress", 0.3)) - resolver.STRESS_RELIEF * bonus), 4)
            pop.housing_pressure = round(max(
                0.0, float(getattr(pop, "housing_pressure", 0.3)) - resolver.GRIEVANCE_RELIEF * 0.5 * bonus), 4)
        if leader is not None:
            # A settled peace is legitimacy-restoring — the *peaceful* renewal
            # path (D6), distinct from the complacency war-purge.
            leader.public_legitimacy = round(min(
                1.0, float(leader.public_legitimacy) + resolver.LEGIT_RESTORE * bonus), 4)
        # MECH-DIP-003: register the peace as a binding accord against the floor it
        # just established (post-relief stress). As complacency rebuilds stress
        # above that floor the accord is strained; a heavy backslide breaks it.
        if treaty is not None:
            base_floor = float(getattr(pop, "demographic_stress", host_grievance)) if pop is not None else host_grievance
            treaty.register(fid, getattr(ins, "mediator_id", None) if was_mediated else None, base_floor)
    return (settled, mediated)


# Blend weight: how strongly memory disposition pulls the engine's trust score.
MEMORY_PULL = 0.30
# How strongly remembered grievance pulls the persistent housing-pressure driver.
SOC_PULL = 0.25
# How strongly the DSI capacity gates the persistent legitimacy that feeds onset.
DSI_PULL = 0.30


def _writeback_dsi(dsi: DiplomaticStabilityModel, soc, state) -> dict:
    """MECH-SOC-003 onset gate: a cohesive/prosperous faction earns governance
    legitimacy (fewer insurgencies begin); a militarized/corrupt/poor one loses
    it. Writes the DSI capacity into the persistent leader.public_legitimacy
    that the rebellion onset formula reads (legitimacy_weight 0.30)."""
    caps = []
    for fid, fac in state.factions.items():
        leader = state.leaders.get(fac.leader_id) if fac.leader_id else None
        if leader is None:
            continue
        grievance = soc.grievance_pressure(fid) if soc else 0.0
        cap = dsi.capacity_for(
            economic=float(getattr(fac, "economic_strength", 0.5)),
            cohesion=float(getattr(fac, "population_stability", 0.7)),
            political_unity=float(getattr(fac, "reputation", 0.7)),
            militarization=float(getattr(fac, "military_strength", 0.5)),
            institutional_control=float(getattr(leader, "institutional_control", 0.5)),
            grievance=grievance,
        )
        target = 0.45 + 0.35 * cap     # capacity -> legitimacy target [0.45, 0.80]
        cur = float(getattr(leader, "public_legitimacy", 0.7))
        leader.public_legitimacy = round((1 - DSI_PULL) * cur + DSI_PULL * target, 4)
        caps.append(cap)
    return {"mean_capacity": round(sum(caps) / len(caps), 3) if caps else 0.0}


def _harvest_grievance(soc: PopulationGrievanceModel, v3) -> dict:
    """Record this turn's social events (hardship/repression/relief) per faction."""
    counts = {"hardship": 0, "repression": 0, "relief": 0}
    if v3 is None:
        return counts
    hosting = {}
    for ins in getattr(v3, "insurgencies", []):
        hosting[ins.host_faction_id] = hosting.get(ins.host_faction_id, 0) + 1
    for fid, pop in getattr(v3, "population", {}).items():
        stress = float(getattr(pop, "demographic_stress", 0.0))
        if hosting.get(fid):
            soc.record(fid, "repression", importance=6.0)
            counts["repression"] += 1
        if stress > 0.5:
            soc.record(fid, "hardship", importance=4.0 + 6.0 * (stress - 0.5))
            counts["hardship"] += 1
        elif stress < 0.3:
            soc.record(fid, "relief", importance=4.0)
            counts["relief"] += 1
    return counts


def _writeback_grievance(soc: PopulationGrievanceModel, v3) -> None:
    """Carry remembered grievance into the persistent housing-pressure driver,
    so a population that suffered keeps elevated stress after the cause fades."""
    if v3 is None:
        return
    for fid, pop in getattr(v3, "population", {}).items():
        gp = soc.grievance_pressure(fid)
        cur = float(getattr(pop, "housing_pressure", 0.3))
        pop.housing_pressure = max(0.0, min(1.0, (1 - SOC_PULL) * cur + SOC_PULL * gp))


def _harvest(mech: FactionDecisionModel, state, prev_breach: dict, seen_conflicts: set,
             seen_treaties: set) -> dict:
    """Record this turn's faction events into episodic memory. Returns counts."""
    counts = {"betrayals": 0, "attacks": 0, "alliances": 0}

    for tid, tr in state.treaties.items():
        total_breaches = sum(tr.breach_count.values()) if tr.breach_count else 0
        if total_breaches > prev_breach.get(tid, 0):
            violators = [f for f, c in (tr.breach_count or {}).items() if c > 0]
            for v in violators:
                for p in tr.parties:
                    if p != v:
                        mech.record_event(p, "broken_treaty", about=v, importance=7.0)
                        counts["betrayals"] += 1
            prev_breach[tid] = total_breaches
        elif getattr(tr, "is_active", False) and total_breaches == 0 and tid not in seen_treaties:
            seen_treaties.add(tid)
            prev_breach[tid] = 0
            for p in tr.parties:
                for o in tr.parties:
                    if p != o:
                        mech.record_event(p, "alliance", about=o, importance=5.0)
                        counts["alliances"] += 1

    for cid, cf in state.conflicts.items():
        if cid not in seen_conflicts:
            seen_conflicts.add(cid)
            for p in cf.parties:
                for o in cf.parties:
                    if p != o:
                        mech.record_event(p, "attack", about=o, importance=6.0)
                        counts["attacks"] += 1
    return counts


def _writeback(mech: FactionDecisionModel, state) -> int:
    """Blend each faction's memory disposition into its engine trust_scores.

    Realizes both canon rules in the engine's trust signal:
      - memory disposition (betrayal hardens, alliance softens) sets the base;
      - a militarily weak faction is nudged toward cooperation ("weakness
        increases the odds of negotiation") so it seeks deals rather than war.
    """
    updated = 0
    for fid, fac in state.factions.items():
        store = mech.stores.get(fid)
        if not store:
            continue
        mil = float(getattr(fac, "military_strength", 0.5))
        weak = mil < mech.weak_threshold
        subjects = {m.about for m in store.memories}
        for other in subjects:
            if other not in state.factions or other == fid:
                continue
            disp, _ = mech.disposition(fid, other)
            target = 0.5 + disp * 0.5  # disposition [-1,1] -> trust [0,1]
            if weak:
                # the weak negotiate: pull trust up toward cooperation
                target = target + (1.0 - target) * (mech.weak_threshold - mil)
            cur = fac.trust_scores.get(other, 0.5)
            fac.trust_scores[other] = round((1 - MEMORY_PULL) * cur + MEMORY_PULL * target, 4)
            updated += 1
    return updated


def run(seed: int, turns: int, memory_on: bool) -> dict:
    from engine_advanced import GUMASAdvancedEngine

    engine = GUMASAdvancedEngine(seed=seed)
    engine.init_scenario()
    mech = FactionDecisionModel(seed=seed) if memory_on else None
    soc = PopulationGrievanceModel(seed=seed) if memory_on else None
    dsi = DiplomaticStabilityModel() if memory_on else None
    weary = WarWearinessModel() if memory_on else None
    cons = ConsequenceLayer() if memory_on else None
    recov = PostWarRecoveryModel() if memory_on else None
    compl = ComplacencyModel() if memory_on else None
    resolver = InsurgencyResolutionModel(seed=seed) if memory_on else None
    med = MediationModel() if memory_on else None
    treaty = TreatyEnforcementModel(seed=seed) if memory_on else None
    culture = CultureModel() if memory_on else None
    succ = SuccessionModel(seed=seed) if memory_on else None
    power = PowerDynamicsModel() if memory_on else None
    terr = TerritorialConsequenceModel() if memory_on else None
    eco = WarEconomyModel() if memory_on else None
    assim = AssimilationModel() if memory_on else None
    prev_breach: dict = {}
    seen_conflicts: set = set()
    seen_treaties: set = set()
    traj: list[dict] = []
    harvest_total = {"betrayals": 0, "attacks": 0, "alliances": 0,
                     "hardship": 0, "repression": 0, "relief": 0}

    for t in range(turns):
        res = engine.step()
        d = res.to_dict()
        state = engine.get_state()
        v3 = engine.get_v3_state()
        if memory_on:
            mech.tick(1)
            soc.tick(1)
            c = _harvest(mech, state, prev_breach, seen_conflicts, seen_treaties)
            cg = _harvest_grievance(soc, v3)
            for k in c:
                harvest_total[k] += c[k]
            for k in cg:
                harvest_total[k] += cg[k]
            _writeback(mech, state)
            _writeback_grievance(soc, v3)
            _writeback_dsi(dsi, soc, state)
            _writeback_weariness(weary, v3)
            intel_pressure = min(1.0, d.get("v3_result", {}).get("intelligence_ops", 0) / 15.0)
            _writeback_consequences(cons, state, v3, intel_pressure)
            _writeback_recovery(recov, state, v3)
            _writeback_complacency(compl, state, v3)
            _writeback_mediation(med, state, v3)
            _writeback_resolution(resolver, state, v3, treaty, culture)
            _writeback_treaties(treaty, state, v3)
            _writeback_succession(succ, state, v3)
            _writeback_territory(terr, state, v3)
            _writeback_assimilation(assim, terr, state, v3)
            _writeback_economy(eco, state, v3)
            _writeback_power(power, state)
        traj.append({
            "turn": d["turn"],
            "stability": d["stability_index"],
            "risk": d["risk_index"],
            "conflicts": len(state.conflicts),
            "insurgencies": _active_civil_wars(v3),
        })

    final = traj[-1]
    return {
        "memory_on": memory_on, "seed": seed, "turns": turns,
        "final_stability": final["stability"], "final_risk": final["risk"],
        "final_conflicts": final["conflicts"],
        "final_insurgencies": final["insurgencies"],
        "mean_risk": round(sum(p["risk"] for p in traj) / len(traj), 4),
        "peak_conflicts": max(p["conflicts"] for p in traj),
        "peak_insurgencies": max(p["insurgencies"] for p in traj),
        "harvested": harvest_total,
        "trajectory": traj,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--turns", type=int, default=50)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out-json", default=None)
    args = p.parse_args()

    print(f"GUMAS x MECH-GOV-001 — seed {args.seed}, {args.turns} turns (A/B)")
    baseline = run(args.seed, args.turns, memory_on=False)
    memory = run(args.seed, args.turns, memory_on=True)

    def line(label, r):
        print(f"  {label:8} | stability {r['final_stability']:.3f} | "
              f"risk {r['final_risk']:.3f} | mean risk {r['mean_risk']:.3f} | "
              f"insurgencies {r['final_insurgencies']} (peak {r['peak_insurgencies']}) | "
              f"conflicts {r['final_conflicts']}")
    print("\nResults:")
    line("baseline", baseline)
    line("memory", memory)
    h = memory["harvested"]
    print(f"\n  diplomacy memory: {h['betrayals']} betrayals, {h['attacks']} attacks, "
          f"{h['alliances']} alliances")
    print(f"  social memory:    {h['hardship']} hardship, {h['repression']} repression, "
          f"{h['relief']} relief -> population grievance")
    ds = memory["final_stability"] - baseline["final_stability"]
    dr = memory["final_risk"] - baseline["final_risk"]
    di = memory["final_insurgencies"] - baseline["final_insurgencies"]
    print(f"  delta (memory - baseline): stability {ds:+.3f}, risk {dr:+.3f}, "
          f"insurgencies {di:+d}, conflicts {memory['final_conflicts'] - baseline['final_conflicts']:+d}")

    if args.out_json:
        Path(args.out_json).write_text(json.dumps(
            {"baseline": baseline, "memory": memory}, indent=2) + "\n")
        print(f"\n  wrote {args.out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

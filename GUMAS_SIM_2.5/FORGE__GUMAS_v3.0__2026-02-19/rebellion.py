#!/usr/bin/env python3
"""
GUMAS v3.0 — Rebellion & State Fragmentation Module
====================================================
Anchor: GUMAS-ENGINE-REBELLION-V3
Seed:   EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP:    L2_ENGINE_V3
Version: 3.0.0

Models insurgency onset, civil war escalation, separatist movements,
and state fragmentation. Internal conflicts are distinct from
interstate wars (handled in v2.0 combat.py) and interact with
population dynamics, surveillance, and economic stress.

High demographic stress (population.py) + low government legitimacy
(leader.public_legitimacy) → elevated rebellion onset probability.
Active surveillance (intelligence.py) suppresses onset but increases
severity if rebellion succeeds.

Subsystem roles in tick lifecycle:
    Phase 20 — Rebellion Tick (final v3.0 phase, after Intel Tick)

Formulas:
    calc_rebellion_onset_probability()  — probability a rebellion begins
    calc_insurgency_strength()          — combat effectiveness of rebels
    calc_state_fragmentation_risk()     — risk of faction splitting
    calc_repression_effectiveness()     — how well the state suppresses unrest
    calc_civil_war_escalation()         — probability insurgency → full civil war

Design principles:
    - Stdlib only; no numpy/scipy
    - Rebellions are modelled as new internal ConflictState objects
    - State fragmentation creates new FactionState entries (splinter factions)
    - Picard_Delta_3 governs creation of new splinter factions (high-impact)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any


# ============================================================================
# ENUMS
# ============================================================================

class InsurgencyPhase(Enum):
    """Insurgency lifecycle phases."""
    LATENT         = "latent"       # conditions exist but no open action
    ORGANIZING     = "organizing"   # cells forming, no violence yet
    ACTIVE         = "active"       # open guerrilla operations
    ESCALATED      = "escalated"    # multi-district operations
    CIVIL_WAR      = "civil_war"    # full conventional warfare
    SUPPRESSED     = "suppressed"   # temporarily defeated
    RESOLVED       = "resolved"     # ended via negotiation or victory


class InsurgencyType(Enum):
    """Ideological basis of the insurgency."""
    SEPARATIST      = "separatist"    # seeks territorial independence
    IDEOLOGICAL     = "ideological"   # seeks regime change
    ETHNIC          = "ethnic"        # ethnic/sectarian grievance
    ECONOMIC        = "economic"      # resource / class-based
    RELIGIOUS       = "religious"     # religious authority challenge


class FragmentationType(Enum):
    """How a faction splits."""
    PEACEFUL_SECESSION   = "peaceful_secession"   # negotiated split
    FORCED_PARTITION     = "forced_partition"     # imposed by external power
    CIVIL_WAR_SPLIT      = "civil_war_split"      # outcome of internal conflict
    COUP_SUCCESSION      = "coup_succession"      # post-coup fragmentation


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class InsurgencyState:
    """
    An active internal insurgency within a faction.

    The insurgency occupies a fraction of the faction's territory
    and exerts military pressure on the governing faction.
    """
    insurgency_id: str
    host_faction_id: str           # governing faction being challenged
    insurgency_type: InsurgencyType

    phase: InsurgencyPhase = InsurgencyPhase.ORGANIZING

    # Combat capability
    insurgent_strength: float = 0.1    # normalized [0, 1]
    popular_support: float = 0.3       # fraction of population sympathetic

    # Territory control (fraction of faction's territory)
    territory_controlled: float = 0.0

    # Grievance drivers (pulled from PopulationState / LeaderState)
    economic_grievance: float = 0.5
    political_grievance: float = 0.5
    ethnic_grievance: float = 0.3

    # External support (other factions sponsoring rebels)
    external_sponsor_id: Optional[str] = None
    external_support_level: float = 0.0

    # State repression response
    repression_level: float = 0.5

    # Turns active
    turns_active: int = 0
    casualties_inflicted: float = 0.0
    casualties_suffered: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["phase"] = self.phase.value
        d["insurgency_type"] = self.insurgency_type.value
        return d


@dataclass
class FragmentationEvent:
    """
    A state fragmentation event creating a splinter faction.

    Requires Picard_Delta_3 authorization in engine (high-impact mutation).
    """
    event_id: str
    parent_faction_id: str
    splinter_faction_name: str
    fragmentation_type: FragmentationType

    # Initial state of the splinter faction
    initial_military: float = 0.2
    initial_economic: float = 0.3
    initial_territory: float = 0.15   # fraction of parent territory

    # Relations with parent
    initial_trust_with_parent: float = 0.1
    triggers_conflict: bool = True

    turn_occurred: int = 0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["fragmentation_type"] = self.fragmentation_type.value
        return d


# ============================================================================
# REBELLION ENGINE
# ============================================================================

class RebellionEngine:
    """
    Drives insurgency lifecycle and state fragmentation.

    Usage (inside engine.py Phase 20):
        reb_engine = RebellionEngine()
        events = reb_engine.tick(insurgencies, pop_states, leaders, factions, rng)
    """

    # Minimum onset probability to trigger new insurgency
    ONSET_THRESHOLD = 0.08

    # Insurgency strength at which civil war phase is entered
    CIVIL_WAR_THRESHOLD = 0.55

    # Territory control at which fragmentation risk becomes critical
    FRAGMENTATION_TERRITORY_THRESHOLD = 0.35

    def tick(
        self,
        insurgencies: List[InsurgencyState],
        demographic_stress: Dict[str, float],       # faction_id → stress
        leader_legitimacy: Dict[str, float],        # faction_id → legitimacy
        leader_institutional_control: Dict[str, float],
        faction_military_strength: Dict[str, float],
        ci_strength: Dict[str, float],              # counter-intel
        rng,
    ) -> List[Dict[str, Any]]:
        """
        Advance all insurgency states by one tick and check for new onsets.

        Returns:
            List of event dicts
        """
        events: List[Dict[str, Any]] = []

        # Phase 1: Check for new insurgency onsets in each faction
        for fid in demographic_stress:
            already_insurgent = any(i.host_faction_id == fid for i in insurgencies)
            if already_insurgent:
                continue

            p_onset = calc_rebellion_onset_probability(
                demographic_stress=demographic_stress.get(fid, 0.0),
                legitimacy=leader_legitimacy.get(fid, 0.7),
                institutional_control=leader_institutional_control.get(fid, 0.5),
                ci_strength=ci_strength.get(fid, 0.3),
            )

            if p_onset > self.ONSET_THRESHOLD and rng.random() < p_onset:
                insurgency_type = rng.choice(list(InsurgencyType))
                new_ins = InsurgencyState(
                    insurgency_id=f"INS_{fid}_{id(rng)}",
                    host_faction_id=fid,
                    insurgency_type=insurgency_type,
                    economic_grievance=demographic_stress.get(fid, 0.5),
                    political_grievance=1.0 - leader_legitimacy.get(fid, 0.7),
                    insurgent_strength=rng.uniform(0.05, 0.15),
                    popular_support=rng.uniform(0.15, 0.45),
                )
                insurgencies.append(new_ins)
                events.append({
                    "type": "REBELLION_ONSET",
                    "faction_id": fid,
                    "insurgency_id": new_ins.insurgency_id,
                    "insurgency_type": insurgency_type.value,
                    "onset_probability": round(p_onset, 3),
                })

        # Phase 2: Advance existing insurgencies
        for ins in list(insurgencies):
            ins.turns_active += 1
            fid = ins.host_faction_id

            repression_eff = calc_repression_effectiveness(
                military_strength=faction_military_strength.get(fid, 0.5),
                ci_strength=ci_strength.get(fid, 0.3),
                popular_legitimacy=leader_legitimacy.get(fid, 0.7),
            )
            ins.repression_level = repression_eff

            # Insurgent strength dynamics
            strength_gain = calc_insurgency_strength(
                popular_support=ins.popular_support,
                economic_grievance=ins.economic_grievance,
                external_support=ins.external_support_level,
                repression_level=repression_eff,
            )
            ins.insurgent_strength = max(
                0.0, min(1.0, ins.insurgent_strength + strength_gain)
            )

            # Territory expansion
            if ins.insurgent_strength > repression_eff:
                territory_gain = (ins.insurgent_strength - repression_eff) * 0.04
                ins.territory_controlled = min(0.8, ins.territory_controlled + territory_gain)
            else:
                territory_loss = (repression_eff - ins.insurgent_strength) * 0.03
                ins.territory_controlled = max(0.0, ins.territory_controlled - territory_loss)

            # Phase transitions
            old_phase = ins.phase
            if ins.insurgent_strength < 0.05 and ins.territory_controlled < 0.01:
                ins.phase = InsurgencyPhase.SUPPRESSED
            elif ins.insurgent_strength >= self.CIVIL_WAR_THRESHOLD:
                p_cw = calc_civil_war_escalation(
                    insurgent_strength=ins.insurgent_strength,
                    popular_support=ins.popular_support,
                    territory_controlled=ins.territory_controlled,
                )
                if rng.random() < p_cw:
                    ins.phase = InsurgencyPhase.CIVIL_WAR
                    events.append({
                        "type": "CIVIL_WAR_ONSET",
                        "faction_id": fid,
                        "insurgency_id": ins.insurgency_id,
                        "insurgent_strength": round(ins.insurgent_strength, 3),
                        "territory_controlled": round(ins.territory_controlled, 3),
                    })
            elif ins.insurgent_strength > 0.30:
                ins.phase = InsurgencyPhase.ESCALATED
            elif ins.insurgent_strength > 0.10:
                ins.phase = InsurgencyPhase.ACTIVE

            # Fragmentation check
            if ins.territory_controlled >= self.FRAGMENTATION_TERRITORY_THRESHOLD:
                frag_risk = calc_state_fragmentation_risk(
                    territory_controlled=ins.territory_controlled,
                    insurgent_strength=ins.insurgent_strength,
                    legitimacy=leader_legitimacy.get(fid, 0.7),
                    turns_active=ins.turns_active,
                )
                if rng.random() < frag_risk:
                    events.append({
                        "type": "STATE_FRAGMENTATION",
                        "faction_id": fid,
                        "insurgency_id": ins.insurgency_id,
                        "territory_split": round(ins.territory_controlled, 3),
                        "fragmentation_risk": round(frag_risk, 3),
                        "picard_delta_3_required": True,   # high-impact mutation flag
                    })

            # Separatist declaration
            if (ins.insurgency_type == InsurgencyType.SEPARATIST
                    and ins.territory_controlled > 0.20
                    and rng.random() < ins.territory_controlled * 0.15):
                events.append({
                    "type": "SEPARATIST_DECLARATION",
                    "faction_id": fid,
                    "insurgency_id": ins.insurgency_id,
                    "territory": round(ins.territory_controlled, 3),
                })

        # Phase 3: Conscription response
        for fid, mil_str in faction_military_strength.items():
            active_ins = [i for i in insurgencies if i.host_faction_id == fid
                          and i.phase in (InsurgencyPhase.CIVIL_WAR, InsurgencyPhase.ESCALATED)]
            if active_ins and rng.random() < 0.3:
                events.append({
                    "type": "MASS_CONSCRIPTION",
                    "faction_id": fid,
                    "trigger": "internal_conflict",
                    "active_insurgencies": len(active_ins),
                })

        return events


# ============================================================================
# PURE FORMULA FUNCTIONS
# ============================================================================

def calc_rebellion_onset_probability(
    demographic_stress: float,
    legitimacy: float,
    institutional_control: float,
    ci_strength: float,
    *,
    stress_weight: float       = 0.35,
    legitimacy_weight: float   = 0.30,
    institution_weight: float  = 0.20,
    ci_suppression: float      = 0.15,
) -> float:
    """
    Probability that a new insurgency begins this turn.

    High demographic stress + low legitimacy → high onset probability.
    Strong institutions and CI suppress onset probability.

    Formula:
        p = stress_weight × demographic_stress
          + legitimacy_weight × (1 - legitimacy)
          - institution_weight × institutional_control
          - ci_suppression × ci_strength

    Returns:
        float in [0.0, 0.60]   (capped — onset is rare per tick)
    """
    p = (
        stress_weight      * demographic_stress
        + legitimacy_weight  * (1.0 - legitimacy)
        - institution_weight * institutional_control
        - ci_suppression     * ci_strength
    )
    return max(0.0, min(0.60, p))


def calc_insurgency_strength(
    popular_support: float,
    economic_grievance: float,
    external_support: float,
    repression_level: float,
    *,
    support_weight: float    = 0.35,
    grievance_weight: float  = 0.30,
    external_weight: float   = 0.20,
    repression_penalty: float = 0.40,
    base_gain: float         = 0.005,
) -> float:
    """
    Change in insurgent strength per turn.

    Popular support and grievance fuel recruitment.
    External sponsorship provides resources and training.
    Effective repression reduces net strength gain.

    Formula:
        raw_gain = base_gain
                 + support_weight × popular_support
                 + grievance_weight × economic_grievance
                 + external_weight × external_support
        net_gain = raw_gain - repression_penalty × repression_level

    Returns:
        float — delta insurgent_strength this turn (can be negative)
    """
    raw_gain = (
        base_gain
        + support_weight   * popular_support
        + grievance_weight * economic_grievance
        + external_weight  * external_support
    )
    net_gain = raw_gain - repression_penalty * repression_level
    return max(-0.08, min(0.08, net_gain))


def calc_state_fragmentation_risk(
    territory_controlled: float,
    insurgent_strength: float,
    legitimacy: float,
    turns_active: int,
    *,
    territory_weight: float  = 0.40,
    strength_weight: float   = 0.30,
    legitimacy_weight: float = 0.20,
    duration_weight: float   = 0.10,
    max_turns_scaling: int   = 20,
) -> float:
    """
    Probability the faction splinters into two independent entities.

    High territory control + strong insurgents + low legitimacy → high fragmentation.
    Longer active insurgencies are more likely to consolidate into statelets.

    Formula:
        duration_factor = min(1, turns_active / max_turns_scaling)
        risk = territory_weight × territory_controlled
             + strength_weight × insurgent_strength
             + legitimacy_weight × (1 - legitimacy)
             + duration_weight × duration_factor

    Returns:
        float in [0.0, 0.80]  (capped — fragmentation is rare)
    """
    duration_factor = min(1.0, turns_active / max_turns_scaling)
    risk = (
        territory_weight  * territory_controlled
        + strength_weight   * insurgent_strength
        + legitimacy_weight * (1.0 - legitimacy)
        + duration_weight   * duration_factor
    )
    return max(0.0, min(0.80, risk))


def calc_repression_effectiveness(
    military_strength: float,
    ci_strength: float,
    popular_legitimacy: float,
    *,
    military_weight: float    = 0.40,
    ci_weight: float          = 0.35,
    legitimacy_weight: float  = 0.25,
) -> float:
    """
    Effectiveness of state repression against insurgents.

    Legitimacy matters: a legitimate state does not need brutal repression.
    Military strength and CI provide direct suppression capability.

    Formula:
        repression = military_weight × military_strength
                   + ci_weight × ci_strength
                   + legitimacy_weight × popular_legitimacy

    Returns:
        float in [0.0, 1.0]
    """
    repression = (
        military_weight   * military_strength
        + ci_weight         * ci_strength
        + legitimacy_weight * popular_legitimacy
    )
    return max(0.0, min(1.0, repression))


def calc_civil_war_escalation(
    insurgent_strength: float,
    popular_support: float,
    territory_controlled: float,
    *,
    strength_weight: float   = 0.45,
    support_weight: float    = 0.30,
    territory_weight: float  = 0.25,
    base_probability: float  = 0.05,
) -> float:
    """
    Probability insurgency escalates to full civil war this turn.

    All three factors must be meaningful for escalation to be likely.
    The sigmoid-like structure ensures escalation only when all are high.

    Formula:
        raw = strength_weight × insurgent_strength
            + support_weight × popular_support
            + territory_weight × territory_controlled
        p = base + raw × raw  (quadratic: slow ramp, fast takeoff)

    Returns:
        float in [0.0, 0.60]
    """
    raw = (
        strength_weight  * insurgent_strength
        + support_weight   * popular_support
        + territory_weight * territory_controlled
    )
    p = base_probability + raw * raw
    return max(0.0, min(0.60, p))

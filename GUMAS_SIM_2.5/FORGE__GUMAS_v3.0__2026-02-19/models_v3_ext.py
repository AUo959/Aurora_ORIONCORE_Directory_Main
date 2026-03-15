#!/usr/bin/env python3
"""
GUMAS v3.0 — Model Extensions
==============================
Anchor: GUMAS-ENGINE-MODELS-V3-EXT
Seed:   EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP:    L2_ENGINE_V3
Version: 3.0.0

Extensions to models.py required for v3.0 subsystems.
These additions are backward-compatible: existing v2.0 fields
are preserved; new fields are appended.

Patch Instructions (to integrate into models.py):
    1. Add new EventType values to the existing EventType enum
    2. Add new enum classes at top of models.py
    3. Add v3.0 fields to GUMASState (via composition or dict extension)
    4. Import new module state classes where needed

New EventType values (15):
    POPULATION_MIGRATION, REFUGEE_CRISIS, TECH_BREAKTHROUGH_ADVANCED,
    TECH_DIFFUSION, TECH_NODE_UNLOCKED, DIPLOMATIC_AGREEMENT,
    DIPLOMATIC_CRISIS, BACK_CHANNEL_DEAL, ULTIMATUM_ISSUED,
    ULTIMATUM_RESOLVED, INTELLIGENCE_SHARING, INTELLIGENCE_COMPROMISE,
    SURVEILLANCE_EXPANSION, REBELLION_ONSET, CIVIL_WAR_ONSET,
    STATE_FRAGMENTATION, SEPARATIST_DECLARATION, MASS_CONSCRIPTION

New standalone models:
    - GUMASStateV3Extension  (composition object for GUMASState)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# Import new v3.0 module state classes
from population   import PopulationState, DemographicProfile
from technology   import FactionTechState, FactionTechState
from negotiation  import NegotiationState, Ultimatum, NegotiationPhase
from intelligence import IntelNetwork, SurveillanceLevel
from rebellion    import InsurgencyState, InsurgencyPhase, InsurgencyType
from l2_state import L2StateBundle


# ============================================================================
# NEW EVENT TYPES (append to EventType enum in models.py)
# ============================================================================

V3_EVENT_TYPES = [
    # Population
    "POPULATION_MIGRATION",
    "REFUGEE_CRISIS",
    "MASS_CONSCRIPTION",
    # Technology
    "TECH_BREAKTHROUGH_ADVANCED",
    "TECH_DIFFUSION",
    "TECH_NODE_UNLOCKED",
    # Negotiation
    "DIPLOMATIC_AGREEMENT",
    "DIPLOMATIC_CRISIS",
    "BACK_CHANNEL_DEAL",
    "ULTIMATUM_ISSUED",
    "ULTIMATUM_RESOLVED",
    # Intelligence
    "INTELLIGENCE_SHARING",
    "INTELLIGENCE_COMPROMISE",
    "SURVEILLANCE_EXPANSION",
    # Rebellion
    "REBELLION_ONSET",
    "CIVIL_WAR_ONSET",
    "STATE_FRAGMENTATION",
    "SEPARATIST_DECLARATION",
]


# ============================================================================
# V3.0 STATE EXTENSION (compose into GUMASState or pass alongside)
# ============================================================================

@dataclass
class GUMASStateV3Extension:
    """
    v3.0 state extension object.

    In v3.0, this is passed alongside GUMASState to the engine.
    Integration path for v3.1+: merge these fields directly into GUMASState.

    Usage:
        engine = GUMASEngineV3(seed=42)
        engine.init_scenario()          # creates both base state and v3 ext
        result = engine.step()          # uses both state objects
    """

    # Population module state (faction_id → PopulationState)
    population: Dict[str, PopulationState] = field(default_factory=dict)

    # Technology module state (faction_id → FactionTechState)
    technology: Dict[str, FactionTechState] = field(default_factory=dict)

    # Active negotiations (list)
    negotiations: List[NegotiationState] = field(default_factory=list)

    # Active ultimatums (list)
    ultimatums: List[Ultimatum] = field(default_factory=list)

    # Intelligence networks (faction_id → IntelNetwork)
    intel_networks: Dict[str, IntelNetwork] = field(default_factory=dict)

    # Active insurgencies (list)
    insurgencies: List[InsurgencyState] = field(default_factory=list)

    # Cross-module caches (recomputed each tick)
    tech_combat_multipliers: Dict[str, float] = field(default_factory=dict)
    tech_economic_multipliers: Dict[str, float] = field(default_factory=dict)
    conscription_capacity: Dict[str, float] = field(default_factory=dict)

    # V3 tick event log (cleared each tick)
    v3_events: List[Dict[str, Any]] = field(default_factory=list)

    # Additive named-entity registry/state bundle (phase 1; no mechanics impact)
    l2_state: Optional[L2StateBundle] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "population": {k: v.to_dict() for k, v in self.population.items()},
            "technology": {k: v.to_dict() for k, v in self.technology.items()},
            "negotiations": [n.to_dict() for n in self.negotiations],
            "ultimatums": [u.to_dict() for u in self.ultimatums],
            "intel_networks": {k: v.to_dict() for k, v in self.intel_networks.items()},
            "insurgencies": [i.to_dict() for i in self.insurgencies],
            "tech_combat_multipliers": dict(self.tech_combat_multipliers),
            "tech_economic_multipliers": dict(self.tech_economic_multipliers),
            "conscription_capacity": dict(self.conscription_capacity),
        }


# ============================================================================
# V3.0 SCENARIO INITIALIZER
# ============================================================================

def init_v3_extension_from_scenario(
    faction_ids: List[str],
    faction_types: Optional[Dict[str, str]] = None,
) -> GUMASStateV3Extension:
    """
    Build a default GUMASStateV3Extension for a given faction list.

    Assigns reasonable starting values for all v3.0 subsystems.
    Used by the v3.0 engine init_scenario() method.

    Args:
        faction_ids: List of faction IDs from the base scenario
        faction_types: Optional mapping faction_id → faction_type string

    Returns:
        GUMASStateV3Extension with default values
    """
    ext = GUMASStateV3Extension()

    for fid in faction_ids:
        # Population
        ext.population[fid] = PopulationState(
            faction_id=fid,
            population_index=1.0,
            profile=DemographicProfile.MATURE_STABLE,
            birth_rate=0.020,
            death_rate=0.010,
            food_security=0.70,
            housing_pressure=0.30,
            unemployment=0.12,
        )

        # Technology (level varies by faction type)
        tech_boost = 0.0
        ftype = (faction_types or {}).get(fid, "")
        if "sovereign_ai" in ftype or "rogue_synthetic" in ftype:
            tech_boost = 1.5    # AI factions start with higher computing
        elif "frontier" in ftype or "nomadic" in ftype:
            tech_boost = -0.3   # frontier factions start slightly behind

        from technology import TechCategory
        ext.technology[fid] = FactionTechState(
            faction_id=fid,
            tech_levels={c.value: max(0.1, 1.0 + tech_boost) for c in TechCategory},
            rd_capacity=0.5,
        )
        if tech_boost > 1.0:
            ext.technology[fid].tech_levels["computing"] = 3.0
            ext.technology[fid].tech_levels["weapons"]   = 2.5

        # Intelligence network
        surv = SurveillanceLevel.MODERATE
        if "authoritarian" in ftype:
            surv = SurveillanceLevel.AUTHORITARIAN
        elif "sovereign_ai" in ftype or "rogue_synthetic" in ftype:
            surv = SurveillanceLevel.TOTALITARIAN

        ext.intel_networks[fid] = IntelNetwork(
            faction_id=fid,
            sigint_capacity=0.3,
            humint_capacity=0.3,
            counter_intel_strength=0.3,
            surveillance_level=surv,
            intel_budget_fraction=0.05,
        )

    return ext


# ============================================================================
# V3.0 TICK RESULT EXTENSION
# ============================================================================

@dataclass
class TickResultV3:
    """
    Extended tick result including v3.0 subsystem outputs.

    Composes with the base TickResult from v2.0.
    """
    turn: int
    v3_events: List[Dict[str, Any]] = field(default_factory=list)
    new_insurgencies: int = 0
    civil_wars_started: int = 0
    tech_breakthroughs: int = 0
    migrations: int = 0
    fragmentation_events: int = 0
    negotiations_concluded: int = 0
    intelligence_ops: int = 0

    def summary(self) -> str:
        return (
            f"Turn {self.turn} v3.0 | "
            f"Insurgencies: +{self.new_insurgencies} | "
            f"Civil Wars: +{self.civil_wars_started} | "
            f"Tech Breakthrus: +{self.tech_breakthroughs} | "
            f"Migrations: +{self.migrations} | "
            f"Negotiations concluded: +{self.negotiations_concluded} | "
            f"Intel ops: +{self.intelligence_ops}"
        )

#!/usr/bin/env python3
"""
GUMAS v3.0 — Population & Demographics Module
===============================================
Anchor: GUMAS-ENGINE-POPULATION-V3
Seed:   EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP:    L2_ENGINE_V3
Version: 3.0.0

Models population dynamics, migration, conscription capacity, and
demographic-driven political pressure. Population pressure is a key
driver of internal conflict onset (see rebellion.py) and economic
ceiling adjustments.

Subsystem roles in tick lifecycle:
    Phase 16 — Population Tick (called by engine after Culture Tick)

Formulas:
    calc_population_growth()       — logistic population growth per turn
    calc_migration_pressure()      — push/pull migration between factions
    calc_conscription_capacity()   — available military manpower
    calc_demographic_stress()      — composite population stress index
    calc_refugee_generation()      — refugees produced by active conflicts

Design principles:
    - Stdlib only; no numpy/scipy
    - All functions stateless and deterministic
    - Faction-level population (not individual agents)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any


# ============================================================================
# ENUMS
# ============================================================================

class DemographicProfile(Enum):
    """Broad demographic profile affecting growth and stress."""
    YOUNG_EXPANDING    = "young_expanding"     # high birth rate, fast growth
    MATURE_STABLE      = "mature_stable"       # balanced, sustainable
    AGING_DECLINING    = "aging_declining"     # low birth rate, shrinking
    WAR_RAVAGED        = "war_ravaged"         # casualties dominate dynamics
    REFUGEE_DISPLACED  = "refugee_displaced"   # majority population displaced


class MigrationReason(Enum):
    """Primary driver of migration event."""
    ECONOMIC_PULL      = "economic_pull"
    CONFLICT_PUSH      = "conflict_push"
    ENVIRONMENTAL_PUSH = "environmental_push"
    CULTURAL_AFFINITY  = "cultural_affinity"
    FORCED_EXPULSION   = "forced_expulsion"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class PopulationState:
    """
    Population and demographic state for a single faction.

    Population is modelled as a normalized index [0.0, 2.0] relative
    to the faction's baseline carrying capacity (1.0 = at capacity).
    """
    faction_id: str

    # Core population index (0.0 = extinct, 1.0 = capacity, 2.0 = overpopulated)
    population_index: float = 1.0

    # Demographic profile
    profile: DemographicProfile = DemographicProfile.MATURE_STABLE

    # Birth / death rates per turn (fractional)
    birth_rate: float = 0.02
    death_rate: float = 0.01

    # Cumulative war casualties (normalized)
    war_casualties: float = 0.0

    # Migration
    net_migration: float = 0.0       # positive = net inflow
    refugee_population: float = 0.0  # displaced persons index

    # Conscription
    military_age_fraction: float = 0.35   # fraction of population conscriptable
    current_mobilization: float = 0.0     # fraction currently mobilized [0,1]

    # Pressure indices (fed to rebellion.py)
    food_security: float = 0.7
    housing_pressure: float = 0.3
    unemployment: float = 0.15

    # Composite stress (computed each tick)
    demographic_stress: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["profile"] = self.profile.value
        return d


@dataclass
class MigrationEvent:
    """A discrete migration event between two factions."""
    origin_faction_id: str
    destination_faction_id: str
    magnitude: float          # population_index units transferred
    reason: MigrationReason
    turn: int

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["reason"] = self.reason.value
        return d


# ============================================================================
# POPULATION ENGINE
# ============================================================================

class PopulationEngine:
    """
    Drives population dynamics for all factions each simulation tick.

    Usage (inside engine.py Phase 16):
        pop_engine = PopulationEngine()
        events = pop_engine.tick(state, rng)
    """

    # Stress → instability thresholds
    HIGH_STRESS_THRESHOLD  = 0.6
    CRISIS_STRESS_THRESHOLD = 0.8

    # Refugee spillover fraction (fraction of refugees that cross borders)
    REFUGEE_SPILLOVER_RATE = 0.15

    def tick(
        self,
        populations: Dict[str, PopulationState],
        faction_conflicts: Dict[str, List[str]],   # faction_id -> list of conflict_ids active
        faction_military_strength: Dict[str, float],
        rng,
    ) -> List[Dict[str, Any]]:
        """
        Advance all population states by one tick.

        Args:
            populations: Mapping faction_id -> PopulationState
            faction_conflicts: Which factions are in active conflict
            faction_military_strength: Current military strength per faction
            rng: Seeded Random instance from engine

        Returns:
            List of event dicts (POPULATION_MIGRATION, REFUGEE_CRISIS)
        """
        events: List[Dict[str, Any]] = []

        for fid, pop in populations.items():
            in_conflict = bool(faction_conflicts.get(fid))

            # 1. Natural population change
            growth = calc_population_growth(
                pop.population_index,
                pop.birth_rate,
                pop.death_rate,
                carrying_capacity=1.0,
            )
            pop.population_index = max(0.0, pop.population_index + growth)

            # 2. War casualties
            if in_conflict:
                casualties = calc_war_casualties(
                    faction_military_strength.get(fid, 0.5),
                    len(faction_conflicts.get(fid, [])),
                )
                pop.war_casualties += casualties
                pop.population_index = max(0.05, pop.population_index - casualties * 0.5)

            # 3. Refugee generation
            refugees = calc_refugee_generation(
                in_conflict=in_conflict,
                conflict_count=len(faction_conflicts.get(fid, [])),
                population_index=pop.population_index,
            )
            if refugees > 0.01:
                pop.refugee_population += refugees
                pop.population_index = max(0.05, pop.population_index - refugees)

            # 4. Demographic stress
            pop.demographic_stress = calc_demographic_stress(
                population_index=pop.population_index,
                food_security=pop.food_security,
                housing_pressure=pop.housing_pressure,
                unemployment=pop.unemployment,
                refugee_fraction=pop.refugee_population / max(pop.population_index, 0.1),
                war_casualties=pop.war_casualties,
            )

            # 5. Emit refugee crisis event if threshold crossed
            if pop.refugee_population > 0.15 and rng.random() < pop.refugee_population:
                events.append({
                    "type": "REFUGEE_CRISIS",
                    "faction_id": fid,
                    "refugee_population": round(pop.refugee_population, 3),
                    "demographic_stress": round(pop.demographic_stress, 3),
                })

        # 6. Cross-border migration
        mig_events = self._resolve_migration(populations, rng)
        events.extend(mig_events)

        return events

    def _resolve_migration(
        self,
        populations: Dict[str, PopulationState],
        rng,
    ) -> List[Dict[str, Any]]:
        """Compute cross-border migration flows between all faction pairs."""
        events = []
        faction_ids = list(populations.keys())

        for i, src_id in enumerate(faction_ids):
            src = populations[src_id]
            for dst_id in faction_ids[i + 1:]:
                dst = populations[dst_id]

                pressure = calc_migration_pressure(
                    src_unemployment=src.unemployment,
                    src_food_security=src.food_security,
                    src_demographic_stress=src.demographic_stress,
                    dst_unemployment=dst.unemployment,
                    dst_food_security=dst.food_security,
                    dst_population_index=dst.population_index,
                )

                if abs(pressure) > 0.05 and rng.random() < abs(pressure) * 0.4:
                    magnitude = abs(pressure) * 0.03 * rng.uniform(0.5, 1.5)
                    if pressure > 0:
                        # src → dst
                        src.population_index = max(0.05, src.population_index - magnitude)
                        dst.population_index = min(2.0, dst.population_index + magnitude)
                        src.net_migration -= magnitude
                        dst.net_migration += magnitude
                        reason = (MigrationReason.CONFLICT_PUSH if src.demographic_stress > 0.6
                                  else MigrationReason.ECONOMIC_PULL)
                    else:
                        # dst → src
                        dst.population_index = max(0.05, dst.population_index - magnitude)
                        src.population_index = min(2.0, src.population_index + magnitude)
                        dst.net_migration -= magnitude
                        src.net_migration += magnitude
                        reason = MigrationReason.ECONOMIC_PULL

                    events.append({
                        "type": "POPULATION_MIGRATION",
                        "origin": src_id if pressure > 0 else dst_id,
                        "destination": dst_id if pressure > 0 else src_id,
                        "magnitude": round(magnitude, 4),
                        "reason": reason.value,
                    })

        return events


# ============================================================================
# PURE FORMULA FUNCTIONS
# ============================================================================

def calc_population_growth(
    population_index: float,
    birth_rate: float,
    death_rate: float,
    carrying_capacity: float = 1.0,
    *,
    logistic_steepness: float = 3.0,
) -> float:
    """
    Logistic population growth per simulation turn.

    Formula (Verhulst logistic):
        r_eff = birth_rate - death_rate
        growth = r_eff × P × (1 - P / K)

    where P = population_index, K = carrying_capacity.

    Args:
        population_index: Current normalized population [0, 2.0]
        birth_rate: Fractional birth rate per turn (e.g. 0.02)
        death_rate: Fractional death rate per turn (e.g. 0.01)
        carrying_capacity: Normalized capacity ceiling (default 1.0)
        logistic_steepness: Amplifies overshoot pressure above K

    Returns:
        Delta population index for this turn (can be negative)
    """
    r = birth_rate - death_rate
    # Standard Verhulst logistic suppression: zero at P=K, negative above K
    suppression = 1.0 - (population_index / carrying_capacity)
    growth = r * population_index * suppression
    return max(-0.1, min(0.1, growth))  # cap delta per turn


def calc_migration_pressure(
    src_unemployment: float,
    src_food_security: float,
    src_demographic_stress: float,
    dst_unemployment: float,
    dst_food_security: float,
    dst_population_index: float,
    *,
    unemployment_weight: float = 0.35,
    food_weight: float = 0.35,
    stress_weight: float = 0.30,
    capacity_dampener: float = 0.5,
) -> float:
    """
    Net migration pressure from src toward dst.

    Positive return = migration src→dst is favoured.
    Negative return = migration dst→src is favoured.

    Formula:
        push  = unemployment_weight × src_unemployment
               + food_weight × (1 - src_food_security)
               + stress_weight × src_demographic_stress
        pull  = unemployment_weight × (1 - dst_unemployment)
               + food_weight × dst_food_security
        cap   = capacity_dampener × max(0, dst_population_index - 1.0)
        net   = push - pull - cap

    Returns:
        float in [-1.0, 1.0]
    """
    push = (
        unemployment_weight * src_unemployment
        + food_weight * (1.0 - src_food_security)
        + stress_weight * src_demographic_stress
    )
    pull = (
        unemployment_weight * (1.0 - dst_unemployment)
        + food_weight * dst_food_security
    )
    capacity_penalty = capacity_dampener * max(0.0, dst_population_index - 1.0)
    net = push - pull - capacity_penalty
    return max(-1.0, min(1.0, net))


def calc_conscription_capacity(
    population_index: float,
    military_age_fraction: float,
    current_mobilization: float,
    *,
    maximum_mobilization_rate: float = 0.6,
    demographic_stress_penalty: float = 0.0,
) -> float:
    """
    Available conscription capacity as fraction of total population.

    Formula:
        base = population_index × military_age_fraction
        available = base × (maximum_mobilization_rate - current_mobilization)
        penalized = available × (1 - demographic_stress_penalty × 0.5)

    Returns:
        float in [0.0, 1.0] — fraction of population available for conscription
    """
    base = population_index * military_age_fraction
    available = base * max(0.0, maximum_mobilization_rate - current_mobilization)
    penalized = available * (1.0 - demographic_stress_penalty * 0.5)
    return max(0.0, min(1.0, penalized))


def calc_demographic_stress(
    population_index: float,
    food_security: float,
    housing_pressure: float,
    unemployment: float,
    refugee_fraction: float,
    war_casualties: float,
    *,
    food_weight: float      = 0.25,
    housing_weight: float   = 0.15,
    unemploy_weight: float  = 0.20,
    refugee_weight: float   = 0.20,
    casualty_weight: float  = 0.20,
) -> float:
    """
    Composite demographic stress index.

    High stress feeds rebellion onset probability (rebellion.py).

    Formula:
        overpop_factor = max(0, population_index - 1.0)
        stress = food_weight    × (1 - food_security)
               + housing_weight × housing_pressure
               + unemploy_weight × unemployment
               + refugee_weight  × min(1, refugee_fraction)
               + casualty_weight × min(1, war_casualties × 2)
               + 0.1 × overpop_factor

    Returns:
        float in [0.0, 1.0]
    """
    overpop = max(0.0, population_index - 1.0)
    stress = (
        food_weight      * (1.0 - food_security)
        + housing_weight * housing_pressure
        + unemploy_weight * unemployment
        + refugee_weight  * min(1.0, refugee_fraction)
        + casualty_weight * min(1.0, war_casualties * 2.0)
        + 0.10 * overpop
    )
    return max(0.0, min(1.0, stress))


def calc_refugee_generation(
    in_conflict: bool,
    conflict_count: int,
    population_index: float,
    *,
    base_refugee_rate: float = 0.04,
    conflict_multiplier: float = 1.8,
) -> float:
    """
    Refugees generated per turn from active conflicts.

    Formula:
        if not in_conflict: return 0
        rate = base_refugee_rate × conflict_multiplier^(conflict_count - 1)
        refugees = rate × population_index

    Returns:
        float — refugee population units generated this turn
    """
    if not in_conflict:
        return 0.0
    rate = base_refugee_rate * (conflict_multiplier ** max(0, conflict_count - 1))
    return min(0.25, rate * population_index)


def calc_war_casualties(
    military_strength: float,
    conflict_count: int,
    *,
    base_casualty_rate: float = 0.015,
) -> float:
    """
    Cumulative war casualties produced per tick.

    Higher military strength = more forces exposed = more casualties
    per unit time, but also greater resilience.

    Formula:
        casualties = base_casualty_rate × military_strength × sqrt(conflict_count)

    Returns:
        float — casualty index units added this turn
    """
    return base_casualty_rate * military_strength * math.sqrt(max(1, conflict_count))

#!/usr/bin/env python3
"""
GUMAS L2 Combat Resolution System v2.0
Anchor: GUMAS-COMBAT-V2
Seed: EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP: L2_ENGINE_CORE
"""

import random
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

from .models import (
    FleetState,
    CombatState,
    BattlefieldCondition,
    EventType,
    SimulationEvent,
)
from .formulas import calc_combat_outcome, calc_combat_losses


# ============================================================================
# TERRAIN MODIFIERS MAPPING
# ============================================================================

TERRAIN_MODIFIERS: Dict[BattlefieldCondition, Tuple[float, float]] = {
    BattlefieldCondition.OPEN_SPACE: (1.0, 1.0),
    BattlefieldCondition.NEBULA: (0.8, 0.8),
    BattlefieldCondition.ASTEROID_FIELD: (0.7, 0.9),
    BattlefieldCondition.ORBITAL: (0.9, 1.1),
    BattlefieldCondition.FORTIFIED_POSITION: (0.6, 1.4),
    BattlefieldCondition.CHOKEPOINT: (0.5, 1.5),
    BattlefieldCondition.DEEP_SPACE: (1.0, 1.0),
}


def get_terrain_modifiers(condition: BattlefieldCondition) -> Tuple[float, float]:
    """
    Get terrain modifiers for battlefield condition.

    Args:
        condition: BattlefieldCondition enum value

    Returns:
        Tuple of (attacker_modifier, defender_modifier)
    """
    return TERRAIN_MODIFIERS.get(condition, (1.0, 1.0))


# ============================================================================
# COMBAT RESOLVER CLASS
# ============================================================================


class CombatResolver:
    """Resolves battles between fleets using GUMAS combat formulas."""

    def __init__(self, rng: random.Random):
        """
        Initialize combat resolver with random number generator.

        Args:
            rng: Random instance for stochastic processes
        """
        self.rng = rng

    def resolve_battle(
        self,
        combat: CombatState,
        attacker_fleets: List[FleetState],
        defender_fleets: List[FleetState],
        topology_manager=None,
    ) -> Dict[str, Any]:
        """
        Resolve a single battle between opposing fleets.

        Args:
            combat: CombatState object describing the battle
            attacker_fleets: List of attacking FleetState objects
            defender_fleets: List of defending FleetState objects
            topology_manager: Optional topology manager for location data

        Returns:
            Dictionary with keys:
                - outcome_ratio: Combat outcome ratio (W value)
                - winner: 'attacker' or 'defender'
                - attacker_losses: Total losses for attacker (0-1)
                - defender_losses: Total losses for defender (0-1)
                - events: List of battle event dictionaries
        """
        # Aggregate fleet strengths and modifiers
        attacker_strength = self._aggregate_fleet_strength(attacker_fleets)
        defender_strength = self._aggregate_fleet_strength(defender_fleets)

        attacker_tactical = self._calc_tactical_skill(attacker_fleets)
        defender_tactical = self._calc_tactical_skill(defender_fleets)

        attacker_ai = self._calc_ai_superiority(attacker_fleets)
        defender_ai = self._calc_ai_superiority(defender_fleets)

        attacker_supply = self._calc_avg_supply(attacker_fleets)
        defender_supply = self._calc_avg_supply(defender_fleets)

        attacker_morale = self._calc_avg_morale(attacker_fleets)
        defender_morale = self._calc_avg_morale(defender_fleets)

        # Get terrain modifiers
        attacker_terrain, defender_terrain = get_terrain_modifiers(combat.condition)

        # Calculate combat outcome
        outcome_ratio = calc_combat_outcome(
            fleet_strength_a=attacker_strength,
            fleet_strength_b=defender_strength,
            tactical_a=attacker_tactical,
            tactical_b=defender_tactical,
            ai_superiority_a=attacker_ai,
            ai_superiority_b=defender_ai,
            terrain_advantage_a=attacker_terrain,
            terrain_advantage_b=defender_terrain,
            supply_a=attacker_supply,
            supply_b=defender_supply,
            morale_a=attacker_morale,
            morale_b=defender_morale,
        )

        # Determine winner
        winner = "attacker" if outcome_ratio > 1.0 else "defender"

        # Calculate losses
        if outcome_ratio > 1.0:
            # Attacker wins, defender takes more losses
            attacker_losses, defender_losses = calc_combat_losses(
                outcome_ratio=outcome_ratio,
                losing_strength=defender_strength,
                duration_turns=combat.turns_active + 1,
            )
        else:
            # Defender wins, attacker takes more losses
            defender_losses, attacker_losses = calc_combat_losses(
                outcome_ratio=1.0 / max(0.01, outcome_ratio),
                losing_strength=attacker_strength,
                duration_turns=combat.turns_active + 1,
            )

        # Generate battle events
        events = self.generate_battle_events(combat, {
            "outcome_ratio": outcome_ratio,
            "winner": winner,
            "attacker_losses": attacker_losses,
            "defender_losses": defender_losses,
        })

        return {
            "outcome_ratio": outcome_ratio,
            "winner": winner,
            "attacker_losses": attacker_losses,
            "defender_losses": defender_losses,
            "events": events,
        }

    def apply_fleet_losses(
        self, fleets: List[FleetState], total_loss: float
    ) -> None:
        """
        Apply combat losses to fleet strengths.

        Args:
            fleets: List of FleetState objects to apply losses to
            total_loss: Total loss as fraction of strength (0-1)
        """
        for fleet in fleets:
            fleet.strength *= max(0.0, 1.0 - total_loss)
            # Morale reduces with losses
            fleet.morale = max(0.0, fleet.morale - total_loss * 0.3)

    def calc_retreat_probability(
        self, losing_ratio: float, morale: float
    ) -> float:
        """
        Calculate probability of fleet retreat.

        Args:
            losing_ratio: Ratio of losses (0-1)
            morale: Fleet morale level (0-1)

        Returns:
            Retreat probability (0-1)
        """
        # Higher losses and lower morale increase retreat probability
        base_prob = losing_ratio * (1.0 - morale) * 0.8
        return min(1.0, max(0.0, base_prob))

    def generate_battle_events(
        self, combat: CombatState, outcome: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate narrative events from battle outcome.

        Args:
            combat: CombatState object
            outcome: Result dictionary from resolve_battle

        Returns:
            List of event dictionaries
        """
        events = []
        winner = outcome["winner"]
        outcome_ratio = outcome["outcome_ratio"]
        attacker_losses = outcome["attacker_losses"]
        defender_losses = outcome["defender_losses"]

        # Main battle outcome event
        if outcome_ratio > 2.0:
            magnitude = min(1.0, outcome_ratio / 3.0)
            description = (
                f"Crushing victory at {combat.location}: "
                f"{'Attackers' if winner == 'attacker' else 'Defenders'} "
                f"achieved overwhelming superiority"
            )
        elif outcome_ratio > 1.2:
            magnitude = 0.6
            description = (
                f"Victory at {combat.location}: "
                f"{'Attackers' if winner == 'attacker' else 'Defenders'} "
                f"prevailed in battle"
            )
        elif outcome_ratio > 0.8:
            magnitude = 0.4
            description = (
                f"Pyrrhic victory at {combat.location}: "
                f"{'Attackers' if winner == 'attacker' else 'Defenders'} "
                f"won at heavy cost"
            )
        else:
            magnitude = 0.5
            description = (
                f"Stalemate at {combat.location}: "
                f"Fleets remained locked in inconclusive combat"
            )

        main_event = {
            "event_type": EventType.FLEET_BATTLE.value,
            "location": combat.location,
            "description": description,
            "magnitude": magnitude,
            "outcome_ratio": outcome_ratio,
            "attacker_losses": attacker_losses,
            "defender_losses": defender_losses,
        }
        events.append(main_event)

        # Heavy losses event
        if attacker_losses > 0.5 or defender_losses > 0.5:
            if attacker_losses > defender_losses:
                events.append({
                    "event_type": EventType.MILITARY_ESCALATION.value,
                    "description": f"Attackers suffered devastating losses at {combat.location}",
                    "magnitude": attacker_losses,
                })
            else:
                events.append({
                    "event_type": EventType.MILITARY_ESCALATION.value,
                    "description": f"Defenders suffered devastating losses at {combat.location}",
                    "magnitude": defender_losses,
                })

        # Terrain-based events
        if combat.condition == BattlefieldCondition.CHOKEPOINT:
            events.append({
                "event_type": EventType.MILITARY_ESCALATION.value,
                "description": f"Critical chokepoint battle at {combat.location}",
                "magnitude": 0.7,
            })
        elif combat.condition == BattlefieldCondition.FORTIFIED_POSITION:
            events.append({
                "event_type": EventType.MILITARY_ESCALATION.value,
                "description": (
                    f"Assault on fortified position at {combat.location}"
                ),
                "magnitude": 0.6,
            })

        return events

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _aggregate_fleet_strength(self, fleets: List[FleetState]) -> float:
        """
        Aggregate total strength of multiple fleets.

        Args:
            fleets: List of FleetState objects

        Returns:
            Total aggregated strength
        """
        return sum(
            fleet.strength * fleet.technology_modifier
            for fleet in fleets
        )

    def _calc_tactical_skill(self, fleets: List[FleetState]) -> float:
        """
        Calculate average tactical skill from fleet experiences.

        Args:
            fleets: List of FleetState objects

        Returns:
            Average tactical skill (0-1)
        """
        if not fleets:
            return 0.5

        # Experience correlates with tactical skill
        avg_experience = sum(f.experience for f in fleets) / len(fleets)
        return min(1.0, 0.5 + avg_experience * 0.3)

    def _calc_ai_superiority(self, fleets: List[FleetState]) -> float:
        """
        Calculate AI/tech superiority from fleet technology modifiers.

        Args:
            fleets: List of FleetState objects

        Returns:
            AI superiority factor (0.5-1.5)
        """
        if not fleets:
            return 1.0

        avg_tech = sum(f.technology_modifier for f in fleets) / len(fleets)
        return avg_tech

    def _calc_avg_supply(self, fleets: List[FleetState]) -> float:
        """
        Calculate average supply level.

        Args:
            fleets: List of FleetState objects

        Returns:
            Average supply level (0-1)
        """
        if not fleets:
            return 1.0

        return sum(f.supply_level for f in fleets) / len(fleets)

    def _calc_avg_morale(self, fleets: List[FleetState]) -> float:
        """
        Calculate average morale level.

        Args:
            fleets: List of FleetState objects

        Returns:
            Average morale level (0-1)
        """
        if not fleets:
            return 1.0

        return sum(f.morale for f in fleets) / len(fleets)


__all__ = [
    "get_terrain_modifiers",
    "CombatResolver",
    "TERRAIN_MODIFIERS",
]

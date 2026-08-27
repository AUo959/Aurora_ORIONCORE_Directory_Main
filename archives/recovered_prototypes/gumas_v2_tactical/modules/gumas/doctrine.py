#!/usr/bin/env python3
"""
GUMAS L2 Doctrine Evolution System v2.0
Anchor: GUMAS-DOCTRINE-V2
Seed: EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP: L2_ENGINE_CORE

Q-learning doctrine evolution and Bayesian faction decision-making.
Factions adapt their military doctrines based on recent outcomes and
maintain learning states via Q-tables.
"""

import random
import uuid
from typing import Dict, List, Optional, Tuple

from modules.gumas.models import (
    GUMASState,
    TickResult,
    FactionState,
    DoctrineProfile,
    DoctrineType,
    SimulationEvent,
    EventType,
)
from modules.gumas.formulas import (
    calc_q_learning_update,
    calc_bayesian_faction_decision,
)


class DoctrineEngine:
    """
    Manages faction military doctrine evolution via Q-learning and
    Bayesian decision-making.

    Each faction maintains:
    - A current DoctrineType
    - A Q-table for reinforcement learning
    - Learning parameters (learning_rate, discount_factor, exploration_rate)
    - Adaptation history
    """

    def __init__(self, rng: random.Random) -> None:
        """
        Initialize DoctrineEngine.

        Args:
            rng: Random number generator for stochastic behavior
        """
        self.rng = rng
        self._recent_history: Dict[str, List[TickResult]] = {}

    def tick(self, state: GUMASState, result: TickResult) -> None:
        """
        Execute one game tick for doctrine evolution system.

        Each turn:
        1. Evaluate current doctrine effectiveness for each faction
        2. Check if any factions should shift doctrine
        3. Apply Q-learning updates based on outcomes
        4. Generate DOCTRINE_SHIFT events for significant changes

        Args:
            state: Current game state
            result: TickResult to accumulate events
        """
        # Track history for this faction
        for faction_id in state.factions:
            if faction_id not in self._recent_history:
                self._recent_history[faction_id] = []
            self._recent_history[faction_id].append(result)
            # Keep only last 5 ticks
            if len(self._recent_history[faction_id]) > 5:
                self._recent_history[faction_id].pop(0)

        # Process each faction
        for faction_id, faction in state.factions.items():
            if not faction.doctrine_id or faction.doctrine_id not in state.doctrines:
                continue

            doctrine = state.doctrines[faction.doctrine_id]
            recent_history = self._recent_history.get(faction_id, [])

            # Evaluate effectiveness
            effectiveness = self.evaluate_doctrine_effectiveness(
                faction,
                doctrine,
                recent_history,
            )

            # Check for doctrine shift
            new_doctrine = self.check_doctrine_shift(
                faction,
                doctrine,
                effectiveness,
            )

            if new_doctrine and new_doctrine != doctrine.current_doctrine:
                old_doctrine = doctrine.current_doctrine
                doctrine.current_doctrine = new_doctrine

                # Record adaptation in history
                doctrine.adaptation_history.append({
                    "turn": state.current_turn,
                    "from_doctrine": old_doctrine.value,
                    "to_doctrine": new_doctrine.value,
                    "effectiveness": effectiveness,
                })

                # Generate event
                event = SimulationEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=EventType.DOCTRINE_SHIFT,
                    turn=state.current_turn,
                    source_faction=faction_id,
                    affected_factions=[faction_id],
                    description=(
                        f"{faction.name} shifted military doctrine from "
                        f"{old_doctrine.value} to {new_doctrine.value}"
                    ),
                    magnitude=0.4,
                )
                result.events.append(event)

            # Apply Q-learning updates
            state_key = self._get_state_key(faction)
            action = self.select_action(doctrine, state_key)
            reward = self._compute_reward(faction, effectiveness)

            # Get max Q-value for next state (would be computed in real system)
            max_future_q = max(
                doctrine.q_table.get(state_key, {}).values()
            ) if state_key in doctrine.q_table else 0.0

            new_q = calc_q_learning_update(
                doctrine.q_table.get(state_key, {}).get(action, 0.0),
                reward,
                max_future_q,
                learning_rate=doctrine.learning_rate,
                discount_factor=doctrine.discount_factor,
            )

            # Update Q-table
            if state_key not in doctrine.q_table:
                doctrine.q_table[state_key] = {}
            doctrine.q_table[state_key][action] = new_q

    def evaluate_doctrine_effectiveness(
        self,
        faction: FactionState,
        doctrine: DoctrineProfile,
        recent_history: List[TickResult],
    ) -> float:
        """
        Score current doctrine based on recent outcomes.

        Calculates effectiveness from:
        - Won battles? +reward
        - Lost territory? -penalty
        - Economic growth? +reward
        - Took casualties? -penalty

        Args:
            faction: Faction to evaluate
            doctrine: Doctrine profile
            recent_history: List of recent TickResults

        Returns:
            Effectiveness score in [-1, 1]
        """
        score = 0.0
        weights = 0.0

        for tick_result in recent_history:
            # Check for military victories (FLEET_BATTLE events with positive outcome)
            for event in tick_result.events:
                if event.event_type == EventType.FLEET_BATTLE:
                    if faction.faction_id == event.source_faction:
                        score += event.magnitude * 0.5
                        weights += 0.5
                    elif faction.faction_id in event.affected_factions:
                        score -= event.magnitude * 0.3
                        weights += 0.3

                # Economic events
                elif event.event_type == EventType.ECONOMIC_BOOM:
                    if faction.faction_id in event.affected_factions:
                        score += 0.2
                        weights += 0.2

                elif event.event_type == EventType.ECONOMIC_SHOCK:
                    if faction.faction_id in event.affected_factions:
                        score -= 0.15
                        weights += 0.15

                # Territory/conflict events
                elif event.event_type == EventType.MILITARY_ESCALATION:
                    if faction.faction_id == event.source_faction:
                        # Escalation initiated by us: slight negative if losing
                        if faction.power_level < 0.5:
                            score -= 0.1
                    else:
                        # Escalation against us
                        if faction.power_level > 0.6:
                            score += 0.1
                    weights += 0.1

        # Normalize score
        if weights > 0:
            score = score / weights

        # Clamp to [-1, 1]
        return max(-1.0, min(1.0, score))

    def select_action(
        self,
        doctrine: DoctrineProfile,
        state_key: str,
    ) -> str:
        """
        Epsilon-greedy action selection from Q-table.

        With probability exploration_rate: pick random action
        Else: pick action with highest Q value for current state

        Actions: "escalate", "defend", "negotiate", "sabotage",
                 "trade", "retreat", "ally"

        Args:
            doctrine: Doctrine profile with Q-table
            state_key: Current state key

        Returns:
            Selected action string
        """
        actions = [
            "escalate",
            "defend",
            "negotiate",
            "sabotage",
            "trade",
            "retreat",
            "ally",
        ]

        # Epsilon-greedy
        if self.rng.random() < doctrine.exploration_rate:
            return self.rng.choice(actions)

        # Greedy: pick best action
        if state_key in doctrine.q_table:
            q_values = doctrine.q_table[state_key]
            if q_values:
                return max(q_values, key=q_values.get)

        return self.rng.choice(actions)

    def update_q_table(
        self,
        doctrine: DoctrineProfile,
        state_key: str,
        action: str,
        reward: float,
        next_state_key: str,
    ) -> None:
        """
        Update Q-table using Q-learning formula.

        Uses calc_q_learning_update to compute new Q-value.

        Args:
            doctrine: Doctrine profile to update
            state_key: Current state key
            action: Action taken
            reward: Immediate reward
            next_state_key: Next state key
        """
        # Get max Q-value in next state
        max_future_q = max(
            doctrine.q_table.get(next_state_key, {}).values()
        ) if next_state_key in doctrine.q_table else 0.0

        current_q = doctrine.q_table.get(state_key, {}).get(action, 0.0)

        new_q = calc_q_learning_update(
            current_q,
            reward,
            max_future_q,
            learning_rate=doctrine.learning_rate,
            discount_factor=doctrine.discount_factor,
        )

        # Update Q-table
        if state_key not in doctrine.q_table:
            doctrine.q_table[state_key] = {}
        doctrine.q_table[state_key][action] = new_q

    def check_doctrine_shift(
        self,
        faction: FactionState,
        doctrine: DoctrineProfile,
        effectiveness: float,
    ) -> Optional[DoctrineType]:
        """
        Check if faction should shift doctrine based on effectiveness.

        If effectiveness < -0.3 for 3+ consecutive turns, shift doctrine.

        Shift logic:
        - CONVENTIONAL → DEFENSIVE if losing
        - DEFENSIVE → ASYMMETRIC if still losing
        - EXPANSIONIST → GUERRILLA if overstretched
        - CYBER → DEFENSIVE if tech advantage lost
        - ASYMMETRIC → GUERRILLA if desperate
        - GUERRILLA → DEFENSIVE if must consolidate
        - DETERRENCE → CONVENTIONAL if threat reduced

        Args:
            faction: Faction to evaluate
            doctrine: Current doctrine
            effectiveness: Effectiveness score

        Returns:
            New DoctrineType if shift recommended, None otherwise
        """
        # Count recent poor performance
        recent_poor_turns = 0
        for entry in doctrine.adaptation_history[-3:]:
            if entry.get("effectiveness", 0) < -0.3:
                recent_poor_turns += 1

        # Trigger shift if 3 consecutive poor turns
        if recent_poor_turns >= 3:
            current = doctrine.current_doctrine

            if current == DoctrineType.CONVENTIONAL:
                if faction.military_strength < 0.4:
                    return DoctrineType.DEFENSIVE
            elif current == DoctrineType.DEFENSIVE:
                if faction.military_strength < 0.3:
                    return DoctrineType.ASYMMETRIC
            elif current == DoctrineType.EXPANSIONIST:
                if faction.controlled_locations and len(faction.controlled_locations) > 8:
                    return DoctrineType.GUERRILLA
            elif current == DoctrineType.CYBER:
                if faction.technological_level < 0.4:
                    return DoctrineType.DEFENSIVE
            elif current == DoctrineType.ASYMMETRIC:
                if faction.military_strength < 0.2:
                    return DoctrineType.GUERRILLA
            elif current == DoctrineType.GUERRILLA:
                if faction.public_stability < 0.3:
                    return DoctrineType.DEFENSIVE
            elif current == DoctrineType.DETERRENCE:
                if faction.power_level > 0.6:
                    return DoctrineType.CONVENTIONAL

        return None

    def make_faction_decision(
        self,
        faction: FactionState,
        scenario_context: Dict,
        memory: List[Dict],
    ) -> Dict[str, float]:
        """
        Use Bayesian faction decision-making.

        Combines scenario weights and historical memory to compute
        probability distribution over possible actions.

        Args:
            faction: Faction making decision
            scenario_context: Current scenario weights for actions
            memory: List of past interaction outcomes

        Returns:
            Dict of action probabilities summing to 1.0
        """
        # Build memory weights from historical outcomes
        memory_weights = {
            "escalate": 0.0,
            "defend": 0.0,
            "negotiate": 0.0,
            "sabotage": 0.0,
            "trade": 0.0,
            "retreat": 0.0,
            "ally": 0.0,
        }

        success_counts = {action: 0 for action in memory_weights}
        total_counts = {action: 0 for action in memory_weights}

        for entry in memory:
            action = entry.get("action")
            success = entry.get("success", False)
            if action in success_counts:
                total_counts[action] += 1
                if success:
                    success_counts[action] += 1

        # Compute memory weights (success rate)
        for action in memory_weights:
            if total_counts[action] > 0:
                memory_weights[action] = success_counts[action] / total_counts[action]
            else:
                memory_weights[action] = 0.5  # Default neutral

        # Apply bias modifier based on faction leadership
        bias_modifier = 1.0
        if faction.leader_id:
            # Leaders with high legitimacy/competency make better decisions
            bias_modifier = 0.8 + faction.legitimacy * 0.2 + faction.technological_level * 0.1

        # Use Bayesian formula
        decision_probs = calc_bayesian_faction_decision(
            scenario_context,
            memory_weights,
            bias_modifier,
        )

        return decision_probs

    def _get_state_key(self, faction: FactionState) -> str:
        """
        Generate state key for Q-learning.

        Encodes relevant faction state into a hashable string.

        Args:
            faction: Faction to encode

        Returns:
            State key string
        """
        # Discretize faction attributes into bins
        power_bin = int(faction.power_level * 4)  # 0-3
        military_bin = int(faction.military_strength * 4)  # 0-3
        tech_bin = int(faction.technological_level * 4)  # 0-3
        economy_bin = int(faction.economy_strength * 4)  # 0-3
        conflicts_bin = min(3, len(faction.active_conflicts))  # 0-3

        return f"p{power_bin}_m{military_bin}_t{tech_bin}_e{economy_bin}_c{conflicts_bin}"

    def _compute_reward(
        self,
        faction: FactionState,
        effectiveness: float,
    ) -> float:
        """
        Compute reward signal for Q-learning.

        Args:
            faction: Faction to reward/penalize
            effectiveness: Doctrine effectiveness score

        Returns:
            Reward value
        """
        # Base reward from effectiveness
        reward = effectiveness

        # Bonus for stable/growing factions
        if faction.power_level > 0.6:
            reward += 0.1

        # Penalty for low stability
        if faction.public_stability < 0.3:
            reward -= 0.15

        # Penalty for many losses
        if len(faction.active_conflicts) > 3:
            reward -= 0.2

        return max(-1.0, min(1.0, reward))


def build_default_doctrines(factions: Dict[str, FactionState]) -> Dict[str, DoctrineProfile]:
    """
    Build default doctrine profiles for all factions.

    Assign default doctrines based on faction characteristics and type.

    Args:
        factions: Dictionary of all factions

    Returns:
        Dictionary mapping faction_id to DoctrineProfile
    """
    default_doctrines_map = {
        "galactic_union": DoctrineType.CONVENTIONAL,
        "velar_imperium": DoctrineType.EXPANSIONIST,
        "ai_warlord": DoctrineType.CYBER,
        "prime_construct": DoctrineType.DETERRENCE,
        "separatist_confed": DoctrineType.GUERRILLA,
        "pmc_syndicate": DoctrineType.CONVENTIONAL,
        "crimson_pact": DoctrineType.ASYMMETRIC,
        "outer_colonies": DoctrineType.DEFENSIVE,
        "zyphari_compact": DoctrineType.DETERRENCE,
    }

    doctrines = {}

    for faction_id, faction in factions.items():
        # Get doctrine from mapping or use CONVENTIONAL as default
        doctrine_type = default_doctrines_map.get(faction_id, DoctrineType.CONVENTIONAL)

        # Create doctrine profile
        doctrine = DoctrineProfile(
            faction_id=faction_id,
            current_doctrine=doctrine_type,
            q_table={},
            learning_rate=0.1,
            discount_factor=0.9,
            exploration_rate=0.2,
            adaptation_history=[],
        )

        doctrines[faction_id] = doctrine

        # Link doctrine to faction
        faction.doctrine_id = faction_id

    return doctrines


__all__ = [
    "DoctrineEngine",
    "build_default_doctrines",
]

#!/usr/bin/env python3
"""
GUMAS L2 Sentinel Operative System v2.0
Anchor: GUMAS-SENTINELS-V2
Seed: EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP: L2_ENGINE_CORE

Sentinel operative mission system with skill advancement.
Operatives conduct covert operations for their factions, gaining
experience and advancing in rank.
"""

import random
import uuid
from typing import Dict, List, Optional

from modules.gumas.models import (
    GUMASState,
    TickResult,
    SentinelOperative,
    SentinelRank,
    MissionState,
    MissionType,
    SimulationEvent,
    EventType,
)
from modules.gumas.formulas import (
    calc_mission_success_probability,
    calc_sentinel_adaptation,
    calc_double_agent_risk,
)


class SentinelEngine:
    """
    Manages sentinel operative missions, advancement, and covert operations.

    Each faction can have 1-3 operatives conducting various mission types.
    Operatives gain experience, advance in rank, and may become double agents.
    """

    def __init__(self, rng: random.Random) -> None:
        """
        Initialize SentinelEngine.

        Args:
            rng: Random number generator for stochastic behavior
        """
        self.rng = rng
        self._active_missions: Dict[str, MissionState] = {}

    def tick(self, state: GUMASState, result: TickResult) -> None:
        """
        Execute one game tick for sentinel operative system.

        Each turn:
        1. Progress active missions (reduce turns_remaining)
        2. Resolve completed missions
        3. Apply mission outcomes
        4. Check for double-agent exposure
        5. Advance operative experience and rank
        6. Generate new mission opportunities

        Args:
            state: Current game state
            result: TickResult to accumulate events
        """
        self.progress_missions(state, result)
        self.resolve_completed_missions(state, result)
        self.check_double_agents(state, result)
        self.generate_missions(state, result)

    def progress_missions(self, state: GUMASState, result: TickResult) -> None:
        """
        Reduce turns_remaining for active missions.

        Args:
            state: Current game state
            result: TickResult to accumulate events
        """
        for mission_id, mission in state.missions.items():
            if not mission.is_complete:
                mission.turns_remaining = max(0, mission.turns_remaining - 1)

    def assign_mission(
        self,
        state: GUMASState,
        operative_id: str,
        mission_type: MissionType,
        target_faction: str,
        target_location: Optional[str],
        difficulty: float,
    ) -> MissionState:
        """
        Create and assign a new mission to an operative.

        Calculate initial success probability using calc_mission_success_probability.
        Duration based on mission type:
        - RECON: 2 turns
        - SABOTAGE: 3 turns
        - ASSASSINATION: 4 turns
        - EXTRACTION: 2 turns
        - DIPLOMACY: 3 turns
        - COUNTERINTEL: 3 turns
        - ARTIFACT_RECOVERY: 5 turns

        Args:
            state: Current game state
            operative_id: ID of operative to assign
            mission_type: Type of mission
            target_faction: Faction being targeted
            target_location: Optional location for mission
            difficulty: Mission difficulty (0-1)

        Returns:
            Created MissionState
        """
        if operative_id not in state.operatives:
            raise ValueError(f"Operative {operative_id} not found")

        operative = state.operatives[operative_id]

        # Get operative skill relevant to mission type
        if mission_type == MissionType.RECONNAISSANCE:
            operative_skill = operative.stealth_skill
        elif mission_type == MissionType.SABOTAGE:
            operative_skill = operative.tech_skill
        elif mission_type == MissionType.ASSASSINATION:
            operative_skill = operative.combat_skill
        elif mission_type == MissionType.EXTRACTION:
            operative_skill = operative.stealth_skill
        elif mission_type == MissionType.DIPLOMACY:
            operative_skill = operative.diplomacy_skill
        elif mission_type == MissionType.COUNTERINTEL:
            operative_skill = operative.stealth_skill
        elif mission_type == MissionType.ARTIFACT_RECOVERY:
            operative_skill = operative.tech_skill
        else:
            operative_skill = 0.5

        # Calculate success probability
        success_prob = calc_mission_success_probability(
            operative_skill,
            difficulty,
            support_level=0.0,
            counter_intel=0.0,
        )

        # Determine mission duration
        duration_map = {
            MissionType.RECONNAISSANCE: 2,
            MissionType.SABOTAGE: 3,
            MissionType.ASSASSINATION: 4,
            MissionType.EXTRACTION: 2,
            MissionType.DIPLOMACY: 3,
            MissionType.COUNTERINTEL: 3,
            MissionType.ARTIFACT_RECOVERY: 5,
        }
        duration = duration_map.get(mission_type, 3)

        # Create mission
        mission = MissionState(
            mission_id=str(uuid.uuid4()),
            mission_type=mission_type,
            assigned_operative=operative_id,
            target_faction=target_faction,
            target_location=target_location,
            difficulty=difficulty,
            success_probability=success_prob,
            turns_remaining=duration,
            is_complete=False,
            outcome=None,
        )

        state.missions[mission.mission_id] = mission
        self._active_missions[mission.mission_id] = mission

        return mission

    def resolve_completed_missions(
        self,
        state: GUMASState,
        result: TickResult,
    ) -> None:
        """
        Resolve missions that have completed (turns_remaining <= 0).

        For each completed mission:
        - Roll against success_probability
        - Apply mission-specific outcomes
        - Update operative stats
        - Generate events

        Args:
            state: Current game state
            result: TickResult to accumulate events
        """
        completed_missions = [
            mid for mid, m in state.missions.items()
            if m.turns_remaining <= 0 and not m.is_complete
        ]

        for mission_id in completed_missions:
            mission = state.missions[mission_id]
            operative = state.operatives[mission.assigned_operative]

            # Roll success
            mission_success = self.rng.random() < mission.success_probability
            mission.outcome = "success" if mission_success else "failure"
            mission.is_complete = True

            # Apply outcomes based on mission type
            if mission_success:
                self._apply_mission_success(
                    state,
                    mission,
                    operative,
                    result,
                )
            else:
                self._apply_mission_failure(
                    state,
                    mission,
                    operative,
                    result,
                )

            # Update operative stats
            self.advance_operative(operative, mission_success, mission.difficulty)

    def _apply_mission_success(
        self,
        state: GUMASState,
        mission: MissionState,
        operative: SentinelOperative,
        result: TickResult,
    ) -> None:
        """
        Apply outcomes of successful mission.

        Args:
            state: Current game state
            mission: Completed mission
            operative: Operative who executed mission
            result: TickResult to accumulate events
        """
        operative.missions_completed += 1
        target_faction = state.factions.get(mission.target_faction)

        if mission.mission_type == MissionType.RECONNAISSANCE:
            description = (
                f"Operative {operative.name} successfully gathered intelligence "
                f"on {mission.target_faction}"
            )
            if target_faction:
                target_faction.diplomatic_capital = max(
                    0.0,
                    target_faction.diplomatic_capital - 0.05,
                )

        elif mission.mission_type == MissionType.SABOTAGE:
            description = (
                f"Operative {operative.name} successfully sabotaged "
                f"{mission.target_faction} operations"
            )
            if target_faction:
                target_faction.economy_strength = max(
                    0.0,
                    target_faction.economy_strength - 0.05,
                )

        elif mission.mission_type == MissionType.ASSASSINATION:
            description = (
                f"Operative {operative.name} eliminated key target in "
                f"{mission.target_faction}"
            )
            if target_faction and target_faction.leader_id:
                # Generate leader change event
                old_leader_id = target_faction.leader_id
                target_faction.leader_id = f"replacement_{uuid.uuid4()}"

                event = SimulationEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=EventType.LEADER_CHANGE,
                    turn=state.current_turn,
                    source_faction=operative.faction_id,
                    affected_factions=[mission.target_faction],
                    description=(
                        f"Leader of {mission.target_faction} was assassinated "
                        f"by sentinel operative"
                    ),
                    magnitude=0.8,
                )
                result.events.append(event)

        elif mission.mission_type == MissionType.EXTRACTION:
            description = (
                f"Operative {operative.name} successfully extracted asset "
                f"from {mission.target_faction}"
            )

        elif mission.mission_type == MissionType.DIPLOMACY:
            description = (
                f"Operative {operative.name} improved relations with "
                f"{mission.target_faction}"
            )
            if target_faction:
                operative_faction = state.factions.get(operative.faction_id)
                if operative_faction:
                    operative_faction.known_relations[mission.target_faction] = min(
                        1.0,
                        operative_faction.known_relations.get(
                            mission.target_faction,
                            0.5,
                        ) + 0.1,
                    )

        elif mission.mission_type == MissionType.COUNTERINTEL:
            description = (
                f"Operative {operative.name} exposed enemy operatives "
                f"in {mission.target_faction}"
            )
            if target_faction:
                target_faction.active_operatives = [
                    op for op in target_faction.active_operatives
                    if self.rng.random() > 0.3  # 30% chance each operative exposed
                ]

        elif mission.mission_type == MissionType.ARTIFACT_RECOVERY:
            description = (
                f"Operative {operative.name} recovered precursor artifact data "
                f"from {mission.target_faction}"
            )
            if mission.target_location and mission.target_location in state.precursor_sites:
                site = state.precursor_sites[mission.target_location]
                # Advance discovery phase
                from modules.gumas.models import DiscoveryPhase
                if site.discovery_phase == DiscoveryPhase.DORMANT:
                    site.discovery_phase = DiscoveryPhase.DETECTED

        else:
            description = f"Operative {operative.name} completed mission against {mission.target_faction}"

        # Generate event
        event = SimulationEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.SENTINEL_MISSION,
            turn=state.current_turn,
            source_faction=operative.faction_id,
            affected_factions=[mission.target_faction],
            description=description,
            magnitude=0.5,
        )
        result.events.append(event)

    def _apply_mission_failure(
        self,
        state: GUMASState,
        mission: MissionState,
        operative: SentinelOperative,
        result: TickResult,
    ) -> None:
        """
        Apply outcomes of failed mission.

        Args:
            state: Current game state
            mission: Failed mission
            operative: Operative who executed mission
            result: TickResult to accumulate events
        """
        operative.missions_failed += 1
        operative.is_active = False  # Mark as captured/killed

        target_faction = state.factions.get(mission.target_faction)
        operative_faction = state.factions.get(operative.faction_id)

        if operative_faction and target_faction:
            operative_faction.known_relations[mission.target_faction] = max(
                -1.0,
                operative_faction.known_relations.get(mission.target_faction, 0.5) - 0.15,
            )

        # Generate exposure event
        event = SimulationEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.ESPIONAGE_EXPOSURE,
            turn=state.current_turn,
            source_faction=operative.faction_id,
            affected_factions=[mission.target_faction, operative.faction_id],
            description=(
                f"Operative {operative.name} captured/killed during mission "
                f"against {mission.target_faction}"
            ),
            magnitude=0.7,
        )
        result.events.append(event)

    def advance_operative(
        self,
        operative: SentinelOperative,
        mission_success: bool,
        mission_difficulty: float,
    ) -> None:
        """
        Advance operative skills and rank based on mission outcomes.

        Uses calc_sentinel_adaptation to update skill levels.
        Updates rank based on experience threshold:
        - 0.0→0.3: CADET
        - 0.3→0.5: OPERATIVE
        - 0.5→0.7: SPECIALIST
        - 0.7→0.9: COMMANDER
        - 0.9→1.0: ELITE

        Args:
            operative: Operative to advance
            mission_success: Whether mission succeeded
            mission_difficulty: Difficulty of mission
        """
        # Update all relevant skills
        operative.combat_skill = calc_sentinel_adaptation(
            operative.combat_skill,
            mission_success,
            mission_difficulty,
        )
        operative.stealth_skill = calc_sentinel_adaptation(
            operative.stealth_skill,
            mission_success,
            mission_difficulty,
        )
        operative.diplomacy_skill = calc_sentinel_adaptation(
            operative.diplomacy_skill,
            mission_success,
            mission_difficulty * 0.7,  # Less weight on diplomacy
        )
        operative.tech_skill = calc_sentinel_adaptation(
            operative.tech_skill,
            mission_success,
            mission_difficulty,
        )

        # Update experience
        if mission_success:
            operative.experience = min(
                1.0,
                operative.experience + 0.05 * mission_difficulty,
            )
        else:
            operative.experience = max(
                0.0,
                operative.experience - 0.02 * mission_difficulty,
            )

        # Update rank
        rank_thresholds = [
            (0.0, SentinelRank.CADET),
            (0.3, SentinelRank.OPERATIVE),
            (0.5, SentinelRank.SPECIALIST),
            (0.7, SentinelRank.COMMANDER),
            (0.9, SentinelRank.ELITE),
        ]

        for threshold, rank in rank_thresholds:
            if operative.experience >= threshold:
                operative.rank = rank
            else:
                break

    def check_double_agents(
        self,
        state: GUMASState,
        result: TickResult,
    ) -> None:
        """
        Check for double-agent infiltration and exposure.

        For each operative: if is_double_agent, chance per turn of leaking intel.
        Uses calc_double_agent_risk. If exposed, generate ESPIONAGE_EXPOSURE event.

        Args:
            state: Current game state
            result: TickResult to accumulate events
        """
        for operative_id, operative in state.operatives.items():
            if not operative.is_double_agent:
                continue

            # Get bilateral trust
            from_faction = state.factions.get(operative.faction_id)
            cover_faction = state.factions.get(operative.cover_faction)

            if not from_faction or not cover_faction:
                continue

            bilateral_trust = from_faction.known_relations.get(
                operative.cover_faction,
                0.5,
            )

            # Calculate double agent risk
            risk = calc_double_agent_risk(
                bilateral_trust,
                intel_sensitivity=0.7,
            )

            # Check for exposure
            if self.rng.random() < risk * 0.15:  # 15% of risk per turn
                operative.is_active = False
                operative.is_double_agent = False

                # Reduce trust significantly
                from_faction.known_relations[operative.cover_faction] = max(
                    -1.0,
                    bilateral_trust - 0.3,
                )

                # Generate exposure event
                event = SimulationEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=EventType.ESPIONAGE_EXPOSURE,
                    turn=state.current_turn,
                    source_faction=operative.cover_faction,
                    affected_factions=[operative.faction_id, operative.cover_faction],
                    description=(
                        f"Double agent {operative.name} exposed in "
                        f"{operative.cover_faction}"
                    ),
                    magnitude=0.8,
                )
                result.events.append(event)

    def generate_missions(
        self,
        state: GUMASState,
        result: TickResult,
    ) -> None:
        """
        Automatically generate mission opportunities based on game state.

        Mission opportunities:
        - Low trust pairs → SABOTAGE/COUNTERINTEL opportunities
        - Active conflicts → RECONNAISSANCE missions
        - Precursor sites → ARTIFACT_RECOVERY opportunities
        - High tension → ASSASSINATION risk

        Args:
            state: Current game state
            result: TickResult to accumulate events
        """
        # Generate opportunity log but don't auto-assign
        # (In a full system, an AI decision-maker would assign these)

        for operative_id, operative in state.operatives.items():
            if not operative.is_active:
                continue

            # Check for current missions
            active_for_operative = [
                m for m in state.missions.values()
                if m.assigned_operative == operative_id and not m.is_complete
            ]

            if active_for_operative:
                continue  # Operative already has mission

            # Look for opportunity
            faction = state.factions.get(operative.faction_id)
            if not faction:
                continue

            # Find potential target (faction with low trust)
            potential_targets = [
                (fid, f) for fid, f in state.factions.items()
                if fid != operative.faction_id
                and faction.known_relations.get(fid, 0.5) < 0.4
            ]

            if not potential_targets:
                continue

            target_fid, _ = self.rng.choice(potential_targets)

            # 20% chance per turn to create opportunity
            if self.rng.random() < 0.2:
                mission_type = self.rng.choice([
                    MissionType.RECONNAISSANCE,
                    MissionType.SABOTAGE,
                    MissionType.COUNTERINTEL,
                ])

                # Auto-assign mission
                try:
                    self.assign_mission(
                        state,
                        operative_id,
                        mission_type,
                        target_fid,
                        target_location=None,
                        difficulty=self.rng.uniform(0.2, 0.7),
                    )
                except ValueError:
                    pass  # Operative no longer exists


def build_default_operatives(
    factions: Dict[str, object],
) -> Dict[str, SentinelOperative]:
    """
    Build default sentinel operatives for each faction.

    Give each major faction 1-2 starting operatives with faction-appropriate
    skill distributions. Union gets a named operative "Elias Radek" as COMMANDER rank.

    Args:
        factions: Dictionary of all factions

    Returns:
        Dictionary mapping operative_id to SentinelOperative
    """
    operatives: Dict[str, SentinelOperative] = {}

    # Named operative for Galactic Union
    operatives["elias_radek"] = SentinelOperative(
        operative_id="elias_radek",
        name="Elias Radek",
        faction_id="galactic_union",
        rank=SentinelRank.COMMANDER,
        combat_skill=0.75,
        stealth_skill=0.8,
        diplomacy_skill=0.7,
        tech_skill=0.65,
        experience=0.75,
        missions_completed=15,
        missions_failed=2,
        is_active=True,
        is_double_agent=False,
    )

    # Default operatives by faction
    faction_operatives = {
        "galactic_union": [
            SentinelOperative(
                operative_id="gu_op_002",
                name="Agent Echo",
                faction_id="galactic_union",
                rank=SentinelRank.OPERATIVE,
                combat_skill=0.6,
                stealth_skill=0.75,
                diplomacy_skill=0.65,
                tech_skill=0.6,
                experience=0.35,
                missions_completed=5,
                missions_failed=1,
            ),
        ],
        "velar_imperium": [
            SentinelOperative(
                operative_id="vi_op_001",
                name="Vex'Tor",
                faction_id="velar_imperium",
                rank=SentinelRank.SPECIALIST,
                combat_skill=0.85,
                stealth_skill=0.6,
                diplomacy_skill=0.5,
                tech_skill=0.55,
                experience=0.5,
                missions_completed=8,
                missions_failed=2,
            ),
        ],
        "ai_warlord": [
            SentinelOperative(
                operative_id="aw_op_001",
                name="Protocol-7",
                faction_id="ai_warlord",
                rank=SentinelRank.SPECIALIST,
                combat_skill=0.7,
                stealth_skill=0.65,
                diplomacy_skill=0.4,
                tech_skill=0.9,
                experience=0.55,
                missions_completed=10,
                missions_failed=1,
            ),
        ],
        "prime_construct": [
            SentinelOperative(
                operative_id="pc_op_001",
                name="Architect-5",
                faction_id="prime_construct",
                rank=SentinelRank.OPERATIVE,
                combat_skill=0.55,
                stealth_skill=0.7,
                diplomacy_skill=0.6,
                tech_skill=0.85,
                experience=0.32,
                missions_completed=4,
                missions_failed=0,
            ),
        ],
    }

    for faction_id, ops_list in faction_operatives.items():
        for op in ops_list:
            operatives[op.operative_id] = op

    return operatives


__all__ = [
    "SentinelEngine",
    "build_default_operatives",
]

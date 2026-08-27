#!/usr/bin/env python3
"""
GUMAS L2 Multi-Agent Galactic Simulation Engine v2.0
=======================================================
Anchor: GUMAS-ENGINE-CORE-V2
Seed: EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP: L2_ENGINE_CORE
Version: 2.0.0

v2.0 integrates all subsystems:
- Galaxy Topology (hyperlane network, spatial movement)
- Military Combat Resolution (fleet battles, terrain modifiers)
- Economic Trade System (supply/demand, sanctions, corporate capture)
- Media Ecosystem (propaganda, public opinion, legitimacy)
- Precursor Artifacts (discovery, activation, power unlocks)
- Sentinel Operatives (missions, skill advancement, espionage)
- Doctrine Evolution (Q-learning AI adaptation)
- Cultural Movements (spread, influence, soft power)
- Enhanced Forecaster (Monte Carlo ensemble with interventions)

Plus all v1.0 systems:
- 15-phase tick lifecycle
- 33 event types
- Coalition lifecycle
- Asymmetric trust
- Leader bias evolution
- Treaty negotiation
- Conflict de-escalation
"""

from __future__ import annotations
import json
import logging
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from copy import deepcopy

from modules.gumas.formulas import (
    apply_bias_hooks, calc_bias_evolution, calc_coalition_stability,
    calc_coalition_utility, calc_deescalation_probability,
    calc_double_agent_risk, calc_reputation_after_decay,
    calc_treaty_breach_score, calc_trust_update, is_treaty_breach,
    calc_combat_outcome, calc_combat_losses, calc_q_learning_update,
    calc_bayesian_faction_decision, calc_sentinel_adaptation,
    calc_economic_equilibrium, calc_trade_flow, calc_corporate_capture_pressure,
    calc_propaganda_effectiveness, calc_media_legitimacy_impact,
    calc_precursor_activation_risk, calc_precursor_power_output,
    calc_mission_success_probability, calc_culture_spread_rate,
    calc_fleet_supply_decay, calc_war_exhaustion, _clamp,
)
from modules.gumas.models import (
    BiasType, CertaintyTag, CoalitionState, CoalitionType,
    ConflictPhase, ConflictState, EventType, FactionState,
    GUMASState, LeaderState, SimulationEvent, TickResult,
    TreatyPhase, TreatyState, FleetState, CombatState,
    BattlefieldCondition, DoctrineProfile, DoctrineType,
    SentinelOperative, SentinelRank, MissionType, MissionState,
    PrecursorSite, DiscoveryPhase, PrecursorOrigin,
    CultureMovement, ResourceType, TopologyNode,
    NarrativeState, MediaOutlet,
)
from modules.gumas.scenarios import build_default_scenario
from modules.gumas.topology import TopologyManager
from modules.gumas.combat import CombatResolver
from modules.gumas.economics import EconomicEngine
from modules.gumas.media import MediaEngine
from modules.gumas.precursors import PrecursorEngine
from modules.gumas.doctrine import DoctrineEngine
from modules.gumas.sentinels import SentinelEngine

logger = logging.getLogger("gumas.engine.v2")


class GUMASEngine:
    """
    Master simulation engine integrating v1.0 and v2.0 subsystems.

    Maintains full backward compatibility while adding:
    - Fleet movement and combat
    - Economic simulation
    - Media/narrative systems
    - Precursor artifacts
    - Sentinel espionage
    - Doctrine adaptation
    - Cultural movements
    """

    def __init__(
        self,
        seed: int = 42,
        ethics_callback: Optional[Callable[[str, Dict[str, Any]], bool]] = None,
    ):
        """
        Initialize GUMAS Engine v2.0.

        Args:
            seed: Random seed for reproducibility
            ethics_callback: Optional function(action_type, params) -> bool for ethics checks
        """
        self._rng = random.Random(seed)
        self._state: Optional[GUMASState] = None
        self._ethics_callback = ethics_callback
        self._tick_counter = 0

        # Sub-engines initialized after scenario load
        self._topology_manager: Optional[TopologyManager] = None
        self._combat_resolver = CombatResolver(self._rng)
        self._economic_engine = EconomicEngine(self._rng)
        self._media_engine = MediaEngine(self._rng)
        self._precursor_engine = PrecursorEngine(self._rng)
        self._doctrine_engine = DoctrineEngine(self._rng)
        self._sentinel_engine = SentinelEngine(self._rng)

        # Event handler dispatch table
        self._EVENT_HANDLERS: Dict[EventType, Callable] = {
            EventType.MILITARY_ESCALATION: self._handle_military_escalation,
            EventType.DIPLOMATIC_OVERTURE: self._handle_diplomatic_overture,
            EventType.ECONOMIC_SHOCK: self._handle_economic_shock,
            EventType.ESPIONAGE_EXPOSURE: self._handle_espionage_exposure,
            EventType.TREATY_VIOLATION: self._handle_treaty_violation,
            EventType.MEDIATION_OFFER: self._handle_mediation_offer,
            EventType.TRADE_AGREEMENT: self._handle_trade_agreement,
            EventType.ECONOMIC_BOOM: self._handle_economic_boom,
            EventType.TECHNOLOGY_BREAKTHROUGH: self._handle_technology_breakthrough,
            EventType.CULTURAL_MOVEMENT: self._handle_cultural_movement,
            EventType.INFRASTRUCTURE_INVESTMENT: self._handle_infrastructure_investment,
            EventType.INTERNAL_COUP: self._handle_internal_coup,
            EventType.LEADER_CHANGE: self._handle_leader_change,
            EventType.TREATY_PROPOSAL: self._handle_treaty_proposal,
            EventType.INTELLIGENCE_LEAK: self._handle_intelligence_leak,
            EventType.HUMANITARIAN_CRISIS: self._handle_humanitarian_crisis,
            EventType.CUSTOM: self._handle_custom,
            EventType.FLEET_MOVEMENT: self._handle_fleet_movement,
            EventType.FLEET_BATTLE: self._handle_fleet_battle,
            EventType.PRECURSOR_DISCOVERY: self._handle_precursor_discovery,
            EventType.PRECURSOR_ACTIVATION: self._handle_precursor_activation,
            EventType.SENTINEL_MISSION: self._handle_sentinel_mission,
            EventType.CORPORATE_TAKEOVER: self._handle_corporate_takeover,
            EventType.MEDIA_CAMPAIGN: self._handle_media_campaign,
            EventType.DOCTRINE_SHIFT: self._handle_doctrine_shift,
            EventType.CULTURE_SPREAD: self._handle_culture_spread,
            EventType.RESOURCE_CRISIS: self._handle_resource_crisis,
            EventType.BLOCKADE: self._handle_blockade,
            EventType.COUP_ATTEMPT: self._handle_coup_attempt,
            EventType.ALLIANCE_FORMATION: self._handle_alliance_formation,
            EventType.ALLIANCE_DISSOLUTION: self._handle_alliance_dissolution,
            EventType.SANCTIONS_IMPOSED: self._handle_sanctions_imposed,
            EventType.SANCTIONS_LIFTED: self._handle_sanctions_lifted,
        }

    def init_scenario(
        self,
        state: Optional[GUMASState] = None,
        scenario_id: str = "gumas_canonical_v2",
    ) -> GUMASState:
        """
        Initialize simulation with a scenario.

        Args:
            state: Existing state to load (if None, create from scenario_id)
            scenario_id: Scenario name to build

        Returns:
            Initialized GUMASState
        """
        if state is None:
            state = build_default_scenario(scenario_id, self._rng.randint(0, 1000000))

        self._state = state
        self._tick_counter = 0

        # Initialize sub-engines with state
        if state.topology:
            self._topology_manager = TopologyManager(state.topology)
        else:
            self._topology_manager = None

        logger.info(f"Initialized GUMAS v2.0 with scenario '{scenario_id}'")
        return state

    def step(self) -> TickResult:
        """
        Execute one complete simulation tick (15 phases).

        Returns:
            TickResult with state changes and events
        """
        self._require_init()

        result = TickResult(
            turn=self._state.turn,
            events_processed=[],
            events_generated=[],
            state_changes=[],
            ethics_flags=[],
        )

        # 15-phase tick lifecycle
        self._process_event_queue(result)           # Phase 1
        self._update_leader_hooks(result)           # Phase 2
        self._evaluate_conflicts(result)            # Phase 3
        self._evaluate_treaties(result)             # Phase 4
        self._peacetime_recovery(result)            # Phase 5
        self._diplomacy_tick(result)                # Phase 6
        self._coalition_lifecycle(result)           # Phase 7
        self._fleet_movement_tick(result)           # Phase 8
        self._combat_resolution_tick(result)        # Phase 9
        self._economic_tick(result)                 # Phase 10
        self._media_tick(result)                    # Phase 11
        self._precursor_tick(result)                # Phase 12
        self._sentinel_tick(result)                 # Phase 13
        self._doctrine_tick(result)                 # Phase 14
        self._culture_tick(result)                  # Phase 15a
        self._generate_emergent_events(result)      # Phase 15b

        self._state.turn += 1
        self._tick_counter += 1
        self._state.history.append(result)
        return result

    def _append_state_change(self, result: TickResult, change: str) -> None:
        """Helper to track state changes."""
        result.state_changes.append(change)

    def run(self, n_turns: int = 1) -> List[TickResult]:
        """
        Execute multiple ticks.

        Args:
            n_turns: Number of ticks to run

        Returns:
            List of TickResults
        """
        results = []
        for _ in range(n_turns):
            results.append(self.step())
        return results

    def get_state(self) -> GUMASState:
        """Get current simulation state."""
        self._require_init()
        return self._state

    def inject_event(self, event: SimulationEvent) -> None:
        """
        Inject an event into the queue.

        Args:
            event: SimulationEvent to add
        """
        self._require_init()
        self._state.event_queue.append(event)

    def export_state(
        self,
        path: Optional[str] = None,
        include_history: bool = False,
    ) -> Optional[Dict]:
        """
        Export state to JSON.

        Args:
            path: File path to write to (if None, return dict)
            include_history: Include full history

        Returns:
            State dict if path is None
        """
        self._require_init()
        export = self._state.to_dict(include_history=include_history)

        if path:
            Path(path).write_text(json.dumps(export, indent=2, default=str))
            return None
        else:
            return export

    # ===== PRIVATE: Initialization & Helpers =====

    def _require_init(self) -> None:
        """Ensure engine is initialized."""
        if self._state is None:
            raise RuntimeError("Engine not initialized. Call init_scenario() first.")

    def _find_conflict(self, faction_a: str, faction_b: str) -> Optional[ConflictState]:
        """Find conflict between two factions."""
        for conflict in self._state.conflicts.values():
            if (faction_a in conflict.parties and faction_b in conflict.parties):
                return conflict
        return None

    def _get_faction_leader(self, faction_id: str) -> Optional[LeaderState]:
        """Get current leader of faction."""
        faction = self._state.factions.get(faction_id)
        if not faction or not faction.leader_id:
            return None
        return self._state.leaders.get(faction.leader_id)

    def _adjust_trust(
        self,
        faction_a: str,
        faction_b: str,
        delta: float,
        result: TickResult,
    ) -> None:
        """
        Adjust trust between factions (asymmetric logic).

        Trust adjustment is asymmetric:
        - Negative deltas apply at full strength
        - Positive deltas apply at reduced strength (60%)
        - Above 0.7, there's ceiling drag

        Args:
            faction_a: Source faction
            faction_b: Target faction
            delta: Change amount
            result: Result to log changes
        """
        if faction_a not in self._state.factions or faction_b not in self._state.factions:
            return

        faction_state = self._state.factions[faction_a]
        current_trust = faction_state.trust_scores.get(faction_b, 0.5)

        # Asymmetric: positive reduced, negative full
        if delta < 0:
            effective_delta = delta
        else:
            effective_delta = delta * 0.6

        # Ceiling drag above 0.7
        if current_trust > 0.7 and delta > 0:
            effective_delta *= (1.0 - (current_trust - 0.7) * 2)

        new_trust = _clamp(current_trust + effective_delta, 0, 1)
        faction_state.trust_scores[faction_b] = new_trust

        self._append_state_change(
            result,
            f"trust[{faction_a}->{faction_b}] = {new_trust:.3f}"
        )

    def _check_ethics(self, action_type: str, params: Dict[str, Any]) -> bool:
        """
        Check ethics callback if configured.

        Args:
            action_type: Type of action
            params: Action parameters

        Returns:
            True if ethics check passes (or no callback)
        """
        if self._ethics_callback:
            try:
                return self._ethics_callback(action_type, params)
            except Exception as e:
                logger.error(f"Ethics callback error: {e}")
                return False
        return True

    def _escalate_conflict(
        self,
        conflict: ConflictState,
        result: TickResult,
    ) -> None:
        """
        Escalate conflict to next phase.

        Args:
            conflict: Conflict to escalate
            result: Result to log
        """
        old_phase = conflict.phase

        if conflict.phase == ConflictPhase.TENSION:
            conflict.phase = ConflictPhase.ESCALATION
        elif conflict.phase == ConflictPhase.ESCALATION:
            conflict.phase = ConflictPhase.OPEN_CONFLICT
        elif conflict.phase == ConflictPhase.OPEN_CONFLICT:
            # Already at max, increase stalemate
            conflict.stalemate_index = min(1.0, conflict.stalemate_index + 0.1)

        self._append_state_change(
            result,
            f"conflict[{','.join(conflict.parties[:2])}] "
            f"escalated {old_phase.value} -> {conflict.phase.value}"
        )

    def _form_coalition(
        self,
        fid_a: str,
        fid_b: str,
        shared_threat: str,
        avg_trust: float,
        result: TickResult,
    ) -> None:
        """
        Form new coalition between factions.

        Args:
            fid_a: First faction
            fid_b: Second faction
            shared_threat: Threat triggering coalition
            avg_trust: Average trust
            result: Result to log
        """
        coalition = CoalitionState(
            coalition_id=self._make_event_id(),
            members=[fid_a, fid_b],
            coalition_type=CoalitionType.DEFENSIVE_PACT,
            shared_threat=shared_threat,
            founding_trust=avg_trust,
            stability=calc_coalition_stability([avg_trust], self._rng),
            formation_turn=self._tick_counter,
        )
        self._state.coalitions[coalition.coalition_id] = coalition

        self._append_state_change(
            result,
            f"coalition_formed[{fid_a},{fid_b}] against {shared_threat}"
        )

    def _dissolve_coalition(
        self,
        coalition_id: str,
        result: TickResult,
    ) -> None:
        """
        Dissolve a coalition.

        Args:
            coalition_id: Coalition to dissolve
            result: Result to log
        """
        if coalition_id in self._state.coalitions:
            del self._state.coalitions[coalition_id]
            self._append_state_change(result, f"coalition_dissolved[{coalition_id}]")

    def _make_event_id(self) -> str:
        """Generate unique event ID."""
        return f"EVT_{self._tick_counter}_{self._rng.randint(10000, 99999)}"

    def _get_fleets_at_location(
        self,
        location_id: str,
    ) -> Dict[str, List[FleetState]]:
        """
        Get fleets grouped by faction at location.

        Args:
            location_id: Location node ID

        Returns:
            Dict mapping faction_id to list of fleets
        """
        fleets_by_faction = defaultdict(list)
        for fleet in self._state.fleets.values():
            if fleet.location_node == location_id:
                fleets_by_faction[fleet.faction_id].append(fleet)
        return dict(fleets_by_faction)

    def _get_adjacent_factions(self, faction_id: str) -> List[str]:
        """
        Get factions adjacent via topology.

        Args:
            faction_id: Faction to check

        Returns:
            List of adjacent faction IDs
        """
        if not self._topology_manager or not self._state.topology:
            return []

        faction = self._state.factions.get(faction_id)
        if not faction:
            return []

        adjacent = set()
        for node_id in faction.controlled_locations:
            node = self._state.topology.nodes.get(node_id)
            if node:
                for neighbor_id in self._state.topology.adjacency.get(node_id, []):
                    neighbor_node = self._state.topology.nodes.get(neighbor_id)
                    if neighbor_node and neighbor_node.owner_faction and neighbor_node.owner_faction != faction_id:
                        adjacent.add(neighbor_node.owner_faction)

        return list(adjacent)

    # ===== PHASE 1: Event Queue Processing =====

    def _process_event_queue(self, result: TickResult) -> None:
        """
        Process queued events.

        Args:
            result: Result to populate
        """
        while self._state.event_queue:
            event = self._state.event_queue.pop(0)

            # Dispatch to handler
            handler = self._EVENT_HANDLERS.get(event.event_type)
            if handler:
                handler(event, result)
                result.events_processed.append(event)
                logger.debug(f"Processed event: {event.event_type.name}")
            else:
                logger.warning(f"No handler for event type: {event.event_type}")

    # ===== PHASE 2: Leader Bias Evolution =====

    def _update_leader_hooks(self, result: TickResult) -> None:
        """
        Update leader bias and apply hooks.

        Args:
            result: Result to populate
        """
        for faction in self._state.factions.values():
            leader = self._get_faction_leader(faction.faction_id)
            if leader:
                # Evolve bias
                old_bias = leader.dominant_bias
                new_bias = calc_bias_evolution(
                    leader.dominant_bias,
                    faction.economic_strength,
                    faction.population_stability,
                    self._rng,
                )
                leader.dominant_bias = new_bias

                if old_bias != new_bias:
                    self._append_state_change(
                        result,
                        f"leader[{faction.faction_id}] bias shifted {old_bias.value} -> {new_bias.value}"
                    )

                # Apply bias hooks
                apply_bias_hooks(leader, faction, self._rng)

    # ===== PHASE 3: Conflict Evaluation =====

    def _evaluate_conflicts(self, result: TickResult) -> None:
        """
        Evaluate ongoing conflicts.

        Args:
            result: Result to populate
        """
        for conflict in self._state.conflicts.values():
            if conflict.phase == ConflictPhase.OPEN_CONFLICT:
                # Evaluate de-escalation
                leaders = []
                for party_id in conflict.parties:
                    leader = self._get_faction_leader(party_id)
                    if leader:
                        leaders.append(leader)

                if len(leaders) >= 2:
                    deescalation_prob = calc_deescalation_probability(
                        conflict.stalemate_index,
                        conflict.war_cost_estimate,
                        leaders[0].diplomacy_openness,
                        leaders[1].diplomacy_openness,
                    )

                    if self._rng.random() < deescalation_prob:
                        conflict.phase = ConflictPhase.RESOLUTION
                        self._append_state_change(
                            result,
                            f"conflict[{','.join(conflict.parties[:2])}] entering resolution phase"
                        )
            elif conflict.phase == ConflictPhase.RESOLUTION:
                # Transition to deescalation
                conflict.phase = ConflictPhase.DEESCALATION
                self._append_state_change(
                    result,
                    f"conflict[{','.join(conflict.parties[:2])}] deescalating"
                )

    # ===== PHASE 4: Treaty Evaluation =====

    def _evaluate_treaties(self, result: TickResult) -> None:
        """
        Evaluate treaty status.

        Args:
            result: Result to populate
        """
        for treaty in self._state.treaties.values():
            if treaty.is_active:
                # Chance of breach
                leaders = []
                for party_id in treaty.parties:
                    leader = self._get_faction_leader(party_id)
                    if leader:
                        leaders.append((party_id, leader))

                if len(leaders) >= 2:
                    fid_a, leader_a = leaders[0]
                    fid_b, leader_b = leaders[1]

                    breach_score = calc_treaty_breach_score(
                        leader_a.dominant_bias,
                        leader_b.dominant_bias,
                        treaty.terms,
                        self._rng,
                    )

                    if is_treaty_breach(breach_score, self._rng):
                        if fid_a not in treaty.breach_count:
                            treaty.breach_count[fid_a] = 0
                        treaty.breach_count[fid_a] += 1
                        treaty.breach_history.append({"turn": self._tick_counter, "faction": fid_a})

                        self._append_state_change(
                            result,
                            f"treaty[{treaty.treaty_id}] breach by {fid_a} count={treaty.breach_count[fid_a]}"
                        )

                        if sum(treaty.breach_count.values()) >= 3:
                            treaty.phase = TreatyPhase.COLLAPSED
                            treaty.is_active = False
                            self._append_state_change(result, f"treaty[{treaty.treaty_id}] collapsed")

    # ===== PHASE 5: Peacetime Recovery =====

    def _peacetime_recovery(self, result: TickResult) -> None:
        """
        Recover from conflicts during peace.

        Args:
            result: Result to populate
        """
        for faction in self._state.factions.values():
            # Check if in peacetime
            has_open_conflict = any(
                c.phase == ConflictPhase.OPEN_CONFLICT
                for c in self._state.conflicts.values()
                if faction.faction_id in c.parties
            )

            if not has_open_conflict:
                # Recovery: slow increase in economic/population
                faction.economic_strength = min(1.0, faction.economic_strength + 0.01)
                faction.population_stability = min(1.0, faction.population_stability + 0.01)

    # ===== PHASE 6: Diplomacy Tick =====

    def _diplomacy_tick(self, result: TickResult) -> None:
        """
        Handle diplomatic trust decay and updates.

        Args:
            result: Result to populate
        """
        for faction in self._state.factions.values():
            for faction_b_id in list(faction.trust_scores.keys()):
                # Trust decay (slow)
                new_trust = calc_trust_update(
                    faction.trust_scores[faction_b_id],
                    decay_factor=0.01,
                    update=0
                )
                faction.trust_scores[faction_b_id] = new_trust

    # ===== PHASE 7: Coalition Lifecycle =====

    def _coalition_lifecycle(self, result: TickResult) -> None:
        """
        Update coalition stability and survival.

        Args:
            result: Result to populate
        """
        coalitions_to_remove = []
        for coalition_id, coalition in self._state.coalitions.items():
            # Stability decay
            coalition.stability = max(0.0, coalition.stability - 0.02)

            # Chance of dissolution
            if coalition.stability < 0.3 or self._rng.random() < 0.05:
                coalitions_to_remove.append(coalition_id)

        for coalition_id in coalitions_to_remove:
            self._dissolve_coalition(coalition_id, result)

    # ===== PHASE 8: Fleet Movement =====

    def _fleet_movement_tick(self, result: TickResult) -> None:
        """
        Move fleets along hyperlanes.

        Args:
            result: Result to populate
        """
        if not self._topology_manager:
            return

        for fleet in self._state.fleets.values():
            if fleet.movement_target and fleet.movement_target != fleet.location_node:
                # Find path
                path = self._topology_manager.get_path(
                    fleet.location_node,
                    fleet.movement_target,
                )

                if path and len(path) > 1:
                    # Move to next node
                    next_node = path[1]
                    fleet.location_node = next_node

                    # Apply supply decay
                    supply_decay = calc_fleet_supply_decay(
                        fleet.supply_level,
                        fleet.strength,
                        self._rng,
                    )
                    fleet.supply_level = max(0, fleet.supply_level - supply_decay)

                    self._append_state_change(
                        result,
                        f"fleet[{fleet.fleet_id}] moved to {next_node}"
                    )

                    if fleet.location_node == fleet.movement_target:
                        fleet.movement_target = None

    # ===== PHASE 9: Combat Resolution =====

    def _combat_resolution_tick(self, result: TickResult) -> None:
        """
        Resolve naval combats at contested locations.

        Args:
            result: Result to populate
        """
        # Find locations with fleets from multiple factions
        location_fleets = defaultdict(lambda: defaultdict(list))

        for fleet in self._state.fleets.values():
            location_fleets[fleet.location_node][fleet.faction_id].append(fleet)

        # Resolve combats
        for location, fleets_by_faction in location_fleets.items():
            if len(fleets_by_faction) > 1:
                # Combat between factions at this location
                faction_ids = list(fleets_by_faction.keys())
                for i, fid_a in enumerate(faction_ids):
                    for fid_b in faction_ids[i+1:]:
                        # Resolve combat
                        fleets_a = fleets_by_faction[fid_a]
                        fleets_b = fleets_by_faction[fid_b]

                        outcome = self._combat_resolver.resolve_battle(
                            combat=None,
                            attacker_fleets=fleets_a,
                            defender_fleets=fleets_b,
                            topology_manager=self._topology_manager,
                        )

                        # Apply losses
                        self._combat_resolver.apply_fleet_losses(fleets_a, outcome.get("attacker_losses", 0))
                        self._combat_resolver.apply_fleet_losses(fleets_b, outcome.get("defender_losses", 0))

                        self._append_state_change(
                            result,
                            f"combat[{fid_a}-{fid_b}] at {location} winner={outcome.get('winner')}"
                        )

    # ===== PHASE 10: Economic Tick =====

    def _economic_tick(self, result: TickResult) -> None:
        """
        Update economic system.

        Args:
            result: Result to populate
        """
        for faction in self._state.factions.values():
            # Base economic growth
            faction.economic_strength = min(1.0, faction.economic_strength + 0.005)

    # ===== PHASE 11: Media Tick =====

    def _media_tick(self, result: TickResult) -> None:
        """
        Update media narratives and propaganda.

        Args:
            result: Result to populate
        """
        if not self._state.media:
            return

        for narrative in self._state.media.active_narratives:
            faction = self._state.factions.get(narrative.source_faction)
            if not faction:
                continue

            leader = self._get_faction_leader(narrative.source_faction)
            if not leader:
                continue

            # Propaganda effectiveness
            effectiveness = calc_propaganda_effectiveness(
                narrative.message_type,
                leader.public_legitimacy,
                faction.population_stability,
                self._rng,
            )

            # Update effectiveness
            narrative.effectiveness = min(1.0, narrative.effectiveness + effectiveness * 0.05)

            # Legitimacy impact
            legacy_impact = calc_media_legitimacy_impact(
                narrative.effectiveness,
                leader.public_legitimacy,
            )
            leader.public_legitimacy = _clamp(
                leader.public_legitimacy + legacy_impact,
                0, 1
            )

    # ===== PHASE 12: Precursor Tick =====

    def _precursor_tick(self, result: TickResult) -> None:
        """
        Update precursor sites.

        Args:
            result: Result to populate
        """
        for site in self._state.precursor_sites.values():
            if site.discovery_phase == DiscoveryPhase.DETECTED:
                # Check activation risk
                activation_risk = calc_precursor_activation_risk(
                    site.tech_bonus,
                    site.location_node,
                    self._state.factions,
                    self._rng,
                )

                if self._rng.random() < activation_risk:
                    site.discovery_phase = DiscoveryPhase.PARTIALLY_ACTIVATED
                    site.activation_turn = self._tick_counter
                    self._append_state_change(result,
                        f"precursor[{site.site_id}] activated at {site.location_node}"
                    )

            elif site.discovery_phase == DiscoveryPhase.PARTIALLY_ACTIVATED:
                # Generate power
                power = calc_precursor_power_output(
                    site.tech_bonus,
                    site.controller_faction or site.discoverer_faction,
                )
                site.power_level = power

    # ===== PHASE 13: Sentinel Tick =====

    def _sentinel_tick(self, result: TickResult) -> None:
        """
        Update sentinel operatives and missions.

        Args:
            result: Result to populate
        """
        for operative in self._state.operatives.values():
            # Skill advancement
            operative.experience = min(1.0, operative.experience + 0.001)

        # Process missions
        for mission in self._state.missions.values():
            if not mission.is_complete:
                operative = self._state.operatives.get(mission.assigned_operative)
                if operative:
                    # Calculate success
                    success_prob = calc_mission_success_probability(
                        operative.experience,
                        mission.difficulty,
                        operative.rank,
                        self._rng,
                    )

                    if self._rng.random() < success_prob:
                        mission.is_complete = True
                        mission.outcome = "success"
                        operative.missions_completed += 1
                        self._append_state_change(result,
                            f"sentinel[{operative.operative_id}] completed mission {mission.mission_id}"
                        )

    # ===== PHASE 14: Doctrine Tick =====

    def _doctrine_tick(self, result: TickResult) -> None:
        """
        Update doctrine profiles via Q-learning.

        Args:
            result: Result to populate
        """
        for doctrine in self._state.doctrines.values():
            # Q-learning update
            new_q = calc_q_learning_update(
                doctrine.q_table,
                list(doctrine.q_table.keys())[0] if doctrine.q_table else "default",
                self._state.factions[doctrine.faction_id].economic_strength,
                self._state.factions[doctrine.faction_id].military_strength,
                self._rng,
            )
            doctrine.q_table = new_q

    # ===== PHASE 15a: Culture Tick =====

    def _culture_tick(self, result: TickResult) -> None:
        """
        Update cultural movements.

        Args:
            result: Result to populate
        """
        for movement in self._state.culture_movements.values():
            # Spread rate
            spread = calc_culture_spread_rate(
                movement.influence,
                len(movement.spread_factions),
                self._rng,
            )

            movement.influence = min(1.0, movement.influence + spread)

    # ===== PHASE 15b: Emergent Events Generation =====

    def _generate_emergent_events(self, result: TickResult) -> None:
        """
        Generate random events from all subsystems.

        Args:
            result: Result to populate
        """
        # Event generation weights
        destructive_weight = 0.15
        constructive_weight = 0.35
        balanced_weight = 0.50

        rand = self._rng.random()

        if rand < destructive_weight:
            event_type = self._rng.choice([
                EventType.MILITARY_ESCALATION,
                EventType.ECONOMIC_SHOCK,
                EventType.INTELLIGENCE_LEAK,
                EventType.HUMANITARIAN_CRISIS,
                EventType.RESOURCE_CRISIS,
                EventType.BLOCKADE,
                EventType.COUP_ATTEMPT,
            ])
            severity = 0.6 + self._rng.random() * 0.4
        elif rand < destructive_weight + constructive_weight:
            event_type = self._rng.choice([
                EventType.TRADE_AGREEMENT,
                EventType.ECONOMIC_BOOM,
                EventType.TECHNOLOGY_BREAKTHROUGH,
                EventType.CULTURAL_MOVEMENT,
                EventType.INFRASTRUCTURE_INVESTMENT,
                EventType.PRECURSOR_DISCOVERY,
                EventType.FLEET_MOVEMENT,
                EventType.MEDIA_CAMPAIGN,
            ])
            severity = 0.2 + self._rng.random() * 0.4
        else:
            event_type = self._rng.choice([
                EventType.DIPLOMATIC_OVERTURE,
                EventType.TREATY_PROPOSAL,
                EventType.DOCTRINE_SHIFT,
                EventType.ALLIANCE_FORMATION,
            ])
            severity = 0.3 + self._rng.random() * 0.4

        # Pick factions
        faction_ids = list(self._state.factions.keys())
        if len(faction_ids) < 2:
            return

        source_faction = self._rng.choice(faction_ids)
        target_faction = self._rng.choice([f for f in faction_ids if f != source_faction])

        # Create event
        event = SimulationEvent(
            event_id=self._make_event_id(),
            event_type=event_type,
            turn=self._state.turn,
            source_faction=source_faction,
            target_faction=target_faction,
            severity=severity,
            parameters={},
        )

        self._state.event_queue.append(event)
        result.events_generated.append(event)

    # ===== EVENT HANDLERS: v1.0 (17 handlers) =====

    def _handle_military_escalation(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle military escalation event."""
        conflict = self._find_conflict(event.source_faction, event.target_faction)
        if not conflict:
            conflict = ConflictState(
                conflict_id=self._make_event_id(),
                parties=[event.source_faction, event.target_faction],
                phase=ConflictPhase.TENSION,
            )
            self._state.conflicts[conflict.conflict_id] = conflict

        self._escalate_conflict(conflict, result)

        if event.source_faction not in conflict.war_cost_estimate:
            conflict.war_cost_estimate[event.source_faction] = 0.0
        conflict.war_cost_estimate[event.source_faction] += event.severity * 0.1

        self._append_state_change(result, f"military_escalation[{event.source_faction}-{event.target_faction}]")

    def _handle_diplomatic_overture(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle diplomatic overture event."""
        self._adjust_trust(event.source_faction, event.target_faction, event.severity * 0.05, result)

        if event.parameters.get("mediator"):
            conflict = self._find_conflict(event.source_faction, event.target_faction)
            if conflict:
                conflict.mediation_available = True

        self._append_state_change(result, f"diplomatic_overture[{event.source_faction}-{event.target_faction}]")

    def _handle_economic_shock(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle economic shock event."""
        target = self._state.factions.get(event.target_faction)
        if target:
            target.economic_strength = max(0, target.economic_strength - event.severity * 0.1)

            leader = self._get_faction_leader(event.target_faction)
            if leader:
                leader.economic_shock = min(1.0, leader.economic_shock + event.severity * 0.5)

            self._append_state_change(result, f"economic_shock[{event.target_faction}]")

    def _handle_espionage_exposure(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle espionage exposure event."""
        self._adjust_trust(event.source_faction, event.target_faction, -event.severity * 0.15, result)

        target_leader = self._get_faction_leader(event.target_faction)
        if target_leader and target_leader.dominant_bias == BiasType.HYPER_RATIONALISM:
            target_faction = self._state.factions[event.target_faction]
            target_faction.population_stability = max(0, target_faction.population_stability - event.severity * 0.1)

        self._append_state_change(result, f"espionage_exposed[{event.source_faction}->{event.target_faction}]")

    def _handle_treaty_violation(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle treaty violation event."""
        treaty = None
        for t in self._state.treaties.values():
            if event.source_faction in t.parties and event.target_faction in t.parties:
                treaty = t
                break

        if treaty:
            if event.source_faction not in treaty.breach_count:
                treaty.breach_count[event.source_faction] = 0
            treaty.breach_count[event.source_faction] += 1
            treaty.breach_history.append({"turn": self._tick_counter, "faction": event.source_faction})

            treaty.reputation_impact = max(-1.0, treaty.reputation_impact - 0.1)

            if treaty.breach_count[event.source_faction] >= 3:
                treaty.phase = TreatyPhase.COLLAPSED
                treaty.is_active = False
                self._append_state_change(result, f"treaty_collapsed[{treaty.treaty_id}]")
            else:
                self._append_state_change(result, f"treaty_breached[{treaty.treaty_id}]")

    def _handle_mediation_offer(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle mediation offer event."""
        mediator = event.source_faction
        opposing = event.parameters.get("opposing_faction", event.target_faction)
        conflict = self._find_conflict(event.target_faction, opposing)

        if conflict:
            mediator_faction = self._state.factions.get(mediator)
            if mediator_faction:
                trust_a = mediator_faction.trust_scores.get(event.target_faction, 0.5)
                trust_b = mediator_faction.trust_scores.get(opposing, 0.5)

                if trust_a > 0.3 and trust_b > 0.3:
                    conflict.mediation_available = True
                    conflict.mediator_id = mediator
                    self._append_state_change(result, f"mediation_accepted[{mediator}]")
                else:
                    self._append_state_change(result, f"mediation_rejected[{mediator}]")

    def _handle_trade_agreement(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle trade agreement event."""
        faction_a = self._state.factions.get(event.source_faction)
        faction_b = self._state.factions.get(event.target_faction)

        if faction_a and faction_b:
            boost = 0.03 + self._rng.random() * 0.03
            faction_a.economic_strength = min(1.0, faction_a.economic_strength + boost)
            faction_b.economic_strength = min(1.0, faction_b.economic_strength + boost)

            self._adjust_trust(event.source_faction, event.target_faction, 0.03, result)
            self._adjust_trust(event.target_faction, event.source_faction, 0.03, result)

            self._append_state_change(result, f"trade_agreement[{event.source_faction}-{event.target_faction}]")

    def _handle_economic_boom(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle economic boom event."""
        faction = self._state.factions.get(event.source_faction)
        if faction:
            boost = 0.04 + self._rng.random() * 0.03
            faction.economic_strength = min(1.0, faction.economic_strength + boost)

            leader = self._get_faction_leader(event.source_faction)
            if leader:
                leader.public_legitimacy = min(1.0, leader.public_legitimacy + 0.02)

            self._append_state_change(result, f"economic_boom[{event.source_faction}]")

    def _handle_technology_breakthrough(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle technology breakthrough event."""
        faction = self._state.factions.get(event.source_faction)
        if faction:
            boost = 0.03 + self._rng.random() * 0.02
            faction.technology_level = min(1.0, faction.technology_level + boost)

            faction.military_strength = min(1.0, faction.military_strength + 0.01)
            faction.economic_strength = min(1.0, faction.economic_strength + 0.01)

            self._append_state_change(result, f"technology_breakthrough[{event.source_faction}]")

    def _handle_cultural_movement(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle cultural movement event."""
        faction = self._state.factions.get(event.source_faction)
        if faction:
            boost = 0.03 + self._rng.random() * 0.03
            faction.population_stability = min(1.0, faction.population_stability + boost)

            self._append_state_change(result, f"cultural_movement[{event.source_faction}]")

    def _handle_infrastructure_investment(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle infrastructure investment event."""
        faction = self._state.factions.get(event.source_faction)
        if faction:
            boost = 0.03 + self._rng.random() * 0.02
            faction.economic_strength = min(1.0, faction.economic_strength + boost)

            leader = self._get_faction_leader(event.source_faction)
            if leader:
                leader.public_legitimacy = min(1.0, leader.public_legitimacy + 0.01)

            self._append_state_change(result, f"infrastructure_investment[{event.source_faction}]")

    def _handle_internal_coup(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle internal coup event."""
        faction = self._state.factions.get(event.source_faction)
        if not faction:
            return

        faction.population_stability = max(0, faction.population_stability - event.severity * 0.05)

        if event.severity > 0.7:
            # Coup success - cascade to leader change
            coup_event = SimulationEvent(
                event_id=self._make_event_id(),
                event_type=EventType.LEADER_CHANGE,
                turn=self._state.turn,
                source_faction=event.source_faction,
                target_faction=None,
                severity=0.8,
                parameters={"post_coup": True},
            )
            self._state.event_queue.append(coup_event)
            self._append_state_change(result, f"coup_success[{event.source_faction}]")
        else:
            # Coup failure
            leader = self._get_faction_leader(event.source_faction)
            if leader:
                leader.public_legitimacy = max(0, leader.public_legitimacy - 0.1)
            self._append_state_change(result, f"coup_failed[{event.source_faction}]")

    def _handle_leader_change(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle leader change event."""
        faction = self._state.factions.get(event.source_faction)
        if not faction:
            return

        old_leader = self._get_faction_leader(event.source_faction)
        old_leader_bias = old_leader.dominant_bias if old_leader else None

        # Create new leader with different bias
        all_biases = list(BiasType)
        new_bias = self._rng.choice(
            [b for b in all_biases if b != old_leader_bias]
        )

        new_leader = LeaderState(
            leader_id=self._make_event_id(),
            name=f"Leader_{self._tick_counter}",
            role="Leader",
            faction_id=event.source_faction,
            dominant_bias=new_bias,
            public_legitimacy=0.35 if event.parameters.get("post_coup") else 0.5,
        )
        self._state.leaders[new_leader.leader_id] = new_leader
        faction.leader_id = new_leader.leader_id

        # Trust wobble with neighbors
        adjacent = self._get_adjacent_factions(event.source_faction)
        for neighbor_id in adjacent:
            wobble = (self._rng.random() - 0.5) * 0.06
            self._adjust_trust(event.source_faction, neighbor_id, wobble, result)

        self._append_state_change(result,
            f"leader_replaced[{event.source_faction}] {old_leader_bias.value if old_leader_bias else '?'}->{new_bias.value}"
        )

    def _handle_treaty_proposal(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle treaty proposal event."""
        faction_a = self._state.factions.get(event.source_faction)
        faction_b = self._state.factions.get(event.target_faction)

        if not (faction_a and faction_b):
            return

        # Check conditions
        conflict = self._find_conflict(event.source_faction, event.target_faction)
        if conflict and conflict.phase == ConflictPhase.OPEN_CONFLICT:
            self._append_state_change(result,
                f"treaty_rejected[{event.source_faction}-{event.target_faction}] active_conflict"
            )
            return

        avg_trust = (
            faction_a.trust_scores.get(event.target_faction, 0.5) +
            faction_b.trust_scores.get(event.source_faction, 0.5)
        ) / 2

        leader_a = self._get_faction_leader(event.source_faction)
        leader_b = self._get_faction_leader(event.target_faction)
        leader_a_open = leader_a.diplomacy_openness if leader_a else 0.5
        leader_b_open = leader_b.diplomacy_openness if leader_b else 0.5
        avg_openness = (leader_a_open + leader_b_open) / 2

        if avg_trust > 0.4 and avg_openness > 0.3:
            # Accept
            treaty = TreatyState(
                treaty_id=self._make_event_id(),
                parties=[event.source_faction, event.target_faction],
                phase=TreatyPhase.RATIFICATION,
                terms=event.parameters.get("terms", {}),
                is_active=True,
                turns_since_ratification=0,
            )
            self._state.treaties[treaty.treaty_id] = treaty
            self._append_state_change(result, f"treaty_accepted[{event.source_faction}-{event.target_faction}]")
        else:
            self._append_state_change(result, f"treaty_rejected[{event.source_faction}-{event.target_faction}]")

    def _handle_intelligence_leak(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle intelligence leak event."""
        target = self._state.factions.get(event.source_faction)
        leader = self._get_faction_leader(event.source_faction)
        if target and leader:
            leader.institutional_control = max(
                0,
                leader.institutional_control - event.severity * 0.1
            )

        self._adjust_trust(event.source_faction, event.target_faction, -event.severity * 0.05, result)
        self._adjust_trust(event.target_faction, event.source_faction, -event.severity * 0.05, result)

        # Cascade to espionage if severe
        if event.severity > 0.7 and self._rng.random() < 0.3:
            espionage_event = SimulationEvent(
                event_id=self._make_event_id(),
                event_type=EventType.ESPIONAGE_EXPOSURE,
                turn=self._state.turn,
                source_faction=event.target_faction,
                target_faction=event.source_faction,
                severity=event.severity * 0.8,
            )
            self._state.event_queue.append(espionage_event)

        self._append_state_change(result, f"intelligence_leak[{event.source_faction}]")

    def _handle_humanitarian_crisis(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle humanitarian crisis event."""
        faction = self._state.factions.get(event.source_faction)
        if faction:
            faction.population_stability = max(0, faction.population_stability - event.severity * 0.1)
            faction.economic_strength = max(0, faction.economic_strength - event.severity * 0.05)

            leader = self._get_faction_leader(event.source_faction)
            if leader:
                leader.public_legitimacy = max(0, leader.public_legitimacy - event.severity * 0.05)

            # Neighbor responses
            adjacent = self._get_adjacent_factions(event.source_faction)
            for neighbor_id in adjacent:
                neighbor = self._state.factions.get(neighbor_id)
                if neighbor:
                    neighbor_trust = neighbor.trust_scores.get(event.source_faction, 0.5)
                    if neighbor_trust > 0.5:
                        self._adjust_trust(neighbor_id, event.source_faction, 0.02, result)
                    else:
                        self._adjust_trust(neighbor_id, event.source_faction, -0.01, result)

            self._append_state_change(result, f"humanitarian_crisis[{event.source_faction}]")

    def _handle_custom(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle custom event with parameterized changes."""
        params = event.parameters

        # Apply faction deltas
        if "faction_deltas" in params:
            for faction_id, deltas in params["faction_deltas"].items():
                faction = self._state.factions.get(faction_id)
                if faction:
                    for key, delta in deltas.items():
                        if hasattr(faction, key):
                            old_val = getattr(faction, key)
                            new_val = _clamp(old_val + delta, 0, 1)
                            setattr(faction, key, new_val)

        # Apply trust deltas
        if "trust_deltas" in params:
            for (fid_a, fid_b), delta in params["trust_deltas"].items():
                self._adjust_trust(fid_a, fid_b, delta, result)

        # Apply leader deltas
        if "leader_deltas" in params:
            for faction_id, deltas in params["leader_deltas"].items():
                leader = self._get_faction_leader(faction_id)
                if leader:
                    for key, delta in deltas.items():
                        if hasattr(leader, key):
                            old_val = getattr(leader, key)
                            new_val = _clamp(old_val + delta, 0, 1)
                            setattr(leader, key, new_val)

        self._append_state_change(result, f"custom_applied[{event.source_faction}]")

    # ===== EVENT HANDLERS: v2.0 (16 new handlers) =====

    def _handle_fleet_movement(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle fleet movement event."""
        if not self._topology_manager:
            return

        fleet_id = event.parameters.get("fleet_id")
        target_node = event.parameters.get("target_node")

        fleet = self._state.fleets.get(fleet_id)
        if fleet:
            fleet.movement_target = target_node
            self._append_state_change(result, f"fleet_movement[{fleet_id}] -> {target_node}")

    def _handle_fleet_battle(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle fleet battle event."""
        location = event.parameters.get("location")
        if not location:
            return

        fleets_at_location = self._get_fleets_at_location(location)
        if len(fleets_at_location) < 2:
            return

        faction_ids = list(fleets_at_location.keys())
        for i, fid_a in enumerate(faction_ids):
            for fid_b in faction_ids[i+1:]:
                outcome = self._combat_resolver.resolve_combat(
                    fid_a, fleets_at_location[fid_a],
                    fid_b, fleets_at_location[fid_b],
                    location,
                )

                self._append_state_change(result,
                    f"fleet_battle[{fid_a}-{fid_b}] at {location} winner={outcome.get('winner')}"
                )

    def _handle_precursor_discovery(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle precursor discovery event."""
        site_id = event.parameters.get("site_id")
        site = self._state.precursor_sites.get(site_id)

        if site:
            site.discovery_phase = DiscoveryPhase.DETECTED
            site.discoverer_faction = event.source_faction
            self._append_state_change(result, f"precursor_discovered[{site_id}]")

    def _handle_precursor_activation(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle precursor activation event."""
        site_id = event.parameters.get("site_id")
        site = self._state.precursor_sites.get(site_id)

        if site:
            site.discovery_phase = DiscoveryPhase.FULLY_ACTIVATED
            site.activation_turn = self._tick_counter
            self._append_state_change(result, f"precursor_activated[{site_id}]")

    def _handle_sentinel_mission(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle sentinel mission event."""
        operative_id = event.parameters.get("operative_id")
        operative = self._state.operatives.get(operative_id)

        if operative:
            mission_type = event.parameters.get("mission_type", MissionType.RECONNAISSANCE)
            mission = MissionState(
                mission_id=self._make_event_id(),
                mission_type=mission_type,
                assigned_operative=operative_id,
                target_faction=event.target_faction or operative.faction_id,
                target_location=event.parameters.get("target_location"),
                difficulty=event.severity,
            )
            self._state.missions[mission.mission_id] = mission
            self._append_state_change(result,
                f"sentinel_mission[{operative_id}] assigned {mission_type.value}"
            )

    def _handle_corporate_takeover(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle corporate takeover event."""
        faction = self._state.factions.get(event.target_faction)
        if faction:
            faction.economic_strength = max(0, faction.economic_strength - event.severity * 0.1)
            self._append_state_change(result, f"corporate_takeover[{event.target_faction}]")

    def _handle_media_campaign(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle media campaign event."""
        if not self._state.media:
            return

        faction = self._state.factions.get(event.source_faction)
        if faction:
            narrative_type = event.parameters.get("narrative_type", "propaganda")
            narrative = NarrativeState(
                narrative_id=self._make_event_id(),
                source_faction=event.source_faction,
                target_audience=[event.target_faction] if event.target_faction else [],
                message_type=narrative_type,
                effectiveness=0.1,
            )
            self._state.media.active_narratives.append(narrative)
            self._append_state_change(result, f"media_campaign[{event.source_faction}]")

    def _handle_doctrine_shift(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle doctrine shift event."""
        faction_id = event.source_faction
        if faction_id in self._state.doctrines:
            doctrine = self._state.doctrines[faction_id]
            new_doctrine = event.parameters.get("doctrine_type", DoctrineType.CONVENTIONAL)
            doctrine.current_doctrine = new_doctrine
            self._append_state_change(result,
                f"doctrine_shift[{faction_id}] -> {new_doctrine.value}"
            )

    def _handle_culture_spread(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle culture spread event."""
        movement_id = event.parameters.get("movement_id")
        movement = self._state.culture_movements.get(movement_id)

        if movement and event.target_faction:
            if event.target_faction not in movement.spread_factions:
                movement.spread_factions.append(event.target_faction)
                self._append_state_change(result,
                    f"culture_spread[{movement_id}] -> {event.target_faction}"
                )

    def _handle_resource_crisis(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle resource crisis event."""
        faction = self._state.factions.get(event.source_faction)

        if faction:
            faction.economic_strength = max(0, faction.economic_strength - event.severity * 0.1)
            self._append_state_change(result, f"resource_crisis[{event.source_faction}]")

    def _handle_blockade(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle blockade event."""
        target = self._state.factions.get(event.target_faction)
        if target:
            target.economic_strength = max(0, target.economic_strength - event.severity * 0.15)
            self._append_state_change(result, f"blockade[{event.source_faction}->{event.target_faction}]")

    def _handle_coup_attempt(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle coup attempt event."""
        faction = self._state.factions.get(event.source_faction)
        if not faction:
            return

        # Check for military support from fleets
        faction_fleets = [f for f in self._state.fleets.values() if f.faction_id == event.source_faction]
        fleet_support = sum(f.strength for f in faction_fleets) / max(1, sum(
            f.strength for f in self._state.fleets.values()
        ))

        success_threshold = 0.5
        if fleet_support > success_threshold or event.severity > 0.75:
            coup_event = SimulationEvent(
                event_id=self._make_event_id(),
                event_type=EventType.LEADER_CHANGE,
                turn=self._state.turn,
                source_faction=event.source_faction,
                target_faction=None,
                severity=0.85,
                parameters={"post_coup": True, "military_backed": True},
            )
            self._state.event_queue.append(coup_event)
            self._append_state_change(result, f"coup_attempt_success[{event.source_faction}]")
        else:
            faction.population_stability = max(0, faction.population_stability - 0.08)
            self._append_state_change(result, f"coup_attempt_failed[{event.source_faction}]")

    def _handle_alliance_formation(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle alliance formation event."""
        shared_threat = event.parameters.get("shared_threat", "")
        faction_a = self._state.factions.get(event.source_faction)
        faction_b = self._state.factions.get(event.target_faction)

        if faction_a and faction_b:
            avg_trust = (
                faction_a.trust_scores.get(event.target_faction, 0.5) +
                faction_b.trust_scores.get(event.source_faction, 0.5)
            ) / 2

            self._form_coalition(
                event.source_faction,
                event.target_faction,
                shared_threat,
                avg_trust,
                result,
            )

    def _handle_alliance_dissolution(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle alliance dissolution event."""
        coalition_id = event.parameters.get("coalition_id")
        self._dissolve_coalition(coalition_id, result)

    def _handle_sanctions_imposed(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle sanctions imposed event."""
        target = self._state.factions.get(event.target_faction)
        if target:
            target.economic_strength = max(0, target.economic_strength - event.severity * 0.1)
            self._append_state_change(result, f"sanctions_imposed[{event.source_faction}->{event.target_faction}]")

    def _handle_sanctions_lifted(self, event: SimulationEvent, result: TickResult) -> None:
        """Handle sanctions lifted event."""
        target = self._state.factions.get(event.target_faction)
        if target:
            target.economic_strength = min(1.0, target.economic_strength + event.severity * 0.05)
            self._append_state_change(result, f"sanctions_lifted[{event.source_faction}->{event.target_faction}]")


def main():
    """
    Demo: Run 30-turn simulation with canonical scenario.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    engine = GUMASEngine(seed=42)
    state = engine.init_scenario(scenario_id="gumas_canonical_v2")

    print("=" * 80)
    print("GUMAS v2.0 - 30 Turn Simulation")
    print("=" * 80)
    print(f"\nInitial State:")
    print(f"  Factions: {len(state.factions)}")
    print(f"  Conflicts: {len(state.conflicts)}")
    print(f"  Coalitions: {len(state.coalitions)}")
    print(f"  Precursor Sites: {len(state.precursor_sites)}")

    results = engine.run(n_turns=30)

    print(f"\nSimulation Complete: {len(results)} ticks executed")
    print(f"\nFinal State:")
    print(f"  Factions: {len(state.factions)}")
    print(f"  Conflicts: {len(state.conflicts)}")
    print(f"  Coalitions: {len(state.coalitions)}")
    print(f"  Precursor Sites: {len(state.precursor_sites)}")

    # Print summary of last 5 ticks
    print(f"\nLast 5 Ticks Summary:")
    for result in results[-5:]:
        print(f"\nTick {result.turn}:")
        print(f"  Events Processed: {len(result.events_processed)}")
        print(f"  Events Generated: {len(result.events_generated)}")
        print(f"  State Changes: {len(result.state_changes)}")
        if result.state_changes:
            for change in result.state_changes[:3]:
                print(f"    - {change}")
            if len(result.state_changes) > 3:
                print(f"    ... and {len(result.state_changes) - 3} more")

    # Export final state
    export_path = "/tmp/gumas_v2_final_state.json"
    engine.export_state(path=export_path, include_history=False)
    print(f"\nState exported to: {export_path}")


if __name__ == "__main__":
    main()

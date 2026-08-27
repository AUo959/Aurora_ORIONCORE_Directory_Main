#!/usr/bin/env python3
"""
GUMAS L2 Precursor Artifact System v2.0
Anchor: GUMAS-PRECURSORS-V2
Seed: EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP: L2_ENGINE_CORE

Precursor artifact discovery and activation system.
The galaxy contains ancient precursor sites from extinct civilizations.
When discovered and activated, they grant powerful bonuses but carry risk.
"""

import random
import uuid
from typing import Dict, Optional, Set

from modules.gumas.models import (
    GUMASState,
    TickResult,
    PrecursorSite,
    PrecursorOrigin,
    DiscoveryPhase,
    SimulationEvent,
    EventType,
)
from modules.gumas.formulas import (
    calc_precursor_activation_risk,
    calc_precursor_power_output,
)


class PrecursorEngine:
    """
    Manages precursor artifact discovery, activation, and risk.

    Precursor sites evolve through discovery phases:
    DORMANT → DETECTED → INVESTIGATED → PARTIALLY_ACTIVATED → FULLY_ACTIVATED

    From FULLY_ACTIVATED, sites can branch to WEAPONIZED (high risk/reward)
    or CONTAINED (low risk/reward).
    """

    def __init__(self, rng: random.Random) -> None:
        """
        Initialize PrecursorEngine.

        Args:
            rng: Random number generator for stochastic behavior
        """
        self.rng = rng
        self._discovery_progress: Dict[str, int] = {}
        self._activation_progress: Dict[str, int] = {}

    def tick(self, state: GUMASState, result: TickResult) -> None:
        """
        Execute one game tick for precursor artifact system.

        Each turn processes:
        1. Check for discovery events (factions near precursor sites)
        2. Progress activation for sites being investigated
        3. Apply power output bonuses to controlling factions
        4. Check for instability events (cascade failures)
        5. Handle contested sites (multiple factions competing)

        Args:
            state: Current game state
            result: TickResult to accumulate events
        """
        self.check_discoveries(state, result)
        self.progress_activation(state, result)
        self.apply_precursor_bonuses(state, result)
        self.check_instability(state, result)

    def check_discoveries(self, state: GUMASState, result: TickResult) -> None:
        """
        Check for discovery events at DORMANT precursor sites.

        For each DORMANT precursor site: check if any faction controls
        adjacent territory. If so, discovery probability = tech_level * 0.05
        per turn. If discovered, advance to DETECTED phase.

        Args:
            state: Current game state
            result: TickResult to accumulate events
        """
        if not state.precursor_sites or not state.topology:
            return

        for site_id, site in state.precursor_sites.items():
            if site.discovery_phase != DiscoveryPhase.DORMANT:
                continue

            # Find adjacent factions (those controlling adjacent locations)
            adjacent_factions: Set[str] = set()
            if site.location_node in state.topology.adjacency:
                for adj_node_id in state.topology.adjacency[site.location_node]:
                    if adj_node_id in state.topology.nodes:
                        adj_node = state.topology.nodes[adj_node_id]
                        if adj_node.owner_faction:
                            adjacent_factions.add(adj_node.owner_faction)

            # Check discovery for each adjacent faction
            for faction_id in adjacent_factions:
                if faction_id not in state.factions:
                    continue

                faction = state.factions[faction_id]
                discovery_prob = faction.technological_level * 0.05

                if self.rng.random() < discovery_prob:
                    # Discovery successful!
                    site.discovery_phase = DiscoveryPhase.DETECTED
                    site.discoverer_faction = faction_id

                    # Generate event
                    event = SimulationEvent(
                        event_id=str(uuid.uuid4()),
                        event_type=EventType.PRECURSOR_DISCOVERY,
                        turn=state.current_turn,
                        source_faction=faction_id,
                        affected_factions=[faction_id],
                        description=(
                            f"{faction.name} discovered precursor artifact "
                            f"'{site.name}' at {site.location_node}"
                        ),
                        magnitude=0.5,
                    )
                    result.events.append(event)
                    break  # Only one discovery per site per tick

    def progress_activation(self, state: GUMASState, result: TickResult) -> None:
        """
        Progress activation phases for DETECTED/INVESTIGATED sites.

        For DETECTED/INVESTIGATED sites with a controller: advance through
        phases based on controller's tech_level. Each phase takes 3-5 turns.
        Risk increases with each phase.

        Phases:
        - DORMANT → DETECTED (discovered)
        - DETECTED → INVESTIGATED (being studied, 3-5 turns)
        - INVESTIGATED → PARTIALLY_ACTIVATED (activation begins, 3-5 turns)
        - PARTIALLY_ACTIVATED → FULLY_ACTIVATED (fully active, 3-5 turns)
        - FULLY_ACTIVATED → WEAPONIZED or CONTAINED (terminal states)

        Args:
            state: Current game state
            result: TickResult to accumulate events
        """
        for site_id, site in state.precursor_sites.items():
            # Only progress active phases
            if site.discovery_phase not in [
                DiscoveryPhase.DETECTED,
                DiscoveryPhase.INVESTIGATED,
                DiscoveryPhase.PARTIALLY_ACTIVATED,
            ]:
                continue

            if not site.controller_faction:
                continue

            if site.controller_faction not in state.factions:
                continue

            controller = state.factions[site.controller_faction]

            # Initialize progress tracking if needed
            if site_id not in self._activation_progress:
                self._activation_progress[site_id] = 0

            # Increment progress (scaled by controller tech level)
            tech_scale = 0.5 + controller.technological_level * 1.5
            self._activation_progress[site_id] += int(tech_scale)

            # Determine phase duration (3-5 turns, scaled by tech)
            min_turns = max(2, 5 - int(controller.technological_level * 2))
            max_turns = max(3, 8 - int(controller.technological_level * 2))
            phase_duration = self.rng.randint(min_turns, max_turns)

            # Check if phase complete
            if self._activation_progress[site_id] >= phase_duration * 100:
                self._activation_progress[site_id] = 0

                # Advance phase
                if site.discovery_phase == DiscoveryPhase.DETECTED:
                    site.discovery_phase = DiscoveryPhase.INVESTIGATED
                    description = (
                        f"{state.factions[site.controller_faction].name} "
                        f"is investigating '{site.name}'"
                    )
                elif site.discovery_phase == DiscoveryPhase.INVESTIGATED:
                    site.discovery_phase = DiscoveryPhase.PARTIALLY_ACTIVATED
                    site.activation_turn = state.current_turn
                    site.power_level = 0.3
                    description = (
                        f"'{site.name}' is beginning partial activation"
                    )
                elif site.discovery_phase == DiscoveryPhase.PARTIALLY_ACTIVATED:
                    site.discovery_phase = DiscoveryPhase.FULLY_ACTIVATED
                    site.activation_turn = state.current_turn
                    site.power_level = 0.8
                    description = (
                        f"'{site.name}' is now fully activated!"
                    )
                else:
                    return

                # Generate activation event
                event = SimulationEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=EventType.PRECURSOR_ACTIVATION,
                    turn=state.current_turn,
                    source_faction=site.controller_faction,
                    affected_factions=[site.controller_faction],
                    description=description,
                    magnitude=0.7,
                )
                result.events.append(event)

    def apply_precursor_bonuses(self, state: GUMASState, result: TickResult) -> None:
        """
        Apply power output bonuses to controlling factions.

        For PARTIALLY_ACTIVATED and above: use calc_precursor_power_output
        to get bonuses. Apply tech_bonus to faction technological_level,
        military_bonus to military_strength.

        Origin modifiers:
        - ORAK_THUUN: 1.5x (megastructure builders, strong tech)
        - SYTHREX_CONCLAVE: 1.2x (bio-genetic focus, population bonus)
        - VORTHAN_IMPERIUM: 1.3x (cyber-military, strong military bonus)
        - SHROUDBORN: 2.0x but stability < 0.5 (transcendent tech, unstable)
        - UNKNOWN: 1.0x

        Args:
            state: Current game state
            result: TickResult to accumulate events
        """
        for site in state.precursor_sites.values():
            if site.discovery_phase not in [
                DiscoveryPhase.PARTIALLY_ACTIVATED,
                DiscoveryPhase.FULLY_ACTIVATED,
                DiscoveryPhase.WEAPONIZED,
                DiscoveryPhase.CONTAINED,
            ]:
                continue

            if not site.controller_faction:
                continue

            if site.controller_faction not in state.factions:
                continue

            faction = state.factions[site.controller_faction]

            # Determine origin modifier
            origin_modifiers = {
                PrecursorOrigin.ORAK_THUUN: 1.5,
                PrecursorOrigin.SYTHREX_CONCLAVE: 1.2,
                PrecursorOrigin.VORTHAN_IMPERIUM: 1.3,
                PrecursorOrigin.SHROUDBORN: 2.0,
                PrecursorOrigin.UNKNOWN: 1.0,
            }
            origin_modifier = origin_modifiers.get(site.origin, 1.0)

            # Calculate bonuses
            activation_level = {
                DiscoveryPhase.PARTIALLY_ACTIVATED: 0.5,
                DiscoveryPhase.FULLY_ACTIVATED: 1.0,
                DiscoveryPhase.WEAPONIZED: 0.9,
                DiscoveryPhase.CONTAINED: 0.3,
            }.get(site.discovery_phase, 0.0)

            bonuses = calc_precursor_power_output(
                activation_level,
                site.stability,
                origin_modifier,
            )

            # Apply bonuses to faction
            site.tech_bonus = bonuses["tech_bonus"]
            site.military_bonus = bonuses["military_bonus"]

            faction.technological_level = min(
                1.0,
                faction.technological_level + bonuses["tech_bonus"] * 0.01,
            )
            faction.military_strength = min(
                1.0,
                faction.military_strength + bonuses["military_bonus"] * 0.01,
            )

            # Handle SHROUDBORN special case (high reward, but unstable)
            if site.origin == PrecursorOrigin.SHROUDBORN:
                site.stability = min(0.5, site.stability)

    def check_instability(self, state: GUMASState, result: TickResult) -> None:
        """
        Check for catastrophic instability events at active sites.

        For each active site: use calc_precursor_activation_risk. If risk > 0.7,
        chance of catastrophic event.

        Possible outcomes:
        - Containment breach: damages nearby systems
        - Power surge: temporary 2x bonus then shutdown
        - Cascade failure: site destroyed, nearby factions damaged

        Args:
            state: Current game state
            result: TickResult to accumulate events
        """
        for site_id, site in state.precursor_sites.items():
            if site.discovery_phase not in [
                DiscoveryPhase.PARTIALLY_ACTIVATED,
                DiscoveryPhase.FULLY_ACTIVATED,
                DiscoveryPhase.WEAPONIZED,
            ]:
                continue

            if not site.controller_faction:
                continue

            if site.controller_faction not in state.factions:
                continue

            controller = state.factions[site.controller_faction]

            # Calculate instability risk
            risk = calc_precursor_activation_risk(
                site.power_level,
                site.stability,
                controller.technological_level,
            )

            # Check for catastrophic event
            if risk > 0.7 and self.rng.random() < risk * 0.2:
                event_type = self.rng.choice([
                    "containment_breach",
                    "power_surge",
                    "cascade_failure",
                ])

                if event_type == "containment_breach":
                    # Damage controller faction
                    controller.military_strength = max(
                        0.0,
                        controller.military_strength - 0.15,
                    )
                    description = (
                        f"Containment breach at '{site.name}' damages "
                        f"{controller.name}"
                    )
                    magnitude = 0.5

                elif event_type == "power_surge":
                    # Temporary 2x bonus then shutdown
                    old_stability = site.stability
                    site.stability = 0.2
                    site.power_level = min(1.0, site.power_level * 1.5)
                    description = (
                        f"Power surge at '{site.name}' - temporary boost but "
                        f"stability compromised"
                    )
                    magnitude = 0.6

                else:  # cascade_failure
                    # Destroy site, damage controller
                    site.discovery_phase = DiscoveryPhase.DORMANT
                    site.power_level = 0.0
                    site.stability = 0.1
                    site.controller_faction = None
                    controller.military_strength = max(
                        0.0,
                        controller.military_strength - 0.25,
                    )
                    description = (
                        f"Cascade failure at '{site.name}' - site destroyed, "
                        f"{controller.name} severely damaged"
                    )
                    magnitude = 0.9

                event = SimulationEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=EventType.PRECURSOR_ACTIVATION,
                    turn=state.current_turn,
                    source_faction=site.controller_faction,
                    affected_factions=[site.controller_faction],
                    description=description,
                    magnitude=magnitude,
                )
                result.events.append(event)
                site.risk_level = risk


def build_canonical_precursor_sites() -> Dict[str, PrecursorSite]:
    """
    Build the canonical set of precursor sites.

    Returns:
        Dictionary mapping site_id to PrecursorSite objects
    """
    return {
        "hollow_expanse": PrecursorSite(
            site_id="hollow_expanse",
            name="Hollow Expanse Megastructure",
            location_node="HOLLOW-01",
            origin=PrecursorOrigin.ORAK_THUUN,
            discovery_phase=DiscoveryPhase.DORMANT,
            power_level=0.0,
            stability=0.8,
            controller_faction=None,
            discoverer_faction=None,
        ),
        "xyphos_prime": PrecursorSite(
            site_id="xyphos_prime",
            name="Xyphos Prime Bio-Archive",
            location_node="XYPHOS-01",
            origin=PrecursorOrigin.SYTHREX_CONCLAVE,
            discovery_phase=DiscoveryPhase.DORMANT,
            power_level=0.0,
            stability=0.9,
            controller_faction=None,
            discoverer_faction=None,
        ),
        "veil_anomaly": PrecursorSite(
            site_id="veil_anomaly",
            name="Veil Nebula Anomaly",
            location_node="VEIL-01",
            origin=PrecursorOrigin.UNKNOWN,
            discovery_phase=DiscoveryPhase.DORMANT,
            power_level=0.0,
            stability=0.6,
            controller_faction=None,
            discoverer_faction=None,
        ),
        "black_grid_core": PrecursorSite(
            site_id="black_grid_core",
            name="Black Grid Core Network",
            location_node="BLACK-GRID-01",
            origin=PrecursorOrigin.VORTHAN_IMPERIUM,
            discovery_phase=DiscoveryPhase.PARTIALLY_ACTIVATED,
            power_level=0.3,
            stability=0.4,
            controller_faction=None,
            discoverer_faction=None,
        ),
    }


__all__ = [
    "PrecursorEngine",
    "build_canonical_precursor_sites",
]

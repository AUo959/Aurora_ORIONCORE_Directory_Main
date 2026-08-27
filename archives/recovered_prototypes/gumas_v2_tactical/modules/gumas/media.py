#!/usr/bin/env python3
"""
GUMAS L2 Media Ecosystem v2.0
Anchor: GUMAS-MEDIA-V2
Seed: EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP: L2_ENGINE_CORE
"""

import random
from typing import Dict, List, Optional
from .models import (
    GUMASState,
    FactionState,
    MediaEcosystem,
    MediaOutlet,
    NarrativeState,
    EventType,
    SimulationEvent,
    TickResult,
)
from .formulas import (
    calc_propaganda_effectiveness,
    calc_media_legitimacy_impact,
)


class MediaEngine:
    """Media ecosystem simulation for information warfare and propaganda."""

    def __init__(self, rng: random.Random):
        """
        Initialize the media engine.

        Args:
            rng: Random number generator for stochastic events
        """
        self.rng = rng

    def tick(self, state: GUMASState, result: TickResult) -> None:
        """
        Main media tick each turn.

        Sequence:
        1. Update narrative decay (reduce effectiveness of old narratives)
        2. Process active propaganda campaigns
        3. Update public opinion based on events and narratives
        4. Apply legitimacy effects to leaders
        5. Check for media-driven events (information leaks, cultural movements)
        6. Process information freedom changes

        Args:
            state: Current simulation state
            result: TickResult to accumulate events
        """
        if state.media is None:
            return

        # Step 1: Decay narratives
        self.decay_narratives(state)

        # Step 2: Process propaganda campaigns (update public opinion)
        self.update_public_opinion(state, result)

        # Step 3: Apply legitimacy effects
        self.apply_media_legitimacy(state, result)

        # Step 4: Check for information leaks
        self.check_information_leak(state, result)

        # Step 5: Update information freedom
        self._update_information_freedom(state)

        # Step 6: Generate media events
        self._generate_media_events(state, result)

    def launch_narrative(
        self,
        state: GUMASState,
        source_faction: str,
        target_factions: List[str],
        message_type: str,
        content: str,
        severity: float,
        result: TickResult,
    ) -> NarrativeState:
        """
        Create and activate a new narrative/propaganda campaign.

        Uses calc_propaganda_effectiveness to determine initial effectiveness.

        Args:
            state: Current simulation state
            source_faction: Faction launching the narrative
            target_factions: List of target factions
            message_type: Type of message (e.g., "accusation", "inspiration")
            content: Content/description of narrative
            severity: Severity of narrative (0-1)
            result: TickResult to accumulate events

        Returns:
            Created NarrativeState
        """
        if state.media is None:
            return None

        narrative_id = f"narrative_{source_faction}_{state.current_turn}"

        # Calculate effectiveness using media outlets
        source_outlet = state.media.outlets.get(source_faction)
        if source_outlet is None:
            # Use average outlet credibility if no direct outlet
            credibility = 0.5
            reach = 0.5
        else:
            credibility = source_outlet.credibility
            reach = source_outlet.reach

        # Average information freedom of targets as inverse measure
        avg_target_freedom = 0.0
        if target_factions:
            for tf in target_factions:
                avg_target_freedom += state.media.information_freedom.get(tf, 0.5)
            avg_target_freedom /= len(target_factions)
        else:
            avg_target_freedom = 0.5

        # Calculate effectiveness
        effectiveness = calc_propaganda_effectiveness(
            source_credibility=credibility,
            target_info_freedom=avg_target_freedom,
            narrative_alignment=severity,
            media_reach=reach,
        )

        narrative = NarrativeState(
            narrative_id=narrative_id,
            source_faction=source_faction,
            target_audience=target_factions,
            message_type=message_type,
            effectiveness=effectiveness,
            decay_rate=0.05,
            turns_active=0,
        )

        state.media.active_narratives.append(narrative)

        # Generate event
        result.events.append(
            SimulationEvent(
                event_id=f"media_campaign_{narrative_id}",
                event_type=EventType.MEDIA_CAMPAIGN,
                turn=state.current_turn,
                source_faction=source_faction,
                affected_factions=target_factions,
                description=f"Media campaign: {content}",
                magnitude=effectiveness,
            )
        )

        return narrative

    def update_public_opinion(self, state: GUMASState, result: TickResult) -> None:
        """
        Update public opinion between factions based on narratives.

        For each faction pair: drift public opinion toward trust score * 0.3
        + media narrative effects. Public opinion affects legitimacy.

        Args:
            state: Current simulation state
            result: TickResult to accumulate events
        """
        if state.media is None:
            return

        faction_ids = list(state.factions.keys())

        for source_faction_id in faction_ids:
            if source_faction_id not in state.media.public_opinion:
                state.media.public_opinion[source_faction_id] = {}

            source_opinion = state.media.public_opinion[source_faction_id]

            for target_faction_id in faction_ids:
                if source_faction_id == target_faction_id:
                    continue

                # Get current public opinion
                current_opinion = source_opinion.get(target_faction_id, 0.5)

                # Get trust between factions as baseline
                source_faction = state.factions[source_faction_id]
                trust_score = source_faction.known_relations.get(target_faction_id, 0.5)

                # Calculate narrative effect
                narrative_effect = 0.0
                for narrative in state.media.active_narratives:
                    if (
                        narrative.source_faction == source_faction_id
                        and target_faction_id in narrative.target_audience
                    ):
                        # Positive narratives increase opinion
                        narrative_effect += narrative.effectiveness * 0.2

                # Update public opinion with drift
                target_opinion = trust_score * 0.3 + narrative_effect
                new_opinion = current_opinion * 0.7 + target_opinion * 0.3

                source_opinion[target_faction_id] = max(0.0, min(1.0, new_opinion))

    def apply_media_legitimacy(self, state: GUMASState, result: TickResult) -> None:
        """
        Apply media impact on leader legitimacy.

        For each leader: calculate media legitimacy impact based on average
        public opinion of their faction by all other factions.

        Args:
            state: Current simulation state
            result: TickResult to accumulate events
        """
        if state.media is None:
            return

        for leader_id, leader in state.leaders.items():
            faction_id = leader.faction_id
            faction = state.factions.get(faction_id)

            if faction is None:
                continue

            # Calculate average public opinion toward this faction
            avg_public_opinion = 0.0
            opinion_count = 0

            for other_faction_id, opinion_dict in state.media.public_opinion.items():
                if other_faction_id != faction_id:
                    opinion_toward_faction = opinion_dict.get(faction_id, 0.5)
                    avg_public_opinion += opinion_toward_faction
                    opinion_count += 1

            if opinion_count > 0:
                avg_public_opinion /= opinion_count
            else:
                avg_public_opinion = 0.5

            # Get narrative effectiveness (average of all narratives targeting this faction)
            narrative_effectiveness = 0.0
            narrative_count = 0

            for narrative in state.media.active_narratives:
                if faction_id in narrative.target_audience:
                    narrative_effectiveness += narrative.effectiveness
                    narrative_count += 1

            if narrative_count > 0:
                narrative_effectiveness /= narrative_count
            else:
                narrative_effectiveness = 0.0

            # Apply media legitimacy impact
            legitimacy_delta = calc_media_legitimacy_impact(
                public_opinion=avg_public_opinion,
                narrative_effectiveness=narrative_effectiveness,
                current_legitimacy=leader.legitimacy,
            )

            leader.legitimacy = max(0.0, min(1.0, leader.legitimacy + legitimacy_delta))

    def check_information_leak(self, state: GUMASState, result: TickResult) -> None:
        """
        Check for information leaks in low-freedom factions.

        Low information_freedom factions (< 0.3) have chance of leak events
        that damage credibility.

        Args:
            state: Current simulation state
            result: TickResult to accumulate events
        """
        if state.media is None:
            return

        for faction_id, info_freedom in state.media.information_freedom.items():
            if info_freedom < 0.3:
                # Chance of leak proportional to how low freedom is
                leak_chance = (0.3 - info_freedom) * 0.5
                if self.rng.random() < leak_chance:
                    # Damage credibility
                    faction = state.factions.get(faction_id)
                    if faction:
                        faction.legitimacy = max(0.0, faction.legitimacy - 0.05)
                        faction.diplomatic_capital = max(0.0, faction.diplomatic_capital - 0.03)

                    result.events.append(
                        SimulationEvent(
                            event_id=f"information_leak_{faction_id}_{state.current_turn}",
                            event_type=EventType.INTELLIGENCE_LEAK,
                            turn=state.current_turn,
                            source_faction=faction_id,
                            affected_factions=[faction_id],
                            description=f"Information leak from {faction_id}",
                            magnitude=0.3 - info_freedom,
                        )
                    )

    def decay_narratives(self, state: GUMASState) -> None:
        """
        Decay effectiveness of active narratives.

        For each narrative: effectiveness -= decay_rate. Remove if
        effectiveness < 0.05.

        Args:
            state: Current simulation state
        """
        if state.media is None:
            return

        narratives_to_remove = []

        for narrative in state.media.active_narratives:
            narrative.effectiveness -= narrative.decay_rate
            narrative.turns_active += 1

            if narrative.effectiveness < 0.05:
                narratives_to_remove.append(narrative)

        # Remove expired narratives
        for narrative in narratives_to_remove:
            state.media.active_narratives.remove(narrative)

    def _update_information_freedom(self, state: GUMASState) -> None:
        """
        Update information freedom based on faction state.

        Authoritarian factions see reduced freedom; democracies maintain
        higher freedom. Conflicts reduce freedom temporarily.

        Args:
            state: Current simulation state
        """
        if state.media is None:
            return

        for faction_id, faction in state.factions.items():
            current_freedom = state.media.information_freedom.get(faction_id, 0.5)

            # Base drift toward faction's natural freedom level
            faction_type_value = faction.faction_type.value
            if "authoritarian" in faction_type_value or "corporate_oligarchy" in faction_type_value:
                natural_freedom = 0.3
            elif "federation" in faction_type_value or "cultural_spiritual" in faction_type_value:
                natural_freedom = 0.7
            else:
                natural_freedom = 0.5

            # Reduce freedom if in conflict
            conflict_reduction = 0.0
            if faction_id in state.factions[faction_id].active_conflicts:
                conflict_reduction = 0.1

            # Update freedom
            new_freedom = (current_freedom * 0.8 + natural_freedom * 0.2) - conflict_reduction
            state.media.information_freedom[faction_id] = max(0.0, min(1.0, new_freedom))

    def _generate_media_events(self, state: GUMASState, result: TickResult) -> None:
        """
        Generate media-related events.

        Args:
            state: Current simulation state
            result: TickResult to accumulate events
        """
        if state.media is None or not state.factions:
            return

        # Cultural movement event (8% chance)
        if self.rng.random() < 0.08:
            source_faction_id = self.rng.choice(list(state.factions.keys()))
            target_factions = [
                fid for fid in state.factions.keys() if fid != source_faction_id
            ]

            if target_factions:
                self.launch_narrative(
                    state=state,
                    source_faction=source_faction_id,
                    target_factions=target_factions,
                    message_type="cultural_movement",
                    content=f"Cultural movement from {source_faction_id}",
                    severity=self.rng.uniform(0.3, 0.7),
                    result=result,
                )


def build_default_media(factions: Dict[str, FactionState]) -> MediaEcosystem:
    """
    Build initial media ecosystem with outlets and default settings.

    Initialize:
    - Three canonical media outlets (GUN, Zyphari Wire, Dissident Echo)
    - Empty narratives list
    - Neutral public opinion (0.5) for all faction pairs
    - Default information freedom per faction type

    Args:
        factions: Dict of all factions

    Returns:
        Initialized MediaEcosystem
    """
    # Create canonical media outlets
    outlets: Dict[str, MediaOutlet] = {
        "gun": MediaOutlet(
            outlet_id="gun",
            name="GUN (Galactic Union Network)",
            faction_alignment="galactic_union",
            credibility=0.6,
            reach=0.8,
            bias_slant=0.3,
        ),
        "zyphari_wire": MediaOutlet(
            outlet_id="zyphari_wire",
            name="Zyphari Wire",
            faction_alignment="zyphari_compact",
            credibility=0.5,
            reach=0.7,
            bias_slant=0.2,
        ),
        "dissident_echo": MediaOutlet(
            outlet_id="dissident_echo",
            name="Dissident Echo",
            faction_alignment=None,
            credibility=0.4,
            reach=0.4,
            bias_slant=-0.3,
        ),
    }

    # Initialize public opinion (neutral for all pairs)
    public_opinion: Dict[str, Dict[str, float]] = {}
    faction_ids = list(factions.keys())

    for faction_a_id in faction_ids:
        public_opinion[faction_a_id] = {}
        for faction_b_id in faction_ids:
            if faction_a_id != faction_b_id:
                public_opinion[faction_a_id][faction_b_id] = 0.5

    # Initialize information freedom per faction type
    information_freedom: Dict[str, float] = {}

    for faction_id, faction in factions.items():
        faction_type_value = faction.faction_type.value

        if "authoritarian" in faction_type_value or "corporate_oligarchy" in faction_type_value:
            freedom = 0.3
        elif "federation" in faction_type_value or "cultural_spiritual" in faction_type_value:
            freedom = 0.7
        elif "monastic_network" in faction_type_value:
            freedom = 0.6
        else:
            freedom = 0.5

        information_freedom[faction_id] = freedom

    return MediaEcosystem(
        outlets=outlets,
        active_narratives=[],
        public_opinion=public_opinion,
        information_freedom=information_freedom,
    )

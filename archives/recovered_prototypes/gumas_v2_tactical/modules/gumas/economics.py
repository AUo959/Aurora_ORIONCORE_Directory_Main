#!/usr/bin/env python3
"""
GUMAS L2 Economic System v2.0
Anchor: GUMAS-ECONOMICS-V2
Seed: EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP: L2_ENGINE_CORE
"""

import random
from typing import Dict, List, Optional, Tuple
from .models import (
    GUMASState,
    FactionState,
    EconomicState,
    MarketState,
    TradeRoute,
    ResourceType,
    EventType,
    SimulationEvent,
    TickResult,
)
from .formulas import (
    calc_economic_equilibrium,
    calc_trade_flow,
    calc_corporate_capture_pressure,
)


class EconomicEngine:
    """Main economic system for GUMAS simulation."""

    def __init__(self, rng: random.Random):
        """
        Initialize the economic engine.

        Args:
            rng: Random number generator for stochastic events
        """
        self.rng = rng

    def tick(self, state: GUMASState, result: TickResult) -> None:
        """
        Main economic tick that runs each turn.

        Sequence:
        1. Update market prices based on supply/demand
        2. Process trade flows along routes
        3. Apply trade bonuses to faction economic_strength
        4. Process sanctions (reduce trade flow for sanctioned factions)
        5. Calculate GDP index updates per faction
        6. Check corporate capture progression
        7. Apply frontier scarcity effects
        8. Generate economic events

        Args:
            state: Current simulation state
            result: TickResult to accumulate events
        """
        if state.economy is None:
            return

        # Step 1: Update market prices
        self.update_markets(state)

        # Step 2-3: Process trade routes and apply bonuses
        self.process_trade_routes(state, result)

        # Step 4: Apply sanctions
        self._apply_active_sanctions(state, result)

        # Step 5: Calculate GDP updates
        self._update_gdp_indices(state)

        # Step 6: Check corporate capture
        self.check_corporate_capture(state, result)

        # Step 7: Apply frontier scarcity effects
        self.apply_frontier_scarcity(state, result)

        # Step 8: Generate economic events
        self._generate_economic_events(state, result)

    def update_markets(self, state: GUMASState) -> None:
        """
        Update market prices based on supply and demand.

        For each market: recalculate supply/demand based on faction
        production and needs, then compute equilibrium price.

        Args:
            state: Current simulation state
        """
        if state.economy is None:
            return

        for resource_key, market in state.economy.markets.items():
            # Gather supply from factions producing this resource
            total_supply = 0.0
            total_demand = 0.0

            for faction_id, faction in state.factions.items():
                # Simple heuristic: factions contribute based on economic strength
                production = faction.economy_strength * 0.5
                total_supply += production

                # Demand based on population/needs
                # Assume population_stability as a proxy for population size
                demand = faction.public_stability * 0.3
                total_demand += demand

            # Update market state
            market.supply = max(0.01, total_supply)
            market.demand = max(0.01, total_demand)

            # Calculate equilibrium price
            market.price = calc_economic_equilibrium(market.supply, market.demand)

    def process_trade_routes(self, state: GUMASState, result: TickResult) -> None:
        """
        Process trade along routes and apply economic benefits.

        For each trade route:
        - Calculate flow using formulas
        - Apply economic benefits to both endpoint factions
        - Check for blockade events

        Args:
            state: Current simulation state
            result: TickResult to accumulate events
        """
        if state.economy is None:
            return

        for route_id, route in state.economy.trade_routes.items():
            # Get endpoint factions
            if len(route.endpoints) < 2:
                continue

            faction_a_id = route.endpoints[0]
            faction_b_id = route.endpoints[1]

            if faction_a_id not in state.factions or faction_b_id not in state.factions:
                continue

            faction_a = state.factions[faction_a_id]
            faction_b = state.factions[faction_b_id]

            # Calculate flow for primary resource (assume ENERGY for simplicity)
            energy_market = state.economy.markets.get("energy")
            if energy_market is None:
                continue

            flow = calc_trade_flow(
                price_a=energy_market.price,
                price_b=energy_market.price * 0.9,  # Simple price differential
                route_capacity=route.capacity,
                tariff_rate=route.tariff_rate,
                security=route.security,
                is_blockaded=route.is_blockaded,
            )

            # Update trade volume
            energy_market.trade_volume += flow

            # Apply economic benefits: increase economic_strength
            trade_benefit = flow * 0.01
            faction_a.economy_strength = min(1.0, faction_a.economy_strength + trade_benefit)
            faction_b.economy_strength = min(1.0, faction_b.economy_strength + trade_benefit)

            # Check for blockade events
            if route.is_blockaded:
                result.events.append(
                    SimulationEvent(
                        event_id=f"blockade_{route_id}_{state.current_turn}",
                        event_type=EventType.BLOCKADE,
                        turn=state.current_turn,
                        source_faction=None,
                        affected_factions=[faction_a_id, faction_b_id],
                        description=f"Trade route {route_id} is blockaded",
                        magnitude=0.5,
                    )
                )

    def apply_sanctions(
        self,
        state: GUMASState,
        source: str,
        target: str,
        severity: float,
        result: TickResult,
    ) -> None:
        """
        Apply sanctions to a target faction.

        Reduces trade flow to target, damages target economy, and may
        cause blowback to source.

        Args:
            state: Current simulation state
            source: Faction imposing sanctions
            target: Faction targeted by sanctions
            severity: Severity of sanctions (0-1)
            result: TickResult to accumulate events
        """
        if state.economy is None or target not in state.factions:
            return

        target_faction = state.factions[target]

        # Damage target economy
        damage = severity * 0.1
        target_faction.economy_strength = max(0.0, target_faction.economy_strength - damage)

        # Potential blowback to source
        if source in state.factions:
            source_faction = state.factions[source]
            blowback = severity * 0.03
            source_faction.economy_strength = max(0.0, source_faction.economy_strength - blowback)

        # Record sanction
        if target not in state.economy.sanctions_active:
            state.economy.sanctions_active[target] = []
        if source not in state.economy.sanctions_active[target]:
            state.economy.sanctions_active[target].append(source)

        # Generate event
        result.events.append(
            SimulationEvent(
                event_id=f"sanctions_{source}_{target}_{state.current_turn}",
                event_type=EventType.SANCTIONS_IMPOSED,
                turn=state.current_turn,
                source_faction=source,
                affected_factions=[target],
                description=f"{source} imposed sanctions on {target}",
                magnitude=severity,
            )
        )

    def check_corporate_capture(self, state: GUMASState, result: TickResult) -> None:
        """
        Check if corporate influence exceeds capture threshold.

        For each faction: if corporate_influence > threshold, generate
        CORPORATE_TAKEOVER event. Threshold varies by faction type.

        Args:
            state: Current simulation state
            result: TickResult to accumulate events
        """
        if state.economy is None:
            return

        for faction_id, faction in state.factions.items():
            corporate_influence = state.economy.corporate_influence.get(faction_id, 0.0)

            # Threshold based on faction type (authoritarian more vulnerable)
            faction_type_value = faction.faction_type.value
            if "authoritarian" in faction_type_value or "corporate" in faction_type_value:
                threshold = 0.6
            elif "federation" in faction_type_value:
                threshold = 0.8
            else:
                threshold = 0.7

            if corporate_influence > threshold:
                # Generate corporate takeover event
                result.events.append(
                    SimulationEvent(
                        event_id=f"corporate_takeover_{faction_id}_{state.current_turn}",
                        event_type=EventType.CORPORATE_TAKEOVER,
                        turn=state.current_turn,
                        source_faction=None,
                        affected_factions=[faction_id],
                        description=f"Corporate interests capturing {faction_id}",
                        magnitude=corporate_influence - threshold,
                    )
                )

                # Reduce faction autonomy
                faction.legitimacy = max(0.1, faction.legitimacy - 0.1)
                faction.diplomatic_capital = max(0.0, faction.diplomatic_capital - 0.05)

    def calc_faction_gdp(self, faction: FactionState, trade_volume: float) -> float:
        """
        Calculate GDP for a faction.

        Formula:
            GDP = economic_strength * 0.5 + trade_volume * 0.3 + technology_level * 0.2

        Args:
            faction: Faction to calculate GDP for
            trade_volume: Total trade volume of faction

        Returns:
            GDP index value
        """
        gdp = (
            faction.economy_strength * 0.5
            + trade_volume * 0.3
            + faction.technological_level * 0.2
        )
        return max(0.0, gdp)

    def apply_frontier_scarcity(self, state: GUMASState, result: TickResult) -> None:
        """
        Apply penalties to frontier factions with low economic potential.

        Factions with economic_potential < 0.5 suffer:
        - population_stability drain of 0.005/turn
        - economic_strength capped at economic_potential

        Args:
            state: Current simulation state
            result: TickResult to accumulate events
        """
        for faction_id, faction in state.factions.items():
            # Use technological_level as proxy for economic_potential
            economic_potential = faction.technological_level

            if economic_potential < 0.5:
                # Apply stability drain
                faction.public_stability = max(
                    0.0, faction.public_stability - 0.005
                )

                # Cap economic strength
                faction.economy_strength = min(
                    faction.economy_strength, economic_potential
                )

                # Generate resource crisis event if severity is high
                if economic_potential < 0.3 and self.rng.random() < 0.2:
                    result.events.append(
                        SimulationEvent(
                            event_id=f"resource_crisis_{faction_id}_{state.current_turn}",
                            event_type=EventType.RESOURCE_CRISIS,
                            turn=state.current_turn,
                            source_faction=faction_id,
                            affected_factions=[faction_id],
                            description=f"Resource crisis in frontier faction {faction_id}",
                            magnitude=1.0 - economic_potential,
                        )
                    )

    def _apply_active_sanctions(self, state: GUMASState, result: TickResult) -> None:
        """
        Process all active sanctions each turn.

        Args:
            state: Current simulation state
            result: TickResult to accumulate events
        """
        if state.economy is None:
            return

        sanctions_to_remove = []

        for target, sources in list(state.economy.sanctions_active.items()):
            if target not in state.factions:
                sanctions_to_remove.append(target)
                continue

            target_faction = state.factions[target]

            # Apply sanction damage
            for source in sources:
                # Small ongoing damage from sanctions
                target_faction.economy_strength = max(
                    0.0, target_faction.economy_strength - 0.01
                )

            # Randomly lift sanctions (small chance each turn)
            if self.rng.random() < 0.05:
                sanctions_to_remove.append(target)
                result.events.append(
                    SimulationEvent(
                        event_id=f"sanctions_lifted_{target}_{state.current_turn}",
                        event_type=EventType.SANCTIONS_LIFTED,
                        turn=state.current_turn,
                        source_faction=None,
                        affected_factions=[target],
                        description=f"Sanctions against {target} were lifted",
                        magnitude=0.5,
                    )
                )

        # Remove expired sanctions
        for target in sanctions_to_remove:
            if target in state.economy.sanctions_active:
                del state.economy.sanctions_active[target]

    def _update_gdp_indices(self, state: GUMASState) -> None:
        """
        Update GDP index for all factions.

        Args:
            state: Current simulation state
        """
        if state.economy is None:
            return

        for faction_id, faction in state.factions.items():
            # Calculate total trade volume involving this faction
            trade_volume = 0.0
            for market in state.economy.markets.values():
                trade_volume += market.trade_volume

            # Calculate faction GDP
            gdp = self.calc_faction_gdp(faction, trade_volume * 0.1)
            state.economy.gdp_index[faction_id] = gdp

    def _generate_economic_events(self, state: GUMASState, result: TickResult) -> None:
        """
        Generate economic events (boom, shock, trade agreement).

        Args:
            state: Current simulation state
            result: TickResult to accumulate events
        """
        # Economic boom event (5% chance)
        if self.rng.random() < 0.05:
            lucky_faction_id = self.rng.choice(list(state.factions.keys()))
            lucky_faction = state.factions[lucky_faction_id]
            boom_magnitude = self.rng.uniform(0.05, 0.15)

            lucky_faction.economy_strength = min(1.0, lucky_faction.economy_strength + boom_magnitude)

            result.events.append(
                SimulationEvent(
                    event_id=f"economic_boom_{lucky_faction_id}_{state.current_turn}",
                    event_type=EventType.ECONOMIC_BOOM,
                    turn=state.current_turn,
                    source_faction=lucky_faction_id,
                    affected_factions=[lucky_faction_id],
                    description=f"Economic boom in {lucky_faction_id}",
                    magnitude=boom_magnitude,
                )
            )

        # Economic shock event (3% chance)
        if self.rng.random() < 0.03:
            shock_faction_id = self.rng.choice(list(state.factions.keys()))
            shock_faction = state.factions[shock_faction_id]
            shock_magnitude = self.rng.uniform(0.05, 0.15)

            shock_faction.economy_strength = max(0.0, shock_faction.economy_strength - shock_magnitude)

            result.events.append(
                SimulationEvent(
                    event_id=f"economic_shock_{shock_faction_id}_{state.current_turn}",
                    event_type=EventType.ECONOMIC_SHOCK,
                    turn=state.current_turn,
                    source_faction=shock_faction_id,
                    affected_factions=[shock_faction_id],
                    description=f"Economic shock in {shock_faction_id}",
                    magnitude=shock_magnitude,
                )
            )

        # Trade agreement event (7% chance)
        if self.rng.random() < 0.07 and len(state.factions) >= 2:
            faction_ids = list(state.factions.keys())
            faction_a_id = self.rng.choice(faction_ids)
            faction_b_id = self.rng.choice([f for f in faction_ids if f != faction_a_id])

            result.events.append(
                SimulationEvent(
                    event_id=f"trade_agreement_{faction_a_id}_{faction_b_id}_{state.current_turn}",
                    event_type=EventType.TRADE_AGREEMENT,
                    turn=state.current_turn,
                    source_faction=faction_a_id,
                    affected_factions=[faction_a_id, faction_b_id],
                    description=f"Trade agreement between {faction_a_id} and {faction_b_id}",
                    magnitude=0.3,
                )
            )


def build_default_economy(factions: Dict[str, FactionState]) -> EconomicState:
    """
    Build initial economic state with markets and trade routes.

    Creates:
    - Initial markets for all 8 resource types with balanced supply/demand
    - Trade routes connecting neighboring factions in faction ID order

    Args:
        factions: Dict of all factions

    Returns:
        Initialized EconomicState
    """
    # Create markets for all resource types
    markets: Dict[str, MarketState] = {}
    for resource_type in ResourceType:
        markets[resource_type.value] = MarketState(
            resource_type=resource_type,
            supply=1.0,
            demand=1.0,
            price=1.0,
            trade_volume=0.0,
        )

    # Create trade routes between adjacent factions
    trade_routes: Dict[str, TradeRoute] = {}
    faction_ids = sorted(list(factions.keys()))

    for i in range(len(faction_ids) - 1):
        faction_a = faction_ids[i]
        faction_b = faction_ids[i + 1]
        route_id = f"route_{faction_a}_{faction_b}"

        route = TradeRoute(
            route_id=route_id,
            endpoints=[faction_a, faction_b],
            capacity=1.0,
            security=0.8,
            tariff_rate=0.1,
            is_blockaded=False,
        )
        trade_routes[route_id] = route

    # Initialize GDP indices and economic metrics
    gdp_index: Dict[str, float] = {fid: 0.5 for fid in factions.keys()}
    debt_levels: Dict[str, float] = {fid: 0.2 for fid in factions.keys()}
    corporate_influence: Dict[str, float] = {fid: 0.3 for fid in factions.keys()}

    return EconomicState(
        markets=markets,
        trade_routes=trade_routes,
        gdp_index=gdp_index,
        debt_levels=debt_levels,
        corporate_influence=corporate_influence,
        sanctions_active={},
    )

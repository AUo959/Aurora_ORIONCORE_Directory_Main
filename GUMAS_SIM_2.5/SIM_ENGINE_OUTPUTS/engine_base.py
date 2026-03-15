#!/usr/bin/env python3
"""
GUMAS L2 Simulation Engine
============================
Anchor: GUMAS-ENGINE-CORE-V1
Seed: EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP: L2_ENGINE_CORE
Version: 1.0.0

The missing keystone: a turn-based simulation engine that loads
GUMAS entity definitions, initializes galactic state, and runs
multi-agent simulation ticks using the parametric models documented
in PR_L2_GUMAS_ARCHITECTURAL_ENHANCEMENTS and the Runtime Reference
Packet v0.4.

Public API:
    engine = GUMASEngine()
    engine.init_scenario()                       # or init_scenario(state)
    result = engine.step()                       # advance one turn
    state  = engine.get_state()                  # snapshot
    engine.inject_event(event)                   # queue external event
    engine.run(n_turns=10)                       # batch run
    engine.export_state("snapshot.json")         # JSON export

Integration points:
    - Consumes: modules.gumas.models (data structures)
    - Consumes: modules.gumas.formulas (pure simulation math)
    - Consumes: modules.gumas.scenarios (canonical entity loader)
    - Consumed by: src.aurora_orchestrator (as L2 workload)
    - Consumed by: src.bridges.l2_meta_agent_bridge (relay commands)
    - Monitored by: modules.gumas.api.routes (ethics evaluation)

Design Principles:
    - Stdlib only (no numpy/scipy required at runtime)
    - Seed-based reproducibility
    - Full DLP audit trail per tick
    - Every state mutation logged in TickResult
    - Ethics-checkable: every significant action can be routed to
      the existing GUMAS Ethics API for Picard_Delta_3 compliance
"""

from __future__ import annotations

import json
import logging
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from formulas import (
    apply_bias_hooks,
    calc_bias_evolution,
    calc_deescalation_probability,
    calc_double_agent_risk,
    calc_reputation_after_decay,
    calc_treaty_breach_score,
    calc_trust_update,
    is_treaty_breach,
)
from models import (
    BiasType,
    ConflictPhase,
    ConflictState,
    EventType,
    FactionState,
    GUMASState,
    LeaderState,
    SimulationEvent,
    TickResult,
    TreatyPhase,
    TreatyState,
)
from scenarios import build_default_scenario

logger = logging.getLogger(__name__)


# ============================================================================
# ENGINE
# ============================================================================

class GUMASEngine:
    """
    L2 GUMAS multi-agent galactic simulation engine.

    Manages a GUMASState and advances it turn-by-turn through
    conflict resolution, diplomacy, bias evolution, treaty
    enforcement, and espionage mechanics.

    Usage:
        engine = GUMASEngine(seed=42)
        engine.init_scenario()
        for _ in range(20):
            result = engine.step()
            print(f"Turn {result.turn}: {len(result.events_generated)} events")
        engine.export_state("output.json")
    """

    def __init__(
        self,
        seed: int = 42,
        ethics_callback: Optional[Callable[[str, Dict[str, Any]], bool]] = None,
    ):
        """
        Args:
            seed: RNG seed for reproducibility.
            ethics_callback: Optional callable(action_type, params) -> bool.
                If provided, called before significant state mutations.
                Return False to block the action (Picard_Delta_3 veto).
                If None, all actions proceed (ethics checked externally).
        """
        self._seed = seed
        self._rng = random.Random(seed)
        self._state: Optional[GUMASState] = None
        self._ethics_callback = ethics_callback
        self._initialized = False

        logger.info(
            "GUMASEngine created (seed=%d, ethics_callback=%s)",
            seed,
            "attached" if ethics_callback else "none",
        )

    # ------------------------------------------------------------------ #
    # PUBLIC API                                                          #
    # ------------------------------------------------------------------ #

    def init_scenario(
        self,
        state: Optional[GUMASState] = None,
        scenario_id: str = "gumas_canonical_v1",
    ) -> GUMASState:
        """
        Initialize the simulation with a scenario.

        Args:
            state: Pre-built GUMASState. If None, loads the canonical
                   default scenario from scenarios.py.
            scenario_id: Scenario identifier (used if state is None).

        Returns:
            The initialized GUMASState.
        """
        if state is not None:
            self._state = state
        else:
            self._state = build_default_scenario(
                scenario_id=scenario_id,
                seed=self._seed,
            )

        self._rng = random.Random(self._state.seed)
        self._initialized = True

        logger.info(
            "Scenario initialized: %s (factions=%d, leaders=%d, conflicts=%d, seed=%d)",
            self._state.scenario_id,
            len(self._state.factions),
            len(self._state.leaders),
            len(self._state.conflicts),
            self._state.seed,
        )

        return self._state

    def step(self) -> TickResult:
        """
        Advance the simulation by one turn.

        Tick lifecycle:
            1. Process injected events from queue
            2. Update leader bias hooks
            3. Evaluate conflicts (de-escalation, phase transitions)
            4. Evaluate treaties (breach detection, reputation decay)
            5. Run diplomacy tick (trust updates, espionage checks)
            6. Generate emergent events
            7. Record TickResult and append to history

        Returns:
            TickResult with full audit of what happened this turn.
        """
        self._require_init()
        assert self._state is not None  # for type checker

        self._state.turn += 1
        turn = self._state.turn

        result = TickResult(turn=turn)

        # Phase 1: Process injected events
        self._process_event_queue(result)

        # Phase 2: Update leader bias hooks
        self._update_leader_hooks(result)

        # Phase 3: Conflict evaluation
        self._evaluate_conflicts(result)

        # Phase 4: Treaty evaluation
        self._evaluate_treaties(result)

        # Phase 4.5: Peacetime recovery (the missing half)
        self._peacetime_recovery(result)

        # Phase 5: Diplomacy tick
        self._diplomacy_tick(result)

        # Phase 6: Emergent events
        self._generate_emergent_events(result)

        # Record
        self._state.history.append(result)

        logger.info(
            "Turn %d complete: %d events processed, %d generated, %d state changes",
            turn,
            len(result.events_processed),
            len(result.events_generated),
            len(result.state_changes),
        )

        return result

    def run(self, n_turns: int = 10) -> List[TickResult]:
        """Run n_turns of simulation. Returns list of TickResults."""
        self._require_init()
        results = []
        for _ in range(n_turns):
            results.append(self.step())
        return results

    def get_state(self) -> GUMASState:
        """Return the current simulation state."""
        self._require_init()
        assert self._state is not None
        return self._state

    def inject_event(self, event: SimulationEvent) -> None:
        """
        Queue an external event for processing on the next tick.

        Args:
            event: SimulationEvent to inject. event.injected will be
                   set to True automatically.
        """
        self._require_init()
        assert self._state is not None
        event.injected = True
        event.turn = self._state.turn + 1
        self._state.event_queue.append(event)

        logger.info(
            "Event injected: %s (type=%s, source=%s, target=%s)",
            event.event_id,
            event.event_type.value,
            event.source_faction,
            event.target_faction,
        )

    def export_state(self, path: str, include_history: bool = True) -> None:
        """Export current state to JSON file."""
        self._require_init()
        assert self._state is not None
        data = self._state.to_dict(include_history=include_history)
        data["dlp"] = {
            "anchor": "GUMAS-ENGINE-CORE-V1",
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "seed": self._state.seed,
            "turns_completed": self._state.turn,
        }
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w") as f:
            json.dump(data, f, indent=2, default=str)
        logger.info("State exported to %s", path)

    # ------------------------------------------------------------------ #
    # PHASE 1: EVENT QUEUE                                                #
    # ------------------------------------------------------------------ #

    def _process_event_queue(self, result: TickResult) -> None:
        """Drain and process all queued events."""
        assert self._state is not None
        queue = self._state.event_queue
        self._state.event_queue = []

        for event in queue:
            self._apply_event(event, result)
            result.events_processed.append(event)

    def _apply_event(self, event: SimulationEvent, result: TickResult) -> None:
        """Apply a single event's effects to the world state."""
        assert self._state is not None
        handler = self._EVENT_HANDLERS.get(event.event_type)
        if handler:
            handler(self, event, result)
        else:
            logger.warning("No handler for event type: %s", event.event_type.value)

    def _handle_military_escalation(
        self, event: SimulationEvent, result: TickResult,
    ) -> None:
        assert self._state is not None
        src = event.source_faction
        tgt = event.target_faction
        if not src or not tgt:
            return

        severity = event.severity

        # Find or create conflict
        conflict = self._find_conflict(src, tgt)
        if conflict is None:
            cid = f"conflict_{src}_{tgt}_{self._state.turn}"
            conflict = ConflictState(
                conflict_id=cid,
                parties=[src, tgt],
                phase=ConflictPhase.ESCALATION,
            )
            self._state.conflicts[cid] = conflict
            result.state_changes.append({
                "type": "conflict_created",
                "conflict_id": cid,
                "parties": [src, tgt],
            })

        # Escalate phase
        phase_order = [
            ConflictPhase.PEACE, ConflictPhase.TENSION,
            ConflictPhase.ESCALATION, ConflictPhase.OPEN_CONFLICT,
        ]
        idx = phase_order.index(conflict.phase) if conflict.phase in phase_order else 2
        new_idx = min(idx + 1, len(phase_order) - 1)
        old_phase = conflict.phase
        conflict.phase = phase_order[new_idx]

        # Increase war costs
        conflict.war_cost_estimate[src] = min(
            1.0, conflict.war_cost_estimate.get(src, 0.3) + severity * 0.2
        )
        conflict.war_cost_estimate[tgt] = min(
            1.0, conflict.war_cost_estimate.get(tgt, 0.3) + severity * 0.3
        )

        # Trust hit
        self._adjust_trust(src, tgt, -severity * 0.15, result)

        result.state_changes.append({
            "type": "conflict_escalation",
            "conflict_id": conflict.conflict_id,
            "old_phase": old_phase.value,
            "new_phase": conflict.phase.value,
            "severity": severity,
        })

    def _handle_diplomatic_overture(
        self, event: SimulationEvent, result: TickResult,
    ) -> None:
        assert self._state is not None
        src = event.source_faction
        tgt = event.target_faction
        if not src or not tgt:
            return

        # Trust boost
        bonus = event.parameters.get("trust_bonus", 0.1)
        self._adjust_trust(src, tgt, bonus, result)

        # Check if this enables mediation on active conflicts
        for conflict in self._state.conflicts.values():
            if src in conflict.parties and tgt in conflict.parties:
                if not conflict.mediation_available:
                    mediator = event.parameters.get("mediator_id")
                    if mediator and mediator in self._state.factions:
                        conflict.mediation_available = True
                        conflict.mediator_id = mediator
                        result.state_changes.append({
                            "type": "mediation_enabled",
                            "conflict_id": conflict.conflict_id,
                            "mediator": mediator,
                        })

    def _handle_economic_shock(
        self, event: SimulationEvent, result: TickResult,
    ) -> None:
        assert self._state is not None
        tgt = event.target_faction
        if not tgt or tgt not in self._state.factions:
            return

        faction = self._state.factions[tgt]
        shock = event.severity * 0.3
        faction.economic_strength = max(0.05, faction.economic_strength - shock)
        faction.population_stability = max(0.05, faction.population_stability - shock * 0.5)

        # Stress the leader
        leader = self._get_faction_leader(tgt)
        if leader:
            leader.economic_shock += event.severity
            leader.war_pressure = min(1.0, leader.war_pressure + shock * 0.3)

        result.state_changes.append({
            "type": "economic_shock",
            "faction": tgt,
            "severity": event.severity,
            "new_economic_strength": faction.economic_strength,
        })

    def _handle_espionage_exposure(
        self, event: SimulationEvent, result: TickResult,
    ) -> None:
        assert self._state is not None
        src = event.source_faction  # the spy's origin
        tgt = event.target_faction  # the exposed target
        if not src or not tgt:
            return

        # Major trust hit
        self._adjust_trust(tgt, src, -0.25, result)

        # Leader stress
        leader = self._get_faction_leader(tgt)
        if leader:
            leader.betrayals += 1
            # Hyper-rationalism paranoia branch check (PR Section 5.2)
            if leader.dominant_bias == BiasType.HYPER_RATIONALISM:
                paranoia_threshold = event.parameters.get("paranoia_threshold", 0.4)
                institutional_trust = leader.institutional_control
                if institutional_trust < paranoia_threshold:
                    result.state_changes.append({
                        "type": "paranoia_purge_triggered",
                        "leader": leader.leader_id,
                        "institutional_trust": institutional_trust,
                    })
                    leader.oversight_resistance = min(1.0, leader.oversight_resistance + 0.2)

        result.state_changes.append({
            "type": "espionage_exposed",
            "spy_origin": src,
            "target": tgt,
            "severity": event.severity,
        })

    def _handle_treaty_violation(
        self, event: SimulationEvent, result: TickResult,
    ) -> None:
        assert self._state is not None
        violator = event.source_faction
        treaty_id = event.parameters.get("treaty_id")
        if not violator or not treaty_id:
            return

        treaty = self._state.treaties.get(treaty_id)
        if not treaty or not treaty.is_active:
            return

        # Run breach detection formula
        action_severity = event.severity
        is_direct = event.parameters.get("is_direct_action", True)
        trust = 0.5
        for other in treaty.parties:
            if other != violator and other in self._state.factions:
                trust = self._state.factions[other].trust_scores.get(violator, 0.5)
                break

        breach_score = calc_treaty_breach_score(
            action_severity=action_severity,
            is_direct_action=is_direct,
            treaty_ambiguity=treaty.ambiguity_tolerance,
            faction_trust=trust,
        )

        if is_treaty_breach(breach_score, treaty.violation_threshold):
            treaty.breach_count[violator] = treaty.breach_count.get(violator, 0) + 1
            treaty.breach_history.append({
                "turn": self._state.turn,
                "violator": violator,
                "breach_score": round(breach_score, 4),
                "severity": action_severity,
            })

            # Reputation hit
            faction = self._state.factions.get(violator)
            if faction:
                faction.reputation = calc_reputation_after_decay(
                    base_reputation=faction.reputation,
                    breach_penalty=-0.1,
                    breach_count=treaty.breach_count[violator],
                    turns_since_last_breach=0,
                )

            # Check treaty collapse threshold
            total_breaches = sum(treaty.breach_count.values())
            if total_breaches >= 3:
                treaty.phase = TreatyPhase.COLLAPSED
                treaty.is_active = False
                result.state_changes.append({
                    "type": "treaty_collapsed",
                    "treaty_id": treaty_id,
                    "total_breaches": total_breaches,
                })

            result.state_changes.append({
                "type": "treaty_breach_confirmed",
                "treaty_id": treaty_id,
                "violator": violator,
                "breach_score": round(breach_score, 4),
                "cumulative_breaches": treaty.breach_count[violator],
            })

    def _handle_mediation_offer(
        self, event: SimulationEvent, result: TickResult,
    ) -> None:
        assert self._state is not None
        mediator = event.source_faction
        conflict_id = event.parameters.get("conflict_id")
        if not mediator or not conflict_id:
            return

        conflict = self._state.conflicts.get(conflict_id)
        if not conflict:
            return

        # Check mediator neutrality (PR: neutrality_requirement 0.7)
        neutrality_ok = True
        for party in conflict.parties:
            trust = self._state.factions.get(party).trust_scores.get(mediator, 0.5) if self._state.factions.get(party) else 0.5
            if trust < 0.3:
                neutrality_ok = False
                break

        if neutrality_ok:
            conflict.mediation_available = True
            conflict.mediator_id = mediator
            result.state_changes.append({
                "type": "mediation_accepted",
                "conflict_id": conflict_id,
                "mediator": mediator,
            })
        else:
            result.state_changes.append({
                "type": "mediation_rejected",
                "conflict_id": conflict_id,
                "mediator": mediator,
                "reason": "neutrality_insufficient",
            })

    # ------------------------------------------------------------------ #
    # CONSTRUCTIVE EVENT HANDLERS                                          #
    # ------------------------------------------------------------------ #

    def _handle_trade_agreement(
        self, event: SimulationEvent, result: TickResult,
    ) -> None:
        """
        Bilateral trade deal. Both parties gain economically.
        Trust improves. This is how economies grow between wars.

        Magnitude: +0.03-0.06 economic per party (modest).
        Compare to ECONOMIC_SHOCK: -0.10-0.25 (harsh).
        Trade builds slowly. Shocks hit fast. That's the asymmetry.
        """
        assert self._state is not None
        source = self._state.factions.get(event.source_faction or "")
        target = self._state.factions.get(event.target_faction or "")
        if not source or not target:
            return

        trade_value = event.parameters.get("trade_value", 0.04)

        for faction in (source, target):
            ceiling = faction.economic_potential
            if faction.economic_strength < ceiling:
                gain = min(trade_value, ceiling - faction.economic_strength)
                faction.economic_strength = min(
                    ceiling, faction.economic_strength + gain
                )

        # Trade builds trust
        self._adjust_trust(
            event.source_faction or "",
            event.target_faction or "",
            0.02,
            result,
        )

        result.state_changes.append({
            "type": "trade_agreement_executed",
            "source": event.source_faction,
            "target": event.target_faction,
            "trade_value": round(trade_value, 4),
        })

    def _handle_economic_boom(
        self, event: SimulationEvent, result: TickResult,
    ) -> None:
        """
        Domestic economic expansion. Requires peace and stability.

        Magnitude: +0.04-0.07 economic, +0.02 population stability.
        Capped at economic_potential.
        """
        assert self._state is not None
        faction = self._state.factions.get(event.target_faction or "")
        if not faction:
            return

        boom = event.severity * 0.10  # severity 0.3-0.7 → 0.03-0.07
        ceiling = faction.economic_potential
        if faction.economic_strength < ceiling:
            gain = min(boom, ceiling - faction.economic_strength)
            faction.economic_strength += gain

        faction.population_stability = min(
            1.0, faction.population_stability + 0.02
        )

        # Boom boosts leader legitimacy
        leader = self._get_faction_leader(event.target_faction or "")
        if leader:
            leader.public_legitimacy = min(
                1.0, leader.public_legitimacy + 0.02
            )

        result.state_changes.append({
            "type": "economic_boom_realized",
            "faction": event.target_faction,
            "gain": round(boom, 4),
            "new_econ": round(faction.economic_strength, 4),
        })

    def _handle_technology_breakthrough(
        self, event: SimulationEvent, result: TickResult,
    ) -> None:
        """
        Tech breakthrough. Boosts technology, small military and economic
        spillover. This is how factions differentiate over time.

        Magnitude: +0.03-0.05 tech, +0.01 military, +0.01 economic.
        """
        assert self._state is not None
        faction = self._state.factions.get(event.target_faction or "")
        if not faction:
            return

        tech_gain = 0.03 + event.severity * 0.04
        faction.technology_level = min(1.0, faction.technology_level + tech_gain)
        faction.military_strength = min(1.0, faction.military_strength + 0.01)
        ceiling = faction.economic_potential
        faction.economic_strength = min(ceiling, faction.economic_strength + 0.01)

        result.state_changes.append({
            "type": "technology_breakthrough_realized",
            "faction": event.target_faction,
            "tech_gain": round(tech_gain, 4),
            "new_tech": round(faction.technology_level, 4),
        })

    def _handle_cultural_movement(
        self, event: SimulationEvent, result: TickResult,
    ) -> None:
        """
        Cultural movement stabilizes population and builds soft power.

        Magnitude: +0.03-0.06 population stability, +0.01 trust with
        one neighbor. Culture is glue.
        """
        assert self._state is not None
        faction = self._state.factions.get(event.target_faction or "")
        if not faction:
            return

        stabilization = 0.03 + event.severity * 0.05
        faction.population_stability = min(
            1.0, faction.population_stability + stabilization
        )

        # Cultural soft power: small trust gain with a random neighbor
        partner = event.parameters.get("cultural_partner")
        if partner:
            self._adjust_trust(
                event.target_faction or "", partner,
                0.01, result,
            )

        leader = self._get_faction_leader(event.target_faction or "")
        if leader:
            leader.public_legitimacy = min(
                1.0, leader.public_legitimacy + 0.01
            )

        result.state_changes.append({
            "type": "cultural_movement_effect",
            "faction": event.target_faction,
            "stabilization": round(stabilization, 4),
        })

    def _handle_infrastructure_investment(
        self, event: SimulationEvent, result: TickResult,
    ) -> None:
        """
        Post-war reconstruction or peacetime infrastructure program.
        This is the discrete replacement for background recovery.

        Magnitude: +0.03-0.05 economic, +0.02 population stability,
        +0.01 leader legitimacy. Capped at economic_potential.
        """
        assert self._state is not None
        faction = self._state.factions.get(event.target_faction or "")
        if not faction:
            return

        investment = 0.03 + event.severity * 0.04
        ceiling = faction.economic_potential
        if faction.economic_strength < ceiling:
            gain = min(investment, ceiling - faction.economic_strength)
            faction.economic_strength += gain

        faction.population_stability = min(
            1.0, faction.population_stability + 0.02
        )

        leader = self._get_faction_leader(event.target_faction or "")
        if leader:
            leader.public_legitimacy = min(
                1.0, leader.public_legitimacy + 0.01
            )
            leader.elite_support = min(
                1.0, leader.elite_support + 0.01
            )

        result.state_changes.append({
            "type": "infrastructure_investment_executed",
            "faction": event.target_faction,
            "investment": round(investment, 4),
            "new_econ": round(faction.economic_strength, 4),
        })

    _EVENT_HANDLERS: Dict[EventType, Callable[..., None]] = {
        EventType.MILITARY_ESCALATION: _handle_military_escalation,
        EventType.DIPLOMATIC_OVERTURE: _handle_diplomatic_overture,
        EventType.ECONOMIC_SHOCK: _handle_economic_shock,
        EventType.ESPIONAGE_EXPOSURE: _handle_espionage_exposure,
        EventType.TREATY_VIOLATION: _handle_treaty_violation,
        EventType.MEDIATION_OFFER: _handle_mediation_offer,
        EventType.TRADE_AGREEMENT: _handle_trade_agreement,
        EventType.ECONOMIC_BOOM: _handle_economic_boom,
        EventType.TECHNOLOGY_BREAKTHROUGH: _handle_technology_breakthrough,
        EventType.CULTURAL_MOVEMENT: _handle_cultural_movement,
        EventType.INFRASTRUCTURE_INVESTMENT: _handle_infrastructure_investment,
    }

    # ------------------------------------------------------------------ #
    # PHASE 2: LEADER BIAS HOOKS                                          #
    # ------------------------------------------------------------------ #

    def _update_leader_hooks(self, result: TickResult) -> None:
        """
        Phase 2: Evolve leader bias intensity based on accumulated
        stressors, then recalculate bias effect hooks.

        Bias evolution fires when total stressor load exceeds a
        threshold, simulating how pressure changes leaders over time.
        This was the missing link — without it, leaders were static.
        """
        assert self._state is not None

        for leader in self._state.leaders.values():
            # Calculate total stressor load as event_severity proxy
            stressor_load = (
                leader.war_losses * 0.1
                + leader.betrayals * 0.15
                + leader.scandals * 0.1
                + leader.economic_shock * 0.2
                + leader.war_pressure * 0.3
            )
            stressor_load = min(1.0, stressor_load)

            # Evolve bias intensity if stressor load is meaningful
            if stressor_load > 0.05:
                old_intensity = leader.bias_intensity
                leader.bias_intensity = calc_bias_evolution(
                    current_intensity=leader.bias_intensity,
                    plasticity=leader.plasticity,
                    event_severity=stressor_load,
                    has_survivorship_bias=(
                        leader.dominant_bias == BiasType.SURVIVORSHIP
                    ),
                    doctrine_shift_bonus=0.05 if leader.war_losses > 2 else 0.0,
                )

                if abs(leader.bias_intensity - old_intensity) > 0.01:
                    result.state_changes.append({
                        "type": "bias_evolved",
                        "leader": leader.leader_id,
                        "old_intensity": round(old_intensity, 4),
                        "new_intensity": round(leader.bias_intensity, 4),
                        "stressor_load": round(stressor_load, 4),
                    })

                # Stressor decay: pressure bleeds off slowly each turn
                leader.economic_shock = max(0.0, leader.economic_shock - 0.02)
                leader.war_pressure = max(0.0, leader.war_pressure - 0.01)

            # Recalculate hooks from (potentially evolved) intensity
            hooks = apply_bias_hooks(
                leader.dominant_bias.value,
                leader.bias_intensity,
            )
            leader.evidence_gain_multiplier = hooks["evidence_gain_multiplier"]
            leader.risk_tolerance = hooks["risk_tolerance"]
            leader.diplomacy_openness = hooks["diplomacy_openness"]
            leader.escalation_threshold = hooks["escalation_threshold"]
            leader.oversight_resistance = hooks["oversight_resistance"]

    # ------------------------------------------------------------------ #
    # PHASE 3: CONFLICT EVALUATION                                        #
    # ------------------------------------------------------------------ #

    def _evaluate_conflicts(self, result: TickResult) -> None:
        """Evaluate all active conflicts for phase transitions."""
        assert self._state is not None

        for conflict in list(self._state.conflicts.values()):
            if conflict.phase in (ConflictPhase.PEACE, ConflictPhase.RESOLUTION):
                continue

            conflict.turns_active += 1

            # Calculate de-escalation probability
            parties = conflict.parties
            if len(parties) < 2:
                continue

            a, b = parties[0], parties[1]
            p_deesc = calc_deescalation_probability(
                war_cost_a=conflict.war_cost_estimate.get(a, 0.3),
                war_cost_b=conflict.war_cost_estimate.get(b, 0.3),
                stalemate_index=conflict.stalemate_index,
                internal_pressure_a=conflict.internal_pressure.get(a, 0.2),
                internal_pressure_b=conflict.internal_pressure.get(b, 0.2),
                mediation_available=conflict.mediation_available,
            )
            conflict.deescalation_probability = p_deesc

            # Leader diplomacy_openness modifies the effective roll
            leader_a = self._get_faction_leader(a)
            leader_b = self._get_faction_leader(b)
            openness_bonus = 0.0
            if leader_a:
                openness_bonus += (leader_a.diplomacy_openness - 0.5) * 0.1
            if leader_b:
                openness_bonus += (leader_b.diplomacy_openness - 0.5) * 0.1

            effective_p = min(1.0, max(0.0, p_deesc + openness_bonus))

            # Stochastic resolution
            roll = self._rng.random()
            if roll < effective_p:
                old_phase = conflict.phase
                # De-escalation step
                deesc_transitions = {
                    ConflictPhase.OPEN_CONFLICT: ConflictPhase.STALEMATE,
                    ConflictPhase.STALEMATE: ConflictPhase.DEESCALATION,
                    ConflictPhase.ESCALATION: ConflictPhase.TENSION,
                    ConflictPhase.TENSION: ConflictPhase.CEASEFIRE,
                    ConflictPhase.DEESCALATION: ConflictPhase.CEASEFIRE,
                    ConflictPhase.CEASEFIRE: ConflictPhase.NEGOTIATION,
                    ConflictPhase.NEGOTIATION: ConflictPhase.RESOLUTION,
                }
                new_phase = deesc_transitions.get(conflict.phase, conflict.phase)
                conflict.phase = new_phase

                result.state_changes.append({
                    "type": "conflict_deescalated",
                    "conflict_id": conflict.conflict_id,
                    "old_phase": old_phase.value,
                    "new_phase": new_phase.value,
                    "deescalation_probability": round(p_deesc, 4),
                    "roll": round(roll, 4),
                })

            # Natural escalation pressure from leader bias
            elif conflict.phase in (ConflictPhase.TENSION, ConflictPhase.ESCALATION):
                for party_id in parties:
                    leader = self._get_faction_leader(party_id)
                    if leader and leader.escalation_threshold < 0.5:
                        # Wider window + stronger roll = more escalation
                        esc_chance = (0.5 - leader.escalation_threshold) * 0.5
                        esc_roll = self._rng.random()
                        if esc_roll < esc_chance:
                            self._escalate_conflict(conflict, result)
                            # War pressure on the escalating leader
                            leader.war_pressure = min(
                                1.0, leader.war_pressure + 0.1
                            )
                            leader.war_losses += 1 if conflict.phase == ConflictPhase.OPEN_CONFLICT else 0
                            break

            # War cost accrual for active conflicts
            if conflict.phase in (ConflictPhase.OPEN_CONFLICT, ConflictPhase.STALEMATE):
                for party_id in parties:
                    current_cost = conflict.war_cost_estimate.get(party_id, 0.3)
                    conflict.war_cost_estimate[party_id] = min(
                        1.0, current_cost + 0.03
                    )
                    conflict.internal_pressure[party_id] = min(
                        1.0, conflict.internal_pressure.get(party_id, 0.2) + 0.04
                    )
                    # War stress on leaders
                    leader = self._get_faction_leader(party_id)
                    if leader:
                        leader.war_pressure = min(1.0, leader.war_pressure + 0.05)
                        leader.war_losses += 1
                        leader.public_legitimacy = max(
                            0.1, leader.public_legitimacy - 0.02
                        )
                conflict.stalemate_index = min(
                    1.0, conflict.stalemate_index + 0.05
                )
                conflict.casualty_index = min(
                    1.0, conflict.casualty_index + 0.03
                )

    def _escalate_conflict(
        self, conflict: ConflictState, result: TickResult,
    ) -> None:
        old_phase = conflict.phase
        if conflict.phase == ConflictPhase.TENSION:
            conflict.phase = ConflictPhase.ESCALATION
        elif conflict.phase == ConflictPhase.ESCALATION:
            conflict.phase = ConflictPhase.OPEN_CONFLICT

        if conflict.phase != old_phase:
            result.state_changes.append({
                "type": "conflict_escalated",
                "conflict_id": conflict.conflict_id,
                "old_phase": old_phase.value,
                "new_phase": conflict.phase.value,
                "cause": "leader_bias_pressure",
            })

    # ------------------------------------------------------------------ #
    # PHASE 4: TREATY EVALUATION                                          #
    # ------------------------------------------------------------------ #

    def _evaluate_treaties(self, result: TickResult) -> None:
        """Evaluate active treaties for reputation decay."""
        assert self._state is not None

        for treaty in self._state.treaties.values():
            if not treaty.is_active:
                continue

            treaty.turns_since_ratification += 1

            # Reputation recovery via decay for all parties
            for party_id in treaty.parties:
                faction = self._state.factions.get(party_id)
                if faction and faction.reputation < 0.7:
                    breaches = treaty.breach_count.get(party_id, 0)
                    if breaches == 0:
                        # Clean record: slow reputation recovery
                        faction.reputation = min(
                            1.0, faction.reputation + 0.01
                        )

    # ------------------------------------------------------------------ #
    # PHASE 4.5: PEACETIME RECOVERY                                       #
    # ------------------------------------------------------------------ #

    def _peacetime_recovery(self, result: TickResult) -> None:
        """
        Phase 4.5: Background maintenance during peace.

        This is NOT the primary recovery mechanism — that's handled
        by discrete constructive events (trade agreements, infrastructure
        investments, economic booms) in Phase 6.

        This phase handles only:
        - Tiny population stability drift (people adapt)
        - Leader stressor decay (pressure fades with time)
        - Post-resolution trust building (peace dividends)
        - War-weariness accumulation for leaders in active conflict
        """
        assert self._state is not None

        # Determine which factions are currently in active fighting
        factions_at_war = set()
        for conflict in self._state.conflicts.values():
            if conflict.phase in (
                ConflictPhase.OPEN_CONFLICT,
                ConflictPhase.ESCALATION,
                ConflictPhase.STALEMATE,
            ):
                for party in conflict.parties:
                    factions_at_war.add(party)

        for fid, faction in self._state.factions.items():
            at_war = fid in factions_at_war
            leader = self._get_faction_leader(fid)

            if not at_war:
                # Population stability: homeostatic recovery toward baseline.
                # Rate scales with distance from equilibrium — faster when
                # deeply destabilized, gentler near the attractor.
                _POP_EQUILIBRIUM = 0.45
                _POP_RECOVERY_BASE = 0.006
                _POP_RECOVERY_ACCEL = 0.012  # extra rate when far below eq
                if faction.population_stability < 0.80:
                    gap = max(0.0, _POP_EQUILIBRIUM - faction.population_stability)
                    rate = _POP_RECOVERY_BASE + _POP_RECOVERY_ACCEL * gap
                    faction.population_stability = min(
                        1.0, faction.population_stability + rate
                    )

                # Leader maintenance during peace
                if leader:
                    # War pressure bleeds off during peace
                    leader.war_pressure = max(
                        0.0, leader.war_pressure - 0.02
                    )
                    # War losses heal slowly (leaders process, retire, rotate)
                    if leader.war_losses > 0 and self._state.turn % 5 == 0:
                        leader.war_losses = max(0, leader.war_losses - 1)
                    # Legitimacy recovery: competent governance in peacetime
                    # rebuilds public confidence (slow, capped below peak)
                    _LEG_EQUILIBRIUM = 0.45
                    _LEG_RECOVERY_RATE = 0.004
                    if leader.public_legitimacy < _LEG_EQUILIBRIUM:
                        leader.public_legitimacy = min(
                            _LEG_EQUILIBRIUM,
                            leader.public_legitimacy + _LEG_RECOVERY_RATE,
                        )
            else:
                # At war: war-weariness accumulates
                if leader:
                    leader.war_pressure = min(
                        1.0, leader.war_pressure + 0.02
                    )

        # Post-resolution trust building (peace dividends)
        for conflict in self._state.conflicts.values():
            if conflict.phase == ConflictPhase.RESOLUTION:
                for i, party_a in enumerate(conflict.parties):
                    for party_b in conflict.parties[i + 1:]:
                        fa = self._state.factions.get(party_a)
                        fb = self._state.factions.get(party_b)
                        if fa and fb:
                            trust_ab = fa.trust_scores.get(party_b, 0.5)
                            if trust_ab < 0.55:
                                fa.trust_scores[party_b] = min(
                                    0.55, trust_ab + 0.02
                                )
                            trust_ba = fb.trust_scores.get(party_a, 0.5)
                            if trust_ba < 0.55:
                                fb.trust_scores[party_a] = min(
                                    0.55, trust_ba + 0.02
                                )

    # ------------------------------------------------------------------ #
    # PHASE 5: DIPLOMACY TICK                                             #
    # ------------------------------------------------------------------ #

    def _diplomacy_tick(self, result: TickResult) -> None:
        """Run trust updates and espionage checks."""
        assert self._state is not None

        faction_ids = list(self._state.factions.keys())

        # Natural trust drift toward neutral (slow mean reversion)
        for fid in faction_ids:
            faction = self._state.factions[fid]
            for other_id, trust in list(faction.trust_scores.items()):
                drift = (0.5 - trust) * 0.01
                faction.trust_scores[other_id] = max(
                    0.0, min(1.0, trust + drift)
                )

        # Espionage risk check for low-trust pairs
        for i, fid_a in enumerate(faction_ids):
            for fid_b in faction_ids[i + 1:]:
                trust_ab = self._state.factions[fid_a].trust_scores.get(fid_b, 0.5)
                if trust_ab < 0.35:
                    risk = calc_double_agent_risk(
                        bilateral_trust=trust_ab,
                        intel_sensitivity=0.5,
                    )
                    roll = self._rng.random()
                    if roll < risk * 0.1:  # Low base probability per turn
                        event = SimulationEvent(
                            event_id=f"espionage_{fid_a}_{fid_b}_{self._state.turn}",
                            event_type=EventType.ESPIONAGE_EXPOSURE,
                            turn=self._state.turn,
                            source_faction=fid_a,
                            target_faction=fid_b,
                            severity=0.4 + self._rng.random() * 0.3,
                            description=f"Espionage detected between {fid_a} and {fid_b}",
                        )
                        result.events_generated.append(event)
                        self._apply_event(event, result)

        # Update derived diplomacy fields
        for fid in faction_ids:
            faction = self._state.factions[fid]
            avg_trust = (
                sum(faction.trust_scores.values()) / max(1, len(faction.trust_scores))
            )
            faction.verification_demand = max(0.0, 1.0 - avg_trust)
            faction.deal_discount = max(0.0, (0.5 - avg_trust) * 0.2)
            faction.coalition_invite_weight = min(1.0, avg_trust * faction.reputation)

    # ------------------------------------------------------------------ #
    # PHASE 6: EMERGENT EVENTS                                            #
    # ------------------------------------------------------------------ #

    def _generate_emergent_events(self, result: TickResult) -> None:
        """
        Phase 6: Generate stochastic emergent events.

        The galaxy must not converge to peace. Turbulence sources:
        - Economic shocks from instability
        - Leader-driven diplomatic overtures (high openness)
        - Leader-driven military escalation (low escalation_threshold)
        - Faction-on-faction aggression from low-trust pairs (new conflicts)
        - Intelligence leaks from espionage-heavy factions
        - Internal coups when leader legitimacy is critically low
        """
        assert self._state is not None

        # Track who's fighting for positive event eligibility
        factions_at_war_this_turn: set = set()
        for conflict in self._state.conflicts.values():
            if conflict.phase in (
                ConflictPhase.OPEN_CONFLICT,
                ConflictPhase.ESCALATION,
                ConflictPhase.STALEMATE,
            ):
                for party in conflict.parties:
                    factions_at_war_this_turn.add(party)

        # --- Economic shocks (probability scales with instability) ---
        for fid, faction in self._state.factions.items():
            if faction.population_stability < 0.5:
                shock_p = 0.06 + (0.5 - faction.population_stability) * 0.2
                if self._rng.random() < shock_p:
                    event = SimulationEvent(
                        event_id=f"econ_shock_{fid}_{self._state.turn}",
                        event_type=EventType.ECONOMIC_SHOCK,
                        turn=self._state.turn,
                        target_faction=fid,
                        severity=0.3 + self._rng.random() * 0.4,
                        description=f"Economic instability in {faction.name}",
                    )
                    result.events_generated.append(event)
                    self._apply_event(event, result)

        # --- Leader-driven actions ---
        for leader in self._state.leaders.values():
            faction = self._state.factions.get(leader.faction_id)
            if not faction:
                continue

            # Diplomatic overtures from open leaders
            if leader.diplomacy_openness > 0.55 and self._rng.random() < 0.08:
                candidates = [
                    fid for fid in self._state.factions
                    if fid != leader.faction_id
                    and faction.trust_scores.get(fid, 0.5) > 0.3
                ]
                if candidates:
                    target = self._rng.choice(candidates)
                    event = SimulationEvent(
                        event_id=f"diplo_{leader.faction_id}_{target}_{self._state.turn}",
                        event_type=EventType.DIPLOMATIC_OVERTURE,
                        turn=self._state.turn,
                        source_faction=leader.faction_id,
                        target_faction=target,
                        severity=0.3,
                        parameters={"trust_bonus": 0.05 + leader.diplomacy_openness * 0.05},
                        description=f"Diplomatic overture from {leader.name}",
                    )
                    result.events_generated.append(event)
                    self._apply_event(event, result)

            # Military escalation from aggressive leaders
            if leader.escalation_threshold < 0.45 and self._rng.random() < 0.10:
                enemies = [
                    fid for fid in self._state.factions
                    if fid != leader.faction_id
                    and faction.trust_scores.get(fid, 0.5) < 0.4
                ]
                if enemies:
                    target = self._rng.choice(enemies)
                    severity = 0.3 + (0.45 - leader.escalation_threshold) * 0.5
                    event = SimulationEvent(
                        event_id=f"aggression_{leader.faction_id}_{target}_{self._state.turn}",
                        event_type=EventType.MILITARY_ESCALATION,
                        turn=self._state.turn,
                        source_faction=leader.faction_id,
                        target_faction=target,
                        severity=min(0.8, severity),
                        description=(
                            f"{leader.name} provokes military escalation "
                            f"against {self._state.factions.get(target, target)}"
                        ),
                    )
                    result.events_generated.append(event)
                    self._apply_event(event, result)
                    # Stress the aggressor too
                    leader.war_pressure = min(1.0, leader.war_pressure + 0.1)

        # --- Low-trust pair friction (new conflict seeds) ---
        faction_ids = list(self._state.factions.keys())
        for i, fid_a in enumerate(faction_ids):
            for fid_b in faction_ids[i + 1:]:
                trust = self._state.factions[fid_a].trust_scores.get(fid_b, 0.5)
                if trust < 0.25 and self._rng.random() < 0.04:
                    # Check no existing conflict
                    existing = self._find_conflict(fid_a, fid_b)
                    if existing is None:
                        event = SimulationEvent(
                            event_id=f"friction_{fid_a}_{fid_b}_{self._state.turn}",
                            event_type=EventType.MILITARY_ESCALATION,
                            turn=self._state.turn,
                            source_faction=fid_a,
                            target_faction=fid_b,
                            severity=0.3 + self._rng.random() * 0.2,
                            description=f"Border friction between {fid_a} and {fid_b}",
                        )
                        result.events_generated.append(event)
                        self._apply_event(event, result)

        # --- Internal coup risk (low legitimacy + high war pressure) ---
        for leader in self._state.leaders.values():
            coup_risk = (
                (1.0 - leader.public_legitimacy) * 0.4
                + leader.war_pressure * 0.3
                + (leader.betrayals * 0.05)
            )
            if coup_risk > 0.4 and self._rng.random() < coup_risk * 0.05:
                result.state_changes.append({
                    "type": "internal_coup_attempt",
                    "leader": leader.leader_id,
                    "faction": leader.faction_id,
                    "coup_risk": round(coup_risk, 4),
                })
                # Coup destabilizes: legitimacy hit, scandal, elite support drop
                leader.public_legitimacy = max(0.1, leader.public_legitimacy - 0.15)
                leader.elite_support = max(0.1, leader.elite_support - 0.2)
                leader.scandals += 1
                # Faction instability
                faction = self._state.factions.get(leader.faction_id)
                if faction:
                    faction.population_stability = max(
                        0.1, faction.population_stability - 0.1
                    )

        # ============================================================
        # CONSTRUCTIVE EMERGENT EVENTS
        #
        # These are first-class events, same as military escalations.
        # Things that build are as real as things that destroy.
        #
        # Design ratios (target):
        #   Frequency: constructive ~3-4x more often than destructive
        #   Magnitude: destructive ~2-3x harder per hit
        #   Net: slowly positive with sharp periodic reversals
        # ============================================================

        # --- Trade agreements (high-trust pairs not at war) ---
        # This is the primary constructive driver. Most economic
        # interactions between polities are cooperative.
        faction_ids = list(self._state.factions.keys())
        for i, fid_a in enumerate(faction_ids):
            for fid_b in faction_ids[i + 1:]:
                if fid_a in factions_at_war_this_turn or fid_b in factions_at_war_this_turn:
                    continue
                trust = self._state.factions[fid_a].trust_scores.get(fid_b, 0.5)
                # Higher trust = more likely trade. p=0.02 at trust 0.5, up to 0.06 at trust 0.8
                trade_p = max(0.0, (trust - 0.35) * 0.12)
                if trade_p > 0 and self._rng.random() < trade_p:
                    trade_value = 0.02 + trust * 0.03  # 0.03-0.05
                    event = SimulationEvent(
                        event_id=f"trade_{fid_a}_{fid_b}_{self._state.turn}",
                        event_type=EventType.TRADE_AGREEMENT,
                        turn=self._state.turn,
                        source_faction=fid_a,
                        target_faction=fid_b,
                        severity=0.3,
                        parameters={"trade_value": trade_value},
                        description=f"Trade agreement between {fid_a} and {fid_b}",
                    )
                    result.events_generated.append(event)
                    self._apply_event(event, result)

        # --- Economic boom (strong economy + stable population + peace) ---
        # Less frequent than trade, bigger per-hit. Domestic expansion.
        for fid, faction in self._state.factions.items():
            if fid in factions_at_war_this_turn:
                continue
            if (faction.economic_strength > 0.4
                    and faction.population_stability > 0.5
                    and faction.economic_strength < faction.economic_potential):
                if self._rng.random() < 0.025:
                    event = SimulationEvent(
                        event_id=f"boom_{fid}_{self._state.turn}",
                        event_type=EventType.ECONOMIC_BOOM,
                        turn=self._state.turn,
                        target_faction=fid,
                        severity=0.3 + self._rng.random() * 0.4,
                        description=f"Economic expansion in {faction.name}",
                    )
                    result.events_generated.append(event)
                    self._apply_event(event, result)

        # --- Technology breakthrough (high tech factions) ---
        # Rare but impactful. Tech accumulates.
        for fid, faction in self._state.factions.items():
            if faction.technology_level > 0.4 and self._rng.random() < 0.02:
                event = SimulationEvent(
                    event_id=f"tech_{fid}_{self._state.turn}",
                    event_type=EventType.TECHNOLOGY_BREAKTHROUGH,
                    turn=self._state.turn,
                    target_faction=fid,
                    severity=0.3 + self._rng.random() * 0.3,
                    description=f"Technology breakthrough in {faction.name}",
                )
                result.events_generated.append(event)
                self._apply_event(event, result)

        # --- Cultural movement (population below baseline + peace) ---
        # Social recovery. Not economic — this is people finding stability.
        for fid, faction in self._state.factions.items():
            if fid in factions_at_war_this_turn:
                continue
            if faction.population_stability < 0.6 and faction.population_stability > 0.1:
                if self._rng.random() < 0.04:
                    # Pick a random neighbor for cultural exchange
                    neighbors = [
                        f for f in faction_ids
                        if f != fid and faction.trust_scores.get(f, 0.5) > 0.3
                    ]
                    partner = self._rng.choice(neighbors) if neighbors else None
                    event = SimulationEvent(
                        event_id=f"culture_{fid}_{self._state.turn}",
                        event_type=EventType.CULTURAL_MOVEMENT,
                        turn=self._state.turn,
                        target_faction=fid,
                        severity=0.3 + self._rng.random() * 0.3,
                        parameters={"cultural_partner": partner},
                        description=f"Cultural movement in {faction.name}",
                    )
                    result.events_generated.append(event)
                    self._apply_event(event, result)

        # --- Infrastructure investment (below economic potential + peace) ---
        # Deliberate rebuilding. The domestic equivalent of trade deals.
        for fid, faction in self._state.factions.items():
            if fid in factions_at_war_this_turn:
                continue
            if faction.economic_strength < faction.economic_potential * 0.85:
                invest_p = 0.04 + faction.technology_level * 0.02
                if self._rng.random() < invest_p:
                    event = SimulationEvent(
                        event_id=f"infra_{fid}_{self._state.turn}",
                        event_type=EventType.INFRASTRUCTURE_INVESTMENT,
                        turn=self._state.turn,
                        target_faction=fid,
                        severity=0.3 + self._rng.random() * 0.3,
                        description=f"Infrastructure investment in {faction.name}",
                    )
                    result.events_generated.append(event)
                    self._apply_event(event, result)

        # --- Peace legitimacy (resolved conflict → leader credibility) ---
        for conflict in self._state.conflicts.values():
            if (conflict.phase == ConflictPhase.RESOLUTION
                    and conflict.turns_active > 0
                    and self._rng.random() < 0.06):
                for party in conflict.parties:
                    leader = self._get_faction_leader(party)
                    if leader and leader.public_legitimacy < 0.8:
                        leader.public_legitimacy = min(
                            1.0, leader.public_legitimacy + 0.03
                        )
                        result.state_changes.append({
                            "type": "peace_legitimacy_boost",
                            "leader": leader.leader_id,
                            "delta": 0.03,
                        })

    # ------------------------------------------------------------------ #
    # HELPERS                                                             #
    # ------------------------------------------------------------------ #

    def _require_init(self) -> None:
        if not self._initialized or self._state is None:
            raise RuntimeError(
                "Engine not initialized. Call init_scenario() first."
            )

    def _find_conflict(
        self, faction_a: str, faction_b: str,
    ) -> Optional[ConflictState]:
        """Find an existing conflict involving both factions."""
        assert self._state is not None
        for conflict in self._state.conflicts.values():
            if faction_a in conflict.parties and faction_b in conflict.parties:
                return conflict
        return None

    def _get_faction_leader(self, faction_id: str) -> Optional[LeaderState]:
        """Get the primary leader for a faction."""
        assert self._state is not None
        faction = self._state.factions.get(faction_id)
        if faction and faction.leader_id:
            return self._state.leaders.get(faction.leader_id)
        return None

    def _adjust_trust(
        self,
        faction_a: str,
        faction_b: str,
        delta: float,
        result: TickResult,
    ) -> None:
        """Adjust bilateral trust and log the change."""
        assert self._state is not None
        fa = self._state.factions.get(faction_a)
        fb = self._state.factions.get(faction_b)

        old_ab = None
        if fa and faction_b in fa.trust_scores:
            old_ab = fa.trust_scores[faction_b]
            fa.trust_scores[faction_b] = max(
                0.0, min(1.0, fa.trust_scores[faction_b] + delta)
            )
        if fb and faction_a in fb.trust_scores:
            fb.trust_scores[faction_a] = max(
                0.0, min(1.0, fb.trust_scores[faction_a] + delta)
            )

        if old_ab is not None:
            result.state_changes.append({
                "type": "trust_adjusted",
                "faction_a": faction_a,
                "faction_b": faction_b,
                "delta": round(delta, 4),
                "new_trust_ab": round(fa.trust_scores[faction_b], 4) if fa else None,
            })

    def _check_ethics(
        self, action_type: str, params: Dict[str, Any],
    ) -> bool:
        """
        Check action against ethics callback if attached.
        Returns True if action is allowed, False if vetoed.
        """
        if self._ethics_callback is None:
            return True
        try:
            return self._ethics_callback(action_type, params)
        except Exception as e:
            logger.error("Ethics callback error: %s", e)
            # Picard_Delta_3: when in doubt, block
            return False


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

def main() -> None:
    """Demo: run the canonical scenario for 20 turns."""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(name)s %(levelname)s - %(message)s",
    )

    print("=" * 60)
    print("  GUMAS L2 Simulation Engine — Demo Run")
    print("  Anchor: GUMAS-ENGINE-CORE-V1")
    print("  Ethics: Picard_Delta_3")
    print("=" * 60)

    engine = GUMASEngine(seed=42)
    state = engine.init_scenario()

    print(f"\nScenario: {state.scenario_id}")
    print(f"Factions: {len(state.factions)}")
    print(f"Leaders:  {len(state.leaders)}")
    print(f"Conflicts: {len(state.conflicts)}")
    print()

    for _ in range(20):
        result = engine.step()
        events_str = ", ".join(
            e.event_type.value for e in result.events_generated
        ) or "none"
        changes = len(result.state_changes)

        # Show conflict phases
        phases = {
            c.conflict_id: c.phase.value
            for c in state.conflicts.values()
            if c.phase != ConflictPhase.PEACE
        }
        print(
            f"  Turn {result.turn:>3}: "
            f"{changes:>2} changes, "
            f"emergent=[{events_str}], "
            f"conflicts={phases}"
        )

    # Final summary
    print("\n" + "=" * 60)
    print("  Final State Summary")
    print("=" * 60)

    for fid, faction in state.factions.items():
        leader = engine._get_faction_leader(fid)
        leader_name = leader.name if leader else "none"
        low_trust = [
            other for other, t in faction.trust_scores.items() if t < 0.3
        ]
        print(
            f"  {faction.name:<30} "
            f"rep={faction.reputation:.2f}  "
            f"mil={faction.military_strength:.2f}  "
            f"econ={faction.economic_strength:.2f}  "
            f"leader={leader_name}"
        )
        if low_trust:
            print(f"    ↳ low trust with: {', '.join(low_trust)}")

    print()
    for cid, conflict in state.conflicts.items():
        print(
            f"  Conflict '{cid}': {conflict.phase.value} "
            f"(turns={conflict.turns_active}, "
            f"deesc_p={conflict.deescalation_probability:.3f})"
        )

    # Export
    output_path = "gumas_demo_output.json"
    engine.export_state(output_path)
    print(f"\nState exported to {output_path}")


if __name__ == "__main__":
    main()

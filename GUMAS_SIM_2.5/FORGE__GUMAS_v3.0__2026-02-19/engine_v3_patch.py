#!/usr/bin/env python3
"""
GUMAS v3.0 — Engine Integration Patch
=======================================
Anchor: GUMAS-ENGINE-V3-PATCH
Seed:   EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP:    L2_ENGINE_V3
Version: 3.0.0

Integrates the five new v3.0 subsystems (population, technology,
negotiation, intelligence, rebellion) into the existing GUMAS engine
lifecycle as Phases 16–20.

This patch uses a mixin / extension pattern: GUMASEngineV3 inherits
from the v2.0 GUMASEngine and overrides the step() method to add
5 new phases after the existing 15.

Design decisions:
    - Full backward compatibility: all v2.0 mechanics unchanged
    - V3 state held in GUMASStateV3Extension (composition)
    - Ethics gate (Picard_Delta_3) guards fragmentation events
    - Each phase returns event dicts appended to TickResult

Phases added:
    Phase 16: Population Tick
    Phase 17: Technology Tick
    Phase 18: Negotiation Tick
    Phase 19: Intelligence Tick
    Phase 20: Rebellion Tick (+ cross-module feedback writes)

Cross-module feedback (post Phase 20):
    - tech_combat_multipliers applied to FactionState.military_strength
    - tech_economic_multipliers applied to FactionState.economic_strength
    - demographic_stress fed to rebellion onset check
    - ci_strength fed from IntelNetwork to rebellion engine
    - insurgency territory_controlled reduces effective economic output
"""

from __future__ import annotations

import logging
import sys
import os
from typing import Any, Dict, List, Optional

# --- v2.0 engine imports (adjust path as needed) ---
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models_v3_ext import (
    GUMASStateV3Extension,
    TickResultV3,
    init_v3_extension_from_scenario,
)
from population   import PopulationEngine, calc_conscription_capacity
from technology   import TechnologyEngine, calc_civilian_tech_multiplier, TechCategory
from negotiation  import NegotiationEngine
from intelligence import IntelligenceEngine
from rebellion    import RebellionEngine

logger = logging.getLogger(__name__)


# ============================================================================
# V3.0 ENGINE MIXIN
# ============================================================================

class GUMASEngineV3Mixin:
    """
    Mixin providing v3.0 tick phases 16–20.

    Requires the host class to have:
        self._state         — GUMASState (v2.0 base state)
        self._rng           — seeded Random instance
        self._ethics_callback — optional Picard_Delta_3 gate
        self._initialized   — bool

    The mixin provides:
        self._v3_state      — GUMASStateV3Extension
        self._pop_engine    — PopulationEngine
        self._tech_engine   — TechnologyEngine
        self._neg_engine    — NegotiationEngine
        self._intel_engine  — IntelligenceEngine
        self._reb_engine    — RebellionEngine
        self.step_v3()      — run all 5 new phases, return TickResultV3
    """

    def _init_v3_subsystems(self) -> None:
        """Called by GUMASEngineV3.init_scenario() after base init."""
        if not self._initialized:
            raise RuntimeError("Base engine must be initialized before v3 subsystems.")

        fids = list(self._state.factions.keys())
        faction_types = {
            fid: self._state.factions[fid].faction_type.value
            for fid in fids
        }

        self._v3_state = init_v3_extension_from_scenario(fids, faction_types)

        # Set up intel sharing between high-trust pairs
        for fid_a in fids:
            for fid_b in fids:
                if fid_a == fid_b:
                    continue
                trust = self._state.factions[fid_a].trust_scores.get(fid_b, 0.0)
                if trust > 0.65:
                    self._v3_state.intel_networks[fid_a].sharing_partners.add(fid_b)

        self._pop_engine   = PopulationEngine()
        self._tech_engine  = TechnologyEngine()
        self._neg_engine   = NegotiationEngine()
        self._intel_engine = IntelligenceEngine()
        self._reb_engine   = RebellionEngine()

        logger.info("GUMAS v3.0 subsystems initialized for %d factions.", len(fids))

    def step_v3(self) -> TickResultV3:
        """
        Execute tick phases 16–20 and apply cross-module feedback.

        Returns:
            TickResultV3 with event summary
        """
        state  = self._state
        v3     = self._v3_state
        rng    = self._rng
        result = TickResultV3(turn=state.current_turn)

        # ── Phase 16: Population Tick ────────────────────────────────────────
        faction_conflicts: Dict[str, List[str]] = {}
        for cid, conflict in state.conflicts.items():
            for fid in conflict.parties:
                faction_conflicts.setdefault(fid, []).append(cid)

        pop_events = self._pop_engine.tick(
            populations=v3.population,
            faction_conflicts=faction_conflicts,
            faction_military_strength={
                fid: f.military_strength for fid, f in state.factions.items()
            },
            rng=rng,
        )
        for ev in pop_events:
            result.v3_events.append(ev)
            if ev["type"] == "POPULATION_MIGRATION":
                result.migrations += 1

        # ── Phase 17: Technology Tick ────────────────────────────────────────
        trust_matrix: Dict[str, Dict[str, float]] = {
            fid: dict(f.trust_scores)
            for fid, f in state.factions.items()
        }

        tech_events = self._tech_engine.tick(
            tech_states=v3.technology,
            trust_matrix=trust_matrix,
            rng=rng,
        )
        for ev in tech_events:
            result.v3_events.append(ev)
            if ev["type"] == "TECH_BREAKTHROUGH_ADVANCED":
                result.tech_breakthroughs += 1

        # Recompute tech multipliers for cross-module feedback
        for fid, ts in v3.technology.items():
            v3.tech_combat_multipliers[fid]   = self._tech_engine.get_combat_multiplier(ts)
            v3.tech_economic_multipliers[fid] = self._tech_engine.get_economic_multiplier(ts)

        # ── Phase 18: Negotiation Tick ───────────────────────────────────────
        leader_openness = {
            fid: state.leaders[f.leader_id].diplomacy_openness
            for fid, f in state.factions.items()
            if f.leader_id and f.leader_id in state.leaders
        }

        neg_events = self._neg_engine.tick(
            negotiations=v3.negotiations,
            ultimatums=v3.ultimatums,
            trust_matrix=trust_matrix,
            leader_diplomacy_openness=leader_openness,
            rng=rng,
        )
        for ev in neg_events:
            result.v3_events.append(ev)
            if ev["type"] in ("DIPLOMATIC_AGREEMENT", "BACK_CHANNEL_DEAL"):
                result.negotiations_concluded += 1
                # Apply trust boost from concluded negotiation
                neg_id = ev.get("negotiation_id")
                neg = next((n for n in v3.negotiations if n.negotiation_id == neg_id), None)
                if neg and neg.trust_delta != 0:
                    for fid_pair in [(neg.party_a, neg.party_b), (neg.party_b, neg.party_a)]:
                        src, dst = fid_pair
                        if src in state.factions:
                            current = state.factions[src].trust_scores.get(dst, 0.0)
                            state.factions[src].trust_scores[dst] = min(
                                1.0, current + neg.trust_delta
                            )

        # ── Phase 19: Intelligence Tick ──────────────────────────────────────
        intel_events = self._intel_engine.tick(
            networks=v3.intel_networks,
            faction_military={
                fid: f.military_strength for fid, f in state.factions.items()
            },
            faction_economic={
                fid: f.economic_strength for fid, f in state.factions.items()
            },
            trust_matrix=trust_matrix,
            rng=rng,
        )
        for ev in intel_events:
            result.v3_events.append(ev)
            if ev["type"] in ("INTELLIGENCE_SHARING", "INTELLIGENCE_COMPROMISE"):
                result.intelligence_ops += 1

        # Apply surveillance legitimacy penalties
        for fid, net in v3.intel_networks.items():
            from intelligence import calc_surveillance_legitimacy_penalty
            penalty = calc_surveillance_legitimacy_penalty(net.surveillance_level)
            if fid in state.factions and state.factions[fid].leader_id:
                lid = state.factions[fid].leader_id
                if lid in state.leaders:
                    state.leaders[lid].public_legitimacy = max(
                        0.0, state.leaders[lid].public_legitimacy + penalty
                    )

        # ── Phase 20: Rebellion Tick ─────────────────────────────────────────
        reb_events = self._reb_engine.tick(
            insurgencies=v3.insurgencies,
            demographic_stress={
                fid: v3.population[fid].demographic_stress
                for fid in v3.population
            },
            leader_legitimacy={
                fid: state.leaders[f.leader_id].public_legitimacy
                for fid, f in state.factions.items()
                if f.leader_id and f.leader_id in state.leaders
            },
            leader_institutional_control={
                fid: state.leaders[f.leader_id].institutional_control
                for fid, f in state.factions.items()
                if f.leader_id and f.leader_id in state.leaders
            },
            faction_military_strength={
                fid: f.military_strength for fid, f in state.factions.items()
            },
            ci_strength={
                fid: v3.intel_networks[fid].counter_intel_strength
                for fid in v3.intel_networks
            },
            rng=rng,
        )

        for ev in reb_events:
            # Gate fragmentation events through Picard_Delta_3
            if ev.get("picard_delta_3_required"):
                if self._ethics_callback and not self._ethics_callback(
                    "STATE_FRAGMENTATION", ev
                ):
                    logger.warning(
                        "Picard_Delta_3: STATE_FRAGMENTATION blocked for %s",
                        ev.get("faction_id"),
                    )
                    continue

            result.v3_events.append(ev)

            if ev["type"] == "REBELLION_ONSET":
                result.new_insurgencies += 1
            elif ev["type"] == "CIVIL_WAR_ONSET":
                result.civil_wars_started += 1
            elif ev["type"] == "STATE_FRAGMENTATION":
                result.fragmentation_events += 1
                # Reduce host faction military and economic to reflect split
                fid = ev.get("faction_id")
                split = ev.get("territory_split", 0.1)
                if fid in state.factions:
                    state.factions[fid].military_strength = max(
                        0.05,
                        state.factions[fid].military_strength * (1.0 - split * 0.5)
                    )
                    state.factions[fid].economic_strength = max(
                        0.05,
                        state.factions[fid].economic_strength * (1.0 - split * 0.6)
                    )

        # ── Cross-Module Feedback ────────────────────────────────────────────
        self._apply_v3_feedback(state, v3)

        v3.v3_events = result.v3_events.copy()
        return result

    def _apply_v3_feedback(self, state, v3: GUMASStateV3Extension) -> None:
        """
        Apply computed v3.0 multipliers back to v2.0 base state fields.

        This is the integration point where new mechanics affect existing
        simulation variables (military_strength, economic_strength, etc.).
        """
        for fid, faction in state.factions.items():

            # Technology combat multiplier → military strength ceiling boost
            tech_cmult = v3.tech_combat_multipliers.get(fid, 1.0)
            if tech_cmult > 1.0:
                # Soft boost: pull actual strength toward a tech-boosted target
                target = min(1.0, faction.military_strength * tech_cmult)
                faction.military_strength += (target - faction.military_strength) * 0.05

            # Technology economic multiplier → economic potential boost
            tech_emult = v3.tech_economic_multipliers.get(fid, 1.0)
            if tech_emult > 1.0:
                # Raise economic potential ceiling
                faction.economic_potential = min(1.0, faction.economic_potential * tech_emult)

            # Civilian tech boost to economic strength (from energy/materials/computing)
            if fid in v3.technology:
                ts = v3.technology[fid]
                civtech = calc_civilian_tech_multiplier(
                    energy_level    = ts.get_level(TechCategory.ENERGY),
                    materials_level = ts.get_level(TechCategory.MATERIALS),
                    computing_level = ts.get_level(TechCategory.COMPUTING),
                )
                if civtech > 1.0:
                    faction.economic_strength = min(
                        faction.economic_potential,
                        faction.economic_strength * (1.0 + (civtech - 1.0) * 0.03)
                    )

            # Insurgency drag: active insurgencies reduce effective output
            active_ins = [
                i for i in v3.insurgencies
                if i.host_faction_id == fid
            ]
            for ins in active_ins:
                drag = ins.territory_controlled * 0.08
                faction.military_strength  = max(0.05, faction.military_strength  - drag * 0.5)
                faction.economic_strength  = max(0.05, faction.economic_strength  - drag * 0.7)
                faction.population_stability = max(
                    0.05, faction.population_stability - drag * 0.4
                )

            # Conscription capacity update
            if fid in v3.population:
                pop = v3.population[fid]
                cap = calc_conscription_capacity(
                    pop.population_index,
                    pop.military_age_fraction,
                    pop.current_mobilization,
                    demographic_stress_penalty=pop.demographic_stress,
                )
                v3.conscription_capacity[fid] = cap

            # Fused intel estimates — update faction's perception of others
            if fid in v3.intel_networks:
                net = v3.intel_networks[fid]
                for target_fid, estimates in net.fused_estimates.items():
                    # Faction now "perceives" target's state with accuracy-weighted error
                    # (This would feed into threat perception and doctrine updates)
                    pass  # Perception system reserved for v3.1


# ============================================================================
# COMBINED V3.0 ENGINE
# ============================================================================

class GUMASEngineV3(GUMASEngineV3Mixin):
    """
    Full GUMAS v3.0 engine with all 20 tick phases.

    This class combines the v2.0 GUMASEngine (via deferred import to
    avoid circular deps at design time) with the v3.0 mixin.

    Public API (backward-compatible + extensions):
        engine = GUMASEngineV3(seed=42)
        engine.init_scenario()               # init base + v3 subsystems
        result, v3_result = engine.full_step() # advance one full turn (all 20 phases)
        engine.run_v3(n_turns=10)            # batch run
        engine.export_state_v3("out.json")   # full export

    Usage alongside v2.0 engine (standalone mode):
        engine = GUMASEngineV3(seed=42, standalone_v3=True)
        engine.init_minimal()               # minimal state for v3-only testing
    """

    def __init__(self, seed: int = 42, ethics_callback=None):
        # Defer import of v2.0 engine to allow standalone testing
        try:
            # Attempt to import v2.0 engine from parent directory
            parent = os.path.join(os.path.dirname(__file__), "..", "SIM_ENGINE_OUTPUTS")
            sys.path.insert(0, parent)
            from engine import GUMASEngine
            # We cannot call super().__init__ from a dynamic import,
            # so we delegate instead
            self._base_engine = GUMASEngine(seed=seed, ethics_callback=ethics_callback)
            self._delegate_mode = True
        except ImportError:
            self._delegate_mode = False
            logger.warning("v2.0 engine not found; running in v3-standalone mode.")

        self._seed = seed
        import random
        self._rng = random.Random(seed + 1000)  # separate RNG stream for v3
        self._ethics_callback = ethics_callback
        self._initialized = False

    def init_scenario(self, state=None) -> None:
        """Initialize base scenario and v3.0 subsystems."""
        if self._delegate_mode:
            self._base_engine.init_scenario(state)
            # Mirror state reference
            self._state = self._base_engine._state
        else:
            # Standalone: create minimal state for v3-only testing
            self._init_minimal_state()

        self._initialized = True
        self._init_v3_subsystems()

    def _init_minimal_state(self) -> None:
        """
        Minimal state object for v3-standalone testing.
        Creates a lightweight namespace mirroring GUMASState API.
        """
        import types, random

        state = types.SimpleNamespace()
        state.current_turn = 0
        state.factions = {}
        state.leaders = {}
        state.conflicts = {}

        # Create 3 test factions
        for i, (fid, fname, ftype_val) in enumerate([
            ("GU_CORE",     "Galactic Union",           "federation"),
            ("VELAR_IMP",   "Velar Imperium",            "authoritarian imperial bloc"),
            ("OUTER_CONF",  "Outer Colonies Confederation", "frontier confederation"),
        ]):
            f = types.SimpleNamespace()
            f.faction_id = fid
            f.name = fname
            f.faction_type = types.SimpleNamespace(value=ftype_val)
            f.leader_id = f"LEADER_{fid}"
            f.military_strength = 0.5 + (i * 0.05)
            f.economic_strength = 0.5 + (i * 0.03)
            f.economic_potential = 0.75
            f.population_stability = 0.70
            f.trust_scores = {
                other_fid: round(0.3 + random.Random(42 + i).uniform(-0.1, 0.2), 2)
                for other_fid in ["GU_CORE", "VELAR_IMP", "OUTER_CONF"]
                if other_fid != fid
            }
            state.factions[fid] = f

            l = types.SimpleNamespace()
            l.leader_id = f.leader_id
            l.public_legitimacy = 0.70
            l.institutional_control = 0.55
            l.diplomacy_openness = 0.50
            state.leaders[f.leader_id] = l

        self._state = state

    def full_step(self):
        """
        Execute a complete 20-phase tick.

        Returns:
            (base_TickResult or None, TickResultV3)
        """
        base_result = None
        if self._delegate_mode:
            base_result = self._base_engine.step()
            self._state = self._base_engine._state  # sync state reference
            self._state.current_turn = base_result.turn
        else:
            self._state.current_turn += 1

        v3_result = self.step_v3()
        return base_result, v3_result

    def run_v3(self, n_turns: int = 10) -> List[TickResultV3]:
        """Run n turns and return all TickResultV3 objects."""
        results = []
        for _ in range(n_turns):
            _, v3r = self.full_step()
            results.append(v3r)
            logger.info(v3r.summary())
        return results

    def get_v3_state(self) -> GUMASStateV3Extension:
        return self._v3_state

    def export_v3_state(self, path: str) -> None:
        """Export v3.0 state extension to JSON."""
        import json
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self._v3_state.to_dict(), fh, indent=2, default=str)
        logger.info("V3 state exported to %s", path)

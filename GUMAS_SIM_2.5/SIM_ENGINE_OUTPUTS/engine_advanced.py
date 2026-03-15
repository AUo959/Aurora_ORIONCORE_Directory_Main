#!/usr/bin/env python3
"""
GUMAS Advanced Simulation Engine
================================
Synthesizes the strongest available engine lineage in this repository:
- Base lifecycle and state model from SIM_ENGINE_OUTPUTS/engine.py
- Forge v3 subsystem phases (Population, Technology, Negotiation,
  Intelligence, Rebellion) from FORGE__GUMAS_v3.0__2026-02-19

This module exposes a single 20-phase-capable engine with deterministic
IDs, backward-compatible base state mutation, and advanced metrics.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from engine_base import GUMASEngine as BaseGUMASEngine
from models import (
    ConflictPhase,
    EventType,
    GUMASState,
    SimulationEvent,
    TickResult,
    TreatyPhase,
    TreatyState,
)

_THIS_DIR = Path(__file__).resolve().parent
_FORGE_DIR = _THIS_DIR.parent / "FORGE__GUMAS_v3.0__2026-02-19"
if _FORGE_DIR.is_dir() and str(_FORGE_DIR) not in sys.path:
    sys.path.insert(0, str(_FORGE_DIR))

try:
    from intelligence import IntelligenceEngine
    from l2_state import L2StateBundle, build_empty_l2_state_bundle, build_l2_state_bundle
    from models_v3_ext import GUMASStateV3Extension, TickResultV3, init_v3_extension_from_scenario
    from negotiation import (
        NegotiationEngine,
        NegotiationPhase,
        NegotiationState,
        Ultimatum,
    )
    from population import PopulationEngine, calc_conscription_capacity
    from rebellion import InsurgencyPhase, RebellionEngine
    from technology import TechCategory, TechnologyEngine, calc_civilian_tech_multiplier
except ImportError as exc:
    raise ImportError(
        "Failed to import Forge v3 modules required by engine_advanced.py. "
        f"Expected directory: {_FORGE_DIR}"
    ) from exc

logger = logging.getLogger(__name__)


@dataclass
class AdvancedTickResult:
    """Combined base + v3 tick result with synthesized metrics."""

    turn: int
    base_result: TickResult
    v3_result: TickResultV3
    stability_index: float
    risk_index: float
    system_components: Dict[str, Any]
    summary: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn": self.turn,
            "stability_index": round(self.stability_index, 4),
            "risk_index": round(self.risk_index, 4),
            "system_components": dict(self.system_components),
            "summary": self.summary,
            "timestamp": self.timestamp,
            "base_result": self.base_result.to_dict(),
            "v3_result": {
                "turn": self.v3_result.turn,
                "v3_events": list(self.v3_result.v3_events),
                "new_insurgencies": self.v3_result.new_insurgencies,
                "civil_wars_started": self.v3_result.civil_wars_started,
                "tech_breakthroughs": self.v3_result.tech_breakthroughs,
                "migrations": self.v3_result.migrations,
                "fragmentation_events": self.v3_result.fragmentation_events,
                "negotiations_concluded": self.v3_result.negotiations_concluded,
                "intelligence_ops": self.v3_result.intelligence_ops,
            },
        }


class GUMASAdvancedEngine(BaseGUMASEngine):
    """
    Synthesized advanced engine.

    Execution order per tick:
    - Base engine phases (1..6 from SIM_ENGINE_OUTPUTS/engine.py)
    - v3 Forge phases (16..20)
    - Cross-module feedback into base faction/leader state
    """

    _ACTIVE_CONFLICT_PHASES = {
        ConflictPhase.TENSION,
        ConflictPhase.ESCALATION,
        ConflictPhase.OPEN_CONFLICT,
        ConflictPhase.STALEMATE,
        ConflictPhase.CEASEFIRE,
        ConflictPhase.NEGOTIATION,
        ConflictPhase.DEESCALATION,
    }

    def __init__(
        self,
        seed: int = 42,
        ethics_callback=None,
    ):
        super().__init__(seed=seed, ethics_callback=ethics_callback)

        self._v3_state: Optional[GUMASStateV3Extension] = None
        self._pop_engine = PopulationEngine()
        self._tech_engine = TechnologyEngine()
        self._neg_engine = NegotiationEngine()
        self._intel_engine = IntelligenceEngine()
        self._reb_engine = RebellionEngine()

        self._advanced_history: List[AdvancedTickResult] = []
        self._event_ledger_records: List[Dict[str, Any]] = []
        self._ultimatum_counter = 0

    def init_scenario(
        self,
        state: Optional[GUMASState] = None,
        scenario_id: str = "gumas_canonical_v1",
    ) -> GUMASState:
        world = super().init_scenario(state=state, scenario_id=scenario_id)
        self._init_v3_subsystems()
        self._advanced_history.clear()
        self._event_ledger_records.clear()
        return world

    def step(self) -> AdvancedTickResult:
        """Run one synthesized tick and return a combined result."""
        base_result = super().step()
        turn = base_result.turn

        if self._v3_state is None:
            empty_v3 = TickResultV3(turn=turn)
            combined = self._assemble_advanced_result(base_result, empty_v3)
            self._advanced_history.append(combined)
            return combined

        self._sync_negotiation_tracks()

        v3_result = TickResultV3(turn=turn)
        phase_ordinals: Dict[str, int] = {}
        self._record_v3_events(
            self._issue_ultimatums(),
            v3_result,
            base_result,
            turn,
            phase="ultimatum",
            phase_ordinals=phase_ordinals,
        )

        faction_conflicts = self._build_faction_conflict_index()
        pop_events = self._pop_engine.tick(
            populations=self._v3_state.population,
            faction_conflicts=faction_conflicts,
            faction_military_strength={
                fid: f.military_strength for fid, f in self.get_state().factions.items()
            },
            rng=self._rng,
        )
        self._record_v3_events(
            pop_events,
            v3_result,
            base_result,
            turn,
            phase="population",
            phase_ordinals=phase_ordinals,
        )

        trust_matrix = {
            fid: dict(f.trust_scores)
            for fid, f in self.get_state().factions.items()
        }
        tech_events = self._tech_engine.tick(
            tech_states=self._v3_state.technology,
            trust_matrix=trust_matrix,
            rng=self._rng,
        )
        self._record_v3_events(
            tech_events,
            v3_result,
            base_result,
            turn,
            phase="technology",
            phase_ordinals=phase_ordinals,
        )

        for fid, tech_state in self._v3_state.technology.items():
            self._v3_state.tech_combat_multipliers[fid] = self._tech_engine.get_combat_multiplier(
                tech_state
            )
            self._v3_state.tech_economic_multipliers[fid] = self._tech_engine.get_economic_multiplier(
                tech_state
            )

        leader_openness = {
            fid: self.get_state().leaders[f.leader_id].diplomacy_openness
            for fid, f in self.get_state().factions.items()
            if f.leader_id and f.leader_id in self.get_state().leaders
        }
        neg_events = self._neg_engine.tick(
            negotiations=self._v3_state.negotiations,
            ultimatums=self._v3_state.ultimatums,
            trust_matrix=trust_matrix,
            leader_diplomacy_openness=leader_openness,
            rng=self._rng,
        )
        self._record_v3_events(
            neg_events,
            v3_result,
            base_result,
            turn,
            phase="negotiation",
            phase_ordinals=phase_ordinals,
        )

        intel_events = self._intel_engine.tick(
            networks=self._v3_state.intel_networks,
            faction_military={
                fid: f.military_strength for fid, f in self.get_state().factions.items()
            },
            faction_economic={
                fid: f.economic_strength for fid, f in self.get_state().factions.items()
            },
            trust_matrix=trust_matrix,
            rng=self._rng,
        )
        self._record_v3_events(
            intel_events,
            v3_result,
            base_result,
            turn,
            phase="intelligence",
            phase_ordinals=phase_ordinals,
        )

        reb_events = self._reb_engine.tick(
            insurgencies=self._v3_state.insurgencies,
            demographic_stress={
                fid: self._v3_state.population[fid].demographic_stress
                for fid in self._v3_state.population
            },
            leader_legitimacy={
                fid: self.get_state().leaders[f.leader_id].public_legitimacy
                for fid, f in self.get_state().factions.items()
                if f.leader_id and f.leader_id in self.get_state().leaders
            },
            leader_institutional_control={
                fid: self.get_state().leaders[f.leader_id].institutional_control
                for fid, f in self.get_state().factions.items()
                if f.leader_id and f.leader_id in self.get_state().leaders
            },
            faction_military_strength={
                fid: f.military_strength for fid, f in self.get_state().factions.items()
            },
            ci_strength={
                fid: self._v3_state.intel_networks[fid].counter_intel_strength
                for fid in self._v3_state.intel_networks
            },
            rng=self._rng,
        )

        id_map = self._canonicalize_insurgency_ids()
        for event in reb_events:
            if "insurgency_id" in event and event["insurgency_id"] in id_map:
                event["insurgency_id"] = id_map[event["insurgency_id"]]
        self._record_v3_events(
            reb_events,
            v3_result,
            base_result,
            turn,
            phase="rebellion",
            phase_ordinals=phase_ordinals,
        )

        self._apply_v3_feedback(base_result)
        self._compact_v3_state()

        combined = self._assemble_advanced_result(base_result, v3_result)
        self._advanced_history.append(combined)
        self._v3_state.v3_events = list(v3_result.v3_events)
        return combined

    def run(self, n_turns: int = 10) -> List[AdvancedTickResult]:
        self._require_init()
        results: List[AdvancedTickResult] = []
        for _ in range(max(0, n_turns)):
            results.append(self.step())
        return results

    def get_v3_state(self) -> Optional[GUMASStateV3Extension]:
        return self._v3_state

    def get_advanced_history(self) -> List[AdvancedTickResult]:
        return list(self._advanced_history)

    def export_advanced_state(
        self,
        path: str,
        *,
        include_base_history: bool = False,
        include_advanced_history: bool = True,
        include_event_ledger: bool = True,
        event_ledger_path: Optional[str] = None,
    ) -> None:
        self._require_init()
        state = self.get_state()

        l2_state: Optional[L2StateBundle] = None
        if self._v3_state is not None:
            l2_state = self._v3_state.l2_state
        if l2_state is None:
            l2_state = build_empty_l2_state_bundle(
                workspace_root=_THIS_DIR.parent.parent,
                faction_ids=state.factions.keys(),
                warning="L2 state was unavailable at export time.",
            )

        payload: Dict[str, Any] = {
            "anchor": "GUMAS-ENGINE-ADVANCED-SYNTH",
            "version": "4.0.0-synth",
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "turn": state.turn,
            "base_state": state.to_dict(include_history=include_base_history),
            "v3_state": self._v3_state.to_dict() if self._v3_state else {},
            "l2_state": l2_state.to_dict(),
        }

        if self._advanced_history:
            latest = self._advanced_history[-1]
            payload["latest_metrics"] = {
                "stability_index": latest.stability_index,
                "risk_index": latest.risk_index,
                "system_components": dict(latest.system_components),
                "summary": latest.summary,
            }

        if include_advanced_history:
            payload["advanced_history"] = [item.to_dict() for item in self._advanced_history]

        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)

        if include_event_ledger:
            resolved_ledger_path = (
                Path(event_ledger_path).resolve()
                if event_ledger_path
                else output.with_name("advanced_event_ledger.ndjson").resolve()
            )
            self._write_event_ledger(resolved_ledger_path)
            payload["event_ledger"] = {
                "schema_version": "event-ledger-v1",
                "record_count": len(self._event_ledger_records),
                "path": str(resolved_ledger_path),
            }

        self._atomic_write_json(output, payload)

    # ------------------------------------------------------------------ #
    # Internal: initialization and phase wiring
    # ------------------------------------------------------------------ #

    def _init_v3_subsystems(self) -> None:
        state = self.get_state()
        faction_ids = list(state.factions.keys())

        faction_types: Dict[str, str] = {}
        for fid, faction in state.factions.items():
            ftype = faction.faction_type.value.lower().replace(" ", "_")
            faction_types[fid] = ftype

        self._v3_state = init_v3_extension_from_scenario(
            faction_ids=faction_ids,
            faction_types=faction_types,
        )

        for fid_a in faction_ids:
            for fid_b in faction_ids:
                if fid_a == fid_b:
                    continue
                trust = state.factions[fid_a].trust_scores.get(fid_b, 0.0)
                if trust >= 0.68:
                    self._v3_state.intel_networks[fid_a].sharing_partners.add(fid_b)

        self._sync_negotiation_tracks(force_create=True)

        workspace_root = _THIS_DIR.parent.parent
        try:
            self._v3_state.l2_state = build_l2_state_bundle(
                workspace_root=workspace_root,
                base_state=state,
            )
        except Exception as exc:
            logger.warning("Failed to build additive L2 state bundle: %s", exc)
            self._v3_state.l2_state = build_empty_l2_state_bundle(
                workspace_root=workspace_root,
                faction_ids=faction_ids,
                warning=f"Failed to build L2 state bundle: {exc}",
            )

    def _build_faction_conflict_index(self) -> Dict[str, List[str]]:
        index: Dict[str, List[str]] = {}
        for cid, conflict in self.get_state().conflicts.items():
            if conflict.phase not in self._ACTIVE_CONFLICT_PHASES:
                continue
            for fid in conflict.parties:
                index.setdefault(fid, []).append(cid)
        return index

    def _sync_negotiation_tracks(self, force_create: bool = False) -> None:
        if self._v3_state is None:
            return

        existing = {
            (
                n.linked_conflict_id,
                tuple(sorted((n.party_a, n.party_b))),
            )
            for n in self._v3_state.negotiations
            if n.linked_conflict_id
        }

        for conflict in self.get_state().conflicts.values():
            if len(conflict.parties) < 2:
                continue
            if not force_create and conflict.phase not in self._ACTIVE_CONFLICT_PHASES:
                continue

            for pair in self._iter_pairs(conflict.parties):
                key = (conflict.conflict_id, tuple(sorted(pair)))
                if key in existing:
                    continue

                trust = self.get_state().factions[pair[0]].trust_scores.get(pair[1], 0.5)
                phase = self._map_conflict_phase_to_negotiation_phase(conflict.phase)
                neg = NegotiationState(
                    negotiation_id=f"NEG_{conflict.conflict_id}_{pair[0]}_{pair[1]}",
                    party_a=pair[0],
                    party_b=pair[1],
                    mediator_id=conflict.mediator_id,
                    phase=phase,
                    reservation_a=max(0.2, 0.45 - trust * 0.15),
                    reservation_b=max(0.2, 0.45 - trust * 0.15),
                    linked_conflict_id=conflict.conflict_id,
                )
                self._v3_state.negotiations.append(neg)
                existing.add(key)

    def _issue_ultimatums(self) -> List[Dict[str, Any]]:
        if self._v3_state is None:
            return []

        pending_pairs = {
            tuple(sorted((u.issuer_faction_id, u.target_faction_id)))
            for u in self._v3_state.ultimatums
            if u.outcome.value == "pending"
        }

        events: List[Dict[str, Any]] = []
        for conflict in self.get_state().conflicts.values():
            if conflict.phase not in {ConflictPhase.ESCALATION, ConflictPhase.OPEN_CONFLICT}:
                continue
            for a, b in self._iter_pairs(conflict.parties):
                pair = tuple(sorted((a, b)))
                if pair in pending_pairs:
                    continue

                trust_ab = self.get_state().factions[a].trust_scores.get(b, 0.5)
                trust_ba = self.get_state().factions[b].trust_scores.get(a, 0.5)
                low_trust = min(trust_ab, trust_ba)
                if low_trust > 0.22:
                    continue
                if self._rng.random() >= 0.10:
                    continue

                issuer = a if trust_ab <= trust_ba else b
                target = b if issuer == a else a
                self._ultimatum_counter += 1
                ult = Ultimatum(
                    ultimatum_id=f"ULT_{self.get_state().turn}_{self._ultimatum_counter:03d}",
                    issuer_faction_id=issuer,
                    target_faction_id=target,
                    demand="Withdraw forces from contested frontier",
                    threat="Escalated military operation",
                    deadline_turns=3,
                    resolve_strength=0.65 + self._rng.random() * 0.25,
                )
                self._v3_state.ultimatums.append(ult)
                pending_pairs.add(pair)
                events.append(
                    {
                        "type": "ULTIMATUM_ISSUED",
                        "ultimatum_id": ult.ultimatum_id,
                        "issuer": issuer,
                        "target": target,
                        "linked_conflict_id": conflict.conflict_id,
                        "resolve_strength": round(ult.resolve_strength, 3),
                    }
                )

        return events

    # ------------------------------------------------------------------ #
    # Internal: event recording and base-state bridging
    # ------------------------------------------------------------------ #

    def _record_v3_events(
        self,
        events: Iterable[Dict[str, Any]],
        v3_result: TickResultV3,
        base_result: TickResult,
        turn: int,
        *,
        phase: str,
        phase_ordinals: Dict[str, int],
    ) -> None:
        for event in events:
            normalized = dict(event)
            normalized.setdefault("turn", turn)
            normalized.setdefault("phase", phase)
            ordinal = phase_ordinals.get(phase, 0) + 1
            phase_ordinals[phase] = ordinal

            payload_hash = self._stable_payload_hash(normalized)
            event_id = self._build_v3_event_id(turn, phase, ordinal, payload_hash)
            existing_event_id = normalized.get("event_id")
            if existing_event_id and existing_event_id != event_id:
                normalized["source_event_id"] = existing_event_id

            normalized["event_id"] = event_id
            normalized["event_ordinal"] = ordinal
            normalized["payload_hash"] = payload_hash
            v3_result.v3_events.append(normalized)
            self._event_ledger_records.append(
                self._build_event_atom(
                    normalized_event=normalized,
                    turn=turn,
                    phase=phase,
                    ordinal=ordinal,
                    payload_hash=payload_hash,
                )
            )

            etype = normalized.get("type", "UNKNOWN")
            if etype == "POPULATION_MIGRATION":
                v3_result.migrations += 1
            elif etype == "TECH_BREAKTHROUGH_ADVANCED":
                v3_result.tech_breakthroughs += 1
            elif etype in {"DIPLOMATIC_AGREEMENT", "BACK_CHANNEL_DEAL"}:
                v3_result.negotiations_concluded += 1
            elif etype in {"INTELLIGENCE_SHARING", "INTELLIGENCE_COMPROMISE"}:
                v3_result.intelligence_ops += 1
            elif etype == "REBELLION_ONSET":
                v3_result.new_insurgencies += 1
            elif etype == "CIVIL_WAR_ONSET":
                v3_result.civil_wars_started += 1
            elif etype == "STATE_FRAGMENTATION":
                v3_result.fragmentation_events += 1

            base_result.state_changes.append(
                {
                    "type": "v3_event",
                    "event_type": etype,
                    "payload": normalized,
                }
            )
            self._apply_v3_event_to_base(normalized, base_result)

    def _apply_v3_event_to_base(self, event: Dict[str, Any], result: TickResult) -> None:
        state = self.get_state()
        etype = event.get("type")

        if etype == "POPULATION_MIGRATION":
            src = state.factions.get(event.get("origin", ""))
            dst = state.factions.get(event.get("destination", ""))
            mag = float(event.get("magnitude", 0.0))
            if src:
                src.population_stability = self._clamp(src.population_stability - mag * 0.03)
            if dst:
                dst.population_stability = self._clamp(dst.population_stability - mag * 0.02)
                dst.economic_strength = min(
                    dst.economic_potential,
                    dst.economic_strength + mag * 0.01,
                )

        elif etype == "REFUGEE_CRISIS":
            fid = event.get("faction_id")
            faction = state.factions.get(fid or "")
            if faction:
                faction.population_stability = self._clamp(faction.population_stability - 0.05)
                faction.economic_strength = max(0.05, faction.economic_strength - 0.02)
                leader = self._get_faction_leader(fid)
                if leader:
                    leader.public_legitimacy = self._clamp(leader.public_legitimacy - 0.03)

        elif etype == "TECH_BREAKTHROUGH_ADVANCED":
            fid = event.get("faction_id")
            faction = state.factions.get(fid or "")
            if faction:
                faction.technology_level = self._clamp(faction.technology_level + 0.03)
                faction.military_strength = self._clamp(faction.military_strength + 0.005)

        elif etype == "TECH_DIFFUSION":
            dst = state.factions.get(event.get("destination_faction", ""))
            amount = float(event.get("amount", 0.0))
            if dst:
                dst.technology_level = self._clamp(dst.technology_level + amount * 0.20)

        elif etype == "TECH_NODE_UNLOCKED":
            fid = event.get("faction_id")
            faction = state.factions.get(fid or "")
            if faction:
                faction.military_strength = self._clamp(faction.military_strength + 0.003)
                faction.economic_strength = min(
                    faction.economic_potential,
                    faction.economic_strength + 0.004,
                )

        elif etype in {"DIPLOMATIC_AGREEMENT", "BACK_CHANNEL_DEAL"}:
            party_a = event.get("party_a", "")
            party_b = event.get("party_b", "")
            trust_boost = float(event.get("trust_boost", 0.03))
            if party_a and party_b:
                self._adjust_trust(party_a, party_b, trust_boost, result)
                self._ensure_bilateral_treaty(party_a, party_b)

        elif etype == "DIPLOMATIC_CRISIS":
            party_a = event.get("party_a", "")
            party_b = event.get("party_b", "")
            if party_a and party_b:
                self._adjust_trust(party_a, party_b, -0.05, result)

        elif etype == "ULTIMATUM_RESOLVED":
            outcome = event.get("outcome")
            issuer = event.get("issuer")
            target = event.get("target")
            if outcome == "defied" and issuer and target:
                escalation = SimulationEvent(
                    event_id=f"ultimatum_escalation_{issuer}_{target}_{state.turn}",
                    event_type=EventType.MILITARY_ESCALATION,
                    turn=state.turn,
                    source_faction=issuer,
                    target_faction=target,
                    severity=0.5,
                    description="Ultimatum defied; conflict escalation triggered.",
                )
                self._apply_event(escalation, result)
                result.events_generated.append(escalation)

        elif etype == "INTELLIGENCE_COMPROMISE":
            defending = event.get("defending_faction")
            leader = self._get_faction_leader(defending or "")
            if leader:
                leader.betrayals += 1
                leader.public_legitimacy = self._clamp(leader.public_legitimacy - 0.01)

        elif etype == "INTELLIGENCE_SHARING":
            sender = event.get("sender", "")
            receiver = event.get("receiver", "")
            if sender and receiver:
                self._adjust_trust(sender, receiver, 0.01, result)

        elif etype == "SURVEILLANCE_EXPANSION":
            fid = event.get("faction_id")
            leader = self._get_faction_leader(fid or "")
            penalty = float(event.get("legitimacy_penalty", -0.01))
            if leader:
                leader.public_legitimacy = self._clamp(leader.public_legitimacy + penalty)

        elif etype == "REBELLION_ONSET":
            fid = event.get("faction_id")
            faction = state.factions.get(fid or "")
            if faction:
                faction.population_stability = self._clamp(faction.population_stability - 0.06)
                faction.economic_strength = max(0.05, faction.economic_strength - 0.02)

        elif etype == "CIVIL_WAR_ONSET":
            fid = event.get("faction_id")
            faction = state.factions.get(fid or "")
            if faction:
                faction.military_strength = max(0.05, faction.military_strength - 0.04)
                faction.population_stability = self._clamp(faction.population_stability - 0.08)

        elif etype == "STATE_FRAGMENTATION":
            if event.get("picard_delta_3_required") and not self._check_ethics(
                "STATE_FRAGMENTATION", event
            ):
                result.ethics_flags.append(
                    {
                        "type": "STATE_FRAGMENTATION_BLOCKED",
                        "payload": dict(event),
                    }
                )
                return

            fid = event.get("faction_id")
            split = float(event.get("territory_split", 0.1))
            faction = state.factions.get(fid or "")
            if faction:
                faction.military_strength = max(0.05, faction.military_strength * (1.0 - split * 0.6))
                faction.economic_strength = max(0.05, faction.economic_strength * (1.0 - split * 0.7))
                faction.population_stability = self._clamp(
                    faction.population_stability * (1.0 - split * 0.5)
                )

        elif etype == "SEPARATIST_DECLARATION":
            fid = event.get("faction_id")
            faction = state.factions.get(fid or "")
            if faction:
                for other in list(faction.trust_scores.keys()):
                    faction.trust_scores[other] = max(0.0, faction.trust_scores[other] - 0.01)

        elif etype == "MASS_CONSCRIPTION":
            fid = event.get("faction_id")
            faction = state.factions.get(fid or "")
            if faction:
                faction.military_strength = self._clamp(faction.military_strength + 0.03)
                faction.economic_strength = max(0.05, faction.economic_strength - 0.03)
                faction.population_stability = self._clamp(faction.population_stability - 0.03)

    def _ensure_bilateral_treaty(self, faction_a: str, faction_b: str) -> None:
        state = self.get_state()
        parties = {faction_a, faction_b}
        for treaty in state.treaties.values():
            if treaty.is_active and set(treaty.parties) == parties:
                return

        treaty_id = f"treaty_{faction_a}_{faction_b}_{state.turn}"
        state.treaties[treaty_id] = TreatyState(
            treaty_id=treaty_id,
            parties=[faction_a, faction_b],
            phase=TreatyPhase.RATIFICATION,
            enforcement_level=0.65,
            violation_threshold=0.6,
            ambiguity_tolerance=0.2,
            is_active=True,
            terms={
                "source": "advanced_negotiation_track",
                "turn": state.turn,
            },
        )

    # ------------------------------------------------------------------ #
    # Internal: feedback + cleanup + metrics
    # ------------------------------------------------------------------ #

    def _apply_v3_feedback(self, base_result: TickResult) -> None:
        if self._v3_state is None:
            return

        state = self.get_state()
        for fid, faction in state.factions.items():
            tech_cmult = self._v3_state.tech_combat_multipliers.get(fid, 1.0)
            if tech_cmult > 1.0:
                target = min(1.0, faction.military_strength * tech_cmult)
                faction.military_strength += (target - faction.military_strength) * 0.05

            tech_emult = self._v3_state.tech_economic_multipliers.get(fid, 1.0)
            if tech_emult > 1.0:
                faction.economic_potential = min(1.0, faction.economic_potential * tech_emult)

            tech_state = self._v3_state.technology.get(fid)
            if tech_state:
                civtech = calc_civilian_tech_multiplier(
                    energy_level=tech_state.get_level(TechCategory.ENERGY),
                    materials_level=tech_state.get_level(TechCategory.MATERIALS),
                    computing_level=tech_state.get_level(TechCategory.COMPUTING),
                )
                faction.economic_strength = min(
                    faction.economic_potential,
                    faction.economic_strength * (1.0 + (civtech - 1.0) * 0.03),
                )
                faction.technology_level = self._clamp(
                    faction.technology_level + (sum(tech_state.tech_levels.values()) / 40.0)
                )

            if fid in self._v3_state.population:
                pop = self._v3_state.population[fid]
                cap = calc_conscription_capacity(
                    pop.population_index,
                    pop.military_age_fraction,
                    pop.current_mobilization,
                    demographic_stress_penalty=pop.demographic_stress,
                )
                self._v3_state.conscription_capacity[fid] = cap

            active_ins = [
                ins
                for ins in self._v3_state.insurgencies
                if ins.host_faction_id == fid
                and ins.phase in {
                    InsurgencyPhase.ACTIVE,
                    InsurgencyPhase.ESCALATED,
                    InsurgencyPhase.CIVIL_WAR,
                }
            ]
            for ins in active_ins:
                drag = ins.territory_controlled * 0.08
                faction.military_strength = max(0.05, faction.military_strength - drag * 0.5)
                faction.economic_strength = max(0.05, faction.economic_strength - drag * 0.7)
                faction.population_stability = max(
                    0.05,
                    faction.population_stability - drag * 0.4,
                )

            base_result.state_changes.append(
                {
                    "type": "v3_feedback",
                    "faction": fid,
                    "economic_strength": round(faction.economic_strength, 4),
                    "military_strength": round(faction.military_strength, 4),
                    "economic_potential": round(faction.economic_potential, 4),
                    "technology_level": round(faction.technology_level, 4),
                }
            )

    def _compact_v3_state(self) -> None:
        if self._v3_state is None:
            return

        self._v3_state.negotiations = [
            n
            for n in self._v3_state.negotiations
            if n.phase not in {NegotiationPhase.AGREED, NegotiationPhase.BREAKDOWN}
            or n.turns_active < 3
        ]

        self._v3_state.ultimatums = [
            u
            for u in self._v3_state.ultimatums
            if not (u.outcome.value != "pending" and u.turns_elapsed > 2)
        ]

        self._v3_state.insurgencies = [
            i
            for i in self._v3_state.insurgencies
            if i.phase != InsurgencyPhase.RESOLVED
        ]

    def _assemble_advanced_result(
        self,
        base_result: TickResult,
        v3_result: TickResultV3,
    ) -> AdvancedTickResult:
        stability, risk, components = self._compute_system_indices()
        summary = (
            f"Turn {base_result.turn}: stability={stability:.3f}, risk={risk:.3f}, "
            f"v3_events={len(v3_result.v3_events)}"
        )
        return AdvancedTickResult(
            turn=base_result.turn,
            base_result=base_result,
            v3_result=v3_result,
            stability_index=stability,
            risk_index=risk,
            system_components=components,
            summary=summary,
        )

    def _compute_system_indices(self) -> Tuple[float, float, Dict[str, Any]]:
        state = self.get_state()

        factions = list(state.factions.values())
        leaders = list(state.leaders.values())

        avg_pop_stability = self._mean([f.population_stability for f in factions], default=0.5)
        avg_legitimacy = self._mean([l.public_legitimacy for l in leaders], default=0.5)

        trust_values: List[float] = []
        for faction in factions:
            trust_values.extend(faction.trust_scores.values())
        avg_trust = self._mean(trust_values, default=0.5)

        active_conflicts = sum(
            1
            for c in state.conflicts.values()
            if c.phase in self._ACTIVE_CONFLICT_PHASES
        )

        active_insurgencies = 0
        if self._v3_state is not None:
            active_insurgencies = sum(
                1
                for i in self._v3_state.insurgencies
                if i.phase
                in {
                    InsurgencyPhase.ORGANIZING,
                    InsurgencyPhase.ACTIVE,
                    InsurgencyPhase.ESCALATED,
                    InsurgencyPhase.CIVIL_WAR,
                }
            )

        conflict_pressure = min(1.0, active_conflicts / 8.0)
        insurgency_pressure = min(1.0, active_insurgencies / 6.0)

        stability = self._clamp(
            0.35 * avg_pop_stability
            + 0.30 * avg_legitimacy
            + 0.25 * avg_trust
            + 0.10 * (1.0 - conflict_pressure)
        )

        risk = self._clamp(
            0.35 * (1.0 - avg_pop_stability)
            + 0.25 * (1.0 - avg_legitimacy)
            + 0.20 * (1.0 - avg_trust)
            + 0.10 * conflict_pressure
            + 0.10 * insurgency_pressure
        )

        components: Dict[str, Any] = {
            "avg_population_stability": avg_pop_stability,
            "avg_leader_legitimacy": avg_legitimacy,
            "avg_trust": avg_trust,
            "active_conflict_count": active_conflicts,
            "active_insurgency_count": active_insurgencies,
            "conflict_pressure": conflict_pressure,
            "insurgency_pressure": insurgency_pressure,
            "stability_contrib_population": 0.35 * avg_pop_stability,
            "stability_contrib_legitimacy": 0.30 * avg_legitimacy,
            "stability_contrib_trust": 0.25 * avg_trust,
            "stability_contrib_conflict_relief": 0.10 * (1.0 - conflict_pressure),
            "risk_contrib_population": 0.35 * (1.0 - avg_pop_stability),
            "risk_contrib_legitimacy": 0.25 * (1.0 - avg_legitimacy),
            "risk_contrib_trust": 0.20 * (1.0 - avg_trust),
            "risk_contrib_conflict": 0.10 * conflict_pressure,
            "risk_contrib_insurgency": 0.10 * insurgency_pressure,
        }
        return stability, risk, components

    # ------------------------------------------------------------------ #
    # Internal: deterministic ID and utility helpers
    # ------------------------------------------------------------------ #

    def _build_event_atom(
        self,
        *,
        normalized_event: Dict[str, Any],
        turn: int,
        phase: str,
        ordinal: int,
        payload_hash: str,
    ) -> Dict[str, Any]:
        state = self.get_state()
        etype = normalized_event.get("type", "UNKNOWN")
        return {
            "type": "event_atom",
            "schema_version": "event-ledger-v1",
            "engine_version": "4.0.0-synth",
            "seed": state.seed,
            "scenario_id": state.scenario_id,
            "event_id": normalized_event.get("event_id"),
            "turn": turn,
            "phase": phase,
            "ordinal": ordinal,
            "event_type": etype,
            "faction_ids": self._extract_faction_ids(normalized_event),
            "payload_hash": payload_hash,
            "payload": normalized_event,
        }

    def _write_event_ledger(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=str(path.parent),
            text=True,
        )
        tmp_path = Path(tmp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                for record in self._event_ledger_records:
                    f.write(
                        json.dumps(
                            record,
                            sort_keys=True,
                            separators=(",", ":"),
                            ensure_ascii=True,
                            default=str,
                        )
                    )
                    f.write("\n")
            os.replace(str(tmp_path), str(path))
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    @staticmethod
    def _atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=str(path.parent),
            text=True,
        )
        tmp_path = Path(tmp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, default=str)
            os.replace(str(tmp_path), str(path))
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    @staticmethod
    def _sanitize_phase(phase: str) -> str:
        clean = "".join(ch.lower() if ch.isalnum() else "_" for ch in phase.strip())
        clean = "_".join(part for part in clean.split("_") if part)
        return clean or "unknown"

    @staticmethod
    def _canonicalize_value(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                str(k): GUMASAdvancedEngine._canonicalize_value(v)
                for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))
            }
        if isinstance(value, (list, tuple)):
            return [GUMASAdvancedEngine._canonicalize_value(v) for v in value]
        if isinstance(value, set):
            canon = [GUMASAdvancedEngine._canonicalize_value(v) for v in value]
            return sorted(canon, key=lambda item: json.dumps(item, sort_keys=True, default=str))
        if hasattr(value, "value"):
            try:
                return value.value  # Enum-like objects
            except Exception:
                return str(value)
        return value

    def _stable_payload_hash(self, payload: Dict[str, Any]) -> str:
        canonical_payload = self._canonicalize_value(payload)
        digest = hashlib.sha256(
            json.dumps(
                canonical_payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                default=str,
            ).encode("utf-8")
        ).hexdigest()
        return f"sha256:{digest}"

    def _build_v3_event_id(
        self,
        turn: int,
        phase: str,
        ordinal: int,
        payload_hash: str,
    ) -> str:
        clean_phase = self._sanitize_phase(phase)
        hash_suffix = payload_hash.replace("sha256:", "")[:10]
        return f"EVT_{turn:04d}_{clean_phase}_{ordinal:03d}_{hash_suffix}"

    def _extract_faction_ids(self, event: Dict[str, Any]) -> List[str]:
        keys = (
            "faction_id",
            "source_faction",
            "target_faction",
            "origin",
            "destination",
            "issuer",
            "target",
            "party_a",
            "party_b",
            "sender",
            "receiver",
            "defending_faction",
            "destination_faction",
            "host_faction_id",
        )
        seen = set()
        ordered: List[str] = []
        for key in keys:
            value = event.get(key)
            if isinstance(value, str) and value and value not in seen:
                ordered.append(value)
                seen.add(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and item and item not in seen:
                        ordered.append(item)
                        seen.add(item)
        return ordered

    def _canonicalize_insurgency_ids(self) -> Dict[str, str]:
        if self._v3_state is None:
            return {}

        mapping: Dict[str, str] = {}
        for idx, insurgency in enumerate(self._v3_state.insurgencies):
            old_id = insurgency.insurgency_id
            new_id = f"INS_{insurgency.host_faction_id}_{idx:03d}"
            if old_id != new_id:
                mapping[old_id] = new_id
                insurgency.insurgency_id = new_id
        return mapping

    @staticmethod
    def _map_conflict_phase_to_negotiation_phase(conflict_phase: ConflictPhase) -> NegotiationPhase:
        if conflict_phase in {ConflictPhase.OPEN_CONFLICT, ConflictPhase.STALEMATE}:
            return NegotiationPhase.POSITIONAL
        if conflict_phase in {ConflictPhase.ESCALATION, ConflictPhase.TENSION}:
            return NegotiationPhase.EXPLORATORY
        return NegotiationPhase.INTEGRATIVE

    @staticmethod
    def _iter_pairs(items: List[str]) -> Iterable[Tuple[str, str]]:
        for i, a in enumerate(items):
            for b in items[i + 1 :]:
                yield a, b

    @staticmethod
    def _mean(values: List[float], default: float) -> float:
        if not values:
            return default
        return sum(values) / len(values)

    @staticmethod
    def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
        return max(lo, min(hi, value))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    engine = GUMASAdvancedEngine(seed=42)
    state = engine.init_scenario()
    print(
        f"Initialized advanced engine | factions={len(state.factions)} "
        f"leaders={len(state.leaders)} conflicts={len(state.conflicts)}"
    )
    results = engine.run(5)
    for res in results:
        print(res.summary)

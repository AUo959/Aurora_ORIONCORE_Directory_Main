#!/usr/bin/env python3
"""
GUMAS L2 Simulation Data Models
================================
Anchor: GUMAS-ENGINE-MODELS-V1
Seed: EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP: L2_ENGINE_CORE
Version: 1.0.0

Data models for the L2 GUMAS multi-agent galactic simulation.
All schemas derived from the Runtime Reference Packet v0.4 and
PR_L2_GUMAS_ARCHITECTURAL_ENHANCEMENTS.

Conventions:
- Probabilities and trust scores: [0.0, 1.0]
- Cost indices: [0.0, +inf)
- Signed shocks: (-inf, +inf)
- Update cadence: turn-based (per engine tick)
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================================
# ENUMS
# ============================================================================

class CertaintyTag(Enum):
    """Data provenance tags per Runtime Reference Packet."""
    CANON = "CANON"
    STAGING = "STAGING"
    UNCONFIRMED = "UNCONFIRMED"
    LEGEND_CONTESTED = "LEGEND_CONTESTED"
    APPROX = "APPROX"


class BiasType(Enum):
    """Leader cognitive bias types (Section 1.1 of Runtime Reference Packet)."""
    STATUS_QUO = "status_quo_bias"
    SURVIVORSHIP = "survivorship_bias"
    CONFIRMATION = "confirmation_bias"
    SUNK_COST = "sunk_cost_fallacy"
    HYPER_RATIONALISM = "hyper_rationalism_bias"
    FEAR_BASED = "fear_based_decision_making"
    MORAL_LICENSING = "moral_self_licensing"
    ZERO_SUM = "zero_sum_thinking"


class FactionType(Enum):
    """Polity governance types from entity registry."""
    FEDERATION = "federation"
    AUTHORITARIAN = "authoritarian imperial bloc"
    CORPORATE_OLIGARCHY = "corporate oligarchy"
    CULTURAL_SPIRITUAL = "cultural-spiritual polity"
    CLAN_CONFEDERATION = "clan confederation"
    MONASTIC_NETWORK = "monastic network"
    NOMADIC_DIASPORA = "nomadic diaspora"
    SOVEREIGN_AI = "sovereign AI entity"
    ROGUE_SYNTHETIC = "rogue synthetic coalition"
    BREAKAWAY_BLOC = "breakaway bloc"
    PMC = "private military conglomerate"
    MILITANT_SPIRITUAL = "militant spiritual order"
    FRONTIER_CONFEDERATION = "frontier confederation"


class ConflictPhase(Enum):
    """Conflict lifecycle phases."""
    PEACE = "peace"
    TENSION = "tension"
    ESCALATION = "escalation"
    OPEN_CONFLICT = "open_conflict"
    STALEMATE = "stalemate"
    DEESCALATION = "deescalation"
    CEASEFIRE = "ceasefire"
    NEGOTIATION = "negotiation"
    RESOLUTION = "resolution"


class TreatyPhase(Enum):
    """Treaty negotiation phases (Section 1.4)."""
    NONE = "none"
    CEASEFIRE_TALKS = "ceasefire_talks"
    BARGAINING = "bargaining"
    INTERNAL_PRESSURE = "internal_pressure"
    RATIFICATION = "ratification"
    MONITORING = "monitoring"
    VIOLATED = "violated"
    COLLAPSED = "collapsed"


class EventType(Enum):
    """Injected event types for the simulation."""
    MILITARY_ESCALATION = "military_escalation"
    DIPLOMATIC_OVERTURE = "diplomatic_overture"
    ESPIONAGE_EXPOSURE = "espionage_exposure"
    ECONOMIC_SHOCK = "economic_shock"
    LEADER_CHANGE = "leader_change"
    TREATY_PROPOSAL = "treaty_proposal"
    TREATY_VIOLATION = "treaty_violation"
    INTELLIGENCE_LEAK = "intelligence_leak"
    HUMANITARIAN_CRISIS = "humanitarian_crisis"
    TECHNOLOGY_BREAKTHROUGH = "technology_breakthrough"
    CULTURAL_MOVEMENT = "cultural_movement"
    INTERNAL_COUP = "internal_coup"
    MEDIATION_OFFER = "mediation_offer"
    TRADE_AGREEMENT = "trade_agreement"
    ECONOMIC_BOOM = "economic_boom"
    INFRASTRUCTURE_INVESTMENT = "infrastructure_investment"
    CUSTOM = "custom"


# ============================================================================
# LEADER STATE
# ============================================================================

@dataclass
class LeaderState:
    """
    Leader with cognitive bias system (Section 1.1).

    Bias hooks (engine-facing):
    - evidence_gain_multiplier (per evidence type)
    - risk_tolerance (0-1)
    - diplomacy_openness (0-1)
    - escalation_threshold (0-1)
    - oversight_resistance (0-1)
    """
    leader_id: str
    name: str
    role: str
    faction_id: str
    dominant_bias: BiasType
    secondary_biases: List[BiasType] = field(default_factory=list)
    bias_intensity: float = 0.5
    plasticity: float = 0.3

    # Bias effect hooks
    evidence_gain_multiplier: float = 1.0
    risk_tolerance: float = 0.5
    diplomacy_openness: float = 0.5
    escalation_threshold: float = 0.5
    oversight_resistance: float = 0.3

    # Internal state
    public_legitimacy: float = 0.7
    elite_support: float = 0.6
    institutional_control: float = 0.5
    war_pressure: float = 0.0

    # Stressors (cumulative)
    war_losses: int = 0
    betrayals: int = 0
    scandals: int = 0
    economic_shock: float = 0.0

    certainty: CertaintyTag = CertaintyTag.STAGING

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["dominant_bias"] = self.dominant_bias.value
        d["secondary_biases"] = [b.value for b in self.secondary_biases]
        d["certainty"] = self.certainty.value
        return d


# ============================================================================
# FACTION STATE
# ============================================================================

@dataclass
class FactionState:
    """
    Polity state from entity registry (Section 3.1).
    Includes diplomacy memory (Section 1.5) via trust_scores.
    """
    faction_id: str
    name: str
    faction_type: FactionType
    notes: str = ""

    # Current leader (leader_id reference)
    leader_id: Optional[str] = None

    # Economic/military indicators
    military_strength: float = 0.5
    economic_strength: float = 0.5
    technology_level: float = 0.5
    population_stability: float = 0.7

    # Diplomacy memory (Section 1.5): trust[other_faction_id] -> score
    trust_scores: Dict[str, float] = field(default_factory=dict)

    # Reputation (affected by treaty breaches)
    reputation: float = 0.7

    # Derived fields (Section 1.5)
    verification_demand: float = 0.5
    deal_discount: float = 0.0
    coalition_invite_weight: float = 0.5

    # Structural ceiling: not every polity can reach max economy.
    # Governed by type, resources, governance model.
    economic_potential: float = 0.7

    certainty: CertaintyTag = CertaintyTag.STAGING

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["faction_type"] = self.faction_type.value
        d["certainty"] = self.certainty.value
        return d


# ============================================================================
# CONFLICT STATE
# ============================================================================

@dataclass
class ConflictState:
    """
    Conflict instance between parties (Section 1.2).
    """
    conflict_id: str
    parties: List[str]  # faction_ids
    phase: ConflictPhase = ConflictPhase.TENSION

    # De-escalation inputs (Section 1.2)
    war_cost_estimate: Dict[str, float] = field(default_factory=dict)
    stalemate_index: float = 0.0
    internal_pressure: Dict[str, float] = field(default_factory=dict)
    mediation_available: bool = False
    mediator_id: Optional[str] = None

    # De-escalation output
    deescalation_probability: float = 0.0

    # Eligible compromises
    eligible_compromises: List[str] = field(default_factory=list)

    # History
    turns_active: int = 0
    casualty_index: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["phase"] = self.phase.value
        return d


# ============================================================================
# TREATY STATE
# ============================================================================

@dataclass
class TreatyState:
    """
    Treaty instance (Section 1.4).
    """
    treaty_id: str
    parties: List[str]  # faction_ids
    phase: TreatyPhase = TreatyPhase.NONE

    # Treaty parameters (PR Section 5.1)
    enforcement_level: float = 0.5
    violation_threshold: float = 0.6
    ambiguity_tolerance: float = 0.2

    # Breach tracking per faction
    breach_count: Dict[str, int] = field(default_factory=dict)
    breach_history: List[Dict[str, Any]] = field(default_factory=list)
    reputation_impact: float = -0.1

    # Terms
    terms: Dict[str, Any] = field(default_factory=dict)

    # Monitoring
    turns_since_ratification: int = 0
    is_active: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["phase"] = self.phase.value
        return d


# ============================================================================
# SIMULATION EVENT
# ============================================================================

@dataclass
class SimulationEvent:
    """Event injected into or generated by the simulation."""
    event_id: str
    event_type: EventType
    turn: int
    source_faction: Optional[str] = None
    target_faction: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    severity: float = 0.5
    description: str = ""
    injected: bool = False  # True if externally injected, False if emergent

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["event_type"] = self.event_type.value
        return d


# ============================================================================
# TICK RESULT
# ============================================================================

@dataclass
class TickResult:
    """Result of a single simulation tick."""
    turn: int
    events_processed: List[SimulationEvent] = field(default_factory=list)
    events_generated: List[SimulationEvent] = field(default_factory=list)
    state_changes: List[Dict[str, Any]] = field(default_factory=list)
    ethics_flags: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn": self.turn,
            "events_processed": [e.to_dict() for e in self.events_processed],
            "events_generated": [e.to_dict() for e in self.events_generated],
            "state_changes": self.state_changes,
            "ethics_flags": self.ethics_flags,
            "timestamp": self.timestamp,
        }


# ============================================================================
# GUMAS WORLD STATE (top-level snapshot)
# ============================================================================

@dataclass
class GUMASState:
    """
    Complete simulation state at a given turn.
    This is the top-level object the engine manages.
    """
    scenario_id: str
    turn: int = 0
    seed: int = 42

    factions: Dict[str, FactionState] = field(default_factory=dict)
    leaders: Dict[str, LeaderState] = field(default_factory=dict)
    conflicts: Dict[str, ConflictState] = field(default_factory=dict)
    treaties: Dict[str, TreatyState] = field(default_factory=dict)

    # Event queue (pending injected events)
    event_queue: List[SimulationEvent] = field(default_factory=list)

    # Full history of tick results
    history: List[TickResult] = field(default_factory=list)

    # DLP metadata
    anchor: str = "GUMAS-ENGINE-V1"
    ethics_protocol: str = "Picard_Delta_3"
    version: str = "1.0.0"

    def to_dict(self, include_history: bool = False) -> Dict[str, Any]:
        """Serialize state to dict. History excluded by default for size."""
        result = {
            "scenario_id": self.scenario_id,
            "turn": self.turn,
            "seed": self.seed,
            "factions": {k: v.to_dict() for k, v in self.factions.items()},
            "leaders": {k: v.to_dict() for k, v in self.leaders.items()},
            "conflicts": {k: v.to_dict() for k, v in self.conflicts.items()},
            "treaties": {k: v.to_dict() for k, v in self.treaties.items()},
            "event_queue_depth": len(self.event_queue),
            "history_depth": len(self.history),
            "anchor": self.anchor,
            "ethics_protocol": self.ethics_protocol,
            "version": self.version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if include_history:
            result["history"] = [h.to_dict() for h in self.history]
        return result

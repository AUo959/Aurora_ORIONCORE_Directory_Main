#!/usr/bin/env python3
"""
GUMAS v2.0 Data Models - Galactic Union Multi-Agent Simulation Engine

This module provides comprehensive data models for the GUMAS simulation engine,
maintaining full backward compatibility with v1.0 while adding massive new capabilities
for economic systems, galactic topology, military operations, cultural dynamics,
precursor artifacts, and sentinel operations.

Reference: Runtime Reference Packet v2.0
Anchor: GUMAS-ENGINE-MODELS-V2
Seed: EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP: L2_ENGINE_CORE
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any


# ============================================================================
# BACKWARD COMPATIBILITY: v1.0 ENUMS (PRESERVED)
# ============================================================================

class CertaintyTag(Enum):
    """Epistemic certainty levels for simulation states."""
    CANON = "canon"
    STAGING = "staging"
    UNCONFIRMED = "unconfirmed"
    LEGEND_CONTESTED = "legend_contested"
    APPROX = "approx"
    # v2.0 additions
    CANON_PROMOTE = "canon_promote"
    LOCKED_POSITION = "locked_position"
    PLACED = "placed"


class BiasType(Enum):
    """Cognitive bias types affecting faction decision-making."""
    STATUS_QUO = "status_quo"
    SURVIVORSHIP = "survivorship"
    CONFIRMATION = "confirmation"
    SUNK_COST = "sunk_cost"
    HYPER_RATIONALISM = "hyper_rationalism"
    FEAR_BASED = "fear_based"
    MORAL_LICENSING = "moral_licensing"
    ZERO_SUM = "zero_sum"


class FactionType(Enum):
    """Types of galactic factions."""
    FEDERATION = "federation"
    AUTHORITARIAN = "authoritarian"
    CORPORATE_OLIGARCHY = "corporate_oligarchy"
    CULTURAL_SPIRITUAL = "cultural_spiritual"
    CLAN_CONFEDERATION = "clan_confederation"
    MONASTIC_NETWORK = "monastic_network"
    NOMADIC_DIASPORA = "nomadic_diaspora"
    SOVEREIGN_AI = "sovereign_ai"
    ROGUE_SYNTHETIC = "rogue_synthetic"
    BREAKAWAY_BLOC = "breakaway_bloc"
    PMC = "pmc"
    MILITANT_SPIRITUAL = "militant_spiritual"
    FRONTIER_CONFEDERATION = "frontier_confederation"


class ConflictPhase(Enum):
    """Phases of conflict escalation."""
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
    """Phases of treaty negotiation and implementation."""
    NONE = "none"
    CEASEFIRE_TALKS = "ceasefire_talks"
    BARGAINING = "bargaining"
    INTERNAL_PRESSURE = "internal_pressure"
    RATIFICATION = "ratification"
    MONITORING = "monitoring"
    VIOLATED = "violated"
    COLLAPSED = "collapsed"


class EventType(Enum):
    """Types of simulation events that drive narrative."""
    # v1.0 original 17 types
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
    # v2.0 additions
    FLEET_MOVEMENT = "fleet_movement"
    FLEET_BATTLE = "fleet_battle"
    PRECURSOR_DISCOVERY = "precursor_discovery"
    PRECURSOR_ACTIVATION = "precursor_activation"
    SENTINEL_MISSION = "sentinel_mission"
    CORPORATE_TAKEOVER = "corporate_takeover"
    MEDIA_CAMPAIGN = "media_campaign"
    DOCTRINE_SHIFT = "doctrine_shift"
    CULTURE_SPREAD = "culture_spread"
    RESOURCE_CRISIS = "resource_crisis"
    BLOCKADE = "blockade"
    COUP_ATTEMPT = "coup_attempt"
    ALLIANCE_FORMATION = "alliance_formation"
    ALLIANCE_DISSOLUTION = "alliance_dissolution"
    SANCTIONS_IMPOSED = "sanctions_imposed"
    SANCTIONS_LIFTED = "sanctions_lifted"


# ============================================================================
# v2.0 NEW ENUMS
# ============================================================================

class CoalitionType(Enum):
    """Types of coalitions between factions."""
    ECONOMIC_BLOC = "economic_bloc"
    DEFENSIVE_PACT = "defensive_pact"
    INTELLIGENCE_SHARING = "intelligence_sharing"
    CULTURAL_ALLIANCE = "cultural_alliance"


class ResourceType(Enum):
    """Types of resources traded in galactic economy."""
    ENERGY = "energy"
    MINERALS = "minerals"
    FOOD = "food"
    TECHNOLOGY = "technology"
    RARE_MATERIALS = "rare_materials"
    MILITARY_HARDWARE = "military_hardware"
    LUXURY_GOODS = "luxury_goods"
    INFORMATION = "information"


class LocationType(Enum):
    """Types of locations in galactic topology."""
    SYSTEM = "system"
    PLANET = "planet"
    MOON = "moon"
    STATION = "station"
    ANOMALY = "anomaly"
    REGION = "region"
    ROUTE = "route"
    FACILITY = "facility"
    DOMAIN = "domain"


class HyperlaneType(Enum):
    """Types of hyperspatial travel routes."""
    MAJOR_LANE = "major_lane"
    MINOR_LANE = "minor_lane"
    WORMHOLE = "wormhole"
    JUMP_GATE = "jump_gate"
    DRIFT_CORRIDOR = "drift_corridor"
    SECRET_PASSAGE = "secret_passage"


class BattlefieldCondition(Enum):
    """Environmental conditions affecting combat."""
    OPEN_SPACE = "open_space"
    NEBULA = "nebula"
    ASTEROID_FIELD = "asteroid_field"
    ORBITAL = "orbital"
    FORTIFIED_POSITION = "fortified_position"
    CHOKEPOINT = "chokepoint"
    DEEP_SPACE = "deep_space"


class DiscoveryPhase(Enum):
    """Phases of precursor artifact discovery."""
    DORMANT = "dormant"
    DETECTED = "detected"
    INVESTIGATED = "investigated"
    PARTIALLY_ACTIVATED = "partially_activated"
    FULLY_ACTIVATED = "fully_activated"
    WEAPONIZED = "weaponized"
    CONTAINED = "contained"


class PrecursorOrigin(Enum):
    """Origins of precursor artifacts."""
    ORAK_THUUN = "orak_thuun"
    SYTHREX_CONCLAVE = "sythrex_conclave"
    VORTHAN_IMPERIUM = "vorthan_imperium"
    SHROUDBORN = "shroudborn"
    UNKNOWN = "unknown"


class SentinelRank(Enum):
    """Ranks of sentinel operatives."""
    CADET = "cadet"
    OPERATIVE = "operative"
    SPECIALIST = "specialist"
    COMMANDER = "commander"
    ELITE = "elite"


class MissionType(Enum):
    """Types of sentinel missions."""
    RECONNAISSANCE = "reconnaissance"
    SABOTAGE = "sabotage"
    ASSASSINATION = "assassination"
    EXTRACTION = "extraction"
    DIPLOMACY = "diplomacy"
    COUNTERINTEL = "counterintel"
    ARTIFACT_RECOVERY = "artifact_recovery"


class DoctrineType(Enum):
    """Military doctrine types."""
    CONVENTIONAL = "conventional"
    ASYMMETRIC = "asymmetric"
    CYBER = "cyber"
    DEFENSIVE = "defensive"
    EXPANSIONIST = "expansionist"
    GUERRILLA = "guerrilla"
    DETERRENCE = "deterrence"


# ============================================================================
# BACKWARD COMPATIBILITY: v1.0 DATACLASSES (PRESERVED WITH v1.0 SCHEMA)
# ============================================================================

@dataclass
class LeaderState:
    """Represents the state of a faction leader (v1.0 canonical schema)."""
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
        return {
            "leader_id": self.leader_id,
            "name": self.name,
            "role": self.role,
            "faction_id": self.faction_id,
            "dominant_bias": self.dominant_bias.value,
            "secondary_biases": [b.value for b in self.secondary_biases],
            "bias_intensity": self.bias_intensity,
            "plasticity": self.plasticity,
            "evidence_gain_multiplier": self.evidence_gain_multiplier,
            "risk_tolerance": self.risk_tolerance,
            "diplomacy_openness": self.diplomacy_openness,
            "escalation_threshold": self.escalation_threshold,
            "oversight_resistance": self.oversight_resistance,
            "public_legitimacy": self.public_legitimacy,
            "elite_support": self.elite_support,
            "institutional_control": self.institutional_control,
            "war_pressure": self.war_pressure,
            "war_losses": self.war_losses,
            "betrayals": self.betrayals,
            "scandals": self.scandals,
            "economic_shock": self.economic_shock,
            "certainty": self.certainty.value,
        }


@dataclass
class ConflictState:
    """Represents current state of a conflict between factions (v1.0 canonical schema)."""
    conflict_id: str
    parties: List[str]  # faction_ids (v1.0: list of parties)
    phase: ConflictPhase = ConflictPhase.TENSION

    # De-escalation inputs
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
        return {
            "conflict_id": self.conflict_id,
            "parties": self.parties,
            "phase": self.phase.value,
            "war_cost_estimate": self.war_cost_estimate,
            "stalemate_index": self.stalemate_index,
            "internal_pressure": self.internal_pressure,
            "mediation_available": self.mediation_available,
            "mediator_id": self.mediator_id,
            "deescalation_probability": self.deescalation_probability,
            "eligible_compromises": self.eligible_compromises,
            "turns_active": self.turns_active,
            "casualty_index": self.casualty_index,
        }


@dataclass
class TreatyState:
    """Represents negotiation and enforcement state of a treaty (v1.0 canonical schema)."""
    treaty_id: str
    parties: List[str]  # faction_ids
    phase: TreatyPhase = TreatyPhase.NONE

    # Treaty parameters
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
        return {
            "treaty_id": self.treaty_id,
            "parties": self.parties,
            "phase": self.phase.value,
            "enforcement_level": self.enforcement_level,
            "violation_threshold": self.violation_threshold,
            "ambiguity_tolerance": self.ambiguity_tolerance,
            "breach_count": self.breach_count,
            "breach_history": self.breach_history,
            "reputation_impact": self.reputation_impact,
            "terms": self.terms,
            "turns_since_ratification": self.turns_since_ratification,
            "is_active": self.is_active,
        }


@dataclass
class SimulationEvent:
    """Represents a single event in the simulation timeline (v1.0 canonical schema)."""
    event_id: str
    event_type: EventType
    turn: int
    source_faction: Optional[str] = None
    target_faction: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    severity: float = 0.5
    description: str = ""
    injected: bool = False
    cascade_root_id: Optional[str] = None
    parent_event_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "turn": self.turn,
            "source_faction": self.source_faction,
            "target_faction": self.target_faction,
            "parameters": self.parameters,
            "severity": self.severity,
            "description": self.description,
            "injected": self.injected,
            "cascade_root_id": self.cascade_root_id,
            "parent_event_id": self.parent_event_id,
        }


@dataclass
class TickResult:
    """Result of a single simulation tick (v1.0 canonical schema)."""
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
# v2.0 NEW DATACLASSES: COALITIONS
# ============================================================================

@dataclass
class CoalitionState:
    """Represents a coalition between multiple factions."""
    coalition_id: str
    members: List[str]
    coalition_type: CoalitionType
    stability: float
    shared_threat: str
    founding_trust: float
    formation_turn: int
    deterrence_bonus: float = 0.0
    trade_bonus: float = 0.0
    intel_bonus: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "coalition_id": self.coalition_id,
            "members": self.members,
            "coalition_type": self.coalition_type.value,
            "stability": self.stability,
            "shared_threat": self.shared_threat,
            "founding_trust": self.founding_trust,
            "formation_turn": self.formation_turn,
            "deterrence_bonus": self.deterrence_bonus,
            "trade_bonus": self.trade_bonus,
            "intel_bonus": self.intel_bonus,
        }


# ============================================================================
# v2.0 NEW DATACLASSES: ECONOMIC SYSTEM
# ============================================================================

@dataclass
class MarketState:
    """Represents a market for a specific resource type."""
    resource_type: ResourceType
    supply: float
    demand: float
    price: float = 1.0
    trade_volume: float = 0.0
    sanctions: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "resource_type": self.resource_type.value,
            "supply": self.supply,
            "demand": self.demand,
            "price": self.price,
            "trade_volume": self.trade_volume,
            "sanctions": self.sanctions,
        }


@dataclass
class TradeRoute:
    """Represents a trade route between factions or locations."""
    route_id: str
    endpoints: List[str]
    capacity: float
    security: float
    tariff_rate: float
    is_blockaded: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "route_id": self.route_id,
            "endpoints": self.endpoints,
            "capacity": self.capacity,
            "security": self.security,
            "tariff_rate": self.tariff_rate,
            "is_blockaded": self.is_blockaded,
        }


@dataclass
class EconomicState:
    """Represents the economic state of the simulation."""
    markets: Dict[str, MarketState]
    trade_routes: Dict[str, TradeRoute]
    gdp_index: Dict[str, float]
    debt_levels: Dict[str, float]
    corporate_influence: Dict[str, float]
    sanctions_active: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "markets": {k: v.to_dict() for k, v in self.markets.items()},
            "trade_routes": {k: v.to_dict() for k, v in self.trade_routes.items()},
            "gdp_index": self.gdp_index,
            "debt_levels": self.debt_levels,
            "corporate_influence": self.corporate_influence,
            "sanctions_active": self.sanctions_active,
        }


# ============================================================================
# v2.0 NEW DATACLASSES: GALACTIC TOPOLOGY
# ============================================================================

@dataclass
class TopologyNode:
    """Represents a location in galactic space."""
    node_id: str
    name: str
    location_type: LocationType
    owner_faction: Optional[str]
    strategic_value: float
    resources: Dict[str, float]
    population: float
    defense_level: float
    is_chokepoint: bool = False
    certainty: CertaintyTag = CertaintyTag.CANON

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "location_type": self.location_type.value,
            "owner_faction": self.owner_faction,
            "strategic_value": self.strategic_value,
            "resources": self.resources,
            "population": self.population,
            "defense_level": self.defense_level,
            "is_chokepoint": self.is_chokepoint,
            "certainty": self.certainty.value,
        }


@dataclass
class HyperlaneEdge:
    """Represents a travel route between topology nodes."""
    edge_id: str
    from_node: str
    to_node: str
    lane_type: HyperlaneType
    travel_time: float
    capacity: float
    is_contested: bool = False
    control_faction: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "from_node": self.from_node,
            "to_node": self.to_node,
            "lane_type": self.lane_type.value,
            "travel_time": self.travel_time,
            "capacity": self.capacity,
            "is_contested": self.is_contested,
            "control_faction": self.control_faction,
        }


@dataclass
class GalaxyTopology:
    """Represents the galactic topology graph."""
    nodes: Dict[str, TopologyNode]
    edges: Dict[str, HyperlaneEdge]
    adjacency: Dict[str, List[str]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nodes": {k: v.to_dict() for k, v in self.nodes.items()},
            "edges": {k: v.to_dict() for k, v in self.edges.items()},
            "adjacency": self.adjacency,
        }


# ============================================================================
# v2.0 NEW DATACLASSES: MILITARY OPERATIONS
# ============================================================================

@dataclass
class FleetState:
    """Represents a military fleet."""
    fleet_id: str
    faction_id: str
    name: str
    strength: float
    technology_modifier: float
    morale: float
    location_node: str
    movement_target: Optional[str] = None
    movement_eta: int = 0
    supply_level: float = 1.0
    experience: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fleet_id": self.fleet_id,
            "faction_id": self.faction_id,
            "name": self.name,
            "strength": self.strength,
            "technology_modifier": self.technology_modifier,
            "morale": self.morale,
            "location_node": self.location_node,
            "movement_target": self.movement_target,
            "movement_eta": self.movement_eta,
            "supply_level": self.supply_level,
            "experience": self.experience,
        }


@dataclass
class CombatState:
    """Represents active combat between fleets."""
    combat_id: str
    location: str
    attacker_fleets: List[str]
    defender_fleets: List[str]
    condition: BattlefieldCondition
    turns_active: int = 0
    outcome_ratio: float = 1.0
    is_resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "combat_id": self.combat_id,
            "location": self.location,
            "attacker_fleets": self.attacker_fleets,
            "defender_fleets": self.defender_fleets,
            "condition": self.condition.value,
            "turns_active": self.turns_active,
            "outcome_ratio": self.outcome_ratio,
            "is_resolved": self.is_resolved,
        }


# ============================================================================
# v2.0 NEW DATACLASSES: MEDIA AND NARRATIVE
# ============================================================================

@dataclass
class MediaOutlet:
    """Represents a media outlet in the faction."""
    outlet_id: str
    name: str
    faction_alignment: Optional[str]
    credibility: float
    reach: float
    bias_slant: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outlet_id": self.outlet_id,
            "name": self.name,
            "faction_alignment": self.faction_alignment,
            "credibility": self.credibility,
            "reach": self.reach,
            "bias_slant": self.bias_slant,
        }


@dataclass
class NarrativeState:
    """Represents an active narrative/propaganda campaign."""
    narrative_id: str
    source_faction: str
    target_audience: List[str]
    message_type: str
    effectiveness: float
    decay_rate: float = 0.05
    turns_active: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "narrative_id": self.narrative_id,
            "source_faction": self.source_faction,
            "target_audience": self.target_audience,
            "message_type": self.message_type,
            "effectiveness": self.effectiveness,
            "decay_rate": self.decay_rate,
            "turns_active": self.turns_active,
        }


@dataclass
class MediaEcosystem:
    """Represents the media and information landscape."""
    outlets: Dict[str, MediaOutlet]
    active_narratives: List[NarrativeState]
    public_opinion: Dict[str, Dict[str, float]]
    information_freedom: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outlets": {k: v.to_dict() for k, v in self.outlets.items()},
            "active_narratives": [n.to_dict() for n in self.active_narratives],
            "public_opinion": self.public_opinion,
            "information_freedom": self.information_freedom,
        }


# ============================================================================
# v2.0 NEW DATACLASSES: PRECURSOR ARTIFACTS
# ============================================================================

@dataclass
class PrecursorSite:
    """Represents a precursor artifact site."""
    site_id: str
    name: str
    location_node: str
    origin: PrecursorOrigin
    discovery_phase: DiscoveryPhase = DiscoveryPhase.DORMANT
    power_level: float = 0.0
    stability: float = 1.0
    controller_faction: Optional[str] = None
    discoverer_faction: Optional[str] = None
    tech_bonus: float = 0.0
    military_bonus: float = 0.0
    risk_level: float = 0.0
    activation_turn: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "site_id": self.site_id,
            "name": self.name,
            "location_node": self.location_node,
            "origin": self.origin.value,
            "discovery_phase": self.discovery_phase.value,
            "power_level": self.power_level,
            "stability": self.stability,
            "controller_faction": self.controller_faction,
            "discoverer_faction": self.discoverer_faction,
            "tech_bonus": self.tech_bonus,
            "military_bonus": self.military_bonus,
            "risk_level": self.risk_level,
            "activation_turn": self.activation_turn,
        }


# ============================================================================
# v2.0 NEW DATACLASSES: SENTINEL OPERATIVES
# ============================================================================

@dataclass
class SentinelOperative:
    """Represents a sentinel operative."""
    operative_id: str
    name: str
    faction_id: str
    rank: SentinelRank
    combat_skill: float
    stealth_skill: float
    diplomacy_skill: float
    tech_skill: float
    experience: float = 0.0
    missions_completed: int = 0
    missions_failed: int = 0
    is_active: bool = True
    is_double_agent: bool = False
    cover_faction: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operative_id": self.operative_id,
            "name": self.name,
            "faction_id": self.faction_id,
            "rank": self.rank.value,
            "combat_skill": self.combat_skill,
            "stealth_skill": self.stealth_skill,
            "diplomacy_skill": self.diplomacy_skill,
            "tech_skill": self.tech_skill,
            "experience": self.experience,
            "missions_completed": self.missions_completed,
            "missions_failed": self.missions_failed,
            "is_active": self.is_active,
            "is_double_agent": self.is_double_agent,
            "cover_faction": self.cover_faction,
        }


@dataclass
class MissionState:
    """Represents a sentinel mission."""
    mission_id: str
    mission_type: MissionType
    assigned_operative: str
    target_faction: str
    target_location: Optional[str]
    difficulty: float
    success_probability: float = 0.5
    turns_remaining: int = 1
    is_complete: bool = False
    outcome: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "mission_type": self.mission_type.value,
            "assigned_operative": self.assigned_operative,
            "target_faction": self.target_faction,
            "target_location": self.target_location,
            "difficulty": self.difficulty,
            "success_probability": self.success_probability,
            "turns_remaining": self.turns_remaining,
            "is_complete": self.is_complete,
            "outcome": self.outcome,
        }


# ============================================================================
# v2.0 NEW DATACLASSES: DOCTRINE AND LEARNING
# ============================================================================

@dataclass
class DoctrineProfile:
    """Represents a faction's military doctrine and learning state."""
    faction_id: str
    current_doctrine: DoctrineType
    q_table: Dict[str, Dict[str, float]]
    learning_rate: float = 0.1
    discount_factor: float = 0.9
    exploration_rate: float = 0.2
    adaptation_history: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "faction_id": self.faction_id,
            "current_doctrine": self.current_doctrine.value,
            "q_table": self.q_table,
            "learning_rate": self.learning_rate,
            "discount_factor": self.discount_factor,
            "exploration_rate": self.exploration_rate,
            "adaptation_history": self.adaptation_history,
        }


# ============================================================================
# v2.0 NEW DATACLASSES: CULTURAL DYNAMICS
# ============================================================================

@dataclass
class CultureMovement:
    """Represents a cultural or ideological movement."""
    movement_id: str
    name: str
    origin_faction: str
    spread_factions: List[str]
    influence: float
    subversive: bool = False
    affects_legitimacy: float = 0.0
    affects_unity: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "movement_id": self.movement_id,
            "name": self.name,
            "origin_faction": self.origin_faction,
            "spread_factions": self.spread_factions,
            "influence": self.influence,
            "subversive": self.subversive,
            "affects_legitimacy": self.affects_legitimacy,
            "affects_unity": self.affects_unity,
        }


# ============================================================================
# BACKWARD COMPATIBILITY: v1.0 FACTION AND GLOBAL STATE (WITH v1.0 SCHEMA)
# ============================================================================

@dataclass
class FactionState:
    """Represents the state of a faction in the simulation (v1.0 canonical schema)."""
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

    # Diplomacy memory: trust[other_faction_id] -> score
    trust_scores: Dict[str, float] = field(default_factory=dict)

    # Reputation (affected by treaty breaches)
    reputation: float = 0.7

    # Derived fields
    verification_demand: float = 0.5
    deal_discount: float = 0.0
    coalition_invite_weight: float = 0.5

    # Structural ceiling: not every polity can reach max economy
    economic_potential: float = 0.7

    certainty: CertaintyTag = CertaintyTag.STAGING

    # v2.0 additions (all optional with defaults)
    coalition_memberships: List[str] = field(default_factory=list)
    fleet_ids: List[str] = field(default_factory=list)
    controlled_locations: List[str] = field(default_factory=list)
    active_operatives: List[str] = field(default_factory=list)
    doctrine_id: Optional[str] = None
    cultural_movements: List[str] = field(default_factory=list)
    media_control: float = 0.5
    soft_power: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "faction_id": self.faction_id,
            "name": self.name,
            "faction_type": self.faction_type.value,
            "notes": self.notes,
            "leader_id": self.leader_id,
            "military_strength": self.military_strength,
            "economic_strength": self.economic_strength,
            "technology_level": self.technology_level,
            "population_stability": self.population_stability,
            "trust_scores": self.trust_scores,
            "reputation": self.reputation,
            "verification_demand": self.verification_demand,
            "deal_discount": self.deal_discount,
            "coalition_invite_weight": self.coalition_invite_weight,
            "economic_potential": self.economic_potential,
            "certainty": self.certainty.value,
            "coalition_memberships": self.coalition_memberships,
            "fleet_ids": self.fleet_ids,
            "controlled_locations": self.controlled_locations,
            "active_operatives": self.active_operatives,
            "doctrine_id": self.doctrine_id,
            "cultural_movements": self.cultural_movements,
            "media_control": self.media_control,
            "soft_power": self.soft_power,
        }


@dataclass
class GUMASState:
    """Complete state representation of the GUMAS simulation (v1.0 canonical schema + v2.0 additions)."""
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
    anchor: str = "GUMAS-ENGINE-V2"
    ethics_protocol: str = "Picard_Delta_3"
    version: str = "2.0.0"

    # v2.0 additions (all optional with defaults)
    coalitions: Dict[str, CoalitionState] = field(default_factory=dict)
    topology: Optional[GalaxyTopology] = None
    fleets: Dict[str, FleetState] = field(default_factory=dict)
    combat_zones: Dict[str, CombatState] = field(default_factory=dict)
    economy: Optional[EconomicState] = None
    media: Optional[MediaEcosystem] = None
    precursor_sites: Dict[str, PrecursorSite] = field(default_factory=dict)
    operatives: Dict[str, SentinelOperative] = field(default_factory=dict)
    missions: Dict[str, MissionState] = field(default_factory=dict)
    doctrines: Dict[str, DoctrineProfile] = field(default_factory=dict)
    culture_movements: Dict[str, CultureMovement] = field(default_factory=dict)

    def to_dict(self, include_history: bool = False) -> Dict[str, Any]:
        """Serialize complete simulation state to dictionary."""
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
            "coalitions": {k: v.to_dict() for k, v in self.coalitions.items()},
            "topology": self.topology.to_dict() if self.topology else None,
            "fleets": {k: v.to_dict() for k, v in self.fleets.items()},
            "combat_zones": {k: v.to_dict() for k, v in self.combat_zones.items()},
            "economy": self.economy.to_dict() if self.economy else None,
            "media": self.media.to_dict() if self.media else None,
            "precursor_sites": {k: v.to_dict() for k, v in self.precursor_sites.items()},
            "operatives": {k: v.to_dict() for k, v in self.operatives.items()},
            "missions": {k: v.to_dict() for k, v in self.missions.items()},
            "doctrines": {k: v.to_dict() for k, v in self.doctrines.items()},
            "culture_movements": {k: v.to_dict() for k, v in self.culture_movements.items()},
        }
        if include_history:
            result["history"] = [h.to_dict() for h in self.history]
        return result


__all__ = [
    # v1.0 enums
    "CertaintyTag",
    "BiasType",
    "FactionType",
    "ConflictPhase",
    "TreatyPhase",
    "EventType",
    # v2.0 enums
    "CoalitionType",
    "ResourceType",
    "LocationType",
    "HyperlaneType",
    "BattlefieldCondition",
    "DiscoveryPhase",
    "PrecursorOrigin",
    "SentinelRank",
    "MissionType",
    "DoctrineType",
    # v1.0 dataclasses
    "LeaderState",
    "ConflictState",
    "TreatyState",
    "SimulationEvent",
    "TickResult",
    "FactionState",
    "GUMASState",
    # v2.0 dataclasses
    "CoalitionState",
    "MarketState",
    "TradeRoute",
    "EconomicState",
    "TopologyNode",
    "HyperlaneEdge",
    "GalaxyTopology",
    "FleetState",
    "CombatState",
    "MediaOutlet",
    "NarrativeState",
    "MediaEcosystem",
    "PrecursorSite",
    "SentinelOperative",
    "MissionState",
    "DoctrineProfile",
    "CultureMovement",
]

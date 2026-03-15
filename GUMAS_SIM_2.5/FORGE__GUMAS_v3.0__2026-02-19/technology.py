#!/usr/bin/env python3
"""
GUMAS v3.0 — Technology Development Tree Module
================================================
Anchor: GUMAS-ENGINE-TECHNOLOGY-V3
Seed:   EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP:    L2_ENGINE_V3
Version: 3.0.0

Models Research & Development investment, technology branching trees,
military vs civilian tech distinction, inter-faction tech diffusion,
and technology advantage in combat and economics.

Subsystem roles in tick lifecycle:
    Phase 17 — Technology Tick (after Population Tick)

Formulas:
    calc_tech_advance_rate()     — R&D investment → tech level gain
    calc_tech_diffusion()        — passive tech transfer between factions
    calc_military_tech_advantage()  — tech edge in combat resolution
    calc_civilian_tech_multiplier() — tech boost to economic potential
    calc_tech_espionage_yield()  — stolen tech from sentinel missions

Design principles:
    - Stdlib only; no numpy/scipy
    - Tech levels: float [0.0, 5.0] per domain (not a percentage)
    - Branching tree: unlocks cascade when thresholds are crossed
    - Diffusion: trust-weighted passive transfer each turn
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Set, Any


# ============================================================================
# ENUMS
# ============================================================================

class TechCategory(Enum):
    """Primary technology domains."""
    PROPULSION     = "propulsion"        # fleet speed, hyperlane access
    WEAPONS        = "weapons"           # combat effectiveness
    SHIELDING      = "shielding"         # combat defense
    COMPUTING      = "computing"         # doctrine, espionage, media
    BIOTECH        = "biotech"           # population health, bioweapons
    ENERGY         = "energy"            # economic multiplier, weapons
    MATERIALS      = "materials"         # construction, fleet hull strength
    PRECURSOR_TECH = "precursor_tech"    # understanding of precursor artifacts


class TechMaturity(Enum):
    """Technology maturity phase — affects diffusion rate."""
    EXPERIMENTAL   = "experimental"   # just discovered, hard to apply
    DEVELOPING     = "developing"     # being integrated into systems
    OPERATIONAL    = "operational"    # fully deployed and effective
    LEGACY         = "legacy"         # being superseded, still functional


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class TechNode:
    """
    A single technology in the development tree.

    Nodes unlock at threshold tech levels and provide
    multiplier bonuses to specified game mechanics.
    """
    node_id: str
    category: TechCategory
    name: str
    description: str

    # Unlock condition: requires parent node + minimum category level
    parent_node_id: Optional[str] = None
    unlock_level_required: float = 0.0

    # Game effect multipliers (1.0 = no effect)
    combat_multiplier: float = 1.0
    economic_multiplier: float = 1.0
    espionage_multiplier: float = 1.0
    population_multiplier: float = 1.0   # health/food production

    maturity: TechMaturity = TechMaturity.EXPERIMENTAL
    is_unlocked: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["category"] = self.category.value
        d["maturity"] = self.maturity.value
        return d


@dataclass
class FactionTechState:
    """
    Technology state for a single faction.

    tech_levels: category → float [0.0, 5.0]
    active_rd: category → R&D investment fraction (sums to ≤ 1.0)
    unlocked_nodes: set of node_ids that have been unlocked
    """
    faction_id: str

    # Current tech levels per domain
    tech_levels: Dict[str, float] = field(default_factory=lambda: {
        c.value: 1.0 for c in TechCategory
    })

    # Active R&D allocation (fractions, should sum ≤ 1.0)
    active_rd: Dict[str, float] = field(default_factory=lambda: {
        c.value: 0.125 for c in TechCategory  # default: evenly spread
    })

    # R&D capacity (scales with economic strength)
    rd_capacity: float = 0.5

    # Nodes unlocked
    unlocked_nodes: Set[str] = field(default_factory=set)

    # Tech stolen from others (bonus fractional levels)
    stolen_tech: Dict[str, float] = field(default_factory=dict)

    # Accumulated research per category (converted to levels at threshold)
    research_progress: Dict[str, float] = field(default_factory=lambda: {
        c.value: 0.0 for c in TechCategory
    })

    def get_level(self, category: TechCategory) -> float:
        return self.tech_levels.get(category.value, 0.0)

    def total_tech_level(self) -> float:
        return sum(self.tech_levels.values())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "faction_id": self.faction_id,
            "tech_levels": dict(self.tech_levels),
            "active_rd": dict(self.active_rd),
            "rd_capacity": self.rd_capacity,
            "unlocked_nodes": list(self.unlocked_nodes),
            "stolen_tech": dict(self.stolen_tech),
            "research_progress": dict(self.research_progress),
        }


# ============================================================================
# CANONICAL TECH TREE
# ============================================================================

CANONICAL_TECH_TREE: List[TechNode] = [
    # PROPULSION
    TechNode("prop_1", TechCategory.PROPULSION, "Hyperlane Mapping",
             "Improves fleet route efficiency by 15%.",
             unlock_level_required=0.0, combat_multiplier=1.05, economic_multiplier=1.10),
    TechNode("prop_2", TechCategory.PROPULSION, "Jump Drive",
             "Enables wormhole transit; bypasses minor hyperlane chokepoints.",
             parent_node_id="prop_1", unlock_level_required=2.0,
             combat_multiplier=1.15, economic_multiplier=1.20),
    TechNode("prop_3", TechCategory.PROPULSION, "Drift Corridor Mastery",
             "Full access to SECRET_PASSAGE hyperlane class.",
             parent_node_id="prop_2", unlock_level_required=3.5,
             combat_multiplier=1.25, economic_multiplier=1.30),

    # WEAPONS
    TechNode("weap_1", TechCategory.WEAPONS, "Directed Energy Arrays",
             "Fleet combat effectiveness +10%.",
             unlock_level_required=0.0, combat_multiplier=1.10),
    TechNode("weap_2", TechCategory.WEAPONS, "Orbital Strike Platforms",
             "Enables BLOCKADE events with fortification bonus.",
             parent_node_id="weap_1", unlock_level_required=2.0,
             combat_multiplier=1.20),
    TechNode("weap_3", TechCategory.WEAPONS, "Precursor Weapon Integration",
             "Applies precursor power output to combat (requires precursor_tech ≥ 3).",
             parent_node_id="weap_2", unlock_level_required=4.0,
             combat_multiplier=1.50),

    # SHIELDING
    TechNode("shld_1", TechCategory.SHIELDING, "Phase Shielding",
             "Fleet defense +10%; reduces casualties.",
             unlock_level_required=0.0, combat_multiplier=1.08),
    TechNode("shld_2", TechCategory.SHIELDING, "Adaptive Hull Lattice",
             "Fleet defense +20%; materials level required.",
             parent_node_id="shld_1", unlock_level_required=2.5,
             combat_multiplier=1.20),

    # COMPUTING
    TechNode("comp_1", TechCategory.COMPUTING, "Predictive Analytics",
             "Espionage operations +10%; doctrine Q-learning rate +0.02.",
             unlock_level_required=0.0, espionage_multiplier=1.10),
    TechNode("comp_2", TechCategory.COMPUTING, "Distributed Inference Grid",
             "Media campaign effectiveness +15%; sentinel tradecraft bonus.",
             parent_node_id="comp_1", unlock_level_required=2.0,
             espionage_multiplier=1.20, economic_multiplier=1.10),
    TechNode("comp_3", TechCategory.COMPUTING, "Autonomous Battle Management",
             "Combat +20% via real-time tactical AI.",
             parent_node_id="comp_2", unlock_level_required=3.5,
             combat_multiplier=1.20, espionage_multiplier=1.30),

    # BIOTECH
    TechNode("bio_1", TechCategory.BIOTECH, "Advanced Medicine",
             "Population growth rate +0.005; war casualty rate -20%.",
             unlock_level_required=0.0, population_multiplier=1.15),
    TechNode("bio_2", TechCategory.BIOTECH, "Genetic Optimization",
             "Population ceiling +10%; food security +0.05.",
             parent_node_id="bio_1", unlock_level_required=2.0,
             population_multiplier=1.25, economic_multiplier=1.05),

    # ENERGY
    TechNode("nrg_1", TechCategory.ENERGY, "Fusion Reactors",
             "Economic strength ceiling +0.1.",
             unlock_level_required=0.0, economic_multiplier=1.12),
    TechNode("nrg_2", TechCategory.ENERGY, "Zero-Point Extraction",
             "Economic ceiling +0.2; fleet supply decay -30%.",
             parent_node_id="nrg_1", unlock_level_required=3.0,
             economic_multiplier=1.25, combat_multiplier=1.08),

    # MATERIALS
    TechNode("mat_1", TechCategory.MATERIALS, "Nano-Composite Hulls",
             "Fleet combat losses -15%.",
             unlock_level_required=0.0, combat_multiplier=1.08),
    TechNode("mat_2", TechCategory.MATERIALS, "Crystalline Infrastructure",
             "Infrastructure investment events more effective.",
             parent_node_id="mat_1", unlock_level_required=2.0,
             economic_multiplier=1.15),

    # PRECURSOR TECH
    TechNode("prec_1", TechCategory.PRECURSOR_TECH, "Precursor Archaeology",
             "Precursor discovery rate +25%; activation risk -10%.",
             unlock_level_required=0.0),
    TechNode("prec_2", TechCategory.PRECURSOR_TECH, "Precursor Power Conduit",
             "Doubles precursor power_output for controlling faction.",
             parent_node_id="prec_1", unlock_level_required=2.5,
             combat_multiplier=1.15, economic_multiplier=1.15),
    TechNode("prec_3", TechCategory.PRECURSOR_TECH, "Transcendent Integration",
             "Unlocks SHROUDBORN-class activation without risk penalty.",
             parent_node_id="prec_2", unlock_level_required=4.0,
             combat_multiplier=1.40, economic_multiplier=1.40),
]


# ============================================================================
# TECHNOLOGY ENGINE
# ============================================================================

class TechnologyEngine:
    """
    Drives R&D investment, tech advancement, diffusion, and node unlocking.

    Usage (inside engine.py Phase 17):
        tech_engine = TechnologyEngine()
        events = tech_engine.tick(tech_states, trust_matrix, rng)
    """

    # Research needed per tech level increment
    RESEARCH_PER_LEVEL = 5.0

    # Maximum diffusion rate per turn between friendly factions
    MAX_DIFFUSION_RATE = 0.08

    # Max tech level per category
    MAX_TECH_LEVEL = 5.0

    def __init__(self):
        self._tree: Dict[str, TechNode] = {n.node_id: n for n in CANONICAL_TECH_TREE}

    def tick(
        self,
        tech_states: Dict[str, FactionTechState],
        trust_matrix: Dict[str, Dict[str, float]],
        rng,
    ) -> List[Dict[str, Any]]:
        """
        Advance technology state for all factions.

        Args:
            tech_states: faction_id → FactionTechState
            trust_matrix: faction_id → {other_id → trust_score}
            rng: Seeded Random instance

        Returns:
            List of event dicts (TECH_BREAKTHROUGH_ADVANCED, TECH_DIFFUSION)
        """
        events: List[Dict[str, Any]] = []

        # Phase 1: R&D investment → progress accumulation
        for fid, ts in tech_states.items():
            advance_events = self._apply_rd_investment(ts, rng)
            events.extend(advance_events)

        # Phase 2: Tech diffusion between friendly factions
        faction_ids = list(tech_states.keys())
        for i, src_id in enumerate(faction_ids):
            for dst_id in faction_ids[i + 1:]:
                trust = trust_matrix.get(src_id, {}).get(dst_id, 0.0)
                if trust > 0.4:
                    diff_event = self._apply_diffusion(
                        tech_states[src_id], tech_states[dst_id], trust, rng
                    )
                    if diff_event:
                        events.append(diff_event)

        # Phase 3: Node unlock checks
        for fid, ts in tech_states.items():
            unlock_events = self._check_node_unlocks(ts)
            events.extend(unlock_events)

        return events

    def _apply_rd_investment(
        self,
        ts: FactionTechState,
        rng,
    ) -> List[Dict[str, Any]]:
        events = []
        for cat_val, rd_fraction in ts.active_rd.items():
            if rd_fraction <= 0:
                continue
            rate = calc_tech_advance_rate(
                rd_fraction=rd_fraction,
                rd_capacity=ts.rd_capacity,
                current_level=ts.tech_levels.get(cat_val, 0.0),
                max_level=self.MAX_TECH_LEVEL,
            )
            ts.research_progress[cat_val] = ts.research_progress.get(cat_val, 0.0) + rate

            # Level up when progress threshold reached
            while ts.research_progress.get(cat_val, 0.0) >= self.RESEARCH_PER_LEVEL:
                current = ts.tech_levels.get(cat_val, 0.0)
                if current < self.MAX_TECH_LEVEL:
                    ts.tech_levels[cat_val] = round(current + 0.5, 2)
                    ts.research_progress[cat_val] -= self.RESEARCH_PER_LEVEL
                    events.append({
                        "type": "TECH_BREAKTHROUGH_ADVANCED",
                        "faction_id": ts.faction_id,
                        "category": cat_val,
                        "new_level": ts.tech_levels[cat_val],
                    })
                else:
                    ts.research_progress[cat_val] = 0.0
                    break
        return events

    def _apply_diffusion(
        self,
        src: FactionTechState,
        dst: FactionTechState,
        trust: float,
        rng,
    ) -> Optional[Dict[str, Any]]:
        # Find largest tech gap that can diffuse
        best_cat = None
        best_gap = 0.0
        for cat_val in src.tech_levels:
            gap = src.tech_levels[cat_val] - dst.tech_levels.get(cat_val, 0.0)
            if gap > best_gap:
                best_gap = gap
                best_cat = cat_val

        if best_cat is None or best_gap < 0.3:
            return None

        diffused = calc_tech_diffusion(
            gap=best_gap,
            trust_score=trust,
            max_diffusion_rate=self.MAX_DIFFUSION_RATE,
        )

        if diffused > 0.01 and rng.random() < trust * 0.5:
            dst.tech_levels[best_cat] = min(
                self.MAX_TECH_LEVEL,
                dst.tech_levels.get(best_cat, 0.0) + diffused
            )
            return {
                "type": "TECH_DIFFUSION",
                "source_faction": src.faction_id,
                "destination_faction": dst.faction_id,
                "category": best_cat,
                "amount": round(diffused, 4),
            }
        return None

    def _check_node_unlocks(
        self,
        ts: FactionTechState,
    ) -> List[Dict[str, Any]]:
        events = []
        for node in self._tree.values():
            if node.node_id in ts.unlocked_nodes:
                continue
            if node.parent_node_id and node.parent_node_id not in ts.unlocked_nodes:
                continue
            current_level = ts.tech_levels.get(node.category.value, 0.0)
            if current_level >= node.unlock_level_required:
                ts.unlocked_nodes.add(node.node_id)
                events.append({
                    "type": "TECH_NODE_UNLOCKED",
                    "faction_id": ts.faction_id,
                    "node_id": node.node_id,
                    "node_name": node.name,
                    "category": node.category.value,
                })
        return events

    def get_combat_multiplier(self, ts: FactionTechState) -> float:
        """Aggregate combat multiplier from all unlocked nodes."""
        mult = 1.0
        for nid in ts.unlocked_nodes:
            node = self._tree.get(nid)
            if node:
                mult *= node.combat_multiplier
        return mult

    def get_economic_multiplier(self, ts: FactionTechState) -> float:
        """Aggregate economic multiplier from all unlocked nodes."""
        mult = 1.0
        for nid in ts.unlocked_nodes:
            node = self._tree.get(nid)
            if node:
                mult *= node.economic_multiplier
        return mult


# ============================================================================
# PURE FORMULA FUNCTIONS
# ============================================================================

def calc_tech_advance_rate(
    rd_fraction: float,
    rd_capacity: float,
    current_level: float,
    max_level: float = 5.0,
    *,
    base_rate: float = 0.8,
    diminishing_factor: float = 1.5,
) -> float:
    """
    Research points accumulated per turn in a given domain.

    Formula:
        proximity = 1 - (current_level / max_level)
        rate = base_rate × rd_fraction × rd_capacity × proximity^diminishing_factor

    Diminishing returns: harder to advance near the tech ceiling.

    Returns:
        float — research points accumulated this turn
    """
    proximity = max(0.0, 1.0 - (current_level / max_level))
    rate = base_rate * rd_fraction * rd_capacity * (proximity ** diminishing_factor)
    return max(0.0, rate)


def calc_tech_diffusion(
    gap: float,
    trust_score: float,
    max_diffusion_rate: float = 0.08,
    *,
    gap_weight: float = 0.6,
    trust_weight: float = 0.4,
) -> float:
    """
    Passive tech transfer from advanced to less-advanced faction per turn.

    Formula:
        diffusion = max_diffusion_rate × (gap_weight × gap/5 + trust_weight × trust_score)

    Returns:
        float — tech level units transferred this turn
    """
    if gap <= 0.0:
        return 0.0  # no gap → nothing to diffuse
    normalized_gap = min(1.0, gap / 5.0)
    # Trust amplifies diffusion of the gap; without a gap trust has no effect
    diffusion = max_diffusion_rate * normalized_gap * (gap_weight + trust_weight * trust_score)
    return max(0.0, diffusion)


def calc_military_tech_advantage(
    attacker_level: float,
    defender_level: float,
    *,
    advantage_cap: float = 0.40,
    per_level_bonus: float = 0.06,
) -> float:
    """
    Combat advantage from technology differential.

    Formula:
        diff = attacker_level - defender_level
        advantage = diff × per_level_bonus
        clamped to [-advantage_cap, +advantage_cap]

    Returns:
        float — fractional combat bonus (positive favours attacker)
    """
    diff = attacker_level - defender_level
    advantage = diff * per_level_bonus
    return max(-advantage_cap, min(advantage_cap, advantage))


def calc_civilian_tech_multiplier(
    energy_level: float,
    materials_level: float,
    computing_level: float,
    *,
    energy_weight: float    = 0.40,
    materials_weight: float = 0.30,
    computing_weight: float = 0.30,
    baseline_level: float   = 1.0,
    max_bonus: float        = 0.50,
) -> float:
    """
    Economic multiplier from civilian technology applications.

    Formula:
        above_baseline = (energy_weight × energy_level
                        + materials_weight × materials_level
                        + computing_weight × computing_level) - baseline_level
        multiplier = 1.0 + max_bonus × max(0, above_baseline) / 5.0

    Returns:
        float in [1.0, 1.0 + max_bonus]
    """
    weighted = (
        energy_weight    * energy_level
        + materials_weight * materials_level
        + computing_weight * computing_level
    )
    above = max(0.0, weighted - baseline_level)
    multiplier = 1.0 + max_bonus * (above / 5.0)
    return min(1.0 + max_bonus, multiplier)


def calc_tech_espionage_yield(
    sentinel_computing_skill: float,
    target_tech_level: float,
    target_counter_intel: float,
    *,
    base_yield: float = 0.3,
    skill_weight: float = 0.5,
) -> float:
    """
    Technology level stolen via a successful espionage mission.

    Formula:
        success_factor = skill_weight × sentinel_computing_skill
                        + (1 - skill_weight) × min(1, target_tech_level / 5)
        yield = base_yield × success_factor × (1 - target_counter_intel × 0.5)

    Returns:
        float — tech level units stolen (to be added to stolen_tech registry)
    """
    success_factor = (
        skill_weight * sentinel_computing_skill
        + (1.0 - skill_weight) * min(1.0, target_tech_level / 5.0)
    )
    yield_val = base_yield * success_factor * (1.0 - target_counter_intel * 0.5)
    return max(0.0, min(1.0, yield_val))

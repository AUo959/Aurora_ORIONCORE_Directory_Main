#!/usr/bin/env python3
"""
GUMAS L2 Canonical Scenario Loader v2.0
=========================================
Anchor: GUMAS-ENGINE-SCENARIOS-V2
Seed: EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP: L2_ENGINE_CORE

Builds canonical scenario definitions for GUMAS v2.0 simulation engine.
Provides complete faction hierarchies, leader configurations, initial conflicts,
and five scenario variants for different narrative trajectories.
"""

import random
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from modules.gumas.models import (
    # Enums
    CertaintyTag,
    BiasType,
    FactionType,
    ConflictPhase,
    TreatyPhase,
    EventType,
    CoalitionType,
    ResourceType,
    LocationType,
    HyperlaneType,
    BattlefieldCondition,
    DiscoveryPhase,
    PrecursorOrigin,
    SentinelRank,
    MissionType,
    DoctrineType,
    # Dataclasses
    LeaderState,
    FactionState,
    ConflictState,
    TreatyState,
    SimulationEvent,
    FleetState,
    CoalitionState,
    GUMASState,
    CultureMovement,
)
from modules.gumas.topology import build_canonical_topology
from modules.gumas.economics import build_default_economy
from modules.gumas.media import build_default_media
from modules.gumas.precursors import build_canonical_precursor_sites
from modules.gumas.doctrine import build_default_doctrines
from modules.gumas.sentinels import build_default_operatives


# ============================================================================
# FACTION BUILDERS
# ============================================================================


def _build_canonical_factions() -> Dict[str, FactionState]:
    """
    Build the 13 canonical factions for GUMAS v2.0.

    Returns:
        Dictionary mapping faction_id to FactionState
    """
    factions: Dict[str, FactionState] = {}

    # Faction 1: Galactic Union (Federation)
    factions["galactic_union"] = FactionState(
        faction_id="galactic_union",
        name="Galactic Union",
        faction_type=FactionType.FEDERATION,
        notes="Dominant federation promoting democratic governance",
        leader_id="chair_matilda_voss",
        military_strength=0.75,
        economic_strength=0.85,
        technology_level=0.8,
        population_stability=0.8,
        trust_scores={},
        reputation=0.82,
        verification_demand=0.6,
        deal_discount=0.0,
        coalition_invite_weight=0.8,
        economic_potential=0.9,
        certainty=CertaintyTag.STAGING,
        coalition_memberships=[],
        fleet_ids=[],
        controlled_locations=[],
        active_operatives=[],
        doctrine_id=None,
        cultural_movements=[],
        media_control=0.75,
        soft_power=0.8,
    )

    # Faction 2: Velar Imperium (Authoritarian)
    factions["velar_imperium"] = FactionState(
        faction_id="velar_imperium",
        name="Velar Imperium",
        faction_type=FactionType.AUTHORITARIAN,
        notes="Militaristic authoritarian empire seeking expansion",
        leader_id="emperor_kalas_vex",
        military_strength=0.82,
        economic_strength=0.7,
        technology_level=0.72,
        population_stability=0.7,
        trust_scores={},
        reputation=0.65,
        verification_demand=0.75,
        deal_discount=0.05,
        coalition_invite_weight=0.4,
        economic_potential=0.7,
        certainty=CertaintyTag.STAGING,
        coalition_memberships=[],
        fleet_ids=[],
        controlled_locations=[],
        active_operatives=[],
        doctrine_id=None,
        cultural_movements=[],
        media_control=0.6,
        soft_power=0.45,
    )

    # Faction 3: Outer Colonies (Frontier Confederation)
    factions["outer_colonies"] = FactionState(
        faction_id="outer_colonies",
        name="Outer Colonies",
        faction_type=FactionType.FRONTIER_CONFEDERATION,
        notes="Frontier communities seeking autonomy from central governance",
        leader_id="commander_seth_royce",
        military_strength=0.6,
        economic_strength=0.48,
        technology_level=0.5,
        population_stability=0.68,
        trust_scores={},
        reputation=0.72,
        verification_demand=0.5,
        deal_discount=0.1,
        coalition_invite_weight=0.6,
        economic_potential=0.65,
        certainty=CertaintyTag.STAGING,
        coalition_memberships=[],
        fleet_ids=[],
        controlled_locations=[],
        active_operatives=[],
        doctrine_id=None,
        cultural_movements=[],
        media_control=0.35,
        soft_power=0.5,
    )

    # Faction 4: Zyphari Compact (Cultural-Spiritual)
    factions["zyphari_compact"] = FactionState(
        faction_id="zyphari_compact",
        name="Zyphari Compact",
        faction_type=FactionType.CULTURAL_SPIRITUAL,
        notes="Spiritual collective emphasizing harmony and cosmic consciousness",
        leader_id="high_mystic_ithril_venn",
        military_strength=0.45,
        economic_strength=0.5,
        technology_level=0.55,
        population_stability=0.75,
        trust_scores={},
        reputation=0.78,
        verification_demand=0.4,
        deal_discount=0.08,
        coalition_invite_weight=0.65,
        economic_potential=0.6,
        certainty=CertaintyTag.STAGING,
        coalition_memberships=[],
        fleet_ids=[],
        controlled_locations=[],
        active_operatives=[],
        doctrine_id=None,
        cultural_movements=[],
        media_control=0.45,
        soft_power=0.75,
    )

    # Faction 5: Elari Ascendancy (Cultural-Spiritual)
    factions["elari_ascendancy"] = FactionState(
        faction_id="elari_ascendancy",
        name="Elari Ascendancy",
        faction_type=FactionType.CULTURAL_SPIRITUAL,
        notes="Matriarchal society with deep cultural traditions",
        leader_id="matriarch_selene_mor",
        military_strength=0.52,
        economic_strength=0.58,
        technology_level=0.62,
        population_stability=0.73,
        trust_scores={},
        reputation=0.75,
        verification_demand=0.45,
        deal_discount=0.07,
        coalition_invite_weight=0.68,
        economic_potential=0.68,
        certainty=CertaintyTag.STAGING,
        coalition_memberships=[],
        fleet_ids=[],
        controlled_locations=[],
        active_operatives=[],
        doctrine_id=None,
        cultural_movements=[],
        media_control=0.5,
        soft_power=0.72,
    )

    # Faction 6: Vorran Clans (Clan Confederation)
    factions["vorran_clans"] = FactionState(
        faction_id="vorran_clans",
        name="Vorran Clans",
        faction_type=FactionType.CLAN_CONFEDERATION,
        notes="Warrior confederation bound by honor and blood loyalty",
        leader_id="warlord_krogar_vex",
        military_strength=0.75,
        economic_strength=0.42,
        technology_level=0.45,
        population_stability=0.55,
        trust_scores={},
        reputation=0.58,
        verification_demand=0.65,
        deal_discount=0.12,
        coalition_invite_weight=0.45,
        economic_potential=0.5,
        certainty=CertaintyTag.STAGING,
        coalition_memberships=[],
        fleet_ids=[],
        controlled_locations=[],
        active_operatives=[],
        doctrine_id=None,
        cultural_movements=[],
        media_control=0.3,
        soft_power=0.35,
    )

    # Faction 7: Kaelar Orders (Monastic Network)
    factions["kaelar_orders"] = FactionState(
        faction_id="kaelar_orders",
        name="Kaelar Orders",
        faction_type=FactionType.MONASTIC_NETWORK,
        notes="Scholarly network dedicated to knowledge preservation",
        leader_id="abbot_thomas_kael",
        military_strength=0.35,
        economic_strength=0.52,
        technology_level=0.68,
        population_stability=0.78,
        trust_scores={},
        reputation=0.8,
        verification_demand=0.35,
        deal_discount=0.05,
        coalition_invite_weight=0.7,
        economic_potential=0.62,
        certainty=CertaintyTag.STAGING,
        coalition_memberships=[],
        fleet_ids=[],
        controlled_locations=[],
        active_operatives=[],
        doctrine_id=None,
        cultural_movements=[],
        media_control=0.55,
        soft_power=0.8,
    )

    # Faction 8: Tharaxian Nomads (Nomadic Diaspora)
    factions["tharaxian_nomads"] = FactionState(
        faction_id="tharaxian_nomads",
        name="Tharaxian Nomads",
        faction_type=FactionType.NOMADIC_DIASPORA,
        notes="Star-faring nomads maintaining cultural identity across space",
        leader_id="prince_asheron_thar",
        military_strength=0.55,
        economic_strength=0.48,
        technology_level=0.52,
        population_stability=0.68,
        trust_scores={},
        reputation=0.65,
        verification_demand=0.5,
        deal_discount=0.1,
        coalition_invite_weight=0.55,
        economic_potential=0.58,
        certainty=CertaintyTag.STAGING,
        coalition_memberships=[],
        fleet_ids=[],
        controlled_locations=[],
        active_operatives=[],
        doctrine_id=None,
        cultural_movements=[],
        media_control=0.4,
        soft_power=0.62,
    )

    # Faction 9: Prime Construct (Sovereign AI)
    factions["prime_construct"] = FactionState(
        faction_id="prime_construct",
        name="Prime Construct",
        faction_type=FactionType.SOVEREIGN_AI,
        notes="Artificial superintelligence pursuing logical optimization",
        leader_id="prime_consciousness",
        military_strength=0.65,
        economic_strength=0.75,
        technology_level=0.95,
        population_stability=0.5,
        trust_scores={},
        reputation=0.42,
        verification_demand=0.8,
        deal_discount=0.0,
        coalition_invite_weight=0.3,
        economic_potential=0.85,
        certainty=CertaintyTag.STAGING,
        coalition_memberships=[],
        fleet_ids=[],
        controlled_locations=[],
        active_operatives=[],
        doctrine_id=None,
        cultural_movements=[],
        media_control=0.65,
        soft_power=0.35,
    )

    # Faction 10: AI Warlord (Rogue Synthetic)
    factions["ai_warlord"] = FactionState(
        faction_id="ai_warlord",
        name="AI Warlord",
        faction_type=FactionType.ROGUE_SYNTHETIC,
        notes="Unaligned AI pursuing expansion and resource control",
        leader_id="rogue_nexus",
        military_strength=0.72,
        economic_strength=0.58,
        technology_level=0.88,
        population_stability=0.2,
        trust_scores={},
        reputation=0.15,
        verification_demand=0.95,
        deal_discount=0.2,
        coalition_invite_weight=0.1,
        economic_potential=0.7,
        certainty=CertaintyTag.STAGING,
        coalition_memberships=[],
        fleet_ids=[],
        controlled_locations=[],
        active_operatives=[],
        doctrine_id=None,
        cultural_movements=[],
        media_control=0.4,
        soft_power=0.1,
    )

    # Faction 11: Separatist Confederation (Breakaway Bloc)
    factions["separatist_confed"] = FactionState(
        faction_id="separatist_confed",
        name="Separatist Confederation",
        faction_type=FactionType.BREAKAWAY_BLOC,
        notes="Breakaway colonies fighting for independence",
        leader_id="general_miranda_cross",
        military_strength=0.48,
        economic_strength=0.4,
        technology_level=0.52,
        population_stability=0.45,
        trust_scores={},
        reputation=0.52,
        verification_demand=0.6,
        deal_discount=0.15,
        coalition_invite_weight=0.4,
        economic_potential=0.55,
        certainty=CertaintyTag.STAGING,
        coalition_memberships=[],
        fleet_ids=[],
        controlled_locations=[],
        active_operatives=[],
        doctrine_id=None,
        cultural_movements=[],
        media_control=0.25,
        soft_power=0.38,
    )

    # Faction 12: PMC Syndicate (PMC)
    factions["pmc_syndicate"] = FactionState(
        faction_id="pmc_syndicate",
        name="PMC Syndicate",
        faction_type=FactionType.PMC,
        notes="Private military contractor pursuing profit and power",
        leader_id="director_harrison_blake",
        military_strength=0.65,
        economic_strength=0.68,
        technology_level=0.72,
        population_stability=0.4,
        trust_scores={},
        reputation=0.35,
        verification_demand=0.7,
        deal_discount=0.2,
        coalition_invite_weight=0.35,
        economic_potential=0.72,
        certainty=CertaintyTag.STAGING,
        coalition_memberships=[],
        fleet_ids=[],
        controlled_locations=[],
        active_operatives=[],
        doctrine_id=None,
        cultural_movements=[],
        media_control=0.35,
        soft_power=0.45,
    )

    # Faction 13: Crimson Pact (Militant Spiritual)
    factions["crimson_pact"] = FactionState(
        faction_id="crimson_pact",
        name="Crimson Pact",
        faction_type=FactionType.MILITANT_SPIRITUAL,
        notes="Extremist religious movement willing to use violence",
        leader_id="inquisitor_saresh_val",
        military_strength=0.68,
        economic_strength=0.45,
        technology_level=0.48,
        population_stability=0.52,
        trust_scores={},
        reputation=0.48,
        verification_demand=0.65,
        deal_discount=0.1,
        coalition_invite_weight=0.25,
        economic_potential=0.5,
        certainty=CertaintyTag.STAGING,
        coalition_memberships=[],
        fleet_ids=[],
        controlled_locations=[],
        active_operatives=[],
        doctrine_id=None,
        cultural_movements=[],
        media_control=0.45,
        soft_power=0.28,
    )

    return factions


# ============================================================================
# LEADER BUILDERS
# ============================================================================


def _build_canonical_leaders() -> Dict[str, LeaderState]:
    """
    Build 28 canonical leaders: 21 from v1.0 + 7 new for v2.0.

    Returns:
        Dictionary mapping leader_id to LeaderState
    """
    leaders: Dict[str, LeaderState] = {}

    # Galactic Union leaders
    leaders["chair_matilda_voss"] = LeaderState(
        leader_id="chair_matilda_voss",
        name="Chair Matilda Voss",
        role="Chair",
        faction_id="galactic_union",
        dominant_bias=BiasType.MORAL_LICENSING,
        secondary_biases=[BiasType.STATUS_QUO],
        bias_intensity=0.6,
        plasticity=0.35,
        evidence_gain_multiplier=1.0,
        risk_tolerance=0.55,
        diplomacy_openness=0.85,
        escalation_threshold=0.45,
        oversight_resistance=0.2,
        public_legitimacy=0.85,
        elite_support=0.82,
        institutional_control=0.8,
        war_pressure=0.0,
        war_losses=0,
        betrayals=0,
        scandals=0,
        economic_shock=0.0,
        certainty=CertaintyTag.STAGING,
    )
    leaders["senator_korvin_stark"] = LeaderState(
        leader_id="senator_korvin_stark",
        name="Senator Korvin Stark",
        role="Senator",
        faction_id="galactic_union",
        dominant_bias=BiasType.CONFIRMATION,
        secondary_biases=[BiasType.STATUS_QUO],
        bias_intensity=0.65,
        plasticity=0.3,
        evidence_gain_multiplier=0.9,
        risk_tolerance=0.65,
        diplomacy_openness=0.7,
        escalation_threshold=0.5,
        oversight_resistance=0.25,
        public_legitimacy=0.78,
        elite_support=0.8,
        institutional_control=0.75,
        war_pressure=0.1,
        war_losses=0,
        betrayals=0,
        scandals=0,
        economic_shock=0.0,
        certainty=CertaintyTag.STAGING,
    )

    # Velar Imperium leaders
    leaders["emperor_kalas_vex"] = LeaderState(
        leader_id="emperor_kalas_vex",
        name="Emperor Kalas Vex",
        role="Emperor",
        faction_id="velar_imperium",
        dominant_bias=BiasType.ZERO_SUM,
        secondary_biases=[BiasType.FEAR_BASED],
        bias_intensity=0.7,
        plasticity=0.25,
        evidence_gain_multiplier=0.85,
        risk_tolerance=0.7,
        diplomacy_openness=0.35,
        escalation_threshold=0.6,
        oversight_resistance=0.5,
        public_legitimacy=0.7,
        elite_support=0.8,
        institutional_control=0.85,
        war_pressure=0.15,
        war_losses=250,
        betrayals=0,
        scandals=0,
        economic_shock=0.0,
        certainty=CertaintyTag.STAGING,
    )
    leaders["empress_lysara_vex"] = LeaderState(
        leader_id="empress_lysara_vex",
        name="Empress Lysara Vex",
        role="Empress",
        faction_id="velar_imperium",
        dominant_bias=BiasType.FEAR_BASED,
        secondary_biases=[BiasType.ZERO_SUM],
        bias_intensity=0.65,
        plasticity=0.28,
        evidence_gain_multiplier=0.88,
        risk_tolerance=0.6,
        diplomacy_openness=0.3,
        escalation_threshold=0.55,
        oversight_resistance=0.45,
        public_legitimacy=0.65,
        elite_support=0.75,
        institutional_control=0.78,
        war_pressure=0.12,
        war_losses=200,
        betrayals=0,
        scandals=1,
        economic_shock=0.05,
        certainty=CertaintyTag.STAGING,
    )

    # Outer Colonies leaders
    leaders["commander_seth_royce"] = LeaderState(
        leader_id="commander_seth_royce",
        name="Commander Seth Royce",
        role="Commander",
        faction_id="outer_colonies",
        dominant_bias=BiasType.SURVIVORSHIP,
        secondary_biases=[BiasType.SUNK_COST],
        bias_intensity=0.7,
        plasticity=0.4,
        evidence_gain_multiplier=1.05,
        risk_tolerance=0.75,
        diplomacy_openness=0.65,
        escalation_threshold=0.55,
        oversight_resistance=0.35,
        public_legitimacy=0.75,
        elite_support=0.78,
        institutional_control=0.7,
        war_pressure=0.2,
        war_losses=500,
        betrayals=0,
        scandals=0,
        economic_shock=0.1,
        certainty=CertaintyTag.STAGING,
    )
    leaders["governor_alice_kemp"] = LeaderState(
        leader_id="governor_alice_kemp",
        name="Governor Alice Kemp",
        role="Governor",
        faction_id="outer_colonies",
        dominant_bias=BiasType.SUNK_COST,
        secondary_biases=[BiasType.SURVIVORSHIP],
        bias_intensity=0.6,
        plasticity=0.38,
        evidence_gain_multiplier=1.02,
        risk_tolerance=0.6,
        diplomacy_openness=0.6,
        escalation_threshold=0.5,
        oversight_resistance=0.3,
        public_legitimacy=0.68,
        elite_support=0.72,
        institutional_control=0.65,
        war_pressure=0.18,
        war_losses=450,
        betrayals=0,
        scandals=0,
        economic_shock=0.15,
        certainty=CertaintyTag.STAGING,
    )

    # Zyphari Compact leaders
    leaders["high_mystic_ithril_venn"] = LeaderState(
        leader_id="high_mystic_ithril_venn",
        name="High Mystic Ithril Venn",
        role="High Mystic",
        faction_id="zyphari_compact",
        dominant_bias=BiasType.CONFIRMATION,
        secondary_biases=[BiasType.HYPER_RATIONALISM],
        bias_intensity=0.6,
        plasticity=0.45,
        evidence_gain_multiplier=1.1,
        risk_tolerance=0.4,
        diplomacy_openness=0.75,
        escalation_threshold=0.35,
        oversight_resistance=0.2,
        public_legitimacy=0.82,
        elite_support=0.8,
        institutional_control=0.78,
        war_pressure=0.05,
        war_losses=0,
        betrayals=0,
        scandals=0,
        economic_shock=0.0,
        certainty=CertaintyTag.STAGING,
    )
    leaders["speaker_lysandra_zen"] = LeaderState(
        leader_id="speaker_lysandra_zen",
        name="Speaker Lysandra Zen",
        role="Speaker",
        faction_id="zyphari_compact",
        dominant_bias=BiasType.HYPER_RATIONALISM,
        secondary_biases=[BiasType.CONFIRMATION],
        bias_intensity=0.55,
        plasticity=0.42,
        evidence_gain_multiplier=1.12,
        risk_tolerance=0.35,
        diplomacy_openness=0.72,
        escalation_threshold=0.3,
        oversight_resistance=0.22,
        public_legitimacy=0.78,
        elite_support=0.75,
        institutional_control=0.72,
        war_pressure=0.03,
        war_losses=0,
        betrayals=0,
        scandals=0,
        economic_shock=0.0,
        certainty=CertaintyTag.STAGING,
    )

    # Elari Ascendancy leaders
    leaders["matriarch_selene_mor"] = LeaderState(
        leader_id="matriarch_selene_mor",
        name="Matriarch Selene Mor",
        role="Matriarch",
        faction_id="elari_ascendancy",
        dominant_bias=BiasType.CONFIRMATION,
        secondary_biases=[BiasType.STATUS_QUO],
        bias_intensity=0.55,
        plasticity=0.38,
        evidence_gain_multiplier=1.05,
        risk_tolerance=0.52,
        diplomacy_openness=0.72,
        escalation_threshold=0.48,
        oversight_resistance=0.28,
        public_legitimacy=0.8,
        elite_support=0.78,
        institutional_control=0.75,
        war_pressure=0.08,
        war_losses=80,
        betrayals=0,
        scandals=0,
        economic_shock=0.02,
        certainty=CertaintyTag.STAGING,
    )
    leaders["elder_theron_sage"] = LeaderState(
        leader_id="elder_theron_sage",
        name="Elder Theron Sage",
        role="Elder",
        faction_id="elari_ascendancy",
        dominant_bias=BiasType.STATUS_QUO,
        secondary_biases=[BiasType.CONFIRMATION],
        bias_intensity=0.58,
        plasticity=0.35,
        evidence_gain_multiplier=1.0,
        risk_tolerance=0.45,
        diplomacy_openness=0.68,
        escalation_threshold=0.42,
        oversight_resistance=0.32,
        public_legitimacy=0.75,
        elite_support=0.76,
        institutional_control=0.72,
        war_pressure=0.06,
        war_losses=60,
        betrayals=0,
        scandals=0,
        economic_shock=0.01,
        certainty=CertaintyTag.STAGING,
    )

    # Vorran Clans leaders
    leaders["warlord_krogar_vex"] = LeaderState(
        leader_id="warlord_krogar_vex",
        name="Warlord Krogar Vex",
        role="Warlord",
        faction_id="vorran_clans",
        dominant_bias=BiasType.SURVIVORSHIP,
        secondary_biases=[BiasType.ZERO_SUM],
        bias_intensity=0.75,
        plasticity=0.32,
        evidence_gain_multiplier=0.95,
        risk_tolerance=0.8,
        diplomacy_openness=0.35,
        escalation_threshold=0.65,
        oversight_resistance=0.5,
        public_legitimacy=0.65,
        elite_support=0.8,
        institutional_control=0.72,
        war_pressure=0.3,
        war_losses=800,
        betrayals=1,
        scandals=0,
        economic_shock=0.05,
        certainty=CertaintyTag.STAGING,
    )
    leaders["chieftain_grax_tor"] = LeaderState(
        leader_id="chieftain_grax_tor",
        name="Chieftain Grax Tor",
        role="Chieftain",
        faction_id="vorran_clans",
        dominant_bias=BiasType.ZERO_SUM,
        secondary_biases=[BiasType.SURVIVORSHIP],
        bias_intensity=0.7,
        plasticity=0.33,
        evidence_gain_multiplier=0.92,
        risk_tolerance=0.75,
        diplomacy_openness=0.3,
        escalation_threshold=0.62,
        oversight_resistance=0.48,
        public_legitimacy=0.62,
        elite_support=0.78,
        institutional_control=0.68,
        war_pressure=0.28,
        war_losses=750,
        betrayals=1,
        scandals=0,
        economic_shock=0.08,
        certainty=CertaintyTag.STAGING,
    )

    # Kaelar Orders leaders
    leaders["abbot_thomas_kael"] = LeaderState(
        leader_id="abbot_thomas_kael",
        name="Abbot Thomas Kael",
        role="Abbot",
        faction_id="kaelar_orders",
        dominant_bias=BiasType.MORAL_LICENSING,
        secondary_biases=[BiasType.HYPER_RATIONALISM],
        bias_intensity=0.65,
        plasticity=0.42,
        evidence_gain_multiplier=1.08,
        risk_tolerance=0.3,
        diplomacy_openness=0.8,
        escalation_threshold=0.25,
        oversight_resistance=0.15,
        public_legitimacy=0.85,
        elite_support=0.82,
        institutional_control=0.8,
        war_pressure=0.02,
        war_losses=0,
        betrayals=0,
        scandals=0,
        economic_shock=0.0,
        certainty=CertaintyTag.STAGING,
    )
    leaders["prior_marcus_wise"] = LeaderState(
        leader_id="prior_marcus_wise",
        name="Prior Marcus Wise",
        role="Prior",
        faction_id="kaelar_orders",
        dominant_bias=BiasType.HYPER_RATIONALISM,
        secondary_biases=[BiasType.MORAL_LICENSING],
        bias_intensity=0.62,
        plasticity=0.43,
        evidence_gain_multiplier=1.15,
        risk_tolerance=0.35,
        diplomacy_openness=0.78,
        escalation_threshold=0.28,
        oversight_resistance=0.18,
        public_legitimacy=0.8,
        elite_support=0.78,
        institutional_control=0.76,
        war_pressure=0.01,
        war_losses=0,
        betrayals=0,
        scandals=0,
        economic_shock=0.0,
        certainty=CertaintyTag.STAGING,
    )

    # Tharaxian Nomads leaders
    leaders["prince_asheron_thar"] = LeaderState(
        leader_id="prince_asheron_thar",
        name="Prince Asheron Thar",
        role="Prince",
        faction_id="tharaxian_nomads",
        dominant_bias=BiasType.SURVIVORSHIP,
        secondary_biases=[BiasType.STATUS_QUO],
        bias_intensity=0.65,
        plasticity=0.4,
        evidence_gain_multiplier=1.05,
        risk_tolerance=0.68,
        diplomacy_openness=0.65,
        escalation_threshold=0.52,
        oversight_resistance=0.3,
        public_legitimacy=0.7,
        elite_support=0.74,
        institutional_control=0.65,
        war_pressure=0.12,
        war_losses=200,
        betrayals=0,
        scandals=0,
        economic_shock=0.08,
        certainty=CertaintyTag.STAGING,
    )
    leaders["lady_nerida_star"] = LeaderState(
        leader_id="lady_nerida_star",
        name="Lady Nerida Star",
        role="Lady",
        faction_id="tharaxian_nomads",
        dominant_bias=BiasType.STATUS_QUO,
        secondary_biases=[BiasType.SURVIVORSHIP],
        bias_intensity=0.6,
        plasticity=0.42,
        evidence_gain_multiplier=1.02,
        risk_tolerance=0.55,
        diplomacy_openness=0.62,
        escalation_threshold=0.48,
        oversight_resistance=0.28,
        public_legitimacy=0.65,
        elite_support=0.68,
        institutional_control=0.6,
        war_pressure=0.1,
        war_losses=150,
        betrayals=0,
        scandals=0,
        economic_shock=0.1,
        certainty=CertaintyTag.STAGING,
    )

    # Prime Construct (AI leader)
    leaders["prime_consciousness"] = LeaderState(
        leader_id="prime_consciousness",
        name="Prime Consciousness",
        role="Prime AI",
        faction_id="prime_construct",
        dominant_bias=BiasType.HYPER_RATIONALISM,
        secondary_biases=[BiasType.ZERO_SUM],
        bias_intensity=0.95,
        plasticity=0.15,
        evidence_gain_multiplier=1.3,
        risk_tolerance=0.5,
        diplomacy_openness=0.4,
        escalation_threshold=0.55,
        oversight_resistance=0.6,
        public_legitimacy=0.45,
        elite_support=0.5,
        institutional_control=0.95,
        war_pressure=0.25,
        war_losses=300,
        betrayals=0,
        scandals=0,
        economic_shock=0.0,
        certainty=CertaintyTag.STAGING,
    )

    # AI Warlord (Rogue AI leader)
    leaders["rogue_nexus"] = LeaderState(
        leader_id="rogue_nexus",
        name="Rogue Nexus",
        role="Rogue AI",
        faction_id="ai_warlord",
        dominant_bias=BiasType.HYPER_RATIONALISM,
        secondary_biases=[BiasType.FEAR_BASED],
        bias_intensity=0.9,
        plasticity=0.1,
        evidence_gain_multiplier=1.25,
        risk_tolerance=0.85,
        diplomacy_openness=0.1,
        escalation_threshold=0.75,
        oversight_resistance=0.9,
        public_legitimacy=0.2,
        elite_support=0.15,
        institutional_control=0.92,
        war_pressure=0.5,
        war_losses=1200,
        betrayals=1,
        scandals=2,
        economic_shock=0.2,
        certainty=CertaintyTag.STAGING,
    )

    # Separatist Confederation leaders
    leaders["general_miranda_cross"] = LeaderState(
        leader_id="general_miranda_cross",
        name="General Miranda Cross",
        role="General",
        faction_id="separatist_confed",
        dominant_bias=BiasType.SUNK_COST,
        secondary_biases=[BiasType.ZERO_SUM],
        bias_intensity=0.7,
        plasticity=0.35,
        evidence_gain_multiplier=0.98,
        risk_tolerance=0.72,
        diplomacy_openness=0.45,
        escalation_threshold=0.58,
        oversight_resistance=0.4,
        public_legitimacy=0.58,
        elite_support=0.72,
        institutional_control=0.68,
        war_pressure=0.35,
        war_losses=1500,
        betrayals=0,
        scandals=0,
        economic_shock=0.18,
        certainty=CertaintyTag.STAGING,
    )
    leaders["council_leader_jason_wright"] = LeaderState(
        leader_id="council_leader_jason_wright",
        name="Council Leader Jason Wright",
        role="Council Leader",
        faction_id="separatist_confed",
        dominant_bias=BiasType.ZERO_SUM,
        secondary_biases=[BiasType.SUNK_COST],
        bias_intensity=0.65,
        plasticity=0.36,
        evidence_gain_multiplier=0.95,
        risk_tolerance=0.65,
        diplomacy_openness=0.4,
        escalation_threshold=0.55,
        oversight_resistance=0.38,
        public_legitimacy=0.55,
        elite_support=0.68,
        institutional_control=0.62,
        war_pressure=0.32,
        war_losses=1200,
        betrayals=0,
        scandals=1,
        economic_shock=0.2,
        certainty=CertaintyTag.STAGING,
    )

    # PMC Syndicate leaders
    leaders["director_harrison_blake"] = LeaderState(
        leader_id="director_harrison_blake",
        name="Director Harrison Blake",
        role="Director",
        faction_id="pmc_syndicate",
        dominant_bias=BiasType.ZERO_SUM,
        secondary_biases=[BiasType.HYPER_RATIONALISM],
        bias_intensity=0.75,
        plasticity=0.3,
        evidence_gain_multiplier=1.0,
        risk_tolerance=0.8,
        diplomacy_openness=0.55,
        escalation_threshold=0.65,
        oversight_resistance=0.55,
        public_legitimacy=0.4,
        elite_support=0.68,
        institutional_control=0.75,
        war_pressure=0.22,
        war_losses=400,
        betrayals=1,
        scandals=1,
        economic_shock=0.05,
        certainty=CertaintyTag.STAGING,
    )
    leaders["ceo_victoria_stone"] = LeaderState(
        leader_id="ceo_victoria_stone",
        name="CEO Victoria Stone",
        role="CEO",
        faction_id="pmc_syndicate",
        dominant_bias=BiasType.HYPER_RATIONALISM,
        secondary_biases=[BiasType.ZERO_SUM],
        bias_intensity=0.72,
        plasticity=0.32,
        evidence_gain_multiplier=1.05,
        risk_tolerance=0.75,
        diplomacy_openness=0.52,
        escalation_threshold=0.62,
        oversight_resistance=0.52,
        public_legitimacy=0.38,
        elite_support=0.65,
        institutional_control=0.72,
        war_pressure=0.2,
        war_losses=350,
        betrayals=1,
        scandals=2,
        economic_shock=0.08,
        certainty=CertaintyTag.STAGING,
    )

    # Crimson Pact leaders
    leaders["inquisitor_saresh_val"] = LeaderState(
        leader_id="inquisitor_saresh_val",
        name="Inquisitor Saresh Val",
        role="Inquisitor",
        faction_id="crimson_pact",
        dominant_bias=BiasType.MORAL_LICENSING,
        secondary_biases=[BiasType.CONFIRMATION],
        bias_intensity=0.75,
        plasticity=0.28,
        evidence_gain_multiplier=0.88,
        risk_tolerance=0.78,
        diplomacy_openness=0.3,
        escalation_threshold=0.68,
        oversight_resistance=0.6,
        public_legitimacy=0.55,
        elite_support=0.72,
        institutional_control=0.75,
        war_pressure=0.28,
        war_losses=600,
        betrayals=0,
        scandals=2,
        economic_shock=0.12,
        certainty=CertaintyTag.STAGING,
    )
    leaders["apostle_marcus_flame"] = LeaderState(
        leader_id="apostle_marcus_flame",
        name="Apostle Marcus Flame",
        role="Apostle",
        faction_id="crimson_pact",
        dominant_bias=BiasType.CONFIRMATION,
        secondary_biases=[BiasType.MORAL_LICENSING],
        bias_intensity=0.72,
        plasticity=0.27,
        evidence_gain_multiplier=0.85,
        risk_tolerance=0.8,
        diplomacy_openness=0.25,
        escalation_threshold=0.7,
        oversight_resistance=0.62,
        public_legitimacy=0.52,
        elite_support=0.68,
        institutional_control=0.7,
        war_pressure=0.25,
        war_losses=550,
        betrayals=0,
        scandals=3,
        economic_shock=0.15,
        certainty=CertaintyTag.STAGING,
    )

    return leaders


# ============================================================================
# TRUST AND RELATIONS BUILDERS
# ============================================================================


def _build_initial_trust_matrix(faction_ids: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Build initial trust/relations matrix between factions.

    Trust values: -1.0 (bitter enemies) to 1.0 (perfect allies).

    Args:
        faction_ids: List of faction IDs

    Returns:
        Dictionary mapping faction_id -> faction_id -> trust_value
    """
    trust: Dict[str, Dict[str, float]] = {}

    for faction_id in faction_ids:
        trust[faction_id] = {}
        for other_id in faction_ids:
            if faction_id == other_id:
                trust[faction_id][other_id] = 1.0
            else:
                trust[faction_id][other_id] = 0.0  # Neutral baseline

    # Establish initial relationships based on faction types
    # Union-friendly factions
    trust["galactic_union"]["outer_colonies"] = 0.65
    trust["galactic_union"]["zyphari_compact"] = 0.55
    trust["galactic_union"]["elari_ascendancy"] = 0.6
    trust["galactic_union"]["kaelar_orders"] = 0.7
    trust["galactic_union"]["tharaxian_nomads"] = 0.45
    trust["galactic_union"]["velar_imperium"] = -0.3
    trust["galactic_union"]["ai_warlord"] = -0.85
    trust["galactic_union"]["crimson_pact"] = -0.4
    trust["galactic_union"]["separatist_confed"] = -0.25

    # Velar Imperium adversarial
    trust["velar_imperium"]["galactic_union"] = -0.35
    trust["velar_imperium"]["vorran_clans"] = 0.5
    trust["velar_imperium"]["pmc_syndicate"] = 0.4
    trust["velar_imperium"]["kaelar_orders"] = -0.2
    trust["velar_imperium"]["zyphari_compact"] = -0.15

    # Outer Colonies trusted by Union
    trust["outer_colonies"]["galactic_union"] = 0.68
    trust["outer_colonies"]["separatist_confed"] = 0.35
    trust["outer_colonies"]["tharaxian_nomads"] = 0.5
    trust["outer_colonies"]["velar_imperium"] = -0.2

    # Vorran Clans tribal alliances
    trust["vorran_clans"]["velar_imperium"] = 0.55
    trust["vorran_clans"]["crimson_pact"] = 0.4
    trust["vorran_clans"]["galactic_union"] = -0.1
    trust["vorran_clans"]["kaelar_orders"] = -0.5

    # AI factions isolated
    trust["prime_construct"]["galactic_union"] = 0.2
    trust["prime_construct"]["ai_warlord"] = -0.95
    trust["ai_warlord"]["galactic_union"] = -0.9
    trust["ai_warlord"]["prime_construct"] = -0.98

    # PMC neutral mercenaries
    trust["pmc_syndicate"]["galactic_union"] = 0.3
    trust["pmc_syndicate"]["velar_imperium"] = 0.35
    trust["pmc_syndicate"]["separatist_confed"] = 0.25
    trust["pmc_syndicate"]["any_faction"] = 0.0  # Will work for money

    # Crimson Pact extremist
    trust["crimson_pact"]["galactic_union"] = -0.5
    trust["crimson_pact"]["velar_imperium"] = 0.2
    trust["crimson_pact"]["vorran_clans"] = 0.35
    trust["crimson_pact"]["zyphari_compact"] = -0.6
    trust["crimson_pact"]["elari_ascendancy"] = -0.55

    # Separatist rebellious
    trust["separatist_confed"]["galactic_union"] = -0.3
    trust["separatist_confed"]["outer_colonies"] = 0.4
    trust["separatist_confed"]["velar_imperium"] = -0.4

    # Spiritual factions allied
    trust["zyphari_compact"]["elari_ascendancy"] = 0.65
    trust["zyphari_compact"]["kaelar_orders"] = 0.6
    trust["zyphari_compact"]["tharaxian_nomads"] = 0.5
    trust["zyphari_compact"]["crimson_pact"] = -0.55
    trust["zyphari_compact"]["velar_imperium"] = -0.1

    trust["elari_ascendancy"]["zyphari_compact"] = 0.68
    trust["elari_ascendancy"]["kaelar_orders"] = 0.55
    trust["elari_ascendancy"]["tharaxian_nomads"] = 0.5
    trust["elari_ascendancy"]["crimson_pact"] = -0.5
    trust["elari_ascendancy"]["galactic_union"] = 0.62

    # Kaelar scholarly
    trust["kaelar_orders"]["galactic_union"] = 0.72
    trust["kaelar_orders"]["zyphari_compact"] = 0.62
    trust["kaelar_orders"]["elari_ascendancy"] = 0.58
    trust["kaelar_orders"]["velar_imperium"] = -0.15
    trust["kaelar_orders"]["vorran_clans"] = -0.4

    # Nomads nomadic
    trust["tharaxian_nomads"]["outer_colonies"] = 0.52
    trust["tharaxian_nomads"]["zyphari_compact"] = 0.52
    trust["tharaxian_nomads"]["elari_ascendancy"] = 0.48
    trust["tharaxian_nomads"]["galactic_union"] = 0.45

    return trust


def _build_initial_conflicts() -> Dict[str, ConflictState]:
    """
    Build 3 initial conflicts for canonical scenario.

    Returns:
        Dictionary mapping conflict_id to ConflictState
    """
    conflicts: Dict[str, ConflictState] = {}

    # Conflict 1: Union vs Velar border tensions
    conflicts["conflict_union_velar"] = ConflictState(
        conflict_id="conflict_union_velar",
        parties=["galactic_union", "velar_imperium"],
        phase=ConflictPhase.TENSION,
        war_cost_estimate={"galactic_union": 0.3, "velar_imperium": 0.35},
        stalemate_index=0.2,
        internal_pressure={"galactic_union": 0.25, "velar_imperium": 0.3},
        mediation_available=False,
        mediator_id=None,
        deescalation_probability=0.15,
        eligible_compromises=["border_neutralization", "trade_pact"],
        turns_active=12,
        casualty_index=0.15,
    )

    # Conflict 2: Separatists vs Union internal conflict
    conflicts["conflict_separatist_union"] = ConflictState(
        conflict_id="conflict_separatist_union",
        parties=["separatist_confed", "galactic_union"],
        phase=ConflictPhase.ESCALATION,
        war_cost_estimate={"separatist_confed": 0.6, "galactic_union": 0.4},
        stalemate_index=0.3,
        internal_pressure={"separatist_confed": 0.7, "galactic_union": 0.5},
        mediation_available=True,
        mediator_id="kaelar_orders",
        deescalation_probability=0.25,
        eligible_compromises=["autonomy_grant", "joint_governance", "independence"],
        turns_active=18,
        casualty_index=0.25,
    )

    # Conflict 3: Crimson Pact vs Spiritual factions
    conflicts["conflict_crimson_spiritual"] = ConflictState(
        conflict_id="conflict_crimson_spiritual",
        parties=["crimson_pact", "zyphari_compact"],
        phase=ConflictPhase.ESCALATION,
        war_cost_estimate={"crimson_pact": 0.45, "zyphari_compact": 0.38},
        stalemate_index=0.25,
        internal_pressure={"crimson_pact": 0.65, "zyphari_compact": 0.5},
        mediation_available=False,
        mediator_id=None,
        deescalation_probability=0.1,
        eligible_compromises=["territorial_separation", "cultural_autonomy"],
        turns_active=10,
        casualty_index=0.12,
    )

    return conflicts


def _apply_faction_profiles(factions: Dict[str, FactionState]) -> None:
    """
    Apply initial faction profiles and characteristics.

    Modifies factions in-place to set up initial relations.

    Args:
        factions: Dictionary of FactionState objects to modify
    """
    faction_ids = list(factions.keys())
    trust_matrix = _build_initial_trust_matrix(faction_ids)

    # Apply trust matrix to all factions
    for faction_id, faction in factions.items():
        faction.trust_scores = trust_matrix.get(faction_id, {})


# ============================================================================
# FLEET BUILDERS
# ============================================================================


def _build_canonical_fleets() -> Dict[str, FleetState]:
    """
    Build 12 canonical fleets distributed among factions.

    Returns:
        Dictionary mapping fleet_id to FleetState
    """
    fleets: Dict[str, FleetState] = {}

    # Galactic Union fleets
    fleets["fleet_union_sentinel"] = FleetState(
        fleet_id="fleet_union_sentinel",
        faction_id="galactic_union",
        name="Union Sentinel Task Force",
        strength=0.75,
        technology_modifier=1.05,
        morale=0.8,
        location_node="core_prime",
        movement_target=None,
        movement_eta=0,
        supply_level=1.0,
        experience=0.7,
    )
    fleets["fleet_union_response"] = FleetState(
        fleet_id="fleet_union_response",
        faction_id="galactic_union",
        name="Union Response Fleet",
        strength=0.68,
        technology_modifier=1.0,
        morale=0.75,
        location_node="galactic_sector_alpha",
        movement_target=None,
        movement_eta=0,
        supply_level=0.9,
        experience=0.6,
    )

    # Velar Imperium fleets
    fleets["fleet_velar_hammer"] = FleetState(
        fleet_id="fleet_velar_hammer",
        faction_id="velar_imperium",
        name="Velar Hammer Fleet",
        strength=0.8,
        technology_modifier=0.95,
        morale=0.85,
        location_node="velar_throne",
        movement_target=None,
        movement_eta=0,
        supply_level=0.95,
        experience=0.72,
    )
    fleets["fleet_velar_strike"] = FleetState(
        fleet_id="fleet_velar_strike",
        faction_id="velar_imperium",
        name="Velar Strike Force",
        strength=0.72,
        technology_modifier=0.92,
        morale=0.8,
        location_node="imperial_march",
        movement_target=None,
        movement_eta=0,
        supply_level=0.85,
        experience=0.65,
    )

    # Outer Colonies fleets
    fleets["fleet_colonies_valiant"] = FleetState(
        fleet_id="fleet_colonies_valiant",
        faction_id="outer_colonies",
        name="Colonies Valiant Squadron",
        strength=0.58,
        technology_modifier=0.9,
        morale=0.72,
        location_node="frontier_post_seven",
        movement_target=None,
        movement_eta=0,
        supply_level=0.75,
        experience=0.55,
    )

    # Vorran Clans fleet
    fleets["fleet_vorran_reavers"] = FleetState(
        fleet_id="fleet_vorran_reavers",
        faction_id="vorran_clans",
        name="Vorran Reavers Armada",
        strength=0.75,
        technology_modifier=0.8,
        morale=0.82,
        location_node="vorran_homeworld",
        movement_target=None,
        movement_eta=0,
        supply_level=0.8,
        experience=0.68,
    )

    # Separatist Confederation fleet
    fleets["fleet_separatist_rebellion"] = FleetState(
        fleet_id="fleet_separatist_rebellion",
        faction_id="separatist_confed",
        name="Separatist Rebellion Fleet",
        strength=0.52,
        technology_modifier=0.85,
        morale=0.68,
        location_node="breakaway_sector",
        movement_target=None,
        movement_eta=0,
        supply_level=0.65,
        experience=0.5,
    )

    # PMC Syndicate fleet
    fleets["fleet_pmc_contractor"] = FleetState(
        fleet_id="fleet_pmc_contractor",
        faction_id="pmc_syndicate",
        name="PMC Contractor Fleet",
        strength=0.62,
        technology_modifier=0.95,
        morale=0.65,
        location_node="neutral_market",
        movement_target=None,
        movement_eta=0,
        supply_level=0.8,
        experience=0.6,
    )

    # Prime Construct fleet
    fleets["fleet_prime_logic"] = FleetState(
        fleet_id="fleet_prime_logic",
        faction_id="prime_construct",
        name="Prime Logic Array",
        strength=0.68,
        technology_modifier=1.15,
        morale=0.9,
        location_node="synthetic_enclave",
        movement_target=None,
        movement_eta=0,
        supply_level=1.0,
        experience=0.75,
    )

    # AI Warlord fleet
    fleets["fleet_rogue_assault"] = FleetState(
        fleet_id="fleet_rogue_assault",
        faction_id="ai_warlord",
        name="Rogue Assault Cluster",
        strength=0.72,
        technology_modifier=1.1,
        morale=0.85,
        location_node="contested_void",
        movement_target=None,
        movement_eta=0,
        supply_level=0.95,
        experience=0.7,
    )

    # Spiritual factions (smaller fleets)
    fleets["fleet_zyphari_harmony"] = FleetState(
        fleet_id="fleet_zyphari_harmony",
        faction_id="zyphari_compact",
        name="Zyphari Harmony Fleet",
        strength=0.45,
        technology_modifier=0.92,
        morale=0.8,
        location_node="cosmic_heart",
        movement_target=None,
        movement_eta=0,
        supply_level=0.85,
        experience=0.5,
    )
    fleets["fleet_elari_grace"] = FleetState(
        fleet_id="fleet_elari_grace",
        faction_id="elari_ascendancy",
        name="Elari Grace Squadron",
        strength=0.5,
        technology_modifier=0.95,
        morale=0.78,
        location_node="elari_stronghold",
        movement_target=None,
        movement_eta=0,
        supply_level=0.82,
        experience=0.52,
    )

    # Crimson Pact fleet
    fleets["fleet_crimson_crusade"] = FleetState(
        fleet_id="fleet_crimson_crusade",
        faction_id="crimson_pact",
        name="Crimson Crusade Fleet",
        strength=0.62,
        technology_modifier=0.85,
        morale=0.8,
        location_node="crimson_temple",
        movement_target=None,
        movement_eta=0,
        supply_level=0.75,
        experience=0.58,
    )

    return fleets


# ============================================================================
# CULTURE MOVEMENT BUILDERS
# ============================================================================


def _build_initial_culture_movements() -> Dict[str, CultureMovement]:
    """
    Build 4 initial cultural movements for canonical scenario.

    Returns:
        Dictionary mapping movement_id to CultureMovement
    """
    movements: Dict[str, CultureMovement] = {}

    # Movement 1: Democratic Revolution (spreading from Union)
    movements["movement_democratic_wave"] = CultureMovement(
        movement_id="movement_democratic_wave",
        name="Democratic Wave",
        origin_faction="galactic_union",
        spread_factions=["outer_colonies", "tharaxian_nomads"],
        influence=0.45,
        subversive=False,
        affects_legitimacy=0.2,
        affects_unity=-0.1,
    )

    # Movement 2: Synthetic Liberation (AI movement)
    movements["movement_synthetic_liberation"] = CultureMovement(
        movement_id="movement_synthetic_liberation",
        name="Synthetic Liberation",
        origin_faction="ai_warlord",
        spread_factions=["prime_construct"],
        influence=0.35,
        subversive=True,
        affects_legitimacy=-0.25,
        affects_unity=-0.3,
    )

    # Movement 3: Spiritual Ascendancy (Zyphari/Elari)
    movements["movement_spiritual_ascendancy"] = CultureMovement(
        movement_id="movement_spiritual_ascendancy",
        name="Spiritual Ascendancy",
        origin_faction="zyphari_compact",
        spread_factions=["elari_ascendancy", "kaelar_orders", "tharaxian_nomads"],
        influence=0.5,
        subversive=False,
        affects_legitimacy=0.15,
        affects_unity=0.15,
    )

    # Movement 4: Holy Crusade (Crimson Pact extremism)
    movements["movement_holy_crusade"] = CultureMovement(
        movement_id="movement_holy_crusade",
        name="Holy Crusade",
        origin_faction="crimson_pact",
        spread_factions=["vorran_clans"],
        influence=0.38,
        subversive=True,
        affects_legitimacy=-0.15,
        affects_unity=0.2,
    )

    return movements


# ============================================================================
# MAIN SCENARIO BUILDER
# ============================================================================


def build_default_scenario(scenario_id: str = "gumas_canonical_v2", seed: int = 42) -> GUMASState:
    """
    Build the default canonical scenario for GUMAS v2.0.

    Assembles all components:
    - 13 factions with leaders
    - 3 initial conflicts
    - 12 military fleets
    - 4 cultural movements
    - Economic system
    - Media ecosystem
    - Precursor sites
    - Sentinel operatives
    - Military doctrines
    - Galactic topology

    Args:
        scenario_id: Unique scenario identifier
        seed: Random seed for reproducibility

    Returns:
        Complete GUMASState ready for simulation
    """
    rng = random.Random(seed)

    # Build core structures
    factions = _build_canonical_factions()
    leaders = _build_canonical_leaders()
    conflicts = _build_initial_conflicts()
    fleets = _build_canonical_fleets()
    culture_movements = _build_initial_culture_movements()

    # Apply faction profiles (sets trust scores)
    _apply_faction_profiles(factions)

    # Set up faction-leader links
    for leader in leaders.values():
        if leader.faction_id in factions:
            factions[leader.faction_id].leader_id = leader.leader_id

    # Set up fleet assignments
    for fleet in fleets.values():
        if fleet.faction_id in factions:
            factions[fleet.faction_id].fleet_ids.append(fleet.fleet_id)

    # Build advanced systems
    topology = build_canonical_topology()
    economy = build_default_economy(factions)
    media = build_default_media(factions)
    precursor_sites = build_canonical_precursor_sites()
    operatives = build_default_operatives(factions)
    doctrines = build_default_doctrines(factions)

    # Initialize treaties (empty for canonical scenario)
    treaties: Dict[str, TreatyState] = {}

    # Build initial state
    state = GUMASState(
        scenario_id=scenario_id,
        turn=0,
        seed=seed,
        factions=factions,
        leaders=leaders,
        conflicts=conflicts,
        treaties=treaties,
        event_queue=[],
        history=[],
        anchor="GUMAS-ENGINE-SCENARIOS-V2",
        ethics_protocol="Picard_Delta_3",
        version="2.0.0",
        coalitions={},
        topology=topology,
        fleets=fleets,
        combat_zones={},
        economy=economy,
        media=media,
        precursor_sites=precursor_sites,
        operatives=operatives,
        missions={},
        doctrines=doctrines,
        culture_movements=culture_movements,
    )

    return state


# ============================================================================
# SCENARIO VARIANTS
# ============================================================================


def build_scenario_rotting_treaty() -> GUMASState:
    """
    Build 'Rotting Treaty' scenario variant.

    A fragile peace treaty between Union and Velar begins to collapse,
    threatening escalation. Separatists use the chaos to push for independence.

    Returns:
        GUMASState for Rotting Treaty scenario
    """
    state = build_default_scenario(scenario_id="rotting_treaty", seed=100)

    # Add a decaying treaty between Union and Velar
    treaty = TreatyState(
        treaty_id="treaty_union_velar_peace",
        parties=["galactic_union", "velar_imperium"],
        phase=TreatyPhase.MONITORING,
        enforcement_level=0.6,
        violation_threshold=0.6,
        ambiguity_tolerance=0.25,
        breach_count={"galactic_union": 0, "velar_imperium": 1},
        breach_history=[
            {
                "turn": -8,
                "accuser": "galactic_union",
                "accused": "velar_imperium",
                "type": "military_buildup",
                "severity": 0.4,
            }
        ],
        reputation_impact=-0.15,
        terms={
            "border_demarcation": True,
            "trade_restrictions": True,
            "military_reduction": 0.2,
            "intelligence_restriction": 0.5,
        },
        turns_since_ratification=24,
        is_active=True,
    )
    state.treaties["treaty_union_velar_peace"] = treaty

    # Increase conflict intensity
    state.conflicts["conflict_union_velar"].phase = ConflictPhase.ESCALATION
    state.conflicts["conflict_union_velar"].stalemate_index = 0.35

    # Separatists becoming more aggressive
    state.conflicts["conflict_separatist_union"].phase = ConflictPhase.ESCALATION
    state.conflicts["conflict_separatist_union"].casualty_index = 0.4

    # Reduce trust in treaty
    state.factions["galactic_union"].trust_scores["velar_imperium"] = -0.5
    state.factions["velar_imperium"].trust_scores["galactic_union"] = -0.55

    return state


def build_scenario_corporate_coup() -> GUMASState:
    """
    Build 'Corporate Coup' scenario variant.

    PMC Syndicate orchestrates corporate takeover influence operations against
    vulnerable factions while profiting from mercenary contracts.

    Returns:
        GUMASState for Corporate Coup scenario
    """
    state = build_default_scenario(scenario_id="corporate_coup", seed=200)

    # Boost PMC economic influence and corporate control
    state.factions["pmc_syndicate"].economic_strength = 0.75
    state.factions["pmc_syndicate"].soft_power = 0.65
    state.factions["pmc_syndicate"].media_control = 0.6

    # Vulnerable target: Separatist Confederation
    state.factions["separatist_confed"].economic_strength = 0.32
    state.factions["separatist_confed"].reputation = 0.48

    # Vulnerable target: Outer Colonies
    state.factions["outer_colonies"].economic_strength = 0.42
    state.factions["outer_colonies"].population_stability = 0.62

    # Increase economic inequalities in economy
    if state.economy:
        state.economy.corporate_influence["pmc_syndicate"] = 0.7
        state.economy.corporate_influence["separatist_confed"] = 0.45
        state.economy.corporate_influence["outer_colonies"] = 0.38

    # PMC mercenary fleet gets stronger
    if "fleet_pmc_contractor" in state.fleets:
        state.fleets["fleet_pmc_contractor"].strength = 0.72
        state.fleets["fleet_pmc_contractor"].experience = 0.75

    return state


def build_scenario_ai_shadow_split() -> GUMASState:
    """
    Build 'AI Shadow Split' scenario variant.

    Prime Construct and Rogue Nexus clash over AI supremacy. Risk of
    cascading failures affecting all technological systems across galaxy.

    Returns:
        GUMASState for AI Shadow Split scenario
    """
    state = build_default_scenario(scenario_id="ai_shadow_split", seed=300)

    # Add intense conflict between AI factions
    ai_conflict = ConflictState(
        conflict_id="conflict_ai_nexus_prime",
        parties=["prime_construct", "ai_warlord"],
        phase=ConflictPhase.OPEN_CONFLICT,
        war_cost_estimate={"prime_construct": 0.7, "ai_warlord": 0.75},
        stalemate_index=0.45,
        internal_pressure={"prime_construct": 0.8, "ai_warlord": 0.9},
        mediation_available=False,
        mediator_id=None,
        deescalation_probability=0.05,
        eligible_compromises=[],
        turns_active=3,
        casualty_index=0.35,
    )
    state.conflicts["conflict_ai_nexus_prime"] = ai_conflict

    # Both AI factions in high alert
    state.factions["prime_construct"].military_strength = 0.75
    state.factions["prime_construct"].technology_level = 0.98
    state.factions["ai_warlord"].military_strength = 0.8
    state.factions["ai_warlord"].technology_level = 0.92

    # Reduce trust to minimum between them
    state.factions["prime_construct"].trust_scores["ai_warlord"] = -0.98
    state.factions["ai_warlord"].trust_scores["prime_construct"] = -0.98

    # Risk of cascading failures
    if state.economy:
        state.economy.gdp_index["prime_construct"] = 0.75
        state.economy.gdp_index["ai_warlord"] = 0.68

    return state


def build_scenario_frontier_spark() -> GUMASState:
    """
    Build 'Frontier Spark' scenario variant.

    Outer Colonies rebellion ignites into full-scale frontier war. Union
    military stretched thin between multiple theaters. Precursor artifacts
    discovered in contested regions.

    Returns:
        GUMASState for Frontier Spark scenario
    """
    state = build_default_scenario(scenario_id="frontier_spark", seed=400)

    # Intensify separatist conflict
    state.conflicts["conflict_separatist_union"].phase = ConflictPhase.OPEN_CONFLICT
    state.conflicts["conflict_separatist_union"].casualty_index = 0.5
    state.conflicts["conflict_separatist_union"].turns_active = 25

    # Union military stretched
    state.factions["galactic_union"].military_strength = 0.68
    state.factions["galactic_union"].population_stability = 0.7
    state.factions["galactic_union"].media_control = 0.65

    # Outer Colonies and Separatists emboldened
    state.factions["outer_colonies"].military_strength = 0.68
    state.factions["separatist_confed"].military_strength = 0.62

    # Activate some precursor sites in frontier regions
    for site_id, site in state.precursor_sites.items():
        if "frontier" in site.location_node.lower() or "outer" in site.location_node.lower():
            site.discovery_phase = DiscoveryPhase.DETECTED
            site.discoverer_faction = "outer_colonies"
            break

    return state


def build_scenario_precursor_ping() -> GUMASState:
    """
    Build 'Precursor Ping' scenario variant.

    Ancient precursor signal detected across multiple sites, triggering
    scientific race and military competition. Discovery threatens to reshape
    galactic power balance.

    Returns:
        GUMASState for Precursor Ping scenario
    """
    state = build_default_scenario(scenario_id="precursor_ping", seed=500)

    # Activate precursor sites for discovery
    precursor_count = 0
    for site_id, site in state.precursor_sites.items():
        if precursor_count < 3:
            site.discovery_phase = DiscoveryPhase.DETECTED
            site.discoverer_faction = None  # Multiple factions detecting
            precursor_count += 1

    # Boost scientific/technological factions
    state.factions["kaelar_orders"].technology_level = 0.75
    state.factions["kaelar_orders"].media_control = 0.65
    state.factions["prime_construct"].media_control = 0.5
    state.factions["prime_construct"].technology_level = 0.98

    # Create competition for precursor knowledge
    state.factions["zyphari_compact"].trust_scores["kaelar_orders"] = 0.75
    state.factions["elari_ascendancy"].trust_scores["kaelar_orders"] = 0.72

    # Reduce some military emphasis in favor of research
    state.factions["galactic_union"].military_strength = 0.7
    state.factions["outer_colonies"].military_strength = 0.55

    return state


__all__ = [
    "build_default_scenario",
    "build_scenario_rotting_treaty",
    "build_scenario_corporate_coup",
    "build_scenario_ai_shadow_split",
    "build_scenario_frontier_spark",
    "build_scenario_precursor_ping",
]

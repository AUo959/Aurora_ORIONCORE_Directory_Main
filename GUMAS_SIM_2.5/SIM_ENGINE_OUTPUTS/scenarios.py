#!/usr/bin/env python3
"""
GUMAS L2 Canonical Scenario Loader
====================================
Anchor: GUMAS-ENGINE-SCENARIOS-V1
Seed: EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP: L2_ENGINE_CORE
Version: 1.0.0

Loads canonical GUMAS scenarios from Runtime Reference Packet entity
data. Provides the default galactic state that the engine initializes
with, including all 13 polities, their leaders, and initial
relationship matrices.

This module is the bridge between the L2 design documents and the
running engine. Entity definitions below are transcribed verbatim
from the Runtime Reference Packet v0.4 Section 3 and the L2 GUMAS
Staging Dossier.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from models import (
    BiasType,
    CertaintyTag,
    ConflictPhase,
    ConflictState,
    FactionState,
    FactionType,
    GUMASState,
    LeaderState,
)


# ============================================================================
# CANONICAL FACTIONS (Runtime Reference Packet v0.4, Section 3.1)
# ============================================================================

def _build_canonical_factions() -> Dict[str, FactionState]:
    """Build the 13 canonical polities from the Runtime Reference Packet."""
    raw = [
        ("galactic_union", "Galactic Union", FactionType.FEDERATION,
         "Core interstellar polity; Senate governance; internal blocs."),
        ("velar_imperium", "Velar Imperium", FactionType.AUTHORITARIAN,
         "Divide-and-rule internal factionalism; realism-first authoritarian dynamics."),
        ("outer_colonies", "Outer Colonies Confederation", FactionType.FRONTIER_CONFEDERATION,
         "Decentralized breakaway space; pirate-capital integration in some regions."),
        ("zyphari_compact", "Zyphari Compact", FactionType.CORPORATE_OLIGARCHY,
         "Trade coalitions, financial warfare, Algorithmic Prose culture."),
        ("elari_ascendancy", "Elari Ascendancy", FactionType.CULTURAL_SPIRITUAL,
         "Celestial Abstraction; Symmetry Doctrine influence."),
        ("vorran_clans", "Vorran Clans", FactionType.CLAN_CONFEDERATION,
         "Resonance Sculpture; communal identity emphasis."),
        ("kaelar_orders", "Kaelar Monastic Orders", FactionType.MONASTIC_NETWORK,
         "Perfect Uncertainty; Organic Ink Histories."),
        ("tharaxian_nomads", "Tharaxian Nomads", FactionType.NOMADIC_DIASPORA,
         "Silent Poetry; gesture/light/bio-signal communication forms."),
        ("prime_construct", "Prime Construct Polity", FactionType.SOVEREIGN_AI,
         "Logic-driven diplomacy; contested organic reception."),
        ("ai_warlord", "AI-Warlord Collective", FactionType.ROGUE_SYNTHETIC,
         "Nemesis Core Intelligence leadership; mixed wings."),
        ("separatist_confed", "Separatist Confederation", FactionType.BREAKAWAY_BLOC,
         "Moderate vs hardline splinters possible."),
        ("pmc_syndicate", "PMC Syndicate", FactionType.PMC,
         "Security-for-profit; intelligence branch."),
        ("crimson_pact", "Crimson Pact", FactionType.MILITANT_SPIRITUAL,
         "War-chaplain leadership; zeal-driven doctrine."),
    ]

    factions: Dict[str, FactionState] = {}
    for fid, name, ftype, notes in raw:
        factions[fid] = FactionState(
            faction_id=fid,
            name=name,
            faction_type=ftype,
            notes=notes,
            certainty=CertaintyTag.STAGING,
        )
    return factions


# ============================================================================
# CANONICAL LEADERS (Runtime Reference Packet v0.4, Section 3.3)
# ============================================================================

def _build_canonical_leaders() -> Dict[str, LeaderState]:
    """
    Build all faction leaders with bias assignments.

    Sources:
      - Character Roster (Appendix 18, Origin Thread Dossier)
      - L2 Runtime Reference Packet v0.4 (Section 3.3)
      - Staging Dossier: Velar Imperium deep-dive
      - Engine-generated STAGING leaders for 5 undocumented factions
        (Zyphari, Elari, Vorran, Kaelar, Tharaxian) using naming
        conventions from the factional linguistic protocol.

    Every faction gets a primary leader so bias-driven behavior
    fires galaxy-wide. The simulation generates canon.
    """
    raw = [
        # ============================================================
        # GALACTIC UNION — documented in Character Roster 18.1
        # ============================================================
        ("zylox_rhaegos", "Chancellor Zylox Rhaegos",
         "Supreme Chancellor of the Galactic Union",
         "galactic_union", BiasType.STATUS_QUO),
        ("kael_durn", "General Kael Durn",
         "Supreme Military Commander, GU Armed Forces",
         "galactic_union", BiasType.SUNK_COST),
        ("lirian_vael_torin", "Grand Strategist Lirian Vael-Torin",
         "Covert Military Advisor to Chancellor Zylox",
         "galactic_union", BiasType.CONFIRMATION),
        ("varek_norr", "Director Varek Norr",
         "Director of the Office of Strategic Diplomacy (OSD)",
         "galactic_union", BiasType.HYPER_RATIONALISM),
        ("vael_saros", "Chief Marshal Vael Saros",
         "Leader of the Union Marshals",
         "galactic_union", BiasType.MORAL_LICENSING),
        ("renn_valcor", "High Chancellor Renn Valcor",
         "Speaker of the Union Senate",
         "galactic_union", BiasType.STATUS_QUO),
        ("selene_arcturus", "Admiral Selene Arcturus",
         "Commander of the Union Naval Forces",
         "galactic_union", BiasType.SURVIVORSHIP),
        ("callan_deyrus", "Director Callan Deyrus",
         "Head of Union Intelligence Bureau (UIB)",
         "galactic_union", BiasType.HYPER_RATIONALISM),
        ("anaya_ral_seyr", "Minister Anaya Ral-Seyr",
         "Minister of Trade & Economy",
         "galactic_union", BiasType.CONFIRMATION),

        # ============================================================
        # VELAR IMPERIUM — documented in Staging Dossier Section 16.1
        # Lord Marshal Virex Tal'Varen: "maintains power via
        # factional rivalry" → ZERO_SUM (win/loss absolutism;
        # divide-and-rule requires it)
        # ============================================================
        ("virex_talvaren", "Lord Marshal Virex Tal'Varen",
         "Supreme military-political strongman; divide-and-rule architect",
         "velar_imperium", BiasType.ZERO_SUM),

        # ============================================================
        # OUTER COLONIES — documented in Staging Dossier (Velar section)
        # Pirate Queen: "mobile fortress / refugee ship / black-market
        # hub" → SURVIVORSHIP (overconfidence from past survival)
        # ============================================================
        ("theryn_kaelvakar", "Pirate Queen Theryn Kael'Vakar",
         "Confederation Leader; captain of the Khar'Thyrix",
         "outer_colonies", BiasType.SURVIVORSHIP),

        # ============================================================
        # SEPARATIST CONFEDERATION — documented in Roster 18.3
        # Military leader: committed to breakaway → SUNK_COST
        # ============================================================
        ("rhaegon_torr_kai", "Supreme Commander Rhaegon Torr-Kai",
         "Military Leader of the Separatist Confederation",
         "separatist_confed", BiasType.SUNK_COST),

        # ============================================================
        # AI-WARLORD COLLECTIVE — documented in Roster 18.3
        # AI Overlord: pure logic → HYPER_RATIONALISM
        # ============================================================
        ("nemesis_core", "Nemesis Core Intelligence",
         "AI Overlord of the AI-Warlord Collective",
         "ai_warlord", BiasType.HYPER_RATIONALISM),

        # ============================================================
        # PRIME CONSTRUCT POLITY — documented in Roster 18.1
        # ============================================================
        ("prime_construct_leader", "Prime Construct",
         "AI Sovereign Entity",
         "prime_construct", BiasType.HYPER_RATIONALISM),

        # ============================================================
        # PMC SYNDICATE — documented in Roster 18.3
        # CEO/military: profit justifies all → MORAL_LICENSING
        # ============================================================
        ("vailen_rix", "Executive Commander Vailen Rix",
         "CEO & Military Leader of PMC Syndicate",
         "pmc_syndicate", BiasType.MORAL_LICENSING),

        # ============================================================
        # CRIMSON PACT — documented in Roster 18.3
        # War-chaplain: zeal-driven, defensive doctrine → FEAR_BASED
        # ============================================================
        ("malrik_voska", "Supreme War-Chaplain Malrik Voska",
         "Spiritual & Military Leader of the Crimson Pact",
         "crimson_pact", BiasType.FEAR_BASED),

        # ============================================================
        # ZYPHARI COMPACT — No documented leader.
        # STAGING: corporate oligarchy, Algorithmic Prose culture,
        # predictive media → CONFIRMATION (corporate echo chamber,
        # filters contradictory market signals).
        # Name follows Zyphari convention: guild-syllable structures.
        # ============================================================
        ("qellan_vyss", "Board Sovereign Qellan Vyss",
         "Chairman of the Zyphari Compact Governing Board",
         "zyphari_compact", BiasType.CONFIRMATION),

        # ============================================================
        # ELARI ASCENDANCY — No documented leader.
        # STAGING: cultural-spiritual polity, Celestial Abstraction,
        # Symmetry Doctrine → STATUS_QUO (sacred traditions resist
        # disruption).
        # Name follows Elari convention: flowing vowels, luminous.
        # ============================================================
        ("aelindra_voss_aurai", "Luminary Aelindra Voss-Aurai",
         "High Luminary of the Elari Ascendancy",
         "elari_ascendancy", BiasType.STATUS_QUO),

        # ============================================================
        # VORRAN CLANS — No documented leader.
        # STAGING: clan confederation, communal identity emphasis,
        # Resonance Sculpture → ZERO_SUM (clan loyalty: with us
        # or against us).
        # Name follows Vorran convention: resonant consonants, communal.
        # ============================================================
        ("drenn_korvath", "Resonance Chief Drenn Korvath",
         "First Chief of the Vorran Clan Council",
         "vorran_clans", BiasType.ZERO_SUM),

        # ============================================================
        # KAELAR MONASTIC ORDERS — No documented leader.
        # STAGING: monastic skeptics, Perfect Uncertainty, Organic Ink
        # Histories → STATUS_QUO (institutional inertia of monastic
        # orders, even those professing uncertainty).
        # Name follows Kaelar convention: archival, deliberate.
        # ============================================================
        ("thessa_nai_oruun", "Elder Inscriber Thessa Nai-Oruun",
         "Keeper of the First Archive, Kaelar Monastic Orders",
         "kaelar_orders", BiasType.STATUS_QUO),

        # ============================================================
        # THARAXIAN NOMADS — No documented leader.
        # STAGING: nomadic diaspora, Silent Poetry, gesture/light
        # communication → SURVIVORSHIP (trust what kept the drift
        # alive; adapt from proven patterns).
        # Name follows Tharaxian convention: soft sibilants, drift.
        # ============================================================
        ("sivaen_the_driftcaller", "Driftcaller Sivaen",
         "Voice of the Tharaxian Migration Council",
         "tharaxian_nomads", BiasType.SURVIVORSHIP),
    ]

    leaders: Dict[str, LeaderState] = {}
    for lid, name, role, faction_id, bias in raw:
        leaders[lid] = LeaderState(
            leader_id=lid,
            name=name,
            role=role,
            faction_id=faction_id,
            dominant_bias=bias,
            certainty=CertaintyTag.STAGING,
        )

    return leaders


# ============================================================================
# INITIAL TRUST MATRIX
# ============================================================================

def _build_initial_trust_matrix(
    faction_ids: List[str],
) -> Dict[str, Dict[str, float]]:
    """
    Build initial bilateral trust scores.

    Design: start with 0.5 (neutral) and apply structural adjustments
    based on documented faction relationships.
    """
    trust: Dict[str, Dict[str, float]] = {}
    for fid in faction_ids:
        trust[fid] = {other: 0.5 for other in faction_ids if other != fid}

    # Structural adjustments from dossier lore
    adjustments = [
        # Allies / positive
        ("galactic_union", "elari_ascendancy", 0.15),
        ("galactic_union", "vorran_clans", 0.10),
        ("elari_ascendancy", "vorran_clans", 0.20),  # Symmetry Doctrine allies
        ("galactic_union", "kaelar_orders", 0.05),
        ("galactic_union", "tharaxian_nomads", 0.05),

        # Rivals / negative
        ("galactic_union", "velar_imperium", -0.20),
        ("galactic_union", "ai_warlord", -0.30),
        ("galactic_union", "separatist_confed", -0.15),
        ("galactic_union", "crimson_pact", -0.10),
        ("velar_imperium", "separatist_confed", -0.10),
        ("prime_construct", "ai_warlord", -0.25),  # Contested AI sovereignty

        # Commercial / transactional
        ("zyphari_compact", "pmc_syndicate", 0.10),
        ("zyphari_compact", "galactic_union", -0.05),  # economic friction
        ("pmc_syndicate", "velar_imperium", 0.05),     # client relationship

        # Neutral-leaning
        ("kaelar_orders", "tharaxian_nomads", 0.10),  # philosophical alignment
        ("outer_colonies", "separatist_confed", 0.10),  # autonomy sympathy
    ]

    for fid_a, fid_b, delta in adjustments:
        if fid_a in trust and fid_b in trust.get(fid_a, {}):
            trust[fid_a][fid_b] = max(0.0, min(1.0, trust[fid_a][fid_b] + delta))
        if fid_b in trust and fid_a in trust.get(fid_b, {}):
            trust[fid_b][fid_a] = max(0.0, min(1.0, trust[fid_b][fid_a] + delta))

    return trust


# ============================================================================
# INITIAL CONFLICTS
# ============================================================================

def _build_initial_conflicts() -> Dict[str, ConflictState]:
    """Seed the galaxy with canonical tension points."""
    return {
        "union_imperium_border": ConflictState(
            conflict_id="union_imperium_border",
            parties=["galactic_union", "velar_imperium"],
            phase=ConflictPhase.TENSION,
            war_cost_estimate={"galactic_union": 0.3, "velar_imperium": 0.4},
            stalemate_index=0.2,
            internal_pressure={"galactic_union": 0.2, "velar_imperium": 0.3},
        ),
        "ai_sovereignty_crisis": ConflictState(
            conflict_id="ai_sovereignty_crisis",
            parties=["galactic_union", "prime_construct", "ai_warlord"],
            phase=ConflictPhase.ESCALATION,
            war_cost_estimate={
                "galactic_union": 0.2,
                "prime_construct": 0.1,
                "ai_warlord": 0.5,
            },
            stalemate_index=0.1,
            internal_pressure={
                "galactic_union": 0.4,
                "prime_construct": 0.1,
                "ai_warlord": 0.2,
            },
        ),
        "separatist_tension": ConflictState(
            conflict_id="separatist_tension",
            parties=["galactic_union", "separatist_confed"],
            phase=ConflictPhase.TENSION,
            war_cost_estimate={"galactic_union": 0.1, "separatist_confed": 0.6},
            stalemate_index=0.0,
            internal_pressure={"galactic_union": 0.1, "separatist_confed": 0.5},
        ),
    }


# ============================================================================
# SCENARIO BUILDER
# ============================================================================

def build_default_scenario(
    scenario_id: str = "gumas_canonical_v1",
    seed: int = 42,
) -> GUMASState:
    """
    Build the canonical GUMAS galactic scenario from Runtime Reference
    Packet data.

    Returns a fully initialized GUMASState ready for engine.step().
    """
    factions = _build_canonical_factions()
    leaders = _build_canonical_leaders()

    # Assign leaders to factions
    for leader in leaders.values():
        faction = factions.get(leader.faction_id)
        if faction and faction.leader_id is None:
            faction.leader_id = leader.leader_id

    # Build and apply trust matrix
    trust_matrix = _build_initial_trust_matrix(list(factions.keys()))
    for fid, scores in trust_matrix.items():
        if fid in factions:
            factions[fid].trust_scores = scores

    # Apply structural faction strengths
    _apply_faction_profiles(factions)

    # Build initial conflicts
    conflicts = _build_initial_conflicts()

    return GUMASState(
        scenario_id=scenario_id,
        seed=seed,
        factions=factions,
        leaders=leaders,
        conflicts=conflicts,
    )


def _apply_faction_profiles(factions: Dict[str, FactionState]) -> None:
    """Apply differentiated military/economic/tech profiles.

    economic_potential is the structural ceiling: not every polity
    can reach max economy. Corporate oligarchies outperform
    monastic networks. That's reality.
    """
    profiles = {
        #                         mil   eco  tech  pop   eco_potential
        "galactic_union":     (0.8, 0.8, 0.7, 0.7,  0.90),
        "velar_imperium":     (0.9, 0.6, 0.6, 0.5,  0.80),
        "outer_colonies":     (0.3, 0.4, 0.4, 0.6,  0.65),
        "zyphari_compact":    (0.4, 0.9, 0.7, 0.6,  0.95),
        "elari_ascendancy":   (0.3, 0.5, 0.6, 0.8,  0.70),
        "vorran_clans":       (0.6, 0.4, 0.4, 0.8,  0.60),
        "kaelar_orders":      (0.2, 0.3, 0.5, 0.9,  0.45),
        "tharaxian_nomads":   (0.3, 0.3, 0.4, 0.7,  0.50),
        "prime_construct":    (0.5, 0.6, 0.9, 0.5,  0.85),
        "ai_warlord":         (0.7, 0.3, 0.8, 0.3,  0.50),
        "separatist_confed":  (0.4, 0.3, 0.4, 0.4,  0.55),
        "pmc_syndicate":      (0.6, 0.5, 0.5, 0.4,  0.70),
        "crimson_pact":       (0.5, 0.2, 0.3, 0.6,  0.45),
    }
    for fid, (mil, eco, tech, pop, eco_pot) in profiles.items():
        if fid in factions:
            factions[fid].military_strength = mil
            factions[fid].economic_strength = eco
            factions[fid].technology_level = tech
            factions[fid].population_stability = pop
            factions[fid].economic_potential = eco_pot

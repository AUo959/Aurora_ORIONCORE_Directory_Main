#!/usr/bin/env python3
"""
GUMAS v3.0 — Advanced Diplomacy & Negotiation Engine
=====================================================
Anchor: GUMAS-ENGINE-NEGOTIATION-V3
Seed:   EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP:    L2_ENGINE_V3
Version: 3.0.0

Models multi-round treaty negotiation, BATNA (Best Alternative to
Negotiated Agreement) dynamics, back-channel secret diplomacy,
diplomatic crises, ultimatum mechanics, and concession tracking.

This module extends v2.0 treaty mechanics with full negotiation
lifecycle modelling, allowing factions to bargain, signal resolve,
issue ultimatums, and conduct secret deals outside public channels.

Subsystem roles in tick lifecycle:
    Phase 18 — Negotiation Tick (after Technology Tick)

Formulas:
    calc_negotiation_success()      — probability current round succeeds
    calc_concession_threshold()     — minimum concession needed to continue
    calc_batna_strength()           — value of no-deal outcome for each party
    calc_diplomatic_crisis_severity() — severity when talks break down
    calc_back_channel_trust_boost() — trust earned via secret deal
    calc_ultimatum_compliance()     — probability target complies with ultimatum

Design principles:
    - Stdlib only; no numpy/scipy
    - Negotiation state is separate from treaty state (pre-treaty)
    - BATNA: each faction evaluates the value of walking away
    - Ultimatums: one-shot high-stakes coercion mechanic
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Any


# ============================================================================
# ENUMS
# ============================================================================

class NegotiationPhase(Enum):
    """Active negotiation lifecycle phases."""
    EXPLORATORY        = "exploratory"     # initial feelers, no commitment
    POSITIONAL         = "positional"      # opening positions staked out
    INTEGRATIVE        = "integrative"     # parties seeking joint gains
    CONCESSION         = "concession"      # trading concessions
    IMPASSE            = "impasse"         # talks stalled, BATNA recalculated
    BREAKDOWN          = "breakdown"       # talks collapsed
    AGREED             = "agreed"          # deal reached, moves to TreatyState
    BACK_CHANNEL       = "back_channel"    # secret bilateral track


class ConcessionType(Enum):
    """Type of concession offered in negotiation."""
    TERRITORIAL        = "territorial"
    ECONOMIC           = "economic"
    MILITARY           = "military"
    INTELLIGENCE       = "intelligence"
    SYMBOLIC           = "symbolic"        # prestige, face-saving gestures


class UltimatumOutcome(Enum):
    """Resolution of an issued ultimatum."""
    PENDING    = "pending"
    COMPLIED   = "complied"
    DEFIED     = "defied"
    EXPIRED    = "expired"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Concession:
    """A single concession offer from one faction to another."""
    from_faction_id: str
    to_faction_id: str
    concession_type: ConcessionType
    magnitude: float          # [0.0, 1.0] — fraction of the issue at stake
    accepted: Optional[bool] = None
    turn_offered: int = 0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["concession_type"] = self.concession_type.value
        return d


@dataclass
class NegotiationState:
    """
    Active negotiation between two or more factions.

    One negotiation can involve mediators and multiple parties, but
    always has exactly two principal parties (the disputants).
    """
    negotiation_id: str
    party_a: str              # faction_id
    party_b: str              # faction_id
    mediator_id: Optional[str] = None

    phase: NegotiationPhase = NegotiationPhase.EXPLORATORY
    round_number: int = 0
    max_rounds: int = 12

    # BATNA scores (value of no-deal to each party; higher = less urgent to deal)
    batna_a: float = 0.5
    batna_b: float = 0.5

    # Current positions [0.0, 1.0] — fraction of demands met
    position_a: float = 1.0   # party A wants everything
    position_b: float = 0.0   # party B offers nothing

    # Reservation values (minimum acceptable outcome)
    reservation_a: float = 0.4
    reservation_b: float = 0.4

    # Zone of possible agreement = [reservation_b, 1-reservation_a]
    # If negative, no deal is possible

    # Concession history
    concessions: List[Concession] = field(default_factory=list)

    # Trust modifier this negotiation generated
    trust_delta: float = 0.0

    # Linked back-channel (optional secret track)
    back_channel_active: bool = False
    back_channel_trust_boost: float = 0.0

    # Issue resolution
    agreed_outcome: Optional[float] = None   # agreed position [0,1] if AGREED
    turns_active: int = 0
    linked_conflict_id: Optional[str] = None

    def has_zone_of_agreement(self) -> bool:
        """True if deal space is non-empty."""
        return (1.0 - self.reservation_a) >= self.reservation_b

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["phase"] = self.phase.value
        d["concessions"] = [c.to_dict() for c in self.concessions]
        return d


@dataclass
class Ultimatum:
    """
    A coercive diplomatic demand issued by one faction to another.

    If the target defies, the issuer is expected to follow through
    on the implied threat (military escalation, sanctions, etc.).
    """
    ultimatum_id: str
    issuer_faction_id: str
    target_faction_id: str
    demand: str                    # human-readable demand description
    threat: str                    # consequence if defied
    deadline_turns: int = 3        # turns remaining to comply
    resolve_strength: float = 0.7  # issuer's credibility / commitment [0,1]
    outcome: UltimatumOutcome = UltimatumOutcome.PENDING

    turns_elapsed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["outcome"] = self.outcome.value
        return d


# ============================================================================
# NEGOTIATION ENGINE
# ============================================================================

class NegotiationEngine:
    """
    Drives multi-round negotiation, back-channel diplomacy, and ultimatums.

    Usage (inside engine.py Phase 18):
        neg_engine = NegotiationEngine()
        events = neg_engine.tick(negotiations, ultimatums, trust_matrix, leaders, rng)
    """

    # Probability of an impasse leading to full breakdown per turn
    BREAKDOWN_PROBABILITY = 0.15

    # Probability per turn that a back-channel is opened between warring parties
    BACK_CHANNEL_OPEN_PROBABILITY = 0.08

    def tick(
        self,
        negotiations: List[NegotiationState],
        ultimatums: List[Ultimatum],
        trust_matrix: Dict[str, Dict[str, float]],
        leader_diplomacy_openness: Dict[str, float],   # faction_id → openness
        rng,
    ) -> List[Dict[str, Any]]:
        """
        Advance all active negotiations and ultimatums by one turn.

        Returns:
            List of event dicts
        """
        events: List[Dict[str, Any]] = []

        # Process negotiations
        for neg in list(negotiations):
            neg.turns_active += 1
            neg.round_number += 1

            diplomacy_a = leader_diplomacy_openness.get(neg.party_a, 0.5)
            diplomacy_b = leader_diplomacy_openness.get(neg.party_b, 0.5)
            trust_ab = trust_matrix.get(neg.party_a, {}).get(neg.party_b, 0.0)

            ev = self._advance_negotiation(neg, diplomacy_a, diplomacy_b, trust_ab, rng)
            if ev:
                events.extend(ev)

        # Process ultimatums
        for ult in list(ultimatums):
            ult.turns_elapsed += 1
            ev = self._resolve_ultimatum(ult, trust_matrix, leader_diplomacy_openness, rng)
            if ev:
                events.append(ev)

        return events

    def _advance_negotiation(
        self,
        neg: NegotiationState,
        diplomacy_a: float,
        diplomacy_b: float,
        trust_ab: float,
        rng,
    ) -> List[Dict[str, Any]]:
        events = []

        # Max rounds exceeded → breakdown
        if neg.round_number > neg.max_rounds:
            neg.phase = NegotiationPhase.BREAKDOWN
            events.append({
                "type": "DIPLOMATIC_CRISIS",
                "negotiation_id": neg.negotiation_id,
                "party_a": neg.party_a,
                "party_b": neg.party_b,
                "reason": "max_rounds_exceeded",
                "severity": calc_diplomatic_crisis_severity(trust_ab, neg.round_number),
            })
            return events

        if neg.phase in (NegotiationPhase.AGREED, NegotiationPhase.BREAKDOWN):
            return events

        # Recalculate BATNAs
        neg.batna_a = calc_batna_strength(
            military_position=0.5,
            economic_position=0.5,
            alliance_support=trust_ab,
            war_cost=0.3,
        )
        neg.batna_b = calc_batna_strength(
            military_position=0.5,
            economic_position=0.5,
            alliance_support=trust_ab,
            war_cost=0.3,
        )

        # Success probability this round
        p_success = calc_negotiation_success(
            diplomacy_a=diplomacy_a,
            diplomacy_b=diplomacy_b,
            trust_score=trust_ab,
            round_number=neg.round_number,
            mediator_bonus=0.15 if neg.mediator_id else 0.0,
            back_channel_active=neg.back_channel_active,
        )

        if rng.random() < p_success and neg.has_zone_of_agreement():
            # Deal reached
            neg.agreed_outcome = (
                (1.0 - neg.reservation_a + neg.reservation_b) / 2.0
            )
            neg.phase = NegotiationPhase.AGREED
            trust_boost = calc_back_channel_trust_boost(
                trust_ab, neg.back_channel_active, neg.round_number
            )
            neg.trust_delta = trust_boost
            events.append({
                "type": "BACK_CHANNEL_DEAL" if neg.back_channel_active else "DIPLOMATIC_AGREEMENT",
                "negotiation_id": neg.negotiation_id,
                "party_a": neg.party_a,
                "party_b": neg.party_b,
                "agreed_outcome": round(neg.agreed_outcome, 3),
                "trust_boost": round(trust_boost, 3),
                "rounds_taken": neg.round_number,
            })
        else:
            # Concession exchange
            threshold_a = calc_concession_threshold(
                batna=neg.batna_a,
                current_position=neg.position_a,
                round_number=neg.round_number,
                urgency=diplomacy_a,
            )
            if rng.random() < threshold_a:
                delta = rng.uniform(0.03, 0.10)
                neg.position_a = max(neg.reservation_a, neg.position_a - delta)
                neg.concessions.append(Concession(
                    neg.party_a, neg.party_b,
                    ConcessionType.SYMBOLIC, delta, turn_offered=neg.round_number
                ))

            threshold_b = calc_concession_threshold(
                batna=neg.batna_b,
                current_position=1.0 - neg.position_b,
                round_number=neg.round_number,
                urgency=diplomacy_b,
            )
            if rng.random() < threshold_b:
                delta = rng.uniform(0.03, 0.10)
                neg.position_b = min(1.0 - neg.reservation_b, neg.position_b + delta)
                neg.concessions.append(Concession(
                    neg.party_b, neg.party_a,
                    ConcessionType.SYMBOLIC, delta, turn_offered=neg.round_number
                ))

            # Impasse check
            if neg.position_a - neg.position_b < 0.05:
                neg.phase = NegotiationPhase.IMPASSE
                if rng.random() < self.BREAKDOWN_PROBABILITY:
                    neg.phase = NegotiationPhase.BREAKDOWN
                    events.append({
                        "type": "DIPLOMATIC_CRISIS",
                        "negotiation_id": neg.negotiation_id,
                        "party_a": neg.party_a,
                        "party_b": neg.party_b,
                        "reason": "impasse_breakdown",
                        "severity": calc_diplomatic_crisis_severity(trust_ab, neg.round_number),
                    })
            else:
                neg.phase = NegotiationPhase.CONCESSION

        return events

    def _resolve_ultimatum(
        self,
        ult: Ultimatum,
        trust_matrix: Dict[str, Dict[str, float]],
        leader_openness: Dict[str, float],
        rng,
    ) -> Optional[Dict[str, Any]]:
        if ult.outcome != UltimatumOutcome.PENDING:
            return None

        # Deadline expired
        if ult.turns_elapsed >= ult.deadline_turns:
            target_openness = leader_openness.get(ult.target_faction_id, 0.5)
            p_comply = calc_ultimatum_compliance(
                issuer_resolve=ult.resolve_strength,
                target_risk_tolerance=target_openness,
                trust_score=trust_matrix.get(ult.issuer_faction_id, {}).get(
                    ult.target_faction_id, 0.0
                ),
                turns_remaining=0,
            )
            if rng.random() < p_comply:
                ult.outcome = UltimatumOutcome.COMPLIED
            else:
                ult.outcome = UltimatumOutcome.DEFIED

            return {
                "type": "ULTIMATUM_RESOLVED",
                "ultimatum_id": ult.ultimatum_id,
                "issuer": ult.issuer_faction_id,
                "target": ult.target_faction_id,
                "outcome": ult.outcome.value,
                "resolve_strength": ult.resolve_strength,
            }
        return None

    def open_back_channel(self, neg: NegotiationState) -> None:
        """Activate the back-channel track for a negotiation."""
        neg.back_channel_active = True
        neg.phase = NegotiationPhase.BACK_CHANNEL


# ============================================================================
# PURE FORMULA FUNCTIONS
# ============================================================================

def calc_negotiation_success(
    diplomacy_a: float,
    diplomacy_b: float,
    trust_score: float,
    round_number: int,
    mediator_bonus: float = 0.0,
    back_channel_active: bool = False,
    *,
    base_probability: float = 0.10,
    patience_bonus_per_round: float = 0.012,
    back_channel_bonus: float = 0.08,
) -> float:
    """
    Probability that the current negotiation round produces agreement.

    Formula:
        avg_diplomacy = (diplomacy_a + diplomacy_b) / 2
        p = base + avg_diplomacy × 0.3
              + trust_score × 0.25
              + patience_bonus × round_number
              + mediator_bonus
              + back_channel_bonus (if active)

    Returns:
        float in [0.0, 1.0]
    """
    avg_diplomacy = (diplomacy_a + diplomacy_b) / 2.0
    p = (
        base_probability
        + avg_diplomacy * 0.30
        + trust_score * 0.25
        + patience_bonus_per_round * round_number
        + mediator_bonus
        + (back_channel_bonus if back_channel_active else 0.0)
    )
    return max(0.0, min(0.95, p))


def calc_concession_threshold(
    batna: float,
    current_position: float,
    round_number: int,
    urgency: float,
    *,
    batna_weight: float = 0.35,
    urgency_weight: float = 0.30,
    patience_decay: float = 0.025,
    position_stubbornness: float = 0.20,
) -> float:
    """
    Probability that a faction makes a concession this round.

    Weaker BATNA → more willing to concede.
    Higher urgency (diplomacy openness) → more willing to concede.
    Longer negotiation → patience decays, willingness to concede rises.
    Farther from zone of agreement → more stubborn.

    Formula:
        p = batna_weight × (1 - batna)
          + urgency_weight × urgency
          + patience_decay × round_number
          - position_stubbornness × current_position

    Returns:
        float in [0.0, 1.0]
    """
    p = (
        batna_weight * (1.0 - batna)
        + urgency_weight * urgency
        + patience_decay * round_number
        - position_stubbornness * current_position
    )
    return max(0.0, min(0.9, p))


def calc_batna_strength(
    military_position: float,
    economic_position: float,
    alliance_support: float,
    war_cost: float,
    *,
    military_weight: float  = 0.35,
    economic_weight: float  = 0.30,
    alliance_weight: float  = 0.20,
    war_cost_weight: float  = 0.15,
) -> float:
    """
    Strength of a faction's Best Alternative to Negotiated Agreement.

    Higher BATNA = faction is comfortable walking away from the table.

    Formula:
        batna = military_weight × military_position
              + economic_weight × economic_position
              + alliance_weight × alliance_support
              - war_cost_weight × war_cost

    Returns:
        float in [0.0, 1.0]
    """
    batna = (
        military_weight  * military_position
        + economic_weight  * economic_position
        + alliance_weight  * alliance_support
        - war_cost_weight  * war_cost
    )
    return max(0.0, min(1.0, batna))


def calc_diplomatic_crisis_severity(
    trust_score: float,
    rounds_elapsed: int,
    *,
    base_severity: float = 0.3,
    trust_penalty: float = 0.4,
    round_bonus: float   = 0.02,
) -> float:
    """
    Severity of the diplomatic crisis when negotiations break down.

    Higher trust means a breakdown is more surprising and severe.
    More rounds elapsed = more invested, greater disappointment.

    Formula:
        severity = base + trust_penalty × trust_score + round_bonus × rounds

    Returns:
        float in [0.0, 1.0]
    """
    severity = base_severity + trust_penalty * trust_score + round_bonus * rounds_elapsed
    return max(0.0, min(1.0, severity))


def calc_back_channel_trust_boost(
    current_trust: float,
    back_channel_active: bool,
    rounds_taken: int,
    *,
    public_boost: float       = 0.06,
    back_channel_mult: float  = 1.4,
    speed_bonus_threshold: int = 4,
    speed_bonus: float        = 0.03,
) -> float:
    """
    Trust gained from reaching agreement.

    Back-channel deals generate less public trust but more private
    goodwill. Fast agreements (few rounds) signal mutual good faith.

    Formula:
        boost = public_boost × (1 + back_channel_mult × back_channel_active)
              + speed_bonus × (rounds_taken < speed_bonus_threshold)
              - 0.01 × current_trust   (diminishing returns)

    Returns:
        float — delta trust [0.0, 0.20]
    """
    boost = public_boost * (back_channel_mult if back_channel_active else 1.0)
    if rounds_taken < speed_bonus_threshold:
        boost += speed_bonus
    boost -= 0.01 * current_trust
    return max(0.0, min(0.20, boost))


def calc_ultimatum_compliance(
    issuer_resolve: float,
    target_risk_tolerance: float,
    trust_score: float,
    turns_remaining: int,
    *,
    resolve_weight: float = 0.50,
    risk_weight: float    = 0.30,
    trust_weight: float   = 0.20,
) -> float:
    """
    Probability the ultimatum target complies before or at deadline.

    High issuer resolve = target fears the threat is credible.
    High target risk tolerance = target is more likely to defy.
    Low trust = threat is seen as more credible (no goodwill).

    Formula:
        p_comply = resolve_weight × issuer_resolve
                 - risk_weight × target_risk_tolerance
                 + trust_weight × (1 - trust_score)
                 + 0.05 × max(0, turns_remaining - 1)

    Returns:
        float in [0.0, 1.0]
    """
    p = (
        resolve_weight * issuer_resolve
        - risk_weight  * target_risk_tolerance
        + trust_weight * (1.0 - trust_score)
        + 0.05 * max(0, turns_remaining - 1)
    )
    return max(0.0, min(0.95, p))

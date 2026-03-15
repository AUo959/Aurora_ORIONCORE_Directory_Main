#!/usr/bin/env python3
"""
GUMAS v3.0 — Intelligence Network Module
=========================================
Anchor: GUMAS-ENGINE-INTELLIGENCE-V3
Seed:   EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP:    L2_ENGINE_V3
Version: 3.0.0

Models SIGINT/HUMINT intelligence gathering, intelligence sharing
between allies, surveillance state capacity, counter-intelligence
networks, and intelligence fusion (combining multiple sources).

Distinct from the v2.0 sentinels.py (individual operative missions),
this module models the institutional intelligence apparatus:
aggregate collection posture, inter-agency coordination, and
strategic intelligence estimates.

Subsystem roles in tick lifecycle:
    Phase 19 — Intelligence Tick (after Negotiation Tick)

Formulas:
    calc_sigint_yield()         — signals intelligence gathering output
    calc_humint_penetration()   — human intelligence network depth
    calc_intelligence_fusion()  — combined estimate quality from multiple sources
    calc_counter_intel_pressure() — effectiveness of CI in catching operatives
    calc_surveillance_state()   — domestic monitoring affecting population metrics

Design principles:
    - Stdlib only; no numpy/scipy
    - Intelligence is modelled as estimates, not ground truth
    - Uncertainty degrades estimates; CI reduces adversary accuracy
    - Intel sharing creates alliance dependency (Picard_Delta_3 governs leaks)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any


# ============================================================================
# ENUMS
# ============================================================================

class IntelType(Enum):
    """Intelligence collection modalities."""
    SIGINT    = "sigint"     # signals / electronic intelligence
    HUMINT    = "humint"     # human intelligence (agents, defectors)
    IMINT     = "imint"      # imagery intelligence (satellite, reconnaissance)
    OSINT     = "osint"      # open-source intelligence
    CYBINT    = "cybint"     # cyber intelligence (network intrusion)


class IntelQuality(Enum):
    """Quality tier of an intelligence product."""
    NOISE       = "noise"       # unreliable / unverified
    RAW         = "raw"         # single-source, unconfirmed
    CORROBORATED = "corroborated"  # multi-source confirmed
    ACTIONABLE  = "actionable"  # verified, ready for decision-making


class SurveillanceLevel(Enum):
    """Domestic surveillance capacity of a regime."""
    OPEN          = "open"           # minimal monitoring
    MODERATE      = "moderate"       # standard law enforcement
    AUTHORITARIAN = "authoritarian"  # broad state surveillance
    TOTALITARIAN  = "totalitarian"   # comprehensive monitoring


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class IntelReport:
    """
    A single intelligence product on a target faction.

    Represents an estimate of the target's state, not ground truth.
    Error is the absolute deviation from true state.
    """
    report_id: str
    producing_faction: str
    target_faction: str
    intel_type: IntelType
    quality: IntelQuality
    turn_produced: int

    # Estimated values for target (normalized [0,1])
    estimated_military_strength: Optional[float] = None
    estimated_economic_strength: Optional[float] = None
    estimated_trust_level: Optional[float] = None   # estimated trust toward producer

    # Estimate accuracy (1.0 = perfect; 0.0 = useless)
    accuracy: float = 0.5

    # Sharing (list of faction_ids that have received this report)
    shared_with: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["intel_type"] = self.intel_type.value
        d["quality"] = self.quality.value
        return d


@dataclass
class IntelNetwork:
    """
    Institutional intelligence apparatus for a single faction.

    Tracks collection capabilities, CI posture, and accumulated
    intelligence products.
    """
    faction_id: str

    # Collection capacity per modality [0.0, 1.0]
    sigint_capacity: float = 0.3
    humint_capacity: float = 0.3
    imint_capacity: float  = 0.3
    osint_capacity: float  = 0.5
    cybint_capacity: float = 0.2

    # Counter-intelligence posture [0.0, 1.0]
    counter_intel_strength: float = 0.3

    # Domestic surveillance level
    surveillance_level: SurveillanceLevel = SurveillanceLevel.MODERATE

    # Current intelligence budget (fraction of economic output)
    intel_budget_fraction: float = 0.05

    # Intelligence sharing agreements (partner faction_ids)
    sharing_partners: Set[str] = field(default_factory=set)

    # Accumulated intelligence reports (current turn's products)
    current_reports: List[IntelReport] = field(default_factory=list)

    # Fused estimates (updated each tick via intelligence fusion)
    fused_estimates: Dict[str, Dict[str, float]] = field(default_factory=dict)
    # fused_estimates[target_faction_id][attribute] = estimated_value

    # CI catches this turn (operative_ids caught by CI)
    ci_catches: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "faction_id": self.faction_id,
            "sigint_capacity": self.sigint_capacity,
            "humint_capacity": self.humint_capacity,
            "imint_capacity": self.imint_capacity,
            "osint_capacity": self.osint_capacity,
            "cybint_capacity": self.cybint_capacity,
            "counter_intel_strength": self.counter_intel_strength,
            "surveillance_level": self.surveillance_level.value,
            "intel_budget_fraction": self.intel_budget_fraction,
            "sharing_partners": list(self.sharing_partners),
            "fused_estimates": dict(self.fused_estimates),
        }


# ============================================================================
# INTELLIGENCE ENGINE
# ============================================================================

class IntelligenceEngine:
    """
    Drives intelligence collection, fusion, CI operations, and sharing.

    Usage (inside engine.py Phase 19):
        intel_engine = IntelligenceEngine()
        events = intel_engine.tick(networks, faction_states, trust_matrix, rng)
    """

    # Minimum accuracy for a report to be actionable
    ACTIONABLE_THRESHOLD = 0.70

    # CI catch probability scale factor
    CI_CATCH_SCALE = 0.35

    def tick(
        self,
        networks: Dict[str, IntelNetwork],
        faction_military: Dict[str, float],
        faction_economic: Dict[str, float],
        trust_matrix: Dict[str, Dict[str, float]],
        rng,
    ) -> List[Dict[str, Any]]:
        """
        Run one intelligence tick for all factions.

        Args:
            networks: faction_id → IntelNetwork
            faction_military: faction_id → true military strength
            faction_economic: faction_id → true economic strength
            trust_matrix: faction_id → {other_id → trust}
            rng: Seeded Random instance

        Returns:
            List of event dicts
        """
        events: List[Dict[str, Any]] = []

        # Clear previous tick reports
        for net in networks.values():
            net.current_reports.clear()
            net.ci_catches.clear()

        # Phase 1: Collection
        for fid, net in networks.items():
            for target_id, target_net in networks.items():
                if target_id == fid:
                    continue
                report = self._collect_intel(
                    net, target_id, target_net,
                    faction_military.get(target_id, 0.5),
                    faction_economic.get(target_id, 0.5),
                    rng,
                )
                if report:
                    net.current_reports.append(report)

        # Phase 2: Counter-intelligence
        for fid, net in networks.items():
            for target_id, target_net in networks.items():
                if target_id == fid:
                    continue
                # Check if any operative from target_id is caught
                catch_prob = calc_counter_intel_pressure(
                    ci_strength=net.counter_intel_strength,
                    adversary_humint=networks.get(target_id, net).humint_capacity,
                    trust_score=trust_matrix.get(fid, {}).get(target_id, 0.0),
                )
                if rng.random() < catch_prob * self.CI_CATCH_SCALE:
                    events.append({
                        "type": "INTELLIGENCE_COMPROMISE",
                        "defending_faction": fid,
                        "adversary_faction": target_id,
                        "ci_strength": round(catch_prob, 3),
                    })

        # Phase 3: Intelligence fusion
        for fid, net in networks.items():
            fused = self._fuse_intelligence(net)
            net.fused_estimates = fused

        # Phase 4: Intelligence sharing
        for fid, net in networks.items():
            for partner_id in net.sharing_partners:
                if partner_id not in networks:
                    continue
                share_event = self._share_intelligence(net, networks[partner_id], rng)
                if share_event:
                    events.append(share_event)

        # Phase 5: Surveillance state effects on population
        for fid, net in networks.items():
            if net.surveillance_level in (
                SurveillanceLevel.AUTHORITARIAN,
                SurveillanceLevel.TOTALITARIAN,
            ):
                events.append({
                    "type": "SURVEILLANCE_EXPANSION",
                    "faction_id": fid,
                    "level": net.surveillance_level.value,
                    "legitimacy_penalty": calc_surveillance_legitimacy_penalty(
                        net.surveillance_level
                    ),
                })

        return events

    def _collect_intel(
        self,
        collector: IntelNetwork,
        target_id: str,
        target_net: IntelNetwork,
        true_military: float,
        true_economic: float,
        rng,
    ) -> Optional[IntelReport]:
        """Run one collection attempt against a target."""
        # SIGINT yield
        sigint = calc_sigint_yield(
            collector.sigint_capacity,
            collector.cybint_capacity,
            target_net.counter_intel_strength,
        )
        humint = calc_humint_penetration(
            collector.humint_capacity,
            target_net.counter_intel_strength,
            target_net.surveillance_level.value,
        )

        # Combined accuracy
        accuracy = calc_intelligence_fusion(sigint, humint, 0.0, collector.osint_capacity)

        if accuracy < 0.15:
            return None  # below threshold, no useful product

        # Add noise to estimates
        noise = rng.gauss(0.0, (1.0 - accuracy) * 0.2)
        est_military = max(0.0, min(1.0, true_military + noise))
        est_economic = max(0.0, min(1.0, true_economic + noise * 0.8))

        quality = (
            IntelQuality.ACTIONABLE    if accuracy >= self.ACTIONABLE_THRESHOLD else
            IntelQuality.CORROBORATED  if accuracy >= 0.50 else
            IntelQuality.RAW           if accuracy >= 0.30 else
            IntelQuality.NOISE
        )

        return IntelReport(
            report_id=f"{collector.faction_id}_{target_id}_{id(rng)}",
            producing_faction=collector.faction_id,
            target_faction=target_id,
            intel_type=IntelType.SIGINT if sigint > humint else IntelType.HUMINT,
            quality=quality,
            turn_produced=0,
            estimated_military_strength=round(est_military, 3),
            estimated_economic_strength=round(est_economic, 3),
            accuracy=round(accuracy, 3),
        )

    def _fuse_intelligence(
        self,
        net: IntelNetwork,
    ) -> Dict[str, Dict[str, float]]:
        """Fuse all current reports into best estimates per target."""
        fused: Dict[str, Dict[str, float]] = {}
        target_reports: Dict[str, List[IntelReport]] = {}

        for report in net.current_reports:
            target_reports.setdefault(report.target_faction, []).append(report)

        for target_id, reports in target_reports.items():
            if not reports:
                continue
            # Weighted average by accuracy
            total_weight = sum(r.accuracy for r in reports)
            if total_weight == 0:
                continue

            fused[target_id] = {}
            for attr in ("estimated_military_strength", "estimated_economic_strength"):
                values = [
                    (getattr(r, attr), r.accuracy)
                    for r in reports
                    if getattr(r, attr) is not None
                ]
                if values:
                    weighted_sum = sum(v * w for v, w in values)
                    total_w = sum(w for _, w in values)
                    fused[target_id][attr] = round(weighted_sum / total_w, 3)

        return fused

    def _share_intelligence(
        self,
        sender: IntelNetwork,
        receiver: IntelNetwork,
        rng,
    ) -> Optional[Dict[str, Any]]:
        """Share one actionable report with a partner."""
        actionable = [
            r for r in sender.current_reports
            if r.quality in (IntelQuality.ACTIONABLE, IntelQuality.CORROBORATED)
            and r.target_faction not in receiver.sharing_partners
        ]
        if not actionable:
            return None

        report = rng.choice(actionable)
        report.shared_with.append(receiver.faction_id)
        receiver.current_reports.append(report)

        return {
            "type": "INTELLIGENCE_SHARING",
            "sender": sender.faction_id,
            "receiver": receiver.faction_id,
            "target": report.target_faction,
            "quality": report.quality.value,
            "accuracy": report.accuracy,
        }


# ============================================================================
# PURE FORMULA FUNCTIONS
# ============================================================================

def calc_sigint_yield(
    sigint_capacity: float,
    cybint_capacity: float,
    target_ci_strength: float,
    *,
    sigint_weight: float  = 0.60,
    cybint_weight: float  = 0.40,
    ci_penalty_scale: float = 0.50,
) -> float:
    """
    Intelligence yield from electronic / signals collection.

    Formula:
        raw = sigint_weight × sigint_capacity + cybint_weight × cybint_capacity
        yield = raw × (1 - ci_penalty_scale × target_ci_strength)

    Returns:
        float in [0.0, 1.0]
    """
    raw = sigint_weight * sigint_capacity + cybint_weight * cybint_capacity
    ci_penalty = ci_penalty_scale * target_ci_strength
    yield_val = raw * (1.0 - ci_penalty)
    return max(0.0, min(1.0, yield_val))


def calc_humint_penetration(
    humint_capacity: float,
    target_ci_strength: float,
    target_surveillance_level: str,
    *,
    surveillance_penalties: Optional[Dict[str, float]] = None,
) -> float:
    """
    Depth of human intelligence penetration into a target faction.

    Surveillance level penalises HUMINT: authoritarian states are
    harder to run agents inside.

    Formula:
        surv_penalty = surveillance_penalties[target_surveillance_level]
        penetration = humint_capacity × (1 - target_ci_strength × 0.6)
                                      × (1 - surv_penalty)

    Returns:
        float in [0.0, 1.0]
    """
    if surveillance_penalties is None:
        surveillance_penalties = {
            SurveillanceLevel.OPEN.value:          0.00,
            SurveillanceLevel.MODERATE.value:      0.10,
            SurveillanceLevel.AUTHORITARIAN.value: 0.30,
            SurveillanceLevel.TOTALITARIAN.value:  0.55,
        }
    surv_penalty = surveillance_penalties.get(target_surveillance_level, 0.10)
    penetration = (
        humint_capacity
        * (1.0 - target_ci_strength * 0.6)
        * (1.0 - surv_penalty)
    )
    return max(0.0, min(1.0, penetration))


def calc_intelligence_fusion(
    sigint_yield: float,
    humint_penetration: float,
    imint_yield: float,
    osint_yield: float,
    *,
    sigint_weight: float  = 0.30,
    humint_weight: float  = 0.35,
    imint_weight: float   = 0.20,
    osint_weight: float   = 0.15,
    synergy_bonus: float  = 0.05,
) -> float:
    """
    Combined accuracy estimate from fusing multiple intelligence streams.

    Multi-source corroboration provides a synergy bonus when at least
    two sources exceed 0.3 yield.

    Formula:
        base = weighted sum of yields
        n_strong = count of yields > 0.3
        fused = base + synergy_bonus × max(0, n_strong - 1)

    Returns:
        float in [0.0, 1.0]
    """
    base = (
        sigint_weight  * sigint_yield
        + humint_weight  * humint_penetration
        + imint_weight   * imint_yield
        + osint_weight   * osint_yield
    )
    strong_sources = sum(
        1 for v in (sigint_yield, humint_penetration, imint_yield, osint_yield)
        if v > 0.30
    )
    fused = base + synergy_bonus * max(0, strong_sources - 1)
    return max(0.0, min(1.0, fused))


def calc_counter_intel_pressure(
    ci_strength: float,
    adversary_humint: float,
    trust_score: float,
    *,
    ci_weight: float     = 0.55,
    humint_weight: float = 0.35,
    trust_dampener: float = 0.10,
) -> float:
    """
    Probability that counter-intelligence detects an adversary operative per turn.

    Higher trust reduces CI activity (allies are less suspicious).
    Stronger CI and weaker adversary HUMINT → higher catch probability.

    Formula:
        p = ci_weight × ci_strength
          + humint_weight × adversary_humint
          - trust_dampener × trust_score

    Returns:
        float in [0.0, 1.0]
    """
    p = (
        ci_weight      * ci_strength
        + humint_weight  * adversary_humint
        - trust_dampener * trust_score
    )
    return max(0.0, min(1.0, p))


def calc_surveillance_legitimacy_penalty(
    surveillance_level: SurveillanceLevel,
    *,
    penalties: Optional[Dict[str, float]] = None,
) -> float:
    """
    Legitimacy penalty imposed by high domestic surveillance.

    Used to update leader.public_legitimacy each tick.

    Returns:
        float — legitimacy delta (negative = penalty)
    """
    if penalties is None:
        penalties = {
            SurveillanceLevel.OPEN.value:          0.000,
            SurveillanceLevel.MODERATE.value:      0.002,
            SurveillanceLevel.AUTHORITARIAN.value: 0.012,
            SurveillanceLevel.TOTALITARIAN.value:  0.025,
        }
    return -penalties.get(surveillance_level.value, 0.002)

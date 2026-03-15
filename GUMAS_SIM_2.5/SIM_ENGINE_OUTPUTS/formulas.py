#!/usr/bin/env python3
"""
GUMAS L2 Simulation Formulas
=============================
Anchor: GUMAS-ENGINE-FORMULAS-V1
Seed: EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP: L2_ENGINE_CORE
Version: 1.0.0

Pure functions implementing the L2 simulation formulas documented in
PR_L2_GUMAS_ARCHITECTURAL_ENHANCEMENTS Section 5.2 and the Runtime
Reference Packet v0.4 Section 1.

All functions are stateless and deterministic for a given input.
Side effects are handled by the engine, not by these functions.

Formula Index:
  1. calc_deescalation_probability  — Section 1.2 / PR 5.2 Formula 1
  2. calc_bias_evolution            — Section 1.1 / PR 5.2 Formula 2
  3. calc_treaty_breach_score       — Section 1.4 / PR 5.2 Formula 3
  4. calc_reputation_decay          — Section 1.5 / PR 5.2 Formula 4
  5. calc_double_agent_risk         — Section 1.3 / PR 5.2 Formula 5
  6. calc_trust_update              — Section 1.5
  7. apply_bias_hooks               — Section 1.1 bias effect modifiers
"""

from __future__ import annotations

from typing import Dict, Optional


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp a value to [lo, hi]."""
    return max(lo, min(hi, value))


# ============================================================================
# 1. DE-ESCALATION PROBABILITY
# ============================================================================

def calc_deescalation_probability(
    war_cost_a: float,
    war_cost_b: float,
    stalemate_index: float,
    internal_pressure_a: float,
    internal_pressure_b: float,
    mediation_available: bool,
    *,
    cost_weight: float = 0.3,
    stalemate_weight: float = 0.25,
    pressure_weight: float = 0.25,
    mediation_bonus: float = 0.2,
) -> float:
    """
    Calculate de-escalation probability for a conflict.

    Formula (PR Section 5.2 Formula 1):
        P = cost_weight × avg_war_cost
          + stalemate_weight × stalemate_index
          + pressure_weight × avg_internal_pressure
          + mediation_bonus × mediation_available

    Edge Cases:
        - stalemate_index == 1.0 → force P >= 0.5
        - avg_war_cost > 0.9 for both → force P >= 0.6

    Returns:
        float in [0.0, 1.0]
    """
    avg_war_cost = (war_cost_a + war_cost_b) / 2.0
    avg_pressure = (internal_pressure_a + internal_pressure_b) / 2.0
    mediation_flag = 1.0 if mediation_available else 0.0

    p = (
        cost_weight * avg_war_cost
        + stalemate_weight * stalemate_index
        + pressure_weight * avg_pressure
        + mediation_bonus * mediation_flag
    )

    # Edge case: total stalemate triggers negotiation
    if stalemate_index >= 1.0:
        p = max(p, 0.5)

    # Edge case: catastrophic mutual cost
    if war_cost_a > 0.9 and war_cost_b > 0.9:
        p = max(p, 0.6)

    return _clamp(p)


# ============================================================================
# 2. BIAS EVOLUTION
# ============================================================================

def calc_bias_evolution(
    current_intensity: float,
    plasticity: float,
    event_severity: float,
    has_survivorship_bias: bool = False,
    doctrine_shift_bonus: float = 0.0,
) -> float:
    """
    Calculate new bias intensity after an event.

    Formula (PR Section 5.2 Formula 2):
        new_intensity = current_intensity × (1 - plasticity × event_severity)
                      + adaptation_factor × doctrine_shift_bonus

    Constraints:
        - Result clamped to [0.0, 1.0]
        - adaptation_factor = 0.1 if leader has survivorship_bias, else 0.0

    Returns:
        float in [0.0, 1.0]
    """
    adaptation_factor = 0.1 if has_survivorship_bias else 0.0

    new_intensity = (
        current_intensity * (1.0 - plasticity * event_severity)
        + adaptation_factor * doctrine_shift_bonus
    )

    return _clamp(new_intensity)


# ============================================================================
# 3. TREATY BREACH DETECTION
# ============================================================================

def calc_treaty_breach_score(
    action_severity: float,
    is_direct_action: bool,
    treaty_ambiguity: float,
    faction_trust: float,
    *,
    ambiguity_tolerance: float = 0.2,
    trust_discount_multiplier: float = 0.1,
) -> float:
    """
    Calculate breach score for a potential treaty violation.

    Formula (PR Section 5.2 Formula 3):
        breach_score = (action_severity × violation_weight)
                     - (treaty_ambiguity × ambiguity_tolerance)
                     - (faction_trust × trust_discount)

    Where:
        violation_weight = 1.0 (direct) or 0.5 (indirect/proxy)
        trust_discount = trust_discount_multiplier × bilateral_trust_score

    Returns:
        Raw breach score (not clamped — compare against violation_threshold).
    """
    violation_weight = 1.0 if is_direct_action else 0.5
    trust_discount = trust_discount_multiplier * faction_trust

    return (
        action_severity * violation_weight
        - treaty_ambiguity * ambiguity_tolerance
        - faction_trust * trust_discount
    )


def is_treaty_breach(
    breach_score: float,
    violation_threshold: float = 0.6,
) -> bool:
    """Determine if breach_score exceeds the violation threshold."""
    return breach_score > violation_threshold


# ============================================================================
# 4. REPUTATION DECAY
# ============================================================================

def calc_reputation_after_decay(
    base_reputation: float,
    breach_penalty: float,
    breach_count: int,
    turns_since_last_breach: int,
    *,
    decay_factor: float = 0.95,
    floor: float = 0.1,
) -> float:
    """
    Calculate reputation after time-based decay of breach penalties.

    Formula (PR Section 5.2 Formula 4):
        new_reputation = base_reputation
                       + breach_penalty × breach_count × decay_factor^turns_since_breach

    Note: breach_penalty is negative (default -0.1), so this reduces reputation.

    Constraints:
        - decay_factor: 0.95 per turn
        - Floor: reputation cannot drop below 0.1

    Returns:
        float, minimum = floor
    """
    decayed_penalty = breach_penalty * breach_count * (decay_factor ** turns_since_last_breach)
    new_rep = base_reputation + decayed_penalty
    return max(floor, new_rep)


# ============================================================================
# 5. DOUBLE-AGENT RISK
# ============================================================================

def calc_double_agent_risk(
    bilateral_trust: float,
    intel_sensitivity: float,
    *,
    base_risk: float = 0.15,
    trust_modifier: float = -0.1,
    sensitivity_multiplier: float = 0.3,
) -> float:
    """
    Calculate probability of double-agent presence in intelligence sharing.

    Formula (PR Section 5.2 Formula 5):
        P = base_risk
          + sensitivity_multiplier × intel_sensitivity
          + trust_modifier

    Constraints:
        - Result clamped to [0.0, 0.8] (never certain, never impossible)
        - If bilateral_trust > 0.8: additional -0.1 modifier

    Returns:
        float in [0.0, 0.8]
    """
    high_trust_bonus = -0.1 if bilateral_trust > 0.8 else 0.0

    p = (
        base_risk
        + sensitivity_multiplier * intel_sensitivity
        + trust_modifier
        + high_trust_bonus
    )

    return _clamp(p, lo=0.0, hi=0.8)


# ============================================================================
# 6. TRUST UPDATE
# ============================================================================

def calc_trust_update(
    current_trust: float,
    betrayal_penalty: float,
    alliance_bonus: float,
    *,
    lambda_coeff: float = 1.0,
    delta_coeff: float = 1.0,
) -> float:
    """
    Update bilateral trust score.

    Formula (Runtime Reference Packet Section 1.5):
        T_new = clamp01(T_old - λ(B) + δ(A))

    Where:
        B = betrayal_penalty (exponential decay for repeats recommended)
        A = alliance-building / humanitarian / compliance actions
        λ, δ = tunable per faction culture + leader bias profile

    Returns:
        float in [0.0, 1.0]
    """
    new_trust = current_trust - lambda_coeff * betrayal_penalty + delta_coeff * alliance_bonus
    return _clamp(new_trust)


# ============================================================================
# 7. BIAS EFFECT HOOKS
# ============================================================================

# Default bias hook profiles per BiasType.
# Maps BiasType.value -> dict of hook adjustments (deltas from neutral 0.5).
BIAS_HOOK_PROFILES: Dict[str, Dict[str, float]] = {
    "status_quo_bias": {
        "evidence_gain_multiplier": 0.8,  # discounts novel evidence
        "risk_tolerance": 0.3,
        "diplomacy_openness": 0.4,
        "escalation_threshold": 0.7,      # slow to escalate
        "oversight_resistance": 0.6,      # resists institutional change
    },
    "survivorship_bias": {
        "evidence_gain_multiplier": 0.7,  # only counts confirmatory wins
        "risk_tolerance": 0.7,
        "diplomacy_openness": 0.4,
        "escalation_threshold": 0.4,      # quick to double down
        "oversight_resistance": 0.5,
    },
    "confirmation_bias": {
        "evidence_gain_multiplier": 0.5,  # heavy filter on contradictory data
        "risk_tolerance": 0.5,
        "diplomacy_openness": 0.3,
        "escalation_threshold": 0.5,
        "oversight_resistance": 0.4,
    },
    "sunk_cost_fallacy": {
        "evidence_gain_multiplier": 0.6,
        "risk_tolerance": 0.8,            # escalating commitment
        "diplomacy_openness": 0.2,        # won't back down
        "escalation_threshold": 0.3,      # very easy to escalate
        "oversight_resistance": 0.5,
    },
    "hyper_rationalism_bias": {
        "evidence_gain_multiplier": 1.2,  # overcounts quantifiable data
        "risk_tolerance": 0.6,
        "diplomacy_openness": 0.5,
        "escalation_threshold": 0.5,
        "oversight_resistance": 0.7,      # trusts own logic over committees
    },
    "fear_based_decision_making": {
        "evidence_gain_multiplier": 0.9,
        "risk_tolerance": 0.2,            # extremely risk-averse
        "diplomacy_openness": 0.3,
        "escalation_threshold": 0.3,      # defensive overreaction
        "oversight_resistance": 0.3,
    },
    "moral_self_licensing": {
        "evidence_gain_multiplier": 0.8,
        "risk_tolerance": 0.6,
        "diplomacy_openness": 0.5,
        "escalation_threshold": 0.4,
        "oversight_resistance": 0.8,      # "greater good" justification
    },
    "zero_sum_thinking": {
        "evidence_gain_multiplier": 0.7,
        "risk_tolerance": 0.6,
        "diplomacy_openness": 0.1,        # sees all deals as losses
        "escalation_threshold": 0.3,
        "oversight_resistance": 0.5,
    },
}


def apply_bias_hooks(
    bias_type_value: str,
    bias_intensity: float,
) -> Dict[str, float]:
    """
    Calculate effective bias hook values for a leader.

    Applies intensity scaling: hooks interpolate between neutral (0.5)
    and the bias profile value based on intensity.

    Args:
        bias_type_value: BiasType enum value string
        bias_intensity: 0.0 (no effect) to 1.0 (full effect)

    Returns:
        Dict with keys: evidence_gain_multiplier, risk_tolerance,
        diplomacy_openness, escalation_threshold, oversight_resistance
    """
    neutral = {
        "evidence_gain_multiplier": 1.0,
        "risk_tolerance": 0.5,
        "diplomacy_openness": 0.5,
        "escalation_threshold": 0.5,
        "oversight_resistance": 0.5,
    }

    profile = BIAS_HOOK_PROFILES.get(bias_type_value)
    if profile is None:
        return neutral

    result = {}
    for key, neutral_val in neutral.items():
        profile_val = profile.get(key, neutral_val)
        # Lerp between neutral and profile based on intensity
        result[key] = neutral_val + (profile_val - neutral_val) * bias_intensity

    return result

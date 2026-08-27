#!/usr/bin/env python3
"""
GUMAS L2 Simulation Formulas v2.0
===================================
Anchor: GUMAS-ENGINE-FORMULAS-V2
Seed: EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP: L2_ENGINE_CORE
Version: 2.0.0
"""

from typing import Dict, Tuple


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """
    Clamp a value between lower and upper bounds.

    Args:
        value: The value to clamp
        lo: Lower bound (default 0.0)
        hi: Upper bound (default 1.0)

    Returns:
        Clamped value
    """
    return max(lo, min(hi, value))


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
    mediation_bonus: float = 0.2
) -> float:
    """
    Calculate probability of conflict deescalation.

    Formula:
        P_deescalate = (1 - avg_cost) * cost_weight
                     + stalemate_index * stalemate_weight
                     + avg_pressure * pressure_weight
                     + [mediation_bonus if available else 0]

    Args:
        war_cost_a: Cost to faction A (0-1)
        war_cost_b: Cost to faction B (0-1)
        stalemate_index: How stalemated conflict is (0-1)
        internal_pressure_a: Internal pressure in faction A (0-1)
        internal_pressure_b: Internal pressure in faction B (0-1)
        mediation_available: Whether third-party mediation exists
        cost_weight: Weight for cost term
        stalemate_weight: Weight for stalemate term
        pressure_weight: Weight for pressure term
        mediation_bonus: Bonus if mediation available

    Returns:
        Deescalation probability (0-1)
    """
    avg_cost = (war_cost_a + war_cost_b) / 2.0
    avg_pressure = (internal_pressure_a + internal_pressure_b) / 2.0

    prob = (
        (1.0 - avg_cost) * cost_weight
        + stalemate_index * stalemate_weight
        + avg_pressure * pressure_weight
    )

    if mediation_available:
        prob += mediation_bonus

    return _clamp(prob)


def calc_bias_evolution(
    current_intensity: float,
    plasticity: float,
    event_severity: float,
    has_survivorship_bias: bool = False,
    doctrine_shift_bonus: float = 0.0
) -> float:
    """
    Calculate how bias evolves after an event.

    Formula:
        B_new = B_old + (1 - plasticity) * event_severity * direction
               + [survivorship_bonus if applicable]
               + doctrine_shift_bonus

    Args:
        current_intensity: Current bias strength (0-1)
        plasticity: Susceptibility to change (0-1)
        event_severity: Impact magnitude (0-1)
        has_survivorship_bias: Whether survivorship bias applies
        doctrine_shift_bonus: Bonus from institutional change

    Returns:
        New bias intensity (0-1)
    """
    direction = 1.0 if event_severity > 0.5 else -1.0
    delta = (1.0 - plasticity) * event_severity * direction

    if has_survivorship_bias:
        delta += event_severity * 0.1

    delta += doctrine_shift_bonus

    return _clamp(current_intensity + delta)


def calc_treaty_breach_score(
    action_severity: float,
    is_direct_action: bool,
    treaty_ambiguity: float,
    faction_trust: float,
    *,
    ambiguity_tolerance: float = 0.2,
    trust_discount_multiplier: float = 0.1
) -> float:
    """
    Calculate the severity of a potential treaty breach.

    Formula:
        breach_score = action_severity * (2 if direct else 1)
                     * (1 - ambiguity_tolerance * treaty_ambiguity)
                     * (1 - faction_trust * trust_discount_multiplier)

    Args:
        action_severity: How severe the action is (0-1)
        is_direct_action: Whether action is direct violation
        treaty_ambiguity: How ambiguous treaty terms are (0-1)
        faction_trust: Trust level with faction (0-1)
        ambiguity_tolerance: How much ambiguity to allow
        trust_discount_multiplier: How much trust reduces breach score

    Returns:
        Breach score (0+)
    """
    severity_mult = 2.0 if is_direct_action else 1.0
    ambiguity_factor = 1.0 - (ambiguity_tolerance * treaty_ambiguity)
    trust_factor = 1.0 - (faction_trust * trust_discount_multiplier)

    score = action_severity * severity_mult * ambiguity_factor * trust_factor
    return _clamp(score, 0.0, 10.0)


def is_treaty_breach(breach_score: float, violation_threshold: float = 0.6) -> bool:
    """
    Determine if a breach score constitutes an actual treaty violation.

    Args:
        breach_score: Calculated breach severity
        violation_threshold: Score at which breach is triggered

    Returns:
        True if breach threshold exceeded
    """
    return breach_score >= violation_threshold


def calc_reputation_after_decay(
    base_reputation: float,
    breach_penalty: float,
    breach_count: int,
    turns_since_last_breach: int,
    *,
    decay_factor: float = 0.95,
    floor: float = 0.1
) -> float:
    """
    Calculate reputation after accounting for breaches and decay.

    Formula:
        rep = base_reputation
            - (breach_penalty * breach_count)
            + (turns_since_last_breach * 0.01)
            - (base_reputation * (1 - decay_factor))

    Args:
        base_reputation: Starting reputation (0-1)
        breach_penalty: Points lost per breach
        breach_count: Number of breaches
        turns_since_last_breach: Turns elapsed since last violation
        decay_factor: How much reputation decays per turn
        floor: Minimum reputation value

    Returns:
        Updated reputation (floor to 1)
    """
    rep = base_reputation
    rep -= breach_penalty * breach_count
    rep += turns_since_last_breach * 0.01
    rep -= base_reputation * (1.0 - decay_factor)

    return _clamp(rep, floor, 1.0)


def calc_double_agent_risk(
    bilateral_trust: float,
    intel_sensitivity: float,
    *,
    base_risk: float = 0.15,
    trust_modifier: float = -0.1,
    sensitivity_multiplier: float = 0.3
) -> float:
    """
    Calculate risk of double-agent infiltration.

    Formula:
        risk = base_risk
              + (bilateral_trust * trust_modifier)
              + (intel_sensitivity * sensitivity_multiplier)

    Args:
        bilateral_trust: Trust level with other faction (0-1)
        intel_sensitivity: Sensitivity of intelligence (0-1)
        base_risk: Base infiltration risk
        trust_modifier: How trust affects risk
        sensitivity_multiplier: How intel sensitivity affects risk

    Returns:
        Double-agent risk (0-1)
    """
    risk = (
        base_risk
        + (bilateral_trust * trust_modifier)
        + (intel_sensitivity * sensitivity_multiplier)
    )
    return _clamp(risk)


def calc_trust_update(
    current_trust: float,
    betrayal_penalty: float,
    alliance_bonus: float,
    *,
    lambda_coeff: float = 1.0,
    delta_coeff: float = 1.0
) -> float:
    """
    Calculate trust level after events.

    Formula:
        trust_new = current_trust
                  - (betrayal_penalty * lambda_coeff)
                  + (alliance_bonus * delta_coeff)

    Args:
        current_trust: Current trust level (0-1)
        betrayal_penalty: Points lost from betrayal
        alliance_bonus: Points gained from alliance action
        lambda_coeff: Betrayal penalty coefficient
        delta_coeff: Alliance bonus coefficient

    Returns:
        Updated trust level (0-1)
    """
    trust = (
        current_trust
        - (betrayal_penalty * lambda_coeff)
        + (alliance_bonus * delta_coeff)
    )
    return _clamp(trust)


BIAS_HOOK_PROFILES: Dict[str, Dict[str, float]] = {
    "confirmation_bias": {
        "evidence_weight": 1.5,
        "disconfirm_weight": 0.5,
        "intensity_cap": 0.8,
    },
    "availability_heuristic": {
        "recent_weight": 2.0,
        "frequency_discount": 0.3,
        "intensity_cap": 0.75,
    },
    "anchoring_bias": {
        "initial_impact": 1.8,
        "decay_rate": 0.02,
        "intensity_cap": 0.85,
    },
    "sunk_cost_fallacy": {
        "investment_weight": 1.6,
        "rationality_discount": 0.4,
        "intensity_cap": 0.7,
    },
    "overconfidence_bias": {
        "self_rating_boost": 1.4,
        "reality_check": 0.6,
        "intensity_cap": 0.8,
    },
    "in_group_bias": {
        "loyalty_weight": 1.7,
        "out_group_discount": 0.3,
        "intensity_cap": 0.9,
    },
    "hindsight_bias": {
        "revision_weight": 1.5,
        "humility_factor": 0.4,
        "intensity_cap": 0.75,
    },
    "fundamental_attribution_error": {
        "personal_factor": 1.6,
        "situational_discount": 0.3,
        "intensity_cap": 0.8,
    },
}


def apply_bias_hooks(bias_type_value: str, bias_intensity: float) -> Dict[str, float]:
    """
    Apply cognitive bias hooks to decision parameters.

    Args:
        bias_type_value: One of the keys in BIAS_HOOK_PROFILES
        bias_intensity: Strength of bias (0-1)

    Returns:
        Dictionary of parameter modifiers based on bias type
    """
    if bias_type_value not in BIAS_HOOK_PROFILES:
        return {}

    profile = BIAS_HOOK_PROFILES[bias_type_value]
    clamped_intensity = _clamp(bias_intensity, 0.0, profile["intensity_cap"])

    return {
        key: value * clamped_intensity
        for key, value in profile.items()
        if key != "intensity_cap"
    }


def calc_coalition_utility(
    own_strength: float,
    ally_strength: float,
    threat_strength: float,
    bilateral_trust: float,
    own_economic: float,
    ally_economic: float
) -> float:
    """
    Calculate utility of forming a coalition.

    Formula:
        utility = (threat_strength - max(own_strength, ally_strength))
                * bilateral_trust
                + (own_economic + ally_economic) * 0.1

    Args:
        own_strength: Military strength of own faction
        ally_strength: Military strength of ally
        threat_strength: Strength of common threat
        bilateral_trust: Trust between factions (0-1)
        own_economic: Own economic capacity
        ally_economic: Ally economic capacity

    Returns:
        Coalition utility (negative is beneficial)
    """
    threat_advantage = threat_strength - max(own_strength, ally_strength)
    military_benefit = threat_advantage * bilateral_trust
    economic_benefit = (own_economic + ally_economic) * 0.1

    return military_benefit + economic_benefit


def calc_coalition_stability(
    bilateral_trust: float,
    shared_threat_level: float,
    turns_active: int,
    members_at_war: bool
) -> float:
    """
    Calculate stability of an active coalition.

    Formula:
        If members_at_war: return 0.0
        inertia = min(0.2, turns_active * 0.01)
        stability = bilateral_trust * 0.4
                  + shared_threat_level * 0.3
                  + inertia
                  + 0.1

    Args:
        bilateral_trust: Trust between coalition members (0-1)
        shared_threat_level: Common threat level (0-1)
        turns_active: Number of turns coalition has existed
        members_at_war: Whether coalition members are at war

    Returns:
        Coalition stability (0-1)
    """
    if members_at_war:
        return 0.0

    inertia = min(0.2, turns_active * 0.01)
    stability = (
        bilateral_trust * 0.4
        + shared_threat_level * 0.3
        + inertia
        + 0.1
    )

    return _clamp(stability)


def calc_combat_outcome(
    fleet_strength_a: float,
    fleet_strength_b: float,
    tactical_a: float,
    tactical_b: float,
    ai_superiority_a: float,
    ai_superiority_b: float,
    battlefield_modifier: float = 1.0,
    terrain_advantage_a: float = 1.0,
    terrain_advantage_b: float = 1.0,
    supply_a: float = 1.0,
    supply_b: float = 1.0,
    morale_a: float = 1.0,
    morale_b: float = 1.0
) -> float:
    """
    Calculate combat outcome ratio.

    Formula:
        W = (FS_A * TA_A * AS_A * terrain_a * supply_a * morale_a * battlefield_modifier)
          / max(0.01, FS_B * TA_B * AS_B * terrain_b * supply_b * morale_b)

    W > 1.0: A wins, W < 1.0: B wins

    Args:
        fleet_strength_a: Fleet size/strength of side A
        fleet_strength_b: Fleet size/strength of side B
        tactical_a: Tactical skill of side A (0-1)
        tactical_b: Tactical skill of side B (0-1)
        ai_superiority_a: AI/tech advantage of side A (0-1)
        ai_superiority_b: AI/tech advantage of side B (0-1)
        battlefield_modifier: Environmental modifier (default 1.0)
        terrain_advantage_a: Terrain advantage for A (default 1.0)
        terrain_advantage_b: Terrain advantage for B (default 1.0)
        supply_a: Supply level for A (default 1.0)
        supply_b: Supply level for B (default 1.0)
        morale_a: Morale level for A (default 1.0)
        morale_b: Morale level for B (default 1.0)

    Returns:
        Combat outcome ratio (higher = A wins)
    """
    numerator = (
        fleet_strength_a * tactical_a * ai_superiority_a
        * terrain_advantage_a * supply_a * morale_a
        * battlefield_modifier
    )

    denominator = max(
        0.01,
        fleet_strength_b * tactical_b * ai_superiority_b
        * terrain_advantage_b * supply_b * morale_b
    )

    return numerator / denominator


def calc_combat_losses(
    outcome_ratio: float,
    losing_strength: float,
    duration_turns: int
) -> Tuple[float, float]:
    """
    Calculate losses for both sides of combat.

    Formula:
        winner_losses = losing_strength * 0.1 * duration_turns / max(1, outcome_ratio)
        loser_losses = losing_strength * 0.2 * duration_turns * min(outcome_ratio, 3.0)

    Args:
        outcome_ratio: Combat outcome W value
        losing_strength: Base strength of losing side
        duration_turns: Combat duration in turns

    Returns:
        Tuple of (winner_losses, loser_losses) both clamped [0, 0.9]
    """
    winner_losses = (
        losing_strength * 0.1 * duration_turns / max(1, outcome_ratio)
    )

    loser_losses = (
        losing_strength * 0.2 * duration_turns * min(outcome_ratio, 3.0)
    )

    winner_losses = _clamp(winner_losses, 0.0, 0.9)
    loser_losses = _clamp(loser_losses, 0.0, 0.9)

    return (winner_losses, loser_losses)


def calc_q_learning_update(
    current_q: float,
    reward: float,
    max_future_q: float,
    *,
    learning_rate: float = 0.1,
    discount_factor: float = 0.9
) -> float:
    """
    Calculate Q-learning update for reinforcement learning.

    Formula:
        Q(s,a) = Q(s,a) + α(R + γ max Q(s',a') - Q(s,a))

    Args:
        current_q: Current Q-value
        reward: Immediate reward from action
        max_future_q: Maximum Q-value in next state
        learning_rate: Learning rate (alpha)
        discount_factor: Discount factor (gamma)

    Returns:
        Updated Q-value
    """
    td_target = reward + discount_factor * max_future_q
    update = learning_rate * (td_target - current_q)
    return current_q + update


def calc_bayesian_faction_decision(
    scenario_weights: Dict[str, float],
    memory_weights: Dict[str, float],
    bias_modifier: float = 1.0
) -> Dict[str, float]:
    """
    Calculate Bayesian faction decision probabilities.

    Formula:
        P(action) = normalize(scenario_weight * memory_weight * bias_modifier)

    Args:
        scenario_weights: Dict mapping actions to scenario probabilities
        memory_weights: Dict mapping actions to historical success rates
        bias_modifier: Cognitive bias multiplier (default 1.0)

    Returns:
        Dict of normalized action probabilities summing to 1.0
    """
    joint_probs = {}
    total = 0.0

    for action in scenario_weights:
        if action in memory_weights:
            prob = (
                scenario_weights[action]
                * memory_weights[action]
                * bias_modifier
            )
            joint_probs[action] = max(0.0, prob)
            total += joint_probs[action]

    if total == 0.0:
        return {action: 1.0 / len(joint_probs) for action in joint_probs}

    return {action: prob / total for action, prob in joint_probs.items()}


def calc_sentinel_adaptation(
    current_skill: float,
    mission_success: bool,
    mission_difficulty: float,
    *,
    alpha: float = 0.1,
    beta: float = 0.05
) -> float:
    """
    Calculate sentinel operative skill adaptation.

    Formula:
        S_new = S_old + alpha * success * difficulty
               - beta * (1-success) * difficulty

    Args:
        current_skill: Current skill level (0-1)
        mission_success: Whether mission succeeded
        mission_difficulty: Difficulty of mission (0-1)
        alpha: Learning rate for success
        beta: Learning rate for failure

    Returns:
        Updated skill level (0-1)
    """
    success_val = 1.0 if mission_success else 0.0
    delta = (
        alpha * success_val * mission_difficulty
        - beta * (1.0 - success_val) * mission_difficulty
    )
    return _clamp(current_skill + delta)


def calc_economic_equilibrium(
    supply: float,
    demand: float,
    elasticity: float = 1.0
) -> float:
    """
    Calculate economic equilibrium price.

    Formula:
        P_eq = (demand / max(0.01, supply)) ** (1/max(0.1, elasticity))

    Args:
        supply: Available supply
        demand: Market demand
        elasticity: Price elasticity (default 1.0)

    Returns:
        Equilibrium price (0.01-100.0)
    """
    safe_supply = max(0.01, supply)
    safe_elasticity = max(0.1, elasticity)

    price = (demand / safe_supply) ** (1.0 / safe_elasticity)
    return _clamp(price, 0.01, 100.0)


def calc_trade_flow(
    price_a: float,
    price_b: float,
    route_capacity: float,
    tariff_rate: float,
    security: float,
    is_blockaded: bool
) -> float:
    """
    Calculate trade flow along a route.

    Formula:
        If blockaded: return 0.0
        price_diff = abs(price_a - price_b)
        flow = price_diff * route_capacity * security * (1 - tariff_rate)

    Args:
        price_a: Price in region A
        price_b: Price in region B
        route_capacity: Route capacity limit
        tariff_rate: Tariff rate (0-1)
        security: Route security level (0-1)
        is_blockaded: Whether route is blockaded

    Returns:
        Trade flow (0 to route_capacity)
    """
    if is_blockaded:
        return 0.0

    price_diff = abs(price_a - price_b)
    flow = price_diff * route_capacity * security * (1.0 - tariff_rate)

    return _clamp(flow, 0.0, route_capacity)


def calc_corporate_capture_pressure(
    economic_influence: float,
    institutional_control: float,
    corruption_base: float = 0.1
) -> float:
    """
    Calculate pressure of corporate capture on institutions.

    Formula:
        pressure = economic_influence * (1 - institutional_control) + corruption_base

    Args:
        economic_influence: Corporate economic influence (0-1)
        institutional_control: Institutional independence (0-1)
        corruption_base: Base corruption level (default 0.1)

    Returns:
        Capture pressure (0-1)
    """
    pressure = (
        economic_influence * (1.0 - institutional_control)
        + corruption_base
    )
    return _clamp(pressure)


def calc_propaganda_effectiveness(
    source_credibility: float,
    target_info_freedom: float,
    narrative_alignment: float,
    media_reach: float
) -> float:
    """
    Calculate effectiveness of propaganda campaign.

    Formula:
        effectiveness = source_credibility * media_reach * narrative_alignment
                      * (1 - target_info_freedom * 0.5)

    Args:
        source_credibility: Credibility of propaganda source (0-1)
        target_info_freedom: Information freedom in target (0-1)
        narrative_alignment: Alignment with target beliefs (0-1)
        media_reach: Reach of media (0-1)

    Returns:
        Propaganda effectiveness (0-1)
    """
    effectiveness = (
        source_credibility * media_reach * narrative_alignment
        * (1.0 - target_info_freedom * 0.5)
    )
    return _clamp(effectiveness)


def calc_media_legitimacy_impact(
    public_opinion: float,
    narrative_effectiveness: float,
    current_legitimacy: float
) -> float:
    """
    Calculate media impact on institutional legitimacy.

    Formula:
        delta = (public_opinion - 0.5) * narrative_effectiveness * 0.1
        new_legitimacy = current_legitimacy + delta

    Args:
        public_opinion: Public opinion level (0-1)
        narrative_effectiveness: Effectiveness of narrative (0-1)
        current_legitimacy: Current legitimacy level (0-1)

    Returns:
        Updated legitimacy (0-1)
    """
    delta = (public_opinion - 0.5) * narrative_effectiveness * 0.1
    return _clamp(current_legitimacy + delta)


def calc_precursor_activation_risk(
    power_level: float,
    stability: float,
    controller_tech_level: float
) -> float:
    """
    Calculate risk of activating precursor technology.

    Formula:
        risk = power_level * (1 - stability) * (1 - controller_tech_level * 0.5)

    Args:
        power_level: Power level of artifact (0-1)
        stability: Stability of artifact (0-1)
        controller_tech_level: Tech level of controller (0-1)

    Returns:
        Activation risk (0-1)
    """
    risk = power_level * (1.0 - stability) * (1.0 - controller_tech_level * 0.5)
    return _clamp(risk)


def calc_precursor_power_output(
    activation_level: float,
    site_stability: float,
    origin_modifier: float = 1.0
) -> Dict[str, float]:
    """
    Calculate power output benefits from precursor activation.

    Formula:
        tech_bonus = activation_level * 0.1 * origin_modifier * site_stability
        military_bonus = activation_level * 0.05 * origin_modifier * site_stability
        economic_bonus = activation_level * 0.07 * origin_modifier * site_stability
        risk_level = activation_level * (1 - site_stability) * 0.3

    Args:
        activation_level: Level of activation (0-1)
        site_stability: Stability of site (0-1)
        origin_modifier: Modifier based on artifact origin (default 1.0)

    Returns:
        Dict with tech_bonus, military_bonus, economic_bonus, risk_level
    """
    base_factor = activation_level * origin_modifier * site_stability

    return {
        "tech_bonus": base_factor * 0.1,
        "military_bonus": base_factor * 0.05,
        "economic_bonus": base_factor * 0.07,
        "risk_level": activation_level * (1.0 - site_stability) * 0.3,
    }


def calc_mission_success_probability(
    operative_skill: float,
    mission_difficulty: float,
    support_level: float = 0.0,
    counter_intel: float = 0.0
) -> float:
    """
    Calculate probability of special ops mission success.

    Formula:
        base = operative_skill * 0.6 + support_level * 0.2 + 0.2
        modified = base * (1 - counter_intel * 0.5) * (1 - mission_difficulty * 0.3)

    Args:
        operative_skill: Skill of operative (0-1)
        mission_difficulty: Difficulty of mission (0-1)
        support_level: Level of support (default 0.0)
        counter_intel: Counter-intelligence opposition (default 0.0)

    Returns:
        Success probability (0.05-0.95)
    """
    base = operative_skill * 0.6 + support_level * 0.2 + 0.2
    modified = (
        base
        * (1.0 - counter_intel * 0.5)
        * (1.0 - mission_difficulty * 0.3)
    )
    return _clamp(modified, 0.05, 0.95)


def calc_culture_spread_rate(
    source_influence: float,
    target_cultural_openness: float,
    distance_penalty: float = 0.0,
    is_subversive: bool = False
) -> float:
    """
    Calculate rate of cultural spread.

    Formula:
        base_rate = source_influence * target_cultural_openness * 0.1
        If subversive: base_rate *= 0.5 (ignores distance penalty)
        Else: base_rate *= (1 - distance_penalty)

    Args:
        source_influence: Cultural influence of source (0-1)
        target_cultural_openness: Openness to culture (0-1)
        distance_penalty: Geographic distance penalty (default 0.0)
        is_subversive: Whether spread is subversive (default False)

    Returns:
        Culture spread rate (0-0.2)
    """
    base_rate = source_influence * target_cultural_openness * 0.1

    if is_subversive:
        base_rate *= 0.5
    else:
        base_rate *= (1.0 - distance_penalty)

    return _clamp(base_rate, 0.0, 0.2)


def calc_fleet_supply_decay(
    distance_from_base: float,
    fleet_size: float,
    route_security: float
) -> float:
    """
    Calculate supply line decay per turn.

    Formula:
        decay = distance_from_base * 0.02 * fleet_size / max(0.1, route_security)

    Args:
        distance_from_base: Distance from supply base
        fleet_size: Size of fleet (0-1)
        route_security: Security of supply route (0-1)

    Returns:
        Supply decay per turn (0-0.5)
    """
    decay = (
        distance_from_base * 0.02 * fleet_size / max(0.1, route_security)
    )
    return _clamp(decay, 0.0, 0.5)


def calc_war_exhaustion(
    total_losses: float,
    war_duration: int,
    economic_strain: float,
    population_stability: float
) -> float:
    """
    Calculate cumulative war exhaustion.

    Formula:
        exhaustion = total_losses * 0.3
                   + war_duration * 0.01
                   + economic_strain * 0.2
                   + (1 - population_stability) * 0.2

    Args:
        total_losses: Cumulative military losses (0-1)
        war_duration: Duration of war in turns
        economic_strain: Economic strain from war (0-1)
        population_stability: Population stability (0-1)

    Returns:
        War exhaustion level (0-1)
    """
    exhaustion = (
        total_losses * 0.3
        + war_duration * 0.01
        + economic_strain * 0.2
        + (1.0 - population_stability) * 0.2
    )
    return _clamp(exhaustion)

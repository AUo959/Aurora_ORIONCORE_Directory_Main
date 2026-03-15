#!/usr/bin/env python3
"""
GUMAS v3.0 — Validation Suite
==============================
Anchor: GUMAS-ENGINE-VALIDATE-V3
Seed:   EOS_SEED_ORION
Ethics: Picard_Delta_3
DLP:    L2_ENGINE_V3
Version: 3.0.0

Validates all v3.0 module formulas, state transitions, the
20-phase engine lifecycle, and the CharForge ORION capsule system.
Runs in standalone mode (no v2.0 engine required) for CI/CD integration.

Test structure:
    Section 1:  Population module (6 tests)
    Section 2:  Technology module (5 tests)
    Section 3:  Negotiation module (6 tests)
    Section 4:  Intelligence module (5 tests)
    Section 5:  Rebellion module (5 tests)
    Section 6:  Engine integration (5 full-turn tests)
    Section 7:  Reproducibility (seed test)
    Section 8:  CharForge — ORION Capsule Bundle v0.2.0 (12 tests)

Total: 45 tests
Usage:
    python validate_v3.py
    python validate_v3.py --verbose
"""

from __future__ import annotations

import json
import struct
import sys
import os
import argparse
import tempfile
import traceback
import types
from pathlib import Path
from typing import Callable, List, Tuple

# Add forge directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from population      import *
from technology      import *
from negotiation     import *
from intelligence    import *
from rebellion       import *
from engine_v3_patch import GUMASEngineV3
from charforge       import (
    generate_capsule, verify_capsule, tick_update_state_bin,
    capsule_summary, _encode_state_bin, _decode_state_bin,
    SEVEN_FILES, STATE_VEC_LEN, STATE_VECTOR_SLOTS,
    DECLARED_LAYER, ETHICS_PROTOCOL, ANCHOR_SEED,
    _BIAS_VOICE, _FACTION_VALUES,
)


# ============================================================================
# TEST HARNESS
# ============================================================================

PASS = "  ✓ PASS"
FAIL = "  ✗ FAIL"

class TestSuite:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.passed = 0
        self.failed = 0
        self.failures: List[Tuple[str, str]] = []

    def run(self, name: str, fn: Callable[[], bool]) -> None:
        try:
            result = fn()
            if result:
                self.passed += 1
                if self.verbose:
                    print(f"{PASS}: {name}")
            else:
                self.failed += 1
                self.failures.append((name, "returned False"))
                print(f"{FAIL}: {name}")
        except Exception as e:
            self.failed += 1
            tb = traceback.format_exc() if self.verbose else str(e)
            self.failures.append((name, tb))
            print(f"{FAIL}: {name} — {e}")

    def summary(self) -> bool:
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"GUMAS v3.0 Validation: {self.passed}/{total} tests passed")
        if self.failures:
            print("\nFailed tests:")
            for name, reason in self.failures:
                print(f"  • {name}: {reason}")
        print("=" * 60)
        return self.failed == 0


def _approx(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) < tol


def _in_range(v: float, lo: float, hi: float) -> bool:
    return lo <= v <= hi


# ============================================================================
# SECTION 1: POPULATION
# ============================================================================

def test_pop_growth_at_capacity():
    """Growth approaches zero when at carrying capacity."""
    growth = calc_population_growth(1.0, 0.02, 0.01, carrying_capacity=1.0)
    # At P=K, logistic term (1 - P/K/steepness) is small but not zero
    # just verify it's much less than at P=0.5
    growth_half = calc_population_growth(0.5, 0.02, 0.01, carrying_capacity=1.0)
    return growth < growth_half

def test_pop_growth_overpopulation_negative():
    """Population declines when far over capacity (birth > death, logistic suppression negative)."""
    # P=2.5 far above K=1.0; suppression term (1 - P/K) = -1.5 makes growth negative
    growth = calc_population_growth(2.5, 0.05, 0.01, carrying_capacity=1.0)
    return growth < 0.0

def test_migration_pressure_range():
    """Migration pressure always in [-1, 1]."""
    p = calc_migration_pressure(0.3, 0.7, 0.5, 0.1, 0.9, 1.0)
    return _in_range(p, -1.0, 1.0)

def test_migration_pressure_direction():
    """Distressed source vs neutral destination: positive (outward) pressure."""
    # src: high unemployment, low food, high stress vs dst: neutral, below capacity
    p = calc_migration_pressure(
        src_unemployment=0.5, src_food_security=0.2, src_demographic_stress=0.8,
        dst_unemployment=0.5, dst_food_security=0.5, dst_population_index=0.9
    )
    return p > 0.0

def test_demographic_stress_clamped():
    """Demographic stress always in [0, 1]."""
    s = calc_demographic_stress(2.5, 0.0, 1.0, 1.0, 1.0, 1.0)
    return _in_range(s, 0.0, 1.0)

def test_refugee_no_conflict():
    """No refugees without active conflict."""
    r = calc_refugee_generation(in_conflict=False, conflict_count=0, population_index=1.0)
    return _approx(r, 0.0)


# ============================================================================
# SECTION 2: TECHNOLOGY
# ============================================================================

def test_tech_advance_diminishing_returns():
    """R&D rate decreases as tech level approaches max."""
    rate_low  = calc_tech_advance_rate(0.5, 0.8, 1.0, 5.0)
    rate_high = calc_tech_advance_rate(0.5, 0.8, 4.5, 5.0)
    return rate_low > rate_high

def test_tech_diffusion_zero_gap():
    """No diffusion when gap is zero."""
    d = calc_tech_diffusion(gap=0.0, trust_score=0.9)
    return _approx(d, 0.0)

def test_military_tech_advantage_cap():
    """Military tech advantage is capped at ±0.40."""
    adv = calc_military_tech_advantage(5.0, 0.0)
    return _in_range(adv, -0.40, 0.40)

def test_civilian_tech_multiplier_minimum():
    """Civilian tech multiplier is at least 1.0."""
    m = calc_civilian_tech_multiplier(0.0, 0.0, 0.0)
    return m >= 1.0

def test_tech_espionage_yield_range():
    """Tech espionage yield is in [0, 1]."""
    y = calc_tech_espionage_yield(0.9, 4.5, 0.8)
    return _in_range(y, 0.0, 1.0)


# ============================================================================
# SECTION 3: NEGOTIATION
# ============================================================================

def test_negotiation_success_range():
    """Negotiation success probability always in [0, 1]."""
    p = calc_negotiation_success(0.8, 0.7, 0.9, 8, 0.15, True)
    return _in_range(p, 0.0, 1.0)

def test_negotiation_back_channel_bonus():
    """Back-channel boosts success probability."""
    p_public = calc_negotiation_success(0.5, 0.5, 0.5, 3, 0.0, False)
    p_bc     = calc_negotiation_success(0.5, 0.5, 0.5, 3, 0.0, True)
    return p_bc > p_public

def test_concession_threshold_weak_batna():
    """Weak BATNA increases concession willingness."""
    t_weak   = calc_concession_threshold(batna=0.1, current_position=0.8, round_number=3, urgency=0.5)
    t_strong = calc_concession_threshold(batna=0.9, current_position=0.8, round_number=3, urgency=0.5)
    return t_weak > t_strong

def test_batna_range():
    """BATNA strength always in [0, 1]."""
    b = calc_batna_strength(0.7, 0.6, 0.8, 0.4)
    return _in_range(b, 0.0, 1.0)

def test_diplomatic_crisis_high_trust():
    """Crisis is more severe when trust was high (betrayal effect)."""
    sev_high_trust = calc_diplomatic_crisis_severity(0.9, 5)
    sev_low_trust  = calc_diplomatic_crisis_severity(0.1, 5)
    return sev_high_trust > sev_low_trust

def test_ultimatum_compliance_high_resolve():
    """High issuer resolve increases compliance probability."""
    p_high = calc_ultimatum_compliance(0.95, 0.3, 0.1, 0)
    p_low  = calc_ultimatum_compliance(0.10, 0.3, 0.1, 0)
    return p_high > p_low


# ============================================================================
# SECTION 4: INTELLIGENCE
# ============================================================================

def test_sigint_yield_range():
    """SIGINT yield always in [0, 1]."""
    y = calc_sigint_yield(0.7, 0.5, 0.4)
    return _in_range(y, 0.0, 1.0)

def test_sigint_penalised_by_ci():
    """Strong counter-intel reduces SIGINT yield."""
    y_no_ci = calc_sigint_yield(0.7, 0.5, target_ci_strength=0.0)
    y_ci    = calc_sigint_yield(0.7, 0.5, target_ci_strength=0.9)
    return y_no_ci > y_ci

def test_humint_totalitarian_harder():
    """HUMINT penetration lower in totalitarian states."""
    h_open  = calc_humint_penetration(0.6, 0.2, SurveillanceLevel.OPEN.value)
    h_total = calc_humint_penetration(0.6, 0.2, SurveillanceLevel.TOTALITARIAN.value)
    return h_open > h_total

def test_intel_fusion_synergy():
    """Multi-source fusion with all strong sources exceeds single source."""
    single = calc_intelligence_fusion(0.5, 0.0, 0.0, 0.0)
    multi  = calc_intelligence_fusion(0.5, 0.5, 0.4, 0.3)
    return multi > single

def test_surveillance_penalty():
    """Totalitarian surveillance inflicts larger legitimacy penalty."""
    p_mod   = calc_surveillance_legitimacy_penalty(SurveillanceLevel.MODERATE)
    p_total = calc_surveillance_legitimacy_penalty(SurveillanceLevel.TOTALITARIAN)
    return p_total < p_mod < 0  # both negative, totalitarian more so


# ============================================================================
# SECTION 5: REBELLION
# ============================================================================

def test_rebellion_onset_high_stress():
    """High stress + low legitimacy produces meaningful onset probability."""
    p = calc_rebellion_onset_probability(0.9, 0.1, 0.2, 0.1)
    return p > 0.3

def test_rebellion_onset_stable_state():
    """Stable, legitimate state has near-zero onset probability."""
    p = calc_rebellion_onset_probability(0.1, 0.95, 0.9, 0.8)
    return p < 0.05

def test_insurgency_strength_repressed():
    """Strong repression produces negative strength gain."""
    delta = calc_insurgency_strength(
        popular_support=0.2,
        economic_grievance=0.2,
        external_support=0.0,
        repression_level=0.9,
    )
    return delta < 0.0

def test_state_fragmentation_risk_range():
    """Fragmentation risk always in [0, 0.8]."""
    r = calc_state_fragmentation_risk(0.6, 0.7, 0.2, 15)
    return _in_range(r, 0.0, 0.80)

def test_civil_war_escalation_quadratic():
    """Civil war probability rises faster as all drivers increase."""
    p_low  = calc_civil_war_escalation(0.2, 0.2, 0.2)
    p_high = calc_civil_war_escalation(0.8, 0.8, 0.8)
    return p_high > p_low * 4  # quadratic means disproportionate jump


# ============================================================================
# SECTION 6: ENGINE INTEGRATION
# ============================================================================

def test_engine_initializes():
    """Engine initializes without error."""
    engine = GUMASEngineV3(seed=42)
    engine.init_scenario()
    return engine._initialized

def test_engine_single_step():
    """Engine completes one full step without error."""
    engine = GUMASEngineV3(seed=42)
    engine.init_scenario()
    _, v3r = engine.full_step()
    return v3r.turn == 1

def test_engine_10_turns():
    """Engine runs 10 turns cleanly; no errors."""
    engine = GUMASEngineV3(seed=42)
    engine.init_scenario()
    results = engine.run_v3(10)
    return len(results) == 10 and all(r.turn > 0 for r in results)

def test_engine_export():
    """Engine exports v3 state to JSON without error."""
    import tempfile
    engine = GUMASEngineV3(seed=42)
    engine.init_scenario()
    engine.run_v3(3)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    engine.export_v3_state(path)
    import json
    with open(path) as fh:
        data = json.load(fh)
    return "population" in data and "technology" in data

def test_engine_state_mutation():
    """Population state mutates across turns (not frozen)."""
    engine = GUMASEngineV3(seed=42)
    engine.init_scenario()
    fids = list(engine._v3_state.population.keys())
    initial = {fid: engine._v3_state.population[fid].population_index for fid in fids}
    engine.run_v3(5)
    final   = {fid: engine._v3_state.population[fid].population_index for fid in fids}
    # At least one faction's population should have changed
    return any(abs(initial[fid] - final[fid]) > 1e-6 for fid in fids)


# ============================================================================
# SECTION 7: REPRODUCIBILITY
# ============================================================================

def test_reproducibility():
    """Identical seed produces identical v3 events after 5 turns."""
    def run_and_collect(seed):
        engine = GUMASEngineV3(seed=seed)
        engine.init_scenario()
        results = engine.run_v3(5)
        return [len(r.v3_events) for r in results]

    run1 = run_and_collect(99)
    run2 = run_and_collect(99)
    return run1 == run2


# ============================================================================
# MAIN
# ============================================================================

# ============================================================================
# SECTION 8: CharForge — ORION Capsule Bundle v0.2.0
# ============================================================================
#
# All tests use duck-typed SimpleNamespace objects so that Section 8 runs
# in fully standalone mode — no GUMAS v2.0 engine or models.py required.
#
# State vector precision: float16 has ~3 significant decimal digits.
# Roundtrip tolerance is set to 0.005 (within float16 error bounds).
# ============================================================================

_FLOAT16_TOL: float = 0.005   # float16 precision tolerance for state roundtrip


def _make_test_leader(
    leader_id:               str   = "TEST_LEADER",
    name:                    str   = "Adaline Voss",
    role:                    str   = "Chancellor",
    faction_id:              str   = "TEST_FACTION",
    dominant_bias:           str   = "confirmation_bias",
    secondary_biases:        list  = None,
    bias_intensity:          float = 0.72,
    plasticity:              float = 0.35,
    evidence_gain_multiplier:float = 1.2,
    risk_tolerance:          float = 0.45,
    diplomacy_openness:      float = 0.60,
    escalation_threshold:    float = 0.55,
    oversight_resistance:    float = 0.65,    # > 0.4 → style_ctl active
    public_legitimacy:       float = 0.78,
    elite_support:           float = 0.62,
    institutional_control:   float = 0.50,
    war_pressure:            float = 0.30,
    economic_shock:          float = 0.12,
    war_losses:              int   = 3,
    betrayals:               int   = 1,
    scandals:                int   = 0,
    certainty:               str   = "STAGING",
) -> types.SimpleNamespace:
    """Return a duck-typed leader compatible with charforge.py API."""
    # dominant_bias stored as a tiny object with a .value attribute
    bias_obj = types.SimpleNamespace(value=dominant_bias)
    sec_biases = [types.SimpleNamespace(value=b) for b in (secondary_biases or [])]
    cert_obj   = types.SimpleNamespace(value=certainty)
    return types.SimpleNamespace(
        leader_id                = leader_id,
        name                     = name,
        role                     = role,
        faction_id               = faction_id,
        dominant_bias            = bias_obj,
        secondary_biases         = sec_biases,
        bias_intensity           = bias_intensity,
        plasticity               = plasticity,
        evidence_gain_multiplier = evidence_gain_multiplier,
        risk_tolerance           = risk_tolerance,
        diplomacy_openness       = diplomacy_openness,
        escalation_threshold     = escalation_threshold,
        oversight_resistance     = oversight_resistance,
        public_legitimacy        = public_legitimacy,
        elite_support            = elite_support,
        institutional_control    = institutional_control,
        war_pressure             = war_pressure,
        economic_shock           = economic_shock,
        war_losses               = war_losses,
        betrayals                = betrayals,
        scandals                 = scandals,
        certainty                = cert_obj,
    )


def _make_test_faction(
    faction_id:             str   = "TEST_FACTION",
    name:                   str   = "Solari Compact",
    faction_type:           str   = "federation",
    military_strength:      float = 0.64,
    economic_strength:      float = 0.55,
    technology_level:       float = 0.48,
    population_stability:   float = 0.71,
    reputation:             float = 0.68,
    verification_demand:    float = 0.45,
    deal_discount:          float = 0.05,
    coalition_invite_weight:float = 0.60,
    economic_potential:     float = 0.75,
    trust_scores:           dict  = None,
) -> types.SimpleNamespace:
    """Return a duck-typed faction compatible with charforge.py API."""
    ftype_obj = types.SimpleNamespace(value=faction_type)
    return types.SimpleNamespace(
        faction_id              = faction_id,
        name                    = name,
        faction_type            = ftype_obj,
        military_strength       = military_strength,
        economic_strength       = economic_strength,
        technology_level        = technology_level,
        population_stability    = population_stability,
        reputation              = reputation,
        verification_demand     = verification_demand,
        deal_discount           = deal_discount,
        coalition_invite_weight = coalition_invite_weight,
        economic_potential      = economic_potential,
        trust_scores            = trust_scores or {},
    )


def _generate_test_capsule(tmp_dir: Path) -> Path:
    """Helper: generate a standard test capsule and return its bundle root."""
    leader  = _make_test_leader()
    faction = _make_test_faction()
    return generate_capsule(leader, faction, tmp_dir, overwrite=True)


# ── Test 8.1 ─────────────────────────────────────────────────────────────────

def test_capsule_all_seven_files() -> bool:
    """generate_capsule produces a capsule/ dir containing all seven required files."""
    with tempfile.TemporaryDirectory() as tmp:
        bundle = _generate_test_capsule(Path(tmp))
        capsule_dir = bundle / "capsule"
        return all((capsule_dir / name).exists() for name in SEVEN_FILES)


# ── Test 8.2 ─────────────────────────────────────────────────────────────────

def test_capsule_verify_after_generate() -> bool:
    """verify_capsule returns True immediately after a clean generate_capsule call."""
    with tempfile.TemporaryDirectory() as tmp:
        bundle = _generate_test_capsule(Path(tmp))
        return verify_capsule(bundle) is True


# ── Test 8.3 ─────────────────────────────────────────────────────────────────

def test_capsule_state_bin_roundtrip() -> bool:
    """
    Encoding then decoding the state vector preserves values within float16 tolerance.

    Evidence: float16 has ~3.3 significant decimal digits (machine epsilon ≈ 0.001).
    Tolerance is set to 0.005 — tighter than any authored field differs from itself
    in practice, loose enough to absorb float16 quantisation error.
    """
    leader  = _make_test_leader()
    faction = _make_test_faction()

    original = [
        leader.bias_intensity,
        leader.plasticity,
        leader.evidence_gain_multiplier / 2.0,   # normalised slot
        leader.risk_tolerance,
        leader.diplomacy_openness,
        leader.escalation_threshold,
        leader.oversight_resistance,
        leader.public_legitimacy,
        leader.elite_support,
        leader.institutional_control,
        leader.war_pressure,
        abs(leader.economic_shock),
        faction.military_strength,
        faction.economic_strength,
        faction.technology_level,
        faction.population_stability,
        faction.reputation,
        faction.verification_demand,
        faction.deal_discount,
        faction.coalition_invite_weight,
        faction.economic_potential,
    ]

    encoded = _encode_state_bin(leader, faction)
    decoded = _decode_state_bin(encoded)

    if len(decoded) != STATE_VEC_LEN:
        return False
    return all(abs(decoded[i] - original[i]) < _FLOAT16_TOL for i in range(STATE_VEC_LEN))


# ── Test 8.4 ─────────────────────────────────────────────────────────────────

def test_capsule_identity_fields() -> bool:
    """identity.json contains correct capsule_id, declared_layer, ethics_protocol, anchor_seed."""
    with tempfile.TemporaryDirectory() as tmp:
        bundle  = _generate_test_capsule(Path(tmp))
        capsule = bundle / "capsule"
        identity = json.loads((capsule / "identity.json").read_text(encoding="utf-8"))
        return (
            identity.get("capsule_id")      == "TEST_LEADER"
            and identity.get("declared_layer")  == DECLARED_LAYER
            and identity.get("ethics_protocol") == ETHICS_PROTOCOL
            and identity.get("anchor_seed")     == ANCHOR_SEED
        )


# ── Test 8.5 ─────────────────────────────────────────────────────────────────

def test_capsule_traits_bias_voice() -> bool:
    """
    traits.json voice matches the bias archetype table entry for the leader's
    dominant_bias (confirmation_bias → tone='authoritative', cadence='direct').
    """
    with tempfile.TemporaryDirectory() as tmp:
        bundle = _generate_test_capsule(Path(tmp))
        capsule = bundle / "capsule"
        traits  = json.loads((capsule / "traits.json").read_text(encoding="utf-8"))
        voice   = traits.get("voice", {})
        expected = _BIAS_VOICE.get("confirmation_bias", {})
        return (
            voice.get("tone")    == expected.get("tone")
            and voice.get("cadence") == expected.get("cadence")
        )


# ── Test 8.6 ─────────────────────────────────────────────────────────────────

def test_capsule_traits_faction_values() -> bool:
    """
    traits.json values list matches the faction type table entry for
    'federation' (= ["consensus", "rule_of_law", "collective_security"]).
    """
    with tempfile.TemporaryDirectory() as tmp:
        bundle = _generate_test_capsule(Path(tmp))
        capsule = bundle / "capsule"
        traits  = json.loads((capsule / "traits.json").read_text(encoding="utf-8"))
        expected_values = _FACTION_VALUES.get("federation", [])
        return traits.get("values") == expected_values


# ── Test 8.7 ─────────────────────────────────────────────────────────────────

def test_capsule_knowledge_stressor_rec() -> bool:
    """
    knowledge.jsonl contains a stressor record when leader has war_losses > 0.
    The record's tags must include 'stressors'.
    """
    with tempfile.TemporaryDirectory() as tmp:
        leader  = _make_test_leader(war_losses=5, betrayals=2)
        faction = _make_test_faction()
        bundle  = generate_capsule(leader, faction, Path(tmp), overwrite=True)
        capsule = bundle / "capsule"
        records = [
            json.loads(line)
            for line in (capsule / "knowledge.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        return any("stressors" in rec.get("tags", []) for rec in records)


# ── Test 8.8 ─────────────────────────────────────────────────────────────────

def test_capsule_knowledge_trust_records() -> bool:
    """
    knowledge.jsonl contains trust records for each entry in faction.trust_scores
    (up to 5). Test uses 2 entries: one allied, one adversarial.
    """
    with tempfile.TemporaryDirectory() as tmp:
        faction = _make_test_faction(trust_scores={
            "RIVAL_FACTION":   0.15,   # adversarial
            "ALLY_FACTION":    0.82,   # allied
        })
        leader = _make_test_leader()
        bundle = generate_capsule(leader, faction, Path(tmp), overwrite=True)
        capsule = bundle / "capsule"
        records = [
            json.loads(line)
            for line in (capsule / "knowledge.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        trust_ids = {rec["id"] for rec in records if "trust" in rec.get("tags", [])}
        return (
            "TEST_LEADER__trust_RIVAL_FACTION" in trust_ids
            and "TEST_LEADER__trust_ALLY_FACTION" in trust_ids
        )


# ── Test 8.9 ─────────────────────────────────────────────────────────────────

def test_capsule_tick_update_state_bin() -> bool:
    """
    tick_update_state_bin writes new float16 values and verify_capsule still passes.

    Procedure:
    1. Generate capsule with leader bias_intensity=0.72.
    2. Call tick_update_state_bin with modified leader (bias_intensity=0.30).
    3. Decode new state.bin and confirm slot 0 ≈ 0.30.
    4. verify_capsule returns True (manifest refreshed).
    """
    with tempfile.TemporaryDirectory() as tmp:
        leader  = _make_test_leader(bias_intensity=0.72)
        faction = _make_test_faction()
        bundle  = generate_capsule(leader, faction, Path(tmp), overwrite=True)

        # Modify and update
        leader.bias_intensity = 0.30
        tick_update_state_bin(leader, faction, bundle)

        # Verify new state
        raw     = (bundle / "capsule" / "state.bin").read_bytes()
        decoded = _decode_state_bin(raw)
        slot0_ok    = abs(decoded[0] - 0.30) < _FLOAT16_TOL
        manifest_ok = verify_capsule(bundle)
        return slot0_ok and manifest_ok


# ── Test 8.10 ────────────────────────────────────────────────────────────────

def test_capsule_verify_fails_on_tamper() -> bool:
    """
    verify_capsule returns False after state.bin is modified without updating manifest.

    This confirms the SHA-256 integrity chain is enforced.
    """
    with tempfile.TemporaryDirectory() as tmp:
        bundle      = _generate_test_capsule(Path(tmp))
        state_file  = bundle / "capsule" / "state.bin"

        # Tamper: flip all bytes
        original = state_file.read_bytes()
        tampered = bytes(b ^ 0xFF for b in original)
        state_file.write_bytes(tampered)

        return verify_capsule(bundle) is False


# ── Test 8.11 ────────────────────────────────────────────────────────────────

def test_capsule_summary_keys() -> bool:
    """
    capsule_summary returns a dict with all expected diagnostic keys and
    state_slots == STATE_VEC_LEN (21).
    """
    expected_keys = {"capsule_id", "layer", "bias", "faction_id",
                     "state_slots", "state_vec", "valid"}
    with tempfile.TemporaryDirectory() as tmp:
        bundle  = _generate_test_capsule(Path(tmp))
        summary = capsule_summary(bundle)
        keys_ok  = expected_keys.issubset(summary.keys())
        slots_ok = summary.get("state_slots") == STATE_VEC_LEN
        valid_ok = summary.get("valid") is True
        return keys_ok and slots_ok and valid_ok


# ── Test 8.12 ────────────────────────────────────────────────────────────────

def test_capsule_cns_style_ctl_high_resistance() -> bool:
    """
    cns.yaml self_checks.style_ctl is True when leader.oversight_resistance > 0.4
    and False when oversight_resistance <= 0.4.

    Rationale: high-resistance characters need tighter style enforcement to
    prevent authoritarian tone-bleed across simulation narrative layers.
    """
    with tempfile.TemporaryDirectory() as tmp_high:
        leader_high  = _make_test_leader(oversight_resistance=0.85)
        faction      = _make_test_faction()
        bundle_high  = generate_capsule(leader_high, faction, Path(tmp_high), overwrite=True)
        cns_high     = json.loads(
            (bundle_high / "capsule" / "cns.yaml").read_text(encoding="utf-8")
        )
        style_high   = cns_high["self_checks"]["style_ctl"]

    with tempfile.TemporaryDirectory() as tmp_low:
        leader_low   = _make_test_leader(oversight_resistance=0.20)
        bundle_low   = generate_capsule(leader_low, faction, Path(tmp_low), overwrite=True)
        cns_low      = json.loads(
            (bundle_low / "capsule" / "cns.yaml").read_text(encoding="utf-8")
        )
        style_low    = cns_low["self_checks"]["style_ctl"]

    return style_high is True and style_low is False


def main():
    parser = argparse.ArgumentParser(description="GUMAS v3.0 Validation Suite")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    suite = TestSuite(verbose=args.verbose)

    print("=" * 60)
    print("GUMAS v3.0 Validation Suite")
    print("Anchor: GUMAS-ENGINE-VALIDATE-V3 | Seed: EOS_SEED_ORION")
    print("Ethics: Picard_Delta_3")
    print("=" * 60)

    print("\n── Section 1: Population ──────────────────────────────────")
    suite.run("growth_at_capacity",             test_pop_growth_at_capacity)
    suite.run("growth_overpopulation_negative", test_pop_growth_overpopulation_negative)
    suite.run("migration_pressure_range",       test_migration_pressure_range)
    suite.run("migration_pressure_direction",   test_migration_pressure_direction)
    suite.run("demographic_stress_clamped",     test_demographic_stress_clamped)
    suite.run("refugee_no_conflict",            test_refugee_no_conflict)

    print("\n── Section 2: Technology ──────────────────────────────────")
    suite.run("tech_advance_diminishing_returns", test_tech_advance_diminishing_returns)
    suite.run("tech_diffusion_zero_gap",          test_tech_diffusion_zero_gap)
    suite.run("military_tech_advantage_cap",      test_military_tech_advantage_cap)
    suite.run("civilian_tech_multiplier_minimum", test_civilian_tech_multiplier_minimum)
    suite.run("tech_espionage_yield_range",        test_tech_espionage_yield_range)

    print("\n── Section 3: Negotiation ─────────────────────────────────")
    suite.run("negotiation_success_range",      test_negotiation_success_range)
    suite.run("negotiation_back_channel_bonus", test_negotiation_back_channel_bonus)
    suite.run("concession_threshold_weak_batna",test_concession_threshold_weak_batna)
    suite.run("batna_range",                    test_batna_range)
    suite.run("diplomatic_crisis_high_trust",   test_diplomatic_crisis_high_trust)
    suite.run("ultimatum_compliance_high_resolve", test_ultimatum_compliance_high_resolve)

    print("\n── Section 4: Intelligence ────────────────────────────────")
    suite.run("sigint_yield_range",             test_sigint_yield_range)
    suite.run("sigint_penalised_by_ci",         test_sigint_penalised_by_ci)
    suite.run("humint_totalitarian_harder",     test_humint_totalitarian_harder)
    suite.run("intel_fusion_synergy",           test_intel_fusion_synergy)
    suite.run("surveillance_legitimacy_penalty",test_surveillance_penalty)

    print("\n── Section 5: Rebellion ───────────────────────────────────")
    suite.run("rebellion_onset_high_stress",    test_rebellion_onset_high_stress)
    suite.run("rebellion_onset_stable_state",   test_rebellion_onset_stable_state)
    suite.run("insurgency_strength_repressed",  test_insurgency_strength_repressed)
    suite.run("fragmentation_risk_range",       test_state_fragmentation_risk_range)
    suite.run("civil_war_escalation_quadratic", test_civil_war_escalation_quadratic)

    print("\n── Section 6: Engine Integration ──────────────────────────")
    suite.run("engine_initializes",             test_engine_initializes)
    suite.run("engine_single_step",             test_engine_single_step)
    suite.run("engine_10_turns",                test_engine_10_turns)
    suite.run("engine_export",                  test_engine_export)
    suite.run("engine_state_mutation",          test_engine_state_mutation)

    print("\n── Section 7: Reproducibility ─────────────────────────────")
    suite.run("reproducibility_seed_99",        test_reproducibility)

    print("\n── Section 8: CharForge — ORION Capsule Bundle v0.2.0 ─────")
    suite.run("capsule_all_seven_files",         test_capsule_all_seven_files)
    suite.run("capsule_verify_after_generate",   test_capsule_verify_after_generate)
    suite.run("capsule_state_bin_roundtrip",     test_capsule_state_bin_roundtrip)
    suite.run("capsule_identity_fields",         test_capsule_identity_fields)
    suite.run("capsule_traits_bias_voice",       test_capsule_traits_bias_voice)
    suite.run("capsule_traits_faction_values",   test_capsule_traits_faction_values)
    suite.run("capsule_knowledge_stressor_rec",  test_capsule_knowledge_stressor_rec)
    suite.run("capsule_knowledge_trust_records", test_capsule_knowledge_trust_records)
    suite.run("capsule_tick_update_state_bin",   test_capsule_tick_update_state_bin)
    suite.run("capsule_verify_fails_on_tamper",  test_capsule_verify_fails_on_tamper)
    suite.run("capsule_summary_keys",            test_capsule_summary_keys)
    suite.run("capsule_cns_style_ctl_high_res",  test_capsule_cns_style_ctl_high_resistance)

    passed = suite.summary()
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()

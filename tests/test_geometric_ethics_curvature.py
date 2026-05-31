"""Tests for the geometric-algebra ethics curvature reference engine.

Pins the gate contract (matches the hub's scalar field at the corners) AND proves
the geometric-algebra structure captures dimensional interaction that a weighted
mean structurally cannot.
"""

import importlib.util
import math

import pytest

from tools.geometric_ethics_curvature import (
    DIMENSION_WEIGHTS,
    calculate_curvature,
    _interaction_closed_form,
    _interaction_via_clifford,
    _legs,
)

_HAS_CLIFFORD = importlib.util.find_spec("clifford") is not None


def _all(score: float) -> dict:
    return {d: score for d in DIMENSION_WEIGHTS}


# ── Hard floor: canon mandates any dimension at 0.0 → INFINITE regardless ──────

def test_single_zero_dimension_is_geometric_impossibility():
    scores = _all(0.99)
    scores["layer_integrity"] = 0.0
    result = calculate_curvature(scores)
    assert result.resistance_level == "INFINITE"
    assert result.formation_allowed is False
    assert "layer_integrity" in result.critical_violations


def test_perfect_alignment_is_low_resistance():
    result = calculate_curvature(_all(1.0))
    assert result.resistance_level == "LOW"
    assert result.formation_allowed is True
    assert result.interaction_penalty == pytest.approx(0.0)
    assert result.alignment == pytest.approx(1.0)


def test_high_scores_match_scalar_band():
    # No co-deficits → GA alignment tracks the legacy weighted mean.
    result = calculate_curvature(_all(0.96))
    assert result.composite_scalar == pytest.approx(0.96)
    assert result.resistance_level == "LOW"


# ── Backward compatibility: a lone deficit ≈ scalar (interaction ~ negligible) ─

def test_single_dimension_deficit_tracks_scalar():
    scores = _all(1.0)
    scores["collective_welfare"] = 0.40  # one light dim deficient, no partner
    result = calculate_curvature(scores)
    # Only one deficient dimension → no pair → zero interaction penalty.
    assert result.interaction_penalty == pytest.approx(0.0)
    assert result.alignment == pytest.approx(result.composite_scalar)


# ── The material proof: GA distinguishes synapses the scalar mean cannot ───────

def test_interaction_is_detected_where_scalar_is_blind():
    """Two synapses with IDENTICAL scalar composite, different interaction structure.

    Both carry the same total weighted deficit (Σ wᵢ·dᵢ = 0.22 → composite = 0.78),
    so the legacy scalar gate scores them identically. But one concentrates the
    deficit on the two heaviest dimensions (layer 0.30 + picard 0.25) and the other
    spreads it evenly. Concentrated co-deficit on heavy dimensions must register MORE
    curvature — something Σ wᵢ·scoreᵢ cannot express, because a mean is permutation-
    and concentration-blind.
    """
    # Concentrated: deficit 0.4 on layer + picard only.  Σwd = .30·.4 + .25·.4 = .22
    concentrated = {
        "picard_delta_3": 0.60, "thermax_continuity": 1.0,
        "layer_integrity": 0.60, "collective_welfare": 1.0, "transparency": 1.0,
    }
    # Spread: deficit 0.22 on every dimension.            Σwd = .22·Σw = .22·1 = .22
    spread = {d: 0.78 for d in DIMENSION_WEIGHTS}

    c = calculate_curvature(concentrated)
    s = calculate_curvature(spread)

    # The scalar gate is blind: identical composites.
    assert c.composite_scalar == pytest.approx(0.78)
    assert s.composite_scalar == pytest.approx(0.78)
    assert c.composite_scalar == pytest.approx(s.composite_scalar)

    # The geometric gate is not: concentrated heavy co-deficit → larger interaction,
    # lower alignment. This is the structural information the scalar mean discards.
    assert c.interaction_penalty > s.interaction_penalty
    assert c.alignment < s.alignment


# ── The geometry is genuine: clifford multivector == closed form ──────────────

@pytest.mark.skipif(not _HAS_CLIFFORD, reason="clifford not installed in this env")
def test_clifford_bivector_magnitude_equals_closed_form():
    scores = {
        "picard_delta_3": 0.6, "thermax_continuity": 0.7,
        "layer_integrity": 0.5, "collective_welfare": 0.8, "transparency": 0.9,
    }
    legs = _legs(scores)
    lam = 0.5
    ga = _interaction_via_clifford(legs, lam)
    closed = _interaction_closed_form(legs, lam)
    # The grade-2 magnitude of the real multivector equals the interpretable
    # interaction term — proof the geometry is real, tractable, and not decorative.
    assert ga == pytest.approx(closed, rel=1e-9, abs=1e-12)


@pytest.mark.skipif(not _HAS_CLIFFORD, reason="clifford not installed in this env")
def test_clifford_backend_reported_when_available():
    result = calculate_curvature(_all(0.8), prefer_clifford=True)
    assert result.backend == "clifford"


def test_closed_form_backend_is_deterministic_fallback():
    result = calculate_curvature(_all(0.8), prefer_clifford=False)
    assert result.backend == "closed_form"
    # Closed form must agree with the documented quadrature identity.
    legs = _legs(_all(0.8))
    expected = _interaction_closed_form(legs, 0.5)
    assert result.interaction_penalty == pytest.approx(expected)

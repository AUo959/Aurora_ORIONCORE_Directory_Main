"""Consequence layer — downstream effects for the inert instability signals
the seed-42 lessons flagged (§2.1 intel, §2.2 onset, §2.3 fragmentation,
§2.4 conscription). Pure/tunable; these lock in the shapes."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from gumas_consequence_layer import ConsequenceLayer  # noqa: E402


@pytest.mark.simulation
def test_conscription_mobilizes_only_under_war():
    c = ConsequenceLayer()
    assert c.conscription_target(0.5, active_wars=0) == 0.5          # no war, no change
    assert c.conscription_target(0.5, active_wars=2) > 0.5            # at war, mobilizes
    assert c.conscription_target(0.9, active_wars=2) == 0.9          # already above ceiling


@pytest.mark.simulation
def test_counter_intel_is_self_limiting_and_gentle():
    """CI rises toward a modest ceiling under pressure — gently, because the
    field also gates rebellion onset; aggressive build-up would erase conflict."""
    c = ConsequenceLayer()
    low = c.ci_investment(0.30, intel_pressure=0.8)
    assert 0.30 < low < c.CI_CEILING
    # Quiet intel environment -> slower investment than a noisy one.
    assert c.ci_investment(0.30, 0.0) < c.ci_investment(0.30, 1.0)
    # At the ceiling it stops climbing.
    assert c.ci_investment(c.CI_CEILING, 1.0) == c.CI_CEILING


@pytest.mark.simulation
def test_intel_cost_is_episodic_and_decays_with_ci():
    c = ConsequenceLayer()
    assert c.intel_econ_cost(0.3, intel_pressure=0.0) == 0.0          # quiet -> no cost
    hi = c.intel_econ_cost(0.3, intel_pressure=1.0)
    lo = c.intel_econ_cost(0.7, intel_pressure=1.0)
    assert hi > lo > 0.0                                             # CI investment shrinks it


@pytest.mark.simulation
def test_fragmentation_drag_thresholded():
    c = ConsequenceLayer()
    assert c.fragmentation_drag(0.3) == 0.0                          # small revolt, no split
    assert c.fragmentation_drag(0.7) > 0.0                          # large territory -> capacity loss

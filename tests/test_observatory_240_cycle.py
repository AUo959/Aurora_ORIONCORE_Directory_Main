"""Observatory 240-turn cycle — the official living-galaxy test case.

Runs the full GUMAS L2 galaxy for 240 turns (twice the canonical sim window)
across the canonical seeds through the *committed* mechanic pipeline and locks
the living-galaxy invariants the complacency cycle (MECH-SOC-006) was built to
guarantee:

    1. conflict RECURS (>= 2 waves) — not a one-time swell, not permanent peace
    2. the galaxy never COLLAPSES (stability floor stays above the pinned floor)
    3. complacency is the cycle driver (builds in calm, purged at conflict peaks)
    4. determinism (same seed -> identical trajectory)

These guard against silent regression to either degenerate fixed point
(permanent civil war / permanent peace).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import observatory_240_cycle as O  # noqa: E402

SEEDS = (42, 7, 99)
TURNS = 240


@pytest.fixture(scope="module")
def analyses():
    return [O.analyse_seed(O.run_seed(s, TURNS)) for s in SEEDS]


@pytest.mark.simulation
@pytest.mark.parametrize("seed_idx", range(len(SEEDS)))
def test_living_galaxy_certified_each_seed(analyses, seed_idx):
    a = analyses[seed_idx]
    v = a["verdict"]
    assert v["living_galaxy"], (a["seed"], v)
    assert v["conflict_recurs"]
    assert v["not_permanent_peace"]
    assert v["not_collapsed"]


@pytest.mark.simulation
def test_conflict_recurs_in_at_least_two_waves(analyses):
    """The whole point of MECH-SOC-006: conflict comes back, it doesn't fire
    once and flatline (the permanent-peace degeneracy)."""
    for a in analyses:
        assert a["n_conflict_waves"] >= 2, (a["seed"], a["civil_wars_per_era"])
        assert a["total_new_insurgencies"] > 0


@pytest.mark.simulation
def test_conflict_has_an_off_ramp_besides_war(analyses):
    """MECH-REB-004: civil wars must be able to END by negotiated settlement,
    not only by military suppression. War is no longer the only off-ramp."""
    for a in analyses:
        assert a["verdict"]["has_off_ramp"], (a["seed"], a["total_settlements"])
        assert a["total_settlements"] > 0
        assert a["off_ramp_settlement_share"] > 0.0


@pytest.mark.simulation
def test_conflict_cast_rotates(analyses):
    """Settlement retires a movement and spends its grievance, so the host can
    later host a *different* insurgency — the cast rotates instead of the same
    ~13 wounds reopening (pre-graft). Many distinct insurgencies should form."""
    for a in analyses:
        assert a["verdict"]["cast_rotates"], (a["seed"], a["total_new_insurgencies"])
        assert a["total_new_insurgencies"] > 25


@pytest.mark.simulation
def test_never_collapses_to_pinned_floor(analyses):
    """The original seed-42 attractor crashed and stayed crashed. The living
    galaxy must hold above the collapse floor for the whole horizon."""
    for a in analyses:
        assert a["stability_floor"] > O.COLLAPSE_FLOOR, (a["seed"], a["stability_floor"])


@pytest.mark.simulation
def test_complacency_is_the_cycle_driver(analyses):
    """Complacency must build during calm and be purged at conflict peaks —
    the mechanism, not just the outcome. Peak-era complacency should fall well
    below the calm build-up."""
    for a in analyses:
        compl = a["complacency_per_era"]
        cw = a["civil_wars_per_era"]
        assert max(compl) > 0.2, (a["seed"], compl)        # it builds in calm
        peak_era = max(range(len(cw)), key=lambda i: cw[i])
        # at the heaviest-conflict era complacency is purged below its own peak
        assert compl[peak_era] < max(compl), (a["seed"], peak_era, compl)


@pytest.mark.simulation
def test_determinism(analyses):
    assert O.determinism_ok(42, 60)


@pytest.mark.simulation
def test_metrics_surface_is_complete():
    """The downlink must carry the full instrument set the Observatory reads."""
    rows = O.run_seed(42, 5)["rows"]
    r = rows[0]
    required = {
        "turn", "stability", "risk", "active_civil_wars",
        "complacency_mean", "grievance_mean",
        "comp_avg_population_stability", "comp_avg_leader_legitimacy",
        "comp_avg_trust", "comp_conflict_pressure",
        "v3_new_insurgencies", "v3_civil_wars_started", "v3_migrations",
        "ins_civil_war", "ins_suppressed",
        "pop_demographic_stress", "leader_legitimacy", "leader_war_pressure",
    }
    missing = required - set(r.keys())
    assert not missing, missing

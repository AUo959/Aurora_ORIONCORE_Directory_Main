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
def test_cultural_cost_of_conquest_splits_by_culture(analyses):
    """MECH-CUL-002 (Pillar A): holding reconquered ground costs differently by
    culture — both policies are exercised across the galaxy (assimilationists
    impose identity and breed grievance; tolerant regimes accommodate)."""
    for a in analyses:
        assert a["verdict"]["cultural_cost_active"], (
            a["seed"], a["assimilations"], a["tolerations"])
        assert a["assimilations"] > 0 and a["tolerations"] > 0


@pytest.mark.simulation
def test_war_economy_busts_and_booms(analyses):
    """MECH-ECO-001 (Pillar A): the economy must track the war/peace cycle —
    at-war factions run a depressed economy while at-peace factions enjoy a
    reconstruction boom, a substantial and consistent gap."""
    for a in analyses:
        assert a["verdict"]["war_economy_active"], (
            a["seed"], a["war_economic_health"], a["peace_economic_health"])
        assert a["war_economy_gap"] >= 0.15
        assert a["peace_economic_health"] > a["war_economic_health"]


@pytest.mark.simulation
def test_war_outcomes_reshape_the_world(analyses):
    """MECH-TER-001 (Pillar A): a war's outcome must propagate — factions lose
    territory permanently, that loss diverges their economies (was uniform), and
    the chain reaches power (war-torn factions end weaker than the spared).
    Causal depth > 1, not a self-contained stability scalar."""
    for a in analyses:
        assert a["verdict"]["consequences_propagate"], (
            a["seed"], a["factions_lost_territory"], a["econ_potential_spread"], a["war_power_penalty"])
        assert a["factions_lost_territory"] >= 1
        assert a["econ_potential_spread"] >= 0.05
        assert a["war_power_penalty"] is None or a["war_power_penalty"] > 0


@pytest.mark.simulation
def test_power_politics_splits_by_culture(analyses):
    """MECH-POW-001: factions take a stance toward the galactic hegemon by
    culture — bandwagoners end up measurably more trusting of the strongest
    power than balancers do (a gap that is ~0 without the mechanic)."""
    for a in analyses:
        assert a["verdict"]["power_politics_active"], (a["seed"], a["power_realignment_gap"])
        assert a["power_realignment_gap"] >= 0.05


@pytest.mark.simulation
def test_leadership_turns_over(analyses):
    """MECH-GOV-003: internal politics must not stagnate — regimes fall and
    successors take power (by coup or election), and the turnover changes
    factions' cultures (their dominant_bias), shifting trajectories."""
    for a in analyses:
        assert a["verdict"]["leadership_turns_over"], (a["seed"], a["succession_counts"])
        assert a["total_successions"] > 0
        assert a["factions_with_turnover"] >= 1


@pytest.mark.simulation
def test_cultures_decide_differently(analyses):
    """MECH-GOV-002: under identical mechanics, different cultures must resolve
    conflict at measurably different rates — authentic decisions, not uniform
    behaviour. The settlement-rate spread across well-sampled dominant_bias
    groups must be non-trivial."""
    for a in analyses:
        assert a["verdict"]["cultures_diverge"], (a["seed"], a["settlement_rate_by_culture"])
        assert a["culture_settlement_spread"] >= 0.05
        # and the spread is grounded in >= 2 well-sampled cultures
        assert len(a["settlement_rate_by_culture"]) >= 2


@pytest.mark.simulation
def test_never_collapses_to_pinned_civil_war(analyses):
    """The original seed-42 attractor pinned ~4 active civil wars and stayed
    there. Collapse is gated on conflict *load*, not a stability scalar (D9: the
    honest scalar can't tell health from collapse). The mature civil-war load
    must stay below the permanent-war reference."""
    for a in analyses:
        assert a["verdict"]["not_collapsed"], (a["seed"], a["sustained_civil_war_load"])
        assert a["sustained_civil_war_load"] < O.COLLAPSE_CW_REF


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

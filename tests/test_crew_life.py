"""Crew-life fidelity: shifts, sleep, meals, hygiene, fatigue.

High fidelity means the crew are people. These tests assert the human layer
is actually simulated: the station is never fully asleep, every soul both
sleeps and eats across a day, life-support load is tracked, and the
shift-gating bridge resolves names between the canon roster and the sim
loader.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import crew_life  # noqa: E402


@pytest.mark.simulation
def test_station_is_always_crewed_and_everyone_rests_and_eats():
    model = crew_life.load_model()
    crew = crew_life.load_crew()
    assert len(crew) >= 40, "expected the full L1 roster"
    shifts = crew_life.assign_shifts(crew, model)
    assert set(shifts.values()) == set(model["shifts"]), "every shift must be staffed"

    sim = crew_life.simulate(shifts, crew, model, start_hour=6, hours=24)

    # The habitat is never fully asleep — someone is always on watch.
    for step in range(24):
        on = sim["occupancy"][step].get("on_shift", 0)
        assert on >= 1, f"no crew on shift at step {step}"
        assert sim["occupancy"][step].get("asleep", 0) < len(crew), "everyone asleep at once"

    # Every soul both sleeps and eats over the day.
    for name, st in sim["state"].items():
        activities = {h["activity"] for h in st["hours"]}
        assert "asleep" in activities, f"{name} never slept"
        assert st["meals_eaten"] >= 1, f"{name} never ate"

    # Life-support load is real and the water loop closes near 98%.
    c = sim["consumables"]
    assert c["galley_portions"] > 0 and c["water_drawn_l"] > 0 and c["co2_kg"] > 0
    assert c["water_recycled_l"] / c["water_drawn_l"] > 0.95


@pytest.mark.simulation
def test_shift_gating_bridge_resolves_names():
    """The normalized bridge must match canon names to sim-loader names
    (titles differ), or the watch would gate out the entire crew."""
    assert crew_life.norm_name("Commander Alex Thorne") == crew_life.norm_name("Alex Thorne")
    assert crew_life.norm_name("Dr. Elira Noor") == crew_life.norm_name("Elira Noor")

    model = crew_life.load_model()
    crew = crew_life.load_crew()
    shifts = crew_life.assign_shifts(crew, model)
    sim = crew_life.simulate(shifts, crew, model, start_hour=6, hours=4)
    # Morning watch (06:00) should put the Alpha shift on duty.
    on0 = crew_life.on_shift_awake_norm(sim, 0)
    assert len(on0) >= 5, "morning watch should have a full primary shift on duty"
    fmap = crew_life.fatigue_norm_map(sim, 0)
    assert all(0.0 <= v <= 100.0 for v in fmap.values())

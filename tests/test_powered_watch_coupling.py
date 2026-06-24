"""Regression guard for the L1<->L2 powered-watch coupling, on the living clock.

The first powered watch shipped with a silent defect: the chassis->engine
throughput link keyed task tags by id while the harness records task names, so
engine throughput was pinned flat at 1 turn/hour and the bidirectional coupling
was inert while still printing plausible output.

Orion Station now keeps a continuous history: each check-in is a NEW hour on the
timeline, never a replay of one fixed seed. So this walks two consecutive watch
blocks (distinct hours) and asserts the invariants that must hold for ANY hour —
the coupling is live (throughput exceeds one turn/hour and varies with crew
servicing) — plus that the station clock actually advanced between blocks.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.simulation
@pytest.mark.slow
def test_powered_watch_coupling_is_live_across_advancing_hours(tmp_path):
    """Each watch block, on whatever hour the clock is at, must show live,
    variable, >1 engine throughput — and consecutive blocks must be distinct
    hours, not a replay of the same seed."""
    # Isolated station clock: walk a deterministic sequence of distinct hours
    # without touching the repo's committed chronicle.
    state = tmp_path / "station_state.json"
    state.write_text(json.dumps({"hours_elapsed": 0, "pair_familiarity": {}}) + "\n")
    env = {**os.environ, "AURORA_STATION_STATE": str(state)}

    seeds: list[int] = []
    for _ in range(2):
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools" / "powered_watch.py"), "--no-mesh"],
            capture_output=True, text=True, cwd=REPO_ROOT, env=env, timeout=600,
        )
        assert result.returncode == 0, result.stderr[-800:]

        run = sorted((REPO_ROOT / "reports" / "simulation").glob("powered_watch_v1__*"))[-1]
        telemetry = json.loads((run / "engine_telemetry.json").read_text())

        log = telemetry["log"]
        assert log, "engine produced no turns"
        hours = max(e["hour"] for e in log)
        turns_per_hour = Counter(e["hour"] for e in log)

        # Coupling alive: more turns than hours, and throughput is not flat.
        assert telemetry["turns_total"] > hours, (
            f"engine ran <=1 turn/hour ({dict(turns_per_hour)}) — coupling inert"
        )
        assert len(set(turns_per_hour.values())) > 1, (
            f"engine throughput is flat ({dict(turns_per_hour)}) — "
            "servicing is not powering the engine"
        )
        # Engine class is the advanced engine, not a degenerate fallback.
        assert telemetry["engine_class"] == "GUMASAdvancedEngine"
        seeds.append(int(telemetry["seed"]))

    # The station clock advanced: the second block is a different hour, never a
    # replay of the first.
    assert seeds[0] != seeds[1], f"station clock did not advance between check-ins: {seeds}"
    assert seeds[1] > seeds[0], f"clock ran backwards: {seeds}"

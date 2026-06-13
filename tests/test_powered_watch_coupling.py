"""Regression guard for the L1<->L2 powered-watch coupling.

The first powered watch shipped with a silent defect: the chassis->engine
throughput link keyed task tags by id while the harness records task names,
so engine throughput was pinned flat at 1 turn/hour and the bidirectional
coupling was inert while still printing plausible output. These tests assert
the coupling is live: throughput varies with crew servicing, and the engine
runs more than one turn per hour when servicing is done.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.simulation
@pytest.mark.slow
def test_powered_watch_throughput_scales_with_servicing(tmp_path):
    """A headless powered watch must produce variable, >1 engine throughput.

    This is the test that would have caught the name/id key bug: with the
    bug, every hour ran exactly one turn (flat), so distinct throughput
    values == 1 and turns_total == hours.
    """
    out_dir = tmp_path / "powered_watch_test"
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "powered_watch.py"),
         "--no-mesh"],
        capture_output=True, text=True, cwd=REPO_ROOT, timeout=600,
    )
    assert result.returncode == 0, result.stderr[-800:]

    # Locate the freshest powered-watch telemetry artifact.
    runs = sorted((REPO_ROOT / "reports" / "simulation").glob("powered_watch_v1__*"))
    assert runs, "no powered-watch artifacts produced"
    telemetry = json.loads((runs[-1] / "engine_telemetry.json").read_text())

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

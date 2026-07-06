"""Regression guard for the live station link, on the living station clock.

The first live watch shipped with a silent defect: downlink() returned the most
recent reply already in the channel, so each hour's companion replies echoed the
PRIOR hour's telemetry — the feed looked live (timestamps and engine risk
advanced) while the uplink was lagging a full hour.

Orion Station now keeps a continuous history: each check-in is a NEW hour on the
timeline, never a replay of one fixed seed. So this walks two consecutive watch
blocks (distinct hours) and asserts the invariants that must hold for ANY hour:
  - the link is real-time: each hour's reply references that hour's downlink;
  - the control loop is coherent: when engine risk crosses the advisory
    threshold, Aurora injects a risk-response cell in the same hour;
  - the clock advances: the second block is a different hour, not a replay.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_live_watch(env: dict, report_root: Path) -> tuple[list[dict], dict]:
    result = subprocess.run(  # noqa: S603 - intentional CLI regression test with fixed argv.
        [sys.executable, str(REPO_ROOT / "tools" / "live_watch.py")],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=env,
        timeout=600,
    )
    assert result.returncode == 0, result.stderr[-800:]
    run = sorted(report_root.glob("live_watch_v1__*"))[-1]
    feed = [
        json.loads(line)
        for line in (run / "live_downlink.jsonl").read_text().splitlines()
        if line
    ]
    telemetry = json.loads((run / "engine_telemetry.json").read_text())
    return feed, telemetry


@pytest.mark.simulation
@pytest.mark.slow
def test_live_link_is_fresh_and_clock_advances(tmp_path):
    """Walk two consecutive watch blocks: each must be a real-time link with a
    coherent control loop, and the station clock must advance between them."""
    state = tmp_path / "station_state.json"
    state.write_text(json.dumps({"hours_elapsed": 0, "pair_familiarity": {}}) + "\n")
    report_root = tmp_path / "reports" / "simulation"
    env = {
        **os.environ,
        "AURORA_STATION_STATE": str(state),
        "AURORA_SIM_REPORT_ROOT": str(report_root),
    }

    seeds: list[int] = []
    advisory_seen = False
    for _ in range(2):
        feed, telemetry = _run_live_watch(env, report_root)

        # Pair each hour's downlink with the following uplink reply and assert
        # the reply echoes the SAME hour's content (the stale-reply bug made
        # hour 2's reply quote "hour 1/4").
        checked, pending_to = 0, None
        for ev in feed:
            if ev["kind"] == "downlink":
                pending_to = (ev["hour"], ev["content"])
            elif ev["kind"] == "uplink_reply" and pending_to is not None:
                hour, _ = pending_to
                if ev["ok"]:
                    assert f"hour {hour}/" in ev["content"], (
                        f"hour {hour} reply did not echo this hour's downlink "
                        f"(stale reply): got {ev['content'][:80]!r}"
                    )
                    checked += 1
                pending_to = None
        assert checked >= 4, (
            f"too few fresh-reply checks ({checked}) — link may not be exercising"
        )

        # Control loop coherence: an advisory implies a risk-response cell was
        # injected the same watch (deterministic mechanism, any hour).
        if telemetry["advisory_raised"]:
            advisory_seen = True
            assert telemetry["injected_tasks"], (
                "advisory raised but no risk-response cell injected"
            )

        seeds.append(int(telemetry["seed"]))

    # The station clock advanced — the second block is a new hour, not a replay.
    assert seeds[0] != seeds[1], (
        f"station clock did not advance between check-ins: {seeds}"
    )
    assert seeds[1] > seeds[0], f"clock ran backwards: {seeds}"
    # Across the sequence the control loop must actually fire at least once.
    assert advisory_seen, (
        "no advisory fired across the watch sequence — control loop never exercised"
    )

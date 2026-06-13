"""Regression guard for the live station link.

The first live watch shipped with a silent defect: downlink() returned the
most recent reply already in the channel, so each hour's companion replies
echoed the PRIOR hour's telemetry — the feed looked live (timestamps and
engine risk advanced) while the uplink was lagging a full hour. These tests
assert the link is genuinely real-time: each hour's reply references that
hour's downlink, and the engine->Aurora->chassis control loop fires.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.simulation
@pytest.mark.slow
def test_live_link_replies_are_fresh_and_control_loop_fires():
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "live_watch.py")],
        capture_output=True, text=True, cwd=REPO_ROOT, timeout=600,
    )
    assert result.returncode == 0, result.stderr[-800:]

    runs = sorted((REPO_ROOT / "reports" / "simulation").glob("live_watch_v1__*"))
    assert runs, "no live-watch artifacts produced"
    run = runs[-1]
    feed = [json.loads(line) for line in (run / "live_downlink.jsonl").read_text().splitlines() if line]

    # Pair each hour's downlink with the immediately following uplink reply and
    # assert the reply echoes the SAME hour's content (the stale-reply bug made
    # hour 2's reply quote "hour 1/4").
    checked = 0
    pending_to = None
    for ev in feed:
        if ev["kind"] == "downlink":
            pending_to = (ev["hour"], ev["content"])
        elif ev["kind"] == "uplink_reply" and pending_to is not None:
            hour, sent = pending_to
            token = f"hour {hour}/"
            if ev["ok"]:
                assert token in ev["content"], (
                    f"hour {hour} reply did not echo this hour's downlink "
                    f"(stale reply): got {ev['content'][:80]!r}"
                )
                checked += 1
            pending_to = None
    assert checked >= 4, f"too few fresh-reply checks ({checked}) — link may not be exercising"

    # Control loop: engine risk crossed the advisory threshold and Aurora's
    # advisory injected a risk-response cell (deterministic at seed 808).
    telemetry = json.loads((run / "engine_telemetry.json").read_text())
    assert telemetry["advisory_raised"] is True, "risk advisory did not fire"
    assert telemetry["injected_tasks"], "advisory raised but no risk-response cell injected"

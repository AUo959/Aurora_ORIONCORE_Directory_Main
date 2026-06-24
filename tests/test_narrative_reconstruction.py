"""The hour_aboard harness emits a full L3 narrative reconstruction artifact.

A reconstruction is only trustworthy if it carries the complete L3 engine
output — request/state/evaluation/response — alongside the reconstructed event
chain and a verdict, not just a bare "supported" string. These tests run the
harness on an isolated station clock and assert the artifact is whole.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

VERDICTS = {"supported", "unsupported", "needs_detail", "uncertain", "blocked"}


def _run_hour_aboard(env: dict, scenario: str = "hour_aboard_scenario") -> Path:
    result = subprocess.run(  # noqa: S603 - intentional CLI test with fixed argv.
        [sys.executable, str(REPO_ROOT / "tools" / "hour_aboard.py"),
         "--scenario", scenario, "--no-mesh"],
        capture_output=True, text=True, cwd=REPO_ROOT, env=env, timeout=600,
    )
    assert result.returncode == 0, result.stderr[-800:]
    runs = sorted((REPO_ROOT / "reports" / "simulation").glob(f"{scenario.removesuffix('_scenario')}_v1__*"))
    assert runs, f"no artifact directory produced for {scenario}"
    return runs[-1]


@pytest.mark.simulation
@pytest.mark.slow
def test_reconstruction_carries_full_l3_run_and_event_chain(tmp_path):
    """The emitted narrative_reconstruction.{json,md} must carry the full L3
    run (request/state/evaluation/response) and a coherent event chain."""
    state = tmp_path / "station_state.json"
    state.write_text(json.dumps({"hours_elapsed": 0, "pair_familiarity": {}, "atoms_total": 0}) + "\n")
    env = {**os.environ, "AURORA_STATION_STATE": str(state), "PYTHONPATH": str(REPO_ROOT)}

    run_dir = _run_hour_aboard(env)
    recon = json.loads((run_dir / "narrative_reconstruction.json").read_text())

    # Full L3 engine output, not just a verdict string.
    l3 = recon["l3"]
    assert set(l3) >= {"request", "state", "evaluation", "response"}, "L3 reconstruction is not the full run"
    assert l3["response"]["verdict"] in VERDICTS
    assert l3["state"]["layers"], "canonical state has no resolved layers"

    # The event chain opens the watch, closes it, and ends on the audited proposal.
    phases = [c["phase"] for c in recon["event_chain"]]
    assert phases[0] == "watch open"
    assert "watch close" in phases
    assert phases[-1] == "proposal"
    assert any(c["phase"] == "this watch" for c in recon["event_chain"]), "no closed tasks reconstructed"

    # Souls accounting and the human-readable render are both present.
    assert "/" in recon["watch"]["souls_accounted"]
    md = (run_dir / "narrative_reconstruction.md").read_text()
    assert "# Narrative Reconstruction" in md
    assert "## Validation verdict" in md
    assert l3["response"]["verdict"].upper() in md


@pytest.mark.simulation
@pytest.mark.slow
def test_reconstruction_event_chain_matches_closed_tasks(tmp_path):
    """Every task the sim closed appears once in the reconstructed event chain,
    attributed to the crew member who signed it off."""
    state = tmp_path / "station_state.json"
    state.write_text(json.dumps({"hours_elapsed": 0, "pair_familiarity": {}, "atoms_total": 0}) + "\n")
    env = {**os.environ, "AURORA_STATION_STATE": str(state), "PYTHONPATH": str(REPO_ROOT)}

    run_dir = _run_hour_aboard(env)
    recon = json.loads((run_dir / "narrative_reconstruction.json").read_text())
    sim = json.loads((run_dir / "sim_raw.json").read_text())

    closed_count = len(sim["summary"]["completed_ids"])
    chain_closed = [c for c in recon["event_chain"] if c["phase"] == "this watch"]
    assert len(chain_closed) == closed_count, "closed-task count drifted between sim and reconstruction"
    for c in chain_closed:
        assert c["participants"], f"closed task '{c['label']}' has no owner attributed"

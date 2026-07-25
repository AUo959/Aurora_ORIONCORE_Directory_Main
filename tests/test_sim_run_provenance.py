"""Simulation output must record where it came from.

Field finding 2026-07-25: a run directory appeared that nobody could attribute.
Proving what it was took re-running the harness and diffing, because the output
recorded nothing about its own origin — no process, no invoking command, not
even the path it was written to.

These tests pin the provenance block, including the property that makes a
*copied* directory self-revealing: run_meta records its own output path, so a
directory whose name disagrees with it was copied rather than generated.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import hour_aboard  # noqa: E402


def test_run_meta_records_process_and_output_dir(tmp_path):
    """The block must carry enough to answer 'who made this' without a rerun."""
    out_dir = tmp_path / "hour_aboard_v1__2026-01-01"
    out_dir.mkdir(parents=True)
    scenario = {"name": "hour_aboard_v1", "seed": 808, "anchor_seed": "EOS_SEED_ORION"}

    meta = hour_aboard.build_run_meta(out_dir, scenario)

    assert meta["schema"] == "aurora.sim.run_meta/v1"
    assert meta["tool"] == "tools/hour_aboard.py"
    assert meta["written_at"].endswith("Z")
    assert meta["scenario"] == "hour_aboard_v1"
    assert meta["seed"] == 808

    proc = meta["process"]
    assert proc["pid"] == os.getpid()
    assert proc["ppid"] and proc["parent_command"]
    assert proc["cwd"] and proc["user"]

    assert set(meta["environment"]) >= {"claude_code", "codex", "ci"}


def test_run_meta_output_dir_makes_copies_detectable(tmp_path):
    """A directory whose name disagrees with run_meta.output_dir was copied.

    This is the check that would have answered the 2026-07-25 question in one
    command instead of an evening.
    """
    generated_in = tmp_path / "hour_aboard_v1__2026-07-13"
    generated_in.mkdir(parents=True)
    meta = hour_aboard.build_run_meta(generated_in, {"name": "hour_aboard_v1", "seed": 808})

    recorded = Path(meta["output_dir"]).name
    assert recorded == "hour_aboard_v1__2026-07-13"

    # Simulate the copy: same metadata, different containing directory.
    copied_to = tmp_path / "hour_aboard_v1__2026-07-25"
    assert recorded != copied_to.name, "copy must be detectable by name mismatch"


def test_run_meta_survives_unresolvable_parent(tmp_path, monkeypatch):
    """Provenance is best-effort: it must never crash a simulation run."""
    monkeypatch.setattr(hour_aboard.subprocess, "run", _boom)
    out_dir = tmp_path / "hour_aboard_v1__2026-01-01"
    out_dir.mkdir(parents=True)

    meta = hour_aboard.build_run_meta(out_dir, {"name": "x", "seed": 1})
    assert meta["process"]["parent_command"] == "unknown"


def _boom(*args, **kwargs):
    raise OSError("ps unavailable")


@pytest.mark.simulation
@pytest.mark.slow
def test_harness_emits_run_meta(tmp_path):
    """End-to-end: a real run writes run_meta.json alongside its artifacts."""
    state = tmp_path / "station_state.json"
    state.write_text(json.dumps({"hours_elapsed": 0, "pair_familiarity": {}, "atoms_total": 0}) + "\n")
    reports = tmp_path / "sim_reports"
    env = {
        **os.environ,
        "AURORA_STATION_STATE": str(state),
        "AURORA_SIM_REPORT_ROOT": str(reports),
        "PYTHONPATH": str(REPO_ROOT),
    }

    result = subprocess.run(
        [sys.executable, str(TOOLS_DIR / "hour_aboard.py"), "--no-mesh"],
        cwd=REPO_ROOT, env=env, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr[-800:]

    runs = sorted(reports.glob("hour_aboard_v1__*"))
    assert runs, "no artifact directory produced"
    meta_path = runs[-1] / "run_meta.json"
    assert meta_path.exists(), "run_meta.json was not written"

    meta = json.loads(meta_path.read_text())
    assert Path(meta["output_dir"]).name == runs[-1].name, (
        "run_meta.output_dir must match the directory it was written into, "
        "otherwise copy detection is broken"
    )

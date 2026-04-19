from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = REPO_ROOT / "GUMAS_SIM_2.5" / "SIM_ENGINE_OUTPUTS"
L2_SOURCES_DIR = REPO_ROOT / "GUMAS_SIM_2.0"

_l2_sources_available = L2_SOURCES_DIR.is_dir()
requires_l2_sources = pytest.mark.skipif(
    not _l2_sources_available,
    reason="GUMAS_SIM_2.0 L2 source data not present in this environment",
)

if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

import hourly_retrospective as retro  # noqa: E402


@requires_l2_sources
def test_query_tool_returns_mobile_asset_and_hotspots() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "tools" / "gumas_l2_query.py"),
            "--workspace",
            str(REPO_ROOT),
            "--query",
            "Judicator Prime",
            "--faction-id",
            "galactic_union",
            "--top-hotspots",
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["results"]["mobile_asset_matches"]
    assert any(match["name"] == "G.U.S. Judicator Prime" for match in payload["results"]["mobile_asset_matches"])
    assert payload["faction_context"]["mobile_assets"]
    assert all("SRC-" not in row["name"] for row in payload["faction_context"]["characters"])
    assert payload["hotspots"]["logistics"]


@requires_l2_sources
def test_hourly_retrospective_evidence_and_report_include_named_operational_context(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "advanced_state.json"
    metrics = retro._run_simulation(SIM_DIR, seed=42, turns=3, snapshot_path=snapshot_path)
    evidence = retro._build_evidence_brief(
        seed=42,
        generated_at_utc=datetime.now(timezone.utc),
        current_metrics=metrics,
        snapshot_path=snapshot_path,
    )
    assert evidence["named_operational_context"]["top_named_characters"]
    assert evidence["named_operational_context"]["top_mobile_assets"]
    assert evidence["named_operational_context"]["logistics_hotspots"]

    report_text = retro._build_report(
        generated_at_utc=datetime.now(timezone.utc),
        seed=42,
        previous_metrics=None,
        current_metrics=metrics,
        snapshot_path=snapshot_path,
        trends={},
        alerts=[],
        evidence_brief=evidence,
        evidence_path=tmp_path / "evidence.json",
        latest_evidence_path=tmp_path / "latest_evidence.json",
    )
    assert "## Named Operational Context" in report_text
    assert any(name in report_text for name in ("Nemesis Prime", "Omega-Veil", "Vel-Surak", "Xyphos Prime ruins"))

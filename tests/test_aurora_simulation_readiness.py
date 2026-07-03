from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_ROOT))

import aurora_simulation_readiness as simulation_readiness  # noqa: E402


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_file(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def seed_simulation_tree(root: Path) -> Path:
    engine = root / simulation_readiness.GUMAS_ENGINE_DIR
    for name in [
        "engine.py",
        "engine_advanced.py",
        "engine_base.py",
        "models.py",
        "scenarios.py",
        "formulas.py",
        "GUMAS_ENGINE_VALIDATION_REPORT.json",
    ]:
        write_file(engine / name, "{}\n" if name.endswith(".json") else "")
    write_json(
        engine / "advanced_skill_output.json",
        {
            "version": "v4.0-synth",
            "turn": 123,
            "export_timestamp": "2026-06-26T00:00:00Z",
            "latest_metrics": {"risk_index": 0.42, "stability_index": 0.78, "nested": {"ignored": True}},
        },
    )
    write_file(engine / "advanced_event_ledger.ndjson", '{"event_id":"a"}\n{"event_id":"b"}\n')
    write_file(engine / "hourly_retrospective.py")

    seed99 = root / simulation_readiness.GUMAS_SEED99_DIR
    write_json(seed99 / "advanced_skill_output.json", {"turn": 153})
    write_file(seed99 / "advanced_event_ledger.ndjson", '{"event_id":"seed99"}\n')

    cloudbank = root / simulation_readiness.CLOUDBANK_PATH
    write_file(cloudbank / "simulation/scenario_seed_initializer.py")
    write_file(cloudbank / "tests/test_scenario_seed_initializer.py")
    write_file(root / "tools/l2_scenario_seed_uptake.py")
    write_json(root / "catalog/l2_scenario_seed_catalog.json", {"scenarios": []})
    write_file(root / "docs/L2_SCENARIO_SEED_CATALOG_WORKFLOW_v1.md")
    write_file(root / "GUMAS_SIM_2.5/ORION_SCENARIO_CATALOG_v0_2_15.html")
    write_file(root / "GUMAS_SIM_2.5/ORION_SCENARIO_CATALOG_v0_2_15.pdf")

    duelsim = root / simulation_readiness.DUELSIM_PATH
    write_file(duelsim / "app_server.py")
    write_file(duelsim / "scripts/release_gate_v2_4_1.py")
    (duelsim / "web_app").mkdir(parents=True, exist_ok=True)

    write_file(root / "qgia-knowledge-library-main/data/intake/evidence-ledger.jsonl")
    write_file(root / "qgia-knowledge-library-main/data/truth/outcome-ledger.jsonl")
    write_file(root / "qgia-knowledge-spine-main/data/forecasts/forecast-ledger.jsonl")
    write_json(root / "qgia-knowledge-spine-main/data/priors/prior-table.json", {})
    write_json(root / "qgia-knowledge-spine-main/data/calibration/calibration-report.json", {})

    runner = root / ".codex/skills/gumas-simulation-engine/scripts/run_gumas_advanced.py"
    write_file(runner, "#!/usr/bin/env python3\n")
    return runner


def surface_by_id(payload: dict[str, Any], surface_id: str) -> dict[str, Any]:
    return next(surface for surface in payload["simulation_surfaces"] if surface["surface_id"] == surface_id)


def test_build_report_inventory_marks_simulation_ready(tmp_path: Path) -> None:
    runner = seed_simulation_tree(tmp_path)

    payload = simulation_readiness.build_report(
        tmp_path,
        generated_at="2026-06-26T00:00:00Z",
        skill_runner=runner,
    )

    assert payload["status"] == "ready"
    assert payload["nested_repo_mutation"] is False
    assert payload["live_runtime_execution"] is False
    assert payload["simulation_smoke_executed"] is False
    assert payload["summary"]["ready_required_surface_count"] == payload["summary"]["required_surface_count"]
    assert payload["summary"]["persisted_output_turn"] == 123
    assert payload["summary"]["primary_event_ledger_records"] == 2
    assert surface_by_id(payload, "gumas_advanced_engine")["status"] == "ready"
    assert surface_by_id(payload, "gumas_skill_runner")["status"] == "ready"
    assert payload["execution_paths"][0]["status"] == "ready"


def test_missing_core_engine_blocks_required_surface(tmp_path: Path) -> None:
    runner = seed_simulation_tree(tmp_path)
    (tmp_path / simulation_readiness.GUMAS_ENGINE_DIR / "engine_advanced.py").unlink()

    payload = simulation_readiness.build_report(
        tmp_path,
        generated_at="2026-06-26T00:00:00Z",
        skill_runner=runner,
    )

    assert payload["status"] == "blocked"
    assert payload["summary"]["blocked_required_surface_count"] == 1
    engine_surface = surface_by_id(payload, "gumas_advanced_engine")
    assert engine_surface["status"] == "blocked"
    assert str(simulation_readiness.GUMAS_ENGINE_DIR / "engine_advanced.py") in engine_surface["missing_required_markers"]


def test_run_smoke_records_bounded_simulation_result(tmp_path: Path) -> None:
    runner_path = seed_simulation_tree(tmp_path)
    output_path = tmp_path / "smoke-output.json"

    def fake_runner(
        args: list[str],
        cwd: Path,
        timeout: int,
        env: dict[str, str],
    ) -> simulation_readiness.CommandResult:
        assert cwd == tmp_path
        assert env["PYTHONPYCACHEPREFIX"].endswith("aurora_gumas_pycache")
        payload = {
            "workspace": str(tmp_path),
            "engine_dir": str(tmp_path / simulation_readiness.GUMAS_ENGINE_DIR),
            "engine_mode": "advanced",
            "engine_class": "GUMASAdvancedEngine",
            "scenario_id": "gumas_canonical_v1",
            "turns_requested": 5,
            "turns_completed": 5,
            "last_summary": "Turn 5: stable",
            "output_path": str(output_path),
            "output_exists": True,
        }
        return simulation_readiness.CommandResult(args, str(cwd), 0, json.dumps(payload), "")

    payload = simulation_readiness.build_report(
        tmp_path,
        generated_at="2026-06-26T00:00:00Z",
        run_smoke=True,
        smoke_output=output_path,
        skill_runner=runner_path,
        runner=fake_runner,
    )

    assert payload["status"] == "ready"
    assert payload["simulation_smoke_executed"] is True
    assert payload["summary"]["smoke_probe_status"] == "ready"
    assert payload["smoke_probe"]["result"]["engine_class"] == "GUMASAdvancedEngine"
    assert payload["smoke_probe"]["writes_to_repo"] is False


def test_failed_smoke_blocks_report(tmp_path: Path) -> None:
    runner_path = seed_simulation_tree(tmp_path)

    def fake_runner(
        args: list[str],
        cwd: Path,
        timeout: int,
        env: dict[str, str],
    ) -> simulation_readiness.CommandResult:
        return simulation_readiness.CommandResult(args, str(cwd), 1, "", "import failed")

    payload = simulation_readiness.build_report(
        tmp_path,
        generated_at="2026-06-26T00:00:00Z",
        run_smoke=True,
        skill_runner=runner_path,
        runner=fake_runner,
    )

    assert payload["status"] == "blocked"
    assert payload["smoke_probe"]["status"] == "blocked"
    assert payload["smoke_probe"]["stderr_preview"] == "import failed"


def test_write_report_creates_parent_dirs(tmp_path: Path) -> None:
    runner = seed_simulation_tree(tmp_path)
    payload = simulation_readiness.build_report(tmp_path, skill_runner=runner)
    out = tmp_path / "reports/analysis/aurora_simulation_readiness_latest.json"

    simulation_readiness.write_report(out, payload)

    saved = json.loads(out.read_text(encoding="utf-8"))
    assert saved["tool"] == "aurora_simulation_readiness"

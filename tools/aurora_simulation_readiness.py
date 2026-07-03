#!/usr/bin/env python3
"""Build a simulation-readiness receipt for Aurora operator consoles.

This tool inventories the local simulation runtime surfaces and can optionally
run a bounded GUMAS smoke simulation into a temp output file. It does not mutate
nested repos, send mesh messages, deploy services, or promote canon.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Union


DEFAULT_REPORT_PATH = Path("reports/analysis/aurora_simulation_readiness_latest.json")
GUMAS_ENGINE_DIR = Path("GUMAS_SIM_2.5/SIM_ENGINE_OUTPUTS")
GUMAS_SEED99_DIR = Path("GUMAS_SIM_2.5/SIM_ENGINE_OUTPUTS_SEED99")
DUELSIM_PATH = Path("GUMAS_SIM_2.5/DuelSim/DuelSim_v2.0")
CLOUDBANK_PATH = Path("GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main")
QGIA_LIBRARY_PATH = Path("qgia-knowledge-library-main")
QGIA_SPINE_PATH = Path("qgia-knowledge-spine-main")


@dataclass
class CommandResult:
    args: list[str]
    cwd: str
    returncode: int
    stdout: str
    stderr: str


Runner = Callable[[list[str], Path, int, dict[str, str]], CommandResult]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def default_skill_runner() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    return codex_home / "skills/gumas-simulation-engine/scripts/run_gumas_advanced.py"


def default_smoke_output_path() -> Path:
    return Path(tempfile.gettempdir()) / "aurora_gumas_smoke_latest.json"


def default_pycache_prefix() -> str:
    return str(Path(tempfile.gettempdir()) / "aurora_gumas_pycache")


def read_json(path: Path) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data, None
        return None, "json_root_not_object"
    except FileNotFoundError:
        return None, "missing"
    except json.JSONDecodeError as exc:
        return None, f"invalid_json: {exc.msg}"
    except OSError as exc:
        return None, f"unreadable: {exc}"


def line_count(path: Path) -> Optional[int]:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return sum(1 for _ in handle)
    except OSError:
        return None


def marker(root: Path, rel: Union[Path, str], *, required: bool = True) -> dict[str, Any]:
    rel_path = Path(rel).as_posix()
    path = root / rel_path
    return {"path": rel_path, "exists": path.exists(), "required": required}


def surface_status(markers: Iterable[dict[str, Any]]) -> str:
    marker_list = list(markers)
    if any(item["required"] and not item["exists"] for item in marker_list):
        return "blocked"
    if any(not item["exists"] for item in marker_list):
        return "attention"
    return "ready"


def surface(
    root: Path,
    *,
    surface_id: str,
    title: str,
    role: str,
    repo: str,
    markers: list[dict[str, Any]],
    required: bool = True,
    execution_boundary: str,
) -> dict[str, Any]:
    status = surface_status(markers)
    return {
        "surface_id": surface_id,
        "title": title,
        "role": role,
        "repo": repo,
        "status": status,
        "required": required,
        "markers": markers,
        "missing_required_markers": [
            item["path"] for item in markers if item["required"] and not item["exists"]
        ],
        "execution_boundary": execution_boundary,
    }


def collect_surfaces(root: Path, skill_runner: Path) -> list[dict[str, Any]]:
    return [
        surface(
            root,
            surface_id="gumas_advanced_engine",
            title="GUMAS advanced simulation engine",
            role="primary_multi_turn_simulation_runtime",
            repo="root/GUMAS_SIM_2.5",
            required=True,
            markers=[
                marker(root, GUMAS_ENGINE_DIR / "engine.py"),
                marker(root, GUMAS_ENGINE_DIR / "engine_advanced.py"),
                marker(root, GUMAS_ENGINE_DIR / "engine_base.py"),
                marker(root, GUMAS_ENGINE_DIR / "models.py"),
                marker(root, GUMAS_ENGINE_DIR / "scenarios.py"),
                marker(root, GUMAS_ENGINE_DIR / "formulas.py"),
                marker(root, GUMAS_ENGINE_DIR / "advanced_skill_output.json"),
                marker(root, GUMAS_ENGINE_DIR / "advanced_event_ledger.ndjson"),
                marker(root, GUMAS_ENGINE_DIR / "GUMAS_ENGINE_VALIDATION_REPORT.json"),
            ],
            execution_boundary="local_seeded_engine_run",
        ),
        surface(
            root,
            surface_id="gumas_skill_runner",
            title="Codex GUMAS simulation runner",
            role="bounded_seeded_smoke_execution",
            repo="local_codex_runtime",
            required=True,
            markers=[
                {
                    "path": str(skill_runner),
                    "exists": skill_runner.exists(),
                    "required": True,
                }
            ],
            execution_boundary="runs_local_simulation_to_temp_output_only",
        ),
        surface(
            root,
            surface_id="gumas_seed99_outputs",
            title="GUMAS seed 99 output corpus",
            role="comparison_seed_evidence",
            repo="root/GUMAS_SIM_2.5",
            required=False,
            markers=[
                marker(root, GUMAS_SEED99_DIR / "advanced_skill_output.json", required=False),
                marker(root, GUMAS_SEED99_DIR / "advanced_event_ledger.ndjson", required=False),
            ],
            execution_boundary="persisted_output_evidence_only",
        ),
        surface(
            root,
            surface_id="cloudbank_scenario_seed_bridge",
            title="CloudBank scenario seed bridge",
            role="scenario_seed_uptake_and_runtime_adapter",
            repo="aurora-cloudbank-symbolic-main",
            required=True,
            markers=[
                marker(root, CLOUDBANK_PATH / "simulation/scenario_seed_initializer.py"),
                marker(root, CLOUDBANK_PATH / "tests/test_scenario_seed_initializer.py"),
                marker(root, "tools/l2_scenario_seed_uptake.py"),
                marker(root, "catalog/l2_scenario_seed_catalog.json"),
            ],
            execution_boundary="scenario_fixture_generation_requires_explicit_nested_repo_gate",
        ),
        surface(
            root,
            surface_id="duelsim_runtime",
            title="DuelSim app and release gate",
            role="interactive_simulation_app_surface",
            repo="DuelSim_v2.0",
            required=False,
            markers=[
                marker(root, DUELSIM_PATH / "app_server.py", required=False),
                marker(root, DUELSIM_PATH / "scripts/release_gate_v2_4_1.py", required=False),
                marker(root, DUELSIM_PATH / "web_app", required=False),
            ],
            execution_boundary="separate_nested_repo_runtime",
        ),
        surface(
            root,
            surface_id="qgia_forecast_loop",
            title="QGIA forecast and outcome ledgers",
            role="forecast_simulation_feedback_loop",
            repo="qgia-knowledge-library-main/qgia-knowledge-spine-main",
            required=False,
            markers=[
                marker(root, QGIA_LIBRARY_PATH / "data/intake/evidence-ledger.jsonl", required=False),
                marker(root, QGIA_LIBRARY_PATH / "data/truth/outcome-ledger.jsonl", required=False),
                marker(root, QGIA_SPINE_PATH / "data/forecasts/forecast-ledger.jsonl", required=False),
                marker(root, QGIA_SPINE_PATH / "data/priors/prior-table.json", required=False),
                marker(root, QGIA_SPINE_PATH / "data/calibration/calibration-report.json", required=False),
            ],
            execution_boundary="ledger_presence_only",
        ),
        surface(
            root,
            surface_id="scenario_catalog",
            title="Scenario catalog and fixture contract",
            role="simulation_scenario_supply",
            repo="root/GUMAS_SIM_2.5",
            required=False,
            markers=[
                marker(root, "catalog/l2_scenario_seed_catalog.json", required=False),
                marker(root, "docs/L2_SCENARIO_SEED_CATALOG_WORKFLOW_v1.md", required=False),
                marker(root, "GUMAS_SIM_2.5/ORION_SCENARIO_CATALOG_v0_2_15.html", required=False),
                marker(root, "GUMAS_SIM_2.5/ORION_SCENARIO_CATALOG_v0_2_15.pdf", required=False),
            ],
            execution_boundary="catalog_and_fixture_evidence_only",
        ),
    ]


def compact_latest_output(root: Path) -> dict[str, Any]:
    output_path = root / GUMAS_ENGINE_DIR / "advanced_skill_output.json"
    data, error = read_json(output_path)
    if data is None:
        return {"available": False, "path": output_path.as_posix(), "error": error}
    latest_metrics = data.get("latest_metrics") if isinstance(data.get("latest_metrics"), dict) else {}
    compact_metrics = {
        key: value
        for key, value in latest_metrics.items()
        if isinstance(value, (int, float, str, bool)) or value is None
    }
    return {
        "available": True,
        "path": output_path.as_posix(),
        "turn": data.get("turn"),
        "version": data.get("version"),
        "export_timestamp": data.get("export_timestamp"),
        "latest_metrics": compact_metrics,
    }


def collect_artifact_evidence(root: Path) -> dict[str, Any]:
    return {
        "latest_output": compact_latest_output(root),
        "primary_event_ledger": {
            "path": (root / GUMAS_ENGINE_DIR / "advanced_event_ledger.ndjson").as_posix(),
            "record_count": line_count(root / GUMAS_ENGINE_DIR / "advanced_event_ledger.ndjson"),
        },
        "seed99_event_ledger": {
            "path": (root / GUMAS_SEED99_DIR / "advanced_event_ledger.ndjson").as_posix(),
            "record_count": line_count(root / GUMAS_SEED99_DIR / "advanced_event_ledger.ndjson"),
        },
    }


def run_command(args: list[str], cwd: Path, timeout: int, env: dict[str, str]) -> CommandResult:
    command_env = dict(os.environ)
    command_env.update(env)
    try:
        completed = subprocess.run(
            args,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            env=command_env,
        )
        return CommandResult(args, str(cwd), completed.returncode, completed.stdout, completed.stderr)
    except subprocess.TimeoutExpired as exc:
        return CommandResult(args, str(cwd), 124, exc.stdout or "", exc.stderr or "command timed out")
    except OSError as exc:
        return CommandResult(args, str(cwd), 127, "", str(exc))


def compact_smoke_payload(payload: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "workspace",
        "engine_dir",
        "engine_mode",
        "engine_class",
        "scenario_id",
        "turns_requested",
        "turns_completed",
        "last_summary",
        "output_path",
        "output_exists",
    ]
    return {key: payload.get(key) for key in keys if key in payload}


def build_smoke_probe(
    root: Path,
    *,
    run_smoke: bool,
    skill_runner: Path,
    turns: int,
    seed: int,
    output_path: Path,
    timeout: int,
    runner: Runner,
) -> dict[str, Any]:
    command = [
        "python3",
        str(skill_runner),
        "--workspace",
        str(root),
        "--turns",
        str(max(0, turns)),
        "--seed",
        str(seed),
        "--output",
        str(output_path),
    ]
    probe = {
        "requested": run_smoke,
        "status": "not_run",
        "turns": max(0, turns),
        "seed": seed,
        "command": command,
        "output_path": str(output_path),
        "writes_to_repo": False,
        "nested_repo_mutation": False,
        "live_runtime_execution": False,
        "recommended_next_action": "Run with --run-smoke to execute a bounded local GUMAS smoke simulation.",
    }

    if not run_smoke:
        return probe
    if not skill_runner.exists():
        return {
            **probe,
            "status": "blocked",
            "error": "gumas_skill_runner_missing",
            "recommended_next_action": "Install or sync the gumas-simulation-engine skill before smoke execution.",
        }
    if not (root / GUMAS_ENGINE_DIR).is_dir():
        return {
            **probe,
            "status": "blocked",
            "error": "gumas_engine_dir_missing",
            "recommended_next_action": "Restore GUMAS_SIM_2.5/SIM_ENGINE_OUTPUTS before smoke execution.",
        }

    result = runner(command, root, timeout, {"PYTHONPYCACHEPREFIX": default_pycache_prefix()})
    record = {
        **probe,
        "status": "blocked" if result.returncode else "ready",
        "returncode": result.returncode,
        "stdout_preview": result.stdout[:800],
        "stderr_preview": result.stderr[:800],
    }
    try:
        payload = json.loads(result.stdout)
        if isinstance(payload, dict):
            record["result"] = compact_smoke_payload(payload)
            if result.returncode == 0 and payload.get("output_exists") is False:
                record["status"] = "attention"
                record["recommended_next_action"] = "Smoke command completed but did not confirm output export."
    except json.JSONDecodeError:
        if result.returncode == 0:
            record["status"] = "attention"
            record["recommended_next_action"] = "Smoke command returned non-JSON output; inspect stdout preview."
    if result.returncode == 0 and record["status"] == "ready":
        record["recommended_next_action"] = None
    return record


def execution_paths(root: Path, skill_runner: Path, smoke_output: Path) -> list[dict[str, Any]]:
    runner_available = skill_runner.exists() and (root / GUMAS_ENGINE_DIR).is_dir()
    hourly = root / GUMAS_ENGINE_DIR / "hourly_retrospective.py"
    command_intent = root / "tools/aurora_command_intent.py"
    return [
        {
            "path_id": "gumas_advanced_seeded_smoke",
            "title": "Run bounded GUMAS advanced simulation smoke",
            "status": "ready" if runner_available else "blocked",
            "command": [
                "PYTHONPYCACHEPREFIX=/tmp/aurora_gumas_pycache",
                "python3",
                str(skill_runner),
                "--workspace",
                "$PWD",
                "--turns",
                "5",
                "--seed",
                "42",
                "--output",
                str(smoke_output),
            ],
            "writes_to_repo": False,
            "nested_repo_mutation": False,
        },
        {
            "path_id": "gumas_hourly_retrospective_dry_run",
            "title": "Compute the next GUMAS retrospective turn without canonical writes",
            "status": "ready" if hourly.exists() else "attention",
            "command": [
                "PYTHONPYCACHEPREFIX=/tmp/aurora_gumas_pycache",
                "python3",
                hourly.relative_to(root).as_posix() if hourly.is_absolute() and root in hourly.parents else hourly.as_posix(),
                "--workspace",
                ".",
                "--dry-run",
            ],
            "writes_to_repo": False,
            "nested_repo_mutation": False,
        },
        {
            "path_id": "command_intent_range_simulation",
            "title": "Run in-process command range simulation",
            "status": "ready" if command_intent.exists() else "attention",
            "command": ["python3", "tools/aurora_command_intent.py", "simulate-range", "001//005//"],
            "writes_to_repo": False,
            "nested_repo_mutation": False,
        },
    ]


def report_status(surfaces: list[dict[str, Any]], smoke_probe: dict[str, Any]) -> str:
    required = [item for item in surfaces if item["required"]]
    if any(item["status"] == "blocked" for item in required):
        return "blocked"
    if smoke_probe["requested"] and smoke_probe["status"] == "blocked":
        return "blocked"
    if smoke_probe["requested"] and smoke_probe["status"] not in {"ready", "not_run"}:
        return "attention"
    return "ready"


def summarize(
    surfaces: list[dict[str, Any]],
    paths: list[dict[str, Any]],
    smoke_probe: dict[str, Any],
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    required = [item for item in surfaces if item["required"]]
    latest_output = artifacts.get("latest_output", {})
    primary_ledger = artifacts.get("primary_event_ledger", {})
    return {
        "surface_count": len(surfaces),
        "required_surface_count": len(required),
        "ready_surface_count": sum(1 for item in surfaces if item["status"] == "ready"),
        "attention_surface_count": sum(1 for item in surfaces if item["status"] == "attention"),
        "blocked_surface_count": sum(1 for item in surfaces if item["status"] == "blocked"),
        "ready_required_surface_count": sum(1 for item in required if item["status"] == "ready"),
        "blocked_required_surface_count": sum(1 for item in required if item["status"] == "blocked"),
        "execution_path_count": len(paths),
        "available_execution_path_count": sum(1 for item in paths if item["status"] == "ready"),
        "persisted_output_turn": latest_output.get("turn"),
        "primary_event_ledger_records": primary_ledger.get("record_count"),
        "smoke_probe_status": smoke_probe["status"],
        "smoke_probe_requested": smoke_probe["requested"],
    }


def build_report(
    root: Path,
    *,
    generated_at: Optional[str] = None,
    run_smoke: bool = False,
    turns: int = 5,
    seed: int = 42,
    smoke_output: Optional[Path] = None,
    timeout: int = 30,
    skill_runner: Optional[Path] = None,
    runner: Runner = run_command,
) -> dict[str, Any]:
    resolved_runner = skill_runner or default_skill_runner()
    resolved_smoke_output = smoke_output or default_smoke_output_path()
    if not resolved_smoke_output.is_absolute():
        resolved_smoke_output = root / resolved_smoke_output

    surfaces = collect_surfaces(root, resolved_runner)
    artifacts = collect_artifact_evidence(root)
    paths = execution_paths(root, resolved_runner, resolved_smoke_output)
    smoke_probe = build_smoke_probe(
        root,
        run_smoke=run_smoke,
        skill_runner=resolved_runner,
        turns=turns,
        seed=seed,
        output_path=resolved_smoke_output,
        timeout=timeout,
        runner=runner,
    )
    summary = summarize(surfaces, paths, smoke_probe, artifacts)
    return {
        "schema_version": 1,
        "tool": "aurora_simulation_readiness",
        "generated_at": generated_at or utc_now(),
        "root": str(root),
        "status": report_status(surfaces, smoke_probe),
        "run_mode": "read_only_inventory_plus_optional_bounded_smoke",
        "mutation_posture": "advisory_only",
        "nested_repo_mutation": False,
        "live_runtime_execution": False,
        "simulation_smoke_executed": bool(run_smoke),
        "summary": summary,
        "simulation_surfaces": surfaces,
        "execution_paths": paths,
        "artifact_evidence": artifacts,
        "smoke_probe": smoke_probe,
        "validation_commands": [
            "python3 tools/aurora_simulation_readiness.py --persist-report --summary",
            "python3 tools/aurora_simulation_readiness.py --persist-report --run-smoke --summary",
            "python3 tools/aurora_operator_snapshot.py --persist-report --summary",
            "python3 -m pytest -q tests/test_aurora_simulation_readiness.py tests/test_aurora_operator_snapshot.py",
        ],
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def print_summary(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    print(f"status: {payload['status']}")
    print(
        "required_surfaces: "
        f"{summary['ready_required_surface_count']}/{summary['required_surface_count']}"
    )
    print(f"surfaces: {summary['ready_surface_count']}/{summary['surface_count']} ready")
    print(
        "execution_paths: "
        f"{summary['available_execution_path_count']}/{summary['execution_path_count']}"
    )
    print(f"persisted_output_turn: {summary['persisted_output_turn']}")
    print(f"primary_event_ledger_records: {summary['primary_event_ledger_records']}")
    print(f"smoke_probe: {summary['smoke_probe_status']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Aurora simulation-readiness receipt.")
    parser.add_argument("--root", default=".", help="Workspace root. Defaults to current directory.")
    parser.add_argument("--report-out", help="Write the receipt to this path.")
    parser.add_argument("--persist-report", action="store_true", help=f"Write {DEFAULT_REPORT_PATH}.")
    parser.add_argument("--summary", action="store_true", help="Print a concise summary instead of JSON.")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout.")
    parser.add_argument("--run-smoke", action="store_true", help="Run a bounded GUMAS smoke simulation.")
    parser.add_argument("--turns", type=int, default=5, help="Smoke-run turns. Defaults to 5.")
    parser.add_argument("--seed", type=int, default=42, help="Smoke-run seed. Defaults to 42.")
    parser.add_argument("--smoke-output", type=Path, help="Smoke-run output JSON path. Defaults to temp.")
    parser.add_argument("--timeout", type=int, default=30, help="Smoke-run timeout in seconds.")
    parser.add_argument("--skill-runner", type=Path, help="Override gumas-simulation-engine runner path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    payload = build_report(
        root,
        run_smoke=args.run_smoke,
        turns=args.turns,
        seed=args.seed,
        smoke_output=args.smoke_output,
        timeout=args.timeout,
        skill_runner=args.skill_runner,
    )

    if args.persist_report:
        write_report(root / DEFAULT_REPORT_PATH, payload)
    if args.report_out:
        write_report(Path(args.report_out), payload)

    if args.summary:
        print_summary(payload)
    elif args.json or not (args.persist_report or args.report_out):
        print(json.dumps(payload, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

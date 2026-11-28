#!/usr/bin/env python3
"""Run generated L2 scenario seed fixtures end-to-end through the L1 harness.

Each fixture in ``catalog/generated_watch_scenarios/`` (see
``tools/l2_scenario_fixture_generator.py``) runs through ``tools/hour_aboard.py``
against the CloudBank Orion Station simulation, then:

1. checks the harness run (all fixture tasks registered, work recorded, full
   souls accounting, a valid L3 narrative-audit verdict, ORD dispatch receipt);
2. builds the fixture's root uptake packet and feeds it to CloudBank's
   ``simulation/scenario_seed_initializer.py`` adapter, confirming the runtime
   initializer accepts it with the fixture's seed, ticks, and anchor;
3. writes ``fixture_run_receipt.json`` beside the run artifacts.

Fixture runs use an isolated station clock (fresh state per run), so they are
deterministic per seed and never advance Orion Station's chronicle. Run
artifacts land under ``reports/scenario_fixture_runs/`` (git-ignored, outside
``reports/simulation`` so the station chronicle does not ingest them). A suite
run (``--all``) also refreshes ``reports/analysis/l2_scenario_fixture_runs_latest.json``.

Expected end states are observation categories: the receipt records what the
run produced, never which ending "won".

Usage:
    python3 tools/l2_scenario_fixture_run.py --fixture SCN-0903
    python3 tools/l2_scenario_fixture_run.py --all
    python3 tools/l2_scenario_fixture_run.py --list
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import hour_aboard  # noqa: E402
import l2_scenario_seed_uptake as uptake  # noqa: E402
from _workspace_common import write_json  # noqa: E402

FIXTURE_DIR = ROOT / "catalog" / "generated_watch_scenarios"
MANIFEST = FIXTURE_DIR / "index.json"
DEFAULT_RUN_ROOT = ROOT / "reports" / "scenario_fixture_runs"
SUITE_SUMMARY = ROOT / "reports" / "analysis" / "l2_scenario_fixture_runs_latest.json"
VALID_VERDICTS = {"supported", "plausible", "possible_with_setup", "strained", "contradictory"}

INITIALIZER_DRIVER = r"""
import json, sys
sys.path.insert(0, ".")
from simulation.scenario_seed_initializer import (
    ScenarioSeedInitializationError, initialize_from_uptake_packet,
)
packet = json.loads(sys.argv[1])
try:
    init = initialize_from_uptake_packet(packet)
    print(json.dumps({"accepted": True, "initial_state": init.to_initial_state()}))
except ScenarioSeedInitializationError as exc:
    print(json.dumps({"accepted": False, "error": str(exc)}))
"""


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def resolve(keys: list[str], manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Map card ids (SCN-0903) or fixture ids to manifest rows."""
    by_key = {}
    for row in manifest["fixtures"]:
        by_key[row["card_id"]] = row
        by_key[row["fixture_id"]] = row
    missing = [k for k in keys if k not in by_key]
    if missing:
        raise SystemExit(f"unknown fixture(s): {', '.join(missing)} (see --list)")
    return [by_key[k] for k in keys]


def run_harness(fixture_id: str, out_dir: Path, mesh: bool) -> subprocess.CompletedProcess[str]:
    state = out_dir / "station_state.isolated.json"
    state.write_text(json.dumps({"hours_elapsed": 0, "pair_familiarity": {}}) + "\n")
    env = {**os.environ, "AURORA_STATION_STATE": str(state)}
    argv = [
        sys.executable,
        str(ROOT / "tools" / "hour_aboard.py"),
        "--scenario",
        f"generated_watch_scenarios/{fixture_id}",
        "--out-dir",
        str(out_dir),
    ]
    if not mesh:
        argv.append("--no-mesh")
    return subprocess.run(  # noqa: S603 - our own harness with fixed argv
        argv, capture_output=True, text=True, cwd=ROOT, env=env, timeout=900
    )


def uptake_packet(card_id: str) -> dict[str, Any]:
    catalog = uptake.load_json(uptake.DEFAULT_CATALOG)
    contract = uptake.load_json(uptake.DEFAULT_CONTRACT)
    report = uptake.build_report(catalog, contract, ids=[card_id])
    if report["status"] != "valid":
        raise RuntimeError(f"uptake packet invalid: {report['findings']}")
    return report["packets"][0]


def check_initializer(card_id: str) -> dict[str, Any]:
    try:
        return hour_aboard._run_in_clone(INITIALIZER_DRIVER, uptake_packet(card_id))
    except (Exception, SystemExit) as exc:  # noqa: BLE001 - recorded as a failed check
        return {"accepted": False, "error": str(exc)[:240]}


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def evaluate(fixture: dict[str, Any], out_dir: Path, proc: subprocess.CompletedProcess[str],
             init: dict[str, Any]) -> dict[str, Any]:
    sim = _read(out_dir / "sim_raw.json")
    ops = _read(out_dir / "companion_ops.json")
    souls = _read(out_dir / "souls_accounting.json")
    summary = sim.get("summary", {})
    verdict = ops.get("l3_receipt", {}).get("narrative_audit_verdict")
    task_ids = [t["id"] for t in fixture["tasks"]]
    initial = init.get("initial_state", {})
    checks = {
        "harness_exit_ok": proc.returncode == 0,
        "all_tasks_registered": sorted(sim.get("task_names", {})) == sorted(task_ids),
        "work_recorded": float(summary.get("total_spent", 0)) > 0,
        "souls_accounting_complete": bool(souls.get("complete")),
        "l3_verdict_valid": verdict in VALID_VERDICTS,
        "ord_dispatch_receipt": bool(sim.get("ord_dispatch", {}).get("receipt_sha256")),
        "initializer_accepted": bool(init.get("accepted")),
        "initializer_matches_fixture": (
            initial.get("source_card_id") == fixture["source_scenario_seed"]["card_id"]
            and initial.get("seed") == fixture["seed"]
            and initial.get("ticks") == fixture["ticks"]
            and initial.get("anchor_seed") == fixture["anchor_seed"]
        ),
    }
    overlay = fixture["scenario_seed_overlay"]
    return {
        "card_id": fixture["source_scenario_seed"]["card_id"],
        "handle": fixture["source_scenario_seed"]["handle"],
        "fixture_id": fixture["name"],
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "observations": {
            "seed": fixture["seed"],
            "ticks": summary.get("ticks"),
            "characters_engaged": summary.get("characters_used"),
            "tasks_completed": len(summary.get("completed_ids", [])),
            "task_count": len(task_ids),
            "hours_worked": summary.get("total_spent"),
            "emergent_events": len(sim.get("events", [])),
            "l3_verdict": verdict,
            "souls_logged": souls.get("crew_logged"),
            "ord_drones": sim.get("ord_dispatch", {}).get("drones_required", []),
        },
        "initializer": {
            "accepted": bool(init.get("accepted")),
            "error": init.get("error"),
            "pressure_axes": initial.get("initial_condition_vector", {}).get("pressure", []),
            "role_count": len(initial.get("initial_condition_vector", {}).get("roles", [])),
            "knob_count": len(initial.get("initial_condition_vector", {}).get("knobs", {})),
        },
        "end_state_categories_open": list(overlay["expected_end_state_categories"]),
        "end_state_handling": overlay["end_state_handling"],
        "harness_stderr_tail": proc.stderr.strip().splitlines()[-1][:240] if proc.returncode and proc.stderr else None,
    }


def run_fixture(row: dict[str, Any], run_root: Path, mesh: bool) -> dict[str, Any]:
    fixture = json.loads((ROOT / row["path"]).read_text(encoding="utf-8"))
    out_dir = run_root / fixture["name"]
    out_dir.mkdir(parents=True, exist_ok=True)
    proc = run_harness(fixture["name"], out_dir, mesh)
    init = check_initializer(row["card_id"])
    result = evaluate(fixture, out_dir, proc, init)
    (out_dir / "fixture_run_receipt.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def suite_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    passed = sum(1 for r in results if r["status"] == "pass")
    return {
        "artifact_id": "l2_scenario_fixture_runs",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "runner": "tools/l2_scenario_fixture_run.py",
        "harness": "tools/hour_aboard.py (isolated station clock, no mesh)",
        "fixture_count": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "status": "pass" if passed == len(results) else "fail",
        "results": [
            {
                "card_id": r["card_id"],
                "fixture_id": r["fixture_id"],
                "status": r["status"],
                "failed_checks": sorted(k for k, ok in r["checks"].items() if not ok),
                "tasks_completed": f"{r['observations']['tasks_completed']}/{r['observations']['task_count']}",
                "emergent_events": r["observations"]["emergent_events"],
                "l3_verdict": r["observations"]["l3_verdict"],
                "initializer_accepted": r["initializer"]["accepted"],
            }
            for r in results
        ],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--fixture", nargs="+", help="card ids (SCN-0903) or fixture ids to run")
    group.add_argument("--all", action="store_true", help="run every generated fixture")
    group.add_argument("--list", action="store_true", help="list generated fixtures")
    parser.add_argument("--run-root", default=None, help="artifact root (default reports/scenario_fixture_runs/<date>)")
    parser.add_argument("--mesh", action="store_true", help="also pulse companions over the live mesh")
    parser.add_argument("--no-summary", action="store_true", help="with --all, skip the reports/analysis summary")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = load_manifest()
    if args.list:
        for row in manifest["fixtures"]:
            print(f"{row['card_id']}  {row['fixture_id']}  ({row['fixture_status']})")
        return 0
    rows = manifest["fixtures"] if args.all else resolve(args.fixture, manifest)
    if args.run_root:
        run_root = Path(args.run_root)
    else:
        run_root = DEFAULT_RUN_ROOT / datetime.now(timezone.utc).strftime("%Y-%m-%d")
    run_root.mkdir(parents=True, exist_ok=True)

    results = []
    for row in rows:
        result = run_fixture(row, run_root, args.mesh)
        results.append(result)
        obs = result["observations"]
        mark = "✅" if result["status"] == "pass" else "❌"
        failed = [k for k, ok in result["checks"].items() if not ok]
        print(
            f"{mark} {result['card_id']} {result['handle']}: tasks {obs['tasks_completed']}/{obs['task_count']}, "
            f"events {obs['emergent_events']}, L3 {obs['l3_verdict']}, "
            f"initializer {'ok' if result['initializer']['accepted'] else 'REJECTED'}"
            + (f" — failed: {', '.join(failed)}" if failed else "")
        )
    summary = suite_summary(results)
    if args.all and not args.no_summary:
        write_json(SUITE_SUMMARY, summary)
    print(f"\n{summary['passed']}/{summary['fixture_count']} fixtures passed; artifacts under {run_root}")
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())

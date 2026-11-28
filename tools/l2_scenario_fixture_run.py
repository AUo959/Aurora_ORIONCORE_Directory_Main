#!/usr/bin/env python3
"""Run generated L2 scenario seed fixtures end-to-end through the L1 harness."""

# Each fixture in ``catalog/generated_watch_scenarios/`` (see
# ``tools/l2_scenario_fixture_generator.py``) runs through ``tools/hour_aboard.py``
# against the CloudBank Orion Station simulation, then:
#
# 1. checks the harness run (all fixture tasks registered, work recorded, full
#    souls accounting, a valid L3 narrative-audit verdict, ORD dispatch receipt);
# 2. builds the fixture's root uptake packet and feeds it to CloudBank's
#    ``simulation/scenario_seed_initializer.py`` adapter, confirming the runtime
#    initializer accepts it with the fixture's seed, ticks, and anchor;
# 3. writes ``fixture_run_receipt.json`` beside the run artifacts.
#
# Fixture runs use an isolated station clock (fresh state per run), so they are
# deterministic per seed and never advance Orion Station's chronicle. Run
# artifacts land under ``reports/scenario_fixture_runs/`` (git-ignored, outside
# ``reports/simulation`` so the station chronicle does not ingest them). A suite
# run (``--all``) also refreshes ``reports/analysis/l2_scenario_fixture_runs_latest.json``.
#
# Expected end states are observation categories: the receipt records what the
# run produced, never which ending "won".
#
# Usage:
#     python3 tools/l2_scenario_fixture_run.py --fixture SCN-0903
#     python3 tools/l2_scenario_fixture_run.py --all
#     python3 tools/l2_scenario_fixture_run.py --list

from __future__ import annotations

import argparse
import json
import os
import subprocess  # nosec B404 - runs this repo's own harness with fixed argv
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import hour_aboard  # noqa: E402
import l2_scenario_seed_uptake as uptake  # noqa: E402
import scenario_seed_dynamics as seed_dynamics  # noqa: E402
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
    return subprocess.run(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit # noqa: S603 # nosec B603
        argv, capture_output=True, text=True, cwd=ROOT, env=env, timeout=900, check=False
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


def _initializer_matches(fixture: dict[str, Any], initial: dict[str, Any]) -> bool:
    expected = {
        "source_card_id": fixture["source_scenario_seed"]["card_id"],
        "seed": fixture["seed"],
        "ticks": fixture["ticks"],
        "anchor_seed": fixture["anchor_seed"],
    }
    return all(initial.get(key) == value for key, value in expected.items())


def _expected_task_ids(fixture: dict[str, Any], sim: dict[str, Any]) -> list[str]:
    """Fixture tasks plus one role-position task per seed role."""
    card = fixture["source_scenario_seed"]["card_id"]
    roles = fixture["scenario_seed_overlay"]["roles"]
    return [t["id"] for t in fixture["tasks"]] + [f"{card}-R{i}" for i in range(1, len(roles) + 1)]


def _seed_dynamics_applied(fixture: dict[str, Any], sim: dict[str, Any]) -> bool:
    """The run consumed the seed: plan schema present, every axis wired, solver chosen."""
    dyn = sim.get("seed_dynamics", {})
    solver = dyn.get("dominant_solver")
    shock_axes = {s["axis"] for s in dyn.get("shocks", [])}
    return (
        dyn.get("schema") == seed_dynamics.SCHEMA
        and isinstance(solver, str)
        and bool(solver)
        and shock_axes <= set(fixture["scenario_seed_overlay"]["pressure"])
    )


def _checks(fixture: dict[str, Any], run: dict[str, Any], init: dict[str, Any]) -> dict[str, bool]:
    sim, verdict = run["sim"], run["verdict"]
    return {
        "harness_exit_ok": run["returncode"] == 0,
        "all_tasks_registered": sorted(sim.get("task_names", {})) == sorted(_expected_task_ids(fixture, sim)),
        "seed_dynamics_applied": _seed_dynamics_applied(fixture, sim),
        "work_recorded": float(sim.get("summary", {}).get("total_spent", 0)) > 0,
        "souls_accounting_complete": bool(run["souls"].get("complete")),
        "l3_verdict_valid": verdict in VALID_VERDICTS,
        "ord_dispatch_receipt": bool(sim.get("ord_dispatch", {}).get("receipt_sha256")),
        "initializer_accepted": bool(init.get("accepted")),
        "initializer_matches_fixture": _initializer_matches(fixture, init.get("initial_state", {})),
    }


def _observations(fixture: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    sim = run["sim"]
    summary = sim.get("summary", {})
    return {
        "seed": fixture["seed"],
        "ticks": summary.get("ticks"),
        "characters_engaged": summary.get("characters_used"),
        "tasks_completed": len(summary.get("completed_ids", [])),
        "task_count": len(sim.get("task_names", {})) or len(fixture["tasks"]),
        "hours_worked": summary.get("total_spent"),
        "emergent_events": len(sim.get("events", [])),
        "l3_verdict": run["verdict"],
        "souls_logged": run["souls"].get("crew_logged"),
        "ord_drones": sim.get("ord_dispatch", {}).get("drones_required", []),
        "seed_dynamics": _dynamics_summary(sim),
    }


def _dynamics_summary(sim: dict[str, Any]) -> dict[str, Any]:
    dyn = sim.get("seed_dynamics", {})
    return {
        "dominant_solver": dyn.get("dominant_solver"),
        "pressure_stalls": dyn.get("pressure_stalls", 0),
        "pressure_absorbed": dyn.get("pressure_absorbed", 0),
        "stalls_by_axis": _stalls_by_axis(dyn),
        "crew_diverted_hours": sum(len(v) for v in dyn.get("diversions", {}).values()),
        "role_positions_held": len(dyn.get("role_tasks_completed", [])),
        "escalated_at_hour": None if dyn.get("escalated_at") is None else dyn["escalated_at"] + 1,
    }


def _stalls_by_axis(dyn: dict[str, Any]) -> dict[str, int]:
    out: dict[str, int] = {}
    for shock in dyn.get("shocks", []):
        if not shock["absorbed"]:
            out[shock["axis"]] = out.get(shock["axis"], 0) + 1
    return dict(sorted(out.items()))


def _initializer_summary(init: dict[str, Any]) -> dict[str, Any]:
    vector = init.get("initial_state", {}).get("initial_condition_vector", {})
    return {
        "accepted": bool(init.get("accepted")),
        "error": init.get("error"),
        "pressure_axes": vector.get("pressure", []),
        "role_count": len(vector.get("roles", [])),
        "knob_count": len(vector.get("knobs", {})),
    }


def _stderr_tail(proc: subprocess.CompletedProcess[str]) -> str | None:
    if proc.returncode == 0 or not proc.stderr.strip():
        return None
    return proc.stderr.strip().splitlines()[-1][:240]


def evaluate(fixture: dict[str, Any], out_dir: Path, proc: subprocess.CompletedProcess[str],
             init: dict[str, Any]) -> dict[str, Any]:
    run = {
        "returncode": proc.returncode,
        "sim": _read(out_dir / "sim_raw.json"),
        "souls": _read(out_dir / "souls_accounting.json"),
        "verdict": _read(out_dir / "companion_ops.json").get("l3_receipt", {}).get("narrative_audit_verdict"),
    }
    checks = _checks(fixture, run, init)
    overlay = fixture["scenario_seed_overlay"]
    return {
        "card_id": fixture["source_scenario_seed"]["card_id"],
        "handle": fixture["source_scenario_seed"]["handle"],
        "fixture_id": fixture["name"],
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "observations": _observations(fixture, run),
        "initializer": _initializer_summary(init),
        "end_state_categories_open": list(overlay["expected_end_state_categories"]),
        "end_state_handling": overlay["end_state_handling"],
        "harness_stderr_tail": _stderr_tail(proc),
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
    signatures = {seed_dynamics.run_signature(r["observations"]) for r in results}
    return {
        "artifact_id": "l2_scenario_fixture_runs",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "runner": "tools/l2_scenario_fixture_run.py",
        "harness": "tools/hour_aboard.py (isolated station clock, no mesh)",
        "fixture_count": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "status": "pass" if passed == len(results) else "fail",
        # How many runs came out differently (tasks closed, L3 verdict, solver,
        # stalls, absorptions). Before seed dynamics every fixture ran alike.
        "distinct_run_signatures": len(signatures),
        "l3_verdicts": dict(sorted(Counter(r["observations"]["l3_verdict"] for r in results).items())),
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
                "dominant_solver": r["observations"]["seed_dynamics"]["dominant_solver"],
                "pressure_stalls": r["observations"]["seed_dynamics"]["pressure_stalls"],
                "role_positions_held": r["observations"]["seed_dynamics"]["role_positions_held"],
            }
            for r in results
        ],
    }


def render_line(result: dict[str, Any]) -> str:
    obs = result["observations"]
    dyn = obs["seed_dynamics"]
    mark = "✅" if result["status"] == "pass" else "❌"
    failed = [k for k, ok in result["checks"].items() if not ok]
    initializer = "ok" if result["initializer"]["accepted"] else "REJECTED"
    tail = f" — failed: {', '.join(failed)}" if failed else ""
    return (
        f"{mark} {result['card_id']} {result['handle']}: tasks {obs['tasks_completed']}/{obs['task_count']}, "
        f"events {obs['emergent_events']}, stalls {dyn['pressure_stalls']}, solver {dyn['dominant_solver']}, "
        f"L3 {obs['l3_verdict']}, initializer {initializer}{tail}"
    )


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


def _list(manifest: dict[str, Any]) -> int:
    for row in manifest["fixtures"]:
        print(f"{row['card_id']}  {row['fixture_id']}  ({row['fixture_status']})")
    return 0


def _run_root(arg: str | None) -> Path:
    root = Path(arg).resolve() if arg else DEFAULT_RUN_ROOT / datetime.now(timezone.utc).strftime("%Y-%m-%d")
    root.mkdir(parents=True, exist_ok=True)
    return root


def run_suite(rows: list[dict[str, Any]], run_root: Path, mesh: bool) -> list[dict[str, Any]]:
    results = []
    for row in rows:
        result = run_fixture(row, run_root, mesh)
        print(render_line(result))
        results.append(result)
    return results


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = load_manifest()
    if args.list:
        return _list(manifest)
    rows = manifest["fixtures"] if args.all else resolve(args.fixture, manifest)
    run_root = _run_root(args.run_root)
    summary = suite_summary(run_suite(rows, run_root, args.mesh))
    if args.all and not args.no_summary:
        write_json(SUITE_SUMMARY, summary)
    print(
        f"\n{summary['passed']}/{summary['fixture_count']} fixtures passed "
        f"({summary['distinct_run_signatures']} distinct run signatures, L3 {summary['l3_verdicts']}); "
        f"artifacts under {run_root}"
    )
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())

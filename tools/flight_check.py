#!/usr/bin/env python3
"""
flight_check.py — the flight log.

Runs the declared exercises in catalog/flight_contract.yaml against the
LIVE wiring (real app, real engine, real mesh) and records when each module
last flew. Landed-but-never-invoked is the successor failure mode to
stranded-but-never-published; this makes dormancy measurable and the cure
one command.

Usage:
    python3 tools/flight_check.py run               # fly everything; write receipts
    python3 tools/flight_check.py run --only vault  # substring filter
    python3 tools/flight_check.py status            # staleness report; exit 2 if overdue

Receipts: reports/automation/flight_log_latest.json — per-flight status,
last_flown (preserved across failed runs), and output tail.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = REPO_ROOT / "catalog" / "flight_contract.yaml"
LOG_PATH = REPO_ROOT / "reports" / "automation" / "flight_log_latest.json"

FLIGHT_ENV = {"CSRF_SECRET_KEY": "flight-check-secret", "WS_AUTH_SECRET": "flight-check-ws",
              "JWT_SECRET_KEY": "flight-check-jwt-secret-local-only",
              "PYTHONPYCACHEPREFIX": "/tmp/pyc"}  # noqa: S108 - throwaway pycache prefix


def load_contract(root: Path = REPO_ROOT) -> dict:
    sys.path.insert(0, str(root / "tools"))
    from _workspace_common import load_yaml_like

    return load_yaml_like(root / "catalog" / "flight_contract.yaml") or {}


def load_log() -> dict:
    if LOG_PATH.exists():
        try:
            return json.loads(LOG_PATH.read_text())
        except json.JSONDecodeError:
            pass
    return {"flights": {}}


def run_flight(flight: dict, defaults: dict, root: Path) -> dict:
    cwd = root / str(flight.get("cwd", defaults.get("cwd", ".")))
    python = root / str(flight.get("python", defaults.get("python", sys.executable)))
    env = dict(os.environ)
    env.update(FLIGHT_ENV)
    result = subprocess.run(  # noqa: S603 - interpreter + script from the declared flight contract
        [str(python), "-c", str(flight["script"])],
        capture_output=True, text=True, cwd=cwd, env=env, timeout=300,
    )
    ok = result.returncode == 0
    tail = (result.stdout.strip().splitlines() or [""])[-1] if ok else \
           (result.stderr.strip().splitlines() or ["(no output)"])[-1]
    return {"ok": ok, "detail": tail[:200]}


def cmd_run(only: str | None) -> int:
    contract = load_contract()
    defaults = contract.get("defaults", {})
    log = load_log()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    failures = 0
    for flight in contract.get("flights", []):
        name = str(flight["name"])
        if only and only not in name:
            continue
        try:
            outcome = run_flight(flight, defaults, REPO_ROOT)
        except Exception as exc:
            outcome = {"ok": False, "detail": str(exc)[:200]}
        entry = log["flights"].setdefault(name, {})
        entry["status"] = "flown" if outcome["ok"] else "FAILED"
        entry["detail"] = outcome["detail"]
        entry["last_attempt"] = now
        if outcome["ok"]:
            entry["last_flown"] = now
        else:
            failures += 1
        icon = "🛫" if outcome["ok"] else "❌"
        print(f"  {icon} {name}: {outcome['detail']}")
    log["generated_at_utc"] = now
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text(json.dumps(log, indent=2) + "\n")
    print(f"\nFlight log written: {LOG_PATH.relative_to(REPO_ROOT)}")
    return 1 if failures else 0


def overdue_flights(root: Path = REPO_ROOT) -> list[dict]:
    contract = load_contract(root)
    defaults = contract.get("defaults", {})
    log_path = root / "reports" / "automation" / "flight_log_latest.json"
    log = {}
    if log_path.exists():
        try:
            log = json.loads(log_path.read_text())
        except json.JSONDecodeError:
            log = {}
    flights_log = log.get("flights", {})
    now = datetime.now(timezone.utc)
    overdue: list[dict] = []
    for flight in contract.get("flights", []):
        name = str(flight["name"])
        max_age = int(flight.get("max_age_days", defaults.get("max_age_days", 14)))
        entry = flights_log.get(name) or {}
        last = entry.get("last_flown")
        if not last:
            overdue.append({"name": name, "state": "never flown",
                            "fix": f"python3 tools/flight_check.py run --only {name}"})
            continue
        age = (now - datetime.strptime(last, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)).days
        if age > max_age:
            overdue.append({"name": name, "state": f"last flown {age}d ago (max {max_age})",
                            "fix": f"python3 tools/flight_check.py run --only {name}"})
        if entry.get("status") == "FAILED":
            overdue.append({"name": name, "state": f"last attempt FAILED: {entry.get('detail','')[:80]}",
                            "fix": f"python3 tools/flight_check.py run --only {name}"})
    return overdue


def cmd_status() -> int:
    overdue = overdue_flights()
    if not overdue:
        print("Flight log current: every declared module has flown recently.")
        return 0
    print(f"FLIGHT DEBT — {len(overdue)} item(s):")
    for o in overdue:
        print(f"  {o['name']}: {o['state']}")
        print(f"      → {o['fix']}")
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["run", "status"])
    parser.add_argument("--only", help="substring filter on flight names")
    args = parser.parse_args()
    return cmd_run(args.only) if args.command == "run" else cmd_status()


if __name__ == "__main__":
    sys.exit(main())

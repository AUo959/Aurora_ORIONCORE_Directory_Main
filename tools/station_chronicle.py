#!/usr/bin/env python3
"""
station_chronicle.py — the station's persistent history.

Reconstructs everything that has happened aboard Orion Station from canon
and operational sources into a deterministic event ledger (the L2 GUMAS
event-ledger pattern — event atoms, payload hashes, tiered facts — applied
to L1 per the Architecture Contract: state deltas never overwrite L1 facts;
promotion is gated).

Ledger tiers:
    CANON        - reconstructed from CanonRec (mesh transcripts, drift log)
    OPERATIONAL  - real station operations (activation pulse, roll calls, flights)
    STAGING      - simulated hours appended by tools/hour_aboard.py (promotion-gated)

Surfaces:
    CanonRec canon/L1/station/chronicle/STATION_CHRONICLE.ndjson  (CANON+OPERATIONAL)
    catalog/station_chronicle_staging.ndjson                      (STAGING, append-only)
    catalog/station_state.json                                    (derived persistent state)

Usage:
    python3 tools/station_chronicle.py build    # reconstruct the canon ledger
    python3 tools/station_chronicle.py state    # derive station_state.json from both ledgers
    python3 tools/station_chronicle.py status   # counts and heads
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONREC = REPO_ROOT / "GUMAS_SIM_2.5" / "CanonRec"
CHRONICLE_DIR = CANONREC / "canon" / "L1" / "station" / "chronicle"
CHRONICLE_PATH = CHRONICLE_DIR / "STATION_CHRONICLE.ndjson"
STAGING_PATH = REPO_ROOT / "catalog" / "station_chronicle_staging.ndjson"
STATE_PATH = REPO_ROOT / "catalog" / "station_state.json"

TRANSCRIPTS = CANONREC / "canon" / "L1" / "station" / "mesh_transcripts"
DRIFT_LOG = CANONREC / "DRIFT_LOG.md"
AUTOMATION = REPO_ROOT / "reports" / "automation"
SIMULATION_RUNS = REPO_ROOT / "reports" / "simulation"

LEDGER_SCHEMA = "station-chronicle-v1"


def _hash8(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:8]


def atom(occurred_at: str, tier: str, domain: str, kind: str, summary: str,
         participants: list[str], source: str, payload: object = None) -> dict:
    body = {
        "type": "event_atom",
        "ledger": LEDGER_SCHEMA,
        "occurred_at": occurred_at,
        "tier": tier,
        "domain": domain,
        "event_kind": kind,
        "participants": sorted(participants),
        "summary": summary,
        "source": source,
        "payload_hash": _hash8(payload if payload is not None else summary),
    }
    body["event_id"] = f"SCH_{occurred_at[:10]}_{kind}_{_hash8(body)}"
    return body


# ---------------------------------------------------------------- sources

def from_mesh_transcripts() -> list[dict]:
    """March 2026 mesh era — the station's first live days (CANON reference).

    Historical identifiers ("Captain") are preserved verbatim per
    PILOT_ROLE_DEFINITION; the Pilot is the modern form of that voice.
    """
    atoms = []
    for path in sorted(TRANSCRIPTS.glob("*.jsonl")):
        for line in path.read_text().strip().splitlines():
            ev = json.loads(line)
            if ev.get("event_type") not in ("message_accepted", "agent_reply"):
                continue
            payload = ev.get("payload", {})
            who = payload.get("sender_name") or ev.get("agent_id") or "station"
            content = (payload.get("content") or payload.get("detail") or "")[:160]
            atoms.append(atom(
                ev.get("timestamp", "2026-03-08T00:00:00+00:00")[:19] + "Z",
                "CANON", "mesh", ev["event_type"],
                f"{who}: {content}",
                [who] + [t for t in payload.get("targets", [])],
                f"CanonRec canon/L1/station/mesh_transcripts/{path.name}",
                payload,
            ))
    return atoms


def from_drift_log() -> list[dict]:
    """Canon governance decisions recorded in CanonRec DRIFT_LOG."""
    atoms = []
    text = DRIFT_LOG.read_text()
    for m in re.finditer(r"## Drift Entry — (\d{4}-\d{2}-\d{2})\n(.*?)(?=\n## |\Z)", text, re.DOTALL):
        date, body = m.group(1), m.group(2)
        desc = re.search(r"\*\*Description:\*\*(.*?)(?=\n- \*\*|\Z)", body, re.DOTALL)
        ents = re.search(r"\*\*Entities affected:\*\* (.+)", body)
        summary = " ".join((desc.group(1) if desc else body).split())[:200]
        participants = [e.strip() for e in (ents.group(1).split(",") if ents else [])][:6]
        atoms.append(atom(f"{date}T00:00:00Z", "CANON", "governance", "drift_entry",
                          summary, participants, "CanonRec DRIFT_LOG.md"))
    return atoms


def from_operations() -> list[dict]:
    """Real station operations: activation pulse, roll calls, flights."""
    atoms = []
    pulse_path = AUTOMATION / "station_activation_pulse__2026-06-11.json"
    if pulse_path.exists():
        pulse = json.loads(pulse_path.read_text())
        atoms.append(atom(
            pulse.get("timestamp", "2026-06-11T00:00:00Z"), "OPERATIONAL", "operations",
            "activation_pulse",
            f"Activation pulse {pulse.get('encoded', '#808//.')} from the Pilot — "
            f"{pulse.get('answered')}/{pulse.get('of')} answered; "
            f"{pulse.get('souls_aboard')} souls aboard; station {pulse.get('station_status')}",
            ["Pilot"] + [r["agent"] for r in pulse.get("replies", [])],
            f"reports/automation/{pulse_path.name}", pulse,
        ))
    roll_path = AUTOMATION / "station_roll_call_latest.json"
    if roll_path.exists():
        roll = json.loads(roll_path.read_text())
        atoms.append(atom(
            roll.get("generated_at_utc", "2026-06-12T00:00:00Z"), "OPERATIONAL", "operations",
            "roll_call",
            f"Companion roll call — {roll.get('awake')}/{roll.get('of')} awake and answering",
            ["Pilot"] + [m["agent"] for m in roll.get("muster", [])],
            f"reports/automation/{roll_path.name}", roll,
        ))
    flight_path = AUTOMATION / "flight_log_latest.json"
    if flight_path.exists():
        log = json.loads(flight_path.read_text())
        for name, entry in sorted(log.get("flights", {}).items()):
            if entry.get("last_flown"):
                atoms.append(atom(
                    entry["last_flown"], "OPERATIONAL", "operations", "flight",
                    f"Flight '{name}' flown: {entry.get('detail', '')[:120]}",
                    [], f"reports/automation/{flight_path.name}",
                    {"flight": name, "detail": entry.get("detail")},
                ))
    return atoms


def from_simulation_runs() -> list[dict]:
    """Simulated hours aboard (STAGING tier — promotion-gated candidate canon)."""
    atoms = []
    for run_dir in sorted(SIMULATION_RUNS.glob("*__*")):
        raw_path = run_dir / "sim_raw.json"
        if not raw_path.exists():
            continue
        sim = json.loads(raw_path.read_text())
        stamp = run_dir.name.split("__")[-1] + "T12:00:00Z"
        scenario = run_dir.name.split("__")[0]
        s = sim["summary"]
        names = sim.get("task_names", {})
        run_anchor = {
            "schema_version": LEDGER_SCHEMA, "scenario_id": scenario,
            "ticks": s.get("ticks"), "completed_ids": s.get("completed_ids", []),
        }
        atoms.append(atom(stamp, "STAGING", "simulation", "watch_block_run",
                          f"Simulated {s.get('ticks')}h aboard ({scenario}): "
                          f"{len(s.get('completed_ids', []))} tasks completed, "
                          f"{s.get('total_spent')}h worked by {s.get('characters_used')} crew",
                          [], f"reports/simulation/{run_dir.name}/sim_raw.json", run_anchor))
        for ev in sim.get("events", []):
            atoms.append(atom(stamp, "STAGING", "simulation", f"emergent_{ev['kind']}",
                              ev["description"][:160], ev.get("affected", []),
                              f"reports/simulation/{run_dir.name}/sim_raw.json", ev))
        for rec in sim.get("work_records", []):
            if "COMPLETE" in rec.get("note", ""):
                atoms.append(atom(stamp, "STAGING", "simulation", "task_completed",
                                  f"{rec['agent']} completed {names.get(rec['task'], rec['task'])}",
                                  [rec["agent"]],
                                  f"reports/simulation/{run_dir.name}/sim_raw.json", rec))
    return atoms


# ---------------------------------------------------------------- commands

def cmd_build() -> int:
    atoms = from_mesh_transcripts() + from_drift_log() + from_operations()
    atoms.sort(key=lambda a: a["occurred_at"])
    CHRONICLE_DIR.mkdir(parents=True, exist_ok=True)
    CHRONICLE_PATH.write_text("\n".join(json.dumps(a, sort_keys=True) for a in atoms) + "\n")
    tiers = defaultdict(int)
    for a in atoms:
        tiers[a["tier"]] += 1
    print(f"Chronicle reconstructed: {len(atoms)} event atoms "
          f"({', '.join(f'{k} {v}' for k, v in sorted(tiers.items()))})")
    print(f"  → {CHRONICLE_PATH.relative_to(REPO_ROOT)}")
    return 0


def load_all_atoms() -> list[dict]:
    atoms = []
    for path in (CHRONICLE_PATH, STAGING_PATH):
        if path.exists():
            for line in path.read_text().strip().splitlines():
                if line:
                    atoms.append(json.loads(line))
    # staging regeneration source: simulation runs not yet in the staging ledger
    known = {a["event_id"] for a in atoms}
    for a in from_simulation_runs():
        if a["event_id"] not in known:
            atoms.append(a)
    return sorted(atoms, key=lambda a: a["occurred_at"])


def cmd_state() -> int:
    atoms = load_all_atoms()
    familiarity: dict[str, float] = defaultdict(float)
    experience: dict[str, float] = defaultdict(float)
    completed: dict[str, list[str]] = defaultdict(list)

    for a in atoms:
        people = [p for p in a["participants"] if p and p not in ("station",)]
        if a["event_kind"].startswith("emergent_") and len(people) == 2:
            familiarity["|".join(sorted(people))] += 1.0
        if a["event_kind"] == "task_completed" and people:
            experience[people[0]] += 1.0
        if a["event_kind"] == "watch_block_run":
            run = a.get("summary", "")
            scenario = a["source"].split("/")[-2].split("__")[0] if "/" in a["source"] else run
            completed[scenario] = sorted(set(completed[scenario]))
    # co-work familiarity from raw sim records (hours shared per pair)
    for run_dir in sorted(SIMULATION_RUNS.glob("*__*")):
        raw = run_dir / "sim_raw.json"
        if not raw.exists():
            continue
        sim = json.loads(raw.read_text())
        by_tick_task = defaultdict(set)
        for rec in sim.get("work_records", []):
            by_tick_task[(rec["tick"], rec["task"])].add(rec["agent"])
        for crew in by_tick_task.values():
            crew = sorted(crew)
            for i, x in enumerate(crew):
                for y in crew[i + 1:]:
                    familiarity[f"{x}|{y}"] += 0.5
        for tid in sim["summary"].get("completed_ids", []):
            scenario = run_dir.name.split("__")[0]
            if tid not in completed[scenario]:
                completed[scenario].append(tid)

    state = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ledger_schema": LEDGER_SCHEMA,
        "atoms_total": len(atoms),
        "atoms_by_tier": dict(sorted(
            defaultdict(int, {t: sum(1 for a in atoms if a["tier"] == t)
                              for t in {a["tier"] for a in atoms}}).items())),
        "chronicle_head": _hash8([a["event_id"] for a in atoms]),
        "pair_familiarity": dict(sorted(familiarity.items(), key=lambda kv: -kv[1])),
        "crew_experience_completions": dict(sorted(experience.items(), key=lambda kv: -kv[1])),
        "scenario_completed_tasks": {k: sorted(v) for k, v in completed.items()},
    }
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n")
    print(f"Station state derived: {state['atoms_total']} atoms → "
          f"{len(state['pair_familiarity'])} familiar pairs, "
          f"{len(state['crew_experience_completions'])} crew with completions")
    print(f"  → {STATE_PATH.relative_to(REPO_ROOT)}")
    return 0


def cmd_status() -> int:
    atoms = load_all_atoms()
    tiers = defaultdict(int)
    domains = defaultdict(int)
    for a in atoms:
        tiers[a["tier"]] += 1
        domains[a["domain"]] += 1
    span = (atoms[0]["occurred_at"][:10], atoms[-1]["occurred_at"][:10]) if atoms else ("-", "-")
    print(f"Station chronicle: {len(atoms)} atoms, {span[0]} → {span[1]}")
    print(f"  tiers:   {dict(sorted(tiers.items()))}")
    print(f"  domains: {dict(sorted(domains.items()))}")
    print(f"  state:   {'present' if STATE_PATH.exists() else 'NOT DERIVED (run: state)'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["build", "state", "status"])
    args = parser.parse_args()
    return {"build": cmd_build, "state": cmd_state, "status": cmd_status}[args.command]()


if __name__ == "__main__":
    sys.exit(main())

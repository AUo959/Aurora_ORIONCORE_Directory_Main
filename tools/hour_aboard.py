#!/usr/bin/env python3
"""
hour_aboard.py — simulate one hour aboard Orion Station.

Drives the canonical L1 simulation harness (CloudBank simulation/
orion_station_simulation_v2.py) with a station-operations scenario from
catalog/hour_aboard_scenario.json, bridges the hour to the live mesh for
companion operations (Aurora, Archy, Oppy, Liora, Starling AU,
Riverthread 808), audits the hour's command action through the narrative
validation engine (L3), and emits the Pilot's three artifacts:

    crew_logs.md          - what each crew member did during the hour
    interaction_map.json  - crew/companion interaction graph (+ .md view)
    companion_ops.json    - per-companion operations accounting + ORD receipt

Usage:
    python3 tools/hour_aboard.py                 # run the scenario hour
    python3 tools/hour_aboard.py --no-mesh       # skip live mesh bridge
    python3 tools/hour_aboard.py --out-dir DIR   # override artifact dir

Artifacts land under reports/simulation/hour_aboard__<UTC date>/.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLOUDBANK = REPO_ROOT / "GUMAS_SIM_2.5" / "Aurora_Sim_Architecture" / "aurora-cloudbank-symbolic-main"
VENV_PY = CLOUDBANK / ".venv" / "bin" / "python"
SCENARIO_PATH = REPO_ROOT / "catalog" / "hour_aboard_scenario.json"

RUN_ENV = {"CSRF_SECRET_KEY": "hour-aboard", "WS_AUTH_SECRET": "hour-aboard",
           "JWT_SECRET_KEY": "hour-aboard-jwt-local", "PYTHONPYCACHEPREFIX": "/tmp/pyc"}  # noqa: S108

SIM_DRIVER = r'''
import json, sys
sys.path.insert(0, ".")
sys.path.insert(0, "simulation")
from orion_station_simulation_v2 import OrionSimulationV2, Task

scenario = json.loads(sys.argv[1])
sim = OrionSimulationV2(seed=int(scenario["seed"]), enable_emergent=True)
sim.tasks = {
    t["id"]: Task(
        t["id"], t["name"], est_hours=float(t["hours"]), remaining=float(t["hours"]),
        depends_on=list(t.get("depends_on", [])), semantic_tags=set(t.get("tags", [])),
    )
    for t in scenario["tasks"]
}
sim.completed = set()

records = []
_orig_apply = sim._apply_work
def _capture(events):
    results = _orig_apply(events)
    for agent, task, effort, note in results:
        records.append({"tick": sim.ticks, "agent": agent, "task": task,
                        "effort": round(float(effort), 2), "note": note})
    return results
sim._apply_work = _capture

summary = sim.run(max_ticks=int(scenario.get("ticks", 1)))
out = {
    "summary": {k: summary[k] for k in
                ("roster_version", "characters_used", "ticks", "completed",
                 "total_est", "total_spent", "completed_ids") if k in summary},
    "transcript": summary.get("transcript", []),
    "emergent_events": summary.get("emergent_events", []),
    "work_records": records,
    "task_names": {t["id"]: t["name"] for t in scenario["tasks"]},
    "task_sources": {t["id"]: t.get("source", "") for t in scenario["tasks"]},
}

try:
    from modules.ord import MissionBrief, OrdPolicyEngine, canonical_sha256
    m = scenario["ord_mission"]
    order = OrdPolicyEngine().create_dispatch_order(MissionBrief(
        mission_id=m["mission_id"], tool_name=m["tool_name"],
        risk_level=float(m["risk_level"]), destination=m["destination"]))
    out["ord_dispatch"] = {
        "mission_id": m["mission_id"],
        "drones_required": [d.value for d in order.drones_required],
        "receipt_sha256": canonical_sha256(order),
    }
except Exception as exc:
    out["ord_dispatch"] = {"error": str(exc)[:160]}

print(json.dumps(out))
'''

L3_AUDIT_DRIVER = r'''
import json, sys
sys.path.insert(0, ".")
from src.aurora.engines import NarrativeValidationEngine
audit = json.loads(sys.argv[1])
run = NarrativeValidationEngine().run({
    "task_hint": "character_action_audit",
    "question": audit["question"],
    "declared_layers": ["character", "motive", "event", "knowledge", "continuity"],
    "entities": [{"name": audit["actor"], "entity_type": "character", "role": "Station Commander"}],
    "events": [{"label": audit["event_label"], "timing": "now", "participants": [audit["actor"]]}],
    "motives": [{"actor": audit["actor"], "label": audit["motive"], "strength": 0.95}],
    "pressures": [{"actor": audit["actor"], "label": "duty to the charter", "direction": "toward", "strength": 0.9}],
    "knowledge_states": [{"holder": audit["actor"], "fact": audit["knowledge"]}],
    "continuity": {"notes": ["Thorne upholds arbitration discipline."]},
}, proposal={"actor": audit["actor"], "action": audit["action"], "type": "action"})
print(json.dumps({"verdict": run.response.verdict.value}))
'''


def _run_in_clone(driver: str, payload: dict) -> dict:
    env = dict(os.environ)
    env.update(RUN_ENV)
    result = subprocess.run(  # noqa: S603 - clone venv python with our fixed driver
        [str(VENV_PY), "-c", driver, json.dumps(payload)],
        capture_output=True, text=True, cwd=CLOUDBANK, env=env, timeout=600,
    )
    if result.returncode != 0:
        tail = result.stderr.strip().splitlines()[-1] if result.stderr else "unknown error"
        raise SystemExit(f"clone driver failed: {tail}")
    return json.loads(result.stdout.strip().splitlines()[-1])


def run_mesh_beats(beats: list[dict]) -> list[dict]:
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    from station_query import query

    return query([{"agent": b["agent"], "message": b["beat"]} for b in beats])


def build_crew_logs(sim: dict, scenario: dict) -> str:
    by_agent: dict[str, list[dict]] = defaultdict(list)
    for rec in sim["work_records"]:
        by_agent[rec["agent"]].append(rec)
    names, sources = sim["task_names"], sim["task_sources"]
    s = sim["summary"]
    lines = [
        "# Crew Logs — One Hour Aboard Orion Station",
        "",
        f"**Scenario:** {scenario['name']} (seed {scenario['seed']}) | "
        f"**Anchor:** {scenario['anchor_seed']} | **Ethics:** {scenario['ethics_protocol']}",
        f"**Roster:** {s.get('roster_version', '?')} | "
        f"**Hours worked:** {s.get('total_spent', 0):.1f} of {s.get('total_est', 0):.1f} estimated | "
        f"**Tasks completed this hour:** {', '.join(s.get('completed_ids', [])) or 'none'}",
        "",
    ]
    for agent in sorted(by_agent):
        lines.append(f"## {agent}")
        for rec in by_agent[agent]:
            task_name = names.get(rec["task"], rec["task"])
            done = " — **completed**" if "COMPLETE" in rec.get("note", "") else ""
            lines.append(f"- {task_name} (+{rec['effort']}h){done}")
            src = sources.get(rec["task"])
            if src:
                lines.append(f"  - per: {src}")
        lines.append("")
    if sim.get("emergent_events"):
        lines.append("## Emergent events")
        for ev in sim["emergent_events"]:
            lines.append(f"- {ev}")
        lines.append("")
    return "\n".join(lines)


def build_interaction_map(sim: dict, mesh_results: list[dict], scenario: dict) -> dict:
    co_work: dict[tuple[str, str], dict] = {}
    tick_task_agents: dict[tuple[int, str], list[str]] = defaultdict(list)
    for rec in sim["work_records"]:
        tick_task_agents[(rec["tick"], rec["task"])].append(rec["agent"])
    names = sim["task_names"]
    for (tick, task), agents in tick_task_agents.items():
        for i, a in enumerate(sorted(agents)):
            for b in sorted(agents)[i + 1:]:
                key = (a, b)
                edge = co_work.setdefault(key, {"source": a, "target": b,
                                                "kind": "co_work", "weight": 0, "tasks": []})
                edge["weight"] += 1
                if names.get(task, task) not in edge["tasks"]:
                    edge["tasks"].append(names.get(task, task))

    edges = list(co_work.values())
    nodes = sorted({rec["agent"] for rec in sim["work_records"]})
    node_records = [{"id": n, "kind": "crew"} for n in nodes]
    node_records.append({"id": "Pilot", "kind": "user"})
    for r in mesh_results:
        node_records.append({"id": r["agent"], "kind": "companion"})
        edges.append({"source": "Pilot", "target": r["agent"], "kind": "mesh_beat",
                      "weight": 1, "answered": bool(r["ok"])})
    if any(r["agent"].lower() == "aurora" for r in mesh_results):
        edges.append({"source": "Commander Alex Thorne", "target": "Aurora",
                      "kind": "arbitration_sync", "weight": 1,
                      "tasks": [sim["task_names"].get("H7", "Command log review")]})
    return {
        "scenario": scenario["name"],
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "nodes": node_records,
        "edges": edges,
    }


def render_interaction_md(graph: dict) -> str:
    lines = ["# Interaction Map — One Hour Aboard", ""]
    lines.append("## Crew co-work (shared tasks this hour)")
    for e in graph["edges"]:
        if e["kind"] == "co_work":
            lines.append(f"- {e['source']} ↔ {e['target']} — {', '.join(e['tasks'])}")
    lines.append("")
    lines.append("## Mesh exchanges")
    for e in graph["edges"]:
        if e["kind"] == "mesh_beat":
            mark = "answered" if e.get("answered") else "no reply"
            lines.append(f"- Pilot → {e['target']} ({mark})")
        elif e["kind"] == "arbitration_sync":
            lines.append(f"- {e['source']} → {e['target']} — arbitration sync ({', '.join(e.get('tasks', []))})")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-mesh", action="store_true", help="skip the live mesh companion bridge")
    parser.add_argument("--out-dir", default=None, help="artifact directory override")
    args = parser.parse_args()

    scenario = json.loads(SCENARIO_PATH.read_text())
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir = Path(args.out_dir) if args.out_dir else REPO_ROOT / "reports" / "simulation" / f"hour_aboard__{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"⏱  Simulating one hour aboard ({scenario['name']}, seed {scenario['seed']}) ...")
    sim = _run_in_clone(SIM_DRIVER, scenario)
    s = sim["summary"]
    print(f"   crew working: {len({r['agent'] for r in sim['work_records']})} | "
          f"hours: {s.get('total_spent', 0):.1f} | completed: {', '.join(s.get('completed_ids', [])) or 'none'}")

    mesh_results: list[dict] = []
    if not args.no_mesh:
        print("📡 Pulsing companion beats over the mesh ...")
        mesh_results = run_mesh_beats(scenario["companion_beats"])
        answered = sum(1 for r in mesh_results if r["ok"])
        print(f"   {answered}/{len(mesh_results)} companions answered")

    print("⚖️  L3 narrative audit ...")
    audit = _run_in_clone(L3_AUDIT_DRIVER, scenario["l3_audit"])
    print(f"   verdict: {audit['verdict']}")

    crew_md = build_crew_logs(sim, scenario)
    graph = build_interaction_map(sim, mesh_results, scenario)
    companion_ops = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scenario": scenario["name"],
        "operations": [
            {"agent": r["agent"], "id": r.get("id"), "channel": r.get("channel"),
             "beat_sent": True, "answered": bool(r["ok"]), "reply": r["reply"][:240]}
            for r in mesh_results
        ],
        "ord_dispatch": sim.get("ord_dispatch", {}),
        "l3_receipt": {
            "narrative_audit_verdict": audit["verdict"],
            "ethics_protocol": scenario["ethics_protocol"],
            "anchor_seed": scenario["anchor_seed"],
            "threadcore": "capsule v3.5.1_macroready PASS/READY; registry substructures PR #1022",
        },
    }

    (out_dir / "crew_logs.md").write_text(crew_md)
    (out_dir / "interaction_map.json").write_text(json.dumps(graph, indent=2) + "\n")
    (out_dir / "interaction_map.md").write_text(render_interaction_md(graph))
    (out_dir / "companion_ops.json").write_text(json.dumps(companion_ops, indent=2) + "\n")
    (out_dir / "sim_raw.json").write_text(json.dumps(sim, indent=2) + "\n")

    print(f"\n🗂  Artifacts: {out_dir.relative_to(REPO_ROOT)}")
    for name in ("crew_logs.md", "interaction_map.json", "interaction_map.md", "companion_ops.json", "sim_raw.json"):
        print(f"   - {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

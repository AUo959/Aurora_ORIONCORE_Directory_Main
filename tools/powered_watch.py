#!/usr/bin/env python3
"""
powered_watch.py — the L2 join: the station chassis operates the GUMAS engine.

One subprocess hosts both layers in-process and couples them bidirectionally,
hour by hour, under the Architecture Contract (state deltas only; the engine
never overwrites L1 facts; everything downlinks as receipts):

    chassis → engine   completing engine-servicing tasks (quantum, systems,
                       monitoring, communication) raises engine throughput:
                       base turns/hour + 1 per servicing completion
    engine  → chassis  notable engine events (civil wars, insurgencies,
                       fragmentation) inject analysis tasks onto the next
                       hour's station board
    engine  → history  engine turns become STAGING chronicle atoms (domain
                       "engine") with a deterministic run anchor

Reuses the hour_aboard artifact builders, adds engine_telemetry.json (the
downlink packet), and refreshes persistent station state afterward.

Usage:
    python3 tools/powered_watch.py                        # powered_watch_v1
    python3 tools/powered_watch.py --no-mesh
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(REPO_ROOT / "tools"))
import hour_aboard  # noqa: E402  (artifact builders + clone runner)
from station_chronicle import LEDGER_SCHEMA, STAGING_PATH, atom  # noqa: E402

POWERED_DRIVER = r'''
import json, sys
sys.path.insert(0, ".")
sys.path.insert(0, "simulation")

scenario = json.loads(sys.argv[1])
engine_dir = scenario["engine_ops"]["_engine_dir_abs"]
sys.path.insert(0, engine_dir)

from orion_station_simulation_v2 import OrionSimulationV2, Task, Agent
from engine_advanced import GUMASAdvancedEngine

# --- chassis (L1) -----------------------------------------------------------
sim = OrionSimulationV2(seed=int(scenario["seed"]), enable_emergent=True)
agents, divisions = {}, {}
for char in sim.char_loader.get_all_characters():
    focus = sim.char_loader.get_focus_keywords(char)
    collab = {c.split("(")[0].strip() for c in char.key_collaborators}
    agents[char.name] = Agent(
        name=char.name, role=char.role, character_id=char.character_id,
        base_speed=char.base_speed,
        specialization_multiplier=char.specialization_multiplier,
        collaboration_bonus=char.collaboration_bonus,
        focus_keywords=focus, collaborators=collab,
    )
    divisions[char.name] = char.division
sim.agents = agents

# Keyed by NAME: the harness records task name (not id) in work_records.
task_tags = {t["name"]: set(t.get("tags", [])) for t in scenario["tasks"]}
sim.tasks = {
    t["id"]: Task(
        t["id"], t["name"], est_hours=float(t["hours"]), remaining=float(t["hours"]),
        depends_on=list(t.get("depends_on", [])), semantic_tags=set(t.get("tags", [])),
    )
    for t in scenario["tasks"]
}
sim.completed = set()

history_pairs_applied = 0
for pair, weight in scenario.get("history", {}).get("pair_familiarity", {}).items():
    if float(weight) >= 1.0:
        a, b = pair.split("|", 1)
        if a in sim.agents and b in sim.agents:
            sim.agents[a].collaborators.add(b)
            sim.agents[b].collaborators.add(a)
            history_pairs_applied += 1

records = []
_orig_apply = sim._apply_work
def _capture(events):
    results = _orig_apply(events)
    for agent, task, effort, note in results:
        records.append({"tick": sim.ticks, "agent": agent, "task": task,
                        "effort": round(float(effort), 2), "note": note})
    return results
sim._apply_work = _capture

# --- engine (L2) ------------------------------------------------------------
ops = scenario["engine_ops"]
engine = GUMASAdvancedEngine(seed=int(scenario["seed"]))
init_state = engine.init_scenario()
engine_log, injected_tasks = [], []
service_tags = set(ops["service_tags"])
notable_kinds = list(ops["feedback"]["notable_kinds"])

ticks = int(scenario.get("ticks", 1))
for hour in range(ticks):
    sim.tick()
    completions = [r["task"] for r in records
                   if r["tick"] == hour and "COMPLETE" in r.get("note", "")]
    service_done = [t for t in completions if service_tags & task_tags.get(t, set())]
    turns = min(int(ops["base_turns_per_hour"]) + len(service_done),
                int(ops["max_turns_per_hour"]))
    results = engine.run(turns)
    notable_total = 0
    for res in results:
        d = res.to_dict()
        v3 = d["v3_result"]
        notable = {k: v3.get(k, 0) for k in notable_kinds if v3.get(k, 0)}
        notable_total += sum(notable.values())
        engine_log.append({
            "hour": hour + 1, "turn": d["turn"],
            "stability_index": d["stability_index"], "risk_index": d["risk_index"],
            "summary": d["summary"], "notable": notable,
            "tech_breakthroughs": v3.get("tech_breakthroughs", 0),
            "negotiations_concluded": v3.get("negotiations_concluded", 0),
        })
    # engine → chassis: notable activity becomes next hour's analysis work
    if notable_total and hour + 1 < ticks:
        tid = f"E{hour + 1}"
        name = (f"Analysis cell: review engine turn telemetry "
                f"(hour {hour + 1}: {notable_total} notable event(s))")
        sim.tasks[tid] = Task(tid, name,
                              est_hours=float(ops["feedback"]["injected_task_hours"]),
                              remaining=float(ops["feedback"]["injected_task_hours"]),
                              depends_on=[],
                              semantic_tags=set(ops["feedback"]["injected_task_tags"]))
        injected_tasks.append({"id": tid, "name": name, "hour_injected": hour + 1})

task_names = {t["id"]: t["name"] for t in scenario["tasks"]}
task_names.update({t["id"]: t["name"] for t in injected_tasks})
total_est = sum(t.est_hours for t in sim.tasks.values())
total_spent = sum(t.est_hours - t.remaining for t in sim.tasks.values())
out = {
    "summary": {
        "roster_version": sim.char_loader.version,
        "characters_used": len(sim.agents),
        "ticks": sim.ticks,
        "completed": all(t.completed for t in sim.tasks.values()),
        "total_est": total_est,
        "total_spent": round(total_spent, 2),
        "completed_ids": sorted(sim.completed),
    },
    "transcript": sim.transcript,
    "events": [
        {"tick": e.tick, "kind": e.kind, "description": e.description,
         "multiplier": e.multiplier, "affected": list(e.affected_agents)}
        for e in sim.aurora.events
    ],
    "work_records": records,
    "roster": [{"name": a.name, "role": a.role, "division": divisions.get(a.name, "")}
               for a in sim.agents.values()],
    "task_names": task_names,
    "task_sources": {t["id"]: t.get("source", "") for t in scenario["tasks"]},
    "history_pairs_applied": history_pairs_applied,
    "engine": {
        "engine_class": type(engine).__name__,
        "factions": len(init_state.factions),
        "leaders": len(init_state.leaders),
        "turns_total": len(engine_log),
        "final_stability": engine_log[-1]["stability_index"] if engine_log else None,
        "final_risk": engine_log[-1]["risk_index"] if engine_log else None,
        "log": engine_log,
        "injected_tasks": injected_tasks,
    },
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


def append_engine_atoms(sim: dict, scenario: dict, stamp: str) -> int:
    """Engine telemetry becomes STAGING chronicle atoms (domain: engine)."""
    run_anchor = {
        "schema_version": LEDGER_SCHEMA,
        "scenario_id": scenario["name"],
        "seed": scenario["seed"],
        "engine_class": sim["engine"]["engine_class"],
        "turns": sim["engine"]["turns_total"],
    }
    atoms = [atom(f"{stamp}T12:00:00Z", "STAGING", "engine", "powered_watch_run",
                  f"Chassis ran the {sim['engine']['engine_class']} for "
                  f"{sim['engine']['turns_total']} turns across {sim['summary']['ticks']}h: "
                  f"stability {sim['engine']['final_stability']}, "
                  f"risk {sim['engine']['final_risk']}",
                  [], f"reports/simulation/{scenario['name']}__{stamp}/engine_telemetry.json",
                  run_anchor)]
    for entry in sim["engine"]["log"]:
        if entry["notable"]:
            kinds = ", ".join(f"{k}×{v}" for k, v in entry["notable"].items())
            atoms.append(atom(f"{stamp}T12:00:00Z", "STAGING", "engine", "engine_notable_turn",
                              f"Engine turn {entry['turn']} (watch hour {entry['hour']}): {kinds} — "
                              f"{entry['summary'][:100]}",
                              [], f"reports/simulation/{scenario['name']}__{stamp}/engine_telemetry.json",
                              entry))
    # Idempotent append: engine atoms are content-addressed (event_id), so a
    # re-run on the same day must not duplicate them in the ledger.
    existing = set()
    if STAGING_PATH.exists():
        for line in STAGING_PATH.read_text().splitlines():
            if line.strip():
                existing.add(json.loads(line)["event_id"])
    new = [a for a in atoms if a["event_id"] not in existing]
    with STAGING_PATH.open("a") as fh:
        for a in new:
            fh.write(json.dumps(a, sort_keys=True) + "\n")
    return len(new)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", default="powered_watch_scenario")
    parser.add_argument("--no-mesh", action="store_true")
    args = parser.parse_args()

    scenario_path = REPO_ROOT / "catalog" / f"{args.scenario.removesuffix('.json')}.json"
    scenario = json.loads(scenario_path.read_text())
    scenario["engine_ops"]["_engine_dir_abs"] = str(REPO_ROOT / scenario["engine_ops"]["engine_dir"])

    state_path = REPO_ROOT / "catalog" / "station_state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text())
        scenario["history"] = {"pair_familiarity": state.get("pair_familiarity", {})}
        print(f"📜 Station history loaded: {state.get('atoms_total', 0)} chronicle atoms")

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir = REPO_ROOT / "reports" / "simulation" / f"{scenario['name']}__{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    hours = scenario.get("ticks", 1)
    print(f"⚡ Powered watch: {hours}h aboard, chassis operating the engine "
          f"(seed {scenario['seed']}) ...")
    sim = hour_aboard._run_in_clone(POWERED_DRIVER, scenario)
    s, eng = sim["summary"], sim["engine"]
    print(f"   chassis: {s['characters_used']} crew | {s['total_spent']:.1f}h worked | "
          f"{len(s['completed_ids'])}/{len(sim['task_names'])} tasks | "
          f"{len(sim.get('events', []))} emergent | history pairs {sim.get('history_pairs_applied', 0)}")
    print(f"   engine:  {eng['engine_class']} | {eng['factions']} factions, {eng['leaders']} leaders | "
          f"{eng['turns_total']} turns | stability {eng['final_stability']} | risk {eng['final_risk']}")
    if eng["injected_tasks"]:
        for t in eng["injected_tasks"]:
            print(f"   ↩ engine→chassis: {t['name']}")

    canon_souls = hour_aboard.load_canon_souls()
    hour_records = hour_aboard.build_hour_records(sim, scenario, canon_souls)

    mesh_results: list[dict] = []
    if not args.no_mesh:
        print("📡 Downlink: pulsing companions with chassis + engine status per hour ...")
        for entry in sim["engine"]["log"]:
            pass  # highlights below carry engine state via hour summaries
        mesh_results = hour_aboard.run_mesh_hours(sim, scenario)
        print(f"   {sum(1 for r in mesh_results if r['ok'])}/{len(mesh_results)} beats answered")

    print("⚖️  L3 narrative audit ...")
    audit = hour_aboard._run_in_clone(hour_aboard.L3_AUDIT_DRIVER, scenario["l3_audit"])
    print(f"   verdict: {audit['verdict']}")

    graph = hour_aboard.build_interaction_map(sim, mesh_results, scenario)
    companion_ops = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scenario": scenario["name"],
        "operations": [
            {"hour": r.get("hour"), "agent": r["agent"], "answered": bool(r["ok"]),
             "reply": r["reply"][:240]} for r in mesh_results
        ],
        "ord_dispatch": sim.get("ord_dispatch", {}),
        "l3_receipt": {
            "narrative_audit_verdict": audit["verdict"],
            "ethics_protocol": scenario["ethics_protocol"],
            "anchor_seed": scenario["anchor_seed"],
            "engine_oversight": f"{eng['turns_total']} engine turns under chassis control; "
                                f"final stability {eng['final_stability']}, risk {eng['final_risk']}",
        },
    }
    souls = hour_aboard.build_souls_accounting(hour_records, mesh_results, canon_souls)

    (out_dir / "crew_logs.md").write_text(hour_aboard.build_crew_logs(hour_records, sim, scenario))
    (out_dir / "interaction_map.json").write_text(json.dumps(graph, indent=2) + "\n")
    (out_dir / "interaction_map.md").write_text(hour_aboard.render_interaction_md(graph))
    (out_dir / "companion_ops.json").write_text(json.dumps(companion_ops, indent=2) + "\n")
    (out_dir / "souls_accounting.json").write_text(json.dumps(souls, indent=2) + "\n")
    (out_dir / "engine_telemetry.json").write_text(json.dumps(sim["engine"], indent=2) + "\n")
    (out_dir / "sim_raw.json").write_text(json.dumps(sim, indent=2) + "\n")

    n_atoms = append_engine_atoms(sim, scenario, stamp)
    print(f"\n🗂  Artifacts: {out_dir.relative_to(REPO_ROOT)} (+ engine_telemetry.json)")
    print(f"   souls accounted: {souls['crew_logged']}/{souls['canon_l1_entities']} "
          f"{'✅' if souls['complete'] else '⚠️'} | engine atoms staged: {n_atoms}")

    subprocess.run(  # noqa: S603 - our own tool with a fixed argument
        [sys.executable, str(REPO_ROOT / "tools" / "station_chronicle.py"), "state"],
        cwd=REPO_ROOT, check=False,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

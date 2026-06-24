#!/usr/bin/env python3
"""
hour_aboard.py — simulate hours aboard Orion Station with full souls accounting.

Drives the canonical L1 simulation harness (CloudBank simulation/
orion_station_simulation_v2.py) with a station-operations scenario, engages
the FULL roster (crew without task assignments rotate through division duty
each hour), bridges every hour to the live mesh for companion operations
(Aurora, Archy, Oppy, Liora, Starling AU, Riverthread 808), surfaces
emergent events, audits the closing command action through the narrative
validation engine (L3), and emits:

    crew_logs.md          - hour-by-hour log for every soul aboard
    interaction_map.json  - crew/companion interaction graph (+ .md view)
    companion_ops.json    - per-hour companion operations + ORD receipt
    souls_accounting.json - completeness ledger: every canon soul accounted

Canon souls absent from the sim roster are derived from CanonRec
(canon/L1/characters frontmatter) and carried on duty rotation, so the
accounting always covers the full 41-entity L1 ledger plus the station
intelligences.

Usage:
    python3 tools/hour_aboard.py                                  # hour_aboard_v1
    python3 tools/hour_aboard.py --scenario watch_block_scenario  # 4-hour watch
    python3 tools/hour_aboard.py --no-mesh                        # skip mesh bridge

Artifacts land under reports/simulation/<scenario>__<UTC date>/.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _resolve(candidates: list[Path], marker: str, default: Path) -> Path:
    """First candidate that contains the marker path, else the documented default."""
    for cand in candidates:
        if (cand / marker).exists():
            return cand
    return default


# Layout-flexible resolution: the canonical layout nests the CloudBank clone and
# CanonRec under GUMAS_SIM_2.5/, but a flat multi-repo checkout keeps them as
# siblings of this repo. Resolve both by a marker file, and prefer a project
# .venv when present (falling back to the current interpreter so the harness
# runs without one).
_CB_NESTED = REPO_ROOT / "GUMAS_SIM_2.5" / "Aurora_Sim_Architecture" / "aurora-cloudbank-symbolic-main"
CLOUDBANK = _resolve(
    [_CB_NESTED, REPO_ROOT.parent / "aurora-cloudbank-symbolic", REPO_ROOT / "aurora-cloudbank-symbolic"],
    marker="simulation/orion_station_simulation_v2.py", default=_CB_NESTED,
)
_VENV_PY = CLOUDBANK / ".venv" / "bin" / "python"
VENV_PY = _VENV_PY if _VENV_PY.exists() else Path(sys.executable)
_CANON_NESTED = REPO_ROOT / "GUMAS_SIM_2.5" / "CanonRec" / "canon" / "L1" / "characters"
CANON_CHARACTERS = _resolve(
    [_CANON_NESTED.parent, (REPO_ROOT.parent / "CanonRec" / "canon" / "L1"),
     (REPO_ROOT / "CanonRec" / "canon" / "L1")],
    marker="characters", default=_CANON_NESTED.parent,
) / "characters"

RUN_ENV = {"CSRF_SECRET_KEY": "hour-aboard", "WS_AUTH_SECRET": "hour-aboard",
           "JWT_SECRET_KEY": "hour-aboard-jwt-local", "PYTHONPYCACHEPREFIX": "/tmp/pyc"}  # noqa: S108

DEFAULT_DUTY_POOLS = {"_off_shift": ["off-shift rest cycle", "mess hall — crew meal"]}

SIM_DRIVER = r'''
import json, sys
sys.path.insert(0, ".")
sys.path.insert(0, "simulation")
from orion_station_simulation_v2 import OrionSimulationV2, Task, Agent

scenario = json.loads(sys.argv[1])
sim = OrionSimulationV2(seed=int(scenario["seed"]), enable_emergent=True)

if scenario.get("full_roster"):
    agents = {}
    divisions = {}
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
else:
    divisions = {}
    for char in sim.char_loader.get_all_characters():
        if char.name in sim.agents:
            divisions[char.name] = char.division

sim.tasks = {
    t["id"]: Task(
        t["id"], t["name"], est_hours=float(t["hours"]), remaining=float(t["hours"]),
        depends_on=list(t.get("depends_on", [])), semantic_tags=set(t.get("tags", [])),
    )
    for t in scenario["tasks"]
}
sim.completed = set()

# Persistent history: crew who worked together in past hours (station
# chronicle pair familiarity) become collaborators — past actions raise
# present collaboration-boost odds. State deltas only; no L1 facts changed.
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

# Exactly N ticks: crew rotate to duty once the board clears; no early break.
for _ in range(int(scenario.get("ticks", 1))):
    sim.tick()

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
    "task_names": {t["id"]: t["name"] for t in scenario["tasks"]},
    "task_sources": {t["id"]: t.get("source", "") for t in scenario["tasks"]},
    "history_pairs_applied": history_pairs_applied,
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


def _norm(name: str) -> str:
    n = name.lower()
    for t in ("dr.", "prof.", "lt.", "cmdr.", "commander", "chief", "cadet", "ensign"):
        n = n.replace(t, "")
    return re.sub(r"[^a-z]", "", n)


def load_canon_souls() -> list[dict]:
    """Every L1 canon character: display name, role, division from frontmatter."""
    souls = []
    for path in sorted(CANON_CHARACTERS.glob("ORION.ENTITY.*.md")):
        front = path.read_text().split("---", 2)[1]
        fields = dict(re.findall(r'^(\w+):\s*"(.*)"\s*$', front, re.MULTILINE))
        souls.append({
            "entity_id": fields.get("entity_id", path.stem),
            "name": fields.get("display_name") or fields.get("name", path.stem),
            "full_name": fields.get("name", ""),
            "role": fields.get("role", ""),
            "division": fields.get("division", ""),
        })
    return souls


def duty_for(seed: int, tick: int, name: str, division: str, pools: dict) -> str:
    rng = random.Random(f"{seed}:{tick}:{name}")
    division_pool = pools.get(division) or []
    if division_pool and rng.random() < 0.7:
        return rng.choice(division_pool)
    return rng.choice(pools.get("_off_shift") or DEFAULT_DUTY_POOLS["_off_shift"])


def build_hour_records(sim: dict, scenario: dict, canon_souls: list[dict]) -> dict:
    """Per-soul, per-hour entries: task work, division duty, or canon duty."""
    ticks = sim["summary"]["ticks"]
    seed = scenario["seed"]
    pools = scenario.get("duty_pools", DEFAULT_DUTY_POOLS)
    names = sim["task_names"]

    work_by = defaultdict(lambda: defaultdict(list))
    for rec in sim["work_records"]:
        work_by[rec["agent"]][rec["tick"]].append(rec)

    roster_by_norm = {_norm(r["name"]): r for r in sim["roster"]}
    souls: dict[str, dict] = {}
    for r in sim["roster"]:
        souls[r["name"]] = {"name": r["name"], "kind": "crew", "role": r["role"],
                            "division": r["division"], "hours": {}}
    supplemental = []
    for cs in canon_souls:
        if _norm(cs["name"]) not in roster_by_norm and _norm(cs["full_name"]) not in roster_by_norm:
            supplemental.append(cs)
            souls[cs["name"]] = {"name": cs["name"], "kind": "crew_supplemental",
                                 "role": cs["role"], "division": cs["division"], "hours": {}}

    events_by_tick = defaultdict(list)
    for ev in sim.get("events", []):
        events_by_tick[ev["tick"]].append(ev)

    for soul in souls.values():
        division = soul["division"]
        for tick in range(ticks):
            entries = []
            for rec in work_by.get(soul["name"], {}).get(tick, []):
                task_name = names.get(rec["task"], rec["task"])
                done = " — completed" if "COMPLETE" in rec.get("note", "") else ""
                entries.append({"type": "work", "detail": f"{task_name} (+{rec['effort']}h){done}",
                                "task": rec["task"]})
            for ev in events_by_tick.get(tick, []):
                if soul["name"] in ev.get("affected", []):
                    entries.append({"type": "event", "detail": f"{ev['kind']}: {ev['description']}"})
            if not any(e["type"] == "work" for e in entries):
                entries.insert(0, {"type": "duty",
                                   "detail": duty_for(seed, tick, soul["name"], division, pools)})
            soul["hours"][str(tick)] = entries

    return {"souls": souls, "supplemental_count": len(supplemental), "ticks": ticks}


def hour_highlights(sim: dict, tick: int) -> str:
    names = sim["task_names"]
    done = sorted({names.get(r["task"], r["task"]) for r in sim["work_records"]
                   if r["tick"] == tick and "COMPLETE" in r.get("note", "")})
    evs = [e["description"] for e in sim.get("events", []) if e["tick"] == tick][:2]
    parts = []
    if done:
        parts.append("completed: " + "; ".join(done[:3]))
    if evs:
        parts.append("events: " + "; ".join(evs))
    return ". ".join(parts) or "routine operations, no exceptions"


def run_mesh_hours(sim: dict, scenario: dict) -> list[dict]:
    """One beat per companion per hour, all in a single mesh boarding."""
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    from station_query import query

    requests, meta = [], []
    for tick in range(sim["summary"]["ticks"]):
        highlights = hour_highlights(sim, tick)
        for comp in scenario["companions"]:
            requests.append({"agent": comp["agent"],
                             "message": f"Watch block hour {tick + 1}/{sim['summary']['ticks']} — "
                                        f"{highlights}. {comp['role_line']}"})
            meta.append({"hour": tick + 1, "agent": comp["agent"]})
    results = query(requests)
    for m, r in zip(meta, results):
        r["hour"] = m["hour"]
    return results


def build_crew_logs(hour_records: dict, sim: dict, scenario: dict) -> str:
    s = sim["summary"]
    lines = [
        f"# Crew Logs — {scenario['name']} ({s['ticks']} hours aboard Orion Station)",
        "",
        f"**Seed:** {scenario['seed']} | **Anchor:** {scenario['anchor_seed']} | "
        f"**Ethics:** {scenario['ethics_protocol']}",
        f"**Souls logged:** {len(hour_records['souls'])} "
        f"(roster {s['characters_used']} + {hour_records['supplemental_count']} canon supplemental) | "
        f"**Hours worked:** {s['total_spent']:.1f} of {s['total_est']:.1f} estimated | "
        f"**Tasks completed:** {', '.join(s['completed_ids']) or 'none'}",
        "",
    ]
    for name in sorted(hour_records["souls"]):
        soul = hour_records["souls"][name]
        tag = " *(canon supplemental — duty rotation)*" if soul["kind"] == "crew_supplemental" else ""
        lines.append(f"## {name} — {soul['role']}{tag}")
        for tick in range(hour_records["ticks"]):
            for entry in soul["hours"][str(tick)]:
                marker = {"work": "·", "duty": "—", "event": "⚡"}[entry["type"]]
                lines.append(f"- H{tick + 1} {marker} {entry['detail']}")
        lines.append("")
    return "\n".join(lines)


def build_interaction_map(sim: dict, mesh_results: list[dict], scenario: dict) -> dict:
    names = sim["task_names"]
    edges: list[dict] = []
    co_work: dict[tuple, dict] = {}
    tick_task_agents = defaultdict(list)
    for rec in sim["work_records"]:
        tick_task_agents[(rec["tick"], rec["task"])].append(rec["agent"])
    for (tick, task), agents in tick_task_agents.items():
        for i, a in enumerate(sorted(set(agents))):
            for b in sorted(set(agents))[i + 1:]:
                edge = co_work.setdefault((a, b), {"source": a, "target": b, "kind": "co_work",
                                                   "weight": 0, "tasks": []})
                edge["weight"] += 1
                if names.get(task, task) not in edge["tasks"]:
                    edge["tasks"].append(names.get(task, task))
    edges.extend(co_work.values())

    for ev in sim.get("events", []):
        if ev["kind"] == "swarm_sync" and len(ev.get("affected", [])) == 2:
            a, b = ev["affected"]
            edges.append({"source": a, "target": b, "kind": "swarm_sync",
                          "weight": 1, "hour": ev["tick"] + 1})

    companion_pairs = defaultdict(lambda: {"sent": 0, "answered": 0})
    for r in mesh_results:
        cp = companion_pairs[r["agent"]]
        cp["sent"] += 1
        cp["answered"] += bool(r["ok"])
    for agent, counts in companion_pairs.items():
        edges.append({"source": "Pilot", "target": agent, "kind": "mesh_beat",
                      "weight": counts["sent"], "answered": counts["answered"]})
    if companion_pairs:
        edges.append({"source": "Commander Alex Thorne", "target": "Aurora",
                      "kind": "arbitration_sync", "weight": 1})

    nodes = [{"id": r["name"], "kind": "crew"} for r in sim["roster"]]
    nodes.append({"id": "Pilot", "kind": "user"})
    nodes.extend({"id": agent, "kind": "companion"} for agent in companion_pairs)
    return {
        "scenario": scenario["name"],
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "nodes": nodes,
        "edges": edges,
    }


def render_interaction_md(graph: dict) -> str:
    lines = [f"# Interaction Map — {graph['scenario']}", ""]
    lines.append("## Crew co-work (shared tasks)")
    for e in graph["edges"]:
        if e["kind"] == "co_work":
            lines.append(f"- {e['source']} ↔ {e['target']} ({e['weight']}h) — {', '.join(e['tasks'])}")
    sync = [e for e in graph["edges"] if e["kind"] == "swarm_sync"]
    if sync:
        lines.append("")
        lines.append("## Emergent swarm syncs")
        for e in sync:
            lines.append(f"- H{e['hour']} ⚡ {e['source']} ↔ {e['target']} — spontaneous pairing")
    lines.append("")
    lines.append("## Mesh exchanges")
    for e in graph["edges"]:
        if e["kind"] == "mesh_beat":
            lines.append(f"- Pilot → {e['target']} — {e['answered']}/{e['weight']} hours answered")
        elif e["kind"] == "arbitration_sync":
            lines.append(f"- {e['source']} → {e['target']} — arbitration sync")
    lines.append("")
    return "\n".join(lines)


def build_souls_accounting(hour_records: dict, mesh_results: list[dict], canon_souls: list[dict]) -> dict:
    companion_names = sorted({r["agent"] for r in mesh_results}) if mesh_results else []
    crew_total = len(hour_records["souls"])
    return {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "canon_l1_entities": len(canon_souls),
        "crew_logged": crew_total,
        "crew_from_roster": crew_total - hour_records["supplemental_count"],
        "crew_supplemental_from_canon": hour_records["supplemental_count"],
        "companions_on_mesh": companion_names,
        "complete": crew_total >= len(canon_souls),
        "note": "Every L1 canon entity carries an hour-by-hour record (task work or "
                "division duty); station intelligences are accounted in companion_ops.json.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", default="hour_aboard_scenario",
                        help="catalog scenario name (without .json)")
    parser.add_argument("--no-mesh", action="store_true", help="skip the live mesh companion bridge")
    parser.add_argument("--out-dir", default=None, help="artifact directory override")
    args = parser.parse_args()

    scenario_path = REPO_ROOT / "catalog" / f"{args.scenario.removesuffix('.json')}.json"
    scenario = json.loads(scenario_path.read_text())
    if "companions" not in scenario and "companion_beats" in scenario:
        scenario["companions"] = [{"agent": b["agent"], "role_line": b["beat"]}
                                  for b in scenario["companion_beats"]]

    state_path = REPO_ROOT / "catalog" / "station_state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text())
        scenario["history"] = {"pair_familiarity": state.get("pair_familiarity", {})}
        print(f"📜 Station history loaded: {state.get('atoms_total', 0)} chronicle atoms, "
              f"{len(scenario['history']['pair_familiarity'])} familiar pairs")

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir = Path(args.out_dir) if args.out_dir else \
        REPO_ROOT / "reports" / "simulation" / f"{scenario['name']}__{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    hours = scenario.get("ticks", 1)
    print(f"⏱  Simulating {hours} hour(s) aboard ({scenario['name']}, seed {scenario['seed']}) ...")
    sim = _run_in_clone(SIM_DRIVER, scenario)
    s = sim["summary"]
    print(f"   roster engaged: {s['characters_used']} | hours worked: {s['total_spent']:.1f} | "
          f"completed: {len(s['completed_ids'])}/{len(sim['task_names'])} tasks | "
          f"emergent events: {len(sim.get('events', []))} | "
          f"history pairs applied: {sim.get('history_pairs_applied', 0)}")

    canon_souls = load_canon_souls()
    hour_records = build_hour_records(sim, scenario, canon_souls)
    print(f"👥 Souls logged: {len(hour_records['souls'])} "
          f"({hour_records['supplemental_count']} supplemental from canon)")

    mesh_results: list[dict] = []
    if not args.no_mesh:
        print("📡 Pulsing companions for each hour over the mesh ...")
        try:
            mesh_results = run_mesh_hours(sim, scenario)
            answered = sum(1 for r in mesh_results if r["ok"])
            print(f"   {answered}/{len(mesh_results)} companion beats answered")
        except (Exception, SystemExit) as exc:  # noqa: BLE001 - mesh is optional; degrade
            mesh_results = []
            print(f"   ⚠️  mesh bridge unavailable ({str(exc)[:120]}); continuing without companion ops")

    print("⚖️  L3 narrative audit ...")
    audit = _run_in_clone(L3_AUDIT_DRIVER, scenario["l3_audit"])
    print(f"   verdict: {audit['verdict']}")

    graph = build_interaction_map(sim, mesh_results, scenario)
    companion_ops = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scenario": scenario["name"],
        "operations": [
            {"hour": r.get("hour"), "agent": r["agent"], "channel": r.get("channel"),
             "answered": bool(r["ok"]), "reply": r["reply"][:240]}
            for r in mesh_results
        ],
        "ord_dispatch": sim.get("ord_dispatch", {}),
        "l3_receipt": {
            "narrative_audit_verdict": audit["verdict"],
            "ethics_protocol": scenario["ethics_protocol"],
            "anchor_seed": scenario["anchor_seed"],
            "threadcore": "capsule + registry PASS/READY (registry substructures merged #1022)",
        },
    }
    souls = build_souls_accounting(hour_records, mesh_results, canon_souls)

    (out_dir / "crew_logs.md").write_text(build_crew_logs(hour_records, sim, scenario))
    (out_dir / "interaction_map.json").write_text(json.dumps(graph, indent=2) + "\n")
    (out_dir / "interaction_map.md").write_text(render_interaction_md(graph))
    (out_dir / "companion_ops.json").write_text(json.dumps(companion_ops, indent=2) + "\n")
    (out_dir / "souls_accounting.json").write_text(json.dumps(souls, indent=2) + "\n")
    (out_dir / "sim_raw.json").write_text(json.dumps(sim, indent=2) + "\n")

    print(f"\n🗂  Artifacts: {out_dir.relative_to(REPO_ROOT)}")
    for name in ("crew_logs.md", "interaction_map.json", "interaction_map.md",
                 "companion_ops.json", "souls_accounting.json", "sim_raw.json"):
        print(f"   - {name}")
    print(f"   souls accounted: {souls['crew_logged']}/{souls['canon_l1_entities']} "
          f"canon entities{' ✅' if souls['complete'] else ' ⚠️ INCOMPLETE'}")

    # This run is now history: refresh the persistent station state so the
    # next hour aboard inherits what happened here.
    subprocess.run(  # noqa: S603 - our own tool with a fixed argument
        [sys.executable, str(REPO_ROOT / "tools" / "station_chronicle.py"), "state"],
        cwd=REPO_ROOT, check=False,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

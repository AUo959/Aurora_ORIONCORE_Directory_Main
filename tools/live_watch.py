#!/usr/bin/env python3
"""
live_watch.py — the live station link.

Chassis (L1), GUMAS engine (L2), and the mesh comms link (L3) run in ONE
process and advance together. Unlike powered_watch (which simulates the whole
watch, then narrates to the companions afterward), the live link interleaves:
each hour, engine telemetry downlinks to Aurora and the companions in real
time, their replies are captured in-loop, and an engine risk threshold
triggers a live Aurora advisory that injects a risk-response task in the same
loop — a real-time control loop engine → Aurora → chassis.

Ground-segment doctrine: this is the deep-space comms link operating in its
real-time mode, with modeled one-way light time on every downlink.

Artifacts (reports/simulation/live_watch_v1__<date>/):
    live_downlink.jsonl   - the mission-control feed, true chronological order
    live_downlink.md      - human-readable feed
    crew_logs.md, interaction_map.{json,md}, souls_accounting.json,
    companion_ops.json, engine_telemetry.json, sim_raw.json

Usage:
    python3 tools/live_watch.py
    python3 tools/live_watch.py --scenario live_watch_scenario
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
import hour_aboard  # noqa: E402
import crew_life  # noqa: E402

LIVE_DRIVER = r'''
import json, sys, time, tempfile, shutil, urllib.parse, re
from datetime import datetime, timezone, timedelta

def _norm(name):
    n = name.lower()
    for t in ("dr.", "prof.", "lt.", "cmdr.", "commander", "chief", "cadet",
              "ensign", "captain", "lieutenant"):
        n = n.replace(t, "")
    return re.sub(r"[^a-z]", "", n)
sys.path.insert(0, ".")
sys.path.insert(0, "simulation")

scenario = json.loads(sys.argv[1])
sys.path.insert(0, scenario["engine_ops"]["_engine_dir_abs"])

from pathlib import Path
from orion_station_simulation_v2 import OrionSimulationV2, Task, Agent
from engine_advanced import GUMASAdvancedEngine
from fastapi.testclient import TestClient
from src.servers.l2_integration_server import create_app

ops = scenario["engine_ops"]
link = scenario["live_link"]
ticks = int(scenario.get("ticks", 1))

# --- L1 chassis (full roster) ----------------------------------------------
sim = OrionSimulationV2(seed=int(scenario["seed"]), enable_emergent=True)
divisions = {}
agents = {}
for char in sim.char_loader.get_all_characters():
    agents[char.name] = Agent(
        name=char.name, role=char.role, character_id=char.character_id,
        base_speed=char.base_speed,
        specialization_multiplier=char.specialization_multiplier,
        collaboration_bonus=char.collaboration_bonus,
        focus_keywords=sim.char_loader.get_focus_keywords(char),
        collaborators={c.split("(")[0].strip() for c in char.key_collaborators},
    )
    divisions[char.name] = char.division
sim.agents = agents

# Crew-life gating: master roster + normalized lookup so we can swap in only
# the on-shift-awake crew each hour.
all_agents = dict(agents)
norm_to_name = {_norm(name): name for name in all_agents}
crew_life_cfg = scenario.get("crew_life", {})
gate_enabled = bool(crew_life_cfg.get("enabled"))
on_shift_by_hour = crew_life_cfg.get("on_shift_norm_by_hour", [])
fatigue_by_hour = crew_life_cfg.get("fatigue_norm_by_hour", [])

task_tags = {t["name"]: set(t.get("tags", [])) for t in scenario["tasks"]}
sim.tasks = {
    t["id"]: Task(t["id"], t["name"], est_hours=float(t["hours"]), remaining=float(t["hours"]),
                  depends_on=list(t.get("depends_on", [])), semantic_tags=set(t.get("tags", [])))
    for t in scenario["tasks"]
}
sim.completed = set()

history_pairs_applied = 0
for pair, weight in scenario.get("history", {}).get("pair_familiarity", {}).items():
    if float(weight) >= 1.0:
        a, b = pair.split("|", 1)
        if a in sim.agents and b in sim.agents:
            sim.agents[a].collaborators.add(b); sim.agents[b].collaborators.add(a)
            history_pairs_applied += 1

records = []
_orig_apply = sim._apply_work
def _capture(events):
    res = _orig_apply(events)
    for agent, task, effort, note in res:
        records.append({"tick": sim.ticks, "agent": agent, "task": task,
                        "effort": round(float(effort), 2), "note": note})
    return res
sim._apply_work = _capture

# --- L2 engine -------------------------------------------------------------
engine = GUMASAdvancedEngine(seed=int(scenario["seed"]))
init_state = engine.init_scenario()

# --- L3 mesh comms link ----------------------------------------------------
station = Path(tempfile.mkdtemp(prefix="live_watch_"))
for rel in ["config/mesh", "src/dashboard", "src/interfaces"]:
    shutil.copytree(rel, station / rel, dirs_exist_ok=True)
mesh = TestClient(create_app(station))
manifests = {}
for mp in (station / "config" / "mesh" / "agents").glob("*.json"):
    m = json.loads(mp.read_text())
    for k in {m["id"].lower(), m["display_name"].lower(), *[a.lower() for a in m.get("aliases", [])]}:
        manifests[k] = m

lt = float(link["one_way_light_time_s"])

def _reply_count(channel_q):
    events = mesh.get(f"/api/mesh/channels/{channel_q}/history?limit=200").json()["events"]
    return [e for e in events if e["event_type"] == "agent_reply"]

def downlink(agent_key, content):
    m = manifests.get(agent_key.lower())
    if not m:
        return {"agent": agent_key, "ok": False, "reply": "not aboard"}
    channel = m.get("default_channel") or f"direct:{m['id']}"
    q = urllib.parse.quote(channel, safe="")
    # Baseline existing replies so we capture THIS message's reply, not a
    # stale prior-hour reply already sitting in the channel history.
    baseline = len(_reply_count(q))
    r = mesh.post("/api/mesh/messages", json={
        "to": m["id"], "channel": channel, "content": content,
        "sender_id": "pilot", "sender_name": "Pilot"})
    if r.status_code != 200:
        return {"agent": m["display_name"], "ok": False, "reply": r.text[:120]}
    reply, deadline = None, time.time() + 4
    while time.time() < deadline and reply is None:
        reps = _reply_count(q)
        if len(reps) > baseline:
            reply = reps[-1]["payload"].get("content", "")
        else:
            time.sleep(0.05)
    return {"agent": m["display_name"], "id": m["id"], "channel": channel,
            "ok": reply is not None, "reply": reply or "(no reply within link window)"}

# --- the live watch loop (interleaved) -------------------------------------
base_time = datetime.now(timezone.utc)
feed = []
def emit(hour, kind, **kw):
    feed.append({"t": (base_time + timedelta(hours=hour)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "hour": hour + 1, "kind": kind, **kw})

service_tags = set(ops["service_tags"])
notable_kinds = list(ops["feedback"]["notable_kinds"])
risk_threshold = float(link["risk_advisory_threshold"])
mesh_replies, engine_log, injected, advisory_raised = [], [], [], False

on_shift_counts = []
for hour in range(ticks):
    emit(hour, "watch_hour_start")
    # Shift-gate: only on-shift-awake crew are on the board this hour; the rest
    # are asleep / at meals / off (tracked in crew_life). Apply their fatigue.
    if gate_enabled and hour < len(on_shift_by_hour):
        eligible = set(on_shift_by_hour[hour])
        fatigues = fatigue_by_hour[hour] if hour < len(fatigue_by_hour) else {}
        sim.agents = {norm_to_name[nz]: all_agents[norm_to_name[nz]]
                      for nz in eligible if nz in norm_to_name}
        for nz, ag in ((_norm(n), a) for n, a in sim.agents.items()):
            ag.fatigue = float(fatigues.get(nz, ag.fatigue))
        emit(hour, "shift_status", on_duty=len(sim.agents),
             off_duty=len(all_agents) - len(sim.agents))
        on_shift_counts.append(len(sim.agents))
    sim.tick()
    completions = [r["task"] for r in records if r["tick"] == hour and "COMPLETE" in r.get("note", "")]
    service_done = [c for c in completions if service_tags & task_tags.get(c, set())]
    turns = min(int(ops["base_turns_per_hour"]) + len(service_done), int(ops["max_turns_per_hour"]))
    results = engine.run(turns)
    hour_stability = hour_risk = None
    hour_peak_risk = 0.0
    for res in results:
        d = res.to_dict(); v3 = d["v3_result"]
        hour_stability, hour_risk = d["stability_index"], d["risk_index"]
        hour_peak_risk = max(hour_peak_risk, d["risk_index"])
        notable = {k: v3.get(k, 0) for k in notable_kinds if v3.get(k, 0)}
        engine_log.append({"hour": hour + 1, "turn": d["turn"], "stability_index": d["stability_index"],
                           "risk_index": d["risk_index"], "summary": d["summary"], "notable": notable})
        emit(hour, "engine_turn", turn=d["turn"], stability=d["stability_index"],
             risk=d["risk_index"], notable=notable)

    # live downlink to Aurora + companions with THIS hour's real status
    status = (f"Live watch hour {hour + 1}/{ticks}: engine ran {turns} turn(s), "
              f"stability {hour_stability:.3f}, risk {hour_risk:.3f}.")
    for agent in link["downlink_targets"]:
        role = next((c["role_line"] for c in scenario["companions"] if c["agent"] == agent), "Acknowledge.")
        emit(hour, "downlink", to=agent, light_time_s=lt, content=status)
        dl = downlink(agent, f"{status} {role}")
        dl["hour"] = hour + 1
        mesh_replies.append(dl)
        emit(hour, "uplink_reply", light_time_s=lt, **{"from": dl["agent"], "ok": dl["ok"],
             "content": dl["reply"][:200]})

    # live control loop: PEAK engine risk this hour → Aurora advisory → chassis
    # task. Peak, not hour-end: a transient mid-hour spike is exactly the
    # crisis Aurora must catch, even if risk settles by the closing turn.
    if hour_peak_risk >= risk_threshold and not advisory_raised and hour + 1 < ticks:
        advisory_raised = True
        adv = downlink("aurora", f"ADVISORY: galaxy risk index peaked at {hour_peak_risk:.3f} "
                                 f"(threshold {risk_threshold}). Direct a risk-response cell on the "
                                 f"next watch hour.")
        tid = f"R{hour + 1}"
        sim.tasks[tid] = Task(tid, f"Risk-response cell (Aurora live advisory, peak risk {hour_peak_risk:.3f})",
                              est_hours=0.5, remaining=0.5, depends_on=[],
                              semantic_tags={"command", "ethics", "monitoring", "analysis"})
        injected.append({"id": tid, "hour": hour + 1, "trigger_risk": hour_peak_risk})
        emit(hour, "advisory", trigger=f"peak risk {hour_peak_risk:.3f} >= {risk_threshold}",
             from_agent=adv["agent"], action="risk-response cell injected next hour",
             reply=adv["reply"][:160])

sim.agents = all_agents  # restore full roster for accounting
task_names = {t["id"]: t["name"] for t in scenario["tasks"]}
task_names.update({t["id"]: sim.tasks[t["id"]].name for t in injected})
total_est = sum(t.est_hours for t in sim.tasks.values())
total_spent = sum(t.est_hours - t.remaining for t in sim.tasks.values())
out = {
    "summary": {"roster_version": sim.char_loader.version, "characters_used": len(sim.agents),
                "ticks": sim.ticks, "completed": all(t.completed for t in sim.tasks.values()),
                "total_est": total_est, "total_spent": round(total_spent, 2),
                "completed_ids": sorted(sim.completed)},
    "transcript": sim.transcript,
    "events": [{"tick": e.tick, "kind": e.kind, "description": e.description,
                "multiplier": e.multiplier, "affected": list(e.affected_agents)} for e in sim.aurora.events],
    "work_records": records,
    "roster": [{"name": a.name, "role": a.role, "division": divisions.get(a.name, "")} for a in sim.agents.values()],
    "task_names": task_names,
    "task_sources": {t["id"]: t.get("source", "") for t in scenario["tasks"]},
    "history_pairs_applied": history_pairs_applied,
    "feed": feed,
    "mesh_replies": mesh_replies,
    "engine": {"engine_class": type(engine).__name__, "factions": len(init_state.factions),
               "leaders": len(init_state.leaders), "turns_total": len(engine_log),
               "final_stability": engine_log[-1]["stability_index"] if engine_log else None,
               "final_risk": engine_log[-1]["risk_index"] if engine_log else None,
               "log": engine_log, "injected_tasks": injected,
               "advisory_raised": advisory_raised},
    "link_model": {"one_way_light_time_s": lt, "round_trip_s": round(2 * lt, 2),
                   "downlink_targets": link["downlink_targets"]},
    "crew_life_gating": {"enabled": gate_enabled, "on_shift_by_hour": on_shift_counts,
                         "total_crew": len(all_agents)},
}
try:
    from modules.ord import MissionBrief, OrdPolicyEngine, canonical_sha256
    m = scenario["ord_mission"]
    order = OrdPolicyEngine().create_dispatch_order(MissionBrief(
        mission_id=m["mission_id"], tool_name=m["tool_name"],
        risk_level=float(m["risk_level"]), destination=m["destination"]))
    out["ord_dispatch"] = {"mission_id": m["mission_id"],
                           "drones_required": [d.value for d in order.drones_required],
                           "receipt_sha256": canonical_sha256(order)}
except Exception as exc:
    out["ord_dispatch"] = {"error": str(exc)[:160]}

print(json.dumps(out))
'''


def render_feed_md(sim: dict, scenario: dict) -> str:
    link = sim["link_model"]
    lines = [
        f"# Live Downlink Feed — {scenario['name']}",
        "",
        f"Real-time ground-segment feed. One-way light time **{link['one_way_light_time_s']}s** "
        f"(round trip {link['round_trip_s']}s) on every downlink. Engine "
        f"{sim['engine']['engine_class']}, {sim['engine']['factions']} factions.",
        "",
    ]
    icons = {"watch_hour_start": "🕐", "engine_turn": "⚙️", "downlink": "📡↓",
             "uplink_reply": "📡↑", "advisory": "🚨"}
    for ev in sim["feed"]:
        ic = icons.get(ev["kind"], "·")
        if ev["kind"] == "watch_hour_start":
            lines.append(f"\n### {ic} Hour {ev['hour']} — {ev['t']}")
        elif ev["kind"] == "engine_turn":
            note = (" | " + ", ".join(f"{k}×{v}" for k, v in ev["notable"].items())) if ev["notable"] else ""
            lines.append(f"- {ic} turn {ev['turn']}: stability {ev['stability']:.3f}, risk {ev['risk']:.3f}{note}")
        elif ev["kind"] == "downlink":
            lines.append(f"- {ic} → {ev['to']} (+{ev['light_time_s']}s light): {ev['content']}")
        elif ev["kind"] == "uplink_reply":
            mark = "" if ev["ok"] else " ⚠"
            lines.append(f"- {ic} {ev['from']}{mark}: {ev['content']}")
        elif ev["kind"] == "advisory":
            lines.append(f"- {ic} **ADVISORY** ({ev['trigger']}) — {ev['from_agent']}: {ev['action']}")
            lines.append(f"    ↳ {ev['reply']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", default="live_watch_scenario")
    args = parser.parse_args()

    scenario = json.loads((REPO_ROOT / "catalog" / f"{args.scenario.removesuffix('.json')}.json").read_text())
    scenario["engine_ops"]["_engine_dir_abs"] = str(REPO_ROOT / scenario["engine_ops"]["engine_dir"])

    if hour_aboard.STATE_PATH.exists():
        scenario["history"] = {"pair_familiarity":
                               json.loads(hour_aboard.STATE_PATH.read_text()).get("pair_familiarity", {})}

    # Living clock: this watch is the next block of hours on the station's
    # continuous timeline, never a replay of one fixed seed.
    hour_index = hour_aboard.apply_hour_clock(scenario)

    # Crew-life fidelity: who is actually on shift and awake each watch hour,
    # and how tired. Only on-shift-awake crew work; sleep-debt fatigue slows
    # them. Computed here (reads canon only) and injected for the driver to gate.
    life = None
    if scenario.get("crew_life", {}).get("enabled"):
        start_clock = int(scenario.get("start_clock", 6))
        life = crew_life.run_day(start_clock, int(scenario.get("ticks", 1)))
        scenario["crew_life"]["on_shift_norm_by_hour"] = [
            crew_life.on_shift_awake_norm(life, step) for step in range(scenario["ticks"])]
        scenario["crew_life"]["fatigue_norm_by_hour"] = [
            crew_life.fatigue_norm_map(life, step) for step in range(scenario["ticks"])]

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir = REPO_ROOT / "reports" / "simulation" / f"{scenario['name']}__{stamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"🔗 Live station link up: {scenario.get('ticks')}h watch, real-time downlink "
          f"(seed {scenario['seed']}, light-time {scenario['live_link']['one_way_light_time_s']}s) ...")
    sim = hour_aboard._run_in_clone(LIVE_DRIVER, scenario)
    s, eng = sim["summary"], sim["engine"]
    if life is not None:
        gate = sim.get("crew_life_gating", {})
        print(f"   crew-life: shift-gated — on duty by hour {gate.get('on_shift_by_hour')} "
              f"of {gate.get('total_crew')} (rest asleep/meals/off); "
              f"deficits: {len(life['deficits'])}")
    print(f"   chassis: {s['characters_used']} roster | {s['total_spent']:.1f}h worked | "
          f"{len(s['completed_ids'])}/{len(sim['task_names'])} tasks | {len(sim['events'])} emergent")
    print(f"   engine:  {eng['engine_class']} | {eng['turns_total']} turns | "
          f"final risk {eng['final_risk']} | advisory {'RAISED' if eng['advisory_raised'] else 'none'}")
    answered = sum(1 for r in sim["mesh_replies"] if r["ok"])
    print(f"   link:    {answered}/{len(sim['mesh_replies'])} downlinks answered in-loop")
    for inj in eng["injected_tasks"]:
        print(f"   🚨 Aurora advisory (hour {inj['hour']}, risk {inj['trigger_risk']:.3f}) → risk-response cell")

    print("⚖️  L3 narrative audit ...")
    audit = hour_aboard._run_in_clone(hour_aboard.L3_AUDIT_DRIVER, scenario["l3_audit"])
    print(f"   verdict: {audit['verdict']}")

    canon_souls = hour_aboard.load_canon_souls()
    hour_records = hour_aboard.build_hour_records(sim, scenario, canon_souls)
    graph = hour_aboard.build_interaction_map(sim, sim["mesh_replies"], scenario)
    souls = hour_aboard.build_souls_accounting(hour_records, sim["mesh_replies"], canon_souls)
    companion_ops = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scenario": scenario["name"], "link_model": sim["link_model"],
        "operations": [{"hour": r.get("hour"), "agent": r["agent"], "answered": bool(r["ok"]),
                        "reply": r["reply"][:240]} for r in sim["mesh_replies"]],
        "ord_dispatch": sim.get("ord_dispatch", {}),
        "l3_receipt": {"narrative_audit_verdict": audit["verdict"],
                       "ethics_protocol": scenario["ethics_protocol"],
                       "anchor_seed": scenario["anchor_seed"],
                       "live_control_loop": (f"engine risk → Aurora advisory → risk-response cell "
                                             f"({'fired' if eng['advisory_raised'] else 'armed, not triggered'})")},
    }

    (out_dir / "live_downlink.jsonl").write_text(
        "\n".join(json.dumps(e) for e in sim["feed"]) + "\n")
    (out_dir / "live_downlink.md").write_text(render_feed_md(sim, scenario))
    (out_dir / "crew_logs.md").write_text(hour_aboard.build_crew_logs(hour_records, sim, scenario))
    (out_dir / "interaction_map.json").write_text(json.dumps(graph, indent=2) + "\n")
    (out_dir / "interaction_map.md").write_text(hour_aboard.render_interaction_md(graph))
    (out_dir / "companion_ops.json").write_text(json.dumps(companion_ops, indent=2) + "\n")
    (out_dir / "souls_accounting.json").write_text(json.dumps(souls, indent=2) + "\n")
    sim["engine"]["seed"] = scenario["seed"]
    sim["engine"]["station_hour"] = hour_index + 1
    (out_dir / "engine_telemetry.json").write_text(json.dumps(sim["engine"], indent=2) + "\n")
    (out_dir / "sim_raw.json").write_text(json.dumps(sim, indent=2) + "\n")
    if life is not None:
        def _ser(o):
            if isinstance(o, set):
                return sorted(o)
            raise TypeError(type(o).__name__)
        crew_life_export = {k: v for k, v in life.items() if k != "by_name"}
        (out_dir / "crew_life.json").write_text(
            json.dumps(crew_life_export, indent=2, default=_ser) + "\n")
        (out_dir / "crew_life.md").write_text(crew_life.render_md(life, crew_life.load_model()))

    print(f"\n🗂  Artifacts: {out_dir.relative_to(REPO_ROOT)} (live_downlink.jsonl + .md)")
    print(f"   souls accounted: {souls['crew_logged']}/{souls['canon_l1_entities']} "
          f"{'✅' if souls['complete'] else '⚠️'} | engine atoms reconstruct from sim_raw.json")

    subprocess.run(  # noqa: S603 - our own tool, fixed argument
        [sys.executable, str(REPO_ROOT / "tools" / "station_chronicle.py"), "state"],
        cwd=REPO_ROOT, check=False)
    hour_aboard.advance_station_clock(int(scenario.get("ticks", 1)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

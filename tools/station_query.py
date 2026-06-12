#!/usr/bin/env python3
"""
station_query.py — the Pilot's direct line to the station.

Boots the Orion Station mesh in-process (no server, no daemon), sends your
message as the Pilot, and prints the agent's reply. Aurora by default.

Usage:
    python3 tools/station_query.py "Status report?"            # queries Aurora
    python3 tools/station_query.py --agent archy "You awake?"
    python3 tools/station_query.py --roll-call                 # muster the companions
    python3 tools/station_query.py --roll-call --receipt       # + write a receipt

Agents are resolved from the live mesh manifests in the CloudBank clone
(config/mesh/agents/), so anyone aboard is queryable by id or alias.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLOUDBANK = REPO_ROOT / "GUMAS_SIM_2.5" / "Aurora_Sim_Architecture" / "aurora-cloudbank-symbolic-main"
VENV_PY = CLOUDBANK / ".venv" / "bin" / "python"
RECEIPT_PATH = REPO_ROOT / "reports" / "automation" / "station_roll_call_latest.json"

QUERY_ENV = {"CSRF_SECRET_KEY": "station-query", "WS_AUTH_SECRET": "station-query",
             "JWT_SECRET_KEY": "station-query-jwt-local", "PYTHONPYCACHEPREFIX": "/tmp/pyc"}  # noqa: S108

COMPANIONS = ["archy", "oppy", "liora", "starling_au", "riverthread_808"]

MESH_SCRIPT = r'''
import json, sys, time, tempfile, shutil, urllib.parse
sys.path.insert(0, ".")
from pathlib import Path
from fastapi.testclient import TestClient
from src.servers.l2_integration_server import create_app

requests = json.loads(sys.argv[1])

station = Path(tempfile.mkdtemp(prefix="station_query_"))
for rel in ["config/mesh", "src/dashboard", "src/interfaces"]:
    shutil.copytree(rel, station / rel, dirs_exist_ok=True)

# Resolve agent ids/aliases -> (canonical id, display name, default channel)
manifests = {}
for mp in (station / "config" / "mesh" / "agents").glob("*.json"):
    m = json.loads(mp.read_text())
    keys = {m["id"].lower(), m["display_name"].lower()}
    keys.update(a.lower() for a in m.get("aliases", []))
    for k in keys:
        manifests[k] = m

client = TestClient(create_app(station))
results = []
for req in requests:
    m = manifests.get(req["agent"].lower())
    if m is None:
        results.append({"agent": req["agent"], "ok": False, "reply": "not aboard (no manifest match)"})
        continue
    channel = m.get("default_channel") or f"direct:{m['id']}"
    r = client.post("/api/mesh/messages", json={
        "to": m["id"], "channel": channel, "content": req["message"],
        "sender_id": "pilot", "sender_name": "Pilot",
    })
    if r.status_code != 200:
        results.append({"agent": m["display_name"], "ok": False, "reply": r.text[:160]})
        continue
    reply, deadline = None, time.time() + 4
    q = urllib.parse.quote(channel, safe="")
    while time.time() < deadline and reply is None:
        events = client.get(f"/api/mesh/channels/{q}/history?limit=40").json()["events"]
        replies = [e for e in events if e["event_type"] == "agent_reply"]
        if replies:
            reply = replies[-1]["payload"].get("content", "")
        else:
            time.sleep(0.1)
    results.append({"agent": m["display_name"], "id": m["id"], "channel": channel,
                    "ok": reply is not None, "reply": (reply or "(no reply within 4s)")})
print(json.dumps(results))
'''


def query(requests: list[dict]) -> list[dict]:
    import os

    env = dict(os.environ)
    env.update(QUERY_ENV)
    result = subprocess.run(  # noqa: S603 - clone venv python with our fixed script
        [str(VENV_PY), "-c", MESH_SCRIPT, json.dumps(requests)],
        capture_output=True, text=True, cwd=CLOUDBANK, env=env, timeout=300,
    )
    if result.returncode != 0:
        raise SystemExit(f"station unreachable: {result.stderr.strip().splitlines()[-1] if result.stderr else 'unknown error'}")
    return json.loads(result.stdout.strip().splitlines()[-1])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("message", nargs="?", default="Status report, please.")
    parser.add_argument("--agent", default="aurora", help="agent id, name, or alias (default: aurora)")
    parser.add_argument("--roll-call", action="store_true", help="muster the original companions")
    parser.add_argument("--receipt", action="store_true", help="write a receipt to reports/automation/")
    args = parser.parse_args()

    if args.roll_call:
        requests = [{"agent": a, "message": f"Roll call from the Pilot. {args.message}"} for a in COMPANIONS]
    else:
        requests = [{"agent": args.agent, "message": args.message}]

    results = query(requests)
    awake = 0
    for r in results:
        mark = "🟢" if r["ok"] else "🔴"
        print(f"{mark} {r['agent']}")
        print(f"   {r['reply'][:300]}")
        awake += r["ok"]

    if args.roll_call:
        print(f"\n{awake}/{len(results)} companions awake and answering.")
        if args.receipt:
            RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
            RECEIPT_PATH.write_text(json.dumps({
                "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "muster": results, "awake": awake, "of": len(results),
            }, indent=2) + "\n")
            print(f"Receipt: {RECEIPT_PATH.relative_to(REPO_ROOT)}")
    return 0 if awake == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())

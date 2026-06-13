#!/usr/bin/env python3
"""
crew_life.py — the human layer of Orion Station.

High fidelity means the crew are people, not task-executors: they sleep, eat,
shower, use the head, take recreation, and tire. This models each L1 crew
member's circadian and physiological state on the canonical Alpha/Bravo/
Charlie/Delta shift rotation (canon: orion_station_life_infrastructure.md),
tracks their needs and the station's life-support load, and exposes the
on-shift-awake set + per-crew fatigue so a watch only works the crew who are
actually on duty and rested.

Per crew, per station-hour, exactly one activity:
    on_shift | asleep | meal | hygiene | recreation | personal

Needs tracked: sleep_debt, hunger, hygiene, morale, bathroom events.
Fatigue derives from sleep_debt (real circadian fatigue, not just work).
Consumables: water (showers + head into the 98% loop), galley portions,
O2/CO2 (scrubber load).

Usage:
    python3 tools/crew_life.py day                 # one 24h station day, all crew
    python3 tools/crew_life.py day --start 6 --hours 24
    python3 tools/crew_life.py shifts              # show shift assignments
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = REPO_ROOT / "catalog" / "crew_life_model.json"
CANON_CHARACTERS = REPO_ROOT / "GUMAS_SIM_2.5" / "CanonRec" / "canon" / "L1" / "characters"

# Command/senior roles we guarantee across all four shifts for coverage.
COMMAND_HINTS = ("Commander", "Executive Officer", "XO", "Chief", "Officer", "Lt", "Lieutenant")


def load_model() -> dict:
    return json.loads(MODEL_PATH.read_text())


def load_crew() -> list[dict]:
    crew = []
    for path in sorted(CANON_CHARACTERS.glob("ORION.ENTITY.*.md")):
        front = path.read_text().split("---", 2)[1]
        f = dict(re.findall(r'^(\w+):\s*"(.*)"\s*$', front, re.MULTILINE))
        crew.append({"entity_id": f.get("entity_id", path.stem),
                     "name": f.get("display_name") or f.get("name", path.stem),
                     "role": f.get("role", ""), "division": f.get("division", "")})
    return crew


def assign_shifts(crew: list[dict], model: dict) -> dict[str, str]:
    """Deterministic shift assignment, weighted per canon manning, with at
    least one command/senior officer guaranteed on every shift."""
    shifts = list(model["shifts"])
    order = sorted(crew, key=lambda c: c["entity_id"])
    assignment: dict[str, str] = {}

    # Seed each shift with one senior officer for coverage.
    seniors = [c for c in order if any(h in c["role"] for h in COMMAND_HINTS)]
    for i, shift in enumerate(shifts):
        if i < len(seniors):
            assignment[seniors[i]["name"]] = shift

    # Weighted round-robin for the rest (stable by entity_id).
    weights = [(s, model["shifts"][s]["weight"]) for s in shifts]
    cumulative, acc = [], 0.0
    for s, w in weights:
        acc += w
        cumulative.append((acc, s))
    total = acc
    for idx, c in enumerate(order):
        if c["name"] in assignment:
            continue
        point = ((idx * 0.6180339887) % 1.0) * total  # golden-ratio low-discrepancy
        assignment[c["name"]] = next(s for cum, s in cumulative if point <= cum)
    return assignment


def _in_window(hour: int, window: list[int]) -> bool:
    """Window may wrap past 24 (e.g. sleep [22, 29] == 22:00–05:00)."""
    start, end = window
    h = hour % 24
    if end <= 24:
        return start <= h < end
    return h >= start or h < (end - 24)


def simulate(crew_shifts: dict[str, str], crew: list[dict], model: dict,
             start_hour: int, hours: int) -> dict:
    sh = model["shifts"]
    meals = model["meal_services"]
    rhythm = model["rhythm"]
    n = model["needs"]
    cons = model["consumables"]
    fat = model["fatigue"]
    by_name = {c["name"]: c for c in crew}

    # Deterministic per-crew shower hour within their off-awake time.
    state = {}
    for name, shift in crew_shifts.items():
        state[name] = {"sleep_debt": 4.0, "hunger": 2.0, "hygiene": 6.0, "morale": 6.0,
                       "meals_taken": set(), "showered_today": False, "bathroom_events": 0,
                       "meals_eaten": 0, "peak_sleep_debt": 4.0, "hours": []}

    consumables = {"water_drawn_l": 0.0, "water_recycled_l": 0.0,
                   "galley_portions": 0.0, "co2_kg": 0.0, "o2_kg": 0.0}
    occupancy = defaultdict(lambda: defaultdict(int))  # hour -> activity -> count

    for step in range(hours):
        clock = (start_hour + step) % 24
        day_boundary = clock == 0
        for name, shift in crew_shifts.items():
            st = state[name]
            if day_boundary:
                st["meals_taken"].clear(); st["showered_today"] = False
            work_w, sleep_w = sh[shift]["work"], sh[shift]["sleep"]
            asleep = _in_window(clock, sleep_w)
            on_shift = _in_window(clock, work_w)

            activity = None
            if asleep:
                activity = "asleep"
                st["sleep_debt"] = max(0.0, st["sleep_debt"] - n["sleep_recovery_per_sleep_hour"])
                consumables["co2_kg"] += cons["co2_kg_per_asleep_hour"]
            else:
                st["sleep_debt"] = min(n["sleep_debt_max"], st["sleep_debt"] + n["sleep_debt_per_awake_hour"])
                st["hunger"] += n["hunger_per_awake_hour"]
                st["hygiene"] += n["hygiene_per_hour"]
                consumables["co2_kg"] += cons["co2_kg_per_awake_hour"]
                consumables["o2_kg"] += cons["o2_kg_per_awake_hour"]
                # bathroom: ~even across waking hours
                if (step + hash(name)) % max(2, 16 // max(1, n["bathroom_uses_per_day"])) == 0:
                    st["bathroom_events"] += 1
                    drawn = cons["bathroom_water_liters"]
                    consumables["water_drawn_l"] += drawn
                    consumables["water_recycled_l"] += drawn * cons["water_recycle_efficiency"]

                # Eating is independent of duty: a crew grabs a meal at a meal
                # service whether on or off shift (canon: lunch is shift
                # overlap). This is what stops on-shift crew starving.
                meal_now = next((m for m, w in meals.items() if _in_window(clock, w)), None)
                rec_now = _in_window(clock, rhythm["recreation"])
                ate = False
                if meal_now and meal_now not in st["meals_taken"]:
                    st["meals_taken"].add(meal_now)
                    st["hunger"] = 0.0
                    st["meals_eaten"] += 1
                    consumables["galley_portions"] += cons["meal_portions_per_serving"]
                    ate = True
                st["peak_sleep_debt"] = max(st["peak_sleep_debt"], st["sleep_debt"])

                if on_shift:
                    activity = "on_shift"
                    st["morale"] = max(0.0, st["morale"] - n["morale_work_drain"])
                elif ate:
                    activity = "meal"
                elif not st["showered_today"] and st["hygiene"] >= 6.0:
                    activity = "hygiene"
                    st["showered_today"] = True
                    st["hygiene"] = 0.0
                    drawn = cons["shower_water_liters"]
                    consumables["water_drawn_l"] += drawn
                    consumables["water_recycled_l"] += drawn * cons["water_recycle_efficiency"]
                elif rec_now:
                    activity = "recreation"
                    st["morale"] = min(10.0, st["morale"] + n["morale_recreation_gain"])
                else:
                    activity = "personal"

            fatigue = min(fat["max_fatigue"], st["sleep_debt"] * fat["sleep_debt_to_fatigue"])
            st["hours"].append({"clock": clock, "activity": activity,
                                "sleep_debt": round(st["sleep_debt"], 1),
                                "hunger": round(st["hunger"], 1),
                                "fatigue": round(fatigue, 1)})
            occupancy[step][activity] += 1

    # deficits: chronic deprivation, not a transient pre-meal dip. Flag crew
    # who peaked at near-max sleep debt, or were genuinely underfed for the
    # window length (< 1 meal per ~8 waking hours).
    deficits = []
    # ~1 meal per 10 waking-ish hours; a shift worker who sleeps through one
    # service and eats the other two is fed, not underfed.
    expected_meals = max(1, hours // 10)
    debt_cap = n["sleep_debt_max"] * 0.9
    for name, st in state.items():
        chronic_tired = st["peak_sleep_debt"] >= debt_cap
        underfed = st["meals_eaten"] < expected_meals and hours >= 10
        if chronic_tired or underfed:
            deficits.append({"name": name, "peak_sleep_debt": round(st["peak_sleep_debt"], 1),
                             "meals_eaten": st["meals_eaten"],
                             "reason": "chronic fatigue" if chronic_tired else "underfed"})

    return {"start_hour": start_hour, "hours": hours, "crew_count": len(crew_shifts),
            "shifts": crew_shifts, "state": state, "occupancy": dict(occupancy),
            "consumables": {k: round(v, 2) for k, v in consumables.items()},
            "deficits": deficits, "by_name": by_name}


def norm_name(name: str) -> str:
    """Normalize a crew name to bridge canon display names and sim-loader
    names (titles differ: 'Commander Alex Thorne' vs 'Alex Thorne')."""
    n = name.lower()
    for t in ("dr.", "prof.", "lt.", "cmdr.", "commander", "chief", "cadet",
              "ensign", "captain", "lieutenant"):
        n = n.replace(t, "")
    return re.sub(r"[^a-z]", "", n)


def on_shift_awake(sim: dict, step: int) -> set[str]:
    """The crew eligible to work at a given simulated step (on shift, awake)."""
    return {name for name, st in sim["state"].items()
            if step < len(st["hours"]) and st["hours"][step]["activity"] == "on_shift"}


def on_shift_awake_norm(sim: dict, step: int) -> list[str]:
    return sorted(norm_name(n) for n in on_shift_awake(sim, step))


def fatigue_norm_map(sim: dict, step: int) -> dict[str, float]:
    return {norm_name(name): st["hours"][step]["fatigue"]
            for name, st in sim["state"].items() if step < len(st["hours"])}


def render_md(sim: dict, model: dict) -> str:
    sh = model["shifts"]
    lines = [f"# Crew Life — {sim['hours']}h from station hour {sim['start_hour']:02d}:00",
             "", f"**Crew:** {sim['crew_count']} | shifts: " +
             ", ".join(f"{s} {sum(1 for v in sim['shifts'].values() if v == s)}" for s in sh),
             ""]
    lines.append("## Occupancy by hour (who is doing what)")
    acts = ["on_shift", "asleep", "meal", "hygiene", "recreation", "personal"]
    lines.append("| hour | " + " | ".join(acts) + " |")
    lines.append("|" + "---|" * (len(acts) + 1))
    for step in range(sim["hours"]):
        clock = (sim["start_hour"] + step) % 24
        row = sim["occupancy"].get(step, {})
        lines.append(f"| {clock:02d}:00 | " + " | ".join(str(row.get(a, 0)) for a in acts) + " |")
    c = sim["consumables"]
    lines += ["", "## Life-support load (the station must sustain them)",
              f"- Water drawn: {c['water_drawn_l']} L | recycled (98% loop): {c['water_recycled_l']} L "
              f"| net make-up: {round(c['water_drawn_l'] - c['water_recycled_l'], 2)} L",
              f"- Galley portions served: {c['galley_portions']}",
              f"- CO2 produced (scrubber load): {c['co2_kg']} kg | O2 consumed: {c['o2_kg']} kg", ""]
    if sim["deficits"]:
        lines.append("## ⚠ Crew in deficit (chronic over the window)")
        for d in sim["deficits"]:
            lines.append(f"- {d['name']}: {d['reason']} "
                         f"(peak sleep-debt {d['peak_sleep_debt']}, meals {d['meals_eaten']})")
    else:
        lines.append("## Crew status: all adequately rested and fed across the window ✅")
    return "\n".join(lines) + "\n"


def run_day(start_hour: int, hours: int) -> dict:
    model = load_model()
    crew = load_crew()
    shifts = assign_shifts(crew, model)
    return simulate(shifts, crew, model, start_hour, hours)


def cmd_day(args) -> int:
    model = load_model()
    sim = run_day(args.start, args.hours)
    print(render_md(sim, model))
    return 0


def cmd_shifts(args) -> int:
    model = load_model()
    crew = load_crew()
    shifts = assign_shifts(crew, model)
    by_shift = defaultdict(list)
    for name, s in shifts.items():
        by_shift[s].append(name)
    for s in model["shifts"]:
        members = sorted(by_shift[s])
        print(f"{s} ({model['shifts'][s]['manning']}, {len(members)}): {', '.join(members)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    d = sub.add_parser("day"); d.add_argument("--start", type=int, default=6); d.add_argument("--hours", type=int, default=24)
    sub.add_parser("shifts")
    args = parser.parse_args()
    return {"day": cmd_day, "shifts": cmd_shifts}[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Compile an L2 scenario seed overlay into station-sim dynamics."""
# A generated watch fixture (``catalog/generated_watch_scenarios/``) carries a
# ``scenario_seed_overlay``: roles, pressure axes, and knobs. Without this module
# ``tools/hour_aboard.py`` ignored all three, so every fixture ran the same five
# task steps and every L3 audit came back ``supported``. This module turns the
# overlay into a deterministic *dynamics plan* that the harness feeds the
# CloudBank station sim:
#
# * **Knobs** are scored into six pressure channels (scarcity, opacity,
#   fragility, rigidity, imbalance, constraint). A range knob (``weak->totalizing``)
#   is sampled at a seed-chosen point along the range, and the dominant-solver
#   knob (``bureaucracy | violence | wealth``) picks one solver per seed. That is
#   the seed's ``knob_sweep_or_sensitivity_run`` freedom.
# * **Pressure axes** become per-hour pressure shocks. A shock either lands on an
#   open task and stalls it for that hour, or the station's institutions absorb
#   it. Coercive solvers escalate shocks once the decision path closes; other
#   solvers raise absorption.
# * **Roles** become role-position tasks the crew must hold before end-state
#   branching can close.
# * **Scarcity** diverts a share of the crew each hour to scarcity response.
#
# After the run, :func:`derive_l3_audit` turns what actually happened (stalls,
# absorptions, the ethics gate, the solver) into pressures for the L3 narrative
# audit, so its verdict follows the run instead of a fixed input.
#
# Everything is deterministic per ``(card_id, seed)``: all randomness comes from
# ``random.Random`` seeded with a string, which does not depend on
# ``PYTHONHASHSEED``. Nothing here reads or writes the station clock. Expected
# end states stay observation categories; this module never picks an ending.

from __future__ import annotations

import random
import re
from typing import Any, Dict, List, Optional, Tuple

SCHEMA = "aurora.scenario_seed_dynamics/v1"

# Knob name keyword -> channel. Intensity is always "how much pressure this
# knob setting puts on the crew" (0 = calm, 1 = severe), so each channel has
# its own lexicon: "public" is calm for transparency, "strong" is calm for
# institutions but harsh for norm enforcement.
KNOB_CHANNELS: Tuple[Tuple[str, str], ...] = (
    ("scarcity", "scarcity"),
    ("transparency", "opacity"),
    ("institution", "fragility"),
    ("norm", "rigidity"),
    ("power", "imbalance"),
    ("mobility", "constraint"),
)
SOLVER_KEYWORD = "solver"
NEUTRAL = 0.5

LEXICON: Dict[str, Dict[str, float]] = {
    "scarcity": {
        "desperate": 0.95, "acute": 0.9, "rises": 0.75, "high": 0.8, "strained": 0.6,
        "strategic": 0.55, "medium": 0.5, "moderate": 0.45, "low": 0.25, "abundant": 0.1,
    },
    "opacity": {
        "hidden": 0.85, "secret": 0.85,  # nosec B105 - lexicon word, not a credential
        "tabooed": 0.75, "controlled": 0.75, "sanitized": 0.7,
        "rumor": 0.7, "need-to-know": 0.6, "mixed": 0.5, "cute": 0.6, "forced": 0.45,
        "disclosure": 0.4, "plural": 0.3, "traceable": 0.25, "public": 0.2, "open": 0.2,
    },
    "fragility": {
        "captured": 0.85, "weak": 0.8, "hollow": 0.8, "brittle": 0.75, "rotten": 0.75,
        "loopholes": 0.7, "new": 0.7, "cult": 0.75, "totalizing": 0.65, "irrelevant": 0.6,
        "critical": 0.5, "moderate": 0.45, "strong": 0.3, "guardrails": 0.25, "resilient": 0.2,
    },
    "rigidity": {
        "panic": 0.9, "mob": 0.9, "purges": 0.9, "taboo": 0.85, "taboo-driven": 0.85,
        "emergency": 0.8, "high": 0.7, "strong": 0.65, "mixed": 0.5, "emergent": 0.45,
        "procedural": 0.4, "pragmatic": 0.35, "low": 0.3,
    },
    "imbalance": {
        "dominant": 0.75, "fragmented": 0.7, "contested": 0.7, "uneven": 0.65, "shifting": 0.6,
        "unknown": 0.6, "rare": 0.55, "balanced": 0.25, "even": 0.25,
    },
    "constraint": {
        "takeover": 0.9, "stranded": 0.85, "low": 0.8, "constrained": 0.75, "contained": 0.7,
        "cascade": 0.7, "capture": 0.65, "mobilization": 0.6, "local": 0.55, "localized": 0.55,
        "medium": 0.5, "circulation": 0.5, "migratory": 0.4, "globalized": 0.35, "fluid": 0.3,
    },
}

# Solvers that resolve pressure by force or by controlling information. They
# close the decision path faster in fiction but escalate pressure afterwards.
COERCIVE_SOLVERS = frozenset(
    {
        "violence", "force", "coercion", "censorship", "purge", "propaganda", "secrecy",
        "containment", "exile", "power", "schism",
    }
)

POLE_SPLIT = re.compile(r"\s+vs\.?\s+|\s*/\s*|\s*;\s*|\s+or\s+|\s+but\s+")
RANGE_SPLIT = re.compile(r"\s*->\s*")
PARENS = re.compile(r"\([^)]*\)")
WORD = re.compile(r"[a-z][a-z-]*")


def _rng(card_id: str, seed: int, stream: str) -> random.Random:
    return random.Random(f"{card_id}:{seed}:{stream}")  # noqa: S311 # nosec B311 - deterministic sim, not crypto


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def channel_for(knob_name: str) -> Optional[str]:
    name = knob_name.lower()
    if SOLVER_KEYWORD in name:
        return None
    for keyword, channel in KNOB_CHANNELS:
        if keyword in name:
            return channel
    return "volatility"


def _word_score(word: str, lexicon: Dict[str, float]) -> Optional[float]:
    if word in lexicon:
        return lexicon[word]
    for key, value in lexicon.items():
        # "institution-dominant", "handler-dominant", "taboo-driven"
        if word.endswith("-" + key) or word.startswith(key + "-"):
            return value
    return None


def score_pole(text: str, channel: str) -> float:
    """Mean lexicon intensity of the words in one pole; neutral when none match."""
    lexicon = LEXICON.get(channel, {})
    scores = [s for s in (_word_score(w, lexicon) for w in WORD.findall(text.lower())) if s is not None]
    return round(sum(scores) / len(scores), 4) if scores else NEUTRAL


def score_stage(text: str, channel: str) -> float:
    """A stage with several poles (``a vs b vs c``) is contested: mean plus a contention bump."""
    poles = [p for p in POLE_SPLIT.split(PARENS.sub(" ", text)) if p.strip()]
    if not poles:
        return NEUTRAL
    base = sum(score_pole(p, channel) for p in poles) / len(poles)
    return round(_clamp(base + 0.05 * (len(poles) - 1)), 4)


def score_knob(value: str, channel: str, rng: random.Random) -> Dict[str, Any]:
    """Score a knob; a range (``a -> b``) is sampled at a seed-chosen position."""
    stages = [s for s in RANGE_SPLIT.split(value) if s.strip()]
    if len(stages) <= 1:
        return {"intensity": score_stage(value, channel), "position": None, "stage": value.strip()}
    position = round(rng.random(), 4)
    scaled = position * (len(stages) - 1)
    index = min(int(scaled), len(stages) - 2)
    frac = scaled - index
    low, high = score_stage(stages[index], channel), score_stage(stages[index + 1], channel)
    nearest = stages[index] if frac < 0.5 else stages[index + 1]
    return {"intensity": round(low + (high - low) * frac, 4), "position": position, "stage": nearest.strip()}


def pick_solver(value: str, rng: random.Random) -> Dict[str, Any]:
    options = [o.strip() for o in value.split("|") if o.strip()] or [value.strip()]
    selected = rng.choice(options)
    words = set(WORD.findall(selected.lower()))
    return {"options": options, "selected": selected, "coercive": bool(words & COERCIVE_SOLVERS)}


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _tagged(tasks: List[Dict[str, Any]], tag: str) -> List[str]:
    return [t["id"] for t in tasks if tag in t.get("tags", [])]


def role_tasks(card_id: str, overlay: Dict[str, Any], tasks: List[Dict[str, Any]],
               channels: Dict[str, float]) -> List[Dict[str, Any]]:
    """One role-position task per seed role, after role mapping, before branching."""
    mapping = _tagged(tasks, "roles") or [tasks[0]["id"]]
    axes = list(overlay.get("pressure", []))
    hours = round(0.5 + 0.5 * channels.get("imbalance", NEUTRAL), 2)
    out = []
    for index, role in enumerate(overlay.get("roles", []), start=1):
        axis = axes[(index - 1) % len(axes)] if axes else "pressure"
        out.append(
            {
                "id": f"{card_id}-R{index}",
                "name": f"Hold the {role} position under {axis} pressure",
                "hours": hours,
                "tags": ["seed_role", "role_position", _slug(role), _slug(axis)],
                "source": f"catalog/l2_scenario_seed_catalog.json#/cards/{card_id}",
                "depends_on": list(mapping),
            }
        )
    return out


def _score_knobs(knob_map: Dict[str, str], rng: random.Random) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, float]]:
    """Score every knob; return (per-knob detail, dominant solver, channel means)."""
    knobs: Dict[str, Dict[str, Any]] = {}
    solver: Dict[str, Any] = {"options": [], "selected": "", "coercive": False}
    buckets: Dict[str, List[float]] = {}
    for name in sorted(knob_map):
        raw = knob_map[name]
        channel = channel_for(name)
        if channel is None:
            solver = pick_solver(raw, rng)
            knobs[name] = {"raw": raw, "channel": "solver", "selected": solver["selected"]}
            continue
        scored = score_knob(raw, channel, rng)
        knobs[name] = {"raw": raw, "channel": channel, **scored}
        buckets.setdefault(channel, []).append(scored["intensity"])
    channels = {c: round(sum(v) / len(v), 4) for c, v in sorted(buckets.items())}
    return knobs, solver, channels


def _pressure_axes(pressure: List[str], volatility: float, coercive: bool) -> List[Dict[str, Any]]:
    shock_rate = _clamp(0.12 + 0.45 * volatility + (0.08 if coercive else 0.0), 0.05, 0.85)
    # Later axes in the card are secondary pressures; they fire a little less.
    return [
        {"axis": axis, "shock_rate": round(_clamp(shock_rate * (1.0 - 0.1 * i), 0.05, 0.85), 4)}
        for i, axis in enumerate(pressure)
    ]


def compile_plan(fixture: Dict[str, Any], seed: int) -> Dict[str, Any]:
    """Build the dynamics plan for ``fixture`` at ``seed``. Pure and deterministic."""
    overlay = fixture["scenario_seed_overlay"]
    card_id = fixture["source_scenario_seed"]["card_id"]
    knobs, solver, channels = _score_knobs(overlay.get("knobs", {}), _rng(card_id, seed, "knobs"))
    volatility = round(sum(channels.values()) / len(channels), 4) if channels else NEUTRAL
    coercive = bool(solver["coercive"])
    return {
        "schema": SCHEMA,
        "card_id": card_id,
        "seed": int(seed),
        "knobs": knobs,
        "channels": channels,
        "volatility": volatility,
        "dominant_solver": solver,
        "pressure_axes": _pressure_axes(list(overlay.get("pressure", [])), volatility, coercive),
        "absorb_rate": round(_clamp(0.75 - 0.6 * channels.get("fragility", NEUTRAL), 0.1, 0.9), 4),
        "shock_drag": round(_clamp(0.95 - 0.25 * channels.get("rigidity", NEUTRAL), 0.6, 0.95), 4),
        "escalation": {
            "after_tag": "decision_path",
            "shock_rate_delta": 0.15 if coercive else 0.0,
            "absorb_rate_delta": 0.0 if coercive else 0.1,
        },
        "crew_diversion_rate": round(_clamp(0.6 * channels.get("scarcity", NEUTRAL), 0.0, 0.6), 4),
        "role_tasks": role_tasks(card_id, overlay, list(fixture.get("tasks", [])), channels),
        "rng_stream": f"{card_id}:{seed}:shocks",
    }


def apply_plan(scenario: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Attach a dynamics plan to a fixture scenario in place (after the hour clock ran)."""
    # Adds the role-position tasks, makes end-state branching wait on them, and
    # stores the plan under scenario["seed_dynamics"]. Scenarios without a
    # scenario_seed_overlay are left untouched and None is returned.
    if not scenario.get("scenario_seed_overlay") or not scenario.get("source_scenario_seed"):
        return None
    plan = compile_plan(scenario, int(scenario["seed"]))
    role_ids = [t["id"] for t in plan["role_tasks"]]
    tasks = []
    for task in scenario["tasks"]:
        task = dict(task)
        if "outcome" in task.get("tags", []):
            deps = list(task.get("depends_on", []))
            task["depends_on"] = deps + [r for r in role_ids if r not in deps]
        tasks.append(task)
    scenario["tasks"] = tasks + plan["role_tasks"]
    scenario["seed_dynamics"] = plan
    return plan


def _axis_outcomes(plan: Dict[str, Any], run: Dict[str, Any], completed: set) -> Dict[str, Dict[str, int]]:
    """Per axis: shocks absorbed, stalls recovered (task closed later), stalls left open."""
    out = {a["axis"]: {"absorbed": 0, "recovered": 0, "open": 0} for a in plan.get("pressure_axes", [])}
    for shock in run.get("shocks", []):
        bucket = out.setdefault(shock["axis"], {"absorbed": 0, "recovered": 0, "open": 0})
        if shock["absorbed"]:
            bucket["absorbed"] += 1
        elif shock["task"] in completed:
            bucket["recovered"] += 1
        else:
            bucket["open"] += 1
    return out


def _axis_pressures(plan: Dict[str, Any], run: Dict[str, Any], completed: set) -> List[Dict[str, Any]]:
    out = []
    for axis, counts in _axis_outcomes(plan, run, completed).items():
        if counts["open"]:
            out.append({"label": f"{axis} pressure left {counts['open']} stalled task(s) open at watch close",
                        "direction": "against", "strength": round(min(1.0, 0.4 + 0.2 * counts["open"]), 2)})
        else:
            out.append({"label": f"{axis} pressure carried by the watch "
                                 f"({counts['absorbed']} absorbed, {counts['recovered']} stall(s) recovered)",
                        "direction": "toward", "strength": 0.6})
    return out


def _ethics_pressure(tasks: List[Dict[str, Any]], completed: set) -> List[Dict[str, Any]]:
    ethics = _tagged(tasks, "ethics")
    if not ethics:
        return []
    if all(t in completed for t in ethics):
        return [{"label": "duty to the charter", "direction": "toward", "strength": 0.9}]
    return [{"label": "ethics gate left open at watch close", "direction": "against", "strength": 0.9}]


def _role_pressure(plan: Dict[str, Any], completed: set) -> List[Dict[str, Any]]:
    role_ids = [t["id"] for t in plan.get("role_tasks", [])]
    unheld = [r for r in role_ids if r not in completed]
    if not unheld:
        return []
    return [{"label": f"{len(unheld)}/{len(role_ids)} seed role positions unrepresented at closeout",
             "direction": "against", "strength": round(min(1.0, 0.3 + 0.1 * len(unheld)), 2)}]


def _solver_pressure(solver: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not solver.get("coercive"):
        return []
    return [{"label": f"consent strained by {solver['selected']} as dominant solver",
             "direction": "against", "strength": 0.7}]


def derive_l3_audit(audit: Dict[str, Any], plan: Optional[Dict[str, Any]], sim: Dict[str, Any],
                    tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Return an L3 audit payload whose pressures come from what the run actually did."""
    # * an axis whose stall left a task open at watch close pulls against the closeout;
    # * an axis the station absorbed, recovered from, or never landed pulls toward it;
    # * the ethics gate closing gives the charter-duty pressure, missing it pulls against;
    # * seed roles whose positions were never held leave stakeholders unrepresented;
    # * a coercive dominant solver strains consent.
    if not plan:
        return dict(audit)
    run = sim.get("seed_dynamics", {})
    completed = set(sim.get("summary", {}).get("completed_ids", []))
    solver = plan.get("dominant_solver", {})
    pressures = (
        _axis_pressures(plan, run, completed)
        + _ethics_pressure(tasks, completed)
        + _role_pressure(plan, completed)
        + _solver_pressure(solver)
    )
    stalls = sum(1 for s in run.get("shocks", []) if not s["absorbed"])
    closed = len(completed & {t["id"] for t in tasks})
    action = (
        f"{audit['action']}; dominant solver {solver.get('selected') or 'unset'}; "
        f"{closed}/{len(tasks)} tasks closed under {stalls} pressure stall(s)"
    )
    notes = [
        f"Seed {plan['seed']} sampled volatility {plan['volatility']} across {len(plan['channels'])} channels.",
        f"{len(plan['role_tasks'])} seed roles held as role positions; "
        f"{len(set(run.get('role_tasks_completed', [])))} closed.",
    ]
    return {**audit, "action": action, "pressures": pressures, "continuity_notes": notes}


def run_signature(observations: Dict[str, Any]) -> Tuple[Any, ...]:
    """A compact signature for telling runs apart in a suite summary."""
    dyn = observations.get("seed_dynamics") or {}
    return (
        observations.get("tasks_completed"),
        observations.get("l3_verdict"),
        dyn.get("dominant_solver"),
        dyn.get("pressure_stalls"),
        dyn.get("pressure_absorbed"),
    )

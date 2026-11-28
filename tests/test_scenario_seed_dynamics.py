"""Seed dynamics: L2 scenario seed roles, pressures and knobs drive the station sim.

These are CloudBank-independent unit tests (they run on the 3.9 subset too).
The end-to-end suite checks live in tests/test_l2_scenario_fixtures.py.
"""

from __future__ import annotations

import copy
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import scenario_seed_dynamics as sd  # noqa: E402

FIXTURE_DIR = ROOT / "catalog" / "generated_watch_scenarios"
MANIFEST = json.loads((FIXTURE_DIR / "index.json").read_text(encoding="utf-8"))


def _rng(seed):
    return random.Random(seed)  # noqa: S311 # nosec B311 - deterministic test seed


def _fixtures():
    return [json.loads((ROOT / row["path"]).read_text(encoding="utf-8")) for row in MANIFEST["fixtures"]]


def _fixture(card_id):
    return next(f for f in _fixtures() if f["source_scenario_seed"]["card_id"] == card_id)


def test_knob_channels_cover_every_fixture_knob():
    for fixture in _fixtures():
        for name in fixture["scenario_seed_overlay"]["knobs"]:
            assert sd.channel_for(name) in {None, "scarcity", "opacity", "fragility", "rigidity", "imbalance",
                                            "constraint"}, name


def test_knob_lexicon_orders_settings_by_pressure():
    rng = _rng(0)
    assert sd.score_knob("desperate", "scarcity", rng)["intensity"] > sd.score_knob("strained", "scarcity", rng)[
        "intensity"]
    assert sd.score_knob("hidden", "opacity", rng)["intensity"] > sd.score_knob("public", "opacity", rng)["intensity"]
    assert sd.score_knob("weak", "fragility", rng)["intensity"] > sd.score_knob("strong", "fragility", rng)[
        "intensity"]
    # Parenthetical notes do not move the score; contested poles add pressure.
    assert sd.score_stage("constrained (custody)", "constraint") == sd.score_stage("constrained", "constraint")
    assert sd.score_stage("a vs b vs c", "imbalance") > sd.NEUTRAL


def test_range_knobs_sweep_with_the_seed():
    positions = {sd.score_knob("weak->totalizing", "fragility", _rng(s))["position"] for s in range(20)}
    assert len(positions) > 10
    for s in range(20):
        scored = sd.score_knob("weak->totalizing", "fragility", _rng(s))
        assert 0.65 <= scored["intensity"] <= 0.8


def test_dominant_solver_is_one_of_the_card_options():
    fixture = _fixture("SCN-0002")
    options = [o.strip() for o in fixture["scenario_seed_overlay"]["knobs"]["Dominant solver"].split("|")]
    seen = set()
    for seed in range(30):
        solver = sd.compile_plan(fixture, seed)["dominant_solver"]
        assert solver["selected"] in options
        assert solver["coercive"] == (solver["selected"] == "violence")
        seen.add(solver["selected"])
    assert seen == set(options), "seed sweep should reach every solver option"


def test_plan_is_deterministic_per_seed_and_varies_across_seeds():
    fixture = _fixture("SCN-0903")
    assert sd.compile_plan(fixture, 903) == sd.compile_plan(copy.deepcopy(fixture), 903)
    plans = [json.dumps(sd.compile_plan(fixture, seed), sort_keys=True) for seed in range(903, 913)]
    assert len(set(plans)) > 5


def test_plans_differ_across_fixtures():
    plans = {f["name"]: sd.compile_plan(f, f["seed"]) for f in _fixtures()}
    signatures = {(p["volatility"], p["dominant_solver"]["selected"], p["absorb_rate"]) for p in plans.values()}
    assert len(signatures) >= 20
    for name, plan in plans.items():
        fixture = next(f for f in _fixtures() if f["name"] == name)
        overlay = fixture["scenario_seed_overlay"]
        assert [a["axis"] for a in plan["pressure_axes"]] == overlay["pressure"]
        assert len(plan["role_tasks"]) == len(overlay["roles"])
        assert 0.05 <= min(a["shock_rate"] for a in plan["pressure_axes"])
        assert max(a["shock_rate"] for a in plan["pressure_axes"]) <= 0.85


def test_apply_plan_wires_role_positions_before_branching():
    scenario = copy.deepcopy(_fixture("SCN-0002"))
    plan = sd.apply_plan(scenario)
    role_ids = [t["id"] for t in plan["role_tasks"]]
    by_id = {t["id"]: t for t in scenario["tasks"]}
    assert role_ids == [f"SCN-0002-R{i}" for i in range(1, 6)]
    assert set(role_ids) <= set(by_id)
    mapping = next(t["id"] for t in scenario["tasks"] if "roles" in t["tags"])
    for rid in role_ids:
        assert by_id[rid]["depends_on"] == [mapping]
    branching = next(t for t in scenario["tasks"] if "outcome" in t["tags"])
    assert set(role_ids) <= set(branching["depends_on"])
    assert scenario["seed_dynamics"] is plan
    # The committed fixture file itself is never modified.
    assert len(_fixture("SCN-0002")["tasks"]) == 5


def test_apply_plan_is_a_no_op_for_plain_scenarios():
    scenario = json.loads((ROOT / "catalog" / "hour_aboard_scenario.json").read_text(encoding="utf-8"))
    before = copy.deepcopy(scenario)
    assert sd.apply_plan(scenario) is None
    assert scenario == before


def test_plan_never_picks_an_ending():
    for fixture in _fixtures():
        text = json.dumps(sd.compile_plan(fixture, fixture["seed"]))
        for category in fixture["scenario_seed_overlay"]["expected_end_state_categories"]:
            assert category not in text
        for key in ("forced_winner", "scripted_outcome", "required_ending", "canonical_outcome"):
            assert key not in text


def _sim(completed, shocks, solver="diplomacy"):
    return {
        "summary": {"completed_ids": sorted(completed)},
        "seed_dynamics": {"shocks": shocks, "role_tasks_completed": [c for c in completed if "-R" in c],
                          "dominant_solver": solver},
    }


def _audit_inputs(card="SCN-0002", seed=2):
    scenario = copy.deepcopy(_fixture(card))
    scenario["seed"] = seed
    plan = sd.apply_plan(scenario)
    return scenario, plan


def test_l3_audit_follows_the_run():
    scenario, plan = _audit_inputs()
    all_ids = {t["id"] for t in scenario["tasks"]}
    plan["dominant_solver"] = {"options": ["bureaucracy"], "selected": "bureaucracy", "coercive": False}

    calm = sd.derive_l3_audit(scenario["l3_audit"], plan, _sim(all_ids, []), scenario["tasks"])
    assert {p["direction"] for p in calm["pressures"]} == {"toward"}
    assert any(p["label"] == "duty to the charter" for p in calm["pressures"])

    ethics = next(t["id"] for t in scenario["tasks"] if "ethics" in t["tags"])
    stalled = [{"tick": 2, "axis": "reputation", "task": ethics, "absorbed": False}]
    rough = sd.derive_l3_audit(scenario["l3_audit"], plan, _sim({"SCN-0002-T1"}, stalled), scenario["tasks"])
    against = [p["label"] for p in rough["pressures"] if p["direction"] == "against"]
    assert any("reputation" in label for label in against)
    assert "ethics gate left open at watch close" in against
    assert any("role positions unrepresented" in label for label in against)
    assert "1/" in rough["action"] and "1 pressure stall" in rough["action"]


def test_l3_audit_counts_recovered_stalls_as_carried():
    scenario, plan = _audit_inputs()
    all_ids = {t["id"] for t in scenario["tasks"]}
    plan["dominant_solver"] = {"options": ["wealth"], "selected": "wealth", "coercive": False}
    shocks = [{"tick": 0, "axis": "jurisdiction", "task": "SCN-0002-T1", "absorbed": False}]
    audit = sd.derive_l3_audit(scenario["l3_audit"], plan, _sim(all_ids, shocks), scenario["tasks"])
    juris = next(p for p in audit["pressures"] if p["label"].startswith("jurisdiction"))
    assert juris["direction"] == "toward" and "1 stall(s) recovered" in juris["label"]


def test_coercive_solver_strains_consent():
    scenario, plan = _audit_inputs()
    all_ids = {t["id"] for t in scenario["tasks"]}
    plan["dominant_solver"] = {"options": ["violence"], "selected": "violence", "coercive": True}
    audit = sd.derive_l3_audit(scenario["l3_audit"], plan, _sim(all_ids, [], "violence"), scenario["tasks"])
    assert {"label": "consent strained by violence as dominant solver", "direction": "against",
            "strength": 0.7} in audit["pressures"]


def test_l3_audit_passthrough_without_plan():
    audit = {"actor": "x", "action": "y"}
    assert sd.derive_l3_audit(audit, None, {}, []) == audit


def test_compile_plan_does_not_touch_station_state(tmp_path, monkeypatch):
    state = ROOT / "catalog" / "station_state.json"
    before = state.read_text() if state.exists() else None
    monkeypatch.chdir(tmp_path)
    for fixture in _fixtures():
        sd.apply_plan(copy.deepcopy(fixture))
    assert (state.read_text() if state.exists() else None) == before
    assert list(tmp_path.iterdir()) == []

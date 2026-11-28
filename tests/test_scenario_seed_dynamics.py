"""Seed dynamics: L2 scenario seed roles, pressures and knobs drive the station sim."""

# CloudBank-independent unit tests (they run on the 3.9 subset too). The
# end-to-end suite checks live in tests/test_l2_scenario_fixtures.py.

from __future__ import annotations

import copy
import json
import random
import sys
from pathlib import Path
from unittest import TestCase

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import scenario_seed_dynamics as sd  # noqa: E402

CHECK = TestCase()
FIXTURE_DIR = ROOT / "catalog" / "generated_watch_scenarios"
MANIFEST = json.loads((FIXTURE_DIR / "index.json").read_text(encoding="utf-8"))
CHANNELS = {None, "scarcity", "opacity", "fragility", "rigidity", "imbalance", "constraint"}


def _rng(seed):
    return random.Random(seed)  # noqa: S311 # nosec B311 - deterministic test seed


def _fixtures():
    return [json.loads((ROOT / row["path"]).read_text(encoding="utf-8")) for row in MANIFEST["fixtures"]]


def _fixture(card_id):
    return next(f for f in _fixtures() if f["source_scenario_seed"]["card_id"] == card_id)


def _intensity(value, channel):
    return sd.score_knob(value, channel, _rng(0))["intensity"]


def test_knob_channels_cover_every_fixture_knob():
    names = {name for f in _fixtures() for name in f["scenario_seed_overlay"]["knobs"]}
    CHECK.assertTrue({sd.channel_for(n) for n in names} <= CHANNELS)


def test_knob_lexicon_orders_settings_by_pressure():
    CHECK.assertGreater(_intensity("desperate", "scarcity"), _intensity("strained", "scarcity"))
    CHECK.assertGreater(_intensity("hidden", "opacity"), _intensity("public", "opacity"))
    CHECK.assertGreater(_intensity("weak", "fragility"), _intensity("strong", "fragility"))


def test_parentheticals_ignored_and_contested_poles_add_pressure():
    CHECK.assertEqual(sd.score_stage("constrained (custody)", "constraint"), sd.score_stage("constrained", "constraint"))
    CHECK.assertGreater(sd.score_stage("a vs b vs c", "imbalance"), sd.NEUTRAL)


def test_range_knobs_sweep_with_the_seed():
    scored = [sd.score_knob("weak->totalizing", "fragility", _rng(s)) for s in range(20)]
    CHECK.assertGreater(len({k["position"] for k in scored}), 10)
    CHECK.assertTrue(all(0.65 <= k["intensity"] <= 0.8 for k in scored))


def test_dominant_solver_is_one_of_the_card_options():
    fixture = _fixture("SCN-0002")
    options = [o.strip() for o in fixture["scenario_seed_overlay"]["knobs"]["Dominant solver"].split("|")]
    solvers = [sd.compile_plan(fixture, seed)["dominant_solver"] for seed in range(30)]
    CHECK.assertEqual({s["selected"] for s in solvers}, set(options), "seed sweep should reach every option")
    CHECK.assertTrue(all(s["coercive"] == (s["selected"] == "violence") for s in solvers))


def test_plan_is_deterministic_per_seed_and_varies_across_seeds():
    fixture = _fixture("SCN-0903")
    CHECK.assertEqual(sd.compile_plan(fixture, 903), sd.compile_plan(copy.deepcopy(fixture), 903))
    plans = {json.dumps(sd.compile_plan(fixture, seed), sort_keys=True) for seed in range(903, 913)}
    CHECK.assertGreater(len(plans), 5)


def test_plans_differ_across_fixtures():
    plans = [sd.compile_plan(f, f["seed"]) for f in _fixtures()]
    signatures = {(p["volatility"], p["dominant_solver"]["selected"], p["absorb_rate"]) for p in plans}
    CHECK.assertGreaterEqual(len(signatures), 20)


def test_plan_mirrors_each_overlay():
    for fixture in _fixtures():
        plan = sd.compile_plan(fixture, fixture["seed"])
        overlay = fixture["scenario_seed_overlay"]
        rates = [a["shock_rate"] for a in plan["pressure_axes"]]
        CHECK.assertEqual([a["axis"] for a in plan["pressure_axes"]], overlay["pressure"])
        CHECK.assertEqual(len(plan["role_tasks"]), len(overlay["roles"]))
        CHECK.assertTrue(0.05 <= min(rates) and max(rates) <= 0.85, rates)


def test_apply_plan_adds_role_positions_after_role_mapping():
    scenario = copy.deepcopy(_fixture("SCN-0002"))
    plan = sd.apply_plan(scenario)
    role_ids = [t["id"] for t in plan["role_tasks"]]
    by_id = {t["id"]: t for t in scenario["tasks"]}
    mapping = next(t["id"] for t in scenario["tasks"] if "roles" in t["tags"])
    CHECK.assertEqual(role_ids, [f"SCN-0002-R{i}" for i in range(1, 6)])
    CHECK.assertEqual([by_id[r]["depends_on"] for r in role_ids], [[mapping]] * 5)
    CHECK.assertIs(scenario["seed_dynamics"], plan)


def test_apply_plan_makes_branching_wait_on_roles_without_touching_the_fixture():
    scenario = copy.deepcopy(_fixture("SCN-0002"))
    plan = sd.apply_plan(scenario)
    branching = next(t for t in scenario["tasks"] if "outcome" in t["tags"])
    CHECK.assertTrue({t["id"] for t in plan["role_tasks"]} <= set(branching["depends_on"]))
    CHECK.assertEqual(len(_fixture("SCN-0002")["tasks"]), 5)


def test_apply_plan_is_a_no_op_for_plain_scenarios():
    scenario = json.loads((ROOT / "catalog" / "hour_aboard_scenario.json").read_text(encoding="utf-8"))
    before = copy.deepcopy(scenario)
    CHECK.assertIsNone(sd.apply_plan(scenario))
    CHECK.assertEqual(scenario, before)


def test_plan_never_picks_an_ending():
    banned = ("forced_winner", "scripted_outcome", "required_ending", "canonical_outcome")
    for fixture in _fixtures():
        text = json.dumps(sd.compile_plan(fixture, fixture["seed"]))
        categories = fixture["scenario_seed_overlay"]["expected_end_state_categories"]
        CHECK.assertEqual([c for c in categories if c in text], [], fixture["name"])
        CHECK.assertEqual([k for k in banned if k in text], [], fixture["name"])


def _sim(completed, shocks, solver="diplomacy"):
    return {
        "summary": {"completed_ids": sorted(completed)},
        "seed_dynamics": {"shocks": shocks, "role_tasks_completed": [c for c in completed if "-R" in c],
                          "dominant_solver": solver},
    }


def _audit_inputs(solver, coercive=False):
    scenario = copy.deepcopy(_fixture("SCN-0002"))
    plan = sd.apply_plan(scenario)
    plan["dominant_solver"] = {"options": [solver], "selected": solver, "coercive": coercive}
    return scenario, plan, {t["id"] for t in scenario["tasks"]}


def _against(audit):
    return [p["label"] for p in audit["pressures"] if p["direction"] == "against"]


def test_l3_audit_calm_run_pulls_toward_the_closeout():
    scenario, plan, all_ids = _audit_inputs("bureaucracy")
    audit = sd.derive_l3_audit(scenario["l3_audit"], plan, _sim(all_ids, []), scenario["tasks"])
    CHECK.assertEqual({p["direction"] for p in audit["pressures"]}, {"toward"})
    CHECK.assertIn("duty to the charter", [p["label"] for p in audit["pressures"]])


def test_l3_audit_rough_run_pulls_against_the_closeout():
    scenario, plan, _ = _audit_inputs("bureaucracy")
    ethics = next(t["id"] for t in scenario["tasks"] if "ethics" in t["tags"])
    stalled = [{"tick": 2, "axis": "reputation", "task": ethics, "absorbed": False}]
    audit = sd.derive_l3_audit(scenario["l3_audit"], plan, _sim({"SCN-0002-T1"}, stalled), scenario["tasks"])
    against = " | ".join(_against(audit))
    CHECK.assertIn("reputation pressure left 1 stalled task(s) open", against)
    CHECK.assertIn("ethics gate left open at watch close", against)
    CHECK.assertIn("role positions unrepresented", against)
    CHECK.assertIn("1/10 tasks closed under 1 pressure stall(s)", audit["action"])


def test_l3_audit_counts_recovered_stalls_as_carried():
    scenario, plan, all_ids = _audit_inputs("wealth")
    shocks = [{"tick": 0, "axis": "jurisdiction", "task": "SCN-0002-T1", "absorbed": False}]
    audit = sd.derive_l3_audit(scenario["l3_audit"], plan, _sim(all_ids, shocks), scenario["tasks"])
    juris = next(p for p in audit["pressures"] if p["label"].startswith("jurisdiction"))
    CHECK.assertEqual(juris["direction"], "toward")
    CHECK.assertIn("1 stall(s) recovered", juris["label"])


def test_coercive_solver_strains_consent():
    scenario, plan, all_ids = _audit_inputs("violence", coercive=True)
    audit = sd.derive_l3_audit(scenario["l3_audit"], plan, _sim(all_ids, [], "violence"), scenario["tasks"])
    CHECK.assertEqual(_against(audit), ["consent strained by violence as dominant solver"])


def test_l3_audit_passthrough_without_plan():
    audit = {"actor": "x", "action": "y"}
    CHECK.assertEqual(sd.derive_l3_audit(audit, None, {}, []), audit)


def test_compile_plan_does_not_touch_station_state(tmp_path, monkeypatch):
    state = ROOT / "catalog" / "station_state.json"
    before = state.read_text() if state.exists() else None
    monkeypatch.chdir(tmp_path)
    for fixture in _fixtures():
        sd.apply_plan(copy.deepcopy(fixture))
    CHECK.assertEqual(state.read_text() if state.exists() else None, before)
    CHECK.assertEqual(list(tmp_path.iterdir()), [])

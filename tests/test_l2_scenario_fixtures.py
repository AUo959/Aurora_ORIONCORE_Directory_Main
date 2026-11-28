"""Generated L2 scenario seed fixtures: contract shape, drift gate, and end-to-end runs."""

from __future__ import annotations

import copy
import json
import subprocess  # nosec B404 - runs this repo's own tools with fixed argv
import sys
from pathlib import Path
from unittest import TestCase

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import l2_scenario_fixture_generator as gen  # noqa: E402

CHECK = TestCase()
CATALOG = json.loads((ROOT / "catalog/l2_scenario_seed_catalog.json").read_text(encoding="utf-8"))
CONTRACT = json.loads(
    (ROOT / "catalog/contracts/l2_scenario_fixture_generator_contract_v1.json").read_text(encoding="utf-8")
)
FIXTURE_DIR = ROOT / "catalog" / "generated_watch_scenarios"
MANIFEST = json.loads((FIXTURE_DIR / "index.json").read_text(encoding="utf-8"))
DUNE_LANE = {"SCN-0101", "SCN-0102", "SCN-0103", "SCN-0104", "SCN-0105", "SCN-0106", "SCN-0107", "SCN-0108"}
V022_CARDS = {"SCN-0103", "SCN-0105", "SCN-0106", "SCN-0107", "SCN-0108"}
TOOLS = {
    "generator": ROOT / "tools" / "l2_scenario_fixture_generator.py",
    "runner": ROOT / "tools" / "l2_scenario_fixture_run.py",
}


def _run_tool(tool: str, *args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    argv = [sys.executable, str(TOOLS[tool]), *args]
    return subprocess.run(  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit # noqa: S603 # nosec B603
        argv, capture_output=True, text=True, cwd=cwd, timeout=900, check=False
    )


def _fixtures() -> list[dict]:
    return [json.loads((ROOT / row["path"]).read_text(encoding="utf-8")) for row in MANIFEST["fixtures"]]


def test_committed_fixtures_match_catalog():
    result = _run_tool("generator", "--check")
    CHECK.assertEqual(result.returncode, 0, result.stderr)


def test_every_shortlist_card_has_a_fixture():
    shortlist = {e["id"] for e in CATALOG["fixture_ready_shortlist"]}
    CHECK.assertEqual(len(shortlist), 25)
    CHECK.assertEqual({row["card_id"] for row in MANIFEST["fixtures"]}, shortlist)
    CHECK.assertEqual(MANIFEST["fixture_count"], 25)
    CHECK.assertEqual(len({row["fixture_id"] for row in MANIFEST["fixtures"]}), 25)


def test_fixtures_satisfy_generator_contract_shape():
    shape = CONTRACT["candidate_fixture_shape"]
    for fixture in _fixtures():
        CHECK.assertTrue(set(shape["required_top_level_keys"]) <= set(fixture), fixture["name"])
        CHECK.assertTrue(
            set(shape["source_scenario_seed_required_keys"]) <= set(fixture["source_scenario_seed"]), fixture["name"]
        )
        CHECK.assertGreaterEqual(len(fixture["tasks"]), 4)
        for task in fixture["tasks"]:
            CHECK.assertTrue(set(shape["task_required_keys"]) <= set(task), task.get("id"))
            CHECK.assertTrue(task["source"].startswith("catalog/l2_scenario_seed_catalog.json#/cards/"))


def test_fixtures_are_harness_runnable_shape():
    """Keys tools/hour_aboard.py reads must be present and well-formed."""
    for fixture in _fixtures():
        ids = {t["id"] for t in fixture["tasks"]}
        for task in fixture["tasks"]:
            CHECK.assertTrue(set(task.get("depends_on", [])) <= ids, task["id"])
        for key in ("question", "actor", "action", "motive", "knowledge", "event_label"):
            CHECK.assertTrue(fixture["l3_audit"][key], (fixture["name"], key))
        CHECK.assertTrue({"mission_id", "tool_name", "risk_level", "destination"} <= set(fixture["ord_mission"]))
        CHECK.assertEqual(len(fixture["companions"]), 6)
        CHECK.assertEqual(
            fixture["fixture_meta"]["harness_scenario_arg"], f"generated_watch_scenarios/{fixture['name']}"
        )


def test_seeds_stay_pressure_fields_not_scripts():
    for fixture in _fixtures():
        overlay = fixture["scenario_seed_overlay"]
        CHECK.assertGreaterEqual(len(overlay["roles"]), 4)
        CHECK.assertGreaterEqual(len(overlay["pressure"]), 2)
        CHECK.assertGreaterEqual(len(overlay["knobs"]), 5)
        CHECK.assertGreaterEqual(len(overlay["expected_end_state_categories"]), 3)
        CHECK.assertIn("not required endings", overlay["end_state_handling"])
        text = json.dumps(fixture)
        for key in ("forced_winner", "scripted_outcome", "single_required_ending", "canonical_outcome"):
            CHECK.assertNotIn(f'"{key}"', text)
        CHECK.assertIs(fixture["fixture_meta"]["boundary"]["writes_nested_repos"], False)


def test_dune_lineage_cards_keep_v022_provenance():
    by_card = {f["source_scenario_seed"]["card_id"]: f for f in _fixtures()}
    CHECK.assertTrue(DUNE_LANE & set(by_card), "thematic batch needs at least one SCN-010x card")
    for card_id in V022_CARDS:
        prov = by_card[card_id]["source_scenario_seed"]["lineage_provenance"]
        CHECK.assertEqual(prov["source_version"], "v0.2.2")


def test_contract_candidates_are_marked():
    for fixture in _fixtures():
        seed = fixture["source_scenario_seed"]
        if seed["fixture_status"] == "contract_candidate":
            CHECK.assertTrue(seed["emission_basis"].startswith("contract_candidate_emitted_by_owner_direction"))
        else:
            CHECK.assertEqual(seed["emission_basis"], "ready_candidate_with_runtime_fixture_lane")


def test_generation_fails_closed_on_unresolved_reference():
    catalog = copy.deepcopy(CATALOG)
    catalog["normalized_support_structures"]["wiring_links"].append(
        {"source_card_id": "SCN-0903", "status": "blocked", "normalized_refs": [{"id": "SCN-9999", "status": "unresolved_id"}]}
    )
    with pytest.raises(gen.FixtureGenerationError, match="unresolved"):
        gen.generate(catalog)


def test_generation_rejects_setting_lore():
    catalog = copy.deepcopy(CATALOG)
    catalog["fixture_ready_shortlist"][0]["fixture_blueprint"]["objective"] += " Control the melange trade."
    with pytest.raises(gen.FixtureGenerationError, match="lore"):
        gen.generate(catalog)


def test_generation_rejects_nested_output_path():
    catalog = copy.deepcopy(CATALOG)
    catalog["fixture_ready_shortlist"][0]["fixture_blueprint"]["candidate_output_path"] = (
        "GUMAS_SIM_2.5/CanonRec/canon/x.json"
    )
    with pytest.raises(gen.FixtureGenerationError, match="escapes"):
        gen.generate(catalog)


def test_check_reports_drift(tmp_path):
    fixtures, manifest = gen.generate(CATALOG)
    gen.write_outputs(fixtures, manifest, tmp_path, None, "2026-01-01")
    CHECK.assertEqual(gen.check_drift(fixtures, manifest, tmp_path), [])
    victim = next(tmp_path.glob("l2_scn_0903_*.json"))
    victim.write_text(victim.read_text().replace('"seed": 903', '"seed": 904'))
    (tmp_path / "l2_scn_9999_orphan_v1.json").write_text("{}\n")
    drift = gen.check_drift(fixtures, manifest, tmp_path)
    CHECK.assertTrue(any(d.startswith("stale:") for d in drift), drift)
    CHECK.assertIn("orphan: l2_scn_9999_orphan_v1.json", drift)


@pytest.mark.simulation
@pytest.mark.slow
def test_all_fixtures_run_end_to_end(tmp_path):
    """Every fixture runs through hour_aboard and CloudBank's seed initializer."""
    result = _run_tool("runner", "--all", "--no-summary", "--run-root", str(tmp_path))
    CHECK.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-800:])
    receipts = sorted(tmp_path.glob("*/fixture_run_receipt.json"))
    CHECK.assertEqual(len(receipts), 25)
    for path in receipts:
        receipt = json.loads(path.read_text())
        CHECK.assertEqual(receipt["status"], "pass", (receipt["card_id"], receipt["checks"]))
        CHECK.assertEqual(receipt["observations"]["tasks_completed"], receipt["observations"]["task_count"])
        CHECK.assertTrue(receipt["initializer"]["accepted"])
        CHECK.assertTrue(receipt["end_state_categories_open"], "end states must stay open categories")


@pytest.mark.simulation
@pytest.mark.slow
def test_fixture_runs_are_deterministic_and_leave_station_clock_alone(tmp_path):
    state = ROOT / "catalog" / "station_state.json"
    before = state.read_text() if state.exists() else None
    observations = []
    for run in ("a", "b"):
        result = _run_tool("runner", "--fixture", "SCN-0903", "--run-root", str(tmp_path / run))
        CHECK.assertEqual(result.returncode, 0, result.stderr[-800:])
        receipt = json.loads(next((tmp_path / run).glob("*/fixture_run_receipt.json")).read_text())
        observations.append(receipt["observations"])
    CHECK.assertEqual(observations[0], observations[1])
    CHECK.assertEqual(state.read_text() if state.exists() else None, before)


@pytest.mark.simulation
@pytest.mark.slow
def test_relative_run_root_from_outside_repo(tmp_path):
    """A relative --run-root resolves against the caller's cwd, not the repo."""
    result = _run_tool("runner", "--fixture", "SCN-0903", "--run-root", "runs", cwd=tmp_path)
    CHECK.assertEqual(result.returncode, 0, result.stdout[-800:] + result.stderr[-800:])
    CHECK.assertTrue(next((tmp_path / "runs").glob("*/fixture_run_receipt.json"), None))

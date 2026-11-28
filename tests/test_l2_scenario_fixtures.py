"""Generated L2 scenario seed fixtures: contract shape, drift gate, and end-to-end runs."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import l2_scenario_fixture_generator as gen  # noqa: E402

CATALOG = json.loads((ROOT / "catalog/l2_scenario_seed_catalog.json").read_text(encoding="utf-8"))
CONTRACT = json.loads(
    (ROOT / "catalog/contracts/l2_scenario_fixture_generator_contract_v1.json").read_text(encoding="utf-8")
)
FIXTURE_DIR = ROOT / "catalog" / "generated_watch_scenarios"
MANIFEST = json.loads((FIXTURE_DIR / "index.json").read_text(encoding="utf-8"))
DUNE_LANE = {"SCN-0101", "SCN-0102", "SCN-0103", "SCN-0104", "SCN-0105", "SCN-0106", "SCN-0107", "SCN-0108"}
V022_CARDS = {"SCN-0103", "SCN-0105", "SCN-0106", "SCN-0107", "SCN-0108"}


def _fixtures() -> list[dict]:
    return [json.loads((ROOT / row["path"]).read_text(encoding="utf-8")) for row in MANIFEST["fixtures"]]


def test_committed_fixtures_match_catalog():
    result = subprocess.run(  # noqa: S603 - fixed argv
        [sys.executable, str(ROOT / "tools/l2_scenario_fixture_generator.py"), "--check"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode == 0, result.stderr


def test_every_shortlist_card_has_a_fixture():
    shortlist = {e["id"] for e in CATALOG["fixture_ready_shortlist"]}
    assert len(shortlist) == 25
    assert {row["card_id"] for row in MANIFEST["fixtures"]} == shortlist
    assert MANIFEST["fixture_count"] == 25
    assert len({row["fixture_id"] for row in MANIFEST["fixtures"]}) == 25


def test_fixtures_satisfy_generator_contract_shape():
    shape = CONTRACT["candidate_fixture_shape"]
    for fixture in _fixtures():
        for key in shape["required_top_level_keys"]:
            assert key in fixture, (fixture["name"], key)
        for key in shape["source_scenario_seed_required_keys"]:
            assert key in fixture["source_scenario_seed"], (fixture["name"], key)
        assert len(fixture["tasks"]) >= 4
        for task in fixture["tasks"]:
            for key in shape["task_required_keys"]:
                assert key in task
            assert task["source"].startswith("catalog/l2_scenario_seed_catalog.json#/cards/")


def test_fixtures_are_harness_runnable_shape():
    """Keys tools/hour_aboard.py reads must be present and well-formed."""
    for fixture in _fixtures():
        ids = {t["id"] for t in fixture["tasks"]}
        for task in fixture["tasks"]:
            assert set(task.get("depends_on", [])) <= ids
        for key in ("question", "actor", "action", "motive", "knowledge", "event_label"):
            assert fixture["l3_audit"][key]
        assert {"mission_id", "tool_name", "risk_level", "destination"} <= set(fixture["ord_mission"])
        assert len(fixture["companions"]) == 6
        assert fixture["fixture_meta"]["harness_scenario_arg"] == f"generated_watch_scenarios/{fixture['name']}"


def test_seeds_stay_pressure_fields_not_scripts():
    for fixture in _fixtures():
        overlay = fixture["scenario_seed_overlay"]
        assert len(overlay["roles"]) >= 4
        assert len(overlay["pressure"]) >= 2
        assert len(overlay["knobs"]) >= 5
        assert len(overlay["expected_end_state_categories"]) >= 3
        assert "not required endings" in overlay["end_state_handling"]
        text = json.dumps(fixture)
        for key in ("forced_winner", "scripted_outcome", "single_required_ending", "canonical_outcome"):
            assert f'"{key}"' not in text
        assert fixture["fixture_meta"]["boundary"]["writes_nested_repos"] is False


def test_dune_lineage_cards_keep_v022_provenance():
    by_card = {f["source_scenario_seed"]["card_id"]: f for f in _fixtures()}
    assert DUNE_LANE & set(by_card), "thematic batch needs at least one SCN-010x card"
    for card_id in V022_CARDS:
        prov = by_card[card_id]["source_scenario_seed"]["lineage_provenance"]
        assert prov["source_version"] == "v0.2.2"


def test_contract_candidates_are_marked():
    for fixture in _fixtures():
        seed = fixture["source_scenario_seed"]
        if seed["fixture_status"] == "contract_candidate":
            assert seed["emission_basis"].startswith("contract_candidate_emitted_by_owner_direction")
        else:
            assert seed["emission_basis"] == "ready_candidate_with_runtime_fixture_lane"


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


def test_generation_rejects_nested_output_path(tmp_path):
    catalog = copy.deepcopy(CATALOG)
    catalog["fixture_ready_shortlist"][0]["fixture_blueprint"]["candidate_output_path"] = (
        "GUMAS_SIM_2.5/CanonRec/canon/x.json"
    )
    with pytest.raises(gen.FixtureGenerationError, match="escapes"):
        gen.generate(catalog)


def test_check_reports_drift(tmp_path):
    fixtures, manifest = gen.generate(CATALOG)
    gen.write_outputs(fixtures, manifest, tmp_path, None, "2026-01-01")
    assert gen.check_drift(fixtures, manifest, tmp_path) == []
    victim = next(tmp_path.glob("l2_scn_0903_*.json"))
    victim.write_text(victim.read_text().replace('"seed": 903', '"seed": 904'))
    (tmp_path / "l2_scn_9999_orphan_v1.json").write_text("{}\n")
    drift = gen.check_drift(fixtures, manifest, tmp_path)
    assert any(d.startswith("stale:") for d in drift)
    assert "orphan: l2_scn_9999_orphan_v1.json" in drift


@pytest.mark.simulation
@pytest.mark.slow
def test_all_fixtures_run_end_to_end(tmp_path):
    """Every fixture runs through hour_aboard and CloudBank's seed initializer."""
    result = subprocess.run(  # noqa: S603 - fixed argv
        [
            sys.executable,
            str(ROOT / "tools/l2_scenario_fixture_run.py"),
            "--all",
            "--no-summary",
            "--run-root",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=900,
    )
    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-800:]
    receipts = sorted(tmp_path.glob("*/fixture_run_receipt.json"))
    assert len(receipts) == 25
    for path in receipts:
        receipt = json.loads(path.read_text())
        assert receipt["status"] == "pass", (receipt["card_id"], receipt["checks"])
        assert receipt["observations"]["tasks_completed"] == receipt["observations"]["task_count"]
        assert receipt["initializer"]["accepted"]
        assert receipt["end_state_categories_open"], "end states must stay open categories"


@pytest.mark.simulation
@pytest.mark.slow
def test_fixture_runs_are_deterministic_and_leave_station_clock_alone(tmp_path):
    state = ROOT / "catalog" / "station_state.json"
    before = state.read_text() if state.exists() else None
    observations = []
    for run in ("a", "b"):
        subprocess.run(  # noqa: S603 - fixed argv
            [
                sys.executable,
                str(ROOT / "tools/l2_scenario_fixture_run.py"),
                "--fixture",
                "SCN-0903",
                "--run-root",
                str(tmp_path / run),
            ],
            check=True,
            capture_output=True,
            text=True,
            cwd=ROOT,
            timeout=600,
        )
        receipt = json.loads(next((tmp_path / run).glob("*/fixture_run_receipt.json")).read_text())
        observations.append(receipt["observations"])
    assert observations[0] == observations[1]
    assert (state.read_text() if state.exists() else None) == before

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import l2_scenario_seed_uptake as uptake  # noqa: E402


CATALOG_PATH = ROOT / "catalog/l2_scenario_seed_catalog.json"
CONTRACT_PATH = ROOT / "catalog/contracts/l2_scenario_seed_uptake_contract_v1.json"


def load_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


class L2ScenarioSeedUptakeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_json(CATALOG_PATH)
        self.contract = load_json(CONTRACT_PATH)

    def test_contract_declares_required_uptake_surfaces_and_boundaries(self) -> None:
        required = {
            "root_fixture_generator",
            "state_builder_evidence_envelope",
            "simulation_initializer",
            "ethics_gate",
            "narrative_renderer",
            "canon_promotion_gate",
        }
        self.assertEqual(set(self.contract["required_seed_consumers"]), required)
        surfaces = {
            surface["surface_id"]: surface
            for surface in self.contract["uptake_surfaces"]
        }
        self.assertEqual(set(surfaces), required)
        self.assertEqual(
            surfaces["canon_promotion_gate"]["mutation_boundary"],
            "no_direct_seed_to_canon",
        )
        for surface in surfaces.values():
            policy = surface["handoff_path_policy"]
            self.assertNotIn("writes are permitted", policy.lower())

    def test_all_shortlist_seeds_have_emergence_capacity(self) -> None:
        report = uptake.build_report(self.catalog, self.contract)
        self.assertEqual(report["status"], "valid")
        self.assertEqual(report["summary"]["selected_seed_count"], 25)
        self.assertEqual(report["summary"]["error_count"], 0)
        for packet in report["packets"]:
            metrics = packet["emergence_policy"]["metrics"]
            self.assertGreaterEqual(metrics["roles"], 4)
            self.assertGreaterEqual(metrics["pressure_axes"], 2)
            self.assertGreaterEqual(metrics["knob_axes"], 5)
            self.assertGreaterEqual(metrics["expected_end_state_categories"], 3)
            self.assertFalse(packet["boundary_assertions"]["writes_nested_repos"])

    def test_dune_lineage_packets_preserve_provenance_and_open_outcomes(self) -> None:
        dune_ids = ["SCN-0103", "SCN-0105", "SCN-0106", "SCN-0107", "SCN-0108"]
        report = uptake.build_report(self.catalog, self.contract, dune_ids)
        self.assertEqual(report["status"], "valid")
        self.assertEqual(report["summary"]["selected_seed_count"], 5)
        for packet in report["packets"]:
            provenance = packet["lineage_provenance"]
            self.assertEqual(provenance["source_version"], "v0.2.2")
            self.assertEqual(provenance["source_status"], "lineage_only_missing_from_v0_2_15")
            sim_payload = packet["consumer_payloads"]["simulation_initializer"]
            self.assertIn(
                "observation categories",
                sim_payload["expected_end_state_handling"],
            )
            self.assertEqual(
                packet["boundary_assertions"]["cloudbank_runtime_wiring"],
                "not_authorized_by_this_packet",
            )

    def test_cli_summary_for_first_fixture_candidates(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "tools/l2_scenario_seed_uptake.py",
                "--ids",
                "SCN-0903",
                "SCN-0708",
                "SCN-0805",
                "--summary",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "valid")
        self.assertEqual(payload["summary"]["selected_seed_count"], 3)
        self.assertEqual(payload["summary"]["required_consumer_count"], 6)

    def test_nested_output_paths_are_rejected(self) -> None:
        entry = json.loads(json.dumps(self.catalog["fixture_ready_shortlist"][0]))
        card = next(card for card in self.catalog["cards"] if card["id"] == entry["id"])
        entry["fixture_blueprint"]["candidate_output_path"] = (
            "GUMAS_SIM_2.5/Aurora_Sim_Architecture/"
            "aurora-cloudbank-symbolic-main/generated.json"
        )
        findings = uptake.assess_blueprint(entry, card, self.contract)
        self.assertIn("nested_output_path", {finding["code"] for finding in findings})


if __name__ == "__main__":
    unittest.main()

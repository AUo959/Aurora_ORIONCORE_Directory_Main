from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "catalog/l2_scenario_seed_catalog.json"
CONTRACT_PATH = ROOT / "catalog/contracts/l2_scenario_fixture_generator_contract_v1.json"
SCHEMA_PATH = ROOT / "catalog/schemas/l2_scenario_seed_catalog.schema.json"


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


class L2ScenarioSeedCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_json(CATALOG_PATH)
        self.contract = load_json(CONTRACT_PATH)

    def test_catalog_counts_and_status(self) -> None:
        self.assertEqual(self.catalog["artifact_id"], "AURORA_ROOT_L2_SCENARIO_SEED_CATALOG_v1")
        self.assertEqual(self.catalog["status"], "maintained_root_control_plane_artifact")
        self.assertEqual(len(self.catalog["cards"]), 87)
        self.assertEqual(self.catalog["summary"]["maintained_card_count"], 87)
        self.assertEqual(len(self.catalog["lineage_backup_cards"]), 5)
        self.assertEqual(self.catalog["summary"]["backup_only_lineage_card_count"], 5)
        self.assertEqual(
            self.catalog["authority_and_promotion"]["canon_status"],
            "not_promoted_to_CanonRec",
        )
        self.assertEqual(
            self.catalog["authority_and_promotion"]["runtime_status"],
            "not_wired_to_CloudBank_or_GUMAS_runtime",
        )

    def test_five_lineage_only_cards_remain_backup_only(self) -> None:
        expected_ids = {"SCN-0103", "SCN-0105", "SCN-0106", "SCN-0107", "SCN-0108"}
        backup_cards = self.catalog["lineage_backup_cards"]
        self.assertEqual({card["id"] for card in backup_cards}, expected_ids)
        for card in backup_cards:
            self.assertEqual(card["disposition"], "backup_only")
            self.assertEqual(card["integration_decision"], "backup_only")
            self.assertFalse(card["active_catalog_member"])
            self.assertIn("owner_review_required", card["restore_gate"])

    def test_required_fixture_candidates_are_ready(self) -> None:
        entries = {entry["id"]: entry for entry in self.catalog["fixture_ready_shortlist"]}
        for card_id in ("SCN-0903", "SCN-0708", "SCN-0805"):
            self.assertIn(card_id, entries)
            blueprint = entries[card_id]["fixture_blueprint"]
            self.assertEqual(blueprint["fixture_status"], "ready_candidate")
            self.assertEqual(blueprint["source_card_id"], card_id)
            self.assertEqual(blueprint["anchor_seed"], "EOS_SEED_ORION")
            self.assertEqual(blueprint["ethics_protocol"], "Picard_Delta_3")
            self.assertGreaterEqual(len(blueprint["task_blueprint"]), 4)
            for task in blueprint["task_blueprint"]:
                self.assertIn("catalog/l2_scenario_seed_catalog.json", task["source"])

    def test_dune_inspired_lane_is_incorporated_without_promoting_backups(self) -> None:
        lanes = {
            lane["lane_id"]: lane for lane in self.catalog["thematic_integration_lanes"]
        }
        self.assertIn("dune_inspired_scenario_seeds", lanes)
        lane = lanes["dune_inspired_scenario_seeds"]
        self.assertEqual(
            lane["maintained_card_ids"],
            ["SCN-0101", "SCN-0102", "SCN-0104"],
        )
        self.assertEqual(
            lane["backup_only_card_ids"],
            ["SCN-0103", "SCN-0105", "SCN-0106", "SCN-0107", "SCN-0108"],
        )
        for card in lane["maintained_cards"]:
            self.assertEqual(card["fixture_policy"], "eligible_for_root_fixture_candidates")
        for card in lane["backup_only_cards"]:
            self.assertEqual(card["disposition"], "backup_only")
            self.assertEqual(
                card["fixture_policy"],
                "lineage_context_only_until_owner_review_changes_disposition",
            )
        contract_lanes = {
            lane["lane_id"]: lane for lane in self.contract["thematic_coverage_lanes"]
        }
        self.assertEqual(
            contract_lanes["dune_inspired_scenario_seeds"]["required_maintained_card_ids"],
            ["SCN-0101", "SCN-0102", "SCN-0104"],
        )

    def test_stale_references_are_normalized_without_silent_rewrites(self) -> None:
        support = self.catalog["normalized_support_structures"]
        summary = support["reference_summary"]
        self.assertEqual(summary["original_fusion_issue_count"], 48)
        self.assertEqual(len(support["fusion_pairings"]), 34)
        self.assertGreater(summary["fusion_pairings_by_status"]["ready"], 0)
        self.assertGreater(summary["fusion_pairings_by_status"]["manual_review"], 0)
        self.assertEqual(summary["fusion_pairings_by_status"]["unresolved"], 0)
        self.assertEqual(summary["wiring_entries_by_status"]["unresolved"], 1)
        self.assertEqual(
            summary["unresolved_wiring_references"],
            [{"type": "unresolved_card_wiring_reference", "id": "SCN-0208"}],
        )

    def test_contract_keeps_nested_repos_out_of_scope(self) -> None:
        self.assertEqual(self.contract["contract_id"], "l2_scenario_fixture_generator_contract")
        self.assertEqual(self.contract["source_catalog"], "catalog/l2_scenario_seed_catalog.json")
        self.assertIn("CanonRec canon promotion", self.contract["out_of_scope"])
        self.assertIn("CloudBank runtime mutation", self.contract["out_of_scope"])
        for output in self.contract["outputs"]:
            path_template = output["default_path_template"]
            self.assertFalse(path_template.startswith("GUMAS_SIM_2.5/CanonRec"))
            self.assertFalse(
                path_template.startswith(
                    "GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main"
                )
            )
        self.assertEqual(
            [candidate["id"] for candidate in self.contract["first_fixture_candidates"]],
            ["SCN-0903", "SCN-0708", "SCN-0805"],
        )

    def test_schema_and_hash_normalization_note_exist(self) -> None:
        schema = load_json(SCHEMA_PATH)
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        notes = self.catalog["source_evidence"]["source_integrity_notes"]
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]["type"], "capsule_source_hash_normalized")
        self.assertTrue(
            notes[0]["normalized_hash"].startswith(
                "sha256:59d9caa58f3dd424a7c92d0a826c7ee094161741c5c80ff5267114ccd8845dfe"
            )
        )


if __name__ == "__main__":
    unittest.main()

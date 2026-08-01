from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "catalog/contracts/aurora_state_model_contract_v0_1.json"
WHITE_PAPER_PATH = ROOT / "docs/AURORA_STATE_MODEL_WHITE_PAPER_v0_1.md"
SYSTEM_SPEC_PATH = ROOT / "docs/AURORA_STATE_MODEL_SYSTEM_SPEC_v0_1.md"
PLAN_PATH = ROOT / "docs/AURORA_STATE_MODEL_IMPLEMENTATION_PLAN_v0_1.md"
RECEIPT_PATH = (
    ROOT / "reports/analysis/aurora_state_model_design_package__2026-08-01.json"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class AuroraStateModelContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_json(CONTRACT_PATH)
        cls.artifacts = {
            artifact["artifact_id"]: artifact for artifact in cls.contract["artifacts"]
        }
        cls.fixtures = {
            artifact_id: load_json(ROOT / artifact["fixture_path"])
            for artifact_id, artifact in cls.artifacts.items()
        }

    def test_contract_is_design_only(self) -> None:
        self.assertEqual(self.contract["status"], "draft_adoption_ready")
        self.assertEqual(self.contract["runtime_status"], "not_implemented")
        self.assertEqual(
            self.contract["canon_status"], "non_canonical_design_proposal"
        )
        self.assertFalse(self.contract["first_slice"]["model_training_authorized"])

    def test_contract_artifacts_exist(self) -> None:
        self.assertEqual(
            set(self.artifacts),
            {
                "aurora_state_episode",
                "aurora_epistemic_trace",
                "aurora_dataset_manifest",
            },
        )
        for artifact in self.artifacts.values():
            self.assertTrue((ROOT / artifact["schema_path"]).is_file())
            self.assertTrue((ROOT / artifact["fixture_path"]).is_file())

    def test_schemas_have_expected_top_level_shape(self) -> None:
        for artifact in self.artifacts.values():
            schema = load_json(ROOT / artifact["schema_path"])
            self.assertEqual(
                schema["$schema"], "https://json-schema.org/draft/2020-12/schema"
            )
            self.assertTrue(schema["$id"].startswith("https://aurora.local/schemas/"))
            self.assertEqual(schema["type"], "object")
            self.assertIn("properties", schema)
            self.assertIn("required", schema)
            self.assertFalse(schema["additionalProperties"])

    def test_fixtures_satisfy_required_top_level_contract(self) -> None:
        for artifact_id, artifact in self.artifacts.items():
            schema = load_json(ROOT / artifact["schema_path"])
            fixture = self.fixtures[artifact_id]
            self.assertFalse(set(schema["required"]) - set(fixture))
            self.assertFalse(set(fixture) - set(schema["properties"]))
            for key, property_schema in schema["properties"].items():
                if "const" in property_schema:
                    self.assertEqual(fixture[key], property_schema["const"])
                if "enum" in property_schema:
                    self.assertIn(fixture[key], property_schema["enum"])

    def test_episode_and_epistemic_trace_are_linked(self) -> None:
        episode = self.fixtures["aurora_state_episode"]
        trace = self.fixtures["aurora_epistemic_trace"]
        self.assertEqual(episode["episode_id"], trace["episode_id"])
        self.assertEqual(episode["teacher"]["epistemic_trace_ref"], trace["trace_id"])
        self.assertEqual(
            episode["input"]["observation_view"]["mask_id"],
            trace["observation_mask"]["mask_id"],
        )

    def test_all_fixtures_are_non_promotable(self) -> None:
        prohibited = set(
            self.contract["authority_model"]["prohibited_episode_authorities"]
        )
        for fixture in self.fixtures.values():
            self.assertNotIn(fixture["authority"], prohibited)
            self.assertFalse(fixture["promotion"]["eligible"])

    def test_fixture_forecast_is_normalized(self) -> None:
        trace = self.fixtures["aurora_epistemic_trace"]
        total = sum(item["probability"] for item in trace["forecast"]["outcomes"])
        self.assertAlmostEqual(total, 1.0)

    def test_manifest_uses_grouped_splits_and_is_not_public(self) -> None:
        manifest = self.fixtures["aurora_dataset_manifest"]
        self.assertEqual(
            manifest["split_policy"]["strategy"], "grouped_by_scenario_family"
        )
        self.assertTrue(manifest["seed_policy"]["isolated_per_episode"])
        self.assertFalse(manifest["governance"]["public_release_eligible"])

    def test_documents_state_the_non_active_boundary(self) -> None:
        white_paper = WHITE_PAPER_PATH.read_text(encoding="utf-8")
        system_spec = SYSTEM_SPEC_PATH.read_text(encoding="utf-8")
        plan = PLAN_PATH.read_text(encoding="utf-8")
        self.assertIn("NOT RUNTIME-ACTIVE", white_paper)
        self.assertIn("MUST NOT receive synthetic outcomes", system_spec)
        self.assertIn("DESIGN PACKAGE ONLY", plan)

    def test_receipt_matches_contract_status(self) -> None:
        receipt = load_json(RECEIPT_PATH)
        self.assertEqual(receipt["artifact"], "aurora_state_model_design_package")
        self.assertEqual(receipt["status"], self.contract["status"])
        self.assertEqual(receipt["runtime_status"], "not_implemented")
        self.assertFalse(receipt["nested_repositories_modified"])


if __name__ == "__main__":
    unittest.main()

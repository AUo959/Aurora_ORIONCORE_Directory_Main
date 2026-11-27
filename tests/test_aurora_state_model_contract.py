from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

import pytest

# importorskip, not a bare import. jsonschema is installed by CI and present in
# the repo venv, but not in the macOS system Python people also run the suite
# with. A module-level bare import turns that absence into a COLLECTION error,
# which aborts the entire run — 0 tests instead of 699, from one optional
# dependency. Skipping this module leaves the other 699 reporting.
#
# This matches how the repo already handles it: test_aurora_ace_character_retrieval
# imports jsonschema inside its test, and test_ci_canonrec_clone_depth uses
# importorskip for yaml.
jsonschema = pytest.importorskip("jsonschema")
Draft202012Validator = jsonschema.Draft202012Validator
FormatChecker = jsonschema.FormatChecker
ValidationError = jsonschema.ValidationError

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


def build_validator(schema: dict) -> Draft202012Validator:
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


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
        cls.schemas = {
            artifact_id: load_json(ROOT / artifact["schema_path"])
            for artifact_id, artifact in cls.artifacts.items()
        }
        cls.validators = {
            artifact_id: build_validator(schema)
            for artifact_id, schema in cls.schemas.items()
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
                "aurora_teacher_sufficiency_report",
            },
        )
        for artifact in self.artifacts.values():
            self.assertTrue((ROOT / artifact["schema_path"]).is_file())
            self.assertTrue((ROOT / artifact["fixture_path"]).is_file())

    def test_schemas_are_valid_draft_2020_12(self) -> None:
        for schema in self.schemas.values():
            self.assertEqual(
                schema["$schema"], "https://json-schema.org/draft/2020-12/schema"
            )
            self.assertTrue(schema["$id"].startswith("https://aurora.local/schemas/"))
            self.assertEqual(schema["type"], "object")
            self.assertIn("properties", schema)
            self.assertIn("required", schema)
            self.assertFalse(schema["additionalProperties"])

    def test_fixtures_conform_to_full_schemas(self) -> None:
        for artifact_id, validator in self.validators.items():
            errors = sorted(
                validator.iter_errors(self.fixtures[artifact_id]),
                key=lambda error: list(error.absolute_path),
            )
            self.assertEqual([], errors, msg=f"{artifact_id}: {errors}")

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

    def test_episode_records_realized_seed_and_rng_state(self) -> None:
        episode = self.fixtures["aurora_state_episode"]
        provenance = episode["provenance"]
        self.assertEqual(
            provenance["requested_seed_bundle"], provenance["realized_seed_bundle"]
        )
        self.assertEqual(episode["validation"]["seed_consistency"], "matched")
        self.assertTrue(
            provenance["post_initialization_rng_state_fingerprint"].startswith(
                "sha256:"
            )
        )

    def test_nested_seed_and_probability_constraints_are_enforced(self) -> None:
        bad_seed = deepcopy(self.fixtures["aurora_state_episode"])
        bad_seed["provenance"]["realized_seed_bundle"]["world"] = -1
        with self.assertRaises(ValidationError):
            self.validators["aurora_state_episode"].validate(bad_seed)

        bad_probability = deepcopy(self.fixtures["aurora_epistemic_trace"])
        bad_probability["forecast"]["outcomes"][0]["probability"] = 1.1
        with self.assertRaises(ValidationError):
            self.validators["aurora_epistemic_trace"].validate(bad_probability)

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
        self.assertTrue(manifest["seed_policy"]["records_realized_seeds"])
        self.assertFalse(manifest["governance"]["public_release_eligible"])

    def test_grouped_split_requires_two_families_before_passing(self) -> None:
        manifest = deepcopy(self.fixtures["aurora_dataset_manifest"])
        manifest["split_policy"]["leakage_check"] = "passed"
        with self.assertRaises(ValidationError):
            self.validators["aurora_dataset_manifest"].validate(manifest)

        manifest["scenario_families"].append("station-resilience")
        self.validators["aurora_dataset_manifest"].validate(manifest)

    def test_teacher_sufficiency_gate_follows_reproducibility(self) -> None:
        gate_ids = [gate["id"] for gate in self.contract["quality_gates"]]
        self.assertEqual(gate_ids[1:4], ["G1", "G1.5", "G2"])
        report = self.fixtures["aurora_teacher_sufficiency_report"]
        self.assertEqual(report["gate"]["status"], "not_evaluated")
        self.assertEqual(
            self.contract["first_slice"]["post_generation_decision_gate"], "G1.5"
        )
        self.assertNotIn("G1.5", self.contract["first_slice"]["required_gates"])

        premature_pass = deepcopy(report)
        premature_pass["gate"]["status"] = "passed"
        with self.assertRaises(ValidationError):
            self.validators["aurora_teacher_sufficiency_report"].validate(
                premature_pass
            )

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

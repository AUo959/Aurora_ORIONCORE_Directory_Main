from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import canonrec_bridge_validate as validator  # noqa: E402


CONTRACT_PATH = (
    ROOT
    / "catalog/contracts/AURORA_CANONREC__CONTRACT__BRIDGE_CONTROL_PLANE__v1.0__2026-06-24.json"
)
PACKET_PATH = (
    ROOT
    / "reports/automation/AURORA_CANONREC__PACKET__ORION_ENTITY_0008_MAYA_SHEPARD_SPOTCHECK__v1.0__2026-06-24.json"
)


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


class CanonRecBridgeValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = load_json(CONTRACT_PATH)
        self.packet = load_json(PACKET_PATH)

    def codes(self, result: dict[str, Any]) -> set[str]:
        return {finding["code"] for finding in result["findings"]}

    def test_maya_shepard_review_only_packet_is_valid(self) -> None:
        result = validator.validate_packet(self.packet, self.contract)
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["summary"]["error_count"], 0)

    def test_invalid_layer_is_rejected(self) -> None:
        packet = json.loads(json.dumps(self.packet))
        packet["layer"] = "L4"
        result = validator.validate_packet(packet, self.contract)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("invalid_layer", self.codes(result))

    def test_invalid_claim_status_is_rejected(self) -> None:
        packet = json.loads(json.dumps(self.packet))
        packet["claim_status"] = "CANONISH"
        result = validator.validate_packet(packet, self.contract)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("invalid_claim_status", self.codes(result))

    def test_target_repo_must_be_canonrec(self) -> None:
        packet = json.loads(json.dumps(self.packet))
        packet["target_repo"] = "AUo959/aurora-cloudbank-symbolic"
        result = validator.validate_packet(packet, self.contract)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("invalid_target_repo", self.codes(result))

    def test_merge_approval_required_must_be_true(self) -> None:
        packet = json.loads(json.dumps(self.packet))
        packet["merge_approval_required"] = False
        result = validator.validate_packet(packet, self.contract)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("merge_approval_not_required", self.codes(result))

    def test_v1_delete_operation_is_rejected(self) -> None:
        packet = json.loads(json.dumps(self.packet))
        packet["target_paths"][0]["intended_operation"] = "delete"
        result = validator.validate_packet(packet, self.contract)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("delete_operation_blocked_v1", self.codes(result))

    def test_update_requires_current_blob_sha(self) -> None:
        packet = json.loads(json.dumps(self.packet))
        packet["boundary_assertions"]["canonrec_write_requested"] = True
        packet["target_paths"][0]["intended_operation"] = "update"
        packet["target_paths"][0].pop("current_blob_sha", None)
        result = validator.validate_packet(packet, self.contract)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("missing_current_blob_sha", self.codes(result))

    def test_cloudbank_mirror_write_is_rejected(self) -> None:
        packet = json.loads(json.dumps(self.packet))
        packet["boundary_assertions"]["cloudbank_mirror_write_requested"] = True
        result = validator.validate_packet(packet, self.contract)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("cloudbank_write_blocked", self.codes(result))

    def test_cli_summary_validates_default_packets(self) -> None:
        result = subprocess.run(
            [sys.executable, "tools/canonrec_bridge_validate.py", "--summary"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "valid")
        self.assertGreaterEqual(payload["summary"]["packet_count"], 1)


if __name__ == "__main__":
    unittest.main()

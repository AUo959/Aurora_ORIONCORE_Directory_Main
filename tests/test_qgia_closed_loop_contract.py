from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "catalog/contracts/qgia_knowledge_closed_loop_contract_v1.json"
DOC_PATH = ROOT / "docs/QGIA_KNOWLEDGE_CLOSED_LOOP_CONTRACT_v1.md"
RECEIPT_PATH = ROOT / "reports/analysis/qgia_closed_loop_contract_package__2026-04-18.json"
EVENT_NAME_RE = re.compile(r"^qgia\.[a-z]+(?:\.[a-z]+)+$")


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


class QGIAClosedLoopContractTests(unittest.TestCase):
    def test_contract_file_loads(self) -> None:
        contract = load_json(CONTRACT_PATH)
        self.assertEqual(contract["contract_id"], "qgia_knowledge_closed_loop_contract")
        self.assertEqual(contract["status"], "draft_adoption_ready")
        self.assertIn("qgia-knowledge-library", contract["scope"])
        self.assertIn("qgia-knowledge-spine", contract["scope"])

    def test_contract_referenced_schema_files_exist(self) -> None:
        contract = load_json(CONTRACT_PATH)
        for artifact in contract["artifacts"]:
            schema_path = ROOT / artifact["schema_path"]
            self.assertTrue(schema_path.exists(), str(schema_path))

    def test_event_names_are_unique_and_canonical(self) -> None:
        contract = load_json(CONTRACT_PATH)
        event_names = [event["name"] for event in contract["events"]]
        self.assertEqual(len(event_names), len(set(event_names)))
        for name in event_names:
            self.assertRegex(name, EVENT_NAME_RE)

    def test_schema_files_have_expected_top_level_shape(self) -> None:
        contract = load_json(CONTRACT_PATH)
        for artifact in contract["artifacts"]:
            schema = load_json(ROOT / artifact["schema_path"])
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertIn("$id", schema)
            self.assertIn("title", schema)
            self.assertIn("type", schema)

    def test_doc_and_receipt_exist(self) -> None:
        self.assertTrue(DOC_PATH.exists(), str(DOC_PATH))
        receipt = load_json(RECEIPT_PATH)
        self.assertEqual(receipt["artifact"], "qgia_closed_loop_contract_package")
        self.assertEqual(receipt["status"], "draft_adoption_ready")


if __name__ == "__main__":
    unittest.main()


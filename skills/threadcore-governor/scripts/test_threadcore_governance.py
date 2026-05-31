#!/usr/bin/env python3
"""Fixture-driven tests for threadcore-governor scripts."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from threadcore_report import render_markdown  # noqa: E402
from threadcore_rules import scan_repo  # noqa: E402


class ThreadcoreGovernanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.root_a = self.repo / "root_a"
        self.root_b = self.repo / "root_b"
        self.outside = self.repo / "outside"
        for p in (self.root_a, self.root_b, self.outside):
            p.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _write_json(self, rel: Path, payload: dict) -> Path:
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def _write_text(self, rel: Path, text: str) -> Path:
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def _scan(self) -> dict:
        return scan_repo(str(self.repo), [str(self.root_a), str(self.root_b)], strictness="balanced")

    def _find_rule(self, report: dict, rule_id: str) -> bool:
        return any(f["rule_id"] == rule_id for f in report["findings"])

    def test_t01_valid_checkpoint(self) -> None:
        self._write_json(
            Path("root_a/THREADCORE_CHECKPOINT_valid.json"),
            {
                "augmentation": "THREADCORE",
                "version": "v3.5.1",
                "threadcore_directives": ["one"],
                "checkpoint": {
                    "id": "CP-001",
                    "anchor_seed": "EOS_SEED_ORION",
                    "ethics_protocol": "Picard_Delta_3",
                },
                "beacon_contact": ["ZIPWIZ"],
            },
        )
        report = self._scan()
        families = {a["family"] for a in report["artifacts"]}
        self.assertIn("checkpoint", families)
        self.assertEqual(report["summary"]["by_severity"]["BLOCK"], 0)

    def test_t02_checkpoint_missing_anchor_seed(self) -> None:
        self._write_json(
            Path("root_a/THREADCORE_CHECKPOINT_missing_anchor.json"),
            {
                "augmentation": "THREADCORE",
                "version": "v3.5.1",
                "threadcore_directives": ["one"],
                "checkpoint": {
                    "id": "CP-002",
                    "ethics_protocol": "Picard_Delta_3",
                },
            },
        )
        report = self._scan()
        self.assertTrue(self._find_rule(report, "B_CHECKPOINT_REQUIRED_FIELD"))

    def test_t03_continuity_log_wrong_ethics(self) -> None:
        self._write_json(
            Path("root_a/THREADCORE_Continuity_Log_bad_ethics.json"),
            {
                "symbolic_tool": "DriftConcord::Vector",
                "deployment_key": "DEPLOY-1",
                "activation_phrase": "#THREADCORE_ONLINE",
                "ethics_protocol": "Wrong",
                "timestamp": "2025-05-01T00:00:00Z",
                "status": "Sealed",
            },
        )
        report = self._scan()
        self.assertTrue(self._find_rule(report, "B_INVALID_ETHICS_PROTOCOL"))

    def test_t04_driftpulse_without_anchor_seed(self) -> None:
        self._write_json(
            Path("root_a/threadcore_v3.5.1_driftpulse.json"),
            {
                "capsule_type": "DRIFTPULSE",
                "augmentation": "THREADCORE",
                "version": "v3.5.1",
                "role": "Pulse",
                "ethics_protocol": "Picard_Delta_3",
            },
        )
        report = self._scan()
        rules = [f["rule_id"] for f in report["findings"]]
        self.assertNotIn("B_MISSING_ANCHOR_SEED", rules)

    def test_t05_delta_chain_missing_cdk(self) -> None:
        self._write_json(
            Path("root_a/THREADCORE_DELTA_CHAIN.json"),
            {
                "delta_chain_version": "v1.0",
                "entries": [
                    {
                        "version": "v1.0",
                        "label": "LABEL",
                        "ethics": "Picard_Delta_3",
                    }
                ],
            },
        )
        report = self._scan()
        self.assertTrue(self._find_rule(report, "B_DELTA_ENTRY_REQUIRED_FIELD"))

    def test_t06_beacon_missing_registry_marker(self) -> None:
        self._write_text(
            Path("root_a/THREADCORE_BEACON_test.md"),
            "THREADCORE BEACON::VISIBLE_THREAD v1.0\n\nThread Identity Marker\n",
        )
        report = self._scan()
        self.assertTrue(self._find_rule(report, "B_BEACON_REGISTRY_MARKER_MISSING"))

    def test_t07_beacon_unicode_preserved(self) -> None:
        text = (
            "THREADCORE BEACON::VISIBLE_THREAD v1.0\n"
            "🧭 Symbolic Alias: 🌊 Drift Link\n"
            "Thread Identity Marker\n"
            "Registry Marker: THREADCORE::VISIBLE_NODE.ORION.UNICODE-01\n"
            "THREADREFLECT v1.0\n"
        )
        self._write_text(Path("root_a/THREADCORE_BEACON_unicode.md"), text)
        report = self._scan()
        self.assertEqual(report["summary"]["by_severity"]["BLOCK"], 0)
        serialized = json.dumps(report, ensure_ascii=False)
        self.assertIn("🧭", text)
        self.assertIn("THREADCORE::VISIBLE_NODE.ORION.UNICODE-01", serialized)

    def test_t08_legacy_variant_warning(self) -> None:
        self._write_json(
            Path("root_a/threadcore_payload_legacy.json"),
            {
                "capsule_id": "CAP-LEGACY",
                "threadcore_version": "v3.5.1",
                "role": "Symbolic",
                "ethics_protocol": "Picard_Delta_3",
                "anchor_seed": "EOS_SEED_ORION",
            },
        )
        report = self._scan()
        self.assertTrue(self._find_rule(report, "W_LEGACY_KEY_VARIANT"))

    def test_t09_mixed_summary_counts(self) -> None:
        self._write_json(
            Path("root_a/THREADCORE_CHECKPOINT_ok.json"),
            {
                "augmentation": "THREADCORE",
                "version": "v3.5.1",
                "threadcore_directives": ["ok"],
                "checkpoint": {
                    "id": "CP-9",
                    "anchor_seed": "EOS_SEED_ORION",
                    "ethics_protocol": "Picard_Delta_3",
                },
                "beacon_contact": ["ZIPWIZ"],
            },
        )
        self._write_json(
            Path("root_a/THREADCORE_Continuity_Log_bad.json"),
            {
                "symbolic_tool": "Tool",
                "deployment_key": "DEPLOY-9",
                "activation_phrase": "#THREADCORE_ONLINE",
                "ethics_protocol": "Wrong",
                "timestamp": "2025-05-01T00:00:00Z",
                "status": "Sealed",
            },
        )
        report = self._scan()
        self.assertGreaterEqual(report["summary"]["by_severity"]["BLOCK"], 1)
        self.assertGreaterEqual(report["summary"]["total_artifacts"], 2)

    def test_t10_fail_on_block_exit_code(self) -> None:
        self._write_json(
            Path("root_a/THREADCORE_Continuity_Log_bad.json"),
            {
                "symbolic_tool": "Tool",
                "deployment_key": "DEPLOY-10",
                "activation_phrase": "#THREADCORE_ONLINE",
                "ethics_protocol": "Wrong",
                "timestamp": "2025-05-01T00:00:00Z",
                "status": "Sealed",
            },
        )
        out_json = self.repo / "out" / "scan.json"
        out_md = self.repo / "out" / "scan.md"
        cmd = [
            sys.executable,
            str(SCRIPT_DIR / "threadcore_governance_scan.py"),
            "--repo",
            str(self.repo),
            "--roots",
            f"{self.root_a},{self.root_b}",
            "--out-json",
            str(out_json),
            "--out-md",
            str(out_md),
            "--fail-on-block",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)

    def test_t11_emit_l3_bridge(self) -> None:
        self._write_json(
            Path("root_a/THREADCORE_CHECKPOINT_ok.json"),
            {
                "augmentation": "THREADCORE",
                "version": "v3.5.1",
                "threadcore_directives": ["ok"],
                "checkpoint": {
                    "id": "CP-11",
                    "anchor_seed": "EOS_SEED_ORION",
                    "ethics_protocol": "Picard_Delta_3",
                },
                "beacon_contact": ["ZIPWIZ"],
            },
        )
        out_json = self.repo / "out" / "scan.json"
        out_md = self.repo / "out" / "scan.md"
        out_bridge = self.repo / "out" / "bridge.json"
        cmd = [
            sys.executable,
            str(SCRIPT_DIR / "threadcore_governance_scan.py"),
            "--repo",
            str(self.repo),
            "--roots",
            f"{self.root_a},{self.root_b}",
            "--out-json",
            str(out_json),
            "--out-md",
            str(out_md),
            "--emit-l3-bridge",
            str(out_bridge),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        bridge = json.loads(out_bridge.read_text(encoding="utf-8"))
        self.assertIn("entities", bridge)
        self.assertIn("protocol_update", bridge["entities"])

    def test_t12_root_scope_excludes_outside(self) -> None:
        self._write_json(
            Path("outside/THREADCORE_CHECKPOINT_outside.json"),
            {
                "augmentation": "THREADCORE",
                "version": "v3.5.1",
                "threadcore_directives": ["outside"],
                "checkpoint": {
                    "id": "CP-OUTSIDE",
                    "anchor_seed": "EOS_SEED_ORION",
                    "ethics_protocol": "Picard_Delta_3",
                },
            },
        )
        self._write_json(
            Path("root_a/THREADCORE_CHECKPOINT_inside.json"),
            {
                "augmentation": "THREADCORE",
                "version": "v3.5.1",
                "threadcore_directives": ["inside"],
                "checkpoint": {
                    "id": "CP-INSIDE",
                    "anchor_seed": "EOS_SEED_ORION",
                    "ethics_protocol": "Picard_Delta_3",
                },
            },
        )
        report = self._scan()
        files = {a["file"] for a in report["artifacts"]}
        self.assertIn("root_a/THREADCORE_CHECKPOINT_inside.json", files)
        self.assertNotIn("outside/THREADCORE_CHECKPOINT_outside.json", files)

    def test_markdown_contract_sections(self) -> None:
        self._write_json(
            Path("root_a/THREADCORE_CHECKPOINT_ok.json"),
            {
                "augmentation": "THREADCORE",
                "version": "v3.5.1",
                "threadcore_directives": ["ok"],
                "checkpoint": {
                    "id": "CP-MD",
                    "anchor_seed": "EOS_SEED_ORION",
                    "ethics_protocol": "Picard_Delta_3",
                },
                "beacon_contact": ["ZIPWIZ"],
            },
        )
        report = self._scan()
        md = render_markdown(report)
        self.assertIn("## Scope", md)
        self.assertIn("## Blocking Findings", md)
        self.assertIn("## Warnings", md)
        self.assertIn("## Suggested Patch Plan", md)
        self.assertIn("## L3 Bridge Preview", md)


if __name__ == "__main__":
    unittest.main(verbosity=2)

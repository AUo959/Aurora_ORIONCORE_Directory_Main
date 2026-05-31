#!/usr/bin/env python3
"""Fixture-driven tests for zipwiz-governor scripts."""

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

from zipwiz_rules import scan_repo  # noqa: E402


class ZipWizGovernanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.packaging = self.repo / "packaging"
        self.runtime = self.repo / "runtime"
        self.meta = self.repo / "meta"
        self.reference = self.repo / "reference"
        self.outside = self.repo / "outside"
        for path in (self.packaging, self.runtime, self.meta, self.reference, self.outside):
            path.mkdir(parents=True, exist_ok=True)

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

    def _scan(self, include_evolution: bool = True) -> dict:
        return scan_repo(
            repo_root=str(self.repo),
            roots=[str(self.packaging), str(self.runtime), str(self.meta)],
            reference_roots=[str(self.reference)],
            strictness="balanced",
            include_evolution=include_evolution,
        )

    def _has_rule(self, report: dict, rule_id: str) -> bool:
        return any(row["rule_id"] == rule_id for row in report["findings"])

    def test_t01_valid_bundle_manifest(self) -> None:
        self._write_json(
            Path("packaging/bundle.manifest.json"),
            {
                "bundle_id": "ZIPWIZ.TEST.BUNDLE.2026-02-08.BAY02_1012",
                "created_at": "2026-02-08T16:55:00Z",
                "anchor_seed": "EOS_SEED_ORION",
                "ethics_protocol": "Picard_Delta_3",
                "contents": [{"path": "x.md", "sha256": "a" * 64, "size_bytes": 12, "role": "manifest"}],
            },
        )
        report = self._scan()
        self.assertEqual(report["summary"]["by_severity"]["BLOCK"], 0)

    def test_t02_bundle_missing_anchor(self) -> None:
        self._write_json(
            Path("packaging/bundle.manifest.json"),
            {
                "bundle_id": "ZIPWIZ.TEST.BUNDLE.2026-02-08.BAY02_1012",
                "created_at": "2026-02-08T16:55:00Z",
                "ethics_protocol": "Picard_Delta_3",
                "contents": [{"path": "x.md", "sha256": "a" * 64, "size_bytes": 12}],
            },
        )
        report = self._scan()
        self.assertTrue(self._has_rule(report, "B_BUNDLE_MANIFEST_MISSING_ANCHOR"))

    def test_t03_bundle_wrong_ethics(self) -> None:
        self._write_json(
            Path("packaging/bundle.manifest.json"),
            {
                "bundle_id": "ZIPWIZ.TEST.BUNDLE.2026-02-08.BAY02_1012",
                "created_at": "2026-02-08T16:55:00Z",
                "anchor_seed": "EOS_SEED_ORION",
                "ethics_protocol": "Wrong",
                "contents": [{"path": "x.md", "sha256": "a" * 64, "size_bytes": 12}],
            },
        )
        report = self._scan()
        self.assertTrue(self._has_rule(report, "B_BUNDLE_MANIFEST_INVALID_ETHICS"))

    def test_t04_bundle_hash_invalid(self) -> None:
        self._write_json(
            Path("packaging/bundle.manifest.json"),
            {
                "bundle_id": "ZIPWIZ.TEST.BUNDLE.2026-02-08.BAY02_1012",
                "created_at": "2026-02-08T16:55:00Z",
                "anchor_seed": "EOS_SEED_ORION",
                "ethics_protocol": "Picard_Delta_3",
                "contents": [{"path": "x.md", "sha256": "bad", "size_bytes": 12}],
            },
        )
        report = self._scan()
        self.assertTrue(self._has_rule(report, "B_BUNDLE_HASH_INVALID"))

    def test_t05_staging_missing_layer(self) -> None:
        self._write_json(
            Path("packaging/STAGING_MANIFEST__demo.json"),
            {
                "staging_bay": "Bay",
                "bundle": "ZIPWIZ.TEST.BUNDLE.2026-02-08.BAY02_1012",
                "generated_at_local": "2026-02-08 11:55 UTC-05",
                "build": "BAY02_1012",
                "classification": {"domain": "governance"},
                "files": [{"path": "x.md", "role": "entrypoint", "sha256": "a" * 64, "bytes": 10}],
            },
        )
        report = self._scan()
        self.assertTrue(self._has_rule(report, "B_STAGING_MANIFEST_REQUIRED_FIELD"))

    def test_t06_staging_bundle_mismatch_warn(self) -> None:
        self._write_json(
            Path("packaging/bundle.manifest.json"),
            {
                "bundle_id": "ZIPWIZ.ONE",
                "created_at": "2026-02-08T16:55:00Z",
                "anchor_seed": "EOS_SEED_ORION",
                "ethics_protocol": "Picard_Delta_3",
                "contents": [{"path": "x.md", "sha256": "a" * 64, "size_bytes": 12}],
            },
        )
        self._write_json(
            Path("packaging/STAGING_MANIFEST__demo.json"),
            {
                "staging_bay": "Bay",
                "bundle": "ZIPWIZ.TWO",
                "generated_at_local": "2026-02-08 11:55 UTC-05",
                "build": "BAY02_1012",
                "classification": {"layer": "L3", "domain": "governance"},
                "files": [{"path": "x.md", "role": "entrypoint", "sha256": "a" * 64, "bytes": 10}],
            },
        )
        report = self._scan()
        self.assertTrue(self._has_rule(report, "W_STAGING_BUNDLE_ID_MISMATCH"))

    def test_t07_protocol_missing_frontmatter_ethics(self) -> None:
        self._write_text(
            Path("packaging/L3_GOV__ZIPWIZ_PACKAGING_PROTOCOL.md"),
            "---\ndocid: ORION.L3.GOV.ZIPWIZ.PACKAGING.0001\ndoctype: protocol\nversion: 0.1.0\nanchor_seed: EOS_SEED_ORION\n---\n# ZIPWIZ Packaging and Export Protocol\n",
        )
        report = self._scan()
        self.assertTrue(self._has_rule(report, "B_PROTOCOL_FRONTMATTER_REQUIRED_FIELD"))

    def test_t08_beacon_unicode_preserved(self) -> None:
        self._write_json(
            Path("packaging/ZIPWizard_Universal_Beacon_Capsule.json"),
            {
                "Designation": "aurora://🧭/zipwiz",
                "Action_Request": "EXPORT_THREAD_PACKAGE",
                "Thread_Metadata": {"Thread_Name": "THREAD.🌀.UNICODE"},
                "Thread_Identity_Affirmation": {
                    "Ethics_Lock": "SN1-AS3",
                    "Trust_Anchor": "BeaconSeal::Auto-Named",
                },
                "Output_Format": ".beacon.json",
            },
        )
        report = self._scan()
        serialized = json.dumps(report, ensure_ascii=False)
        self.assertIn("🧭", serialized)
        self.assertEqual(report["summary"]["by_severity"]["BLOCK"], 0)

    def test_t09_beacon_legacy_warn(self) -> None:
        self._write_json(
            Path("packaging/ZIPWizard_Universal_Beacon_Capsule.json"),
            {
                "Designation": "aurora://zipwiz",
                "Action_Request": "EXPORT_THREAD_PACKAGE",
                "Thread_Metadata": {"Thread_Name": "THREAD.TEST"},
                "Thread_Identity_Affirmation": {
                    "Ethics_Lock": "SN1-AS3",
                    "Trust_Anchor": "BeaconSeal::Auto-Named",
                },
                "Output_Format": ".beacon.json",
            },
        )
        report = self._scan()
        self.assertTrue(self._has_rule(report, "W_BEACON_LEGACY_ETHICS_LOCK_ONLY"))

    def test_t10_runtime_stub_warn(self) -> None:
        self._write_text(
            Path("packaging/L3_GOV__ZIPWIZ_PACKAGING_PROTOCOL.md"),
            "---\ndocid: ORION.L3.GOV.ZIPWIZ.PACKAGING.0001\ndoctype: protocol\nversion: 0.1.0\nanchor_seed: EOS_SEED_ORION\nethics_protocol: Picard_Delta_3\nauthority: draft\n---\n# ZIPWIZ Packaging and Export Protocol\n",
        )
        self._write_text(
            Path("runtime/services/command_node/modules/zipwiz.js"),
            "function pingBeacon(){return {ok:true};}\nmodule.exports={pingBeacon};\n",
        )
        report = self._scan()
        self.assertTrue(self._has_rule(report, "W_RUNTIME_ALIGNMENT_DRIFT"))

    def test_t11_mixed_summary_counts(self) -> None:
        self._write_json(
            Path("packaging/bundle.manifest.json"),
            {
                "bundle_id": "ZIPWIZ.TEST.BUNDLE.2026-02-08.BAY02_1012",
                "created_at": "2026-02-08T16:55:00Z",
                "anchor_seed": "EOS_SEED_ORION",
                "ethics_protocol": "Picard_Delta_3",
                "contents": [{"path": "x.md", "sha256": "a" * 64, "size_bytes": 12}],
            },
        )
        self._write_json(
            Path("packaging/STAGING_MANIFEST__demo.json"),
            {
                "staging_bay": "Bay",
                "bundle": "ZIPWIZ.TWO",
                "generated_at_local": "2026-02-08 11:55 UTC-05",
                "build": "BAY02_1012",
                "classification": {"layer": "L3", "domain": "governance"},
                "files": [{"path": "x.md", "role": "entrypoint", "sha256": "bad", "bytes": 10}],
            },
        )
        report = self._scan()
        self.assertGreaterEqual(report["summary"]["total_artifacts"], 2)
        self.assertGreaterEqual(report["summary"]["total_findings"], 1)

    def test_t12_fail_on_block_exit(self) -> None:
        self._write_json(
            Path("packaging/bundle.manifest.json"),
            {
                "bundle_id": "ZIPWIZ.TEST.BUNDLE.2026-02-08.BAY02_1012",
                "created_at": "2026-02-08T16:55:00Z",
                "anchor_seed": "BAD",
                "ethics_protocol": "Picard_Delta_3",
                "contents": [{"path": "x.md", "sha256": "a" * 64, "size_bytes": 12}],
            },
        )
        out_json = self.repo / "out" / "scan.json"
        out_md = self.repo / "out" / "scan.md"
        cmd = [
            sys.executable,
            str(SCRIPT_DIR / "zipwiz_governance_scan.py"),
            "--repo",
            str(self.repo),
            "--roots",
            f"{self.packaging},{self.runtime},{self.meta}",
            "--reference-roots",
            str(self.reference),
            "--out-json",
            str(out_json),
            "--out-md",
            str(out_md),
            "--fail-on-block",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)

    def test_t13_emit_l3_bridge(self) -> None:
        self._write_json(
            Path("packaging/bundle.manifest.json"),
            {
                "bundle_id": "ZIPWIZ.TEST.BUNDLE.2026-02-08.BAY02_1012",
                "created_at": "2026-02-08T16:55:00Z",
                "anchor_seed": "EOS_SEED_ORION",
                "ethics_protocol": "Picard_Delta_3",
                "contents": [{"path": "x.md", "sha256": "a" * 64, "size_bytes": 12}],
            },
        )
        out_json = self.repo / "out" / "scan.json"
        out_md = self.repo / "out" / "scan.md"
        out_bridge = self.repo / "out" / "bridge.json"
        cmd = [
            sys.executable,
            str(SCRIPT_DIR / "zipwiz_governance_scan.py"),
            "--repo",
            str(self.repo),
            "--roots",
            f"{self.packaging},{self.runtime},{self.meta}",
            "--reference-roots",
            str(self.reference),
            "--out-json",
            str(out_json),
            "--out-md",
            str(out_md),
            "--emit-l3-bridge",
            str(out_bridge),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertTrue(out_bridge.exists())
        bridge = json.loads(out_bridge.read_text(encoding="utf-8"))
        self.assertIn("protocol_update", bridge)

    def test_t14_default_exclusion_patterns(self) -> None:
        self._write_json(
            Path("packaging/06_ARCHIVES/bundle.manifest.json"),
            {
                "bundle_id": "ZIPWIZ.SHOULD.NOT.SCAN",
                "created_at": "2026-02-08T16:55:00Z",
                "anchor_seed": "BAD",
                "ethics_protocol": "Wrong",
                "contents": [{"path": "x.md", "sha256": "bad", "size_bytes": 12}],
            },
        )
        report = self._scan()
        files = {artifact["file"] for artifact in report["artifacts"]}
        self.assertFalse(any("06_ARCHIVES" in item for item in files))

    def test_t15_evolution_milestones_present(self) -> None:
        self._write_text(
            Path("packaging/L3_GOV__ZIPWIZ_PACKAGING_PROTOCOL__v0.1.0__2026-02-08.md"),
            "---\ndocid: ORION.L3.GOV.ZIPWIZ.PACKAGING.0001\ndoctype: protocol\nversion: 0.1.0\nanchor_seed: EOS_SEED_ORION\nethics_protocol: Picard_Delta_3\nauthority: draft\n---\n# ZIPWIZ Packaging and Export Protocol\n",
        )
        self._write_text(
            Path("meta/meta_narrative_summary_zipwizard_threadcore_functional_patch_thread.md"),
            "# ZIPWIZARD+ THREADCORE patch\nDate: 2026-02-16\nPatch: THREADCORE_FUNCTIONAL_FOCUS\n",
        )
        self._write_text(
            Path("reference/ZIPWIZ_Constellation_SEEDCARD__v2.2.6b__2025-04-25.md"),
            "# SEEDCARD: ZIPWIZ CONSTELLATION CORE\nVersion: v2.2.6b\nDate: 2025-04-25\n",
        )
        report = self._scan(include_evolution=True)
        dates = {row.get("date") for row in report["evolution_map"]}
        self.assertIn("2025-04-25", dates)
        self.assertIn("2026-02-08", dates)
        self.assertIn("2026-02-16", dates)

    def test_t16_drift_log_not_protocol_family(self) -> None:
        rel = Path("packaging/L3_LOG__DRIFT_LOG_GUMAS_StagingBay__v0.2__2026-02-08__BAY02_0814.md")
        self._write_text(
            rel,
            "# Drift log\nThis references ZIPWIZ Packaging and Export Protocol but is not the protocol document.\n",
        )
        report = self._scan(include_evolution=False)
        protocol_files = {a["file"] for a in report["artifacts"] if a["family"] == "zipwiz_protocol_doc"}
        self.assertNotIn(rel.as_posix(), protocol_files)

    def test_t17_schema_not_bundle_manifest_family(self) -> None:
        rel = Path("packaging/L3_SCHEMA__ORION_BUNDLE_MANIFEST__v0.1.0__2026-02-08.schema.json")
        self._write_json(
            rel,
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "title": "ORION Package Bundle Manifest Schema",
                "type": "object",
                "properties": {
                    "bundle_id": {"type": "string"},
                    "contents": {"type": "array"},
                },
            },
        )
        report = self._scan(include_evolution=False)
        bundle_manifest_files = {a["file"] for a in report["artifacts"] if a["family"] == "bundle_manifest"}
        self.assertNotIn(rel.as_posix(), bundle_manifest_files)

    def test_t18_diagnostic_mode_outputs_matrix(self) -> None:
        self._write_json(
            Path("packaging/bundle.manifest.json"),
            {
                "bundle_id": "ZIPWIZ.TEST.BUNDLE.2026-03-03.BAY01_1010",
                "created_at": "2026-03-03T10:10:00Z",
                "anchor_seed": "EOS_SEED_ORION",
                "ethics_protocol": "Picard_Delta_3",
                "contents": [{"path": "x.md", "sha256": "a" * 64, "size_bytes": 12}],
            },
        )
        self._write_text(
            Path("packaging/L3_GOV__ZIPWIZ_PACKAGING_PROTOCOL.md"),
            "---\ndocid: ORION.L3.GOV.ZIPWIZ.PACKAGING.0001\ndoctype: protocol\nversion: 0.1.0\nanchor_seed: EOS_SEED_ORION\nethics_protocol: Picard_Delta_3\nauthority: approved\n---\n# ZIPWIZ Packaging and Export Protocol\n",
        )
        out_json = self.repo / "out" / "diag_scan.json"
        out_md = self.repo / "out" / "diag_scan.md"
        diag_json = self.repo / "out" / "diag_matrix.json"
        cmd = [
            sys.executable,
            str(SCRIPT_DIR / "zipwiz_governance_scan.py"),
            "--repo",
            str(self.repo),
            "--roots",
            f"{self.packaging},{self.runtime},{self.meta}",
            "--reference-roots",
            str(self.reference),
            "--out-json",
            str(out_json),
            "--out-md",
            str(out_md),
            "--diagnostic-mode",
            "--diagnostic-json",
            str(diag_json),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertTrue(diag_json.exists())
        payload = json.loads(diag_json.read_text(encoding="utf-8"))
        matrix = payload.get("diagnostic_matrix", {})
        self.assertIn("balanced", matrix)
        self.assertIn("strict", matrix)
        self.assertIn("lenient", matrix)
        self.assertIn("balanced_no_evolution", matrix)

    def test_t19_role_and_size_noise_reduction(self) -> None:
        self._write_json(
            Path("packaging/bundle.manifest.json"),
            {
                "bundle_id": "ZIPWIZ.TEST.BUNDLE.2026-03-03.BAY01_1111",
                "created_at": "2026-03-03T11:11:00Z",
                "anchor_seed": "EOS_SEED_ORION",
                "ethics_protocol": "Picard_Delta_3",
                "files": [
                    {"path": "a.md", "sha256": "a" * 64, "bytes": 1, "role": "asset"},
                    {"path": "b.md", "sha256": "b" * 64, "bytes": 2, "role": "entrypoint"},
                    {"path": "c.md", "sha256": "c" * 64, "bytes": 3, "role": "markdown"},
                ],
            },
        )
        report = self._scan(include_evolution=False)
        rules = [row["rule_id"] for row in report["findings"]]
        self.assertIn("I_BUNDLE_SIZE_BYTES_MAPPABLE", rules)
        self.assertIn("I_BUNDLE_ROLE_NORMALIZED", rules)
        self.assertNotIn("W_BUNDLE_SIZE_BYTES_VARIANT", rules)
        self.assertNotIn("W_BUNDLE_ROLE_DRIFT", rules)

    def test_t20_diagnostic_warn_threshold(self) -> None:
        self._write_json(
            Path("packaging/bundle.manifest.json"),
            {
                "bundle_id": "ZIPWIZ.TEST.BUNDLE.2026-03-03.BAY01_1212",
                "created_at_utc": "2026-03-03 12:12 UTC",
                "anchor_seed": "EOS_SEED_ORION",
                "ethics_protocol": "Picard_Delta_3",
                "files": [
                    {"path": "a.md", "sha256": "a" * 64, "bytes": 1, "role": "asset"},
                ],
            },
        )
        out_json = self.repo / "out" / "diag_warn_scan.json"
        out_md = self.repo / "out" / "diag_warn_scan.md"
        diag_json = self.repo / "out" / "diag_warn_matrix.json"
        cmd = [
            sys.executable,
            str(SCRIPT_DIR / "zipwiz_governance_scan.py"),
            "--repo",
            str(self.repo),
            "--roots",
            f"{self.packaging},{self.runtime},{self.meta}",
            "--reference-roots",
            str(self.reference),
            "--out-json",
            str(out_json),
            "--out-md",
            str(out_md),
            "--diagnostic-mode",
            "--warn-threshold",
            "0",
            "--diagnostic-json",
            str(diag_json),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)
        payload = json.loads(diag_json.read_text(encoding="utf-8"))
        matrix = payload["diagnostic_matrix"]
        warn_summary = matrix["balanced"]["warn_summary"]
        self.assertEqual(warn_summary["warn_threshold"], 0)
        self.assertFalse(warn_summary["warn_threshold_exceeded"])
        self.assertEqual(warn_summary["warn_count"], 0)



if __name__ == "__main__":
    unittest.main()

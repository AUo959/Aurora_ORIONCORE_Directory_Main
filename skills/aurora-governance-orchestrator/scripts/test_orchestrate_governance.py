#!/usr/bin/env python3
"""Unit tests for aurora-governance-orchestrator."""

from __future__ import annotations

import argparse
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import orchestrate_governance as og  # noqa: E402


class OrchestratorTests(unittest.TestCase):
    def _args(self, **overrides):
        data = {
            "repo": ".",
            "mode": "full",
            "changed_paths": None,
            "draft_input": None,
            "draft_layer": None,
            "draft_type": None,
            "draft_auto_detect": False,
            "strictness": "balanced",
            "out_json": "/tmp/aurora_governance_orchestrator.json",
            "out_md": "/tmp/aurora_governance_orchestrator.md",
            "tmp_dir": "/tmp",
            "no_threadcore": False,
            "no_zipwiz": False,
            "no_script_governor": False,
            "no_narrative_tone": False,
            "no_repo_stabilizer": False,
            "no_canon": False,
        }
        data.update(overrides)
        return argparse.Namespace(**data)

    def test_root_rebasing_from_repo_marker(self):
        with tempfile.TemporaryDirectory() as td:
            repo_root = Path(td).resolve()
            (repo_root / "GUMAS_SIM_2.5").mkdir(parents=True, exist_ok=True)

            stale_root = (
                "/Users/travisstreets/Library/Mobile Documents/3L68KQB4HG~com~readdle~CommonDocuments/"
                "Documents/Aurora_ORIONCORE_Directory_Main/GUMAS_SIM_2.5"
            )
            entries = og.resolve_roots([stale_root], repo_root)

            self.assertEqual(len(entries), 1)
            self.assertTrue(entries[0]["exists"])
            self.assertTrue(entries[0]["rebased"])
            self.assertEqual(entries[0]["candidate_root"], str((repo_root / "GUMAS_SIM_2.5").resolve()))

    def test_unresolved_roots_emit_blocking_finding(self):
        with tempfile.TemporaryDirectory() as td:
            repo_root = Path(td).resolve()
            stale_root = (
                "/Users/travisstreets/Library/Mobile Documents/3L68KQB4HG~com~readdle~CommonDocuments/"
                "Documents/Aurora_ORIONCORE_Directory_Main/DOES_NOT_EXIST"
            )
            entries = og.resolve_roots([stale_root], repo_root)
            finding = og.make_unresolved_roots_finding("threadcore", entries)

            self.assertEqual(finding["severity"], "BLOCK")
            self.assertEqual(finding["rule_id"], "B_SCAN_ROOTS_UNRESOLVED")
            self.assertEqual(finding["blocking_scope"], "execution_health")

    def test_zipwiz_reference_only_block_is_downgraded(self):
        report = {
            "findings": [
                {
                    "severity": "BLOCK",
                    "rule_id": "B_MALFORMED_JSON",
                    "family": "evolution_evidence",
                    "file": "<evolution_map>",
                    "message": "Malformed JSON",
                    "suggested_fix": "Fix JSON syntax",
                }
            ]
        }
        findings = og.normalize_zipwiz_findings(report)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "WARN")
        self.assertEqual(findings[0]["blocking_scope"], "reference_only")

    def test_findings_include_compatibility_aliases_and_evidence_fallback(self):
        finding = og.make_finding(
            domain="zipwiz",
            severity="WARN",
            rule_id="ZIPWIZ_TEST_RULE",
            file="reports/sample.json",
            message="Sample finding",
            suggested_fix="Sample fix",
            family="test",
            source_tool="unit-test",
            blocking_scope="reference_only",
            raw_ref={"domain": "zipwiz", "finding_index": 0},
            evidence="",
        )

        self.assertEqual(finding["id"], "ZIPWIZ_TEST_RULE")
        self.assertEqual(finding["scope"], "reference_only")
        self.assertEqual(finding["evidence"], "See reports/sample.json")

    def test_scriptless_repo_behavior_is_info(self):
        report = {
            "summary": {
                "scanned_script_files": 0,
            },
            "findings": [],
        }
        findings = og.normalize_script_governor_findings(report)

        ids = {f["rule_id"] for f in findings}
        self.assertIn("I_SCRIPT_SURFACE_EMPTY", ids)

    def test_canon_optional_without_draft_input(self):
        args = self._args(mode="full", draft_input=None)
        routing = og.select_domains(args)

        self.assertNotIn("canon", routing["selected_domains"])

        args_with_draft = self._args(mode="full", draft_input="/tmp/draft.json")
        routing_with_draft = og.select_domains(args_with_draft)
        self.assertIn("canon", routing_with_draft["selected_domains"])

    def test_execution_failure_blocks_verdict(self):
        failure = og.make_execution_failure_finding(
            "threadcore",
            "threadcore scanner crashed",
            {"domain": "threadcore", "exit_code": 2},
        )

        verdict = og.build_verdict(
            [failure],
            selected_domains=["threadcore"],
            domain_reports={"threadcore": {"status": "failed", "summary": {}}},
            root_resolution={},
        )

        self.assertEqual(verdict["status"], "BLOCKED")
        self.assertEqual(verdict["promotion_readiness"], "NOT_READY")
        self.assertEqual(verdict["confidence"], "low")

    def test_output_schema_keys_and_verdict_enum(self):
        with tempfile.TemporaryDirectory() as td:
            repo_root = Path(td).resolve()
            args = self._args(
                repo=str(repo_root),
                no_threadcore=True,
                no_zipwiz=True,
                no_script_governor=True,
                no_repo_stabilizer=True,
                no_canon=True,
            )

            payload = og.run_orchestration(args)

            for key in [
                "scan_meta",
                "routing",
                "root_resolution",
                "domain_reports",
                "findings",
                "summary",
                "verdict",
            ]:
                self.assertIn(key, payload)

            self.assertIn(payload["verdict"]["status"], {"BLOCKED", "PROMOTE_WITH_REMEDIATION", "PROMOTE"})
            self.assertIn(payload["verdict"]["promotion_readiness"], {"NOT_READY", "CONDITIONAL", "READY"})
            self.assertIn(payload["verdict"]["confidence"], {"high", "medium", "low"})


if __name__ == "__main__":
    unittest.main()

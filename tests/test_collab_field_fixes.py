"""Tests for the 2026-07-04 field-findings wave: auto-claims, debt-scanner
remote verification, receipt orphan exclusions, pre-commit self-healing."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import publication_debt  # noqa: E402
import session_stop_hook as hook  # noqa: E402
import workspace_verify_precommit as wvp  # noqa: E402


class TestLiveRemoteBranches(unittest.TestCase):
    def test_parses_ls_remote_output(self):
        fake = SimpleNamespace(returncode=0, stdout=(
            "abc123\trefs/heads/main\n"
            "def456\trefs/heads/codex/some-branch\n"
            "aaa111\trefs/pull/7/head\n"
        ))
        orig = subprocess.run
        subprocess.run = lambda *a, **k: fake  # type: ignore
        try:
            branches = publication_debt._live_remote_branches(Path("."))
        finally:
            subprocess.run = orig
        self.assertEqual(branches, {"main", "codex/some-branch"})

    def test_unreachable_remote_returns_none(self):
        fake = SimpleNamespace(returncode=128, stdout="")
        orig = subprocess.run
        subprocess.run = lambda *a, **k: fake  # type: ignore
        try:
            self.assertIsNone(publication_debt._live_remote_branches(Path(".")))
        finally:
            subprocess.run = orig


class TestOrphanExemptions(unittest.TestCase):
    def test_mechanical_receipts_never_orphan(self):
        raw = ("catalog/session_state.json\n"
               "reports/automation/skill_sync_latest.json\n"
               "reports/analysis/workspace_verify_latest.json\n"
               "reports/analysis/workspace_scan_summary.json\n"
               "tools/real_work.py\n")
        orig = hook._git
        hook._git = lambda *a: raw  # type: ignore
        try:
            self.assertEqual(hook._git_uncommitted_tracked(), ["tools/real_work.py"])
        finally:
            hook._git = orig


class TestAutoClaim(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        claims = Path(self._dir.name)
        self._saved = (hook.CLAIMS_DIR, hook.AUTO_CLAIM_MARKER, hook._run_claim)
        hook.CLAIMS_DIR = claims
        hook.AUTO_CLAIM_MARKER = claims / ".claude_auto_claim"
        self.calls: list[tuple] = []
        hook._run_claim = lambda *a: (  # type: ignore
            self.calls.append(a), SimpleNamespace(returncode=0, stderr=""))[1]
        self.addCleanup(self._restore)

    def _restore(self):
        hook.CLAIMS_DIR, hook.AUTO_CLAIM_MARKER, hook._run_claim = self._saved

    def test_files_claim_and_marker(self):
        hook.file_auto_claim()
        self.assertTrue(hook.AUTO_CLAIM_MARKER.exists())
        self.assertEqual(self.calls[0][0], "create")
        claim_id = hook.AUTO_CLAIM_MARKER.read_text().strip()
        self.assertTrue(claim_id.startswith("claude-auto-"))

    def test_second_start_does_not_double_claim(self):
        hook.file_auto_claim()
        hook.file_auto_claim()
        self.assertEqual(len([c for c in self.calls if c[0] == "create"]), 1)

    def test_release_reads_marker_and_removes_it(self):
        hook.file_auto_claim()
        claim_id = hook.AUTO_CLAIM_MARKER.read_text().strip()
        hook.release_auto_claim()
        self.assertFalse(hook.AUTO_CLAIM_MARKER.exists())
        release = [c for c in self.calls if c[0] == "release"]
        self.assertEqual(release, [("release", "--claim-id", claim_id)])

    def test_release_without_marker_is_noop(self):
        hook.release_auto_claim()
        self.assertEqual(self.calls, [])


class TestProjectFocusStartup(unittest.TestCase):
    def test_surface_project_focus_prints_summary(self):
        calls = []
        orig = hook._run_project_focus
        hook._run_project_focus = lambda *a: (  # type: ignore
            calls.append(a), SimpleNamespace(returncode=0, stdout="Focus summary\n", stderr="")
        )[1]
        try:
            buf = StringIO()
            with redirect_stdout(buf):
                hook.surface_project_focus()
        finally:
            hook._run_project_focus = orig
        self.assertEqual(calls, [("--summary",)])
        self.assertIn("Focus summary", buf.getvalue())

    def test_surface_project_focus_is_advisory_on_failure(self):
        orig = hook._run_project_focus
        hook._run_project_focus = lambda *a: SimpleNamespace(  # type: ignore
            returncode=1, stdout="", stderr="broken registry\n"
        )
        try:
            buf = StringIO()
            with redirect_stdout(buf):
                hook.surface_project_focus()
        finally:
            hook._run_project_focus = orig
        self.assertIn("project focus skipped: broken registry", buf.getvalue())


class TestPrecommitClassification(unittest.TestCase):
    def test_only_pure_regenerable_sets_qualify(self):
        self.assertTrue({"repo_head_match"}.issubset(wvp.REGENERABLE_CHECKS))
        self.assertTrue(
            {"repo_head_match", "manifest_top_level_coverage",
             "repo_branch_match"}.issubset(wvp.REGENERABLE_CHECKS))
        self.assertFalse(
            {"repo_head_match", "secret_scan"}.issubset(wvp.REGENERABLE_CHECKS))

    def test_blocking_checks_extraction(self):
        import json
        out = json.dumps({"findings": [
            {"check": "a", "blocking": True},
            {"check": "b", "blocking": False},
        ]})
        self.assertEqual(wvp._blocking_checks(out), {"a"})
        self.assertIsNone(wvp._blocking_checks("garbage"))


if __name__ == "__main__":
    unittest.main()

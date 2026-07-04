"""Tests for session_state_io extensions: handoff spill, archival,
record-commits, claim guard — and the stop hook's orphan auto-resolve."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import session_state_io as sio  # noqa: E402
from test_session_state_check import _valid_state  # noqa: E402


class _TempStateMixin(unittest.TestCase):
    """Redirect all of sio's filesystem anchors into a temp directory."""

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.root = Path(self._dir.name)
        (self.root / "catalog").mkdir()
        self.path = self.root / "catalog" / "session_state.json"
        self.path.write_text(sio.dumps_canonical(_valid_state()))

        self._saved = {n: getattr(sio, n) for n in
                       ("STATE_PATH", "HANDOFF_DIR", "ARCHIVE_PATH", "load", "save")}
        sio.STATE_PATH = self.path
        sio.HANDOFF_DIR = self.root / "catalog" / "handoffs"
        sio.ARCHIVE_PATH = self.root / "catalog" / "session_state_archive.json"
        orig_load, orig_save = self._saved["load"], self._saved["save"]
        sio.load = lambda path=None: orig_load(path or self.path)  # type: ignore
        sio.save = lambda state, path=None, **kw: orig_save(state, path or self.path, **kw)  # type: ignore
        self.addCleanup(lambda: [setattr(sio, n, v) for n, v in self._saved.items()])

    def _ns(self, **kw):
        defaults = {"platform": "claude-code", "force": False}
        defaults.update(kw)
        return argparse.Namespace(**defaults)

    def _state(self) -> dict:
        return json.loads(self.path.read_text())


class TestHandoffSpill(_TempStateMixin):
    def test_short_detail_stays_inline(self):
        rc = sio.op_suspend_active(self._ns(next_step="go", next_step_detail="Short note."))
        self.assertEqual(rc, 0)
        self.assertEqual(self._state()["active_task"]["next_step_detail"], "Short note.")
        self.assertFalse(sio.HANDOFF_DIR.exists())

    def test_long_detail_spills_to_handoff_file(self):
        long = "First line of the narrative.\n" + ("x" * 1200)
        rc = sio.op_suspend_active(self._ns(next_step="resume lane", next_step_detail=long))
        self.assertEqual(rc, 0)
        inline = self._state()["active_task"]["next_step_detail"]
        self.assertLess(len(inline), 300)
        self.assertIn("catalog/handoffs/", inline)
        handoffs = list(sio.HANDOFF_DIR.glob("*.md"))
        self.assertEqual(len(handoffs), 1)
        content = handoffs[0].read_text()
        self.assertIn("x" * 1200, content)
        self.assertIn("resume lane", content)


class TestArchiveCompleted(_TempStateMixin):
    def _bulk_complete(self, n: int):
        state = self._state()
        state["completed_tasks"] = [
            {"id": f"task-{i}", "status": "completed"} for i in range(n)]
        self.path.write_text(sio.dumps_canonical(state))

    def test_under_keep_is_noop(self):
        self._bulk_complete(5)
        self.assertEqual(sio.op_archive_completed(self._ns(keep=10)), 0)
        self.assertEqual(len(self._state()["completed_tasks"]), 5)
        self.assertFalse(sio.ARCHIVE_PATH.exists())

    def test_archives_oldest_keeps_newest(self):
        self._bulk_complete(15)
        self.assertEqual(sio.op_archive_completed(self._ns(keep=10)), 0)
        remain = [t["id"] for t in self._state()["completed_tasks"]]
        self.assertEqual(remain, [f"task-{i}" for i in range(5, 15)])
        archive = json.loads(sio.ARCHIVE_PATH.read_text())
        self.assertEqual([t["id"] for t in archive["completed_tasks"]],
                         [f"task-{i}" for i in range(5)])

    def test_second_archive_appends_without_duplicates(self):
        self._bulk_complete(15)
        sio.op_archive_completed(self._ns(keep=10))
        self._bulk_complete(15)  # ids overlap with archived ones
        sio.op_archive_completed(self._ns(keep=10))
        archive = json.loads(sio.ARCHIVE_PATH.read_text())
        ids = [t["id"] for t in archive["completed_tasks"]]
        self.assertEqual(len(ids), len(set(ids)))


class TestRecordCommits(_TempStateMixin):
    def test_records_new_commits_and_head(self):
        repo = self.root / "gitrepo"
        repo.mkdir()
        run = lambda *c: subprocess.run(c, cwd=repo, capture_output=True, check=True)
        run("git", "init", "-q", "-b", "main")
        run("git", "-c", "user.email=t@t", "-c", "user.name=t",
            "commit", "-q", "--allow-empty", "-m", "first commit")
        run("git", "-c", "user.email=t@t", "-c", "user.name=t",
            "commit", "-q", "--allow-empty", "-m", "second commit")
        saved_root = sio.REPO_ROOT
        sio.REPO_ROOT = repo
        self.addCleanup(lambda: setattr(sio, "REPO_ROOT", saved_root))

        # invalidate known sha so the tool falls back to last-10
        state = self._state()
        state["known_state"]["main_sha"] = "f" * 40
        self.path.write_text(sio.dumps_canonical(state))

        rc = sio.op_record_commits(self._ns(platform="codex"))
        self.assertEqual(rc, 0)
        state = self._state()
        summaries = [c["summary"] for c in state["recent_commits"]]
        self.assertIn("second commit", summaries)
        self.assertEqual(state["recent_commits"][0]["platform"], "codex")
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                              capture_output=True, text=True).stdout.strip()
        self.assertEqual(state["known_state"]["main_sha"], head)


class TestClaimGuard(_TempStateMixin):
    def _write_claim(self, platform: str, paths: list[str], *,
                     status: str = "active", posture: str = "exclusive_paths"):
        claims = self.root / "catalog" / "session_claims"
        claims.mkdir(exist_ok=True)
        expires = (datetime.now(timezone.utc) + timedelta(hours=2)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        (claims / f"{platform}-test.json").write_text(json.dumps({
            "schema_version": 2, "claim_id": f"{platform}-test", "platform": platform,
            "task": "test-task", "repo": "root", "paths": paths, "status": status,
            "posture": posture, "expires_at": expires,
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }))

    def test_other_platform_active_claim_blocks(self):
        self._write_claim("codex", ["catalog/session_state.json"])
        blockers = sio.blocking_claims("claude-code", self.root)
        self.assertEqual(len(blockers), 1)
        self.assertEqual(blockers[0]["platform"], "codex")

    def test_root_wide_claim_blocks(self):
        self._write_claim("codex", ["."])
        self.assertTrue(sio.blocking_claims("claude-code", self.root))

    def test_own_platform_claim_does_not_block(self):
        self._write_claim("claude-code", ["catalog/session_state.json"])
        self.assertEqual(sio.blocking_claims("claude-code", self.root), [])

    def test_released_claim_does_not_block(self):
        self._write_claim("codex", ["catalog/session_state.json"], status="released")
        self.assertEqual(sio.blocking_claims("claude-code", self.root), [])

    def test_non_overlapping_claim_does_not_block(self):
        self._write_claim("codex", ["GUMAS_SIM_2.5/CanonRec"])
        self.assertEqual(sio.blocking_claims("claude-code", self.root), [])


class TestOrphanAutoResolve(unittest.TestCase):
    def test_marker_with_committed_files_is_deleted(self):
        import session_stop_hook as hook

        with tempfile.TemporaryDirectory() as td:
            claims = Path(td) / "session_claims"
            claims.mkdir()
            resolved = claims / ".orphan_claude-code_1.json"
            resolved.write_text(json.dumps(
                {"uncommitted_files": ["docs/some_committed_file.md"]}))
            live = claims / ".orphan_claude-code_2.json"
            live.write_text(json.dumps({"uncommitted_files": ["still/dirty.py"]}))

            saved_dir = hook.CLAIMS_DIR
            saved_tracked = hook._git_uncommitted_tracked
            saved_warn = hook._debt_staleness_warning
            hook.CLAIMS_DIR = claims
            hook._git_uncommitted_tracked = lambda: ["still/dirty.py"]
            hook._debt_staleness_warning = lambda: None
            try:
                hook.check_orphans()
            finally:
                hook.CLAIMS_DIR = saved_dir
                hook._git_uncommitted_tracked = saved_tracked
                hook._debt_staleness_warning = saved_warn

            self.assertFalse(resolved.exists(), "resolved marker should be deleted")
            self.assertTrue(live.exists(), "marker with dirty files must remain")


if __name__ == "__main__":
    unittest.main()

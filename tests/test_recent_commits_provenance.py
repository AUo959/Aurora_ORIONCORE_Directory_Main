"""recent_commits provenance comes from the commit, not from the sync.

Regression guard for the defect found 2026-09-24: record-commits and the Stop
hook stamped every newly seen commit with the sync's own date and the platform
running the sync, so a Codex sync relabelled six Claude-authored commits as
"codex" and nine of ten entries carried the sync day instead of the commit day.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import session_state_io as sio  # noqa: E402
import session_stop_hook as hook  # noqa: E402
from test_session_state_check import _valid_state  # noqa: E402

CLAUDE_TRAILERS = (
    "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
    "Claude-Session: https://claude.ai/code/session_TEST"
)


class _GitRepo(unittest.TestCase):
    """Temp repo with one trailer-less commit and one Claude-attributed commit."""

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.repo = Path(self._dir.name) / "repo"
        self.repo.mkdir()
        self._git("init", "-q", "-b", "main")
        # Committed 2026-01-02 UTC, no trailer: the shape of every Codex commit.
        self._commit("codex-shaped commit", "2026-01-02T03:00:00+00:00")
        # Committed 23:30 at UTC-4 on 2026-01-05 == 2026-01-06 UTC, Claude trailer.
        self._commit("claude-shaped commit\n\n" + CLAUDE_TRAILERS,
                     "2026-01-05T23:30:00-04:00")

    def _git(self, *args, env=None):
        return subprocess.run(["git", *args], cwd=self.repo,  # noqa: S603, S607 - fixture git in a temp repo
                              capture_output=True, text=True, check=True, env=env).stdout.strip()

    def _commit(self, message, when):
        env = {**os.environ, "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when}
        self._git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q",
                  "--allow-empty", "-m", message, env=env)


class PlatformFromTrailersTest(unittest.TestCase):
    def test_claude_coauthor_trailer(self):
        self.assertEqual(sio.platform_from_trailers(
            "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"), "claude-code")

    def test_claude_session_trailer_alone(self):
        self.assertEqual(sio.platform_from_trailers(
            "Claude-Session: https://claude.ai/code/session_x"), "claude-code")

    def test_no_trailer_is_codex(self):
        self.assertEqual(sio.platform_from_trailers(""), "codex")

    def test_other_bot_trailers_are_not_claude(self):
        self.assertEqual(sio.platform_from_trailers(
            "Co-authored-by: dependabot[bot] <support@github.com>"), "codex")


class CommitRecordsTest(_GitRepo):
    def test_records_carry_commit_date_and_trailer_platform(self):
        recs = sio.commit_records(self.repo, "-10")
        self.assertEqual([r["summary"] for r in recs],
                         ["claude-shaped commit", "codex-shaped commit"])
        claude, codex = recs
        self.assertEqual(claude["platform"], "claude-code")
        self.assertEqual(codex["platform"], "codex")
        self.assertEqual(codex["date"], "2026-01-02")
        # Normalised to UTC: 23:30 at UTC-4 is the next day.
        self.assertEqual(claude["date"], "2026-01-06")

    def test_unresolvable_revision_yields_empty(self):
        self.assertEqual(sio.commit_records(self.repo, "f" * 40 + "..HEAD"), [])


class MergeRecentCommitsTest(unittest.TestCase):
    def test_orders_newest_date_first_and_caps_oldest(self):
        existing = [{"sha": f"e{i}", "date": f"2026-01-{20 - i:02d}"} for i in range(10)]
        late_but_old = [{"sha": "old", "date": "2026-01-01"}]
        merged, added = sio.merge_recent_commits(existing, late_but_old, cap=10)
        self.assertEqual(added, 1)
        # Recorded late but committed earliest: the cap drops it, not a newer one.
        self.assertNotIn("old", [e["sha"] for e in merged])
        self.assertEqual(merged[0]["sha"], "e0")

    def test_does_not_duplicate_known_shas(self):
        existing = [{"sha": "a", "date": "2026-01-03"}]
        merged, added = sio.merge_recent_commits(existing, [{"sha": "a", "date": "2026-01-03"}])
        self.assertEqual((len(merged), added), (1, 0))


class RecordCommitsIsRunnerIndependentTest(_GitRepo):
    def setUp(self):
        super().setUp()
        self.state_path = Path(self._dir.name) / "session_state.json"
        saved = {n: getattr(sio, n) for n in ("REPO_ROOT", "STATE_PATH", "load", "save")}
        self.addCleanup(lambda: [setattr(sio, n, v) for n, v in saved.items()])
        sio.REPO_ROOT = self.repo
        sio.STATE_PATH = self.state_path
        orig_load, orig_save = saved["load"], saved["save"]
        sio.load = lambda path=None: orig_load(path or self.state_path)  # type: ignore
        sio.save = lambda state, path=None: orig_save(state, path or self.state_path)  # type: ignore

    def _run(self, platform, **kw):
        state = _valid_state()
        state["recent_commits"] = kw.pop("existing", [])
        state.setdefault("known_state", {})["main_sha"] = "f" * 40  # force last-10 path
        self.state_path.write_text(sio.dumps_canonical(state))
        ns = argparse.Namespace(platform=platform, force=False, **kw)
        self.assertEqual(sio.op_record_commits(ns), 0)
        return sio.load()["recent_commits"]

    def test_same_labels_whichever_platform_runs_the_sync(self):
        as_codex = self._run("codex")
        as_claude = self._run("claude-code")
        self.assertEqual(as_codex, as_claude)
        by_summary = {c["summary"]: c for c in as_codex}
        self.assertEqual(by_summary["claude-shaped commit"]["platform"], "claude-code")
        self.assertEqual(by_summary["codex-shaped commit"]["platform"], "codex")
        # Neither entry carries the sync day.
        self.assertEqual(by_summary["codex-shaped commit"]["date"], "2026-01-02")

    def test_reattribute_repairs_entries_written_by_the_old_logic(self):
        claude_sha = self._git("rev-parse", "--short", "HEAD")
        stale = [{"sha": claude_sha, "date": "2099-12-31", "platform": "codex",
                  "summary": "claude-shaped commit"}]
        out = self._run("codex", existing=stale, reattribute=True)
        entry = next(c for c in out if c["sha"] == claude_sha)
        self.assertEqual((entry["platform"], entry["date"]), ("claude-code", "2026-01-06"))

    def test_without_reattribute_existing_entries_are_left_alone(self):
        claude_sha = self._git("rev-parse", "--short", "HEAD")
        stale = [{"sha": claude_sha, "date": "2099-12-31", "platform": "codex",
                  "summary": "claude-shaped commit"}]
        out = self._run("codex", existing=stale)
        entry = next(c for c in out if c["sha"] == claude_sha)
        self.assertEqual(entry["platform"], "codex")


class StopHookUsesCommitProvenanceTest(_GitRepo):
    def test_hook_labels_commits_by_trailer_not_by_hook_platform(self):
        saved = hook.REPO_ROOT
        hook.REPO_ROOT = self.repo
        self.addCleanup(lambda: setattr(hook, "REPO_ROOT", saved))
        state = _valid_state()
        state["recent_commits"] = []
        state.setdefault("known_state", {})["main_sha"] = ""
        head = self._git("rev-parse", "HEAD")
        updated, _ = hook._update_state(state, head)
        by_summary = {c["summary"]: c for c in updated["recent_commits"]}
        # The hook is Claude Code's, yet the trailer-less commit stays codex.
        self.assertEqual(by_summary["codex-shaped commit"]["platform"], "codex")
        self.assertEqual(by_summary["claude-shaped commit"]["platform"], "claude-code")
        self.assertEqual(by_summary["codex-shaped commit"]["date"], "2026-01-02")


if __name__ == "__main__":
    unittest.main()

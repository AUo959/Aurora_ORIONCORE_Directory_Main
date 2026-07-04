"""Tests for tools/session_state_merge.py — the structural 3-way merge driver."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import session_state_merge as ssm  # noqa: E402
from test_session_state_check import _valid_state  # noqa: E402


def _fork(base: dict) -> tuple[dict, dict]:
    return copy.deepcopy(base), copy.deepcopy(base)


class TestMergeStates(unittest.TestCase):
    def test_identical_sides_pass_through(self):
        base = _valid_state()
        ours, theirs = _fork(base)
        self.assertEqual(ssm.merge_states(base, ours, theirs), base)

    def test_one_side_changed_wins(self):
        base = _valid_state()
        ours, theirs = _fork(base)
        ours["last_session_summary"] = "Ours did work."
        ours["last_updated"] = "2026-07-04T02:00:00Z"
        merged = ssm.merge_states(base, ours, theirs)
        self.assertEqual(merged["last_session_summary"], "Ours did work.")
        self.assertEqual(merged["last_updated"], "2026-07-04T02:00:00Z")

    def test_completed_tasks_union_by_id(self):
        base = _valid_state()
        ours, theirs = _fork(base)
        ours["completed_tasks"].append({"id": "ours-done", "status": "completed"})
        theirs["completed_tasks"].append({"id": "theirs-done", "status": "completed"})
        merged = ssm.merge_states(base, ours, theirs)
        ids = [t["id"] for t in merged["completed_tasks"]]
        self.assertIn("ours-done", ids)
        self.assertIn("theirs-done", ids)
        self.assertEqual(len(ids), len(set(ids)))

    def test_pending_removal_wins_over_stale_presence(self):
        """One side completes (removes) an item; the other still carries it."""
        base = _valid_state()
        ours, theirs = _fork(base)
        # ours completes note-1: removes from pending, records completion
        ours["pending_for_next_session"] = []
        ours["completed_tasks"].append({"id": "note-1", "status": "completed"})
        ours["last_updated"] = "2026-07-04T03:00:00Z"
        # theirs merely touches something else
        theirs["last_session_summary"] = "Unrelated."
        theirs["last_updated"] = "2026-07-04T02:00:00Z"
        merged = ssm.merge_states(base, ours, theirs)
        self.assertEqual(merged["pending_for_next_session"], [])
        self.assertIn("note-1", [t["id"] for t in merged["completed_tasks"]])

    def test_pending_additions_from_both_sides_kept(self):
        base = _valid_state()
        ours, theirs = _fork(base)
        ours["pending_for_next_session"].append(
            {"id": "ours-new", "description": "From ours."})
        theirs["pending_for_next_session"].append(
            {"id": "theirs-new", "description": "From theirs."})
        merged = ssm.merge_states(base, ours, theirs)
        ids = [p["id"] for p in merged["pending_for_next_session"]]
        self.assertIn("ours-new", ids)
        self.assertIn("theirs-new", ids)

    def test_both_modified_item_takes_newer_side(self):
        base = _valid_state()
        ours, theirs = _fork(base)
        ours["pending_for_next_session"][0]["description"] = "Ours edit."
        ours["last_updated"] = "2026-07-04T01:00:00Z"
        theirs["pending_for_next_session"][0]["description"] = "Theirs edit."
        theirs["last_updated"] = "2026-07-04T02:00:00Z"
        merged = ssm.merge_states(base, ours, theirs)
        self.assertEqual(merged["pending_for_next_session"][0]["description"],
                         "Theirs edit.")

    def test_recent_commits_union_capped_newest_first(self):
        base = _valid_state()
        base["recent_commits"] = [{"sha": f"aaa{i:04x}", "date": "2026-07-01",
                                   "platform": "codex", "summary": f"c{i}"}
                                  for i in range(9)]
        ours, theirs = _fork(base)
        ours["recent_commits"].insert(0, {"sha": "bbb0001", "date": "2026-07-04",
                                          "platform": "claude-code", "summary": "ours"})
        ours["last_updated"] = "2026-07-04T05:00:00Z"
        theirs["recent_commits"].insert(0, {"sha": "ccc0001", "date": "2026-07-03",
                                            "platform": "codex", "summary": "theirs"})
        merged = ssm.merge_states(base, ours, theirs)
        shas = [c["sha"] for c in merged["recent_commits"]]
        self.assertEqual(len(shas), 10)
        self.assertEqual(shas[0], "bbb0001")
        self.assertIn("ccc0001", shas)

    def test_next_step_detail_both_appended_keeps_both(self):
        base = _valid_state()
        base["active_task"]["next_step_detail"] = "Base narrative."
        ours, theirs = _fork(base)
        ours["active_task"]["next_step_detail"] = "Base narrative.\nOurs continuation."
        theirs["active_task"]["next_step_detail"] = "Base narrative.\nTheirs continuation."
        merged = ssm.merge_states(base, ours, theirs)
        detail = merged["active_task"]["next_step_detail"]
        self.assertIn("Ours continuation.", detail)
        self.assertIn("Theirs continuation.", detail)
        self.assertTrue(detail.startswith("Base narrative."))

    def test_snapshot_block_takes_newer_side(self):
        base = _valid_state()
        ours, theirs = _fork(base)
        ours["known_state"] = {"main_sha": "a" * 40}
        ours["last_updated"] = "2026-07-04T01:00:00Z"
        theirs["known_state"] = {"main_sha": "b" * 40}
        theirs["last_updated"] = "2026-07-04T02:00:00Z"
        merged = ssm.merge_states(base, ours, theirs)
        self.assertEqual(merged["known_state"]["main_sha"], "b" * 40)

    def test_replay_of_2026_07_04_concurrency(self):
        """The real event: Codex closes out a PR lane while Claude completes a
        queue item and adds new ones. Everything must survive."""
        base = _valid_state()
        codex, claude = _fork(base)
        codex["active_task"]["next_step_detail"] = "Adapter PR opened."
        codex["last_session_summary"] = "Codex fixed PR findings."
        codex["last_updated"] = "2026-07-04T01:55:03Z"
        codex["completed_tasks"].append({"id": "codex-hygiene", "status": "completed"})

        claude["pending_for_next_session"] = []  # completed note-1
        claude["completed_tasks"].append({"id": "note-1", "status": "completed"})
        claude["pending_for_next_session"].append(
            {"id": "publish-retry", "priority": "high", "assigned_to": "codex",
             "description": "Retry the publish."})
        claude["last_updated"] = "2026-07-04T03:12:00Z"

        merged = ssm.merge_states(base, codex, claude)
        completed = {t["id"] for t in merged["completed_tasks"]}
        self.assertLessEqual({"codex-hygiene", "note-1", "task-0"}, completed)
        pending_ids = [p["id"] for p in merged["pending_for_next_session"]]
        self.assertEqual(pending_ids, ["publish-retry"])
        self.assertEqual(merged["active_task"]["next_step_detail"], "Adapter PR opened.")
        self.assertEqual(merged["last_updated"], "2026-07-04T03:12:00Z")


class TestDriverCli(unittest.TestCase):
    def _write(self, d: dict) -> Path:
        fh = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(d, fh)
        fh.close()
        self.addCleanup(Path(fh.name).unlink)
        return Path(fh.name)

    def test_clean_merge_writes_canonical_to_ours(self):
        base = _valid_state()
        ours, theirs = _fork(base)
        theirs["completed_tasks"].append({"id": "extra", "status": "completed"})
        theirs["last_updated"] = "2026-07-04T09:00:00Z"
        o_path = self._write(ours)
        rc = ssm.main(["ssm", str(self._write(base)), str(o_path), str(self._write(theirs))])
        self.assertEqual(rc, 0)
        merged = json.loads(o_path.read_text())
        self.assertIn("extra", [t["id"] for t in merged["completed_tasks"]])
        self.assertTrue(o_path.read_text().endswith("\n"))

    def test_unparseable_side_falls_back_to_conflict(self):
        bad = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        bad.write("{not json")
        bad.close()
        self.addCleanup(Path(bad.name).unlink)
        rc = ssm.main(["ssm", str(self._write(_valid_state())),
                       str(self._write(_valid_state())), bad.name])
        self.assertEqual(rc, 1)

    def test_contract_violating_merge_falls_back_to_conflict(self):
        base = _valid_state()
        ours, theirs = _fork(base)
        # theirs introduces a malformed pending entry; merged result must be refused
        theirs["pending_for_next_session"].append({"item": "legacy", "detail": "bad"})
        theirs["last_updated"] = "2026-07-04T09:00:00Z"
        o_path = self._write(ours)
        before = o_path.read_text()
        rc = ssm.main(["ssm", str(self._write(base)), str(o_path), str(self._write(theirs))])
        self.assertEqual(rc, 1)
        self.assertEqual(o_path.read_text(), before)


if __name__ == "__main__":
    unittest.main()

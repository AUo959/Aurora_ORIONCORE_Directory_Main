"""Tests for tools/session_state_check.py — the session-state queue contract."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import session_state_check as ssc  # noqa: E402


def _lifecycle_item(item_id: str, *, status: str = "ready") -> dict:
    item = {
        "id": item_id,
        "status": status,
        "priority": "medium",
        "assigned_to": "either",
        "kind": "work",
        "repo": "root",
        "description": f"Work item {item_id}.",
        "created_at": "2026-07-02T00:00:00Z",
        "updated_at": "2026-07-02T00:00:00Z",
        "next_action": "Perform the bounded next step.",
        "definition_of_done": "The change is implemented and validated.",
        "approval_required": False,
    }
    if status in {"ready", "waiting", "parked"}:
        item["review_at"] = "2026-07-09T00:00:00Z"
    if status == "suspended":
        item["resume_by"] = "2026-07-09T00:00:00Z"
    return item


def _valid_state() -> dict:
    active = _lifecycle_item("task-1", status="suspended")
    active["assigned_to"] = "codex"
    return {
        "schema_version": 3,
        "protocol": {"on_session_start": [], "on_session_end": []},
        "active_task": active,
        "task_queue": [_lifecycle_item("task-2")],
        "completed_tasks": [{"id": "task-0", "status": "completed"}],
        "pending_for_next_session": [],
        "known_state": {"main_sha": "2ce76d4bb781c20ccf33d46dd55700b828769a33"},
        "last_updated": "2026-07-02T00:00:00Z",
        "last_platform": "codex",
    }


class TestValidate(unittest.TestCase):
    def test_valid_document_passes(self):
        self.assertEqual(ssc.validate(_valid_state()), [])

    def test_idle_active_slot_passes(self):
        state = _valid_state()
        state["active_task"] = None
        self.assertEqual(ssc.validate(state), [])

    def test_missing_top_level_key_flagged(self):
        state = _valid_state()
        del state["pending_for_next_session"]
        findings = ssc.validate(state)
        self.assertTrue(any("pending_for_next_session" in f for f in findings))

    def test_legacy_pending_entry_flagged(self):
        state = _valid_state()
        state["pending_for_next_session"].append(
            {"item": "old-report", "detail": "All done previously."}
        )
        findings = ssc.validate(state)
        self.assertTrue(any("deprecated and must be empty" in f for f in findings))

    def test_bad_priority_flagged(self):
        state = _valid_state()
        state["task_queue"][0]["priority"] = "urgent"
        findings = ssc.validate(state)
        self.assertTrue(any("priority 'urgent'" in f for f in findings))

    def test_bad_assigned_to_flagged(self):
        state = _valid_state()
        state["task_queue"][0]["assigned_to"] = "chatgpt"
        findings = ssc.validate(state)
        self.assertTrue(any("assigned_to 'chatgpt'" in f for f in findings))

    def test_duplicate_ids_across_open_work_flagged(self):
        state = _valid_state()
        state["task_queue"].append(copy.deepcopy(state["task_queue"][0]))
        findings = ssc.validate(state)
        self.assertTrue(any("duplicate id 'task-2'" in f for f in findings))

    def test_open_completed_duplicate_requires_reopen_provenance(self):
        state = _valid_state()
        state["completed_tasks"].append({"id": "task-2", "status": "completed"})
        findings = ssc.validate(state)
        self.assertTrue(any("intentionally reopened" in f for f in findings))

    def test_reopened_item_with_provenance_passes(self):
        state = _valid_state()
        state["completed_tasks"].append({"id": "task-2", "status": "completed"})
        state["task_queue"][0].update(
            {
                "reopened_at": "2026-07-03T00:00:00Z",
                "reopen_reason": "The earlier completion was recorded in error.",
            }
        )
        self.assertEqual(ssc.validate(state), [])

    def test_waiting_item_requires_trigger(self):
        state = _valid_state()
        state["task_queue"][0]["status"] = "waiting"
        state["task_queue"][0]["waiting_on"] = "external"
        findings = ssc.validate(state)
        self.assertTrue(any("concrete trigger" in f for f in findings))

    def test_owner_gate_requires_decision_packet(self):
        state = _valid_state()
        state["task_queue"][0].update(
            {
                "status": "waiting",
                "assigned_to": "owner",
                "waiting_on": "owner",
                "trigger": "Owner chooses a license.",
                "approval_required": True,
            }
        )
        findings = ssc.validate(state)
        self.assertTrue(any("kind='decision'" in f for f in findings))
        self.assertTrue(any("gate_scope" in f for f in findings))
        self.assertTrue(any("evidence_ref" in f for f in findings))
        self.assertTrue(any("decision_options" in f for f in findings))

    def test_suspended_task_requires_resume_by(self):
        state = _valid_state()
        del state["active_task"]["resume_by"]
        findings = ssc.validate(state)
        self.assertTrue(any("active_task.resume_by" in f for f in findings))

    def test_bad_timestamp_flagged(self):
        state = _valid_state()
        state["last_updated"] = "yesterday"
        findings = ssc.validate(state)
        self.assertTrue(any("last_updated" in f for f in findings))

    def test_bad_platform_flagged(self):
        state = _valid_state()
        state["last_platform"] = "cursor"
        findings = ssc.validate(state)
        self.assertTrue(any("last_platform" in f for f in findings))

    def test_bad_main_sha_flagged(self):
        state = _valid_state()
        state["known_state"]["main_sha"] = "not-a-sha"
        findings = ssc.validate(state)
        self.assertTrue(any("main_sha" in f for f in findings))

    def test_completed_task_without_id_flagged(self):
        state = _valid_state()
        state["completed_tasks"].append({"status": "completed"})
        findings = ssc.validate(state)
        self.assertTrue(any("completed_tasks[1]" in f for f in findings))

    def test_extra_unknown_fields_allowed(self):
        state = _valid_state()
        state["review_debt"] = []
        state["active_task"]["context_files"] = ["a.md"]
        self.assertEqual(ssc.validate(state), [])


class TestCheckFile(unittest.TestCase):
    def test_missing_file_exit_2(self):
        code, findings = ssc.check_file(Path("/nonexistent/session_state.json"))
        self.assertEqual(code, 2)
        self.assertTrue(findings)

    def test_invalid_json_exit_2(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            fh.write("{not json")
            path = Path(fh.name)
        try:
            code, _ = ssc.check_file(path)
            self.assertEqual(code, 2)
        finally:
            path.unlink()

    def test_valid_file_exit_0(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(_valid_state(), fh)
            path = Path(fh.name)
        try:
            code, findings = ssc.check_file(path)
            self.assertEqual((code, findings), (0, []))
        finally:
            path.unlink()

    def test_live_repo_state_is_valid(self):
        code, findings = ssc.check_file()
        self.assertEqual(findings, [])
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()

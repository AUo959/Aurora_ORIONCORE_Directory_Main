"""Tests for tools/session_state_io.py — the canonical session-state write path."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import session_state_io as sio  # noqa: E402
from test_session_state_check import _valid_state  # noqa: E402


class TestCanonicalSerialization(unittest.TestCase):
    def test_ascii_escaped_and_newline_terminated(self):
        text = sio.dumps_canonical({"k": "em—dash"})
        self.assertIn("em\\u2014dash", text)
        self.assertTrue(text.endswith("\n"))

    def test_matches_json_module_default_style(self):
        state = _valid_state()
        self.assertEqual(sio.dumps_canonical(state), json.dumps(state, indent=2) + "\n")

    def test_fmt_is_idempotent(self):
        state = _valid_state()
        once = sio.dumps_canonical(state)
        twice = sio.dumps_canonical(json.loads(once))
        self.assertEqual(once, twice)


class TestSave(unittest.TestCase):
    def _tmp(self, state: dict) -> Path:
        import tempfile

        fh = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(state, fh)
        fh.close()
        self.addCleanup(Path(fh.name).unlink)
        return Path(fh.name)

    def test_valid_state_written_canonically(self):
        path = self._tmp(_valid_state())
        findings = sio.save(json.loads(path.read_text()), path)
        self.assertEqual(findings, [])
        self.assertEqual(path.read_text(), sio.dumps_canonical(_valid_state()))

    def test_invalid_state_refused_file_untouched(self):
        path = self._tmp(_valid_state())
        before = path.read_text()
        bad = _valid_state()
        bad["task_queue"][0]["status"] = "queued"
        findings = sio.save(bad, path)
        self.assertTrue(findings)
        self.assertEqual(path.read_text(), before)


class TestMutations(unittest.TestCase):
    """Drive the op_* handlers against a temp state file."""

    def setUp(self):
        import tempfile

        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.path = Path(self._dir.name) / "session_state.json"
        self.path.write_text(sio.dumps_canonical(_valid_state()))
        self._orig = sio.STATE_PATH
        sio.STATE_PATH = self.path
        # load() default arg captured STATE_PATH at def time; patch via lambda
        self._orig_load = sio.load
        sio.load = lambda path=None: self._orig_load(path or self.path)  # type: ignore
        self._orig_save = sio.save
        sio.save = lambda state, path=None, **kw: self._orig_save(  # type: ignore
            state, path or self.path, **kw
        )
        self.addCleanup(self._restore)

    def _restore(self):
        sio.STATE_PATH = self._orig
        sio.load = self._orig_load
        sio.save = self._orig_save

    def _ns(self, **kw):
        import argparse

        defaults = {
            "platform": "claude-code",
            "approval_evidence": None,
            "review_at": None,
        }
        defaults.update(kw)
        return argparse.Namespace(**defaults)

    def test_complete_item_moves_to_completed(self):
        rc = sio.op_complete_item(self._ns(item_id="task-2", detail="done"))
        self.assertEqual(rc, 0)
        state = json.loads(self.path.read_text())
        self.assertNotIn("task-2", [p["id"] for p in state["task_queue"]])
        entry = next(t for t in state["completed_tasks"] if t["id"] == "task-2")
        self.assertEqual(entry["detail"], "done")
        self.assertEqual(entry["platform"], "claude-code")

    def test_complete_unknown_id_refused(self):
        self.assertEqual(sio.op_complete_item(self._ns(item_id="ghost", detail=None)), 1)

    def test_add_pending_validates(self):
        rc = sio.op_add_pending(self._ns(
            item_id="new-item", description="Do it.", priority="high", assigned_to="codex"))
        self.assertEqual(rc, 0)
        state = json.loads(self.path.read_text())
        added = next(p for p in state["task_queue"] if p["id"] == "new-item")
        self.assertEqual(added["status"], "ready")
        self.assertFalse(added["approval_required"])
        self.assertEqual(state["pending_for_next_session"], [])

    def test_add_pending_duplicate_id_refused(self):
        rc = sio.op_add_pending(self._ns(
            item_id="task-2", description="Dup of queue item.",
            priority="low", assigned_to="either"))
        self.assertEqual(rc, 1)
        state = json.loads(self.path.read_text())
        self.assertEqual(
            1,
            sum(1 for p in state["task_queue"] if p["id"] == "task-2"),
        )

    def test_add_owner_decision_normalizes_gate_fields(self):
        rc = sio.op_add_item(
            self._ns(
                item_id="license-decision",
                status="ready",
                priority="high",
                assigned_to="either",
                kind="work",
                repo="root",
                description="Select the public license.",
                created_at=None,
                review_at="2026-07-09T00:00:00Z",
                next_action="Choose a license from the evidence packet.",
                definition_of_done="The choice is recorded.",
                approval_required=True,
                waiting_on=None,
                trigger="Owner reviews the license options.",
                gate_scope="public_license_selection",
                evidence_ref=["LICENSE_REVIEW.md"],
                decision_option=["Apache-2.0", "Keep unlicensed"],
            )
        )
        self.assertEqual(rc, 0)
        state = json.loads(self.path.read_text())
        item = next(p for p in state["task_queue"] if p["id"] == "license-decision")
        self.assertEqual(item["status"], "waiting")
        self.assertEqual(item["kind"], "decision")
        self.assertEqual(item["assigned_to"], "owner")
        self.assertEqual(item["waiting_on"], "owner")

    def test_start_then_complete_active_clears_slot(self):
        state = _valid_state()
        state["active_task"] = None
        self.path.write_text(sio.dumps_canonical(state))
        self.assertEqual(sio.op_start_item(self._ns(item_id="task-2")), 0)
        started = json.loads(self.path.read_text())
        self.assertEqual(started["active_task"]["id"], "task-2")
        self.assertNotIn("task-2", [p["id"] for p in started["task_queue"]])

        self.assertEqual(
            sio.op_complete_active(self._ns(detail="Implemented and validated.")),
            0,
        )
        completed = json.loads(self.path.read_text())
        self.assertIsNone(completed["active_task"])
        self.assertIn("task-2", [p["id"] for p in completed["completed_tasks"]])

    def test_ready_item_reactivates_external_wait(self):
        state = _valid_state()
        state["task_queue"][0].update(
            {
                "status": "waiting",
                "waiting_on": "external",
                "trigger": "CI finishes.",
            }
        )
        self.path.write_text(sio.dumps_canonical(state))
        rc = sio.op_ready_item(
            self._ns(
                item_id="task-2",
                review_at="2026-07-10T00:00:00Z",
                next_action="Address the completed CI result.",
                assigned_to="codex",
                reason=None,
            )
        )
        self.assertEqual(rc, 0)
        item = json.loads(self.path.read_text())["task_queue"][0]
        self.assertEqual(item["status"], "ready")
        self.assertNotIn("waiting_on", item)
        self.assertNotIn("trigger", item)

    def test_ready_item_requires_reason_to_correct_owner_gate(self):
        state = _valid_state()
        state["task_queue"][0].update(
            {
                "status": "waiting",
                "assigned_to": "owner",
                "kind": "decision",
                "waiting_on": "owner",
                "trigger": "Owner reviews a routine test.",
                "approval_required": True,
                "gate_scope": "public_license_selection",
                "evidence_refs": ["tests/test_example.py"],
                "decision_options": ["Run test", "Skip test"],
            }
        )
        self.path.write_text(sio.dumps_canonical(state))
        args = self._ns(
            item_id="task-2",
            review_at="2026-07-10T00:00:00Z",
            next_action="Run the reversible validation.",
            assigned_to=None,
            reason=None,
        )
        self.assertEqual(sio.op_ready_item(args), 1)

        args.reason = "Reversible validation was incorrectly owner-gated."
        self.assertEqual(sio.op_ready_item(args), 0)
        item = json.loads(self.path.read_text())["task_queue"][0]
        self.assertEqual(item["status"], "ready")
        self.assertEqual(item["assigned_to"], "either")
        self.assertEqual(item["kind"], "work")
        self.assertFalse(item["approval_required"])
        self.assertIn("gate_reclassified_at", item)

    def test_wait_active_owner_gate_requires_decision_packet(self):
        rc = sio.op_wait_active(
            self._ns(
                waiting_on="owner",
                trigger="Owner selects the publication license.",
                review_at="2026-07-09T00:00:00Z",
                approval_required=True,
                gate_scope="public_license_selection",
                evidence_ref=["LICENSE.md"],
                decision_option=["Apache-2.0", "Keep private"],
            )
        )
        self.assertEqual(rc, 0)
        state = json.loads(self.path.read_text())
        self.assertIsNone(state["active_task"])
        queued = next(p for p in state["task_queue"] if p["id"] == "task-1")
        self.assertEqual(queued["status"], "waiting")
        self.assertEqual(queued["assigned_to"], "owner")
        self.assertTrue(queued["approval_required"])

    def test_owner_gated_completion_requires_evidence(self):
        state = _valid_state()
        state["task_queue"][0].update(
            {
                "status": "waiting",
                "assigned_to": "owner",
                "kind": "decision",
                "waiting_on": "owner",
                "trigger": "Owner selects the publication license.",
                "approval_required": True,
                "gate_scope": "public_license_selection",
                "evidence_refs": ["LICENSE.md"],
                "decision_options": ["Apache-2.0", "Keep private"],
            }
        )
        self.path.write_text(sio.dumps_canonical(state))
        self.assertEqual(
            sio.op_complete_item(self._ns(item_id="task-2", detail="Selected.")),
            1,
        )
        self.assertEqual(
            sio.op_complete_item(
                self._ns(
                    item_id="task-2",
                    detail="Selected Apache-2.0.",
                    approval_evidence="Owner decision receipt LICENSE-001.",
                )
            ),
            0,
        )
        completed = next(
            item
            for item in json.loads(self.path.read_text())["completed_tasks"]
            if item["id"] == "task-2"
        )
        self.assertEqual(completed["gate_scope"], "public_license_selection")
        self.assertEqual(
            completed["approval_evidence"], "Owner decision receipt LICENSE-001."
        )

    def test_set_summary_sets_one_shot_flag(self):
        rc = sio.op_set_summary(self._ns(text="Manual summary."))
        self.assertEqual(rc, 0)
        state = json.loads(self.path.read_text())
        self.assertEqual(state["last_session_summary"], "Manual summary.")
        self.assertTrue(state["_summary_set_manually"])

    def test_set_tool_version_updates_map(self):
        rc = sio.op_set_tool_version(self._ns(tool="node", version="26.5.0"))
        self.assertEqual(rc, 0)
        state = json.loads(self.path.read_text())
        self.assertEqual(state["tool_versions"]["node"], "26.5.0")
        self.assertEqual(state["last_platform"], "claude-code")

    def test_set_tool_version_refuses_non_object(self):
        state = _valid_state()
        state["tool_versions"] = []
        self.path.write_text(sio.dumps_canonical(state))
        rc = sio.op_set_tool_version(self._ns(tool="node", version="26.5.0"))
        self.assertEqual(rc, 1)
        state = json.loads(self.path.read_text())
        self.assertEqual(state["tool_versions"], [])

    def test_suspend_active(self):
        rc = sio.op_suspend_active(
            self._ns(
                next_step="resume_here",
                resume_by="2026-07-09T00:00:00Z",
                next_step_detail="Cold start notes.",
            )
        )
        self.assertEqual(rc, 0)
        state = json.loads(self.path.read_text())
        self.assertEqual(state["active_task"]["status"], "suspended")
        self.assertEqual(state["active_task"]["next_step"], "resume_here")
        self.assertEqual(
            state["active_task"]["resume_by"], "2026-07-09T00:00:00Z"
        )


class TestHookFlagLifecycle(unittest.TestCase):
    def test_stop_hook_clears_manual_flag_after_honoring(self):
        import session_stop_hook as hook

        state = _valid_state()
        state["_summary_set_manually"] = True
        state["last_session_summary"] = "Manual."
        updated, _ = hook._update_state(dict(state), "abc1234")
        self.assertNotIn("_summary_set_manually", updated)
        self.assertEqual(updated["last_session_summary"], "Manual.")


if __name__ == "__main__":
    unittest.main()

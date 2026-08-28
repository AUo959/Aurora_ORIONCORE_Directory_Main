"""Tests for the time-aware Aurora session queue audit."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import session_queue_health as health  # noqa: E402
from test_session_state_check import _valid_state  # noqa: E402


NOW = datetime(2026, 7, 5, tzinfo=timezone.utc)


def _write_inputs(tmp_path: Path, state: dict) -> tuple[Path, Path, Path]:
    root = tmp_path / "workspace"
    catalog = root / "catalog"
    catalog.mkdir(parents=True)
    state_path = catalog / "session_state.json"
    policy_path = catalog / "session_queue_policy.json"
    state_path.write_text(json.dumps(state), encoding="utf-8")
    policy_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "suspended_warning_days": 7,
                "suspended_review_days": 14,
                "owner_gate": {
                    "allowed_scopes": [
                        "public_license_selection",
                        "canon_promotion",
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    return root, state_path, policy_path


def _report(tmp_path: Path, state: dict) -> dict:
    root, state_path, policy_path = _write_inputs(tmp_path, state)
    return health.build_report(
        root,
        state_path=state_path,
        policy_path=policy_path,
        now=NOW,
        generated_at="2026-07-05T00:00:00Z",
    )


def test_counts_actionable_work_without_owner_approval(tmp_path: Path) -> None:
    state = _valid_state()
    state["active_task"] = None
    report = _report(tmp_path, state)

    assert report["status"] == "ready"
    assert report["summary"]["ready_count"] == 1
    assert report["summary"]["owner_gate_count"] == 0
    assert report["next_ready"][0]["id"] == "task-2"


def test_suspended_task_past_resume_date_needs_triage(tmp_path: Path) -> None:
    state = _valid_state()
    state["active_task"]["resume_by"] = "2026-07-04T00:00:00Z"
    report = _report(tmp_path, state)

    assert report["status"] == "attention"
    assert any(
        item["check"] == "suspended_task_review_due"
        for item in report["findings"]
    )


def test_due_queue_review_is_visible(tmp_path: Path) -> None:
    state = _valid_state()
    state["active_task"] = None
    state["task_queue"][0]["review_at"] = "2026-07-04T00:00:00Z"
    report = _report(tmp_path, state)

    assert report["summary"]["due_review_count"] == 1
    assert any(item["check"] == "queue_review_due" for item in report["findings"])


def test_non_policy_owner_gate_scope_blocks_health(tmp_path: Path) -> None:
    state = _valid_state()
    state["active_task"] = None
    state["task_queue"][0].update(
        {
            "status": "waiting",
            "assigned_to": "owner",
            "kind": "decision",
            "waiting_on": "owner",
            "trigger": "Owner decides whether routine tests may run.",
            "approval_required": True,
            "gate_scope": "routine_local_testing",
            "evidence_refs": ["tests/test_example.py"],
            "decision_options": ["Run tests", "Do not run tests"],
        }
    )
    report = _report(tmp_path, state)

    assert report["status"] == "blocked"
    assert report["summary"]["owner_gate_count"] == 1
    assert any(
        item["check"] == "owner_gate_scope_invalid" and item["blocking"]
        for item in report["findings"]
    )

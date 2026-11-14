"""Boundary, freshness, and CLI tests for Aurora Intelligent UI bridge."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import aurora_intelligent_ui_bridge as bridge  # noqa: E402


@pytest.fixture
def report():
    return {
        "schema_version": 1,
        "tool": "aurora_mission_control",
        "run_mode": "read_only",
        "mutation_posture": "advisory_only",
        "nested_repo_mutation": False,
        "generated_at": "2026-08-15T05:30:37Z",
        "status": "blocked",
        "summary": {
            "source_count": 1,
            "source_error_count": 0,
            "operator_inbox_count": 2,
            "approval_required_count": 1,
            "blocking_count": 0,
            "build_lanes": {"ready": 0, "attention": 0, "blocked": 1},
        },
        "source_reports": {"workspace_verify": {"status": "warn"}},
        "operator_inbox": [
            {
                "item_id": "i1",
                "title": "Verify workspace",
                "priority": "P1",
                "status": "open",
                "category": "validation",
                "source": "workspace_verify",
                "target_repo": "root",
                "approval_required": False,
                "blocking": False,
                "evidence_refs": ["tools/workspace_verify.py::status", "/private/path"],
                "recommended_next_action": "Review verification findings.",
                "mutation_posture": "advisory_only",
                "suggested_commands": ["should-not-export"],
            },
            {
                "item_id": "i2",
                "title": "Review restricted recovery candidates",
                "priority": "P2",
                "status": "open",
                "category": "recovery_review",
                "source": "recovery_index",
                "target_repo": "root",
                "approval_required": True,
                "blocking": False,
                "evidence_refs": ["reports/analysis/restricted_recovery_candidates.json"],
                "recommended_next_action": "Secret evidence",
                "mutation_posture": "advisory_only",
            },
        ],
        "build_lanes": [
            {
                "lane_id": "root-python",
                "title": "Python tooling",
                "status": "blocked",
                "missing_required_tools": ["sqlite3"],
                "mutation_posture": "readiness_only",
                "evidence_refs": ["reports/analysis/devkit.json"],
            }
        ],
        "private_state": {"do_not_export": True},
    }


NOW = datetime(2026, 10, 15, 20, 0, tzinfo=timezone.utc)
DIGEST = hashlib.sha256(b"fixture").hexdigest()


def make(report, now=NOW):
    return bridge.build_snapshot(report, input_sha256=DIGEST, now=now)


def test_existing_report_stays_read_only_and_is_stale(report):
    original = copy.deepcopy(report)
    data = make(report)
    assert data["source"]["freshness"] == "stale"
    assert data["source"]["generated_at"] == "2026-08-15T05:30:37+00:00"
    assert data["source"]["sha256"] == DIGEST
    assert data["health"]["inbox_items"] == 2
    assert data["health"]["lanes"]["blocked"] == 1
    assert data["authority"]["canon_write"] is False
    assert data["authority"]["runtime_execution"] is False
    assert data["authority"]["nested_repo_mutation"] is False
    assert "private_state" not in data
    assert report == original


def test_evidence_and_commands_are_allowlisted(report):
    data = make(report)
    assert data["operator_inbox"][0]["evidence_refs"] == [
        "tools/workspace_verify.py::status"
    ]
    assert data["operator_inbox"][1]["evidence_restricted"] is True
    assert data["operator_inbox"][1]["evidence_refs"] == []
    assert "Secret" not in data["operator_inbox"][1]["next_action"]
    assert "suggested_commands" not in data["operator_inbox"][0]


@pytest.mark.parametrize("key,value", [
    ("run_mode", "execute"), ("mutation_posture", "write_allowed"),
    ("nested_repo_mutation", True), ("schema_version", 2), ("tool", "other"),
])
def test_rejects_source_contract_violation(report, key, value):
    report[key] = value
    with pytest.raises(bridge.BridgeError):
        make(report)


def test_rejects_item_permission_change(report):
    report["operator_inbox"][0]["mutation_posture"] = "can_execute"
    with pytest.raises(bridge.BridgeError):
        make(report)


def test_rejects_inconsistent_summary(report):
    report["summary"]["operator_inbox_count"] = 77
    with pytest.raises(bridge.BridgeError, match="mismatch"):
        make(report)


def test_freshness_and_future_timestamp(report):
    generated = bridge.timestamp(report["generated_at"], "source")
    assert make(report, now=generated + timedelta(hours=47))["source"]["freshness"] == "fresh"
    assert make(report, now=generated + timedelta(hours=49))["source"]["freshness"] == "stale"
    with pytest.raises(bridge.BridgeError, match="future"):
        make(report, now=generated - timedelta(hours=1))


def test_naive_timestamp_rejected(report):
    report["generated_at"] = "2026-08-15T05:30:37"
    with pytest.raises(bridge.BridgeError, match="offset"):
        make(report)


def test_cli_no_implicit_write_and_explicit_export(report, tmp_path, capsys):
    source = tmp_path / "source.json"
    raw = json.dumps(report).encode()
    source.write_bytes(raw)
    assert bridge.main(["--input", str(source)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["source"]["sha256"] == hashlib.sha256(raw).hexdigest()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["source.json"]
    out = tmp_path / "bridge.json"
    assert bridge.main(["--input", str(source), "--output", str(out)]) == 0
    assert out.exists()


def test_cli_fails_closed_for_bad_input(tmp_path, capsys):
    source = tmp_path / "invalid.json"
    source.write_text('{"schema_version": 99}', encoding="utf-8")
    assert bridge.main(["--input", str(source)]) == 2
    assert "unsupported" in capsys.readouterr().err

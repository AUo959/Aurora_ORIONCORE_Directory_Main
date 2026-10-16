"""End-to-end HTTP security and freshness checks for Intelligent UI retrieval."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import aurora_intelligent_ui_service as service  # noqa: E402

TOKEN = "correct-horse-high-entropy-test-token-12345"
WRONG = "wrong-token"
CONFIG = {service.TOKEN_HASH_ENV: hashlib.sha256(TOKEN.encode()).hexdigest()}
ENDPOINT = "/v1/mission-control/snapshot"


@pytest.fixture
def saved_report():
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
                "item_id": "p1",
                "title": "Review validation findings",
                "category": "validation",
                "priority": "P1",
                "source": "workspace_verify",
                "target_repo": "root",
                "status": "open",
                "approval_required": False,
                "blocking": False,
                "mutation_posture": "advisory_only",
                "evidence_refs": ["tools/workspace_verify.py::finding", "/secrets/hidden"],
                "recommended_next_action": "Review validation result.",
                "suggested_commands": ["dangerous-unreviewed-command"],
            },
            {
                "item_id": "p2",
                "title": "Review restricted recovery candidates",
                "category": "recovery_review",
                "priority": "P2",
                "source": "recovery_index",
                "target_repo": "root",
                "status": "open",
                "approval_required": True,
                "blocking": False,
                "mutation_posture": "advisory_only",
                "evidence_refs": ["reports/analysis/private-recovery.json"],
                "recommended_next_action": "Secret underlying review path",
            },
        ],
        "build_lanes": [
            {
                "lane_id": "root-python",
                "title": "Root tooling",
                "status": "blocked",
                "missing_required_tools": ["sqlite3"],
                "evidence_refs": ["reports/analysis/devkit.json"],
                "mutation_posture": "readiness_only",
            }
        ],
        "hidden_report_body": {"should_never_appear": "VERY_PRIVATE"},
    }


@pytest.fixture
def workspace(tmp_path, saved_report):
    report_path = tmp_path / service.bridge.SOURCE_REFERENCE
    report_path.parent.mkdir(parents=True)
    report_path.write_text(json.dumps(saved_report), encoding="utf-8")
    return tmp_path, report_path


@pytest.fixture
def client(workspace):
    root, _path = workspace
    with TestClient(service.create_app(root=root, environ=CONFIG)) as http:
        yield http


def headers(token=TOKEN):
    return {"Authorization": f"Bearer {token}"}


def test_requires_dedicated_digest():
    with pytest.raises(service.AuthConfigurationError):
        service.create_app(environ={})
    with pytest.raises(service.AuthConfigurationError):
        service.create_app(environ={service.TOKEN_HASH_ENV: "plain-text"})
    with pytest.raises(service.AuthConfigurationError):
        service.create_app(environ={service.TOKEN_HASH_ENV: "A" * 64})


def test_missing_or_invalid_token_fails_before_reading_report(tmp_path):
    http = TestClient(service.create_app(root=tmp_path, environ=CONFIG))
    assert http.get(ENDPOINT).status_code == 401
    response = http.get(ENDPOINT, headers=headers(WRONG))
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert http.get(ENDPOINT, headers={"Authorization": "Basic abc"}).status_code == 401
    assert http.get(ENDPOINT, headers=headers("x" * 4097)).status_code == 401


def test_read_only_snapshot_enforces_redaction_and_provenance(client, workspace):
    root, path = workspace
    original_bytes = path.read_bytes()
    response = client.get(ENDPOINT, headers=headers())
    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "aurora.mission_control.snapshot"
    assert payload["schema_version"] == 1
    assert payload["authority"]["mode"] == "read_only"
    assert payload["authority"]["canon_write"] is False
    assert payload["authority"]["runtime_execution"] is False
    assert payload["source"]["freshness"] == "stale"
    assert payload["source"]["sha256"] == hashlib.sha256(original_bytes).hexdigest()
    assert payload["source"]["generated_at"] == "2026-08-15T05:30:37+00:00"
    assert payload["health"]["inbox_items"] == 2
    assert payload["operator_inbox"][1]["evidence_restricted"] is True
    assert payload["operator_inbox"][1]["evidence_refs"] == []
    as_text = response.text
    assert "VERY_PRIVATE" not in as_text
    assert "dangerous-unreviewed-command" not in as_text
    assert "private-recovery.json" not in as_text
    assert "Secret underlying" not in as_text
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "access-control-allow-origin" not in response.headers
    assert path.read_bytes() == original_bytes
    assert len(list(root.rglob("*"))) == 3  # reports/, analysis/, one source JSON


def test_post_disabled_and_docs_not_published(client):
    assert client.post(ENDPOINT, headers=headers(), json={"run": True}).status_code == 405
    assert client.get("/openapi.json").status_code == 404
    assert client.get("/docs").status_code == 404


def test_reads_latest_saved_bytes_without_running_collector(client, workspace, saved_report):
    _root, path = workspace
    first = client.get(ENDPOINT, headers=headers()).json()
    saved_report["generated_at"] = "2026-09-01T05:30:37Z"
    path.write_text(json.dumps(saved_report), encoding="utf-8")
    second = client.get(ENDPOINT, headers=headers()).json()
    assert first["source"]["sha256"] != second["source"]["sha256"]
    assert second["source"]["generated_at"] == "2026-09-01T05:30:37+00:00"


def test_source_errors_do_not_leak_file_paths(workspace):
    root, path = workspace
    http = TestClient(service.create_app(root=root, environ=CONFIG))
    path.write_text('{"schema_version": 500}', encoding="utf-8")
    response = http.get(ENDPOINT, headers=headers())
    assert response.status_code == 503
    assert response.json()["detail"] == "Validated snapshot unavailable"
    assert "source" not in response.text.lower()


def test_symlink_escape_is_rejected(tmp_path):
    outside = tmp_path.parent / (tmp_path.name + "-external.json")
    outside.write_text('{"secret": "not-shareable"}', encoding="utf-8")
    report_path = tmp_path / service.bridge.SOURCE_REFERENCE
    report_path.parent.mkdir(parents=True)
    report_path.symlink_to(outside)
    http = TestClient(service.create_app(root=tmp_path, environ=CONFIG))
    response = http.get(ENDPOINT, headers=headers())
    assert response.status_code == 503
    assert "not-shareable" not in response.text


def test_report_size_limited(tmp_path):
    report_path = tmp_path / service.bridge.SOURCE_REFERENCE
    report_path.parent.mkdir(parents=True)
    report_path.write_bytes(b"X" * (service.MAX_REPORT_BYTES + 1))
    http = TestClient(service.create_app(root=tmp_path, environ=CONFIG))
    assert http.get(ENDPOINT, headers=headers()).status_code == 503

"""Protocol-level stdio checks for the single-tool, read-only Aurora MCP surface."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("mcp")
pytest.importorskip("fastapi")

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools/aurora_intelligent_ui_mcp.py"
TOOL = "get_mission_control_snapshot"


@pytest.fixture
def saved_workspace(tmp_path: Path) -> Path:
    report = {
        "schema_version": 1, "tool": "aurora_mission_control",
        "run_mode": "read_only", "mutation_posture": "advisory_only",
        "nested_repo_mutation": False,
        "generated_at": "2026-08-15T05:30:37Z", "status": "blocked",
        "source_reports": {"workspace_verify": {"status": "warn"}},
        "summary": {
            "source_count": 1, "source_error_count": 0,
            "operator_inbox_count": 2, "approval_required_count": 1,
            "blocking_count": 0,
            "build_lanes": {"ready": 0, "attention": 0, "blocked": 1},
        },
        "operator_inbox": [
            {
                "item_id": "verify", "title": "Review workspace verification",
                "priority": "P1", "status": "open", "category": "validation",
                "source": "workspace_verify", "target_repo": "root",
                "approval_required": False, "blocking": False,
                "evidence_refs": ["tools/workspace_verify.py::report"],
                "recommended_next_action": "Review verification report.",
                "mutation_posture": "advisory_only",
                "suggested_commands": ["NOT_AN_EXECUTABLE_COMMAND"],
            },
            {
                "item_id": "restricted", "title": "Review restricted recovery artifacts",
                "priority": "P2", "status": "open", "category": "recovery_review",
                "source": "recovery_index", "target_repo": "root",
                "approval_required": True, "blocking": False,
                "evidence_refs": ["reports/analysis/private-recovery.json"],
                "recommended_next_action": "secret:source",
                "mutation_posture": "advisory_only",
            },
        ],
        "build_lanes": [{
            "lane_id": "python", "title": "Python tools", "status": "blocked",
            "missing_required_tools": ["sqlite3"],
            "mutation_posture": "readiness_only",
            "evidence_refs": ["reports/analysis/devkit.json"],
        }],
        "private_payload": "DO_NOT_EXPORT",
    }
    source = tmp_path / "reports/analysis/aurora_mission_control_latest.json"
    source.parent.mkdir(parents=True)
    source.write_text(json.dumps(report), encoding="utf-8")
    return tmp_path


def run_stdio(*, root: Path, missing_report: bool = False):
    async def operation():
        env = dict(os.environ)
        env["AURORA_UI_ROOT"] = str(root)
        params = StdioServerParameters(
            command=sys.executable, args=[str(SCRIPT)], env=env,
        )
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                listed = await session.list_tools()
                assert [item.name for item in listed.tools] == [TOOL]
                item = listed.tools[0]
                assert item.annotations is not None
                assert item.annotations.read_only_hint is True
                assert item.annotations.open_world_hint is False
                assert not item.inputSchema.get("required")
                result = await session.call_tool(TOOL, arguments={})
                return result
    return asyncio.run(operation())


def test_mcp_stdio_reads_fixed_source_without_leaking_data(saved_workspace: Path):
    source = saved_workspace / "reports/analysis/aurora_mission_control_latest.json"
    original = source.read_bytes()
    result = run_stdio(root=saved_workspace)
    assert result.is_error is False
    payload = result.structured_content
    if payload is None:
        payload = json.loads(result.content[0].text)
    assert payload["kind"] == "aurora.mission_control.snapshot"
    assert payload["source"]["freshness"] == "stale"
    assert payload["source"]["sha256"] == hashlib.sha256(original).hexdigest()
    assert payload["authority"]["canon_write"] is False
    assert payload["authority"]["runtime_execution"] is False
    assert payload["operator_inbox"][1]["evidence_restricted"] is True
    assert payload["operator_inbox"][1]["evidence_refs"] == []
    transcript = json.dumps(payload)
    assert "DO_NOT_EXPORT" not in transcript
    assert "NOT_AN_EXECUTABLE_COMMAND" not in transcript
    assert "private-recovery.json" not in transcript
    assert source.read_bytes() == original
    assert sorted(p.name for p in saved_workspace.rglob("*") if p.is_file()) == ["aurora_mission_control_latest.json"]


def test_mcp_stdio_fails_closed_when_no_report(tmp_path: Path):
    result = run_stdio(root=tmp_path)
    assert result.is_error is True
    text = json.dumps([str(x) for x in result.content])
    assert "DO_NOT_EXPORT" not in text
    assert str(tmp_path) not in text


def test_no_additional_tools_exposed():
    source = SCRIPT.read_text(encoding="utf-8")
    assert source.count("@mcp.tool(") == 1
    assert 'mcp.run(transport="stdio")' in source
    assert "ace_materialize" not in source

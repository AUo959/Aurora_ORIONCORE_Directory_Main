from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_ROOT))

import project_focus_announcement as focus  # noqa: E402


FIXED_NOW = datetime(2026, 7, 8, 12, 0, tzinfo=timezone.utc)


def write_registry(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "announcements": [
                    {
                        "id": "active-demo-focus",
                        "status": "active",
                        "priority": "P2",
                        "title": "Current project focus: workable public demos",
                        "summary": "Build workable demos for the public.",
                        "agent_expectation": "Surface demo proposals when relevant.",
                        "guidance": ["Prefer smallest validated demo slices."],
                        "evidence_refs": ["reports/analysis/aurora_demo_readiness_latest.json"],
                        "suggested_commands": ["make demo-readiness"],
                        "effective_at": "2026-07-08T00:00:00Z",
                        "expires_at": None,
                    },
                    {
                        "id": "expired",
                        "status": "active",
                        "title": "Expired focus",
                        "summary": "Old.",
                        "effective_at": "2026-07-01T00:00:00Z",
                        "expires_at": "2026-07-02T00:00:00Z",
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_build_report_includes_only_active_announcements_by_default(tmp_path: Path) -> None:
    registry = tmp_path / "catalog/project_focus_announcements.json"
    write_registry(registry)

    report = focus.build_report(tmp_path, registry, now=FIXED_NOW, generated_at="2026-07-08T12:00:00Z")

    assert report["tool"] == "project_focus_announcement"
    assert report["run_mode"] == "read_only"
    assert report["mutation_posture"] == "advisory_only"
    assert report["nested_repo_mutation"] is False
    assert report["status"] == "active"
    assert report["summary"]["announcement_count"] == 2
    assert report["summary"]["active_count"] == 1
    assert [item["id"] for item in report["announcements"]] == ["active-demo-focus"]


def test_include_inactive_keeps_expired_records_visible(tmp_path: Path) -> None:
    registry = tmp_path / "catalog/project_focus_announcements.json"
    write_registry(registry)

    report = focus.build_report(tmp_path, registry, include_inactive=True, now=FIXED_NOW)

    assert [item["id"] for item in report["announcements"]] == ["active-demo-focus", "expired"]
    assert report["announcements"][1]["active"] is False


def test_summary_mentions_agent_expectation_and_commands(tmp_path: Path) -> None:
    registry = tmp_path / "catalog/project_focus_announcements.json"
    write_registry(registry)
    report = focus.build_report(tmp_path, registry, now=FIXED_NOW)

    summary = focus.format_summary(report)

    assert "Current project focus: workable public demos" in summary
    assert "Surface demo proposals when relevant." in summary
    assert "make demo-readiness" in summary

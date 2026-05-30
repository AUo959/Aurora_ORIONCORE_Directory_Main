from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_ROOT))

import aurora_mission_control as mission  # noqa: E402


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_manifest(path: Path) -> None:
    payload = {
        "schema_version": 1,
        "id": "test-mission-control",
        "default_report_path": "reports/analysis/aurora_mission_control_latest.json",
        "run_mode": "read_only",
        "mutation_posture": "advisory_only",
        "max_inbox_items": 12,
        "max_evidence_refs": 12,
        "sources": [
            {"id": "workspace_verify", "enabled": True},
            {"id": "integration_gate", "enabled": True},
            {"id": "recovery_index", "enabled": True},
            {"id": "devkit", "enabled": True},
            {"id": "recommendations", "enabled": True},
            {"id": "git_status", "enabled": True},
        ],
        "build_lanes": mission.DEFAULT_BUILD_LANES,
        "validation_commands": ["python3 tools/aurora_mission_control.py --summary"],
    }
    write_file(path, json.dumps(payload, indent=2) + "\n")


def workspace_report(blocking: bool = False) -> dict[str, Any]:
    findings = []
    if blocking:
        findings.append({"check": "manifest", "blocking": True})
    return {
        "status": "fail" if blocking else "pass",
        "summary": {
            "finding_count": len(findings),
            "blocking_count": 1 if blocking else 0,
        },
        "findings": findings,
    }


def integration_report(failing: bool = False) -> dict[str, Any]:
    return {
        "verdict": "fail" if failing else "pass",
        "checks": [
            {
                "name": "command_gateway_safety",
                "status": "fail" if failing else "pass",
            }
        ],
        "commands": [],
    }


def recovery_report() -> dict[str, Any]:
    return {
        "status": "READY",
        "summary": {
            "candidate_count": 2,
            "discovered_candidate_count": 2,
        },
        "candidates": [
            {
                "path": "intake/root-note.md",
                "restricted_material_possible": False,
            },
            {
                "path": "intake/restricted-token.txt",
                "restricted_material_possible": True,
            },
        ],
    }


def devkit_report(missing: str | None = None) -> dict[str, Any]:
    toolchain = []
    all_tools = {
        tool_id
        for lane in mission.DEFAULT_BUILD_LANES
        for tool_id in lane["required_tools"] + lane["recommended_tools"]
    }
    for tool_id in sorted(all_tools):
        toolchain.append(
            {
                "id": tool_id,
                "status": "missing" if tool_id == missing else "ok",
            }
        )
    return {
        "status": "WARN" if missing else "READY",
        "toolchain": toolchain,
        "findings": [],
        "install_plan": [],
    }


def recommendations_report(blocking: bool = False) -> dict[str, Any]:
    recommendations = [
        {
            "recommendation_id": "aurora-rec-p1-recovery-restricted",
            "title": "Review 2 restricted recovery candidates carefully",
            "category": "recovery_review",
            "priority": "P1",
            "confidence": "medium",
            "target_repo": "root",
            "owner_surface": "root control-plane repo",
            "evidence_refs": ["intake/restricted-token.txt", "intake/restricted-note.md"],
            "source": "recovery_index",
            "recommended_next_action": "Handle restricted candidates through a separate review decision; do not copy them.",
            "suggested_commands": ["python3 tools/workspace_recovery_index.py --summary"],
            "approval_required": True,
            "mutation_posture": "advisory_only",
            "blocking": False,
            "status": "open",
        },
        {
            "recommendation_id": "aurora-rec-p2-recovery-review-review-root",
            "title": "Review 2 recovery candidates routed to root",
            "category": "recovery_review",
            "priority": "P2",
            "confidence": "medium",
            "target_repo": "root",
            "owner_surface": "root control-plane repo",
            "evidence_refs": ["intake/root-note.md"],
            "source": "recovery_index",
            "recommended_next_action": "Review candidates as routing evidence only. Do not promote.",
            "suggested_commands": ["python3 tools/workspace_recovery_index.py --summary"],
            "approval_required": True,
            "mutation_posture": "advisory_only",
            "blocking": False,
            "status": "open",
        }
    ]
    if blocking:
        recommendations.insert(
            0,
            {
                "recommendation_id": "aurora-rec-p0-workspace-verify",
                "title": "Resolve workspace verifier finding: manifest",
                "category": "validation",
                "priority": "P0",
                "confidence": "high",
                "target_repo": "root",
                "owner_surface": "root control-plane repo",
                "evidence_refs": ["tools/workspace_verify.py::manifest"],
                "source": "workspace_verify",
                "recommended_next_action": "Run workspace scan and verify.",
                "suggested_commands": ["python3 tools/workspace_verify.py"],
                "approval_required": False,
                "mutation_posture": "advisory_only",
                "blocking": True,
                "status": "blocked",
            },
        )
    return {
        "status": "blocked" if blocking else "open",
        "summary": {
            "recommendation_count": len(recommendations),
            "blocking_count": 1 if blocking else 0,
            "approval_required_count": 2,
        },
        "recommendations": recommendations,
    }


def git_report(dirty: bool = False) -> dict[str, Any]:
    return {
        "status": "dirty" if dirty else "clean",
        "returncode": 0,
        "branch": "main",
        "changed_paths": ["README.md"] if dirty else [],
    }


def collectors(
    *,
    blocking: bool = False,
    missing_tool: str | None = None,
) -> dict[str, mission.Collector]:
    return {
        "workspace_verify": lambda root, manifest: workspace_report(blocking),
        "integration_gate": lambda root, manifest: integration_report(blocking),
        "recovery_index": lambda root, manifest: recovery_report(),
        "devkit": lambda root, manifest: devkit_report(missing_tool),
        "recommendations": lambda root, manifest: recommendations_report(blocking),
        "git_status": lambda root, manifest: git_report(False),
    }


def build_test_report(
    tmp_path: Path,
    *,
    blocking: bool = False,
    missing_tool: str | None = None,
) -> dict[str, Any]:
    root = tmp_path / "workspace"
    manifest_path = root / "catalog" / "mission_control_manifest.json"
    write_manifest(manifest_path)
    return mission.build_report(
        root,
        manifest_path,
        collectors=collectors(blocking=blocking, missing_tool=missing_tool),
        generated_at="2026-05-23T00:00:00Z",
    )


def test_report_shape_and_read_only_invariants(tmp_path: Path) -> None:
    report = build_test_report(tmp_path)

    assert report["tool"] == "aurora_mission_control"
    assert report["run_mode"] == "read_only"
    assert report["mutation_posture"] == "advisory_only"
    assert report["nested_repo_mutation"] is False
    assert report["status"] == "attention"
    assert report["summary"]["source_count"] == 6
    assert report["summary"]["operator_inbox_count"] == 2
    assert report["summary"]["approval_required_count"] == 2
    assert report["operator_inbox"][0]["mutation_posture"] == "advisory_only"


def test_blocking_recommendations_make_report_blocked(tmp_path: Path) -> None:
    report = build_test_report(tmp_path, blocking=True)

    assert report["status"] == "blocked"
    assert report["operator_inbox"][0]["priority"] == "P0"
    assert report["operator_inbox"][0]["blocking"] is True
    assert report["summary"]["blocking_count"] == 1


def test_devkit_tool_state_drives_build_lane_readiness(tmp_path: Path) -> None:
    report = build_test_report(tmp_path, missing_tool="docker")

    lanes = {item["lane_id"]: item for item in report["build_lanes"]}
    assert lanes["containerized-services"]["status"] == "blocked"
    assert lanes["containerized-services"]["missing_required_tools"] == ["docker"]
    assert report["status"] == "blocked"


def test_recovery_source_summary_preserves_restricted_count(tmp_path: Path) -> None:
    report = build_test_report(tmp_path)

    recovery = report["source_reports"]["recovery_index"]
    assert recovery["candidate_count"] == 2
    assert recovery["restricted_candidate_count"] == 1


def test_restricted_recovery_inbox_redacts_candidate_paths(tmp_path: Path) -> None:
    report = build_test_report(tmp_path)

    restricted = [
        item
        for item in report["operator_inbox"]
        if "restricted recovery candidates" in item["title"]
    ]
    assert len(restricted) == 1
    assert restricted[0]["evidence_refs"] == [
        "reports/analysis/workspace_recovery_index_latest.json::restricted_recovery_candidates_metadata"
    ]


def test_source_errors_become_operator_inbox_items(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    manifest_path = root / "catalog" / "mission_control_manifest.json"
    write_manifest(manifest_path)

    report = mission.build_report(
        root,
        manifest_path,
        collectors={
            **collectors(),
            "recovery_index": lambda root, manifest: {
                "status": "error",
                "error": "fixture failure",
            },
        },
        generated_at="2026-05-23T00:00:00Z",
    )

    source_error_items = [
        item
        for item in report["operator_inbox"]
        if item["item_id"] == "mission-p1-source-error-recovery_index"
    ]
    assert len(source_error_items) == 1
    assert source_error_items[0]["category"] == "validation"

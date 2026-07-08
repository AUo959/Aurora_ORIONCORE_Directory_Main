from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_ROOT))

import aurora_recommendation_engine as engine  # noqa: E402


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_manifest(path: Path) -> None:
    payload = {
        "schema_version": 1,
        "id": "test-recommendation-engine",
        "default_report_path": "reports/analysis/aurora_recommendations_latest.json",
        "run_mode": "read_only",
        "mutation_posture": "advisory_only",
        "max_recommendations": 50,
        "max_recovery_groups": 8,
        "max_evidence_refs": 12,
        "sources": [
            {"id": "workspace_verify", "weight": 100},
            {"id": "integration_gate", "weight": 90},
            {"id": "recovery_index", "weight": 60},
            {"id": "devkit", "weight": 50},
            {"id": "git_status", "weight": 40},
        ],
        "validation_commands": ["python3 tools/aurora_recommendation_engine.py --summary"],
    }
    write_file(path, json.dumps(payload, indent=2) + "\n")


def workspace_report(blocking: bool = False) -> dict[str, Any]:
    findings = []
    if blocking:
        findings.append(
            {
                "check": "manifest_top_level_coverage",
                "severity": "error",
                "blocking": True,
                "details": "missing_from_manifest=['example']",
                "suggested_fix": "Run `python3 tools/workspace_scan.py`.",
            }
        )
    return {
        "status": "fail" if blocking else "pass",
        "summary": {
            "finding_count": len(findings),
            "blocking_count": 1 if blocking else 0,
            "warning_count": 0,
        },
        "findings": findings,
    }


def integration_report(failing: bool = False) -> dict[str, Any]:
    checks = [
        {
            "name": "command_gateway_safety",
            "status": "fail" if failing else "pass",
            "classification": "fail" if failing else "pass",
            "failures": ["execute_request envelope is not blocked pending verification"] if failing else [],
            "warnings": [],
        }
    ]
    return {
        "verdict": "fail" if failing else "pass",
        "run_mode": "read_only",
        "nested_repo_mutation": False,
        "checks": checks,
        "commands": [],
    }


def recovery_report() -> dict[str, Any]:
    return {
        "status": "READY",
        "summary": {"candidate_count": 4, "discovered_candidate_count": 4},
        "candidates": [
            {
                "path": "intake/root-note.md",
                "promotion_status": "pending_review",
                "canonical_status": "not_promoted",
                "target_repo_hint": "root",
                "owner_surface_hint": "root control-plane repo",
                "restricted_material_possible": False,
            },
            {
                "path": "intake/root-script.py",
                "promotion_status": "pending_review",
                "canonical_status": "not_promoted",
                "target_repo_hint": "root",
                "owner_surface_hint": "root control-plane repo",
                "restricted_material_possible": False,
            },
            {
                "path": "intake/cloudbank-logic.py",
                "promotion_status": "pending_review",
                "canonical_status": "not_promoted",
                "target_repo_hint": "aurora-cloudbank-symbolic-main",
                "owner_surface_hint": "canonical nested repo",
                "restricted_material_possible": False,
            },
            {
                "path": "intake/restricted-token.txt",
                "promotion_status": "pending_review",
                "canonical_status": "not_promoted",
                "target_repo_hint": "review-required",
                "owner_surface_hint": "manual recovery review",
                "restricted_material_possible": True,
            },
        ],
    }


def devkit_report() -> dict[str, Any]:
    return {
        "status": "WARN",
        "findings": [
            {
                "severity": "warning",
                "id": "tool_docker_missing",
                "message": "docker is missing.",
                "next_step": "Review Docker install through an explicit system-level package-manager decision.",
            }
        ],
        "install_plan": [
            {
                "tool_id": "docker",
                "status": "manual",
                "install_command_text": "",
                "update_command_text": "",
                "notes": "Manual install required.",
            }
        ],
    }


def git_report(dirty: bool = True) -> dict[str, Any]:
    return {
        "status": "dirty" if dirty else "clean",
        "returncode": 0,
        "branch": "main...origin/main",
        "changed_paths": ["tools/aurora_command_intent.py", "README.md"] if dirty else [],
    }


def collectors(
    *,
    workspace_blocking: bool = False,
    integration_failing: bool = False,
    dirty: bool = True,
) -> dict[str, engine.Collector]:
    return {
        "workspace_verify": lambda root, manifest: workspace_report(workspace_blocking),
        "integration_gate": lambda root, manifest: integration_report(integration_failing),
        "recovery_index": lambda root, manifest: recovery_report(),
        "devkit": lambda root, manifest: devkit_report(),
        "git_status": lambda root, manifest: git_report(dirty),
    }


def write_triage_log(root: Path, filename: str, entries: list[dict[str, Any]]) -> None:
    payload = {
        "schema_version": 1,
        "generated_at": "2026-07-08T05:15:00Z",
        "entries": entries,
    }
    write_file(root / "reports" / "analysis" / filename, json.dumps(payload, indent=2) + "\n")


def build_test_report(
    tmp_path: Path,
    *,
    workspace_blocking: bool = False,
    integration_failing: bool = False,
    dirty: bool = True,
) -> dict[str, Any]:
    root = tmp_path / "workspace"
    manifest = root / "catalog" / "recommendation_engine_manifest.json"
    write_manifest(manifest)
    return engine.build_report(
        root,
        manifest,
        collectors=collectors(
            workspace_blocking=workspace_blocking,
            integration_failing=integration_failing,
            dirty=dirty,
        ),
        generated_at="2026-05-21T00:00:00Z",
    )


def test_report_shape_and_advisory_only_invariants(tmp_path: Path) -> None:
    report = build_test_report(tmp_path, workspace_blocking=True, integration_failing=True)

    assert report["tool"] == "aurora_recommendation_engine"
    assert report["run_mode"] == "read_only"
    assert report["mutation_posture"] == "advisory_only"
    assert report["nested_repo_mutation"] is False
    assert report["status"] == "blocked"
    assert report["recommendations"]

    for item in report["recommendations"]:
        assert set(item) == set(engine.RECOMMENDATION_FIELDS)
        assert item["mutation_posture"] == "advisory_only"
        assert item["category"] in engine.VALID_CATEGORIES


def test_blocking_validation_and_integration_failures_rank_as_p0(tmp_path: Path) -> None:
    report = build_test_report(tmp_path, workspace_blocking=True, integration_failing=True)

    p0_items = [item for item in report["recommendations"] if item["priority"] == "P0"]
    assert {item["source"] for item in p0_items} == {"workspace_verify", "integration_gate"}
    assert all(item["blocking"] for item in p0_items)
    assert report["recommendations"][0]["priority"] == "P0"


def test_recovery_candidates_are_grouped_without_promotion(tmp_path: Path) -> None:
    report = build_test_report(tmp_path)

    recovery_items = [
        item
        for item in report["recommendations"]
        if item["source"] == "recovery_index" and item["category"] == "recovery_review"
    ]
    assert recovery_items
    grouped = [item for item in recovery_items if "routed to root" in item["title"]]
    assert grouped
    assert grouped[0]["approval_required"] is True
    assert "Do not promote" in grouped[0]["recommended_next_action"]
    assert grouped[0]["target_repo"] == "root"


def test_restricted_recovery_candidates_get_careful_handling_recommendation(tmp_path: Path) -> None:
    report = build_test_report(tmp_path)

    restricted = [
        item
        for item in report["recommendations"]
        if item["source"] == "recovery_index" and "restricted" in item["title"].lower()
    ]
    assert len(restricted) == 1
    assert restricted[0]["priority"] == "P1"
    assert restricted[0]["approval_required"] is True
    assert "do not copy" in restricted[0]["recommended_next_action"].lower()


def test_triaged_false_positive_suppresses_restricted_recommendation(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    manifest = root / "catalog" / "recommendation_engine_manifest.json"
    write_manifest(manifest)
    write_triage_log(
        root,
        "restricted_recovery_triage__2026-07-08.json",
        [
            {
                "path": "intake/restricted-token.txt",
                "classification": "false_positive",
                "reviewer": "claude-code",
                "reviewed_at": "2026-07-08T05:15:00Z",
                "notes": "Heuristic false positive.",
            }
        ],
    )
    report = engine.build_report(
        root,
        manifest,
        collectors=collectors(),
        generated_at="2026-05-21T00:00:00Z",
    )

    restricted_titles = [
        item["title"]
        for item in report["recommendations"]
        if item["source"] == "recovery_index" and item["category"] == "recovery_review"
    ]
    assert not any("restricted" in title.lower() for title in restricted_titles)
    assert not any("escalate" in title.lower() for title in restricted_titles)
    assert not any("owner review needed" in title.lower() for title in restricted_titles)


def test_triaged_live_credential_becomes_blocking_p0(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    manifest = root / "catalog" / "recommendation_engine_manifest.json"
    write_manifest(manifest)
    write_triage_log(
        root,
        "restricted_recovery_triage__2026-07-08.json",
        [
            {
                "path": "intake/restricted-token.txt",
                "classification": "live_credential_confirmed",
                "reviewer": "claude-code",
                "reviewed_at": "2026-07-08T05:15:00Z",
                "notes": "Confirmed live key.",
            }
        ],
    )
    report = engine.build_report(
        root,
        manifest,
        collectors=collectors(),
        generated_at="2026-05-21T00:00:00Z",
    )

    escalations = [
        item
        for item in report["recommendations"]
        if item["source"] == "recovery_index" and "escalate" in item["title"].lower()
    ]
    assert len(escalations) == 1
    assert escalations[0]["priority"] == "P0"
    assert escalations[0]["blocking"] is True
    assert escalations[0]["status"] == "blocked"
    # No untriaged "review carefully" duplicate for the same candidate.
    assert not any(
        "review carefully" in item["title"].lower()
        for item in report["recommendations"]
        if item["source"] == "recovery_index"
    )


def test_triaged_needs_owner_review_becomes_p2_batch(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    manifest = root / "catalog" / "recommendation_engine_manifest.json"
    write_manifest(manifest)
    write_triage_log(
        root,
        "restricted_recovery_triage__2026-07-08.json",
        [
            {
                "path": "intake/restricted-token.txt",
                "classification": "needs_owner_review",
                "reviewer": "claude-code",
                "reviewed_at": "2026-07-08T05:15:00Z",
                "notes": "Ambiguous internal reference.",
            }
        ],
    )
    report = engine.build_report(
        root,
        manifest,
        collectors=collectors(),
        generated_at="2026-05-21T00:00:00Z",
    )

    owner_review_items = [
        item
        for item in report["recommendations"]
        if item["source"] == "recovery_index" and "owner review needed" in item["title"].lower()
    ]
    assert len(owner_review_items) == 1
    assert owner_review_items[0]["priority"] == "P2"
    assert owner_review_items[0]["blocking"] is False


def test_devkit_warnings_remain_approval_gated(tmp_path: Path) -> None:
    report = build_test_report(tmp_path)

    devkit_items = [item for item in report["recommendations"] if item["source"] == "devkit"]
    assert len(devkit_items) == 1
    assert devkit_items[0]["priority"] == "P2"
    assert devkit_items[0]["approval_required"] is True
    assert devkit_items[0]["blocking"] is False


def test_dirty_worktree_is_informational_not_failure(tmp_path: Path) -> None:
    report = build_test_report(tmp_path, dirty=True)

    git_items = [item for item in report["recommendations"] if item["source"] == "git_status"]
    assert len(git_items) == 1
    assert git_items[0]["priority"] == "P2"
    assert git_items[0]["status"] == "informational"
    assert git_items[0]["blocking"] is False
    assert "tools/aurora_command_intent.py" in git_items[0]["evidence_refs"]


def test_clean_sources_can_report_clear_when_no_recommendations(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    manifest = root / "catalog" / "recommendation_engine_manifest.json"
    write_manifest(manifest)

    report = engine.build_report(
        root,
        manifest,
        collectors={
            "workspace_verify": lambda root, manifest: workspace_report(False),
            "integration_gate": lambda root, manifest: integration_report(False),
            "recovery_index": lambda root, manifest: {"status": "READY", "summary": {}, "candidates": []},
            "devkit": lambda root, manifest: {"status": "READY", "findings": [], "install_plan": []},
            "git_status": lambda root, manifest: git_report(False),
        },
        generated_at="2026-05-21T00:00:00Z",
    )

    assert report["status"] == "clear"
    assert report["summary"]["recommendation_count"] == 0

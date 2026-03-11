from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import _workspace_common as workspace_common  # noqa: E402


def run_command(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=check,
    )


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def copy_repo_file(source_relative: str, destination_root: Path) -> None:
    source = REPO_ROOT / source_relative
    destination = destination_root / source_relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def build_test_workspace(root: Path) -> None:
    for relative in (
        "archives",
        "catalog",
        "docs",
        "intake",
        "projects",
        "reports/analysis",
        "reports/automation",
        "repos",
        "skills",
        "tests",
        "tools",
        "_staging",
    ):
        (root / relative).mkdir(parents=True, exist_ok=True)

    for keep_path in (
        "archives/.gitkeep",
        "intake/.gitkeep",
        "projects/.gitkeep",
        "repos/.gitkeep",
        "_staging/.gitkeep",
    ):
        write_file(root / keep_path, "")

    write_file(root / "README.md", "# Test Workspace\n")
    write_file(root / "AGENTS.md", "# Test Agents\n")
    write_file(
        root / "aurora_cloudbank_symbolic_architecture_discovery_report.md",
        "# Discovery Report\n",
    )
    write_file(root / "docs/repo-boundary-notice.md", "# Boundary\n")
    write_file(root / "reports/analysis/example.md", "# Example\n")
    write_file(root / "catalog/classification_overrides.yaml", json.dumps({"overrides": []}, indent=2) + "\n")
    write_file(root / "catalog/relocation_plan.json", json.dumps({"generated_at": "2026-03-10T00:00:00Z", "batches": []}, indent=2) + "\n")

    copy_repo_file(".gitignore", root)
    copy_repo_file(".gitattributes", root)
    copy_repo_file(".githooks/pre-commit", root)
    copy_repo_file("tools/_workspace_common.py", root)
    copy_repo_file("tools/workspace_apply_moves.py", root)
    copy_repo_file("tools/workspace_scan.py", root)

    run_command(["git", "init"], cwd=root)
    run_command(["git", "config", "user.email", "codex@example.com"], cwd=root)
    run_command(["git", "config", "user.name", "Codex"], cwd=root)
    run_command(["git", "add", "."], cwd=root)
    run_command(["git", "commit", "-m", "initial fixture"], cwd=root)

    run_command(
        [
            sys.executable,
            str(root / "tools" / "workspace_scan.py"),
            "--root",
            str(root),
        ],
        cwd=root,
    )
    run_command(["git", "add", "."], cwd=root)
    run_command(["git", "commit", "-m", "generate control-plane artifacts"], cwd=root)


def run_verify(root: Path, *extra_args: str) -> subprocess.CompletedProcess[str]:
    return run_command(
        [sys.executable, str(REPO_ROOT / "tools" / "workspace_verify.py"), "--root", str(root), *extra_args],
        cwd=REPO_ROOT,
        check=False,
    )


@pytest.fixture()
def workspace_root(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    build_test_workspace(root)
    return root


def test_root_policy_records_manage_expected_top_level_entries(workspace_root: Path) -> None:
    records = {
        record["current_path"]: record
        for record in workspace_common.top_level_policy_records(workspace_root)
    }
    assert records["AGENTS.md"]["status"] == "managed"
    assert records["skills"]["status"] == "managed"
    assert records["tests"]["status"] == "managed"
    assert records["aurora_cloudbank_symbolic_architecture_discovery_report.md"]["status"] == "managed"


def test_archive_inventory_skips_nested_repo_internals(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    (root / "outer").mkdir(parents=True)
    write_file(root / "outer" / "keep.zip", "root archive\n")
    nested_repo = root / "outer" / "nested_repo"
    nested_repo.mkdir(parents=True)
    run_command(["git", "init"], cwd=nested_repo)
    write_file(nested_repo / "ignored.zip", "nested archive\n")

    artifacts = workspace_common.iter_archive_artifacts(root)
    relative_paths = {workspace_common.relpath(path, root) for path in artifacts}
    assert "outer/keep.zip" in relative_paths
    assert "outer/nested_repo/ignored.zip" not in relative_paths


def test_workspace_verify_passes_with_current_root_surface(workspace_root: Path) -> None:
    result = run_verify(workspace_root)
    report = json.loads(result.stdout)
    assert result.returncode == 0
    assert report["status"] == "pass"
    assert report["summary"]["finding_count"] == 0


def test_manual_verify_is_side_effect_free_by_default(workspace_root: Path) -> None:
    result = run_verify(workspace_root)
    assert result.returncode == 0
    assert not (workspace_root / "reports" / "analysis" / "workspace_verify_latest.json").exists()
    status = run_command(["git", "status", "--short"], cwd=workspace_root)
    assert status.stdout.strip() == ""


def test_report_writes_are_explicit(workspace_root: Path, tmp_path: Path) -> None:
    explicit_report = tmp_path / "workspace_verify.json"
    explicit_result = run_verify(workspace_root, "--report-out", str(explicit_report))
    assert explicit_result.returncode == 0
    assert explicit_report.exists()
    assert json.loads(explicit_report.read_text(encoding="utf-8"))["status"] == "pass"
    assert not (workspace_root / "reports" / "analysis" / "workspace_verify_latest.json").exists()

    persisted_result = run_verify(workspace_root, "--persist-report")
    assert persisted_result.returncode == 0
    persisted_report = workspace_root / "reports" / "analysis" / "workspace_verify_latest.json"
    assert persisted_report.exists()
    assert json.loads(persisted_report.read_text(encoding="utf-8"))["status"] == "pass"


def test_pre_commit_mode_blocks_on_manifest_drift(workspace_root: Path) -> None:
    write_file(workspace_root / "rogue.bin", "rogue\n")
    result = run_verify(workspace_root, "--git-pre-commit")
    assert result.returncode == 1
    assert "Blocking failures:" in result.stdout
    assert "manifest_top_level_coverage" in result.stdout


def test_manual_verify_warns_for_missing_nested_repo_context(workspace_root: Path) -> None:
    repo_registry = {
        "generated_at": "2026-03-10T00:00:00Z",
        "root": ".",
        "repos": [
            {
                "name": "missing-nested",
                "path": "Nested/MissingRepo",
                "branch": "main",
                "head_sha": "deadbeef",
                "remote_status": "no_remote_configured",
                "validation_command": "git -C Nested/MissingRepo rev-parse HEAD",
                "move_policy": "frozen_until_registry_adoption",
            }
        ],
    }
    write_file(
        workspace_root / "catalog" / "repo_registry.yaml",
        json.dumps(repo_registry, indent=2) + "\n",
    )

    result = run_verify(workspace_root)
    report = json.loads(result.stdout)
    assert result.returncode == 0
    assert report["status"] == "warn"
    assert any(
        finding["check"] == "repo_registry_coverage" and not finding["blocking"]
        for finding in report["findings"]
    )


def test_explicit_determinism_and_relocation_checks_pass(workspace_root: Path) -> None:
    result = run_verify(workspace_root, "--check-determinism", "--exercise-relocation")
    report = json.loads(result.stdout)
    assert result.returncode == 0
    assert report["status"] == "pass"

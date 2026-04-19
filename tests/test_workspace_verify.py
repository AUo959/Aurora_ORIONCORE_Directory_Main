from __future__ import annotations

import builtins
import json
import shutil
import subprocess
import sys
import zipfile
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


def test_top_level_policy_records_keep_unique_ids_with_control_surface_overrides(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    (root / ".agents" / "plugins").mkdir(parents=True)
    write_file(root / "AGENTS.md", "# Test Agents\n")
    write_file(root / "Aurora_Text_109.txt", "one\n")
    write_file(root / "aurora_text_109 2.txt", "two\n")
    write_file(
        root / "catalog" / "classification_overrides.yaml",
        json.dumps(
            {
                "overrides": [
                    {
                        "current_path": ".agents",
                        "id": "dot-agents",
                        "kind": "control_surface",
                        "logical_zone": "tools",
                        "planned_path": ".agents",
                        "git_boundary": "root",
                        "storage_tier": "workspace-control",
                        "retention_policy": "versioned",
                        "owner": "workspace-admin",
                        "status": "managed",
                    }
                ]
            },
            indent=2,
        )
        + "\n",
    )

    overrides = workspace_common.load_classification_overrides(root / "catalog" / "classification_overrides.yaml")
    records = workspace_common.top_level_policy_records(root, overrides=overrides)
    ids = [record["id"] for record in records]

    assert len(ids) == len(set(ids))
    assert any(record["current_path"] == ".agents" and record["id"] == "dot-agents" for record in records)
    assert any(record["current_path"] == "AGENTS.md" and record["id"] == "agents" for record in records)
    assert any(record["current_path"] == "Aurora_Text_109.txt" and record["id"] == "aurora-text-109-txt" for record in records)
    assert any(record["current_path"] == "aurora_text_109 2.txt" and record["id"] == "aurora-text-109-2-txt" for record in records)


def test_top_level_policy_records_omit_paths_with_scan_policy_override(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "catalog").mkdir()
    (root / "Personal").mkdir()
    write_file(root / "aurora_note.txt", "aurora\n")
    write_file(
        root / "catalog" / "classification_overrides.yaml",
        json.dumps(
            {
                "overrides": [
                    {
                        "current_path": "Personal",
                        "scan_policy": "omit",
                    }
                ]
            },
            indent=2,
        )
        + "\n",
    )

    overrides = workspace_common.load_classification_overrides(root / "catalog" / "classification_overrides.yaml")
    records = workspace_common.top_level_policy_records(root, overrides=overrides)
    current_paths = {record["current_path"] for record in records}

    assert "Personal" not in current_paths
    assert "aurora_note.txt" in current_paths


def test_scan_policy_for_entry_auto_omits_private_content_with_generic_filename(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    path = root / "notes.txt"
    write_file(
        path,
        "Patient Name: Jane Example\nDate of Birth: 1990-01-01\nTherapy options attached.\n",
    )

    policy = workspace_common.scan_policy_for_entry(path, root, overrides={})

    assert policy == "omit"


def test_scan_policy_for_entry_auto_omits_unknown_nonproject_content(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    path = root / "notes.txt"
    write_file(path, "General project notes for a school fundraiser.\n")

    policy = workspace_common.scan_policy_for_entry(path, root, overrides={})

    assert policy == "omit"


def test_scan_policy_for_entry_auto_omits_private_pdf_magic_with_generic_extension(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    path = root / "document.bin"
    path.write_bytes(b"%PDF-1.4\nPatient Name Jane Example\nDate of Birth 1990-01-01\n")

    policy = workspace_common.scan_policy_for_entry(path, root, overrides={})

    assert policy == "omit"


def test_scan_policy_for_entry_keeps_approved_scope_content(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    path = root / "notes.txt"
    write_file(path, "Aurora forecast notes for ORION control plane.\n")

    policy = workspace_common.scan_policy_for_entry(path, root, overrides={})

    assert policy == ""


def test_scan_policy_for_entry_keeps_managed_control_surface_despite_private_signal(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    path = root / "tools"
    path.mkdir()
    write_file(path / "medical_notes.txt", "Patient Name: Jane Example\nDate of Birth: 1990-01-01\n")

    policy = workspace_common.scan_policy_for_entry(path, root, overrides={})
    record = workspace_common.classify_top_level(path, root, nested_repo_roots=set())

    assert record["status"] == "managed"
    assert policy == ""


def test_classify_top_level_recognizes_root_infra_control_surfaces(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()

    devcontainer = workspace_common.classify_top_level(root / ".devcontainer", root, nested_repo_roots=set())
    github = workspace_common.classify_top_level(root / ".github", root, nested_repo_roots=set())
    makefile = workspace_common.classify_top_level(root / "Makefile", root, nested_repo_roots=set())
    pre_commit = workspace_common.classify_top_level(root / ".pre-commit-config.yaml", root, nested_repo_roots=set())

    assert devcontainer["status"] == "managed"
    assert devcontainer["logical_zone"] == "tools"
    assert github["status"] == "managed"
    assert github["logical_zone"] == "tools"
    assert makefile["status"] == "managed"
    assert makefile["logical_zone"] == "tools"
    assert pre_commit["status"] == "managed"
    assert pre_commit["logical_zone"] == "tools"


def test_scan_policy_for_entry_auto_omits_private_office_zip_magic_with_generic_extension(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    path = root / "document.data"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "word/document.xml",
            "<w:document><w:body>Patient Name Jane Example Date of Birth 1990-01-01</w:body></w:document>",
        )

    policy = workspace_common.scan_policy_for_entry(path, root, overrides={})

    assert policy == "omit"


def test_scan_policy_for_entry_include_override_can_keep_false_positive(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    path = root / "Personal"
    path.mkdir()
    write_file(
        root / "catalog" / "classification_overrides.yaml",
        json.dumps(
            {
                "overrides": [
                    {
                        "current_path": "Personal",
                        "scan_policy": "include",
                    }
                ]
            },
            indent=2,
        )
        + "\n",
    )

    overrides = workspace_common.load_classification_overrides(root / "catalog" / "classification_overrides.yaml")
    policy = workspace_common.scan_policy_for_entry(path, root, overrides=overrides)
    records = workspace_common.top_level_policy_records(root, overrides=overrides)
    current_paths = {record["current_path"] for record in records}

    assert policy == "include"
    assert "Personal" in current_paths


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


def test_workspace_verify_respects_scan_policy_omit_overrides(workspace_root: Path) -> None:
    (workspace_root / "Personal").mkdir()
    write_file(workspace_root / "Personal" / "note.txt", "private\n")
    write_file(
        workspace_root / "catalog" / "classification_overrides.yaml",
        json.dumps(
            {
                "overrides": [
                    {
                        "current_path": "Personal",
                        "scan_policy": "omit",
                    }
                ]
            },
            indent=2,
        )
        + "\n",
    )

    run_command(
        [
            sys.executable,
            str(workspace_root / "tools" / "workspace_scan.py"),
            "--root",
            str(workspace_root),
        ],
        cwd=workspace_root,
    )

    manifest = workspace_common.load_yaml_like(workspace_root / "catalog" / "workspace_manifest.yaml")
    manifest_paths = {entry["current_path"] for entry in manifest["entries"]}
    assert "Personal" not in manifest_paths

    result = run_verify(workspace_root)
    report = json.loads(result.stdout)
    assert result.returncode == 0
    assert report["status"] == "pass"


def test_workspace_verify_auto_excludes_private_generic_file(workspace_root: Path) -> None:
    write_file(
        workspace_root / "notes.txt",
        "Patient Name: Jane Example\nDate of Birth: 1990-01-01\nTherapy options attached.\n",
    )

    run_command(
        [
            sys.executable,
            str(workspace_root / "tools" / "workspace_scan.py"),
            "--root",
            str(workspace_root),
        ],
        cwd=workspace_root,
    )

    manifest = workspace_common.load_yaml_like(workspace_root / "catalog" / "workspace_manifest.yaml")
    manifest_paths = {entry["current_path"] for entry in manifest["entries"]}
    assert "notes.txt" not in manifest_paths

    result = run_verify(workspace_root)
    report = json.loads(result.stdout)
    assert result.returncode == 0
    assert report["status"] == "pass"


def test_workspace_verify_warns_for_local_only_manifest_entries_missing_in_clean_clone(workspace_root: Path) -> None:
    aurora_local_only = workspace_root / "Aurora_Sim_Architecture"
    write_file(aurora_local_only / "scope_note.md", "Aurora forecast working note.\n")

    run_command(
        [
            sys.executable,
            str(workspace_root / "tools" / "workspace_scan.py"),
            "--root",
            str(workspace_root),
        ],
        cwd=workspace_root,
    )

    manifest = workspace_common.load_yaml_like(workspace_root / "catalog" / "workspace_manifest.yaml")
    manifest_paths = {entry["current_path"] for entry in manifest["entries"]}
    assert "Aurora_Sim_Architecture" in manifest_paths

    shutil.rmtree(aurora_local_only)

    result = run_verify(workspace_root)
    report = json.loads(result.stdout)

    assert result.returncode == 0
    assert report["status"] == "warn"
    assert any(
        finding["check"] == "manifest_execution_context"
        and not finding["blocking"]
        and "Aurora_Sim_Architecture" in finding["details"]
        for finding in report["findings"]
    )
    assert not any(
        finding["check"] == "manifest_top_level_coverage"
        and finding["blocking"]
        and "Aurora_Sim_Architecture" in finding["details"]
        for finding in report["findings"]
    )


def test_workspace_scan_summary_redacts_privacy_exclusions(workspace_root: Path) -> None:
    write_file(
        workspace_root / "notes.txt",
        "Patient Name: Jane Example\nDate of Birth: 1990-01-01\nTherapy options attached.\n",
    )
    (workspace_root / "document.bin").write_bytes(b"%PDF-1.4\nPatient Name Jane Example\nDate of Birth 1990-01-01\n")

    run_command(
        [
            sys.executable,
            str(workspace_root / "tools" / "workspace_scan.py"),
            "--root",
            str(workspace_root),
        ],
        cwd=workspace_root,
    )

    summary = json.loads((workspace_root / "reports" / "analysis" / "workspace_scan_summary.json").read_text(encoding="utf-8"))
    workspace_map = (workspace_root / "docs" / "workspace-map.md").read_text(encoding="utf-8")

    assert summary["privacy_exclusion_count"] == 2
    assert summary["privacy_exclusion_reasons"]["auto_private_content"] == 2
    assert "Top-level paths excluded by privacy screen: `2`" in workspace_map
    assert "notes.txt" not in workspace_map
    assert "document.bin" not in workspace_map


def test_workspace_verify_blocks_redacted_path_leaks_in_generated_artifacts(workspace_root: Path) -> None:
    write_file(
        workspace_root / "notes.txt",
        "Patient Name: Jane Example\nDate of Birth: 1990-01-01\nTherapy options attached.\n",
    )

    run_command(
        [
            sys.executable,
            str(workspace_root / "tools" / "workspace_scan.py"),
            "--root",
            str(workspace_root),
        ],
        cwd=workspace_root,
    )

    workspace_map_path = workspace_root / "docs" / "workspace-map.md"
    leaked_map = workspace_map_path.read_text(encoding="utf-8") + "\n- `notes.txt`\n"
    workspace_map_path.write_text(leaked_map, encoding="utf-8")

    result = run_verify(workspace_root)
    report = json.loads(result.stdout)

    assert result.returncode == 1
    assert report["status"] == "fail"
    assert any(finding["check"] == "privacy_redaction_coverage" for finding in report["findings"])


def test_load_yaml_like_supports_generated_yaml_without_pyyaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_registry_yaml = """generated_at: '2026-03-10T00:00:00Z'
root: .
repos:
- name: aurora-cloudbank-symbolic-main
  path: GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main
  branch: main
  head_sha: 42e0b9fb9f1e0e10a9091d595cf2811f2c14eacf
  remote_status: configured
  validation_command: env -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE -u GIT_PREFIX
    git -C GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main rev-parse
    HEAD && env -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE -u GIT_PREFIX git -C
    GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main status --short
    --branch
  move_policy: frozen_until_registry_adoption
"""
    yaml_path = tmp_path / "repo_registry.yaml"
    write_file(yaml_path, repo_registry_yaml)

    original_import = builtins.__import__

    def blocked_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "yaml":
            raise ImportError("yaml disabled for test")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)

    payload = workspace_common.load_yaml_like(yaml_path)

    assert payload["root"] == "."
    assert payload["repos"][0]["name"] == "aurora-cloudbank-symbolic-main"
    assert payload["repos"][0]["remote_status"] == "configured"
    assert payload["repos"][0]["validation_command"] == (
        "env -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE -u GIT_PREFIX "
        "git -C GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main rev-parse "
        "HEAD && env -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE -u GIT_PREFIX git -C "
        "GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main status --short "
        "--branch"
    )


def test_dump_yaml_like_preserves_yaml_syntax_without_pyyaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "generated_at": "2026-03-10T00:00:00Z",
        "root": ".",
        "repos": [
            {
                "name": "aurora-cloudbank-symbolic-main",
                "path": "GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main",
                "branch": "main",
                "head_sha": "42e0b9fb9f1e0e10a9091d595cf2811f2c14eacf",
                "remote_status": "configured",
                "validation_command": "git -C GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main status --short --branch",
                "move_policy": "frozen_until_registry_adoption",
            }
        ],
    }
    yaml_path = tmp_path / "repo_registry.yaml"

    original_import = builtins.__import__

    def blocked_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "yaml":
            raise ImportError("yaml disabled for test")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)

    workspace_common.dump_yaml_like(payload, yaml_path)
    rendered = yaml_path.read_text(encoding="utf-8")

    assert rendered.startswith('generated_at: "2026-03-10T00:00:00Z"\n')
    assert "{\n" not in rendered
    assert "\nrepos:\n  -\n" in rendered
    assert workspace_common.load_yaml_like(yaml_path) == payload


def test_explicit_determinism_and_relocation_checks_pass(workspace_root: Path) -> None:
    result = run_verify(workspace_root, "--check-determinism", "--exercise-relocation")
    report = json.loads(result.stdout)
    assert result.returncode == 0
    assert report["status"] == "pass"

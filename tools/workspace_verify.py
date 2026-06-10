#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from _workspace_common import (
    TRACKED_FILE_SIZE_LIMIT_BYTES,
    discover_nested_repos,
    git,
    load_yaml_like,
    manifest_enforced_current_paths,
    now_iso_utc,
    resolve_root,
    serialized_root,
    sha256_path,
    top_level_policy_records,
    top_level_policy_records_with_redaction,
    write_json,
)


DEFAULT_REPORT_RELATIVE_PATH = Path("reports") / "analysis" / "workspace_verify_latest.json"
GIT_ENV_STRIP_KEYS = {"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"}


@dataclass(frozen=True)
class Finding:
    check: str
    severity: str
    blocking: bool
    details: str
    suggested_fix: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def error(check: str, details: str, suggested_fix: str) -> Finding:
    return Finding(
        check=check,
        severity="error",
        blocking=True,
        details=details,
        suggested_fix=suggested_fix,
    )


def warning(check: str, details: str, suggested_fix: str) -> Finding:
    return Finding(
        check=check,
        severity="warning",
        blocking=False,
        details=details,
        suggested_fix=suggested_fix,
    )


def clean_env() -> dict[str, str]:
    return {
        key: value
        for key, value in os.environ.items()
        if key not in GIT_ENV_STRIP_KEYS
    }


def load_manifest_entries(root: Path, filename: str, key: str) -> tuple[list[dict[str, Any]], list[Finding]]:
    path = root / "catalog" / filename
    try:
        payload = load_yaml_like(path)
    except FileNotFoundError:
        return [], [error(key, f"Missing required file: {path}", f"Regenerate `{filename}` before running workspace verification.")]
    except Exception as exc:
        return [], [error(key, f"Could not read {path}: {exc}", f"Repair or regenerate `{filename}` before running workspace verification.")]

    entries = payload.get(key) if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        return [], [error(key, f"{path} is missing a valid `{key}` list.", f"Regenerate `{filename}` to restore the expected schema.")]
    normalized = [entry for entry in entries if isinstance(entry, dict)]
    if len(normalized) != len(entries):
        return [], [error(key, f"{path} contains non-object rows in `{key}`.", f"Regenerate `{filename}` to restore the expected schema.")]
    return normalized, []


def load_relocation_plan(root: Path) -> tuple[dict[str, Any] | None, list[Finding]]:
    path = root / "catalog" / "relocation_plan.json"
    try:
        payload = load_yaml_like(path)
    except FileNotFoundError:
        return None, [error("relocation_plan", f"Missing required file: {path}", "Run `python3 tools/workspace_plan_moves.py` to restore the relocation plan.")]
    except Exception as exc:
        return None, [error("relocation_plan", f"Could not read {path}: {exc}", "Regenerate `catalog/relocation_plan.json` before running workspace verification.")]

    if not isinstance(payload, dict) or not isinstance(payload.get("batches"), list):
        return None, [error("relocation_plan", f"{path} is missing a valid `batches` list.", "Regenerate `catalog/relocation_plan.json` before running workspace verification.")]
    return payload, []


def compare_jsonl(path: Path) -> list[dict[str, object]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def is_repo_path_issue(message: str) -> bool:
    lowered = message.lower()
    return any(
        token in lowered
        for token in (
            "not a git repository",
            "no such file or directory",
            "cannot change to",
            "cannot chdir",
            "unable to read current working directory",
        )
    )


def verify_root_git_repo(root: Path) -> list[Finding]:
    try:
        git(["rev-parse", "--show-toplevel"], cwd=root)
    except subprocess.CalledProcessError:
        return [
            error(
                "root_git_repo",
                "The selected root is not a git repository.",
                "Run the verifier from the root control-plane repo or pass `--root` with the correct repo path.",
            )
        ]
    return []


def verify_manifest(root: Path) -> list[Finding]:
    manifest_entries, findings = load_manifest_entries(root, "workspace_manifest.yaml", "entries")
    if findings:
        return findings

    actual_paths = manifest_enforced_current_paths(top_level_policy_records(root))
    cataloged_paths = manifest_enforced_current_paths(manifest_entries)
    missing_from_manifest = sorted(actual_paths - cataloged_paths)
    stale_manifest_entries = sorted(cataloged_paths - actual_paths)
    tracked_top_level_paths: set[str] = set()
    tracked_files = git(["ls-files", "-z"], cwd=root, check=False)
    if tracked_files.returncode == 0:
        for raw_path in tracked_files.stdout.split("\0"):
            if not raw_path:
                continue
            tracked_top_level_paths.add(raw_path.split("/", 1)[0])
    blocking_stale_entries = sorted(
        entry
        for entry in stale_manifest_entries
        if entry in tracked_top_level_paths
    )
    execution_context_stale_entries = sorted(
        entry
        for entry in stale_manifest_entries
        if entry not in tracked_top_level_paths
    )

    if not missing_from_manifest and not stale_manifest_entries:
        return []

    details_parts = []
    if missing_from_manifest:
        details_parts.append(f"missing_from_manifest={missing_from_manifest}")
    if blocking_stale_entries:
        details_parts.append(f"stale_manifest_entries={blocking_stale_entries}")

    findings = []
    if details_parts:
        findings.append(
            error(
                "manifest_top_level_coverage",
                "; ".join(details_parts),
                "Run `python3 tools/workspace_scan.py` to regenerate the manifest and workspace map.",
            )
        )
    if execution_context_stale_entries:
        findings.append(
            warning(
                "manifest_execution_context",
                f"Manifest includes local-only top-level entries unavailable here: {execution_context_stale_entries}",
                "Run from the canonical workspace path before treating local-only workspace inventory drift as a blocking failure.",
            )
        )
    return findings


def verify_privacy_redaction(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    _, _, redacted_paths = top_level_policy_records_with_redaction(root)
    if not redacted_paths:
        return findings

    checked_artifacts = [
        ("docs/workspace-map.md", root / "docs" / "workspace-map.md"),
        ("catalog/archive_inventory.jsonl", root / "catalog" / "archive_inventory.jsonl"),
    ]
    leaking_artifacts: set[str] = set()
    leaked_path_count = 0

    for redacted_path in redacted_paths:
        redacted_path_patterns = (
            f"`{redacted_path}`",
            f"`{redacted_path}/",
            f"\"path\": \"{redacted_path}",
            f"\"canonical_candidate\": \"{redacted_path}",
        )
        path_leaked = False
        for artifact_name, artifact_path in checked_artifacts:
            if not artifact_path.exists():
                continue
            text = artifact_path.read_text(encoding="utf-8", errors="ignore")
            if any(pattern in text for pattern in redacted_path_patterns):
                leaking_artifacts.add(artifact_name)
                path_leaked = True
        if path_leaked:
            leaked_path_count += 1

    if leaked_path_count:
        findings.append(
            error(
                "privacy_redaction_coverage",
                f"{leaked_path_count} excluded top-level paths still appear in generated artifacts: {sorted(leaking_artifacts)}",
                "Run `python3 tools/workspace_scan.py` to regenerate redacted artifacts and remove excluded paths from generated outputs.",
            )
        )
    return findings


def verify_repo_registry(root: Path) -> list[Finding]:
    repo_entries, findings = load_manifest_entries(root, "repo_registry.yaml", "repos")
    if findings:
        return findings

    actual_repos = set(discover_nested_repos(root))
    configured_paths = {
        str(repo["path"])
        for repo in repo_entries
        if isinstance(repo.get("path"), str)
    }
    invalid_entries = [
        repo
        for repo in repo_entries
        if not isinstance(repo.get("path"), str)
    ]
    if invalid_entries:
        findings.append(
            error(
                "repo_registry_shape",
                "One or more repo registry entries are missing a string `path` field.",
                "Regenerate `catalog/repo_registry.yaml` with `python3 tools/workspace_scan.py`.",
            )
        )

    missing_from_context = sorted(configured_paths - actual_repos)
    unexpected_actual = sorted(actual_repos - configured_paths)
    if missing_from_context:
        findings.append(
            warning(
                "repo_registry_coverage",
                f"Configured repos are unavailable in this execution context: {missing_from_context}",
                "Run from the canonical workspace path or update `catalog/repo_registry.yaml` if the repo locations changed.",
            )
        )
    if unexpected_actual:
        findings.append(
            error(
                "repo_registry_coverage",
                f"Nested repos exist on disk but are not registered: {unexpected_actual}",
                "Regenerate `catalog/repo_registry.yaml` with `python3 tools/workspace_scan.py`.",
            )
        )

    env = clean_env()
    for repo in repo_entries:
        repo_rel = repo.get("path")
        if not isinstance(repo_rel, str) or repo_rel in missing_from_context:
            continue

        repo_path = root / repo_rel
        if not repo_path.exists():
            findings.append(
                warning(
                    "repo_registry_path",
                    f"{repo_rel} is missing from the current execution context.",
                    "Run from the canonical workspace path or update `catalog/repo_registry.yaml` if the repo locations changed.",
                )
            )
            continue

        branch_result = git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path, check=False)
        head_result = git(["rev-parse", "HEAD"], cwd=repo_path, check=False)
        if branch_result.returncode != 0 or head_result.returncode != 0:
            branch_error = branch_result.stderr.strip()
            head_error = head_result.stderr.strip()
            details = "; ".join(part for part in (branch_error, head_error) if part) or "Git metadata is unavailable."
            findings.append(
                warning(
                    "repo_registry_path",
                    f"{repo_rel} is present but not accessible as a git repo here: {details}",
                    "Run from the canonical workspace path or repair the nested repo checkout before relying on registry verification.",
                )
            )
            continue

        branch = branch_result.stdout.strip()
        head_sha = head_result.stdout.strip()
        expected_branch = str(repo.get("branch", "")).strip()
        expected_head_sha = str(repo.get("head_sha", "")).strip()
        if branch != expected_branch:
            findings.append(
                error(
                    "repo_branch_match",
                    f"{repo_rel} actual={branch} expected={expected_branch}",
                    "Refresh `catalog/repo_registry.yaml` if the branch change is intentional, or restore the expected nested repo branch.",
                )
            )
        if head_sha != expected_head_sha:
            findings.append(
                error(
                    "repo_head_match",
                    f"{repo_rel} actual={head_sha} expected={expected_head_sha}",
                    "Refresh `catalog/repo_registry.yaml` if the nested repo head changed intentionally, or restore the expected commit.",
                )
            )

        validation_command = str(repo.get("validation_command", "")).strip()
        if not validation_command:
            findings.append(
                error(
                    "repo_validation_command",
                    f"{repo_rel} is missing a validation command.",
                    "Regenerate `catalog/repo_registry.yaml` with `python3 tools/workspace_scan.py`.",
                )
            )
            continue

        command = subprocess.run(
            validation_command,
            cwd=root,
            shell=True,
            text=True,
            capture_output=True,
            env=env,
        )
        if command.returncode != 0:
            stderr = command.stderr.strip()
            stdout = command.stdout.strip()
            details = stderr or stdout or "validation command failed without output"
            if is_repo_path_issue(details):
                findings.append(
                    warning(
                        "repo_validation_command",
                        f"{repo_rel}: {details}",
                        "Run from the canonical workspace path or repair the nested repo checkout before relying on registry verification.",
                    )
                )
            else:
                findings.append(
                    error(
                        "repo_validation_command",
                        f"{repo_rel}: {details}",
                        "Repair the nested repo validation command or refresh the registry entry with `python3 tools/workspace_scan.py`.",
                    )
                )
    return findings


def verify_gitignore(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    ignored_targets = [
        "Complete Archive 4_19 copy",
        "Unzipped Archives",
        "Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main",
        "GUMAS_SIM_2.5/CanonRec",
        "intake/example.bin",
        "projects/example.pdf",
        "_staging/example.txt",
        "archives/example.zip",
        "repos/example.txt",
    ]
    tracked_targets = [
        "README.md",
        "catalog/workspace_manifest.yaml",
        "tools/workspace_scan.py",
        "tests/test_workspace_verify.py",
        "reports/analysis/example.md",
    ]
    for target in ignored_targets:
        result = subprocess.run(
            ["git", "check-ignore", "-q", target],
            cwd=root,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            findings.append(
                error(
                    "gitignore_ignored_target",
                    f"Expected `{target}` to be ignored by git.",
                    "Update `.gitignore` so workspace content zones and nested repos remain untracked at the root level.",
                )
            )
    for target in tracked_targets:
        result = subprocess.run(
            ["git", "check-ignore", "-q", target],
            cwd=root,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            findings.append(
                error(
                    "gitignore_tracked_target",
                    f"Expected `{target}` to remain trackable, but git ignores it.",
                    "Update `.gitignore` so control-plane files remain trackable.",
                )
            )
    return findings


def verify_tracked_sizes(root: Path) -> list[Finding]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=root,
            text=False,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        return [
            error(
                "tracked_file_size_limit",
                f"Could not enumerate tracked files: {exc.stderr.decode('utf-8', errors='ignore') if exc.stderr else exc}",
                "Repair the root git checkout before relying on tracked file size validation.",
            )
        ]

    entries = [item.decode("utf-8") for item in result.stdout.split(b"\x00") if item]
    oversized = []
    for entry in entries:
        path = root / entry
        if path.exists() and path.stat().st_size > TRACKED_FILE_SIZE_LIMIT_BYTES:
            oversized.append(f"{entry}:{path.stat().st_size}")
    if not oversized:
        return []
    return [
        error(
            "tracked_file_size_limit",
            ", ".join(oversized),
            "Move large files out of root git history or lower their tracked footprint before committing.",
        )
    ]


def verify_relocation_plan(root: Path) -> list[Finding]:
    plan, findings = load_relocation_plan(root)
    if findings:
        return findings

    for batch in plan["batches"]:
        batch_id = str(batch.get("batch_id", "<unknown>"))
        rollback_manifest = batch.get("rollback_manifest")
        if not isinstance(rollback_manifest, str):
            findings.append(
                error(
                    "rollback_manifest_exists",
                    f"{batch_id} is missing a string rollback manifest path.",
                    "Regenerate `catalog/relocation_plan.json` before applying moves.",
                )
            )
            continue

        rollback_path = root / rollback_manifest
        if not rollback_path.exists():
            findings.append(
                error(
                    "rollback_manifest_exists",
                    f"{batch_id} references a missing rollback manifest: {rollback_path}",
                    "Regenerate the relocation plan so every batch has a matching rollback manifest.",
                )
            )

        operations = batch.get("operations")
        if not isinstance(operations, list):
            findings.append(
                error(
                    "relocation_operation_shape",
                    f"{batch_id} is missing a valid operations list.",
                    "Regenerate the relocation plan so every batch includes serialized move operations.",
                )
            )
            continue

        for operation in operations:
            if not isinstance(operation, dict):
                findings.append(
                    error(
                        "relocation_operation_shape",
                        f"{batch_id} contains a non-object operation entry.",
                        "Regenerate the relocation plan so every operation has the expected serialized shape.",
                    )
                )
                continue

            required = {
                "batch_id",
                "source",
                "destination",
                "operation",
                "pre_hash",
                "post_hash",
                "rollback_source",
                "reason",
                "approved",
                "applied_at",
            }
            missing = sorted(required - set(operation))
            if missing:
                findings.append(
                    error(
                        "relocation_operation_shape",
                        f"{batch_id} missing={missing}",
                        "Regenerate the relocation plan so every move operation includes the required fields.",
                    )
                )
            if operation.get("operation") != "move":
                findings.append(
                    error(
                        "relocation_operation_kind",
                        f"{batch_id} has unsupported operation `{operation.get('operation')}`",
                        "Phase 1 supports only move operations; regenerate the relocation plan accordingly.",
                    )
                )
            if "path_kind" in operation and operation["path_kind"] not in {"file", "tree"}:
                findings.append(
                    error(
                        "relocation_path_kind",
                        f"{batch_id} has unsupported path_kind `{operation['path_kind']}`",
                        "Regenerate the relocation plan so path kinds stay within `file` or `tree`.",
                    )
                )
    return findings


def verify_determinism(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        with tempfile.TemporaryDirectory(prefix="aurora_scan_a_") as temp_a, tempfile.TemporaryDirectory(
            prefix="aurora_scan_b_"
        ) as temp_b:
            scan_cmd = [
                "python3",
                str(root / "tools" / "workspace_scan.py"),
                "--root",
                str(root),
            ]
            paths = [
                ("--manifest-out", "workspace_manifest.yaml"),
                ("--inventory-out", "archive_inventory.jsonl"),
                ("--repo-registry-out", "repo_registry.yaml"),
                ("--workspace-map-out", "workspace-map.md"),
                ("--summary-out", "summary.json"),
            ]
            cmd_a = scan_cmd[:]
            cmd_b = scan_cmd[:]
            for flag, filename in paths:
                cmd_a.extend([flag, str(Path(temp_a) / filename)])
                cmd_b.extend([flag, str(Path(temp_b) / filename)])
            subprocess.run(cmd_a, cwd=root, check=True, capture_output=True, text=True)
            subprocess.run(cmd_b, cwd=root, check=True, capture_output=True, text=True)

            manifest_a = load_yaml_like(Path(temp_a) / "workspace_manifest.yaml")
            manifest_b = load_yaml_like(Path(temp_b) / "workspace_manifest.yaml")
            manifest_a.pop("generated_at", None)
            manifest_b.pop("generated_at", None)
            registry_a = load_yaml_like(Path(temp_a) / "repo_registry.yaml")
            registry_b = load_yaml_like(Path(temp_b) / "repo_registry.yaml")
            registry_a.pop("generated_at", None)
            registry_b.pop("generated_at", None)
            inventory_a = compare_jsonl(Path(temp_a) / "archive_inventory.jsonl")
            inventory_b = compare_jsonl(Path(temp_b) / "archive_inventory.jsonl")

            if manifest_a != manifest_b:
                findings.append(
                    error(
                        "scan_manifest_determinism",
                        "Manifest output changed across identical scans.",
                        "Repair `tools/workspace_scan.py` so repeated scans produce stable manifest output.",
                    )
                )
            if registry_a != registry_b:
                findings.append(
                    error(
                        "scan_registry_determinism",
                        "Repo registry output changed across identical scans.",
                        "Repair `tools/workspace_scan.py` so repeated scans produce stable registry output.",
                    )
                )
            if inventory_a != inventory_b:
                findings.append(
                    error(
                        "scan_inventory_determinism",
                        "Archive inventory output changed across identical scans.",
                        "Repair `tools/workspace_scan.py` so repeated scans produce stable archive inventory output.",
                    )
                )
    except subprocess.CalledProcessError as exc:
        details = exc.stderr.strip() if exc.stderr else str(exc)
        findings.append(
            error(
                "scan_determinism_runtime",
                f"Determinism check could not complete: {details}",
                "Repair the scanner runtime before relying on determinism validation.",
            )
        )
    return findings


def verify_relocation_rehearsal(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        with tempfile.TemporaryDirectory(prefix="aurora_rehearsal_") as temp_dir:
            temp_root = Path(temp_dir) / "workspace"
            (temp_root / "source").mkdir(parents=True)
            (temp_root / "catalog").mkdir()
            (temp_root / "reports" / "analysis").mkdir(parents=True)
            sample_file = temp_root / "source" / "sample_report.md"
            sample_file.write_text("# sample\n", encoding="utf-8")
            file_digest = sha256_path(sample_file)
            sample_tree = temp_root / "source" / "sample_tree"
            (sample_tree / "nested").mkdir(parents=True)
            (sample_tree / "nested" / "a.txt").write_text("alpha\n", encoding="utf-8")
            (sample_tree / "b.json").write_text("{\"ok\": true}\n", encoding="utf-8")
            tree_digest = sha256_path(sample_tree)

            file_plan = {
                "generated_at": now_iso_utc(),
                "batches": [
                    {
                        "batch_id": "rehearsal_file",
                        "status": "approved",
                        "rollback_manifest": "catalog/rollback_rehearsal_file.json",
                        "operations": [
                            {
                                "batch_id": "rehearsal_file",
                                "source": "source/sample_report.md",
                                "destination": "_staging/sample_report.md",
                                "operation": "move",
                                "pre_hash": file_digest,
                                "post_hash": file_digest,
                                "rollback_source": "source/sample_report.md",
                                "reason": "rehearsal file move",
                                "path_kind": "file",
                                "approved": True,
                                "applied_at": None,
                            }
                        ],
                    }
                ],
            }
            file_rollback = {
                "batch_id": "rehearsal_file_rollback",
                "for_batch": "rehearsal_file",
                "generated_at": now_iso_utc(),
                "operations": [
                    {
                        "batch_id": "rehearsal_file_rollback",
                        "source": "_staging/sample_report.md",
                        "destination": "source/sample_report.md",
                        "operation": "move",
                        "pre_hash": file_digest,
                        "post_hash": file_digest,
                        "rollback_source": "_staging/sample_report.md",
                        "reason": "rollback file rehearsal",
                        "path_kind": "file",
                        "approved": True,
                        "applied_at": None,
                    }
                ],
            }
            tree_plan = {
                "generated_at": now_iso_utc(),
                "batches": [
                    {
                        "batch_id": "rehearsal_tree",
                        "status": "approved",
                        "rollback_manifest": "catalog/rollback_rehearsal_tree.json",
                        "operations": [
                            {
                                "batch_id": "rehearsal_tree",
                                "source": "source/sample_tree",
                                "destination": "_staging/sample_tree",
                                "operation": "move",
                                "pre_hash": tree_digest,
                                "post_hash": tree_digest,
                                "rollback_source": "source/sample_tree",
                                "reason": "rehearsal tree move",
                                "path_kind": "tree",
                                "approved": True,
                                "applied_at": None,
                            }
                        ],
                    }
                ],
            }
            tree_rollback = {
                "batch_id": "rehearsal_tree_rollback",
                "for_batch": "rehearsal_tree",
                "generated_at": now_iso_utc(),
                "operations": [
                    {
                        "batch_id": "rehearsal_tree_rollback",
                        "source": "_staging/sample_tree",
                        "destination": "source/sample_tree",
                        "operation": "move",
                        "pre_hash": tree_digest,
                        "post_hash": tree_digest,
                        "rollback_source": "_staging/sample_tree",
                        "reason": "rollback tree rehearsal",
                        "path_kind": "tree",
                        "approved": True,
                        "applied_at": None,
                    }
                ],
            }
            (temp_root / "_staging").mkdir()
            write_json(temp_root / "catalog" / "relocation_plan_file.json", file_plan)
            write_json(temp_root / "catalog" / "rollback_rehearsal_file.json", file_rollback)
            write_json(temp_root / "catalog" / "relocation_plan_tree.json", tree_plan)
            write_json(temp_root / "catalog" / "rollback_rehearsal_tree.json", tree_rollback)

            scenarios = [
                (
                    "file",
                    temp_root / "catalog" / "relocation_plan_file.json",
                    "rehearsal_file",
                    temp_root / "catalog" / "rollback_rehearsal_file.json",
                    temp_root / "source" / "sample_report.md",
                ),
                (
                    "tree",
                    temp_root / "catalog" / "relocation_plan_tree.json",
                    "rehearsal_tree",
                    temp_root / "catalog" / "rollback_rehearsal_tree.json",
                    temp_root / "source" / "sample_tree",
                ),
            ]

            for label, plan_path, batch_id, rollback_path, final_path in scenarios:
                apply_cmd = [
                    "python3",
                    str(root / "tools" / "workspace_apply_moves.py"),
                    "--root",
                    str(temp_root),
                    "--plan",
                    str(plan_path),
                    "--batch-id",
                    batch_id,
                    "--execute",
                ]
                rollback_cmd = [
                    "python3",
                    str(root / "tools" / "workspace_apply_moves.py"),
                    "--root",
                    str(temp_root),
                    "--rollback-manifest",
                    str(rollback_path),
                    "--execute",
                ]
                apply_result = subprocess.run(apply_cmd, cwd=root, capture_output=True, text=True, check=False)
                rollback_result = subprocess.run(rollback_cmd, cwd=root, capture_output=True, text=True, check=False)
                if apply_result.returncode != 0:
                    findings.append(
                        error(
                            f"relocation_rehearsal_apply_{label}",
                            apply_result.stderr.strip() or "move rehearsal failed",
                            "Repair `tools/workspace_apply_moves.py` so forward move rehearsals pass.",
                        )
                    )
                if rollback_result.returncode != 0:
                    findings.append(
                        error(
                            f"relocation_rehearsal_rollback_{label}",
                            rollback_result.stderr.strip() or "rollback rehearsal failed",
                            "Repair `tools/workspace_apply_moves.py` so rollback rehearsals pass.",
                        )
                    )
                if not final_path.exists():
                    findings.append(
                        error(
                            f"relocation_rehearsal_final_state_{label}",
                            f"{label} sample missing after rollback",
                            "Repair relocation rollback handling so rehearsed content is restored after rollback.",
                        )
                    )
    except Exception as exc:
        findings.append(
            error(
                "relocation_rehearsal_runtime",
                f"Relocation rehearsal could not complete: {exc}",
                "Repair the relocation rehearsal harness before relying on move safety validation.",
            )
        )
    return findings


def verify_session_state(root: Path) -> list[Finding]:
    """Non-blocking: warn when session_state.json is stale vs HEAD.

    Stale state means the last session didn't update the handoff file, so
    the other platform (Codex) may be operating on outdated information.
    Allowed to be 1 commit behind (the auto-commit itself may not have fired
    yet). Two or more commits behind is surfaced as a warning.
    """
    import subprocess as _sp
    state_path = root / "catalog" / "session_state.json"
    if not state_path.exists():
        return []
    try:
        import json as _json
        state = _json.loads(state_path.read_text())
    except Exception:
        return []

    known_sha = state.get("known_state", {}).get("main_sha", "")
    if not known_sha:
        return []

    try:
        # Count commits between known_sha and HEAD
        result = _sp.run(
            ["git", "rev-list", "--count", f"{known_sha}..HEAD"],
            capture_output=True, text=True, cwd=root, check=False,
        )
        if result.returncode != 0:
            return []  # known_sha may not be in history (cross-branch)
        ahead = int(result.stdout.strip() or 0)
    except Exception:
        return []

    if ahead <= 1:
        return []  # 0 = current; 1 = auto-commit pending, acceptable

    return [
        warning(
            "session_state_freshness",
            f"catalog/session_state.json is {ahead} commit(s) behind HEAD "
            f"(last recorded: {known_sha}). The other platform may be operating "
            "on stale workspace context.",
            "Run `python3 tools/session_stop_hook.py` to auto-update, or update "
            "catalog/session_state.json manually and commit.",
        )
    ]


GIT_LOCK_STALE_SECONDS = 30 * 60


def verify_canon_resolvability(root: Path) -> list[Finding]:
    """Warn when the newest L1 Entity Ledger cites canon files that don't resolve.

    The narrative-layer promotion (ADR 2026-06-10) makes canon a dependency:
    every ledger entity carries a `canon_file` path into CanonRec. A citation
    that stops resolving means canon drift between the ledger and CanonRec.
    """
    findings: list[Finding] = []
    ledger_dir = root / "reports" / "analysis"
    ledgers = sorted(ledger_dir.glob("L1_ENTITY_LEDGER__*.json"))
    if not ledgers:
        return findings
    newest = ledgers[-1]
    try:
        payload = json.loads(newest.read_text(encoding="utf-8"))
    except Exception as exc:
        return [warning("canon_resolvability", f"Could not parse {newest.name}: {exc}",
                        "Regenerate the L1 Entity Ledger.")]
    missing = []
    for human in payload.get("humans", []):
        canon_file = human.get("canon_file")
        if canon_file and not (root / canon_file).exists():
            missing.append(f"{human.get('entity_id', '?')} -> {canon_file}")
    if missing:
        sample = "; ".join(missing[:3])
        findings.append(
            warning(
                "canon_resolvability",
                f"{newest.name}: {len(missing)} canon citation(s) do not resolve (e.g. {sample}).",
                "Restore the cited CanonRec files or regenerate the ledger against current canon.",
            )
        )
    return findings


def verify_git_locks(root: Path) -> list[Finding]:
    """Warn about stale .git/index.lock files that silently block commits.

    A zero-byte index.lock left behind by a crashed git process blocks every
    subsequent commit in that repo without any visible signal until the next
    commit attempt (observed 2026-06-01 in aurora-cloudbank-symbolic-main and
    2026-05-23 in qgia-knowledge-library-main).
    """
    findings: list[Finding] = []
    candidates: list[tuple[str, Path]] = [("root", root)]
    try:
        payload = load_yaml_like(root / "catalog" / "repo_registry.yaml")
        for repo in payload.get("repos", []):
            path = str(repo.get("path", ""))
            if not path or path.startswith("~"):
                continue
            candidates.append((str(repo.get("name", path)), root / path))
    except Exception:
        # Registry load problems are reported by verify_repo_registry.
        pass

    now = time.time()
    for name, repo_path in candidates:
        lock = repo_path / ".git" / "index.lock"
        try:
            age_seconds = now - lock.stat().st_mtime
        except OSError:
            continue
        if age_seconds > GIT_LOCK_STALE_SECONDS:
            age_minutes = int(age_seconds // 60)
            findings.append(
                warning(
                    "git_index_lock",
                    f"{name}: .git/index.lock is {age_minutes} minutes old; a"
                    " crashed git process has likely left this repo unable to"
                    " commit.",
                    "Confirm no git process is using the repo, then remove"
                    f" `{lock}`.",
                )
            )
    return findings


def run_checks(root: Path, include_determinism: bool, include_relocation_rehearsal: bool) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(verify_root_git_repo(root))
    findings.extend(verify_git_locks(root))
    findings.extend(verify_canon_resolvability(root))
    findings.extend(verify_manifest(root))
    findings.extend(verify_privacy_redaction(root))
    findings.extend(verify_repo_registry(root))
    findings.extend(verify_gitignore(root))
    findings.extend(verify_relocation_plan(root))
    findings.extend(verify_tracked_sizes(root))
    findings.extend(verify_session_state(root))
    if include_determinism:
        findings.extend(verify_determinism(root))
    if include_relocation_rehearsal:
        findings.extend(verify_relocation_rehearsal(root))
    return findings


def summarize_status(findings: list[Finding]) -> str:
    if any(finding.blocking for finding in findings):
        return "fail"
    if findings:
        return "warn"
    return "pass"


def build_report(root: Path, mode: str, findings: list[Finding]) -> dict[str, Any]:
    return {
        "generated_at": now_iso_utc(),
        "root": serialized_root(root),
        "mode": mode,
        "status": summarize_status(findings),
        "summary": {
            "finding_count": len(findings),
            "blocking_count": sum(1 for finding in findings if finding.blocking),
            "warning_count": sum(1 for finding in findings if not finding.blocking),
        },
        "findings": [finding.to_dict() for finding in findings],
    }


def format_terminal_output(findings: list[Finding]) -> str:
    blocking = sorted(
        [finding for finding in findings if finding.blocking],
        key=lambda finding: (finding.check, finding.details),
    )
    warnings_only = sorted(
        [finding for finding in findings if not finding.blocking],
        key=lambda finding: (finding.check, finding.details),
    )
    sections: list[str] = []
    if blocking:
        lines = ["Blocking failures:"]
        for finding in blocking:
            lines.append(f"- {finding.check}: {finding.details}")
            lines.append(f"  Fix: {finding.suggested_fix}")
        sections.append("\n".join(lines))
    if warnings_only:
        lines = ["Warnings:"]
        for finding in warnings_only:
            lines.append(f"- {finding.check}: {finding.details}")
            lines.append(f"  Fix: {finding.suggested_fix}")
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


def resolve_report_path(root: Path, explicit_path: str | None, persist_report: bool) -> Path | None:
    if explicit_path:
        return Path(explicit_path)
    if persist_report:
        return root / DEFAULT_REPORT_RELATIVE_PATH
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the Aurora workspace control plane.")
    parser.add_argument("--root", default=None)
    parser.add_argument("--git-pre-commit", action="store_true")
    parser.add_argument("--check-determinism", action="store_true")
    parser.add_argument("--exercise-relocation", action="store_true")
    parser.add_argument("--persist-report", action="store_true")
    parser.add_argument("--report-out", default=None)
    args = parser.parse_args()

    root = resolve_root(args.root)
    mode = "pre_commit" if args.git_pre_commit else "manual"
    findings = run_checks(
        root,
        include_determinism=args.check_determinism,
        include_relocation_rehearsal=args.exercise_relocation,
    )
    report = build_report(root, mode, findings)
    report_path = resolve_report_path(root, args.report_out, args.persist_report)

    if report_path is not None:
        write_json(report_path, report)

    if args.git_pre_commit:
        rendered = format_terminal_output(findings)
        if rendered:
            print(rendered)
    else:
        print(json.dumps(report, indent=2))

    return 1 if any(finding.blocking for finding in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())

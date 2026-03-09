#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from _workspace_common import (
    CATALOG_DIR,
    REPORTS_ANALYSIS_DIR,
    TRACKED_FILE_SIZE_LIMIT_BYTES,
    discover_nested_repos,
    git,
    load_yaml_like,
    now_iso_utc,
    relpath,
    resolve_root,
    serialized_root,
    sha256_path,
    top_level_entries,
    write_json,
)


def check(condition: bool, label: str, details: str, failures: list[dict[str, str]]) -> None:
    if not condition:
        failures.append({"check": label, "details": details})


def verify_manifest(root: Path, failures: list[dict[str, str]]) -> None:
    manifest = load_yaml_like(root / "catalog" / "workspace_manifest.yaml")
    cataloged = {entry["current_path"] for entry in manifest["entries"]}
    actual = {relpath(path, root) for path in top_level_entries(root)}
    check(
        cataloged == actual,
        "manifest_top_level_coverage",
        f"cataloged={sorted(cataloged ^ actual)}",
        failures,
    )


def verify_repo_registry(root: Path, failures: list[dict[str, str]]) -> None:
    repo_registry = load_yaml_like(root / "catalog" / "repo_registry.yaml")
    actual_repos = discover_nested_repos(root)
    configured = [repo["path"] for repo in repo_registry["repos"]]
    check(
        sorted(actual_repos) == sorted(configured),
        "repo_registry_coverage",
        f"actual={actual_repos} configured={configured}",
        failures,
    )
    for repo in repo_registry["repos"]:
        repo_path = root / repo["path"]
        branch = git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path).stdout.strip()
        head_sha = git(["rev-parse", "HEAD"], cwd=repo_path).stdout.strip()
        command = subprocess.run(
            repo["validation_command"],
            cwd=root,
            shell=True,
            text=True,
            capture_output=True,
            env={
                key: value
                for key, value in __import__("os").environ.items()
                if key not in {"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"}
            },
        )
        check(
            branch == repo["branch"],
            "repo_branch_match",
            f"{repo['path']} actual={branch} expected={repo['branch']}",
            failures,
        )
        check(
            head_sha == repo["head_sha"],
            "repo_head_match",
            f"{repo['path']} actual={head_sha} expected={repo['head_sha']}",
            failures,
        )
        check(
            command.returncode == 0,
            "repo_validation_command",
            f"{repo['path']} stderr={command.stderr.strip()}",
            failures,
        )


def verify_gitignore(root: Path, failures: list[dict[str, str]]) -> None:
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
        "reports/analysis/example.md",
    ]
    for target in ignored_targets:
        result = subprocess.run(
            ["git", "check-ignore", "-q", target],
            cwd=root,
            capture_output=True,
        )
        check(result.returncode == 0, "gitignore_ignored_target", target, failures)
    for target in tracked_targets:
        result = subprocess.run(
            ["git", "check-ignore", "-q", target],
            cwd=root,
            capture_output=True,
        )
        check(result.returncode != 0, "gitignore_tracked_target", target, failures)


def verify_tracked_sizes(root: Path, failures: list[dict[str, str]]) -> None:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        text=False,
        capture_output=True,
        check=True,
    )
    entries = [item.decode("utf-8") for item in result.stdout.split(b"\x00") if item]
    oversized = []
    for entry in entries:
        path = root / entry
        if path.exists() and path.stat().st_size > TRACKED_FILE_SIZE_LIMIT_BYTES:
            oversized.append(f"{entry}:{path.stat().st_size}")
    check(
        not oversized,
        "tracked_file_size_limit",
        ", ".join(oversized),
        failures,
    )


def verify_relocation_plan(root: Path, failures: list[dict[str, str]]) -> None:
    plan = load_yaml_like(root / "catalog" / "relocation_plan.json")
    for batch in plan["batches"]:
        rollback_path = root / batch["rollback_manifest"]
        check(rollback_path.exists(), "rollback_manifest_exists", str(rollback_path), failures)
        for operation in batch["operations"]:
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
            missing = required - set(operation)
            check(
                not missing,
                "relocation_operation_shape",
                f"{batch['batch_id']} missing={sorted(missing)}",
                failures,
            )
            check(
                operation["operation"] == "move",
                "relocation_operation_kind",
                f"{batch['batch_id']} has {operation['operation']}",
                failures,
            )
            if "path_kind" in operation:
                check(
                    operation["path_kind"] in {"file", "tree"},
                    "relocation_path_kind",
                    f"{batch['batch_id']} has {operation['path_kind']}",
                    failures,
                )


def compare_jsonl(path: Path) -> list[dict[str, object]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def verify_determinism(root: Path, failures: list[dict[str, str]]) -> None:
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
        subprocess.run(cmd_a, cwd=root, check=True)
        subprocess.run(cmd_b, cwd=root, check=True)

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

        check(manifest_a == manifest_b, "scan_manifest_determinism", "manifest mismatch", failures)
        check(registry_a == registry_b, "scan_registry_determinism", "repo registry mismatch", failures)
        check(inventory_a == inventory_b, "scan_inventory_determinism", "inventory mismatch", failures)


def verify_relocation_rehearsal(root: Path, failures: list[dict[str, str]]) -> None:
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
            apply_result = subprocess.run(apply_cmd, cwd=root, capture_output=True, text=True)
            rollback_result = subprocess.run(rollback_cmd, cwd=root, capture_output=True, text=True)
            check(
                apply_result.returncode == 0,
                f"relocation_rehearsal_apply_{label}",
                apply_result.stderr.strip(),
                failures,
            )
            check(
                rollback_result.returncode == 0,
                f"relocation_rehearsal_rollback_{label}",
                rollback_result.stderr.strip(),
                failures,
            )
            check(
                final_path.exists(),
                f"relocation_rehearsal_final_state_{label}",
                f"{label} sample missing after rollback",
                failures,
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the Aurora workspace control plane.")
    parser.add_argument("--root", default=None)
    parser.add_argument("--git-pre-commit", action="store_true")
    parser.add_argument("--check-determinism", action="store_true")
    parser.add_argument("--exercise-relocation", action="store_true")
    parser.add_argument(
        "--report-out",
        default=None,
    )
    args = parser.parse_args()

    root = resolve_root(args.root)
    report_out = (
        Path(args.report_out)
        if args.report_out
        else root / "reports" / "analysis" / "workspace_verify_latest.json"
    )
    failures: list[dict[str, str]] = []

    try:
        git(["rev-parse", "--show-toplevel"], cwd=root)
    except subprocess.CalledProcessError:
        failures.append({"check": "root_git_repo", "details": "root is not a git repository"})

    verify_manifest(root, failures)
    verify_repo_registry(root, failures)
    verify_gitignore(root, failures)
    verify_relocation_plan(root, failures)
    verify_tracked_sizes(root, failures)

    if args.check_determinism:
        verify_determinism(root, failures)
    if args.exercise_relocation:
        verify_relocation_rehearsal(root, failures)

    report = {
        "generated_at": now_iso_utc(),
        "root": serialized_root(root),
        "failures": failures,
        "status": "pass" if not failures else "fail",
    }
    if not args.git_pre_commit:
        write_json(report_out, report)
    if args.git_pre_commit:
        if failures:
            for failure in failures:
                print(f"{failure['check']}: {failure['details']}")
        return 1 if failures else 0
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

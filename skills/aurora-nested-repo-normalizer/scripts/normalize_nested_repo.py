#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[3]
IGNORED_NAMES = {".DS_Store", ".pytest_cache", "__pycache__", "__MACOSX"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}
GIT_ENV_STRIP_KEYS = {"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"}


def now_iso_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_env() -> Dict[str, str]:
    return {key: value for key, value in os.environ.items() if key not in GIT_ENV_STRIP_KEYS}


def run_command(
    args: List[str],
    cwd: Optional[Path] = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=check,
        env=git_env(),
    )


def run_git(args: List[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run_command(["git"] + args, cwd=cwd, check=check)


def is_git_repo(path: Path) -> bool:
    result = run_git(["rev-parse", "--show-toplevel"], cwd=path, check=False)
    return result.returncode == 0


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def should_ignore(parts: Tuple[str, ...], is_dir: bool) -> bool:
    for part in parts:
        if part in IGNORED_NAMES:
            return True
    if not parts:
        return False
    name = parts[-1]
    if name in IGNORED_NAMES:
        return True
    if not is_dir and Path(name).suffix in IGNORED_SUFFIXES:
        return True
    return False


def iter_tracked_files(root: Path) -> Iterable[Path]:
    for current_root, dirnames, filenames in os.walk(root):
        current = Path(current_root)
        relative_dir = current.relative_to(root)

        filtered_dirnames = []
        for dirname in sorted(dirnames):
            relative_parts = relative_dir.parts + (dirname,)
            if dirname == ".git" or should_ignore(relative_parts, is_dir=True):
                continue
            filtered_dirnames.append(dirname)
        dirnames[:] = filtered_dirnames

        for filename in sorted(filenames):
            relative_parts = relative_dir.parts + (filename,)
            if should_ignore(relative_parts, is_dir=False):
                continue
            yield current / filename


def collect_tree_state(root: Path) -> Dict[str, Dict[str, Any]]:
    state: Dict[str, Dict[str, Any]] = {}
    for path in iter_tracked_files(root):
        relative = path.relative_to(root).as_posix()
        stat = path.stat()
        state[relative] = {
            "size": stat.st_size,
            "sha256": sha256_file(path),
        }
    return state


def compare_trees(target: Path, reference: Path) -> Dict[str, Any]:
    target_state = collect_tree_state(target)
    reference_state = collect_tree_state(reference)

    target_paths = set(target_state)
    reference_paths = set(reference_state)
    shared_paths = sorted(target_paths & reference_paths)

    content_mismatches = []
    for relative in shared_paths:
        if target_state[relative] != reference_state[relative]:
            content_mismatches.append(relative)

    return {
        "matches": not (target_paths - reference_paths or reference_paths - target_paths or content_mismatches),
        "only_in_target": sorted(target_paths - reference_paths),
        "only_in_reference": sorted(reference_paths - target_paths),
        "content_mismatches": content_mismatches,
        "file_count": len(shared_paths),
    }


def get_remote_head(remote: str) -> str:
    result = run_git(["ls-remote", remote, "HEAD"], check=True)
    line = result.stdout.strip().splitlines()[0]
    return line.split()[0]


def normalize_remote_url(url: str) -> str:
    return url.rstrip("/")


def inspect_existing_repo(target: Path) -> Dict[str, Any]:
    origin_result = run_git(["config", "--get", "remote.origin.url"], cwd=target, check=False)
    status_result = run_git(["status", "--short", "--branch"], cwd=target, check=False)
    head_result = run_git(["rev-parse", "HEAD"], cwd=target, check=False)
    return {
        "origin_url": origin_result.stdout.strip(),
        "status": status_result.stdout.strip(),
        "head_sha": head_result.stdout.strip(),
    }


def derive_receipt_path(target: Path, workspace_root: Optional[Path], explicit_out: Optional[Path]) -> Optional[Path]:
    if explicit_out:
        return explicit_out
    if workspace_root is None:
        return None
    return workspace_root / "reports" / "analysis" / "nested-repo-normalizer" / ("%s.json" % target.name)


def write_receipt(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def run_workspace_followup(workspace_root: Path) -> List[Dict[str, Any]]:
    commands = [
        ["python3", "tools/workspace_scan.py"],
        ["python3", "tools/workspace_plan_moves.py"],
        ["python3", "tools/workspace_verify.py"],
        ["python3", "tools/workspace_verify.py", "--persist-report"],
    ]
    results = []
    for command in commands:
        result = run_command(command, cwd=workspace_root, check=False)
        results.append(
            {
                "command": command,
                "returncode": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
            }
        )
        if result.returncode != 0:
            break
    return results


def normalize_nested_repo(
    target: Path,
    remote: str,
    dry_run: bool = False,
    workspace_root: Optional[Path] = None,
    refresh_root_control_plane: bool = False,
    receipt_out: Optional[Path] = None,
    clone_if_missing: bool = False,
) -> Dict[str, Any]:
    if target.exists() and not target.is_dir():
        raise NotADirectoryError("Target path is not a directory: %s" % target)
    if refresh_root_control_plane and workspace_root is None:
        raise ValueError("--refresh-root-control-plane requires --workspace-root")

    remote_head = get_remote_head(remote)
    receipt: Dict[str, Any] = {
        "generated_at": now_iso_utc(),
        "target": str(target),
        "remote": remote,
        "remote_head": remote_head,
        "dry_run": dry_run,
        "workspace_root": str(workspace_root) if workspace_root else None,
        "clone_if_missing": clone_if_missing,
        "status": "pending",
        "tree_compare": None,
        "workspace_followup": [],
    }
    output_path = derive_receipt_path(target, workspace_root, receipt_out)
    temp_root: Optional[Path] = None
    try:
        if not target.exists():
            if not clone_if_missing:
                raise FileNotFoundError("Target path does not exist: %s" % target)
            receipt["status"] = "target_missing"
            if dry_run:
                receipt["status"] = "would_clone_missing_target"
                return receipt

            target.parent.mkdir(parents=True, exist_ok=True)
            run_git(["clone", remote, str(target)], check=True)
            attached = inspect_existing_repo(target)
            receipt["attached_repo"] = attached
            receipt["status"] = "cloned_missing_target"
            if refresh_root_control_plane and workspace_root is not None:
                receipt["workspace_followup"] = run_workspace_followup(workspace_root)
                if any(step["returncode"] != 0 for step in receipt["workspace_followup"]):
                    receipt["status"] = "cloned_missing_target_with_root_followup_failure"
                else:
                    receipt["status"] = "cloned_missing_target_with_root_followup"
            return receipt

        if is_git_repo(target):
            existing = inspect_existing_repo(target)
            receipt["existing_repo"] = existing
            if normalize_remote_url(existing["origin_url"]) != normalize_remote_url(remote):
                receipt["status"] = "already_git_repo_remote_mismatch"
                return receipt
            receipt["status"] = "already_normalized"
            if refresh_root_control_plane and workspace_root is not None:
                receipt["workspace_followup"] = run_workspace_followup(workspace_root)
                if any(step["returncode"] != 0 for step in receipt["workspace_followup"]):
                    receipt["status"] = "already_normalized_with_root_followup_failure"
                else:
                    receipt["status"] = "already_normalized_with_root_followup"
            return receipt

        temp_root = Path(tempfile.mkdtemp(prefix="aurora-nested-repo-normalizer-"))
        clone_dir = temp_root / "remote-checkout"
        run_git(["clone", remote, str(clone_dir)], check=True)
        remote_branch = run_git(["branch", "--show-current"], cwd=clone_dir).stdout.strip()
        compare_result = compare_trees(target, clone_dir)
        receipt["remote_branch"] = remote_branch
        receipt["tree_compare"] = compare_result

        if not compare_result["matches"]:
            receipt["status"] = "tree_mismatch"
            return receipt

        if dry_run:
            receipt["status"] = "dry_run_match"
            return receipt

        shutil.copytree(clone_dir / ".git", target / ".git")
        attached = inspect_existing_repo(target)
        receipt["attached_repo"] = attached
        receipt["status"] = "normalized"

        if refresh_root_control_plane and workspace_root is not None:
            receipt["workspace_followup"] = run_workspace_followup(workspace_root)
            if any(step["returncode"] != 0 for step in receipt["workspace_followup"]):
                receipt["status"] = "normalized_with_root_followup_failure"
            else:
                receipt["status"] = "normalized_with_root_followup"
        return receipt
    finally:
        if temp_root is not None:
            shutil.rmtree(temp_root, ignore_errors=True)
        if output_path is not None:
            receipt["receipt_path"] = str(output_path)
            write_receipt(output_path, receipt)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize an extracted Aurora repo mirror into a real nested Git repo.")
    parser.add_argument("--target", required=True, help="Absolute or relative path to the extracted repo directory.")
    parser.add_argument("--remote", required=True, help="Remote Git URL or local path used as the authoritative source.")
    parser.add_argument("--dry-run", action="store_true", help="Compare the target against the remote checkout without attaching .git.")
    parser.add_argument("--workspace-root", help="Aurora workspace root. Enables default receipt placement and root follow-up.")
    parser.add_argument(
        "--refresh-root-control-plane",
        action="store_true",
        help="Run workspace_scan/workspace_plan_moves/workspace_verify after successful normalization.",
    )
    parser.add_argument(
        "--clone-if-missing",
        action="store_true",
        help="If the target path is missing, clone the remote into that path instead of failing.",
    )
    parser.add_argument("--receipt-out", help="Optional explicit path for the JSON receipt.")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    target = Path(args.target).expanduser().resolve()
    workspace_root = Path(args.workspace_root).expanduser().resolve() if args.workspace_root else None
    receipt_out = Path(args.receipt_out).expanduser().resolve() if args.receipt_out else None

    receipt = normalize_nested_repo(
        target=target,
        remote=args.remote,
        dry_run=args.dry_run,
        workspace_root=workspace_root,
        refresh_root_control_plane=args.refresh_root_control_plane,
        receipt_out=receipt_out,
        clone_if_missing=args.clone_if_missing,
    )

    print(json.dumps(receipt, indent=2))
    return 0 if receipt["status"] in {
        "already_normalized",
        "already_normalized_with_root_followup",
        "would_clone_missing_target",
        "cloned_missing_target",
        "cloned_missing_target_with_root_followup",
        "dry_run_match",
        "normalized",
        "normalized_with_root_followup",
    } else 1


if __name__ == "__main__":
    sys.exit(main())

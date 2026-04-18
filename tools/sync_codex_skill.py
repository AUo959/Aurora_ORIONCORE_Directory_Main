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
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SKILLS_ROOT = Path("~/.codex/skills").expanduser()
IGNORED_NAMES = {".DS_Store"}
IGNORED_DIR_NAMES = {"__pycache__", ".pytest_cache"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def should_skip_name(name: str, is_dir: bool) -> bool:
    if name in IGNORED_NAMES:
        return True
    if is_dir and name in IGNORED_DIR_NAMES:
        return True
    if not is_dir and Path(name).suffix in IGNORED_SUFFIXES:
        return True
    return False


def iter_skill_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for current_root, dirnames, filenames in os.walk(root):
        current = Path(current_root)
        dirnames[:] = [name for name in sorted(dirnames) if not should_skip_name(name, is_dir=True)]
        for filename in sorted(filenames):
            if should_skip_name(filename, is_dir=False):
                continue
            files.append(current / filename)
    return files


def collect_manifest(root: Path) -> dict[str, dict[str, Any]]:
    if not root.exists():
        return {}
    manifest: dict[str, dict[str, Any]] = {}
    for path in iter_skill_files(root):
        relative = path.relative_to(root).as_posix()
        manifest[relative] = {
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    return manifest


def ensure_skill_source(source: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Skill source does not exist: {source}")
    if not source.is_dir():
        raise NotADirectoryError(f"Skill source is not a directory: {source}")
    if not (source / "SKILL.md").exists():
        raise ValueError(f"Skill source is missing SKILL.md: {source}")


def build_sync_report(source: Path, destination: Path) -> dict[str, Any]:
    source_manifest = collect_manifest(source)
    destination_manifest = collect_manifest(destination)

    source_paths = set(source_manifest)
    destination_paths = set(destination_manifest)

    changed_paths = sorted(
        path
        for path in source_paths
        if destination_manifest.get(path) != source_manifest[path]
    )
    removed_paths = sorted(destination_paths - source_paths)

    return {
        "source": str(source),
        "destination": str(destination),
        "source_file_count": len(source_manifest),
        "destination_file_count": len(destination_manifest),
        "changed_paths": changed_paths,
        "removed_paths": removed_paths,
        "unchanged_file_count": len(source_paths & destination_paths) - len(source_paths & set(changed_paths)),
    }


def copy_skill_tree(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_root = Path(tempfile.mkdtemp(prefix=f"{destination.name}-sync-", dir=str(destination.parent)))
    staged = temp_root / destination.name
    try:
        shutil.copytree(
            source,
            staged,
            ignore=shutil.ignore_patterns(".DS_Store", "__pycache__", ".pytest_cache", "*.pyc", "*.pyo"),
        )
        if destination.exists():
            shutil.rmtree(destination)
        shutil.move(str(staged), str(destination))
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def sync_skill(source: Path, destination: Path, dry_run: bool = False) -> dict[str, Any]:
    ensure_skill_source(source)
    if source.resolve() == destination.resolve():
        raise ValueError("Source and destination must be different paths")

    report = build_sync_report(source, destination)
    has_changes = bool(report["changed_paths"] or report["removed_paths"])
    if not has_changes:
        report["status"] = "already_in_sync"
        return report

    if dry_run:
        report["status"] = "dry_run"
        return report

    copy_skill_tree(source, destination)
    report["status"] = "synced"
    report["post_sync_file_count"] = len(collect_manifest(destination))
    return report


def run_package_validation(skills_root: Path) -> dict[str, Any]:
    validator = skills_root / "aurora-skill-finder" / "scripts" / "validate_skill_package.py"
    if not validator.exists():
        return {
            "status": "skipped",
            "reason": f"validator not found at {validator}",
        }

    result = subprocess.run(
        [sys.executable, str(validator), "--skills-root", str(skills_root)],
        text=True,
        capture_output=True,
        check=False,
    )
    payload: dict[str, Any]
    try:
        payload = json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError:
        payload = {
            "status": "invalid_output",
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    payload["_returncode"] = result.returncode
    payload["_validator"] = str(validator)
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync a versioned Aurora repo skill into ~/.codex/skills.")
    parser.add_argument("--skill", required=True, help="Skill folder name under the repo-local skills/ directory.")
    parser.add_argument("--repo-root", default=str(ROOT), help="Root of the Aurora workspace repo.")
    parser.add_argument("--skills-root", default=str(DEFAULT_SKILLS_ROOT), help="Installed Codex skills root.")
    parser.add_argument("--dry-run", action="store_true", help="Report what would change without copying files.")
    parser.add_argument(
        "--validate-package",
        action="store_true",
        help="Run the installed-skill package validator after sync.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = Path(args.repo_root).expanduser().resolve()
    skills_root = Path(args.skills_root).expanduser().resolve()
    source = repo_root / "skills" / args.skill
    destination = skills_root / args.skill

    report = sync_skill(source, destination, dry_run=args.dry_run)
    if args.validate_package:
        report["validation"] = run_package_validation(skills_root)

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

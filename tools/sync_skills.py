#!/usr/bin/env python3
"""
sync_skills.py — Propagate project-owned skills from skills/ to every enabled
target in catalog/skill_sync_targets.yaml.

Usage:
    python3 tools/sync_skills.py                      # dry-run (print what would change)
    python3 tools/sync_skills.py --apply              # apply the sync to all enabled targets
    python3 tools/sync_skills.py --apply --skill gitwiz-github-manager
    python3 tools/sync_skills.py --apply --target codex
    python3 tools/sync_skills.py --check              # drift check: exit 2 if any enabled target drifted

Direction: skills/ (canonical source) → installed target directories.
This is one-way. Edit in skills/, then sync (the pre-push and post-merge hooks
do this automatically when skills/ changes).

After a full --apply, updates catalog/session_state.json →
platform_capabilities.<key>.skills per target so the capability map stays
current, and writes a receipt to reports/automation/skill_sync_latest.json.

Skills tracked in skills/ are project-owned (no LICENSE.txt). Platform-managed
skills (chatgpt-apps, doc, pdf, imagegen, etc.) are not managed here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_SRC = REPO_ROOT / "skills"
TARGETS_REGISTRY = REPO_ROOT / "catalog" / "skill_sync_targets.yaml"
RECEIPT_PATH = REPO_ROOT / "reports" / "automation" / "skill_sync_latest.json"

# Legacy fallback when the registry is absent.
DEFAULT_TARGETS = [
    {"name": "codex", "dest": "~/.codex/skills", "enabled": True, "capability_map_key": "codex"},
]

# Files/dirs to exclude when syncing (not project-owned content)
EXCLUDE_PATTERNS = {"__pycache__", "*.pyc", ".DS_Store", ".git"}


def load_targets() -> list[dict]:
    if not TARGETS_REGISTRY.exists():
        return [dict(t) for t in DEFAULT_TARGETS]
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    from _workspace_common import load_yaml_like

    payload = load_yaml_like(TARGETS_REGISTRY) or {}
    targets = payload.get("targets") or []
    return [t for t in targets if isinstance(t, dict) and t.get("name") and t.get("dest")]


def _should_exclude(path: Path) -> bool:
    for pat in EXCLUDE_PATTERNS:
        if pat.startswith("*"):
            if path.name.endswith(pat[1:]):
                return True
        elif path.name == pat:
            return True
    return False


def _file_hash(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def sync_skill(skill_name: str, dest_root: Path, dry_run: bool = True) -> dict:
    src = SKILLS_SRC / skill_name
    dst = dest_root / skill_name

    if not src.exists():
        return {"skill": skill_name, "status": "error", "reason": f"source not found: {src}"}

    changes = []

    for src_file in src.rglob("*"):
        if src_file.is_dir():
            continue
        if _should_exclude(src_file):
            continue

        rel = src_file.relative_to(src)
        dst_file = dst / rel

        if not dst_file.exists():
            changes.append(("add", rel))
            if not dry_run:
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dst_file)
        elif _file_hash(src_file) != _file_hash(dst_file):
            changes.append(("update", rel))
            if not dry_run:
                shutil.copy2(src_file, dst_file)

    if not changes:
        return {"skill": skill_name, "status": "up-to-date", "changes": []}

    return {
        "skill": skill_name,
        "status": "dry-run" if dry_run else "synced",
        "changes": [f"{op}: {path}" for op, path in changes],
    }


def collect_drift(targets: list[dict] | None = None, skills: list[str] | None = None) -> dict[str, list[str]]:
    """Return {target_name: [drift summaries]} for enabled targets, without writing."""
    drift: dict[str, list[str]] = {}
    for target in targets if targets is not None else load_targets():
        if not target.get("enabled"):
            continue
        dest_root = Path(str(target["dest"])).expanduser()
        names = skills or sorted(p.name for p in SKILLS_SRC.iterdir() if p.is_dir())
        entries: list[str] = []
        for skill_name in names:
            result = sync_skill(skill_name, dest_root, dry_run=True)
            if result.get("changes"):
                entries.append(f"{skill_name}: {len(result['changes'])} file(s)")
        if entries:
            drift[str(target["name"])] = entries
    return drift


def _write_receipt(target_results: dict[str, dict]) -> None:
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "skills/",
        "targets": target_results,
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n")


def sync_target(target: dict, skills: list[str], dry_run: bool, full_sync: bool) -> dict:
    """Sync every named skill into one target; print progress; return a result record."""
    dest_root = Path(str(target["dest"])).expanduser()
    print(f"→ target {target['name']} ({dest_root})")
    total_changes = 0
    errors = 0
    changed_skills: dict[str, list[str]] = {}
    for skill_name in skills:
        result = sync_skill(skill_name, dest_root, dry_run=dry_run)
        status = result["status"]
        changes = result.get("changes", [])

        if status == "error":
            print(f"  ❌ {skill_name}: {result.get('reason', '')}")
            errors += 1
        elif status == "up-to-date":
            print(f"  ✅ {skill_name}: up-to-date")
        else:
            icon = "🔍" if dry_run else "🔄"
            print(f"  {icon} {skill_name}: {len(changes)} change(s)")
            for change in changes:
                print(f"       {change}")
            total_changes += len(changes)
            changed_skills[skill_name] = changes
    if not dry_run and full_sync:
        _update_capability_map(target.get("capability_map_key"))
    return {
        "dest": str(dest_root),
        "files_changed": total_changes,
        "skills_changed": changed_skills,
        "errors": errors,
    }


def run_check(targets: list[dict], skill: str | None) -> int:
    """Print drift for the enabled targets; exit 0 when clean, 2 when drifted."""
    drift = collect_drift(targets, [skill] if skill else None)
    if not drift:
        print("All enabled skill-sync targets are up-to-date.")
        return 0
    for name, entries in drift.items():
        print(f"DRIFT {name}:")
        for entry in entries:
            print(f"  - {entry}")
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry-run)")
    parser.add_argument("--skill", help="Sync a single skill by name")
    parser.add_argument("--target", help="Sync a single target by registry name")
    parser.add_argument("--check", action="store_true", help="Drift check only: exit 2 if any enabled target drifted")
    args = parser.parse_args()

    targets = [t for t in load_targets() if t.get("enabled")]
    if args.target:
        targets = [t for t in targets if t["name"] == args.target]
        if not targets:
            print(f"No enabled target named {args.target!r} in {TARGETS_REGISTRY.name}.")
            return 1

    if args.check:
        return run_check(targets, args.skill)

    dry_run = not args.apply
    if dry_run:
        print("DRY RUN — pass --apply to write changes\n")

    skills = [args.skill] if args.skill else sorted(p.name for p in SKILLS_SRC.iterdir() if p.is_dir())

    grand_total = 0
    errors = 0
    target_results: dict[str, dict] = {}

    for target in targets:
        result = sync_target(target, skills, dry_run, full_sync=not args.skill)
        grand_total += result["files_changed"]
        errors += result.pop("errors")
        target_results[target["name"]] = result

    print()
    if dry_run:
        print(f"Would apply {grand_total} change(s) across {len(skills)} skill(s) and {len(targets)} target(s).")
        if grand_total:
            print("Run with --apply to install.")
    else:
        print(f"Synced {grand_total} file(s) across {len(skills)} skill(s) and {len(targets)} target(s).")
        if not args.skill:
            _write_receipt(target_results)

    return 1 if errors else 0


def _update_capability_map(capability_key: str | None) -> None:
    """Update platform_capabilities.<key>.skills in session_state.json with current skills/ list."""
    if not capability_key:
        return
    state_path = REPO_ROOT / "catalog" / "session_state.json"
    if not state_path.exists():
        return
    try:
        state = json.loads(state_path.read_text())
    except Exception:
        return

    current_skills = sorted(
        p.name for p in SKILLS_SRC.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    )

    caps = state.setdefault("platform_capabilities", {})
    platform = caps.setdefault(capability_key, {})
    old_skills = platform.get("skills", [])

    if old_skills == current_skills:
        return  # nothing to update

    platform["skills"] = current_skills
    state_path.write_text(json.dumps(state, indent=2) + "\n")
    added = [s for s in current_skills if s not in old_skills]
    removed = [s for s in old_skills if s not in current_skills]
    changes = []
    if added:
        changes.append(f"+{len(added)} added")
    if removed:
        changes.append(f"-{len(removed)} removed")
    print(f"  📋 capability map [{capability_key}] updated ({', '.join(changes) or 'reordered'}): {len(current_skills)} skills")


if __name__ == "__main__":
    sys.exit(main())

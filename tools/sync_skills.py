#!/usr/bin/env python3
"""
sync_skills.py — Push project-owned skills from skills/ to ~/.codex/skills/

Usage:
    python3 tools/sync_skills.py              # dry-run (print what would change)
    python3 tools/sync_skills.py --apply      # apply the sync
    python3 tools/sync_skills.py --apply --skill gitwiz-github-manager  # single skill

Direction: skills/ (canonical source) → ~/.codex/skills/ (installed)
This is one-way. Edit in skills/, then run this to install.

After --apply, also updates catalog/session_state.json → platform_capabilities.codex.skills
with the current skill list so the capability map stays current automatically.

Skills tracked in skills/ are project-owned (no LICENSE.txt). OpenAI-maintained
skills (chatgpt-apps, doc, pdf, imagegen, etc.) are not managed here.
"""

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_SRC = REPO_ROOT / "skills"
SKILLS_DST = Path.home() / ".codex" / "skills"

# Files/dirs to exclude when syncing (not project-owned content)
EXCLUDE_PATTERNS = {"__pycache__", "*.pyc", ".DS_Store", ".git"}


def _should_exclude(path: Path) -> bool:
    for pat in EXCLUDE_PATTERNS:
        if pat.startswith("*"):
            if path.name.endswith(pat[1:]):
                return True
        elif path.name == pat:
            return True
    return False


def _file_hash(p: Path) -> str:
    h = hashlib.md5()
    h.update(p.read_bytes())
    return h.hexdigest()


def sync_skill(skill_name: str, dry_run: bool = True) -> dict:
    src = SKILLS_SRC / skill_name
    dst = SKILLS_DST / skill_name

    if not src.exists():
        return {"skill": skill_name, "status": "error", "reason": f"source not found: {src}"}

    changes = []

    # Walk source and sync each file
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="Apply changes (default is dry-run)")
    parser.add_argument("--skill", help="Sync a single skill by name")
    args = parser.parse_args()

    dry_run = not args.apply

    if dry_run:
        print("DRY RUN — pass --apply to write changes\n")

    if args.skill:
        skills = [args.skill]
    else:
        skills = sorted(p.name for p in SKILLS_SRC.iterdir() if p.is_dir())

    total_changes = 0
    errors = 0

    for skill_name in skills:
        result = sync_skill(skill_name, dry_run=dry_run)
        status = result["status"]
        changes = result.get("changes", [])
        reason = result.get("reason", "")

        if status == "error":
            print(f"  ❌ {skill_name}: {reason}")
            errors += 1
        elif status == "up-to-date":
            print(f"  ✅ {skill_name}: up-to-date")
        else:
            icon = "🔍" if dry_run else "🔄"
            print(f"  {icon} {skill_name}: {len(changes)} change(s)")
            for change in changes:
                print(f"       {change}")
            total_changes += len(changes)

    print()
    if dry_run:
        print(f"Would apply {total_changes} change(s) across {len(skills)} skill(s).")
        if total_changes:
            print("Run with --apply to install.")
    else:
        print(f"Synced {total_changes} file(s) across {len(skills)} skill(s).")
        if not args.skill:  # only update map on full sync
            _update_capability_map()

    return 1 if errors else 0


def _update_capability_map() -> None:
    """Update platform_capabilities.codex.skills in session_state.json with current skills/ list."""
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
    codex = caps.setdefault("codex", {})
    old_skills = codex.get("skills", [])

    if old_skills == current_skills:
        return  # nothing to update

    codex["skills"] = current_skills
    state_path.write_text(json.dumps(state, indent=2) + "\n")
    added = [s for s in current_skills if s not in old_skills]
    removed = [s for s in old_skills if s not in current_skills]
    changes = []
    if added:
        changes.append(f"+{len(added)} added")
    if removed:
        changes.append(f"-{len(removed)} removed")
    print(f"  📋 capability map updated ({', '.join(changes) or 'reordered'}): {len(current_skills)} skills")


if __name__ == "__main__":
    sys.exit(main())

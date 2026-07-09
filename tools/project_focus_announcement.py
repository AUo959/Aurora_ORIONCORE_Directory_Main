#!/usr/bin/env python3
"""Surface tracked Aurora project-focus announcements.

The registry is versioned under catalog/ so startup hooks, already-running
sessions, and Mission Control can read the same focus guidance without writing
to catalog/session_state.json or local session-claim files.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _workspace_common import now_iso_utc, serialized_root


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "catalog" / "project_focus_announcements.json"
VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}


def parse_time(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def load_registry(path: Path) -> tuple[dict[str, Any], str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"schema_version": 1, "announcements": []}, f"missing registry: {path}"
    except json.JSONDecodeError as exc:
        return {"schema_version": 1, "announcements": []}, f"invalid registry JSON: {exc.msg}"
    except OSError as exc:
        return {"schema_version": 1, "announcements": []}, f"unreadable registry: {exc}"
    if not isinstance(payload, dict):
        return {"schema_version": 1, "announcements": []}, "registry root must be a JSON object"
    return payload, None


def is_active(item: dict[str, Any], now: datetime) -> bool:
    if str(item.get("status", "")).lower() != "active":
        return False
    effective_at = parse_time(item.get("effective_at"))
    expires_at = parse_time(item.get("expires_at"))
    if effective_at and effective_at > now:
        return False
    if expires_at and expires_at <= now:
        return False
    return True


def normalize_announcement(item: dict[str, Any], *, now: datetime) -> dict[str, Any]:
    priority = str(item.get("priority", "P2")).upper()
    if priority not in VALID_PRIORITIES:
        priority = "P2"
    guidance = item.get("guidance", [])
    evidence_refs = item.get("evidence_refs", [])
    suggested_commands = item.get("suggested_commands", [])
    normalized = {
        "id": str(item.get("id", "unnamed-announcement")),
        "status": str(item.get("status", "inactive")),
        "active": is_active(item, now),
        "priority": priority,
        "title": str(item.get("title", "Untitled project focus")),
        "summary": str(item.get("summary", "")),
        "agent_expectation": str(item.get("agent_expectation", "")),
        "guidance": [str(entry) for entry in guidance if str(entry).strip()],
        "target_repo": str(item.get("target_repo", "root")),
        "owner_surface": str(item.get("owner_surface", "root control-plane repo")),
        "evidence_refs": [str(ref) for ref in evidence_refs if str(ref).strip()],
        "suggested_commands": [str(command) for command in suggested_commands if str(command).strip()],
        "effective_at": item.get("effective_at"),
        "expires_at": item.get("expires_at"),
        "mutation_posture": str(item.get("mutation_posture", "advisory_only")),
    }
    return normalized


def registry_relative_path(root: Path, registry_path: Path) -> str:
    resolved_root = root.resolve()
    resolved_registry = registry_path.resolve()
    if resolved_registry.is_relative_to(resolved_root):
        return resolved_registry.relative_to(resolved_root).as_posix()
    return str(resolved_registry)


def build_report(
    root: Path,
    registry_path: Path | None = None,
    *,
    include_inactive: bool = False,
    generated_at: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    checked_at = now or utc_now()
    registry = registry_path or root / "catalog" / "project_focus_announcements.json"
    payload, error = load_registry(registry)
    raw_announcements = payload.get("announcements", [])
    if not isinstance(raw_announcements, list):
        raw_announcements = []
        error = error or "announcements must be a list"

    normalized = [
        normalize_announcement(item, now=checked_at)
        for item in raw_announcements
        if isinstance(item, dict)
    ]
    announcements = [
        item for item in normalized
        if include_inactive or item["active"]
    ]
    active_count = sum(1 for item in normalized if item["active"])
    status = "attention" if error else ("active" if active_count else "quiet")
    report = {
        "schema_version": 1,
        "generated_at": generated_at or now_iso_utc(),
        "root": serialized_root(root),
        "tool": "project_focus_announcement",
        "run_mode": "read_only",
        "mutation_posture": "advisory_only",
        "nested_repo_mutation": False,
        "registry_path": registry_relative_path(root, registry),
        "status": status,
        "summary": {
            "announcement_count": len(normalized),
            "active_count": active_count,
            "included_count": len(announcements),
        },
        "announcements": announcements,
    }
    if error:
        report["error"] = error
    return report


def format_summary(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        f"Aurora Project Focus: {report['status']}",
        f"- Active announcements: {summary['active_count']} of {summary['announcement_count']}",
    ]
    if report.get("error"):
        lines.append(f"- Registry issue: {report['error']}")
    if not report["announcements"]:
        lines.append("- No active project-focus announcements.")
        return "\n".join(lines)

    for item in report["announcements"]:
        lines.append(f"- [{item['priority']}] {item['title']}")
        if item["summary"]:
            lines.append(f"  {item['summary']}")
        if item["agent_expectation"]:
            lines.append(f"  Agent expectation: {item['agent_expectation']}")
        if item["guidance"]:
            lines.append(f"  Proposal guidance: {item['guidance'][0]}")
        if item["suggested_commands"]:
            lines.append(f"  Commands: {'; '.join(item['suggested_commands'][:3])}")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Surface Aurora project-focus announcements.")
    parser.add_argument("--root", default=str(ROOT), help="Aurora root workspace path.")
    parser.add_argument("--registry", help="Announcement registry path. Defaults to catalog/project_focus_announcements.json.")
    parser.add_argument("--include-inactive", action="store_true", help="Include inactive and expired announcements in output.")
    parser.add_argument("--summary", action="store_true", help="Print compact text instead of JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    registry = Path(args.registry).expanduser().resolve() if args.registry else root / "catalog" / "project_focus_announcements.json"
    report = build_report(root, registry, include_inactive=args.include_inactive)
    if args.summary:
        print(format_summary(report))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] != "attention" else 1


if __name__ == "__main__":
    raise SystemExit(main())

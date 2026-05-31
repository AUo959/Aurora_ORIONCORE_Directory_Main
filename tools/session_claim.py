#!/usr/bin/env python3
"""Coordinate concurrent Codex and Claude Code work with local session claims.

## Claim scope and distributed extension

Claims currently use scope="local" — they are machine-local JSON files in
catalog/session_claims/ (gitignored, visible only on this machine).

To support multi-machine / multi-user operation in the future, change the
CLAIM_BACKEND_URL environment variable:

    CLAIM_BACKEND_URL=local://           # default: file system (current)
    CLAIM_BACKEND_URL=redis://host:6379  # future: Redis TTL keys
    CLAIM_BACKEND_URL=github://owner/repo # future: GitHub Issues as claims

The claim schema includes scope and machine_id so that remote-scope claims
carry enough context to identify their origin without changing the format.
Each claim backend must implement read_claims() and write_claim() over the
same JSON payload. No backend-specific code lives here yet — the extension
point is the CLAIM_BACKEND_URL env var and the scope field in the payload.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from _workspace_common import git, write_json


CLAIM_SCHEMA_VERSION = 2  # v2 adds scope and machine_id
DEFAULT_CLAIMS_RELATIVE_DIR = Path("catalog") / "session_claims"
DEFAULT_TTL_MINUTES = 180
NON_MUTATING_POSTURES = {"read_only", "planning", "advisory_only"}
CLAIM_BACKEND_URL = os.environ.get("CLAIM_BACKEND_URL", "local://")
MACHINE_ID_PATH = Path.home() / ".codex" / ".machine_id"


def _get_machine_id() -> str:
    """Return a stable per-machine UUID. Created on first call, persisted."""
    if MACHINE_ID_PATH.exists():
        mid = MACHINE_ID_PATH.read_text().strip()
        if mid:
            return mid
    mid = str(uuid.uuid4())
    MACHINE_ID_PATH.parent.mkdir(parents=True, exist_ok=True)
    MACHINE_ID_PATH.write_text(mid + "\n")
    return mid


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def format_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slug(value: str) -> str:
    lowered = value.strip().lower()
    cleaned = re.sub(r"[^a-z0-9._-]+", "-", lowered).strip("-._")
    return cleaned or "claim"


def claims_dir(root: Path, claims_relative_dir: Path = DEFAULT_CLAIMS_RELATIVE_DIR) -> Path:
    return root / claims_relative_dir


def normalize_repo(value: str) -> str:
    return value.strip() or "root"


def normalize_path(raw_path: str, root: Path) -> str:
    raw = raw_path.strip()
    if raw in {"", "."}:
        return "."

    root_resolved = root.resolve()
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = root_resolved / candidate
    resolved = candidate.resolve(strict=False)
    try:
        relative = resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"Path is outside the workspace root: {raw_path}") from exc

    normalized = relative.as_posix()
    return normalized or "."


def normalize_paths(raw_paths: list[str], root: Path) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw_path in raw_paths:
        normalized = normalize_path(raw_path, root)
        if normalized not in seen:
            seen.add(normalized)
            out.append(normalized)
    return out


def path_overlaps(left: str, right: str) -> bool:
    if left == "." or right == ".":
        return True
    return left == right or left.startswith(f"{right}/") or right.startswith(f"{left}/")


def posture_is_mutating(value: str) -> bool:
    return value not in NON_MUTATING_POSTURES


def claim_path_for(root: Path, claim_id: str) -> Path:
    return claims_dir(root) / f"{claim_id}.json"


def load_claim_file(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "path": path,
            "valid": False,
            "error": str(exc),
            "claim": None,
        }
    if not isinstance(payload, dict):
        return {
            "path": path,
            "valid": False,
            "error": "claim file must contain a JSON object",
            "claim": None,
        }
    return {
        "path": path,
        "valid": True,
        "error": None,
        "claim": payload,
    }


def load_claim_records(root: Path) -> list[dict[str, Any]]:
    directory = claims_dir(root)
    if not directory.exists():
        return []
    return [load_claim_file(path) for path in sorted(directory.glob("*.json"))]


def is_active_claim(claim: dict[str, Any], now: datetime) -> bool:
    if claim.get("status") != "active":
        return False
    expires_at = parse_time(str(claim.get("expires_at", "")))
    return expires_at is None or expires_at > now


def is_stale_claim(claim: dict[str, Any], now: datetime) -> bool:
    if claim.get("status") != "active":
        return False
    expires_at = parse_time(str(claim.get("expires_at", "")))
    return expires_at is not None and expires_at <= now


def claim_summary(record: dict[str, Any], root: Path, now: datetime) -> dict[str, Any]:
    path = record["path"]
    rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)
    if not record["valid"]:
        return {
            "claim_file": rel,
            "valid": False,
            "status": "invalid",
            "error": record["error"],
        }

    claim = record["claim"]
    status = str(claim.get("status", "unknown"))
    if is_stale_claim(claim, now):
        status = "stale"
    return {
        "claim_file": rel,
        "valid": True,
        "status": status,
        "claim_id": claim.get("claim_id"),
        "platform": claim.get("platform"),
        "task_id": claim.get("task_id"),
        "repo": claim.get("repo"),
        "branch": claim.get("branch"),
        "mutation_posture": claim.get("mutation_posture"),
        "paths": claim.get("paths", []),
        "updated_at": claim.get("updated_at"),
        "expires_at": claim.get("expires_at"),
    }


def check_claims(
    *,
    root: Path,
    repo: str,
    paths: list[str],
    mutation_posture: str = "editing",
    exclude_claim_id: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    checked_at = now or utc_now()
    normalized_repo = normalize_repo(repo)
    normalized_paths = normalize_paths(paths or ["."], root)
    incoming_mutates = posture_is_mutating(mutation_posture)

    conflicts: list[dict[str, Any]] = []
    stale: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    active: list[dict[str, Any]] = []

    for record in load_claim_records(root):
        summary = claim_summary(record, root, checked_at)
        if not record["valid"]:
            invalid.append(summary)
            continue

        claim = record["claim"]
        if claim.get("claim_id") == exclude_claim_id:
            continue
        if normalize_repo(str(claim.get("repo", "root"))) != normalized_repo:
            continue

        if is_stale_claim(claim, checked_at):
            stale.append(summary)
            continue
        if not is_active_claim(claim, checked_at):
            continue

        active.append(summary)
        existing_paths = [str(path) for path in claim.get("paths", [])]
        existing_mutates = posture_is_mutating(str(claim.get("mutation_posture", "editing")))
        if not incoming_mutates or not existing_mutates:
            continue

        overlapping_paths = [
            {"requested": requested, "claimed": claimed}
            for requested in normalized_paths
            for claimed in existing_paths
            if path_overlaps(requested, claimed)
        ]
        if overlapping_paths:
            conflicts.append(
                {
                    "claim_id": claim.get("claim_id"),
                    "platform": claim.get("platform"),
                    "task_id": claim.get("task_id"),
                    "branch": claim.get("branch"),
                    "mutation_posture": claim.get("mutation_posture"),
                    "expires_at": claim.get("expires_at"),
                    "overlapping_paths": overlapping_paths,
                }
            )

    return {
        "schema_version": CLAIM_SCHEMA_VERSION,
        "checked_at": format_time(checked_at),
        "root": ".",
        "repo": normalized_repo,
        "paths": normalized_paths,
        "mutation_posture": mutation_posture,
        "status": "conflict" if conflicts else "clear",
        "conflicts": conflicts,
        "active_claims": active,
        "stale_claims": stale,
        "invalid_claims": invalid,
    }


def next_claim_id(root: Path, platform: str, task_id: str, now: datetime) -> str:
    base = f"{slug(platform)}-{now.strftime('%Y%m%dT%H%M%SZ')}-{slug(task_id)}"
    candidate = base
    index = 2
    while claim_path_for(root, candidate).exists():
        candidate = f"{base}-{index}"
        index += 1
    return candidate


def current_branch(root: Path) -> str:
    result = git(
        ["branch", "--show-current"],
        cwd=root,
        check=False,
    )
    return result.stdout.strip() or "detached"


def create_claim(
    *,
    root: Path,
    platform: str,
    task_id: str,
    repo: str,
    paths: list[str],
    mutation_posture: str,
    ttl_minutes: int,
    claim_id: str | None = None,
    session_label: str = "",
    notes: str = "",
    allow_conflict: bool = False,
    now: datetime | None = None,
) -> tuple[int, dict[str, Any]]:
    created_at = now or utc_now()
    normalized_paths = normalize_paths(paths, root)
    if not normalized_paths:
        return 1, {"status": "error", "error": "At least one path claim is required."}

    check = check_claims(
        root=root,
        repo=repo,
        paths=normalized_paths,
        mutation_posture=mutation_posture,
        now=created_at,
    )
    if check["conflicts"] and not allow_conflict:
        return 2, check

    normalized_claim_id = claim_id or next_claim_id(root, platform, task_id, created_at)
    expires_at = created_at + timedelta(minutes=ttl_minutes)
    payload = {
        "schema_version": CLAIM_SCHEMA_VERSION,
        "claim_id": normalized_claim_id,
        "status": "active",
        # --- origin ---
        "platform": platform,
        "machine_id": _get_machine_id(),   # stable UUID per machine
        "host": socket.gethostname(),       # human-readable hostname
        "scope": "local",                   # "local" | "remote" (see module docstring)
        # --- task ---
        "session_label": session_label,
        "task_id": task_id,
        "repo": normalize_repo(repo),
        "branch": current_branch(root),
        "worktree": str(root.resolve()),
        "mutation_posture": mutation_posture,
        "paths": normalized_paths,
        # --- timing ---
        "started_at": format_time(created_at),
        "updated_at": format_time(created_at),
        "expires_at": format_time(expires_at),
        "ttl_minutes": ttl_minutes,
        "notes": notes,
    }
    path = claim_path_for(root, normalized_claim_id)
    write_json(path, payload)
    return 0, {"status": "created", "claim_file": path.relative_to(root).as_posix(), "claim": payload}


def find_claim(root: Path, claim_id: str) -> tuple[Path | None, dict[str, Any] | None]:
    path = claim_path_for(root, claim_id)
    if not path.exists():
        return None, None
    record = load_claim_file(path)
    return path, record["claim"] if record["valid"] else None


def release_claim(root: Path, claim_id: str, now: datetime | None = None) -> tuple[int, dict[str, Any]]:
    path, claim = find_claim(root, claim_id)
    if path is None or claim is None:
        return 1, {"status": "error", "error": f"Claim not found: {claim_id}"}
    released_at = now or utc_now()
    claim["status"] = "released"
    claim["updated_at"] = format_time(released_at)
    claim["released_at"] = format_time(released_at)
    write_json(path, claim)
    return 0, {"status": "released", "claim_file": path.relative_to(root).as_posix(), "claim": claim}


def refresh_claim(root: Path, claim_id: str, ttl_minutes: int, now: datetime | None = None) -> tuple[int, dict[str, Any]]:
    path, claim = find_claim(root, claim_id)
    if path is None or claim is None:
        return 1, {"status": "error", "error": f"Claim not found: {claim_id}"}
    refreshed_at = now or utc_now()
    claim["status"] = "active"
    claim["updated_at"] = format_time(refreshed_at)
    claim["expires_at"] = format_time(refreshed_at + timedelta(minutes=ttl_minutes))
    claim["ttl_minutes"] = ttl_minutes
    write_json(path, claim)
    return 0, {"status": "refreshed", "claim_file": path.relative_to(root).as_posix(), "claim": claim}


def list_claims(root: Path, now: datetime | None = None) -> dict[str, Any]:
    listed_at = now or utc_now()
    claims = [claim_summary(record, root, listed_at) for record in load_claim_records(root)]
    return {
        "schema_version": CLAIM_SCHEMA_VERSION,
        "listed_at": format_time(listed_at),
        "root": ".",
        "claims": claims,
        "summary": {
            "total": len(claims),
            "active": sum(1 for claim in claims if claim.get("status") == "active"),
            "stale": sum(1 for claim in claims if claim.get("status") == "stale"),
            "invalid": sum(1 for claim in claims if claim.get("status") == "invalid"),
        },
    }


def print_human(payload: dict[str, Any]) -> None:
    status = payload.get("status")
    if status in {"created", "released", "refreshed"}:
        claim = payload.get("claim", {})
        print(f"{status}: {claim.get('claim_id')} ({payload.get('claim_file')})")
        return
    if "claims" in payload:
        summary = payload.get("summary", {})
        print(
            "claims: "
            f"{summary.get('active', 0)} active, "
            f"{summary.get('stale', 0)} stale, "
            f"{summary.get('invalid', 0)} invalid"
        )
        for claim in payload["claims"]:
            print(
                f"- {claim.get('claim_id', claim.get('claim_file'))}: "
                f"{claim.get('status')} {claim.get('repo', '')} {claim.get('paths', [])}"
            )
        return
    if status == "conflict":
        print("session claim conflict")
        for conflict in payload.get("conflicts", []):
            print(f"- {conflict.get('claim_id')} by {conflict.get('platform')}: {conflict.get('overlapping_paths')}")
        return
    if status == "clear":
        print("session claim check: clear")
        stale_count = len(payload.get("stale_claims", []))
        invalid_count = len(payload.get("invalid_claims", []))
        if stale_count or invalid_count:
            print(f"non-blocking: {stale_count} stale, {invalid_count} invalid claim file(s)")
        return
    print(json.dumps(payload, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Workspace root. Defaults to current directory.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Create an active local session claim.")
    create.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    create.add_argument("--platform", required=True, help="Platform name, such as codex or claude-code.")
    create.add_argument("--task-id", required=True, help="Task or workflow identifier.")
    create.add_argument("--repo", default="root", help="Repo boundary this claim protects.")
    create.add_argument("--paths", nargs="+", required=True, help="Workspace-relative paths being worked on.")
    create.add_argument("--mutation-posture", default="editing", help="read_only, planning, editing, committing, or publishing.")
    create.add_argument("--ttl-minutes", type=int, default=DEFAULT_TTL_MINUTES, help="Minutes until the claim is stale.")
    create.add_argument("--claim-id", help="Optional explicit claim id.")
    create.add_argument("--session-label", default="", help="Optional human session label.")
    create.add_argument("--notes", default="", help="Optional short note.")
    create.add_argument("--allow-conflict", action="store_true", help="Create even if overlapping active claims exist.")

    check = subparsers.add_parser("check", help="Check intended paths against active local claims.")
    check.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    check.add_argument("--repo", default="root", help="Repo boundary to check.")
    check.add_argument("--paths", nargs="*", default=["."], help="Workspace-relative paths to check. Defaults to whole repo.")
    check.add_argument("--mutation-posture", default="editing", help="Incoming operation posture.")
    check.add_argument("--claim-id", help="Claim id to exclude from conflict checks.")

    release = subparsers.add_parser("release", help="Release a local session claim.")
    release.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    release.add_argument("--claim-id", required=True, help="Claim id to release.")

    refresh = subparsers.add_parser("refresh", help="Refresh a local session claim TTL.")
    refresh.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    refresh.add_argument("--claim-id", required=True, help="Claim id to refresh.")
    refresh.add_argument("--ttl-minutes", type=int, default=DEFAULT_TTL_MINUTES, help="New TTL in minutes.")

    list_parser = subparsers.add_parser("list", help="List local session claims.")
    list_parser.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).expanduser().resolve()

    try:
        if args.command == "create":
            returncode, payload = create_claim(
                root=root,
                platform=args.platform,
                task_id=args.task_id,
                repo=args.repo,
                paths=args.paths,
                mutation_posture=args.mutation_posture,
                ttl_minutes=args.ttl_minutes,
                claim_id=args.claim_id,
                session_label=args.session_label,
                notes=args.notes,
                allow_conflict=args.allow_conflict,
            )
        elif args.command == "check":
            payload = check_claims(
                root=root,
                repo=args.repo,
                paths=args.paths,
                mutation_posture=args.mutation_posture,
                exclude_claim_id=args.claim_id,
            )
            returncode = 2 if payload["conflicts"] else 0
        elif args.command == "release":
            returncode, payload = release_claim(root, args.claim_id)
        elif args.command == "refresh":
            returncode, payload = refresh_claim(root, args.claim_id, args.ttl_minutes)
        elif args.command == "list":
            payload = list_claims(root)
            returncode = 0
        else:
            return 1
    except ValueError as exc:
        payload = {"status": "error", "error": str(exc)}
        returncode = 1

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_human(payload)
    return returncode


if __name__ == "__main__":
    sys.exit(main())

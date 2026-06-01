#!/usr/bin/env python3
"""Plan and claim Aurora CloudBank issue work before either agent edits files.

The broker is a root-control-plane coordination surface. It does not mutate the
CloudBank nested repo, create branches, post GitHub comments, or close issues.
It converts "resolve CloudBank issues" into an explicit local claim decision
using root session claims plus local CloudBank worktree evidence.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from _workspace_common import git, load_yaml_like
import session_claim


BROKER_SCHEMA_VERSION = 1
CLOUDBANK_REPO_NAME = "aurora-cloudbank-symbolic-main"
DEFAULT_REPO_REGISTRY = Path("catalog") / "repo_registry.yaml"
DEFAULT_WORKTREE_PARENT = Path("/private/tmp")
ISSUE_PATTERN = re.compile(r"(?:#|issue[-_/]?|issues[-_/]?)(\d+)", re.IGNORECASE)
CLAIM_TASK_PATTERN = re.compile(r"^cloudbank-issue-(\d+)(?:$|[-_])", re.IGNORECASE)


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def format_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slug(value: str) -> str:
    lowered = value.strip().lower()
    cleaned = re.sub(r"[^a-z0-9._-]+", "-", lowered).strip("-._")
    return cleaned or "cloudbank"


def issue_number(value: str | int) -> int:
    text = str(value).strip().lstrip("#")
    if not re.fullmatch(r"\d+", text):
        raise ValueError(f"Issue must be numeric: {value!r}")
    return int(text)


def issue_from_text(value: str | None) -> int | None:
    if not value:
        return None
    match = ISSUE_PATTERN.search(value)
    return int(match.group(1)) if match else None


def issue_from_task_id(value: str | None) -> int | None:
    if not value:
        return None
    match = CLAIM_TASK_PATTERN.match(value)
    return int(match.group(1)) if match else issue_from_text(value)


def platform_branch_prefix(platform: str) -> str:
    normalized = slug(platform)
    if normalized.startswith("claude"):
        return "claude"
    if normalized.startswith("codex"):
        return "codex"
    return normalized


def branch_for_issue(platform: str, issue: int, label: str = "") -> str:
    suffix = slug(label) if label else "work"
    return f"{platform_branch_prefix(platform)}/cloudbank-issue-{issue}-{suffix}"


def worktree_for_issue(platform: str, issue: int, label: str = "", parent: Path = DEFAULT_WORKTREE_PARENT) -> Path:
    suffix = slug(label) if label else "work"
    return parent / f"cloudbank-{platform_branch_prefix(platform)}-issue-{issue}-{suffix}"


def load_cloudbank_repo(root: Path, registry_path: Path | None = None) -> dict[str, Any]:
    path = registry_path or root / DEFAULT_REPO_REGISTRY
    payload = load_yaml_like(path)
    repos = payload.get("repos", []) if isinstance(payload, dict) else []
    for repo in repos:
        if isinstance(repo, dict) and repo.get("name") == CLOUDBANK_REPO_NAME:
            repo_path = str(repo.get("path", "")).strip()
            if not repo_path:
                raise ValueError(f"{CLOUDBANK_REPO_NAME} has no path in {path}")
            return {
                "name": CLOUDBANK_REPO_NAME,
                "path": repo_path,
                "branch": repo.get("branch"),
                "head_sha": repo.get("head_sha"),
                "remote_status": repo.get("remote_status"),
                "validation_command": repo.get("validation_command"),
                "registry_path": path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path),
            }
    raise ValueError(f"{CLOUDBANK_REPO_NAME} not found in {path}")


def reject_parent_traversal(parts: tuple[str, ...], raw_path: str) -> None:
    if any(part in {"..", ""} for part in parts):
        raise ValueError(f"Unsafe CloudBank path: {raw_path!r}")


def normalize_cloudbank_path(raw_path: str, *, root: Path, repo_rel: str) -> str:
    raw = raw_path.strip()
    if not raw or raw == ".":
        return repo_rel

    root_resolved = root.resolve()
    repo_rel_posix = PurePosixPath(repo_rel).as_posix()
    repo_abs = (root_resolved / repo_rel_posix).resolve(strict=False)
    candidate = Path(raw).expanduser()

    if candidate.is_absolute():
        resolved = candidate.resolve(strict=False)
        try:
            relative = resolved.relative_to(root_resolved).as_posix()
        except ValueError as exc:
            raise ValueError(f"Path is outside the Aurora workspace: {raw_path}") from exc
        try:
            resolved.relative_to(repo_abs)
        except ValueError as exc:
            raise ValueError(f"Path is outside the CloudBank repo: {raw_path}") from exc
        return relative

    posix = PurePosixPath(raw.replace("\\", "/")).as_posix()
    parts = PurePosixPath(posix).parts
    reject_parent_traversal(parts, raw_path)

    if posix.startswith("./"):
        posix = posix[2:]
    if posix == repo_rel_posix or posix.startswith(f"{repo_rel_posix}/"):
        return posix
    return f"{repo_rel_posix}/{posix}"


def normalize_cloudbank_paths(paths: list[str], *, root: Path, repo_rel: str) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for path in paths:
        root_relative = normalize_cloudbank_path(path, root=root, repo_rel=repo_rel)
        if root_relative not in seen:
            seen.add(root_relative)
            normalized.append(root_relative)
    return normalized


def git_status(root: Path, repo_rel: str) -> dict[str, Any]:
    repo_path = root / repo_rel
    if not repo_path.exists():
        return {
            "exists": False,
            "status": "missing",
            "branch": None,
            "head_sha": None,
            "dirty": None,
            "dirty_paths": [],
            "error": "CloudBank repo path is absent in this workspace.",
        }

    result = git(["status", "--short", "--branch"], cwd=repo_path, check=False)
    head = git(["rev-parse", "HEAD"], cwd=repo_path, check=False)
    branch_line = result.stdout.splitlines()[0] if result.stdout else ""
    dirty_lines = [line for line in result.stdout.splitlines()[1:] if line.strip()]
    return {
        "exists": True,
        "status": "ok" if result.returncode == 0 else "error",
        "branch": branch_line.removeprefix("## ").strip() or None,
        "head_sha": head.stdout.strip() if head.returncode == 0 else None,
        "dirty": bool(dirty_lines) if result.returncode == 0 else None,
        "dirty_paths": dirty_lines,
        "error": result.stderr.strip() if result.returncode != 0 else None,
    }


def parse_worktree_porcelain(output: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for line in output.splitlines():
        if not line.strip():
            if current:
                records.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            if current:
                records.append(current)
            current = {"path": value}
        elif key == "HEAD":
            current["head_sha"] = value
        elif key == "branch":
            current["branch"] = value.removeprefix("refs/heads/")
        elif key in {"detached", "bare"}:
            current[key] = True
    if current:
        records.append(current)
    return records


def collect_worktrees(root: Path, repo_rel: str) -> list[dict[str, Any]]:
    repo_path = root / repo_rel
    if not repo_path.exists():
        return []
    result = git(["worktree", "list", "--porcelain"], cwd=repo_path, check=False)
    if result.returncode != 0:
        return [
            {
                "status": "error",
                "error": result.stderr.strip() or result.stdout.strip(),
            }
        ]

    records = []
    for item in parse_worktree_porcelain(result.stdout):
        branch = item.get("branch")
        path = item.get("path")
        item["issue"] = issue_from_text(branch) or issue_from_text(path)
        item["status"] = "ok"
        records.append(item)
    return records


def collect_cloudbank_claims(root: Path, *, now: datetime | None = None) -> list[dict[str, Any]]:
    listed = session_claim.list_claims(root, now=now)
    claims: list[dict[str, Any]] = []
    for claim in listed.get("claims", []):
        repo = str(claim.get("repo") or "")
        task_id = str(claim.get("task_id") or "")
        issue = issue_from_task_id(task_id)
        if repo != CLOUDBANK_REPO_NAME and issue is None:
            continue
        enriched = dict(claim)
        enriched["issue"] = issue
        enriched["broker_claim"] = issue is not None
        claims.append(enriched)
    return claims


def active_claims_for_issue(claims: list[dict[str, Any]], issue: int) -> list[dict[str, Any]]:
    return [claim for claim in claims if claim.get("status") == "active" and claim.get("issue") == issue]


def worktrees_for_issue(worktrees: list[dict[str, Any]], issue: int) -> list[dict[str, Any]]:
    return [item for item in worktrees if item.get("issue") == issue]


def candidate_for_issue(issue: int, claims: list[dict[str, Any]], worktrees: list[dict[str, Any]]) -> dict[str, Any]:
    issue_claims = active_claims_for_issue(claims, issue)
    issue_worktrees = worktrees_for_issue(worktrees, issue)
    blockers: list[dict[str, Any]] = []
    for claim in issue_claims:
        blockers.append(
            {
                "kind": "active_claim",
                "claim_id": claim.get("claim_id"),
                "platform": claim.get("platform"),
                "paths": claim.get("paths", []),
                "expires_at": claim.get("expires_at"),
            }
        )
    for worktree in issue_worktrees:
        blockers.append(
            {
                "kind": "local_worktree",
                "path": worktree.get("path"),
                "branch": worktree.get("branch"),
                "head_sha": worktree.get("head_sha"),
            }
        )
    return {
        "issue": issue,
        "status": "blocked" if blockers else "claim_ready",
        "blockers": blockers,
        "recommended_next_action": (
            "Choose another issue or release/transfer the existing claim before editing."
            if blockers
            else "Run claim with explicit paths before creating a worktree or editing CloudBank."
        ),
    }


def build_report(
    root: Path,
    *,
    issues: list[int] | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    created = generated_at or utc_now()
    cloudbank = load_cloudbank_repo(root)
    repo_rel = cloudbank["path"]
    claims = collect_cloudbank_claims(root, now=created)
    worktrees = collect_worktrees(root, repo_rel)
    requested_issues = sorted(set(issues or []))
    candidates = [candidate_for_issue(issue, claims, worktrees) for issue in requested_issues]

    canonical = git_status(root, repo_rel)
    status = "ready"
    warnings: list[str] = []
    if canonical["exists"] and canonical.get("dirty"):
        warnings.append("canonical_cloudbank_checkout_dirty")
    if not canonical["exists"]:
        warnings.append("canonical_cloudbank_checkout_missing")
    if not requested_issues:
        status = "needs_issue_selection"
    elif any(candidate["status"] == "blocked" for candidate in candidates):
        status = "blocked"

    return {
        "schema_version": BROKER_SCHEMA_VERSION,
        "generated_at": format_time(created),
        "status": status,
        "warnings": warnings,
        "cloudbank_repo": cloudbank,
        "canonical_checkout": canonical,
        "active_cloudbank_claims": [claim for claim in claims if claim.get("status") == "active"],
        "stale_cloudbank_claims": [claim for claim in claims if claim.get("status") == "stale"],
        "local_cloudbank_worktrees": worktrees,
        "requested_issues": requested_issues,
        "candidates": candidates,
        "live_github_state": {
            "status": "not_requested",
            "note": "Use GitHub CLI/connector before treating issue lists, labels, or PR state as live.",
        },
    }


def check_issue_paths(
    *,
    root: Path,
    issue: int,
    paths: list[str],
    mutation_posture: str = "editing",
    now: datetime | None = None,
) -> dict[str, Any]:
    cloudbank = load_cloudbank_repo(root)
    normalized_paths = normalize_cloudbank_paths(paths, root=root, repo_rel=cloudbank["path"])
    checked_at = now or utc_now()
    claims = collect_cloudbank_claims(root, now=checked_at)
    duplicate_issue_claims = active_claims_for_issue(claims, issue)
    path_check = session_claim.check_claims(
        root=root,
        repo=CLOUDBANK_REPO_NAME,
        paths=normalized_paths,
        mutation_posture=mutation_posture,
        now=checked_at,
    )
    duplicate_conflicts = [
        {
            "kind": "active_issue_claim",
            "claim_id": claim.get("claim_id"),
            "platform": claim.get("platform"),
            "paths": claim.get("paths", []),
            "expires_at": claim.get("expires_at"),
        }
        for claim in duplicate_issue_claims
    ]
    status = "conflict" if path_check["conflicts"] or duplicate_conflicts else "clear"
    return {
        "schema_version": BROKER_SCHEMA_VERSION,
        "checked_at": format_time(checked_at),
        "status": status,
        "issue": issue,
        "repo": CLOUDBANK_REPO_NAME,
        "paths": normalized_paths,
        "path_claim_check": path_check,
        "issue_claim_conflicts": duplicate_conflicts,
    }


def claim_issue(
    *,
    root: Path,
    issue: int,
    platform: str,
    paths: list[str],
    label: str = "",
    ttl_minutes: int = session_claim.DEFAULT_TTL_MINUTES,
    validation_command: str = "",
    allow_conflict: bool = False,
    now: datetime | None = None,
) -> tuple[int, dict[str, Any]]:
    claimed_at = now or utc_now()
    cloudbank = load_cloudbank_repo(root)
    normalized_paths = normalize_cloudbank_paths(paths, root=root, repo_rel=cloudbank["path"])
    preflight = check_issue_paths(
        root=root,
        issue=issue,
        paths=normalized_paths,
        mutation_posture="editing",
        now=claimed_at,
    )
    if preflight["status"] == "conflict" and not allow_conflict:
        return 2, preflight

    branch = branch_for_issue(platform, issue, label)
    worktree = worktree_for_issue(platform, issue, label)
    notes = json.dumps(
        {
            "broker": "cloudbank_issue_broker",
            "issue": issue,
            "cloudbank_branch": branch,
            "cloudbank_worktree": str(worktree),
            "validation_command": validation_command,
        },
        sort_keys=True,
    )
    returncode, payload = session_claim.create_claim(
        root=root,
        platform=platform,
        task_id=f"cloudbank-issue-{issue}",
        repo=CLOUDBANK_REPO_NAME,
        paths=normalized_paths,
        mutation_posture="editing",
        ttl_minutes=ttl_minutes,
        session_label=f"CloudBank issue #{issue}",
        notes=notes,
        allow_conflict=allow_conflict,
        now=claimed_at,
    )
    if returncode != 0:
        return returncode, payload

    repo_path = (root / cloudbank["path"]).resolve()
    payload["broker"] = {
        "issue": issue,
        "branch": branch,
        "worktree": str(worktree),
        "worktree_command": (
            f"git -C {shlex.quote(str(repo_path))} fetch origin --prune && "
            f"git -C {shlex.quote(str(repo_path))} worktree add "
            f"{shlex.quote(str(worktree))} -b {shlex.quote(branch)} origin/main"
        ),
        "github_claim_comment": (
            f"Claimed by {platform} for issue #{issue}; branch `{branch}`; "
            f"paths: {', '.join(normalized_paths)}; validation: {validation_command or 'targeted tests TBD'}."
        ),
    }
    return returncode, payload


def release_issue(root: Path, *, issue: int | None = None, claim_id: str | None = None) -> tuple[int, dict[str, Any]]:
    if not issue and not claim_id:
        return 1, {"status": "error", "error": "Provide --issue or --claim-id."}

    released: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    if claim_id:
        code, payload = session_claim.release_claim(root, claim_id)
        if code == 0:
            released.append(payload)
        else:
            errors.append(payload)
    else:
        claims = collect_cloudbank_claims(root)
        matches = active_claims_for_issue(claims, int(issue))
        if not matches:
            return 1, {"status": "error", "error": f"No active claim found for CloudBank issue #{issue}."}
        for claim in matches:
            code, payload = session_claim.release_claim(root, str(claim["claim_id"]))
            if code == 0:
                released.append(payload)
            else:
                errors.append(payload)

    return (0 if not errors else 1), {
        "schema_version": BROKER_SCHEMA_VERSION,
        "status": "released" if released and not errors else "partial" if released else "error",
        "released": released,
        "errors": errors,
    }


def parse_issue_args(values: list[str] | None) -> list[int]:
    return [issue_number(value) for value in values or []]


def print_human(payload: dict[str, Any]) -> None:
    status = payload.get("status")
    if "candidates" in payload:
        print(f"cloudbank issue broker: {status}")
        for warning in payload.get("warnings", []):
            print(f"warning: {warning}")
        for candidate in payload.get("candidates", []):
            print(f"- #{candidate['issue']}: {candidate['status']}")
            for blocker in candidate.get("blockers", []):
                print(f"  blocker: {blocker}")
        if not payload.get("candidates"):
            print("next: provide --issue <number> or refresh live GitHub state before claiming work")
        return
    if payload.get("status") == "created":
        claim = payload.get("claim", {})
        broker = payload.get("broker", {})
        print(f"claimed: {claim.get('claim_id')} for CloudBank issue #{broker.get('issue')}")
        print(f"branch: {broker.get('branch')}")
        print(f"worktree command: {broker.get('worktree_command')}")
        return
    if payload.get("status") == "clear":
        print(f"cloudbank issue #{payload.get('issue')} claim check: clear")
        return
    print(json.dumps(payload, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="Aurora workspace root. Defaults to current directory.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan", help="Build a local-safe issue claim plan.")
    plan.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    plan.add_argument("--issue", action="append", default=[], help="Issue number to evaluate. Repeatable.")

    status = subparsers.add_parser("status", help="Show CloudBank issue claims and local worktrees.")
    status.add_argument("--json", action="store_true", help=argparse.SUPPRESS)

    check = subparsers.add_parser("check", help="Check whether issue paths can be claimed.")
    check.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    check.add_argument("--issue", required=True, help="CloudBank issue number.")
    check.add_argument("--paths", nargs="+", required=True, help="CloudBank-relative or root-relative paths.")

    claim = subparsers.add_parser("claim", help="Create a local CloudBank issue claim.")
    claim.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    claim.add_argument("--issue", required=True, help="CloudBank issue number.")
    claim.add_argument("--platform", required=True, help="codex, claude-code, or another owner label.")
    claim.add_argument("--paths", nargs="+", required=True, help="CloudBank-relative or root-relative paths.")
    claim.add_argument("--label", default="", help="Short branch/worktree suffix.")
    claim.add_argument("--ttl-minutes", type=int, default=session_claim.DEFAULT_TTL_MINUTES)
    claim.add_argument("--validation-command", default="", help="Expected targeted validation command.")
    claim.add_argument("--allow-conflict", action="store_true", help="Create even when conflicts are detected.")

    release = subparsers.add_parser("release", help="Release a CloudBank issue claim.")
    release.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    release.add_argument("--issue", help="Release active claim(s) for this issue.")
    release.add_argument("--claim-id", help="Release one exact claim id.")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).expanduser().resolve()

    try:
        if args.command == "plan":
            payload = build_report(root, issues=parse_issue_args(args.issue))
            returncode = 2 if payload["status"] == "blocked" else 0
        elif args.command == "status":
            payload = build_report(root)
            returncode = 0
        elif args.command == "check":
            payload = check_issue_paths(root=root, issue=issue_number(args.issue), paths=args.paths)
            returncode = 2 if payload["status"] == "conflict" else 0
        elif args.command == "claim":
            returncode, payload = claim_issue(
                root=root,
                issue=issue_number(args.issue),
                platform=args.platform,
                paths=args.paths,
                label=args.label,
                ttl_minutes=args.ttl_minutes,
                validation_command=args.validation_command,
                allow_conflict=args.allow_conflict,
            )
        elif args.command == "release":
            returncode, payload = release_issue(
                root,
                issue=issue_number(args.issue) if args.issue else None,
                claim_id=args.claim_id,
            )
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

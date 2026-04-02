#!/usr/bin/env python3
"""Run a repo-aware sync audit for the Aurora / ORIONCORE workspace."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_HYGIENE_POLICY: dict[str, Any] = {
    "version": 1,
    "defaults": {
        "warning": {
            "status_entries": 20,
            "untracked_files": 8,
            "deleted_files": 5,
            "behind_commits": 25,
        },
        "critical": {
            "status_entries": 75,
            "untracked_files": 25,
            "deleted_files": 25,
            "behind_commits": 200,
        },
        "warn_on_dirty_main": True,
        "warn_on_diverged_main": True,
    },
    "repos": {},
}


def utcnow_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def utcnow_display() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def run_git(repo_path: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_path,
        check=check,
        text=True,
        capture_output=True,
    )


def detect_workspace_root(explicit_root: str | None) -> Path:
    if explicit_root:
        return Path(explicit_root).expanduser().resolve()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            text=True,
            capture_output=True,
        )
        return Path(result.stdout.strip()).resolve()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            "Could not determine workspace root. Run from the repo root or pass --workspace-root."
        ) from exc


def load_structured_file(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return {}
    try:
        loaded = json.loads(raw)
        return loaded if isinstance(loaded, dict) else {}
    except json.JSONDecodeError:
        pass
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError:
        # YAML support not available; treat as no structured content.
        return {}
    try:
        loaded = yaml.safe_load(raw) or {}
        return loaded if isinstance(loaded, dict) else {}
    except Exception as exc:
        # The file exists and contains non-empty data but could not be parsed as YAML.
        print(f"Failed to parse structured file '{path}': {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


def load_repo_registry(workspace_root: Path) -> list[dict[str, Any]]:
    registry_path = workspace_root / "catalog" / "repo_registry.yaml"
    if not registry_path.exists():
        return []
    return load_structured_file(registry_path).get("repos", [])


def merge_policy(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for key in set(base) | set(override):
        base_value = base.get(key)
        override_value = override.get(key)
        if isinstance(base_value, dict) and isinstance(override_value, dict):
            merged[key] = merge_policy(base_value, override_value)
        elif key in override:
            merged[key] = override_value
        else:
            merged[key] = base_value
    return merged


def load_hygiene_policy(workspace_root: Path, explicit_policy: str | None) -> dict[str, Any]:
    if explicit_policy:
        candidate = Path(explicit_policy).expanduser()
        if not candidate.is_absolute():
            candidate = workspace_root / candidate
        policy_path = candidate.resolve()
    else:
        policy_path = workspace_root / "catalog" / "gitwiz_hygiene_policy.yaml"

    if not policy_path.exists():
        return DEFAULT_HYGIENE_POLICY

    loaded = load_structured_file(policy_path)
    if not loaded:
        return DEFAULT_HYGIENE_POLICY

    return merge_policy(DEFAULT_HYGIENE_POLICY, loaded)


def parse_remote_map(remote_output: str) -> dict[str, dict[str, str]]:
    remotes: dict[str, dict[str, str]] = {}
    for raw_line in remote_output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        name, url, kind = parts[0], parts[1], parts[2].strip("()")
        remotes.setdefault(name, {})[kind] = url
    return remotes


def parse_status_lines(status_output: str) -> dict[str, Any]:
    counts = {
        "modified": 0,
        "added": 0,
        "deleted": 0,
        "renamed": 0,
        "copied": 0,
        "unmerged": 0,
        "untracked": 0,
        "other": 0,
    }
    files: list[str] = []
    for raw_line in status_output.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        files.append(line)
        if line.startswith("??"):
            counts["untracked"] += 1
            continue
        state = line[:2]
        if "U" in state:
            counts["unmerged"] += 1
        elif "R" in state:
            counts["renamed"] += 1
        elif "C" in state:
            counts["copied"] += 1
        elif "A" in state:
            counts["added"] += 1
        elif "D" in state:
            counts["deleted"] += 1
        elif "M" in state:
            counts["modified"] += 1
        else:
            counts["other"] += 1
    return {"counts": counts, "files": files}


def count_tracked_changes(status_counts: dict[str, int]) -> int:
    return sum(
        int(status_counts.get(key, 0))
        for key in ("modified", "added", "deleted", "renamed", "copied", "unmerged", "other")
    )


def resolve_target_paths(
    workspace_root: Path,
    canonical_root: Path | None,
    repo_registry: list[dict[str, Any]],
    selection: str,
) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = [
        {
            "name": "root",
            "relative_path": ".",
            "candidate_paths": [workspace_root],
        }
    ]

    for repo in repo_registry:
        rel = repo["path"]
        candidate_paths = [workspace_root / rel]
        if canonical_root:
            candidate_paths.append(canonical_root / rel)
        targets.append(
            {
                "name": repo["name"],
                "relative_path": rel,
                "candidate_paths": candidate_paths,
            }
        )

    if selection == "all":
        return targets
    for target in targets:
        if selection in {target["name"], target["relative_path"], "root"} and target["name"] == selection:
            return [target]
        if selection == "root" and target["name"] == "root":
            return [target]
        if selection == target["relative_path"]:
            return [target]
    available = ", ".join(target["name"] for target in targets)
    raise SystemExit(f"Unknown repo selection '{selection}'. Available: {available}")


def choose_existing_path(candidate_paths: list[Path]) -> Path | None:
    for path in candidate_paths:
        if (path / ".git").exists() or path == path.resolve() and (path / ".git").exists():
            return path.resolve()
    for path in candidate_paths:
        if path.exists():
            return path.resolve()
    return None


def upstream_status(repo_path: Path) -> dict[str, Any]:
    try:
        upstream = run_git(repo_path, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"]).stdout.strip()
    except subprocess.CalledProcessError:
        return {"upstream": "", "ahead": 0, "behind": 0}
    counts = run_git(repo_path, ["rev-list", "--left-right", "--count", f"{upstream}...HEAD"]).stdout.strip().split()
    behind = int(counts[0]) if counts else 0
    ahead = int(counts[1]) if len(counts) > 1 else 0
    return {"upstream": upstream, "ahead": ahead, "behind": behind}


def suggest_actions(summary: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    if not summary["exists"]:
        actions.append("Repo path is missing in the current execution context; use the canonical workspace path or update the target selection.")
        return actions
    if not summary["remotes"]:
        actions.append("Create a private GitHub repo and add origin before treating this repo as synced.")
    if summary["dirty"]:
        actions.append("Review, commit, or ignore local modifications before claiming repo parity with GitHub.")
    if summary["status_counts"]["untracked"]:
        actions.append("Review untracked files; commit them if they belong in Git or add ignore rules if they do not.")
    if summary["ahead"] > 0:
        actions.append(f"Push {summary['branch']} to {summary['upstream'] or 'origin'} so the remote matches local history.")
    if summary["behind"] > 0:
        actions.append(f"Fetch and integrate {summary['upstream']} before pushing to avoid overwriting remote history.")
    if summary["branch"] not in {"", "HEAD", "main"} and summary["remotes"]:
        actions.append("After push, create or update a PR against origin/main so GitHub reflects the local branch work.")
    if summary["branch"] == "main" and (summary["dirty"] or summary["ahead"] > 0):
        actions.append("Consider creating a sync branch and PR if you want reviewable parity updates instead of direct main mutation.")
    if not actions:
        actions.append("No obvious sync action needed; local state appears aligned with the configured remote tracking state.")
    return actions


def repo_hygiene_policy(policy: dict[str, Any], repo_name: str) -> dict[str, Any]:
    defaults = policy.get("defaults", {})
    repo_overrides = policy.get("repos", {}).get(repo_name, {})
    return merge_policy(defaults, repo_overrides)


def hygiene_metric_values(summary: dict[str, Any]) -> dict[str, int]:
    counts = summary.get("status_counts", {})
    tracked_changes = count_tracked_changes(counts)
    return {
        "status_entries": tracked_changes + int(counts.get("untracked", 0)),
        "tracked_changes": tracked_changes,
        "untracked_files": int(counts.get("untracked", 0)),
        "deleted_files": int(counts.get("deleted", 0)),
        "ahead_commits": int(summary.get("ahead", 0)),
        "behind_commits": int(summary.get("behind", 0)),
    }


def add_breach(
    breaches: list[dict[str, Any]],
    *,
    level: str,
    metric: str,
    actual: int | str,
    threshold: int | str,
    message: str,
) -> None:
    breaches.append(
        {
            "level": level,
            "metric": metric,
            "actual": actual,
            "threshold": threshold,
            "message": message,
        }
    )


def evaluate_hygiene(summary: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    breaches: list[dict[str, Any]] = []
    if not summary["exists"]:
        add_breach(
            breaches,
            level="critical",
            metric="repo_presence",
            actual="missing",
            threshold="present",
            message="Repo path is unavailable in the current execution context.",
        )
    elif not summary["remotes"]:
        add_breach(
            breaches,
            level="warning",
            metric="remote_config",
            actual="missing",
            threshold="configured",
            message="Repo has no configured remote, so parity with GitHub cannot be verified.",
        )

    metrics = hygiene_metric_values(summary)
    warning_thresholds = policy.get("warning", {})
    critical_thresholds = policy.get("critical", {})
    for metric, actual in metrics.items():
        critical_threshold = critical_thresholds.get(metric)
        warning_threshold = warning_thresholds.get(metric)
        if isinstance(critical_threshold, int) and actual >= critical_threshold:
            add_breach(
                breaches,
                level="critical",
                metric=metric,
                actual=actual,
                threshold=critical_threshold,
                message=f"{metric} is over the critical repo hygiene budget.",
            )
        elif isinstance(warning_threshold, int) and actual >= warning_threshold:
            add_breach(
                breaches,
                level="warning",
                metric=metric,
                actual=actual,
                threshold=warning_threshold,
                message=f"{metric} is over the warning repo hygiene budget.",
            )

    if summary.get("branch") == "main" and summary.get("dirty") and policy.get("warn_on_dirty_main", True):
        add_breach(
            breaches,
            level="warning",
            metric="dirty_main",
            actual=metrics["status_entries"],
            threshold=0,
            message="Working directly on main is accumulating uncommitted drift.",
        )

    if (
        summary.get("branch") == "main"
        and summary.get("sync_state") == "diverged"
        and policy.get("warn_on_diverged_main", True)
    ):
        add_breach(
            breaches,
            level="warning",
            metric="diverged_main",
            actual=f"{summary.get('ahead', 0)}/{summary.get('behind', 0)}",
            threshold="0/0",
            message="Main has diverged from upstream; large sync work will compound if this is left open.",
        )

    status = "ok"
    if any(breach["level"] == "critical" for breach in breaches):
        status = "critical"
    elif breaches:
        status = "warning"

    return {
        "status": status,
        "metrics": metrics,
        "breaches": breaches,
        "role": policy.get("role", ""),
        "note": policy.get("note", ""),
    }


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def hygiene_actions(summary: dict[str, Any], hygiene: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    breach_metrics = {breach["metric"] for breach in hygiene["breaches"]}
    if "dirty_main" in breach_metrics:
        actions.append("Move active work off main into a short-lived branch before the delta grows further.")
    if "status_entries" in breach_metrics or "tracked_changes" in breach_metrics:
        actions.append("Split the local delta into smaller commit batches by repo and artifact class.")
    if "untracked_files" in breach_metrics:
        actions.append("Decide whether the untracked files are source, generated runtime state, or receipts, then either commit or ignore them.")
    if "deleted_files" in breach_metrics:
        actions.append("Review the deletion set explicitly before staging anything; this size usually means migration drift or path confusion.")
    if "behind_commits" in breach_metrics or summary.get("sync_state") == "diverged":
        actions.append("Fetch and reconcile upstream sooner; once behind grows into the hundreds, recovery becomes a dedicated sync project.")
    if "remote_config" in breach_metrics:
        actions.append("Configure a remote before treating this repo as part of the normal publication loop.")
    if "repo_presence" in breach_metrics:
        actions.append("Run the audit from the canonical workspace path so nested repo state is measured from the real checkout.")
    return dedupe_preserve_order(actions)


def overall_hygiene_status(repos: list[dict[str, Any]]) -> str:
    statuses = {repo.get("hygiene", {}).get("status", "ok") for repo in repos}
    if "critical" in statuses:
        return "critical"
    if "warning" in statuses:
        return "warning"
    return "ok"


def should_fail(overall_status: str, fail_on: str) -> bool:
    if fail_on == "none":
        return False
    if fail_on == "warning":
        return overall_status in {"warning", "critical"}
    return overall_status == "critical"


def build_repo_summary(target: dict[str, Any], fetch: bool, hygiene_policy_config: dict[str, Any]) -> dict[str, Any]:
    chosen_path = choose_existing_path(target["candidate_paths"])
    summary: dict[str, Any] = {
        "name": target["name"],
        "relative_path": target["relative_path"],
        "resolved_path": str(chosen_path) if chosen_path else "",
        "exists": bool(chosen_path and (chosen_path / ".git").exists()),
        "branch": "",
        "head_sha": "",
        "remotes": {},
        "upstream": "",
        "ahead": 0,
        "behind": 0,
        "dirty": False,
        "status_counts": {
            "modified": 0,
            "added": 0,
            "deleted": 0,
            "renamed": 0,
            "copied": 0,
            "unmerged": 0,
            "untracked": 0,
            "other": 0,
        },
        "status_lines": [],
        "sync_state": "missing",
        "suggested_actions": [],
        "hygiene": {},
    }

    if not summary["exists"]:
        repo_policy = repo_hygiene_policy(hygiene_policy_config, summary["name"])
        summary["hygiene"] = evaluate_hygiene(summary, repo_policy)
        summary["suggested_actions"] = suggest_actions(summary)
        summary["suggested_actions"].extend(hygiene_actions(summary, summary["hygiene"]))
        summary["suggested_actions"] = dedupe_preserve_order(summary["suggested_actions"])
        return summary

    repo_path = Path(summary["resolved_path"])
    if fetch:
        run_git(repo_path, ["fetch", "--all", "--prune"], check=False)

    summary["branch"] = run_git(repo_path, ["rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    summary["head_sha"] = run_git(repo_path, ["rev-parse", "HEAD"]).stdout.strip()
    summary["remotes"] = parse_remote_map(run_git(repo_path, ["remote", "-v"]).stdout)
    status = parse_status_lines(run_git(repo_path, ["status", "--short"]).stdout)
    summary["status_counts"] = status["counts"]
    summary["status_lines"] = status["files"]
    summary["dirty"] = bool(status["files"])
    upstream = upstream_status(repo_path)
    summary["upstream"] = upstream["upstream"]
    summary["ahead"] = upstream["ahead"]
    summary["behind"] = upstream["behind"]

    if not summary["remotes"]:
        summary["sync_state"] = "no_remote"
    elif summary["dirty"]:
        summary["sync_state"] = "dirty"
    elif summary["ahead"] > 0 and summary["behind"] > 0:
        summary["sync_state"] = "diverged"
    elif summary["ahead"] > 0:
        summary["sync_state"] = "ahead"
    elif summary["behind"] > 0:
        summary["sync_state"] = "behind"
    else:
        summary["sync_state"] = "in_sync"

    repo_policy = repo_hygiene_policy(hygiene_policy_config, summary["name"])
    summary["hygiene"] = evaluate_hygiene(summary, repo_policy)
    summary["suggested_actions"] = suggest_actions(summary)
    summary["suggested_actions"].extend(hygiene_actions(summary, summary["hygiene"]))
    summary["suggested_actions"] = dedupe_preserve_order(summary["suggested_actions"])
    return summary


def markdown_report(report: dict[str, Any]) -> str:
    overall_status = report.get("overall_hygiene_status", "ok")
    critical_repos = [repo["name"] for repo in report["repos"] if repo.get("hygiene", {}).get("status") == "critical"]
    warning_repos = [repo["name"] for repo in report["repos"] if repo.get("hygiene", {}).get("status") == "warning"]
    lines = [
        "# GITWIZ Sync Audit",
        "",
        f"Generated: {report['generated_at_utc']}",
        f"Workspace Root: `{report['workspace_root']}`",
        f"Canonical Root: `{report['canonical_root'] or 'not_provided'}`",
        f"Policy Path: `{report.get('policy_path') or 'default'}`",
        "",
        "## Summary",
        "",
        f"- Target selection: `{report['selection']}`",
        f"- Repos scanned: `{len(report['repos'])}`",
        f"- Overall hygiene status: `{overall_status}`",
    ]
    problem_repos = [repo["name"] for repo in report["repos"] if repo["sync_state"] != "in_sync"]
    lines.append(f"- Repos needing attention: `{len(problem_repos)}`")
    if problem_repos:
        lines.append(f"- Attention targets: {', '.join(problem_repos)}")
    lines.append(f"- Warning hygiene targets: `{len(warning_repos)}`")
    lines.append(f"- Critical hygiene targets: `{len(critical_repos)}`")
    lines.extend(["", "## Repo Findings", ""])
    for repo in report["repos"]:
        lines.append(f"### {repo['name']}")
        lines.append("")
        lines.append(f"- Path: `{repo['resolved_path'] or repo['relative_path']}`")
        lines.append(f"- Exists: `{repo['exists']}`")
        lines.append(f"- Sync state: `{repo['sync_state']}`")
        lines.append(f"- Hygiene status: `{repo.get('hygiene', {}).get('status', 'ok')}`")
        if repo["exists"]:
            lines.append(f"- Branch: `{repo['branch']}`")
            lines.append(f"- HEAD: `{repo['head_sha']}`")
            lines.append(f"- Upstream: `{repo['upstream'] or 'none'}`")
            lines.append(f"- Ahead / behind: `{repo['ahead']}` / `{repo['behind']}`")
            lines.append(f"- Dirty: `{repo['dirty']}`")
            counts = repo["status_counts"]
            lines.append(
                "- Status counts: "
                f"modified={counts['modified']}, added={counts['added']}, deleted={counts['deleted']}, "
                f"renamed={counts['renamed']}, untracked={counts['untracked']}, unmerged={counts['unmerged']}"
            )
            metrics = repo.get("hygiene", {}).get("metrics", {})
            if metrics:
                lines.append(
                    "- Hygiene metrics: "
                    f"status_entries={metrics['status_entries']}, tracked_changes={metrics['tracked_changes']}, "
                    f"untracked_files={metrics['untracked_files']}, deleted_files={metrics['deleted_files']}, "
                    f"behind_commits={metrics['behind_commits']}"
                )
            if repo["remotes"]:
                remote_summary = ", ".join(
                    f"{name}={values.get('fetch', values.get('push', ''))}" for name, values in sorted(repo["remotes"].items())
                )
                lines.append(f"- Remotes: {remote_summary}")
            if repo["status_lines"]:
                lines.append("- Local status lines:")
                for line in repo["status_lines"][:20]:
                    lines.append(f"  - `{line}`")
        if repo.get("hygiene", {}).get("role"):
            lines.append(f"- Repo role: `{repo['hygiene']['role']}`")
        if repo.get("hygiene", {}).get("note"):
            lines.append(f"- Hygiene note: {repo['hygiene']['note']}")
        breaches = repo.get("hygiene", {}).get("breaches", [])
        if breaches:
            lines.append("- Hygiene breaches:")
            for breach in breaches:
                lines.append(
                    f"  - `{breach['level']}` {breach['metric']}: actual=`{breach['actual']}` threshold=`{breach['threshold']}`"
                )
        lines.append("- Suggested actions:")
        for action in repo["suggested_actions"]:
            lines.append(f"  - {action}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="root", help="Target repo name from repo_registry, 'root', or 'all'.")
    parser.add_argument("--workspace-root", help="Root workspace repo path. Defaults to current Git toplevel.")
    parser.add_argument("--canonical-root", help="Canonical workspace root used to resolve nested repos outside the current worktree.")
    parser.add_argument("--fetch", action="store_true", help="Fetch remotes before evaluating ahead/behind state.")
    parser.add_argument("--policy", help="Repo hygiene policy file. Defaults to catalog/gitwiz_hygiene_policy.yaml when present.")
    parser.add_argument(
        "--fail-on",
        choices=("none", "warning", "critical"),
        default="none",
        help="Return a non-zero exit code when the audit reaches the selected hygiene severity.",
    )
    parser.add_argument("--output-dir", help="Directory to write JSON and Markdown reports into.")
    args = parser.parse_args()

    workspace_root = detect_workspace_root(args.workspace_root)
    canonical_root = Path(args.canonical_root).expanduser().resolve() if args.canonical_root else None
    repo_registry = load_repo_registry(workspace_root)
    hygiene_policy = load_hygiene_policy(workspace_root, args.policy)
    targets = resolve_target_paths(workspace_root, canonical_root, repo_registry, args.repo)
    repo_reports = [build_repo_summary(target, args.fetch, hygiene_policy) for target in targets]
    overall_status = overall_hygiene_status(repo_reports)
    policy_path = args.policy or (
        "catalog/gitwiz_hygiene_policy.yaml"
        if (workspace_root / "catalog" / "gitwiz_hygiene_policy.yaml").exists()
        else ""
    )

    report = {
        "generated_at_utc": utcnow_display(),
        "generated_at_compact": utcnow_compact(),
        "workspace_root": str(workspace_root),
        "canonical_root": str(canonical_root) if canonical_root else "",
        "policy_path": policy_path,
        "selection": args.repo,
        "overall_hygiene_status": overall_status,
        "repos": repo_reports,
    }

    if args.output_dir:
        output_dir = Path(args.output_dir).expanduser().resolve()
    else:
        output_dir = workspace_root / "reports" / "analysis" / "gitwiz"
    output_dir.mkdir(parents=True, exist_ok=True)

    stem = f"GITWIZ_SYNC_AUDIT__{report['generated_at_compact']}"
    json_path = output_dir / f"{stem}.json"
    md_path = output_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(markdown_report(report), encoding="utf-8")

    exit_code = 1 if should_fail(overall_status, args.fail_on) else 0
    print(
        json.dumps(
            {
                "json_report": str(json_path),
                "markdown_report": str(md_path),
                "overall_hygiene_status": overall_status,
                "fail_on": args.fail_on,
                "exit_code": exit_code,
            },
            indent=2,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

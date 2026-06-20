#!/usr/bin/env python3
"""Run a repo-aware sync audit for the Aurora / ORIONCORE workspace."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utcnow_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def utcnow_display() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def load_gh_auth_probe():
    probe_path = Path(__file__).with_name("gitwiz_gh_auth_probe.py")
    spec = importlib.util.spec_from_file_location("gitwiz_gh_auth_probe", probe_path)
    if not spec or not spec.loader:
        raise RuntimeError(f"Could not load GitHub CLI auth probe: {probe_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def collect_gh_auth_context(check: bool, repo: str | None = None) -> dict[str, Any]:
    if not check:
        return {
            "checked": False,
            "status": "not_checked",
            "next_step": "Run with --check-gh-auth before diagnosing GitHub CLI token state.",
        }
    probe = load_gh_auth_probe()
    payload = probe.probe_gh_auth(repo=repo)
    payload["checked"] = True
    return payload


def run_git(repo_path: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603, S607 - git command/args are repo-audit controlled.
        ["git", *args],  # noqa: S607 - git is the required repo audit command.
        cwd=repo_path,
        check=check,
        text=True,
        capture_output=True,
    )


def detect_workspace_root(explicit_root: str | None) -> Path:
    if explicit_root:
        return Path(explicit_root).expanduser().resolve()
    try:
        result = subprocess.run(  # noqa: S607 - git is the required repo discovery command.
            ["git", "rev-parse", "--show-toplevel"],  # noqa: S607
            check=True,
            text=True,
            capture_output=True,
        )
        return Path(result.stdout.strip()).resolve()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            "Could not determine workspace root. Run from the repo root or pass --workspace-root."
        ) from exc


def load_repo_registry(workspace_root: Path) -> list[dict[str, Any]]:
    registry_path = workspace_root / "catalog" / "repo_registry.yaml"
    if not registry_path.exists():
        return []
    try:
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        tools_dir = workspace_root / "tools"
        if str(tools_dir) not in sys.path:
            sys.path.insert(0, str(tools_dir))
        try:
            from _workspace_common import load_yaml_like

            payload = load_yaml_like(registry_path)
        except Exception as exc:
            raise SystemExit(f"Malformed repo registry: {registry_path}: {exc}") from exc
    try:
        return repo_rows_from_payload(payload)
    except ValueError as exc:
        raise SystemExit(f"Malformed repo registry: {exc}") from exc


def repo_rows_from_payload(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    rows = payload.get("repos", [])
    if not isinstance(rows, list):
        raise ValueError("repos must be a list")
    bad_indices = [str(index) for index, row in enumerate(rows) if not isinstance(row, dict)]
    if bad_indices:
        joined = ", ".join(bad_indices)
        raise ValueError(f"repo row index(es): {joined} must be objects")
    return rows


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


def unique_paths(*path_groups: list[str]) -> list[str]:
    return list(dict.fromkeys(path for group in path_groups for path in group if path))


def collect_repo_paths(repo_path: Path, args: list[str]) -> list[str]:
    result = run_git(repo_path, args, check=False)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def collect_local_dirty_paths(repo_path: Path) -> list[str]:
    unstaged = collect_repo_paths(repo_path, ["diff", "--name-only"])
    staged = collect_repo_paths(repo_path, ["diff", "--cached", "--name-only"])
    untracked = collect_repo_paths(repo_path, ["ls-files", "--others", "--exclude-standard"])
    return unique_paths(unstaged, staged, untracked)


def collect_incoming_remote_paths(repo_path: Path, comparison_ref: str, behind: int) -> list[str]:
    if not comparison_ref or behind <= 0:
        return []
    return collect_repo_paths(repo_path, ["diff", "--name-only", f"HEAD..{comparison_ref}"])


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


def git_ref_exists(repo_path: Path, ref: str) -> bool:
    result = run_git(repo_path, ["rev-parse", "--verify", ref], check=False)
    return result.returncode == 0


def comparison_status(repo_path: Path, branch: str) -> dict[str, Any]:
    try:
        upstream = run_git(repo_path, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"]).stdout.strip()
        comparison_ref = upstream
        mode = "configured_upstream"
    except subprocess.CalledProcessError:
        if branch not in {"", "HEAD", "main"} and git_ref_exists(repo_path, "refs/remotes/origin/main"):
            upstream = ""
            comparison_ref = "origin/main"
            mode = "fallback_origin_main"
        else:
            return {"upstream": "", "comparison_ref": "", "ahead": 0, "behind": 0, "comparison_mode": "none"}
    counts = run_git(repo_path, ["rev-list", "--left-right", "--count", f"{comparison_ref}...HEAD"]).stdout.strip().split()
    behind = int(counts[0]) if counts else 0
    ahead = int(counts[1]) if len(counts) > 1 else 0
    return {
        "upstream": upstream,
        "comparison_ref": comparison_ref,
        "ahead": ahead,
        "behind": behind,
        "comparison_mode": mode,
    }


def push_target(summary: dict[str, Any]) -> str:
    if summary["upstream"]:
        return summary["upstream"]
    if summary["branch"] not in {"", "HEAD"}:
        return f"origin/{summary['branch']}"
    return "origin"


def stash_preservation_action(summary: dict[str, Any]) -> str:
    stash_name = f"gitwiz-pre-{summary['branch'] or 'repo'}-sync"
    branch_label = summary["branch"] or "the branch"
    if summary["overlap_paths"]:
        overlap = ", ".join(summary["overlap_paths"][:5])
        return (
            f"Preserve the working copy with a named `git stash push -u -m \"{stash_name}\"`, "
            f"update {branch_label}, then reapply and manually resolve overlap in: {overlap}."
        )
    return (
        f"Preserve the working copy with a named `git stash push -u -m \"{stash_name}\"`, "
        f"update {branch_label}, then reapply the local changes."
    )


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
        actions.append(f"Push {summary['branch']} to {push_target(summary)} so the remote matches local history.")
    if summary["behind"] > 0:
        actions.append(f"Fetch and integrate {summary['comparison_ref']} before pushing to avoid overwriting remote history.")
    if summary["dirty"] and summary["behind"] > 0:
        actions.append(stash_preservation_action(summary))
    actions.extend(branch_workflow_actions(summary))
    if not actions:
        actions.append("No obvious sync action needed; local state appears aligned with the configured remote tracking state.")
    return actions


def branch_workflow_actions(summary: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    if summary["branch"] not in {"", "HEAD", "main"} and summary["remotes"]:
        actions.append("After push, create or update a PR against origin/main so GitHub reflects the local branch work.")
    if summary["branch"] == "main" and (summary["dirty"] or summary["ahead"] > 0):
        actions.append("Consider creating a sync branch and PR if you want reviewable parity updates instead of direct main mutation.")
    return actions


def build_repo_summary(target: dict[str, Any], fetch: bool) -> dict[str, Any]:
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
        "comparison_ref": "",
        "comparison_mode": "none",
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
        "local_dirty_paths": [],
        "incoming_remote_paths": [],
        "overlap_paths": [],
        "sync_state": "missing",
        "suggested_actions": [],
    }

    if not summary["exists"]:
        summary["suggested_actions"] = suggest_actions(summary)
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
    upstream = comparison_status(repo_path, summary["branch"])
    summary["upstream"] = upstream["upstream"]
    summary["comparison_ref"] = upstream["comparison_ref"]
    summary["comparison_mode"] = upstream["comparison_mode"]
    summary["ahead"] = upstream["ahead"]
    summary["behind"] = upstream["behind"]
    summary["local_dirty_paths"] = collect_local_dirty_paths(repo_path) if summary["dirty"] else []
    summary["incoming_remote_paths"] = collect_incoming_remote_paths(repo_path, summary["comparison_ref"], summary["behind"])
    incoming_remote_path_set = set(summary["incoming_remote_paths"])
    summary["overlap_paths"] = [path for path in summary["local_dirty_paths"] if path in incoming_remote_path_set]

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

    summary["suggested_actions"] = suggest_actions(summary)
    return summary


def repo_detail_lines(repo: dict[str, Any]) -> list[str]:
    lines = [
        f"- Branch: `{repo['branch']}`",
        f"- HEAD: `{repo['head_sha']}`",
        f"- Upstream: `{repo['upstream'] or 'none'}`",
    ]
    if repo["comparison_mode"] != "none":
        lines.append(f"- Comparison mode: `{repo['comparison_mode']}`")
    if repo["comparison_ref"] and repo["comparison_ref"] != repo["upstream"]:
        lines.append(f"- Comparison ref: `{repo['comparison_ref']}`")
    lines.append(f"- Ahead / behind: `{repo['ahead']}` / `{repo['behind']}`")
    lines.append(f"- Dirty: `{repo['dirty']}`")
    counts = repo["status_counts"]
    lines.append(
        "- Status counts: "
        f"modified={counts['modified']}, added={counts['added']}, deleted={counts['deleted']}, "
        f"renamed={counts['renamed']}, untracked={counts['untracked']}, unmerged={counts['unmerged']}"
    )
    if repo["remotes"]:
        remote_summary = ", ".join(
            f"{name}={values.get('fetch', values.get('push', ''))}" for name, values in sorted(repo["remotes"].items())
        )
        lines.append(f"- Remotes: {remote_summary}")
    if repo["status_lines"]:
        lines.append("- Local status lines:")
        lines.extend(f"  - `{line}`" for line in repo["status_lines"][:20])
    if repo["overlap_paths"]:
        lines.append(
            f"- Overlap risk: `{len(repo['overlap_paths'])}` dirty path(s) also change in `{repo['comparison_ref'] or 'the comparison branch'}`."
        )
        lines.extend(f"  - `{path}`" for path in repo["overlap_paths"][:10])
    return lines


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# GITWIZ Sync Audit",
        "",
        f"Generated: {report['generated_at_utc']}",
        f"Workspace Root: `{report['workspace_root']}`",
        f"Canonical Root: `{report['canonical_root'] or 'not_provided'}`",
        "",
        "## Summary",
        "",
        f"- Target selection: `{report['selection']}`",
        f"- Repos scanned: `{len(report['repos'])}`",
    ]
    problem_repos = [repo["name"] for repo in report["repos"] if repo["sync_state"] != "in_sync"]
    lines.append(f"- Repos needing attention: `{len(problem_repos)}`")
    if problem_repos:
        lines.append(f"- Attention targets: {', '.join(problem_repos)}")
    gh_auth = report.get("github_cli_auth", {})
    lines.extend(["", "## GitHub CLI Context", ""])
    lines.append(f"- Checked: `{gh_auth.get('checked', False)}`")
    lines.append(f"- Status: `{gh_auth.get('status', 'unknown')}`")
    if gh_auth.get("login"):
        lines.append(f"- Login: `{gh_auth['login']}`")
    if gh_auth.get("repo"):
        lines.append(f"- Repo probe: `{gh_auth['repo']}`")
    if gh_auth.get("next_step"):
        lines.append(f"- Next step: {gh_auth['next_step']}")
    lines.extend(["", "## Repo Findings", ""])
    for repo in report["repos"]:
        lines.append(f"### {repo['name']}")
        lines.append("")
        lines.append(f"- Path: `{repo['resolved_path'] or repo['relative_path']}`")
        lines.append(f"- Exists: `{repo['exists']}`")
        lines.append(f"- Sync state: `{repo['sync_state']}`")
        if repo["exists"]:
            lines.extend(repo_detail_lines(repo))
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
    parser.add_argument("--check-gh-auth", action="store_true", help="Probe gh auth and record current execution-context status in the report.")
    parser.add_argument("--gh-repo", help="Optional owner/repo probe for gh PR access when --check-gh-auth is set.")
    parser.add_argument("--output-dir", help="Directory to write JSON and Markdown reports into.")
    args = parser.parse_args()

    workspace_root = detect_workspace_root(args.workspace_root)
    canonical_root = Path(args.canonical_root).expanduser().resolve() if args.canonical_root else None
    repo_registry = load_repo_registry(workspace_root)
    targets = resolve_target_paths(workspace_root, canonical_root, repo_registry, args.repo)
    repo_reports = [build_repo_summary(target, args.fetch) for target in targets]

    report = {
        "generated_at_utc": utcnow_display(),
        "generated_at_compact": utcnow_compact(),
        "workspace_root": str(workspace_root),
        "canonical_root": str(canonical_root) if canonical_root else "",
        "selection": args.repo,
        "github_cli_auth": collect_gh_auth_context(args.check_gh_auth, args.gh_repo),
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

    print(json.dumps({"json_report": str(json_path), "markdown_report": str(md_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

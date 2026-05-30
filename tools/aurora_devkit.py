#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import datetime as dt
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "reports" / "analysis" / "aurora_devkit_latest.json"
DEFAULT_INSTALL_PLAN = ROOT / "reports" / "analysis" / "aurora_devkit_install_plan_latest.json"
DEFAULT_SKILLS_ROOT = Path("~/.codex/skills").expanduser()
DEFAULT_AUTOMATIONS_ROOT = Path("~/.codex/automations").expanduser()


CommandRunner = Callable[[list[str]], dict[str, Any]]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def relpath(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str], timeout: int = 8) -> dict[str, Any]:
    executable = shutil.which(args[0])
    if executable is None:
        return {
            "status": "missing",
            "command": args,
            "path": None,
            "returncode": None,
            "output": "",
        }

    try:
        result = subprocess.run(
            args,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "command": args,
            "path": executable,
            "returncode": None,
            "output": "",
        }
    except OSError as exc:
        return {
            "status": "error",
            "command": args,
            "path": executable,
            "returncode": None,
            "output": str(exc),
        }

    output = result.stdout.strip() or result.stderr.strip()
    return {
        "status": "ok" if result.returncode == 0 else "error",
        "command": args,
        "path": executable,
        "returncode": result.returncode,
        "output": "\n".join(output.splitlines()[:4]),
    }


def scan_toolchain(manifest: dict[str, Any], runner: CommandRunner = run_command) -> list[dict[str, Any]]:
    tools = []
    for item in manifest.get("toolchain", []):
        probe = runner(list(item["command"]))
        tools.append(
            {
                "id": item["id"],
                "category": item.get("category", "unknown"),
                "required": bool(item.get("required", False)),
                "impact": item.get("impact", ""),
                **probe,
            }
        )
    return tools


def discover_package_manifests(root: Path, manifest: dict[str, Any]) -> list[dict[str, str]]:
    names = set(manifest.get("package_manifest_names", []))
    prune = set(manifest.get("prune_directory_names", []))
    discovered: list[dict[str, str]] = []

    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in sorted(dirnames) if name not in prune]
        current = Path(current_root)
        for filename in sorted(filenames):
            if filename not in names:
                continue
            path = current / filename
            discovered.append(
                {
                    "path": relpath(path, root),
                    "name": filename,
                    "kind": classify_package_manifest(filename),
                }
            )

    return discovered


def classify_package_manifest(filename: str) -> str:
    if filename in {"pyproject.toml", "requirements.txt", "requirements-dev.txt", "setup.py", "setup.cfg", "uv.lock", "poetry.lock", "Pipfile"}:
        return "python"
    if filename in {"package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", ".node-version"}:
        return "javascript"
    if filename in {"Dockerfile", "docker-compose.yml", "devcontainer.json"}:
        return "container"
    if filename in {"Makefile", "Taskfile.yml", ".pre-commit-config.yaml"}:
        return "workflow"
    if filename in {"Brewfile", ".tool-versions", "mise.toml", ".python-version"}:
        return "environment"
    if filename == "Cargo.toml":
        return "rust"
    if filename == "go.mod":
        return "go"
    return "other"


def parse_simple_toml(path: Path) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        try:
            values[key] = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            values[key] = value.strip('"')
    return values


def collect_automations(automations_root: Path) -> list[dict[str, Any]]:
    if not automations_root.exists():
        return []

    automations = []
    for path in sorted(automations_root.glob("*/automation.toml")):
        values = parse_simple_toml(path)
        automations.append(
            {
                "id": values.get("id", path.parent.name),
                "name": values.get("name", path.parent.name),
                "status": values.get("status", "UNKNOWN"),
                "rrule": values.get("rrule", ""),
                "path": str(path),
            }
        )
    return automations


def collect_skill_state(root: Path, skills_root: Path) -> dict[str, Any]:
    repo_local = sorted(path.parent.name for path in (root / "skills").glob("*/SKILL.md"))
    installed = sorted(path.parent.name for path in skills_root.glob("*/SKILL.md")) if skills_root.exists() else []
    return {
        "repo_local_skills": repo_local,
        "installed_skills": installed,
        "repo_local_count": len(repo_local),
        "installed_count": len(installed),
        "missing_installed_for_repo_source": sorted(set(repo_local) - set(installed)),
        "skills_root": str(skills_root),
    }


def collect_registered_repos(root: Path) -> list[dict[str, str]]:
    registry = root / "catalog" / "repo_registry.yaml"
    if not registry.exists():
        return []

    repos: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw_line in registry.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("- name: "):
            if current:
                repos.append(current)
            current = {"name": line.split(": ", 1)[1].strip("'\"")}
            continue
        if current is None:
            continue
        if line.startswith("path: "):
            current["path"] = line.split(": ", 1)[1].strip("'\"")
        elif line.startswith("branch: "):
            current["branch"] = line.split(": ", 1)[1].strip("'\"")
        elif line.startswith("remote_status: "):
            current["remote_status"] = line.split(": ", 1)[1].strip("'\"")
    if current:
        repos.append(current)
    return repos


def build_findings(
    toolchain: list[dict[str, Any]],
    automations: list[dict[str, Any]],
    skill_state: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    for tool in toolchain:
        if tool["status"] == "ok":
            continue
        severity = "blocker" if tool["required"] else "warning"
        findings.append(
            {
                "severity": severity,
                "id": f"tool_{tool['id']}_{tool['status']}",
                "message": f"{tool['id']} is {tool['status']}.",
                "evidence": tool.get("output") or "command not found",
                "next_step": tool.get("impact", ""),
            }
        )

    automation_by_id = {item["id"]: item for item in automations}
    devkit_watch = automation_by_id.get("aurora-dev-toolkit-watch")
    if devkit_watch and devkit_watch.get("status") != "ACTIVE":
        findings.append(
            {
                "severity": "warning",
                "id": "automation_aurora_dev_toolkit_watch_paused",
                "message": "aurora-dev-toolkit-watch exists but is not active.",
                "evidence": f"status={devkit_watch.get('status')}",
                "next_step": "Use a devkit watch lane for read-only drift detection, then apply package changes with explicit approval.",
            }
        )
    elif not devkit_watch:
        findings.append(
            {
                "severity": "warning",
                "id": "automation_aurora_dev_toolkit_watch_missing",
                "message": "No aurora-dev-toolkit-watch automation was found.",
                "evidence": "automation.toml absent under the configured automations root",
                "next_step": "Create a weekly read-only dev toolkit drift watch before enabling package-mutating updates.",
            }
        )

    if skill_state["missing_installed_for_repo_source"]:
        findings.append(
            {
                "severity": "warning",
                "id": "repo_local_skills_not_installed",
                "message": "Some repo-local skill sources are not installed into the machine-local Codex skills root.",
                "evidence": ", ".join(skill_state["missing_installed_for_repo_source"]),
                "next_step": "Run tools/sync_codex_skill.py for each intended skill and validate the installed package.",
            }
        )

    return findings


def build_report(
    root: Path,
    manifest_path: Path,
    skills_root: Path,
    automations_root: Path,
    runner: CommandRunner = run_command,
    generated_at: str | None = None,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    toolchain = scan_toolchain(manifest, runner=runner)
    automations = collect_automations(automations_root)
    skill_state = collect_skill_state(root, skills_root)
    package_manifests = discover_package_manifests(root, manifest)
    repos = collect_registered_repos(root)
    findings = build_findings(toolchain, automations, skill_state)
    install_plan = build_install_plan(manifest, toolchain)

    return {
        "schema_version": 1,
        "generated_at": generated_at or utc_now(),
        "root": str(root),
        "manifest_path": str(manifest_path),
        "toolkit_id": manifest["id"],
        "status": summarize_status(findings),
        "toolchain": toolchain,
        "package_manifests": package_manifests,
        "registered_repos": repos,
        "codex_skills": skill_state,
        "automations": automations,
        "findings": findings,
        "install_plan": install_plan,
        "validation_commands": manifest.get("validation_commands", []),
        "update_lanes": manifest.get("update_lanes", []),
    }


def summarize_status(findings: list[dict[str, str]]) -> str:
    if any(finding["severity"] == "blocker" for finding in findings):
        return "BLOCKED"
    if findings:
        return "WARN"
    return "READY"


def command_text(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def build_install_plan(manifest: dict[str, Any], toolchain: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tool_by_id = {tool["id"]: tool for tool in toolchain}
    recipes = {recipe["tool_id"]: recipe for recipe in manifest.get("install_recipes", [])}
    plan: list[dict[str, Any]] = []

    for tool in toolchain:
        if tool["status"] == "ok":
            continue
        recipe = recipes.get(tool["id"])
        if recipe is None:
            plan.append(
                {
                    "tool_id": tool["id"],
                    "lane": "unplanned",
                    "manager": "unknown",
                    "status": "unplanned",
                    "approval_required": True,
                    "blocked_by": [],
                    "install_command": [],
                    "install_command_text": "",
                    "update_command": [],
                    "update_command_text": "",
                    "notes": "No install recipe is defined in catalog/dev_toolkit_manifest.json.",
                }
            )
            continue

        blocked_by = [
            required
            for required in recipe.get("requires_tools", [])
            if tool_by_id.get(required, {}).get("status") != "ok"
        ]
        install_command = list(recipe.get("install_command", []))
        update_command = list(recipe.get("update_command", []))
        if blocked_by:
            status = "blocked"
        elif install_command:
            status = "ready"
        else:
            status = "manual"
        plan.append(
            {
                "tool_id": tool["id"],
                "lane": recipe.get("lane", "unknown"),
                "manager": recipe.get("manager", "unknown"),
                "status": status,
                "approval_required": bool(recipe.get("approval_required", True)),
                "blocked_by": blocked_by,
                "install_command": install_command,
                "install_command_text": command_text(install_command) if install_command else "",
                "update_command": update_command,
                "update_command_text": command_text(update_command) if update_command else "",
                "notes": recipe.get("notes", ""),
            }
        )

    return plan


def format_install_plan(report: dict[str, Any]) -> str:
    plan = report.get("install_plan", [])
    lines = ["Aurora Dev Toolkit Install Plan"]
    if not plan:
        lines.append("- No missing or broken tools were found.")
        return "\n".join(lines)

    for item in plan:
        lines.append(f"- [{item['status']}] {item['tool_id']} via {item['manager']} ({item['lane']})")
        if item.get("blocked_by"):
            lines.append(f"  blocked_by: {', '.join(item['blocked_by'])}")
        if item.get("install_command_text"):
            lines.append(f"  install: {item['install_command_text']}")
        if item.get("update_command_text"):
            lines.append(f"  update: {item['update_command_text']}")
        if item.get("notes"):
            lines.append(f"  notes: {item['notes']}")
    return "\n".join(lines)


def format_text_report(report: dict[str, Any]) -> str:
    counts = {
        "tools_ok": sum(1 for item in report["toolchain"] if item["status"] == "ok"),
        "tools_total": len(report["toolchain"]),
        "package_manifests": len(report["package_manifests"]),
        "registered_repos": len(report["registered_repos"]),
        "installed_skills": report["codex_skills"]["installed_count"],
        "automations": len(report["automations"]),
        "install_plan_items": len(report.get("install_plan", [])),
    }
    lines = [
        f"Aurora Dev Toolkit: {report['status']}",
        f"- Tools: {counts['tools_ok']}/{counts['tools_total']} ok",
        f"- Package manifests: {counts['package_manifests']}",
        f"- Registered repos: {counts['registered_repos']}",
        f"- Installed skills: {counts['installed_skills']}",
        f"- Automations: {counts['automations']}",
        f"- Install plan items: {counts['install_plan_items']}",
    ]
    if report["findings"]:
        lines.append("- Findings:")
        for finding in report["findings"]:
            lines.append(f"  - [{finding['severity']}] {finding['id']}: {finding['message']}")
    else:
        lines.append("- Findings: none")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit the Aurora developer toolkit surface.")
    parser.add_argument("--root", default=str(ROOT), help="Aurora root workspace path.")
    parser.add_argument("--manifest", help="Toolkit manifest path. Defaults to <root>/catalog/dev_toolkit_manifest.json.")
    parser.add_argument("--skills-root", default=str(DEFAULT_SKILLS_ROOT), help="Installed Codex skills root.")
    parser.add_argument("--automations-root", default=str(DEFAULT_AUTOMATIONS_ROOT), help="Codex automations root.")
    parser.add_argument("--json", action="store_true", dest="json_out", help="Print the full JSON report.")
    parser.add_argument("--install-plan", action="store_true", help="Print the approval-gated install plan instead of the summary.")
    parser.add_argument("--persist-report", action="store_true", help="Write reports/analysis/aurora_devkit_latest.json.")
    parser.add_argument("--persist-install-plan", action="store_true", help="Write reports/analysis/aurora_devkit_install_plan_latest.json.")
    parser.add_argument("--report-out", help="Write the JSON report to this path.")
    parser.add_argument("--fail-on-blocker", action="store_true", help="Exit non-zero when required tools are missing or broken.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    manifest_path = Path(args.manifest).expanduser().resolve() if args.manifest else root / "catalog" / "dev_toolkit_manifest.json"
    skills_root = Path(args.skills_root).expanduser().resolve()
    automations_root = Path(args.automations_root).expanduser().resolve()

    report = build_report(root, manifest_path, skills_root, automations_root)

    if args.persist_report:
        DEFAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if args.persist_install_plan:
        DEFAULT_INSTALL_PLAN.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_INSTALL_PLAN.write_text(json.dumps(report["install_plan"], indent=2) + "\n", encoding="utf-8")

    if args.report_out:
        report_out = Path(args.report_out).expanduser().resolve()
        report_out.parent.mkdir(parents=True, exist_ok=True)
        report_out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if args.json_out:
        print(json.dumps(report, indent=2))
    elif args.install_plan:
        print(format_install_plan(report))
    else:
        print(format_text_report(report))

    if args.fail_on_blocker and report["status"] == "BLOCKED":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

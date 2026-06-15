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
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "reports" / "analysis" / "aurora_devkit_latest.json"
DEFAULT_INSTALL_PLAN = ROOT / "reports" / "analysis" / "aurora_devkit_install_plan_latest.json"
DEFAULT_SKILLS_ROOT = Path("~/.codex/skills").expanduser()
DEFAULT_AUTOMATIONS_ROOT = Path("~/.codex/automations").expanduser()


CommandRunner = Callable[[list[str]], dict[str, Any]]
RepoCommandRunner = Callable[[Path, list[str]], dict[str, Any]]


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


def run_repo_command(repo_path: Path, args: list[str], timeout: int = 15) -> dict[str, Any]:
    command = list(args)
    executable = command[0]
    executable_path: str | None
    if os.sep in executable or (os.altsep and os.altsep in executable):
        candidate = Path(executable)
        if not candidate.is_absolute():
            candidate = repo_path / candidate
        if not candidate.exists():
            return {
                "status": "missing",
                "command": args,
                "path": str(candidate),
                "returncode": None,
                "output": "command not found",
            }
        executable_path = str(candidate)
        command[0] = executable_path
    else:
        executable_path = shutil.which(executable)
        if executable_path is None:
            return {
                "status": "missing",
                "command": args,
                "path": None,
                "returncode": None,
                "output": "command not found",
            }

    try:
        result = subprocess.run(  # noqa: S603 - fixed command probe against a local repo root.
            command,
            cwd=repo_path,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "command": args,
            "path": executable_path,
            "returncode": None,
            "output": "",
        }
    except OSError as exc:
        return {
            "status": "error",
            "command": args,
            "path": executable_path,
            "returncode": None,
            "output": str(exc),
        }

    output = result.stdout.strip() or result.stderr.strip()
    return {
        "status": "ok" if result.returncode == 0 else "error",
        "command": args,
        "path": executable_path,
        "returncode": result.returncode,
        "output": "\n".join(output.splitlines()[:8]),
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


def canonical_root_from_git(root: Path) -> Path | None:
    git = shutil.which("git")
    if git is None:
        return None
    try:
        result = subprocess.run(  # noqa: S603 - fixed git probe against a local repo root.
            [
                git,
                "-C",
                str(root),
                "rev-parse",
                "--path-format=absolute",
                "--git-common-dir",
            ],
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None

    git_common_dir = Path(result.stdout.strip())
    if git_common_dir.name != ".git":
        return None
    return git_common_dir.parent


def resolve_registered_repo_path(root: Path, repo_relpath: str) -> tuple[Path, str]:
    primary = root / repo_relpath
    if primary.exists():
        return primary, "root"

    canonical_root = canonical_root_from_git(root)
    if canonical_root and canonical_root != root:
        fallback = canonical_root / repo_relpath
        if fallback.exists():
            return fallback, "canonical_root"

    return primary, "missing"


def _import_probe(required_imports: list[str]) -> str:
    return (
        "import importlib, json; "
        f"names={required_imports!r}; "
        "versions={}; missing=[]; "
        "\nfor name in names:\n"
        "    try:\n"
        "        module = importlib.import_module(name)\n"
        "        versions[name] = getattr(module, '__version__', 'unknown')\n"
        "    except Exception as exc:\n"
        "        missing.append({'name': name, 'error': f'{type(exc).__name__}: {exc}'})\n"
        "print(json.dumps({'versions': versions, 'missing': missing}, sort_keys=True))"
    )


def collect_registered_python_envs(
    root: Path,
    manifest: dict[str, Any],
    registered_repos: list[dict[str, str]],
    runner: RepoCommandRunner = run_repo_command,
) -> list[dict[str, Any]]:
    repo_by_name = {repo["name"]: repo for repo in registered_repos}
    environments: list[dict[str, Any]] = []

    for check in manifest.get("registered_repo_python_environments", []):
        repo_name = check["repo_name"]
        repo = repo_by_name.get(repo_name)
        repo_relpath = check.get("repo_path") or (repo or {}).get("path", "")
        repo_path, path_resolution = (
            resolve_registered_repo_path(root, repo_relpath)
            if repo_relpath
            else (root, "root")
        )
        venv_path = check.get("venv_path", ".venv")
        python_command = check.get("python_command", [f"{venv_path}/bin/python"])
        required = bool(check.get("required", False))
        required_imports = list(check.get("required_imports", []))
        status_file = check.get("status_file")

        env: dict[str, Any] = {
            "repo_name": repo_name,
            "path": repo_relpath,
            "required": required,
            "venv_path": venv_path,
            "python_command": python_command,
            "resolved_path": str(repo_path),
            "path_resolution": path_resolution,
            "required_imports": required_imports,
            "update_command": check.get("update_command", []),
            "post_update_commands": check.get("post_update_commands", []),
            "auto_update_lane": check.get("auto_update_lane", ""),
            "status_file": status_file,
            "status": "ok",
            "checks": {},
            "notes": check.get("notes", ""),
        }

        if repo is None:
            env["status"] = "missing"
            env["evidence"] = "repo not present in catalog/repo_registry.yaml"
            environments.append(env)
            continue
        if not repo_path.exists():
            env["status"] = "missing"
            env["evidence"] = "registered repo path does not exist"
            environments.append(env)
            continue

        version_check = runner(repo_path, [*python_command, "--version"])
        pip_check = runner(repo_path, [*python_command, "-m", "pip", "--version"])
        import_check = runner(repo_path, [*python_command, "-c", _import_probe(required_imports)]) if required_imports else {
            "status": "ok",
            "command": [],
            "path": None,
            "returncode": 0,
            "output": json.dumps({"versions": {}, "missing": []}),
        }
        dependency_check = runner(repo_path, [*python_command, "-m", "pip", "check"])

        env["checks"] = {
            "python_version": version_check,
            "pip_version": pip_check,
            "required_imports": import_check,
            "pip_check": dependency_check,
        }

        failing = [
            name
            for name, result in env["checks"].items()
            if result.get("status") != "ok"
        ]
        try:
            import_result = json.loads(import_check.get("output", "{}"))
        except json.JSONDecodeError:
            import_result = {"versions": {}, "missing": [{"name": "parse", "error": "invalid import probe output"}]}
        env["import_versions"] = import_result.get("versions", {})
        env["missing_imports"] = import_result.get("missing", [])
        if env["missing_imports"]:
            failing.append("required_imports")

        if status_file:
            status_path = repo_path / status_file
            if not status_path.exists():
                env["status_file_state"] = "missing"
            else:
                try:
                    status_payload = json.loads(status_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    status_payload = {}
                    env["status_file_state"] = "invalid"
                else:
                    actual_python = version_check.get("output", "")
                    actual_pip = pip_check.get("output", "")
                    expected_venv_path = status_payload.get("venv_path")
                    stale_reasons = []
                    if status_payload.get("python_version") != actual_python:
                        stale_reasons.append("python_version")
                    if status_payload.get("pip_version") != actual_pip:
                        stale_reasons.append("pip_version")
                    if expected_venv_path != venv_path:
                        stale_reasons.append("venv_path")
                    env["status_file_state"] = "stale" if stale_reasons else "ok"
                    env["status_file_stale_fields"] = stale_reasons

        if failing:
            env["status"] = "blocked" if required else "warn"
            env["evidence"] = ", ".join(sorted(set(failing)))
        elif env.get("status_file_state") in {"missing", "invalid", "stale"}:
            env["status"] = "warn"
            env["evidence"] = f"{status_file} is {env['status_file_state']}"

        environments.append(env)

    return environments


def _clean_yaml_scalar(value: str) -> str:
    value = value.split("#", 1)[0].strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_dependabot_updates(path: Path) -> list[dict[str, str]]:
    updates: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    in_directories = False

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- package-ecosystem:"):
            if current:
                updates.append(current)
            current = {
                "package_ecosystem": _clean_yaml_scalar(stripped.split(":", 1)[1]),
                "directory": "",
            }
            in_directories = False
            continue
        if current is None:
            continue
        if stripped.startswith("directory:"):
            current["directory"] = _clean_yaml_scalar(stripped.split(":", 1)[1])
            in_directories = False
            continue
        if stripped.startswith("directories:"):
            in_directories = True
            continue
        if in_directories and stripped.startswith("- "):
            updates.append(
                {
                    "package_ecosystem": current["package_ecosystem"],
                    "directory": _clean_yaml_scalar(stripped[2:]),
                }
            )
            continue
        if in_directories and not stripped.startswith("- "):
            in_directories = False

    if current:
        updates.append(current)
    return updates


def _repo_context(root: Path, repo_name: str, registered_repos: list[dict[str, str]]) -> tuple[str, Path, str] | None:
    if repo_name == "root":
        return ".", root, "root control plane"
    repo_by_name = {repo["name"]: repo for repo in registered_repos}
    repo = repo_by_name.get(repo_name)
    if not repo:
        return None
    repo_relpath = repo.get("path", "")
    return repo_relpath, root / repo_relpath, repo.get("branch", "")


def collect_dependency_update_surfaces(
    root: Path,
    manifest: dict[str, Any],
    registered_repos: list[dict[str, str]],
) -> list[dict[str, Any]]:
    surfaces: list[dict[str, Any]] = []

    for surface in manifest.get("dependency_update_surfaces", []):
        repo_name = surface["repo_name"]
        context = _repo_context(root, repo_name, registered_repos)
        required = bool(surface.get("required", False))
        config_path = surface.get("path", ".github/dependabot.yml")
        expected_updates = [
            {
                "package_ecosystem": item["package_ecosystem"],
                "directory": item["directory"],
            }
            for item in surface.get("expected_updates", [])
        ]

        record: dict[str, Any] = {
            "id": surface["id"],
            "repo_name": repo_name,
            "repo_path": "",
            "path": config_path,
            "required": required,
            "status": "ok",
            "expected_updates": expected_updates,
            "actual_updates": [],
            "missing_updates": [],
            "notes": surface.get("notes", ""),
        }

        if context is None:
            record["status"] = "missing"
            record["evidence"] = "repo not present in catalog/repo_registry.yaml"
            surfaces.append(record)
            continue

        repo_relpath, repo_path, _branch = context
        repo_path, path_resolution = (
            resolve_registered_repo_path(root, repo_relpath)
            if repo_relpath != "."
            else (repo_path, "root")
        )
        record["repo_path"] = repo_relpath
        record["resolved_path"] = str(repo_path)
        record["path_resolution"] = path_resolution
        dependabot_path = repo_path / config_path
        if not dependabot_path.exists():
            record["status"] = "missing"
            record["evidence"] = f"{config_path} does not exist"
            surfaces.append(record)
            continue

        actual_updates = parse_dependabot_updates(dependabot_path)
        actual_pairs = {(item["package_ecosystem"], item["directory"]) for item in actual_updates}
        missing_updates = [
            item
            for item in expected_updates
            if (item["package_ecosystem"], item["directory"]) not in actual_pairs
        ]
        record["actual_updates"] = sorted(actual_updates, key=lambda item: (item["package_ecosystem"], item["directory"]))
        record["missing_updates"] = missing_updates
        if missing_updates:
            record["status"] = "warn"
            record["evidence"] = ", ".join(
                f"{item['package_ecosystem']}:{item['directory']}" for item in missing_updates
            )
        surfaces.append(record)

    return surfaces


def build_findings(
    toolchain: list[dict[str, Any]],
    automations: list[dict[str, Any]],
    skill_state: dict[str, Any],
    python_envs: list[dict[str, Any]] | None = None,
    dependency_update_surfaces: list[dict[str, Any]] | None = None,
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

    for env in python_envs or []:
        if env.get("status") == "ok":
            continue
        severity = "blocker" if env.get("required") and env.get("status") == "blocked" else "warning"
        findings.append(
            {
                "severity": severity,
                "id": f"repo_python_env_{env['repo_name']}_{env.get('status', 'unknown')}",
                "message": f"{env['repo_name']} Python environment is {env.get('status', 'unknown')}.",
                "evidence": env.get("evidence", ""),
                "next_step": env.get("notes") or "Use the repo-local virtual environment for validation.",
            }
        )

    for surface in dependency_update_surfaces or []:
        if surface.get("status") == "ok":
            continue
        findings.append(
            {
                "severity": "warning",
                "id": f"dependency_update_surface_{surface['id']}_{surface.get('status', 'unknown')}",
                "message": f"{surface['repo_name']} dependency update surface is {surface.get('status', 'unknown')}.",
                "evidence": surface.get("evidence", ""),
                "next_step": surface.get("notes") or "Update .github/dependabot.yml coverage for this repo.",
            }
        )

    return findings


def build_report(
    root: Path,
    manifest_path: Path,
    skills_root: Path,
    automations_root: Path,
    runner: CommandRunner = run_command,
    repo_runner: RepoCommandRunner = run_repo_command,
    generated_at: str | None = None,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    toolchain = scan_toolchain(manifest, runner=runner)
    automations = collect_automations(automations_root)
    skill_state = collect_skill_state(root, skills_root)
    package_manifests = discover_package_manifests(root, manifest)
    repos = collect_registered_repos(root)
    python_envs = collect_registered_python_envs(root, manifest, repos, runner=repo_runner)
    dependency_update_surfaces = collect_dependency_update_surfaces(root, manifest, repos)
    findings = build_findings(toolchain, automations, skill_state, python_envs, dependency_update_surfaces)
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
        "registered_python_environments": python_envs,
        "dependency_update_surfaces": dependency_update_surfaces,
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
        "dependency_update_surfaces": len(report.get("dependency_update_surfaces", [])),
        "installed_skills": report["codex_skills"]["installed_count"],
        "automations": len(report["automations"]),
        "install_plan_items": len(report.get("install_plan", [])),
    }
    lines = [
        f"Aurora Dev Toolkit: {report['status']}",
        f"- Tools: {counts['tools_ok']}/{counts['tools_total']} ok",
        f"- Package manifests: {counts['package_manifests']}",
        f"- Registered repos: {counts['registered_repos']}",
        f"- Dependency update surfaces: {counts['dependency_update_surfaces']}",
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

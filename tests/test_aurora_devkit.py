from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import aurora_devkit  # noqa: E402


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_discover_package_manifests_prunes_installed_dependency_trees(tmp_path: Path) -> None:
    manifest = {
        "package_manifest_names": ["package.json", "pyproject.toml", "requirements.txt"],
        "prune_directory_names": [".git", ".venv", "node_modules"],
    }
    write_file(tmp_path / "package.json", "{}\n")
    write_file(tmp_path / "app" / "pyproject.toml", "{}\n")
    write_file(tmp_path / "app" / "node_modules" / "dep" / "package.json", "{}\n")
    write_file(tmp_path / ".venv" / "lib" / "python3.11" / "site-packages" / "dep" / "pyproject.toml", "{}\n")

    discovered = aurora_devkit.discover_package_manifests(tmp_path, manifest)
    paths = {item["path"] for item in discovered}

    assert paths == {"app/pyproject.toml", "package.json"}


def test_parse_simple_toml_reads_automation_fields(tmp_path: Path) -> None:
    automation = tmp_path / "automation.toml"
    write_file(
        automation,
        'id = "aurora-dev-toolkit-watch"\n'
        'name = "Aurora Dev Toolkit Watch"\n'
        'status = "ACTIVE"\n'
        'cwds = ["/workspace"]\n',
    )

    parsed = aurora_devkit.parse_simple_toml(automation)

    assert parsed["id"] == "aurora-dev-toolkit-watch"
    assert parsed["status"] == "ACTIVE"
    assert parsed["cwds"] == ["/workspace"]


def test_build_report_flags_missing_tools_and_missing_devkit_watch(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    skills_root = tmp_path / "skills"
    automations_root = tmp_path / "automations"
    root.mkdir()
    skills_root.mkdir()
    write_file(root / "skills" / "agent-dispatcher" / "SKILL.md", "# Agent Dispatcher\n")
    write_file(skills_root / "agent-dispatcher" / "SKILL.md", "# Agent Dispatcher\n")
    automations_root.mkdir()
    write_file(
        root / "catalog" / "repo_registry.yaml",
        "repos:\n- name: example\n  path: repos/example\n  branch: main\n  remote_status: configured\n",
    )
    manifest_path = root / "catalog" / "dev_toolkit_manifest.json"
    write_file(
        manifest_path,
        json.dumps(
            {
                "id": "aurora-dev-toolkit",
                "package_manifest_names": ["package.json"],
                "prune_directory_names": [],
                "toolchain": [
                    {
                        "id": "git",
                        "required": True,
                        "category": "source-control",
                        "command": ["git", "--version"],
                        "impact": "required",
                    },
                    {
                        "id": "ruff",
                        "required": False,
                        "category": "quality",
                        "command": ["ruff", "--version"],
                        "impact": "recommended",
                    },
                ],
            }
        )
        + "\n",
    )

    def fake_runner(args: list[str]) -> dict[str, Any]:
        if args[0] == "git":
            return {"status": "ok", "command": args, "path": "/usr/bin/git", "returncode": 0, "output": "git version test"}
        return {"status": "missing", "command": args, "path": None, "returncode": None, "output": ""}

    report = aurora_devkit.build_report(
        root,
        manifest_path,
        skills_root,
        automations_root,
        runner=fake_runner,
        generated_at="2026-05-16T00:00:00Z",
    )

    finding_ids = {finding["id"] for finding in report["findings"]}
    assert report["status"] == "WARN"
    assert "tool_ruff_missing" in finding_ids
    assert "automation_aurora_dev_toolkit_watch_missing" in finding_ids
    assert report["install_plan"][0]["tool_id"] == "ruff"
    assert report["install_plan"][0]["status"] == "unplanned"
    assert report["registered_repos"] == [{"name": "example", "path": "repos/example", "branch": "main", "remote_status": "configured"}]


def test_build_install_plan_marks_user_space_recipe_ready_when_manager_exists() -> None:
    manifest = {
        "install_recipes": [
            {
                "tool_id": "ruff",
                "lane": "python-user",
                "manager": "uv-tool",
                "requires_tools": ["uv"],
                "approval_required": True,
                "install_command": ["uv", "tool", "install", "ruff"],
                "update_command": ["uv", "tool", "upgrade", "ruff"],
                "notes": "Install Ruff.",
            }
        ]
    }
    toolchain = [
        {"id": "uv", "status": "ok"},
        {"id": "ruff", "status": "missing"},
    ]

    plan = aurora_devkit.build_install_plan(manifest, toolchain)

    assert plan == [
        {
            "tool_id": "ruff",
            "lane": "python-user",
            "manager": "uv-tool",
            "status": "ready",
            "approval_required": True,
            "blocked_by": [],
            "install_command": ["uv", "tool", "install", "ruff"],
            "install_command_text": "uv tool install ruff",
            "update_command": ["uv", "tool", "upgrade", "ruff"],
            "update_command_text": "uv tool upgrade ruff",
            "notes": "Install Ruff.",
        }
    ]

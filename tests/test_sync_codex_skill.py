from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import sync_codex_skill  # noqa: E402


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_skill(root: Path, name: str, script_body: str = "print('ok')\n") -> Path:
    skill_root = root / name
    write_file(skill_root / "SKILL.md", f"---\nname: {name}\n---\n")
    write_file(skill_root / "agents" / "openai.yaml", "interface:\n  display_name: Example\n")
    write_file(skill_root / "scripts" / "example.py", script_body)
    return skill_root


def test_sync_skill_copies_files_and_removes_stale_paths(tmp_path: Path) -> None:
    source = make_skill(tmp_path / "source", "example-skill")
    destination = make_skill(tmp_path / "installed", "example-skill", script_body="print('old')\n")
    write_file(destination / "obsolete.txt", "remove me\n")

    report = sync_codex_skill.sync_skill(source, destination)

    assert report["status"] == "synced"
    assert "scripts/example.py" in report["changed_paths"]
    assert report["removed_paths"] == ["obsolete.txt"]
    assert not (destination / "obsolete.txt").exists()
    assert (destination / "scripts" / "example.py").read_text(encoding="utf-8") == "print('ok')\n"


def test_sync_skill_dry_run_is_non_mutating(tmp_path: Path) -> None:
    source = make_skill(tmp_path / "source", "example-skill")
    destination = make_skill(tmp_path / "installed", "example-skill", script_body="print('old')\n")

    report = sync_codex_skill.sync_skill(source, destination, dry_run=True)

    assert report["status"] == "dry_run"
    assert "scripts/example.py" in report["changed_paths"]
    assert (destination / "scripts" / "example.py").read_text(encoding="utf-8") == "print('old')\n"


def test_run_package_validation_uses_installed_validator(tmp_path: Path) -> None:
    skills_root = tmp_path / "skills"
    validator = skills_root / "aurora-skill-finder" / "scripts" / "validate_skill_package.py"
    write_file(
        validator,
        (
            "#!/usr/bin/env python3\n"
            "import json\n"
            "print(json.dumps({'status': 'ok', 'summary': {'skill_count': 1}}))\n"
        ),
    )

    report = sync_codex_skill.run_package_validation(skills_root)

    assert report["status"] == "ok"
    assert report["summary"]["skill_count"] == 1
    assert report["_returncode"] == 0


def test_cli_reports_sync_and_validation(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo_root = tmp_path / "repo"
    skills_root = tmp_path / "codex-skills"
    make_skill(repo_root / "skills", "example-skill")
    validator = skills_root / "aurora-skill-finder" / "scripts" / "validate_skill_package.py"
    write_file(
        validator,
        (
            "#!/usr/bin/env python3\n"
            "import json\n"
            "print(json.dumps({'status': 'ok'}))\n"
        ),
    )

    exit_code = sync_codex_skill.main(
        [
            "--repo-root",
            str(repo_root),
            "--skills-root",
            str(skills_root),
            "--skill",
            "example-skill",
            "--validate-package",
        ]
    )
    report = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert report["status"] == "synced"
    assert report["validation"]["status"] == "ok"
    assert (skills_root / "example-skill" / "SKILL.md").exists()

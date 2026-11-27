from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import sync_skills
import workspace_verify


def test_verifier_checks_requested_workspace_skills(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    skill = root / "skills" / "example" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("new content")
    installed = tmp_path / "installed"
    registry = root / "catalog" / "skill_sync_targets.yaml"
    registry.parent.mkdir()
    registry.write_text(json.dumps({"targets": [{"name": "isolated", "dest": str(installed), "enabled": True}]}))

    findings = workspace_verify.verify_skill_sync(root)
    assert len(findings) == 1  # nosec B101 - pytest assertion, not runtime enforcement
    assert "isolated" in findings[0].details  # nosec B101 - pytest assertion
    assert not installed.exists(), "Drift checking must remain read-only"  # nosec B101 - pytest assertion

    destination = installed / "example" / "SKILL.md"
    destination.parent.mkdir(parents=True)
    destination.write_text("new content")
    assert workspace_verify.verify_skill_sync(root) == []  # nosec B101 - pytest assertion


def test_empty_explicit_skill_selection_does_not_check_other_skills(tmp_path: Path) -> None:
    (tmp_path / "skills").mkdir()
    assert sync_skills.collect_drift(targets=[], skills=[], root=tmp_path) == {}  # nosec B101 - pytest assertion


def test_scoped_sync_adds_updates_and_preserves_dry_run(tmp_path: Path) -> None:
    source = tmp_path / "source"
    skill = source / "example" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("first")
    destination = tmp_path / "installed"
    result = sync_skills.sync_skill("example", destination, dry_run=True, source_root=source)
    assert result["changes"] == ["add: SKILL.md"]  # nosec B101 - pytest assertion
    assert not destination.exists()  # nosec B101 - pytest assertion
    sync_skills.sync_skill("example", destination, dry_run=False, source_root=source)
    skill.write_text("second")
    result = sync_skills.sync_skill("example", destination, dry_run=True, source_root=source)
    assert result["changes"] == ["update: SKILL.md"]  # nosec B101 - pytest assertion
    assert (destination / "example" / "SKILL.md").read_text() == "first"  # nosec B101 - pytest assertion
    sync_skills.sync_skill("example", destination, dry_run=False, source_root=source)
    result = sync_skills.sync_skill("example", destination, source_root=source)
    assert result["status"] == "up-to-date"  # nosec B101 - pytest assertion

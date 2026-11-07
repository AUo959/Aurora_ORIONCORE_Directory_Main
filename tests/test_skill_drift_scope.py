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
    assert len(findings) == 1
    assert "isolated" in findings[0].details
    assert not installed.exists(), "Drift checking must remain read-only"

    destination = installed / "example" / "SKILL.md"
    destination.parent.mkdir(parents=True)
    destination.write_text("new content")
    assert workspace_verify.verify_skill_sync(root) == []


def test_empty_explicit_skill_selection_does_not_check_other_skills(tmp_path: Path) -> None:
    (tmp_path / "skills").mkdir()
    assert sync_skills.collect_drift(targets=[], skills=[], root=tmp_path) == {}

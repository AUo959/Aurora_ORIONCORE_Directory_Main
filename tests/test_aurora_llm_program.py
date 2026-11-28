"""Tests for the Aurora LLM program registry, steward definitions, and status tool."""

from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import aurora_llm_program_status as status  # noqa: E402

PROGRAM = REPO_ROOT / "catalog" / "aurora_llm_program.json"
CHARTER = REPO_ROOT / "docs" / "AURORA_LLM_PROGRAM_CHARTER_v1.md"
SKILL_MD = REPO_ROOT / "skills" / "aurora-llm-steward" / "SKILL.md"
OPENAI_YAML = REPO_ROOT / "skills" / "aurora-llm-steward" / "agents" / "openai.yaml"
CLAUDE_AGENT = REPO_ROOT / ".claude" / "agents" / "aurora-llm-steward.md"

CATALOG_SAMPLE = '''
    CAPABILITIES = {
        AIModel.FRESH: ModelCapabilities(
            model=AIModel.FRESH,
            verified_on="2026-11-07",
            verified_source="pricing-docs",
        ),
        AIModel.STALE: ModelCapabilities(
            model=AIModel.STALE,
            verified_on="2026-01-01",
            verified_source="pricing-docs",
        ),
        AIModel.RETIRED: ModelCapabilities(
            model=AIModel.RETIRED,
            available=False,  # shut down
            verified_on="2025-01-01",
            verified_source="pricing-docs",
        ),
        AIModel.PLACEHOLDER: ModelCapabilities(
            model=AIModel.PLACEHOLDER,
            verified_on="",
            verified_source="unverified",
        ),
    }
'''


def _frontmatter(path: Path) -> dict[str, str]:
    match = re.match(r"---\n(?P<body>.*?)\n---\n", path.read_text(encoding="utf-8"), re.DOTALL)
    assert match, f"{path} must start with YAML frontmatter"
    out: dict[str, str] = {}
    for line in match.group("body").splitlines():
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip()
    return out


def _copy_root(tmp_path: Path) -> Path:
    root = tmp_path / "root"
    for rel in (status.PROGRAM_PATH, status.CONTRACT_PATH, status.SESSION_STATE_PATH):
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO_ROOT / rel, dest)
    return root


def test_registry_points_at_existing_root_surfaces() -> None:
    program = json.loads(PROGRAM.read_text(encoding="utf-8"))
    for rel in (program["charter"], *program["steward"].values()):
        assert (REPO_ROOT / rel).exists(), rel
    for track in program["tracks"]:
        if track["primary_repo"] == "Aurora_ORIONCORE_Directory_Main":
            for surface in track["surfaces"]:
                assert (REPO_ROOT / surface).exists(), surface


def test_registry_task_ids_exist_in_session_state() -> None:
    program = json.loads(PROGRAM.read_text(encoding="utf-8"))
    state = json.loads((REPO_ROOT / status.SESSION_STATE_PATH).read_text(encoding="utf-8"))
    known = {item["id"] for item in state.get("task_queue", [])}
    known |= {item["id"] for item in state.get("completed_tasks", [])}
    for track in program["tracks"]:
        for task_id in track["task_ids"]:
            assert task_id in known, task_id


def test_skill_and_agent_definitions_agree() -> None:
    skill = _frontmatter(SKILL_MD)
    agent = _frontmatter(CLAUDE_AGENT)
    assert skill["name"] == agent["name"] == "aurora-llm-steward"
    assert skill["description"] and agent["description"]
    assert "$aurora-llm-steward" in OPENAI_YAML.read_text(encoding="utf-8")
    agent_text = CLAUDE_AGENT.read_text(encoding="utf-8")
    assert "skills/aurora-llm-steward/SKILL.md" in agent_text
    assert "docs/AURORA_LLM_PROGRAM_CHARTER_v1.md" in agent_text


def test_charter_keeps_the_governing_rule_and_owner_gates() -> None:
    text = CHARTER.read_text(encoding="utf-8")
    assert "Models reason; Aurora governs." in text
    for gate in ("G0", "G1", "G1.5", "G2", "G3", "G4", "G5"):
        assert f"| {gate} |" in text
    assert "authorizing any model training run" in text


def test_parse_catalog_reads_availability_and_claims() -> None:
    entries = {e["model"]: e for e in status.parse_catalog(CATALOG_SAMPLE)}
    assert set(entries) == {"FRESH", "STALE", "RETIRED", "PLACEHOLDER"}
    assert entries["RETIRED"]["available"] is False
    assert entries["FRESH"]["verified_on"] == "2026-11-07"
    assert entries["PLACEHOLDER"]["verified_source"] == "unverified"


def test_catalog_findings_flag_stale_and_unverified_available_entries() -> None:
    entries = status.parse_catalog(CATALOG_SAMPLE)
    findings = status._catalog_findings(entries, date(2026, 11, 28), 90)
    actions = [f.message for f in findings if f.severity == "action"]
    assert any("STALE" in m for m in actions)
    assert any("PLACEHOLDER" in m for m in actions)
    assert not any("FRESH" in m or "RETIRED" in m for m in actions)


def test_report_on_repo_has_no_action_findings_without_cloudbank() -> None:
    report = status.build_report(REPO_ROOT, None, date(2026, 11, 28))
    assert not report.needs_action, [f.message for f in report.findings]
    assert report.asm["model_training_authorized"] is False
    assert report.asm["next_adoption_step"]
    assert any("not checked" in f.message for f in report.findings)


def test_training_flag_flip_is_flagged(tmp_path: Path) -> None:
    root = _copy_root(tmp_path)
    contract_path = root / status.CONTRACT_PATH
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract["first_slice"]["model_training_authorized"] = True
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    report = status.build_report(root, None, date(2026, 11, 28))
    assert report.needs_action
    assert any(f.track == "T2" and "training" in f.message for f in report.findings)


def test_missing_task_id_is_flagged(tmp_path: Path) -> None:
    root = _copy_root(tmp_path)
    program_path = root / status.PROGRAM_PATH
    program = json.loads(program_path.read_text(encoding="utf-8"))
    program["tracks"][0]["task_ids"].append("does-not-exist")
    program_path.write_text(json.dumps(program), encoding="utf-8")
    report = status.build_report(root, None, date(2026, 11, 28))
    assert any("does-not-exist" in f.message for f in report.findings if f.severity == "action")


def test_cli_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert status.main(["--today", "2026-11-28", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["needs_action"] is False
    assert status.main(["--root", str(tmp_path / "missing")]) == 2

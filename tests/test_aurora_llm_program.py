"""Tests for the Aurora LLM program registry, steward definitions, and status tool."""

from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO

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
    if not match:
        raise AssertionError(f"{path} must start with YAML frontmatter")
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


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


TODAY = date(2026, 11, 28)


class RegistryTests(unittest.TestCase):
    def test_registry_points_at_existing_root_surfaces(self) -> None:
        program = _load(PROGRAM)
        for rel in (program["charter"], *program["steward"].values()):
            self.assertTrue((REPO_ROOT / rel).exists(), rel)
        for track in program["tracks"]:
            if track["primary_repo"] == "Aurora_ORIONCORE_Directory_Main":
                for surface in track["surfaces"]:
                    self.assertTrue((REPO_ROOT / surface).exists(), surface)

    def test_registry_task_ids_exist_in_session_state(self) -> None:
        program = _load(PROGRAM)
        state = _load(REPO_ROOT / status.SESSION_STATE_PATH)
        known = {item["id"] for item in state.get("task_queue", [])}
        known |= {item["id"] for item in state.get("completed_tasks", [])}
        for track in program["tracks"]:
            for task_id in track["task_ids"]:
                self.assertIn(task_id, known)

    def test_skill_and_agent_definitions_agree(self) -> None:
        skill = _frontmatter(SKILL_MD)
        agent = _frontmatter(CLAUDE_AGENT)
        self.assertEqual(skill["name"], "aurora-llm-steward")
        self.assertEqual(agent["name"], "aurora-llm-steward")
        self.assertTrue(skill["description"] and agent["description"])
        self.assertIn("$aurora-llm-steward", OPENAI_YAML.read_text(encoding="utf-8"))
        agent_text = CLAUDE_AGENT.read_text(encoding="utf-8")
        self.assertIn("skills/aurora-llm-steward/SKILL.md", agent_text)
        self.assertIn("docs/AURORA_LLM_PROGRAM_CHARTER_v1.md", agent_text)

    def test_charter_keeps_the_governing_rule_and_owner_gates(self) -> None:
        text = CHARTER.read_text(encoding="utf-8")
        self.assertIn("Models reason; Aurora governs.", text)
        for gate in ("G0", "G1", "G1.5", "G2", "G3", "G4", "G5"):
            self.assertIn(f"| {gate} |", text)
        self.assertIn("authorizing any model training run", text)


class CatalogTests(unittest.TestCase):
    def test_parse_catalog_reads_availability_and_claims(self) -> None:
        entries = {e["model"]: e for e in status.parse_catalog(CATALOG_SAMPLE)}
        self.assertEqual(set(entries), {"FRESH", "STALE", "RETIRED", "PLACEHOLDER"})
        self.assertFalse(entries["RETIRED"]["available"])
        self.assertEqual(entries["FRESH"]["verified_on"], "2026-11-07")
        self.assertEqual(entries["PLACEHOLDER"]["verified_source"], "unverified")

    def test_catalog_findings_flag_stale_and_unverified_available_entries(self) -> None:
        findings = status._catalog_findings(status.parse_catalog(CATALOG_SAMPLE), TODAY, 90)
        actions = [f.message for f in findings if f.severity == "action"]
        self.assertTrue(any("STALE" in m for m in actions))
        self.assertTrue(any("PLACEHOLDER" in m for m in actions))
        self.assertFalse(any("FRESH" in m or "RETIRED" in m for m in actions))

    def test_no_available_model_is_flagged(self) -> None:
        findings = status._catalog_findings([], TODAY, 90)
        self.assertEqual([f.severity for f in findings], ["action"])


class ReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_report_on_repo_has_no_action_findings_without_cloudbank(self) -> None:
        report = status.build_report(REPO_ROOT, None, TODAY)
        self.assertFalse(report.needs_action, [f.message for f in report.findings])
        self.assertFalse(report.asm["model_training_authorized"])
        self.assertTrue(report.asm["next_adoption_step"])
        self.assertTrue(any("not checked" in f.message for f in report.findings))
        self.assertIn("## Tracks", status.render_markdown(report))

    def test_training_flag_flip_is_flagged(self) -> None:
        root = _copy_root(self.tmp_path)
        contract_path = root / status.CONTRACT_PATH
        contract = _load(contract_path)
        contract["first_slice"]["model_training_authorized"] = True
        contract_path.write_text(json.dumps(contract), encoding="utf-8")
        report = status.build_report(root, None, TODAY)
        self.assertTrue(report.needs_action)
        self.assertTrue(any(f.track == "T2" and "training" in f.message for f in report.findings))

    def test_missing_task_id_is_flagged(self) -> None:
        root = _copy_root(self.tmp_path)
        program_path = root / status.PROGRAM_PATH
        program = _load(program_path)
        program["tracks"][0]["task_ids"].append("does-not-exist")
        program_path.write_text(json.dumps(program), encoding="utf-8")
        report = status.build_report(root, None, TODAY)
        actions = [f.message for f in report.findings if f.severity == "action"]
        self.assertTrue(any("does-not-exist" in m for m in actions))

    def test_cli_exit_codes(self) -> None:
        out = StringIO()
        with redirect_stdout(out):
            code = status.main(["--today", "2026-11-28", "--json"])
        self.assertEqual(code, 0)
        self.assertFalse(json.loads(out.getvalue())["needs_action"])
        self.assertEqual(status.main(["--root", str(self.tmp_path / "missing")]), 2)


if __name__ == "__main__":
    unittest.main()

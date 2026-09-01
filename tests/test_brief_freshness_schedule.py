"""Brief cadence had no scheduler; this pins the one added, and the flag it needs.

The interesting failure here is not "the workflow file went missing". It is the
one found while writing it: `--check` alone returns 0 at the warn threshold and
exits 1 only at the blocking one, so a scheduler keyed on exit status would have
stayed silent until commits were already being blocked. That is an incident
notification wearing a warning's name.

So the load-bearing assertion is behavioural — that --exit-on-warn actually
changes the exit code at the warn tier — plus a guard that the workflow really
passes it. A test that only checked the file exists would have passed against
the broken version.
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/brief-freshness.yml"
SCAFFOLD = ROOT / "tools/brief_scaffold.py"


def load_workflow() -> dict:
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    # PyYAML parses the bare key `on:` as the boolean True.
    if True in data:
        data["on"] = data.pop(True)
    return data


class BriefFreshnessScheduleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(
            WORKFLOW.is_file(),
            "the scheduled brief-freshness workflow is the whole point of the "
            "automate-executive-brief item; without it cadence is manual again",
        )
        self.workflow = load_workflow()
        self.steps = self.workflow["jobs"]["check"]["steps"]
        self.run_blocks = "\n".join(
            step.get("run", "") for step in self.steps
        )

    def test_runs_on_a_schedule(self) -> None:
        triggers = self.workflow["on"]
        self.assertIn(
            "schedule", triggers,
            "a workflow_dispatch-only workflow is still human-triggered, which "
            "is the condition being fixed",
        )
        crons = [entry["cron"] for entry in triggers["schedule"]]
        self.assertTrue(crons)
        for cron in crons:
            self.assertEqual(
                5, len(cron.split()), f"malformed cron expression: {cron!r}"
            )

    def test_checks_at_the_warn_tier_not_the_blocking_one(self) -> None:
        self.assertIn(
            "--exit-on-warn", self.run_blocks,
            "without this flag the check exits 0 until the blocking threshold, "
            "so the schedule would alert only once commits are blocked",
        )

    def test_has_the_permission_its_steps_require(self) -> None:
        permissions = self.workflow["permissions"]
        if "gh issue" in self.run_blocks:
            self.assertEqual(
                "write", permissions.get("issues"),
                "steps call `gh issue` but the job lacks issues: write; the "
                "step would fail at runtime, and a scheduled job's failure is "
                "exactly the thing nobody is watching",
            )

    def test_does_not_commit_generated_artifacts(self) -> None:
        # `make brief` regenerates governance artifacts. Running that in CI
        # would leave changes needing a commit, and the Stop hook set this
        # repo's precedent by being advisory-only. Report, do not write.
        for forbidden in ("git commit", "git push", "--persist-report"):
            self.assertNotIn(
                forbidden, self.run_blocks,
                f"scheduled check should not {forbidden!r}; it reports",
            )

    def test_pins_actions_to_shas(self) -> None:
        for step in self.steps:
            uses = step.get("uses")
            if uses:
                ref = uses.split("@", 1)[1]
                self.assertEqual(
                    40, len(ref),
                    f"{uses} is not pinned to a full commit SHA",
                )

    def test_checkout_has_history_to_count_with(self) -> None:
        checkout = next(
            step for step in self.steps
            if step.get("uses", "").startswith("actions/checkout@")
        )
        self.assertEqual(
            0, checkout.get("with", {}).get("fetch-depth"),
            "freshness is measured in commits since the newest brief; a "
            "shallow clone cannot count them. This is the same defect class as "
            "the ACE manifest clone-depth failure.",
        )


class ExitOnWarnBehaviourTests(unittest.TestCase):
    """Drive the real tool rather than asserting on its source."""

    def _run(self, ahead: int, *extra: str) -> int:
        # Patch only the commit count, leaving every threshold and branch of the
        # real --check logic intact, then call the real main().
        argv = ["brief_scaffold.py", "--check", *extra]
        harness = "\n".join([
            "import sys, importlib.util",
            "from pathlib import Path",
            f"sys.argv = {argv!r}",
            f"spec = importlib.util.spec_from_file_location('bs', {str(SCAFFOLD)!r})",
            "mod = importlib.util.module_from_spec(spec)",
            "spec.loader.exec_module(mod)",
            "mod.newest_brief = lambda: Path('executive_brief__2026-01-01.md')",
            f"mod.commits_since = lambda brief: {ahead}",
            "mod.EXEMPT_FILE = Path('/nonexistent-exemption')",
            "sys.exit(mod.main())",
        ])
        proc = subprocess.run(
            [sys.executable, "-c", harness],
            capture_output=True, text=True, cwd=ROOT,
        )
        self.assertNotIn(
            "Traceback", proc.stderr,
            f"harness itself failed rather than exercising the tool:\n{proc.stderr}",
        )
        return proc.returncode

    def test_warn_tier_is_silent_without_the_flag(self) -> None:
        self.assertEqual(0, self._run(61))

    def test_warn_tier_signals_with_the_flag(self) -> None:
        self.assertEqual(1, self._run(61, "--exit-on-warn"))

    def test_blocking_tier_signals_either_way(self) -> None:
        self.assertEqual(1, self._run(151))
        self.assertEqual(1, self._run(151, "--exit-on-warn"))

    def test_healthy_repo_stays_quiet(self) -> None:
        # Guards against the flag turning into an always-on alarm, which people
        # learn to ignore and which would make the schedule worse than nothing.
        self.assertEqual(0, self._run(3, "--exit-on-warn"))


if __name__ == "__main__":
    unittest.main()

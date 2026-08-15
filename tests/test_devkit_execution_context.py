"""Devkit findings must distinguish "missing here" from "missing".

The defect
----------
Devkit findings describe the machine the scan RAN ON, but nothing recorded
which machine that was. Run from a sandboxed container, `gh is missing` was
emitted as a blocker and surfaced by Mission Control as a P1 — a fact about the
container presented as a fact about the workspace. The 2026-08-10 executive
brief traced four of Mission Control's five P1s to exactly this, and `gh`
answered instantly when the same check ran on the owner's Mac. The same blind
spot inflated publication debt with `PR state UNVERIFIED (gh unavailable)`.

A checker whose loudest output is routinely wrong is worse than no checker: it
trains people to scroll past P1s.

The chosen asymmetry
--------------------
Detection is strict — canonical means exactly ``~/dev/Aurora_ORIONCORE_Directory_Main``.
Anything else is treated as possibly-sandboxed and demoted to a warning.

That direction is deliberate. A false NON-canonical verdict demotes a real
problem to a warning: still reported, still visible, just not blocking. A false
CANONICAL verdict would let a throwaway clone raise blockers about its own
missing tooling. Given a checker that already cried wolf, the demotion is the
safer error — and this is the precedent workspace_verify set for
``repo_registry_coverage``, where "unavailable in this execution context" is a
warning while "exists on disk but unregistered" stays an error.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

from aurora_devkit import build_findings, is_canonical_workspace_context  # noqa: E402


def _tool(status: str = "missing", required: bool = True) -> dict:
    return {
        "id": "gh",
        "status": status,
        "required": required,
        "output": "command not found",
        "impact": "GitHub operations unavailable.",
    }


def _env(status: str = "blocked", required: bool = True) -> dict:
    return {
        "repo_name": "aurora-cloudbank-symbolic-main",
        "status": status,
        "required": required,
        "evidence": "interpreter not executable here",
        "notes": "Use the repo-local virtual environment.",
    }


def _findings(monkeypatch, *, canonical: bool, **kwargs) -> list[dict]:
    import aurora_devkit
    monkeypatch.setattr(
        aurora_devkit, "is_canonical_workspace_context", lambda *a, **k: canonical
    )
    return [
        f
        for f in build_findings(
            toolchain=kwargs.get("toolchain", []),
            # A watch automation is supplied so the fixture does not emit the
            # unrelated "no dev-toolkit-watch" warning and muddy the assertions.
            automations=[{"id": "aurora-dev-toolkit-watch", "status": "ACTIVE"}],
            skill_state={"missing_installed_for_repo_source": []},
            python_envs=kwargs.get("python_envs", []),
        )
        # Keep only the findings under test; build_findings also reports on
        # dependency surfaces, which these cases do not exercise.
        if f["id"].startswith(("tool_", "repo_python_env_"))
    ]


# --- the detector ---------------------------------------------------------

def test_canonical_path_is_recognised():
    assert is_canonical_workspace_context(
        Path.home() / "dev" / "Aurora_ORIONCORE_Directory_Main"
    )


def test_sandbox_mount_is_not_canonical():
    assert not is_canonical_workspace_context(
        Path("/sessions/abc/mnt/Aurora_ORIONCORE_Directory_Main")
    )


def test_lookalike_suffix_is_not_canonical():
    """A suffix match would accept this; anchoring to $HOME must not.

    Regression cover for the first version, which tested
    ``endswith("/dev/Aurora_ORIONCORE_Directory_Main")`` and therefore treated a
    throwaway clone under /tmp as the owner's workspace.
    """
    assert not is_canonical_workspace_context(
        Path("/tmp/dev/Aurora_ORIONCORE_Directory_Main")
    )


# --- severity behaviour ---------------------------------------------------

def test_missing_required_tool_blocks_on_the_canonical_workspace(monkeypatch):
    """The check must still bite where it means something."""
    findings = _findings(monkeypatch, canonical=True, toolchain=[_tool()])
    assert len(findings) == 1
    assert findings[0]["severity"] == "blocker"
    assert findings[0]["execution_context"] == "canonical"
    assert "execution context" not in findings[0]["message"]


def test_missing_required_tool_is_only_a_warning_elsewhere(monkeypatch):
    findings = _findings(monkeypatch, canonical=False, toolchain=[_tool()])
    assert len(findings) == 1
    assert findings[0]["severity"] == "warning"
    assert findings[0]["execution_context"] == "non_canonical"
    assert "non-canonical workspace path" in findings[0]["message"]


def test_demoted_findings_are_still_reported(monkeypatch):
    """Demotion must not become suppression — the finding still exists."""
    findings = _findings(monkeypatch, canonical=False, toolchain=[_tool()])
    assert findings, "a demoted finding must still be emitted, not dropped"
    assert "Re-check from the canonical workspace path" in findings[0]["next_step"]


def test_blocked_python_env_follows_the_same_rule(monkeypatch):
    """The CloudBank venv is a macOS build; a Linux sandbox cannot run it."""
    blocking = _findings(monkeypatch, canonical=True, python_envs=[_env()])
    demoted = _findings(monkeypatch, canonical=False, python_envs=[_env()])
    assert blocking[0]["severity"] == "blocker"
    assert demoted[0]["severity"] == "warning"
    assert "non-canonical workspace path" in demoted[0]["message"]


def test_non_required_tool_never_blocks_in_either_context(monkeypatch):
    """Optional tooling was never a blocker and must not become one."""
    for canonical in (True, False):
        findings = _findings(
            monkeypatch, canonical=canonical, toolchain=[_tool(required=False)]
        )
        assert findings[0]["severity"] == "warning"


def test_healthy_tool_emits_nothing(monkeypatch):
    assert _findings(monkeypatch, canonical=False, toolchain=[_tool(status="ok")]) == []

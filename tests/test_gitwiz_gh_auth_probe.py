from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "skills" / "gitwiz-github-manager" / "scripts" / "gitwiz_gh_auth_probe.py"

_SPEC = importlib.util.spec_from_file_location("gitwiz_gh_auth_probe", MODULE_PATH)
assert _SPEC and _SPEC.loader
gitwiz_gh_auth_probe = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(gitwiz_gh_auth_probe)


def completed(args: list[str], stdout: str = "", stderr: str = "", returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=args, returncode=returncode, stdout=stdout, stderr=stderr)


def test_probe_reports_missing_gh(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gitwiz_gh_auth_probe.shutil, "which", lambda _name: None)

    payload = gitwiz_gh_auth_probe.probe_gh_auth()

    assert payload["status"] == "gh_missing"
    assert "Install GitHub CLI" in payload["next_step"]


def test_probe_does_not_call_failed_auth_a_broken_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gitwiz_gh_auth_probe.shutil, "which", lambda _name: "/usr/local/bin/gh")

    def fake_run_command(args: list[str], cwd: Path | None = None):
        assert args == ["gh", "auth", "status"]
        return completed(args, stderr="invalid token", returncode=1)

    monkeypatch.setattr(gitwiz_gh_auth_probe, "run_command", fake_run_command)

    payload = gitwiz_gh_auth_probe.probe_gh_auth()

    assert payload["status"] == "auth_failed_in_current_context"
    assert "sandbox failure is not proof" in payload["next_step"]
    assert "broken" in payload["next_step"]
    assert "gh auth logout" in payload["next_step"]
    assert "gh auth login" in payload["next_step"]


def test_probe_reports_usable_auth_and_repo_access(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gitwiz_gh_auth_probe.shutil, "which", lambda _name: "/usr/local/bin/gh")
    calls: list[list[str]] = []

    def fake_run_command(args: list[str], cwd: Path | None = None):
        calls.append(args)
        if args == ["gh", "auth", "status"]:
            return completed(args, stdout="github.com\n  ✓ Logged in")
        if args == ["gh", "api", "user", "--jq", ".login"]:
            return completed(args, stdout="AUo959\n")
        if args == ["gh", "pr", "list", "--repo", "AUo959/example", "--limit", "1", "--json", "number"]:
            return completed(args, stdout="[]\n")
        raise AssertionError(f"unexpected args: {args}")

    monkeypatch.setattr(gitwiz_gh_auth_probe, "run_command", fake_run_command)

    payload = gitwiz_gh_auth_probe.probe_gh_auth(repo="AUo959/example")

    assert payload["status"] == "usable"
    assert payload["login"] == "AUo959"
    assert calls[-1][0:3] == ["gh", "pr", "list"]

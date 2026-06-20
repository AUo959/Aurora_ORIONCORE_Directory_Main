from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "tools" / "publication_debt.py"

_SPEC = importlib.util.spec_from_file_location("publication_debt", MODULE_PATH)
assert _SPEC and _SPEC.loader
publication_debt = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(publication_debt)


def test_scan_repo_treats_failed_gh_as_context_unverified(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"

    def fake_git(repo_arg: Path, *args: str) -> str:
        assert repo_arg == repo
        command = tuple(args)
        if command == ("rev-parse", "--verify", "-q", "origin/main"):
            return "origin/main"
        if command == ("status", "--porcelain"):
            return ""
        if command == ("for-each-ref", "refs/heads", "--format=%(refname:short)"):
            return "feature/no-pr"
        if command == ("rev-list", "--left-right", "--count", "origin/main...feature/no-pr"):
            return "0\t1"
        if command == ("rev-parse", "--verify", "-q", "refs/remotes/origin/feature/no-pr"):
            return "origin/feature/no-pr"
        raise AssertionError(f"unexpected git args: {args}")

    monkeypatch.setattr(publication_debt, "_git", fake_git)
    monkeypatch.setattr(publication_debt, "_branch_has_open_pr", lambda repo_arg, branch: None)

    debts = publication_debt.scan_repo("root", repo)

    assert len(debts) == 1
    assert debts[0]["class"] == "unpublished_branch"
    assert "current execution context" in debts[0]["detail"]
    assert "make gh-auth-check" in debts[0]["remediation"]
    assert "token as broken" in debts[0]["remediation"]

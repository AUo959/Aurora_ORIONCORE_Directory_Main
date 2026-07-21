"""Tests for tools/registry_sync_heads.py (nested-repo pin refresh)."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "registry_sync_heads", ROOT / "tools" / "registry_sync_heads.py"
)
rsh = importlib.util.module_from_spec(SPEC)
sys.modules["registry_sync_heads"] = rsh
SPEC.loader.exec_module(rsh)

SAMPLE = """generated_at: '2026-07-21T00:00:00Z'
root: .
repos:
- name: AlphaRepo
  path: nested/alpha
  branch: main
  head_sha: 1111111111111111111111111111111111111111
  remote_status: configured
  validation_command: env -u GIT_DIR git -C nested/alpha rev-parse HEAD && env -u
    GIT_DIR git -C nested/alpha status --short --branch
  move_policy: frozen_until_registry_adoption
- name: RemoteOnly
  path: ~remote~
  branch: main
  head_sha: ~pending~
  remote_status: remote_only
"""


def test_parse_registry_captures_fields_and_line_numbers():
    repos, order = rsh.parse_registry(SAMPLE)
    assert order == ["AlphaRepo", "RemoteOnly"]
    assert repos["AlphaRepo"]["path"] == "nested/alpha"
    assert repos["AlphaRepo"]["head_sha"].startswith("1111")
    # line index must point at the head_sha line so surgical edits land correctly
    line = SAMPLE.splitlines()[repos["AlphaRepo"]["_line_head_sha"]]
    assert "head_sha:" in line


def test_placeholder_pins_are_recognised():
    assert rsh.PLACEHOLDER.match("~pending~")
    assert rsh.PLACEHOLDER.match("~remote~")
    assert not rsh.PLACEHOLDER.match("1111111111111111111111111111111111111111")


def test_folded_validation_command_is_not_treated_as_a_field():
    """Continuation lines of a folded YAML scalar must not parse as repo keys."""
    repos, _ = rsh.parse_registry(SAMPLE)
    assert "GIT_DIR" not in repos["AlphaRepo"]
    assert repos["AlphaRepo"]["validation_command"].startswith("env -u GIT_DIR")


def _git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture()
def workspace(tmp_path, monkeypatch):
    """A miniature workspace: a registry plus one real nested git repo."""
    nested = tmp_path / "nested" / "alpha"
    nested.mkdir(parents=True)
    _git(["init", "-q"], nested)
    _git(["config", "user.email", "t@example.com"], nested)
    _git(["config", "user.name", "T"], nested)
    (nested / "f.txt").write_text("hello")
    _git(["add", "-A"], nested)
    _git(["commit", "-qm", "init"], nested)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=nested, capture_output=True, text=True
    ).stdout.strip()

    registry = tmp_path / "catalog" / "repo_registry.yaml"
    registry.parent.mkdir(parents=True)
    registry.write_text(SAMPLE)

    monkeypatch.setattr(rsh, "ROOT", tmp_path)
    monkeypatch.setattr(rsh, "REGISTRY", registry)
    return tmp_path, registry, head


def test_check_mode_detects_drift_and_never_writes(workspace, monkeypatch, capsys):
    _, registry, head = workspace
    before = registry.read_text()
    monkeypatch.setattr(sys, "argv", ["registry_sync_heads.py", "--check"])
    assert rsh.main() == 1  # drift present → non-zero for hooks/CI
    assert registry.read_text() == before  # check mode is read-only
    assert "STALE" in capsys.readouterr().out


def test_apply_updates_only_the_head_sha_line(workspace, monkeypatch):
    _, registry, head = workspace
    before = registry.read_text()
    monkeypatch.setattr(sys, "argv", ["registry_sync_heads.py"])
    assert rsh.main() == 0
    after = registry.read_text()

    assert head in after
    assert "1111111111111111111111111111111111111111" not in after
    # exactly one line differs — formatting and every other field preserved
    diff = [
        (a, b)
        for a, b in zip(before.splitlines(), after.splitlines())
        if a != b
    ]
    assert len(diff) == 1
    assert "head_sha:" in diff[0][1]
    # the placeholder repo is untouched
    assert "head_sha: ~pending~" in after


def test_apply_is_idempotent(workspace, monkeypatch):
    _, registry, _ = workspace
    monkeypatch.setattr(sys, "argv", ["registry_sync_heads.py"])
    rsh.main()
    once = registry.read_text()
    rsh.main()
    assert registry.read_text() == once


def test_check_passes_once_pins_are_current(workspace, monkeypatch):
    _, _, _ = workspace
    monkeypatch.setattr(sys, "argv", ["registry_sync_heads.py"])
    rsh.main()
    monkeypatch.setattr(sys, "argv", ["registry_sync_heads.py", "--check"])
    assert rsh.main() == 0

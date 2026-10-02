"""Read-only and missing-checkout behavior of the status adapter."""
import importlib.util
import json
import shutil
import subprocess  # nosec B404
import unittest
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
SPEC = importlib.util.spec_from_file_location(
    "aurora_session_status", ROOT / "tools/AURORA__TOOL__SESSION_STATUS__v0.1__2026-10-02.py")
STATUS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STATUS)
CHECK = unittest.TestCase()
GIT = shutil.which("git")
NOW = datetime(2026, 10, 2, 22, tzinfo=timezone.utc)


def workspace(tmp_path):
    (tmp_path / "catalog").mkdir()
    (tmp_path / "catalog/session_state.json").write_text(json.dumps({
        "schema_version": 3, "last_updated": NOW.isoformat(), "active_task": None,
        "task_queue": []}))
    (tmp_path / "catalog/repo_registry.yaml").write_text(
        "repos:\n- name: aurora-cloudbank-symbolic-main\n  path: nested\n  head_sha: abc\n")
    return tmp_path


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_missing_checkout_is_not_a_match_and_does_not_write(tmp_path):
    root = workspace(tmp_path)
    before = snapshot(root)
    data = STATUS.build_report(root, NOW)
    CHECK.assertTrue(data["cloudbank"]["status"] == "unavailable")
    CHECK.assertTrue(data["claim_scope"] == "local_only")
    CHECK.assertTrue(data["target_source"] == "root_default")
    CHECK.assertTrue(snapshot(root) == before)


def test_plain_directory_is_not_nested_git_checkout(tmp_path):
    root = workspace(tmp_path)
    # Fixed fixture argv, temporary checkout only; shell=False.
    # Reviewed argv boundary: fixed verbs, resolved executable, separate path, no shell.
    # nosemgrep
    subprocess.run([GIT, "init", str(root)], check=True, capture_output=True)  # noqa: S603  # nosec B603
    (root / "nested").mkdir()
    CHECK.assertTrue(STATUS.build_report(root, NOW)["cloudbank"]["observed_head"] is None)


def test_outside_registry_path_is_never_probed(tmp_path, monkeypatch):
    root = workspace(tmp_path)
    (root / "catalog/repo_registry.yaml").write_text(
        "repos:\n- name: aurora-cloudbank-symbolic-main\n  path: ../outside\n  head_sha: abc\n")
    calls = []
    monkeypatch.setattr(STATUS, "git_value", lambda path, *args: calls.append(path) or None)
    STATUS.build_report(root, NOW)
    CHECK.assertTrue(calls == [root])


def test_stale_invalid_claims_and_waits_are_visible(tmp_path):
    root = workspace(tmp_path)
    claims = root / "catalog/session_claims"
    claims.mkdir()
    (claims / "broken.json").write_text("{")
    (claims / "expired.json").write_text(json.dumps({
        "status": "active", "expires_at": "2026-01-01T00:00:00Z"}))
    state_path = root / "catalog/session_state.json"
    state = json.loads(state_path.read_text())
    state.update(last_updated="2026-09-01T00:00:00Z", active_task={
        "id": "current", "repo": "root", "next_step": "Inspect receipt"}, task_queue=[
        {"id": "authority", "repo": "root", "status": "waiting"},
        {"id": "other", "repo": "CanonRec", "status": "waiting"}])
    state_path.write_text(json.dumps(state))
    data = STATUS.build_report(root, NOW)
    CHECK.assertTrue(data["claims"]["stale"] == 1)
    CHECK.assertTrue(data["claims"]["invalid"] == 1)
    CHECK.assertTrue(data["waiting_items"] == ["authority"])
    CHECK.assertTrue(data["next_action"] == "Inspect receipt")
    CHECK.assertTrue(any("24h" in w for w in data["warnings"]))


def test_malformed_sources_degrade_to_unknown(tmp_path):
    root = workspace(tmp_path)
    (root / "catalog/session_state.json").write_text("[]")
    (root / "catalog/repo_registry.yaml").write_text("[]")
    data = STATUS.build_report(root, NOW)
    CHECK.assertTrue(data["target_source"] == "root_default")
    CHECK.assertTrue(len(data["warnings"]) >= 3)


def test_real_checkout_pin_match_and_drift_ignore_git_environment(tmp_path, monkeypatch):
    root = workspace(tmp_path)
    nested = root / "nested"
    # Fixed fixture argv, temporary checkout only; shell=False.
    # Reviewed argv boundary: fixed verbs, resolved executable, separate path, no shell.
    # nosemgrep
    subprocess.run([GIT, "init", str(nested)], check=True, capture_output=True)  # noqa: S603  # nosec B603
    # Fixed fixture argv, temporary checkout only; shell=False.
    # Reviewed argv boundary: fixed verbs, resolved executable, separate path, no shell.
    # nosemgrep
    subprocess.run([GIT, "-C", str(nested), "-c", "user.name=Test",  # noqa: S603  # nosec B603
                    "-c", "user.email=test@example.invalid", "commit", "--allow-empty", "-m", "fixture"],
                   check=True, capture_output=True)
    # Reviewed argv boundary: fixed verbs, resolved executable, separate path, no shell.
    # nosemgrep
    sha = subprocess.check_output([GIT, "-C", str(nested), "rev-parse", "HEAD"], text=True).strip()  # noqa: S603  # nosec B603
    registry = root / "catalog/repo_registry.yaml"
    registry.write_text(f"repos:\n- name: aurora-cloudbank-symbolic-main\n  path: nested\n  head_sha: {sha}\n")
    monkeypatch.setenv("GIT_DIR", "/missing-git-dir")
    before = snapshot(root)
    CHECK.assertTrue(STATUS.build_report(root, NOW)["cloudbank"]["status"] == "match")
    CHECK.assertTrue(snapshot(root) == before)
    registry.write_text(registry.read_text().replace(sha, "wrong-pin"))
    CHECK.assertTrue(STATUS.build_report(root, NOW)["cloudbank"]["status"] == "drift")


def test_mod_host_contract():
    import pytest
    node = shutil.which("node")
    if not node:
        pytest.skip("Node is required for the Claude mod host contract")
    # Fixed fixture argv, temporary checkout only; shell=False.
    # Reviewed argv boundary: fixed verbs, resolved executable, separate path, no shell.
    # nosemgrep
    subprocess.run([node, str(ROOT / "plugins/aurora-session-status/tests/"  # noqa: S603  # nosec B603
                    "AURORA__TEST__MOD_HOST__v0.1__2026-10-02.mjs")], check=True)


def test_git_reader_rejects_mutating_verbs(tmp_path):
    with CHECK.assertRaises(ValueError):
        STATUS.git_value(tmp_path, "checkout", "main")

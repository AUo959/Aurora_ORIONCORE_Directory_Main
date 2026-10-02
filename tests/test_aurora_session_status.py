"""Read-only and missing-checkout behavior of the status adapter."""
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
SPEC = importlib.util.spec_from_file_location(
    "aurora_session_status", ROOT / "tools/AURORA__TOOL__SESSION_STATUS__v0.1__2026-10-02.py")
STATUS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(STATUS)
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
    assert data["cloudbank"]["status"] == "unavailable"
    assert data["claim_scope"] == "local_only"
    assert data["target_source"] == "root_default"
    assert snapshot(root) == before


def test_plain_directory_is_not_nested_git_checkout(tmp_path):
    root = workspace(tmp_path)
    subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
    (root / "nested").mkdir()
    assert STATUS.build_report(root, NOW)["cloudbank"]["observed_head"] is None


def test_outside_registry_path_is_never_probed(tmp_path, monkeypatch):
    root = workspace(tmp_path)
    (root / "catalog/repo_registry.yaml").write_text(
        "repos:\n- name: aurora-cloudbank-symbolic-main\n  path: ../outside\n  head_sha: abc\n")
    calls = []
    monkeypatch.setattr(STATUS, "git_value", lambda path, *args: calls.append(path) or None)
    STATUS.build_report(root, NOW)
    assert calls == [root]


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
    assert data["claims"]["stale"] == 1
    assert data["claims"]["invalid"] == 1
    assert data["waiting_items"] == ["authority"]
    assert data["next_action"] == "Inspect receipt"
    assert any("24h" in w for w in data["warnings"])


def test_malformed_sources_degrade_to_unknown(tmp_path):
    root = workspace(tmp_path)
    (root / "catalog/session_state.json").write_text("[]")
    (root / "catalog/repo_registry.yaml").write_text("[]")
    data = STATUS.build_report(root, NOW)
    assert data["target_source"] == "root_default"
    assert len(data["warnings"]) >= 3


def test_real_checkout_pin_match_and_drift_ignore_git_environment(tmp_path, monkeypatch):
    root = workspace(tmp_path)
    nested = root / "nested"
    subprocess.run(["git", "init", str(nested)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(nested), "-c", "user.name=Test",
                    "-c", "user.email=test@example.invalid", "commit", "--allow-empty", "-m", "fixture"],
                   check=True, capture_output=True)
    sha = subprocess.check_output(["git", "-C", str(nested), "rev-parse", "HEAD"], text=True).strip()
    registry = root / "catalog/repo_registry.yaml"
    registry.write_text(f"repos:\n- name: aurora-cloudbank-symbolic-main\n  path: nested\n  head_sha: {sha}\n")
    monkeypatch.setenv("GIT_DIR", "/missing-git-dir")
    before = snapshot(root)
    assert STATUS.build_report(root, NOW)["cloudbank"]["status"] == "match"
    assert snapshot(root) == before
    registry.write_text(registry.read_text().replace(sha, "wrong-pin"))
    assert STATUS.build_report(root, NOW)["cloudbank"]["status"] == "drift"


def test_mod_host_contract():
    import shutil
    import pytest
    if not shutil.which("node"):
        pytest.skip("Node is required for the Claude mod host contract")
    subprocess.run(["node", str(ROOT / "plugins/aurora-session-status/tests/"
                    "AURORA__TEST__MOD_HOST__v0.1__2026-10-02.mjs")], check=True)

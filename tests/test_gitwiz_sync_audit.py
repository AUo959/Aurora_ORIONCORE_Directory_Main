from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "skills" / "gitwiz-github-manager" / "scripts" / "gitwiz_sync_audit.py"
SPEC = importlib.util.spec_from_file_location("gitwiz_sync_audit", MODULE_PATH)
assert SPEC and SPEC.loader
gitwiz_sync_audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gitwiz_sync_audit)


def test_repo_hygiene_uses_repo_specific_thresholds() -> None:
    policy = gitwiz_sync_audit.merge_policy(
        gitwiz_sync_audit.DEFAULT_HYGIENE_POLICY,
        {
            "repos": {
                "aurora-cloudbank-symbolic-main": {
                    "warning": {"behind_commits": 10},
                    "critical": {"behind_commits": 50, "deleted_files": 10, "status_entries": 20},
                }
            }
        },
    )

    summary = {
        "name": "aurora-cloudbank-symbolic-main",
        "exists": True,
        "remotes": {"origin": {"fetch": "git@example.com:aurora-cloudbank-symbolic.git"}},
        "branch": "main",
        "sync_state": "dirty",
        "dirty": True,
        "ahead": 3,
        "behind": 120,
        "status_counts": {
            "modified": 2,
            "added": 0,
            "deleted": 15,
            "renamed": 0,
            "copied": 0,
            "unmerged": 0,
            "untracked": 6,
            "other": 0,
        },
    }

    repo_policy = gitwiz_sync_audit.repo_hygiene_policy(policy, summary["name"])
    hygiene = gitwiz_sync_audit.evaluate_hygiene(summary, repo_policy)
    metrics = {breach["metric"]: breach["level"] for breach in hygiene["breaches"]}

    assert hygiene["status"] == "critical"
    assert metrics["behind_commits"] == "critical"
    assert metrics["deleted_files"] == "critical"
    assert metrics["status_entries"] == "critical"
    assert metrics["dirty_main"] == "warning"


def test_clean_repo_is_hygiene_ok() -> None:
    summary = {
        "name": "CanonRec",
        "exists": True,
        "remotes": {"origin": {"fetch": "git@example.com:CanonRec.git"}},
        "branch": "main",
        "sync_state": "in_sync",
        "dirty": False,
        "ahead": 0,
        "behind": 0,
        "status_counts": {
            "modified": 0,
            "added": 0,
            "deleted": 0,
            "renamed": 0,
            "copied": 0,
            "unmerged": 0,
            "untracked": 0,
            "other": 0,
        },
    }

    repo_policy = gitwiz_sync_audit.repo_hygiene_policy(gitwiz_sync_audit.DEFAULT_HYGIENE_POLICY, summary["name"])
    hygiene = gitwiz_sync_audit.evaluate_hygiene(summary, repo_policy)

    assert hygiene["status"] == "ok"
    assert hygiene["breaches"] == []


def test_should_fail_respects_requested_threshold() -> None:
    assert gitwiz_sync_audit.should_fail("ok", "warning") is False
    assert gitwiz_sync_audit.should_fail("warning", "warning") is True
    assert gitwiz_sync_audit.should_fail("warning", "critical") is False
    assert gitwiz_sync_audit.should_fail("critical", "critical") is True

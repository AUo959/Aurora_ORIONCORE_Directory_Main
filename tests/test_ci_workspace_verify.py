from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import ci_workspace_verify  # noqa: E402
import workspace_verify  # noqa: E402


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def commit_file(root: Path, message: str, text: str) -> str:
    path = root / "feature.txt"
    path.write_text(text, encoding="utf-8")
    git(root, "add", "feature.txt")
    git(root, "commit", "-m", message)
    return git(root, "rev-parse", "HEAD")


def build_repo(tmp_path: Path, *, base_extra_commits: int = 0) -> tuple[Path, str]:
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-b", "main")
    git(root, "config", "user.email", "ci@example.com")
    git(root, "config", "user.name", "Aurora CI")
    git(root, "config", "commit.gpgsign", "false")

    (root / "catalog").mkdir()
    (root / "README.md").write_text("# fixture\n", encoding="utf-8")
    git(root, "add", "README.md")
    git(root, "commit", "-m", "initial")
    known_sha = git(root, "rev-parse", "HEAD")

    state = {"known_state": {"main_sha": known_sha}}
    (root / "catalog" / "session_state.json").write_text(
        json.dumps(state, indent=2) + "\n",
        encoding="utf-8",
    )
    git(root, "add", "catalog/session_state.json")
    git(root, "commit", "-m", "record handoff")

    for index in range(base_extra_commits):
        commit_file(root, f"base {index}", f"base {index}\n")

    base_sha = git(root, "rev-parse", "HEAD")
    git(root, "update-ref", "refs/remotes/origin/main", base_sha)
    return root, base_sha


def make_synthetic_pr_merge(root: Path, *, feature_commits: int = 12, edit_session_state: bool = False) -> None:
    base_sha = git(root, "rev-parse", "refs/remotes/origin/main")
    git(root, "checkout", "-b", "feature", base_sha)
    for index in range(feature_commits):
        commit_file(root, f"feature {index}", f"feature {index}\n")

    if edit_session_state:
        state_path = root / "catalog" / "session_state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["note"] = "PR edits coordination state"
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        git(root, "add", "catalog/session_state.json")
        git(root, "commit", "-m", "edit session state")

    git(root, "checkout", "main")
    git(root, "merge", "--no-ff", "feature", "-m", "synthetic PR merge")


def blocking_freshness() -> workspace_verify.Finding:
    return workspace_verify.error(
        "session_state_freshness",
        "session state appears stale against synthetic HEAD",
        "refresh session state",
    )


def pr_env() -> dict[str, str]:
    return {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_BASE_REF": "main"}


def test_unchanged_session_state_ignores_feature_and_synthetic_merge_commits(tmp_path: Path) -> None:
    root, _ = build_repo(tmp_path)
    make_synthetic_pr_merge(root, feature_commits=12)

    adjusted = ci_workspace_verify.adjust_pr_session_state_freshness(
        root,
        [blocking_freshness()],
        pr_env(),
    )

    assert adjusted == []


def test_genuinely_stale_default_branch_still_blocks_in_pr_context(tmp_path: Path) -> None:
    root, _ = build_repo(tmp_path, base_extra_commits=10)
    make_synthetic_pr_merge(root, feature_commits=2)

    adjusted = ci_workspace_verify.adjust_pr_session_state_freshness(
        root,
        [blocking_freshness()],
        pr_env(),
    )

    assert len(adjusted) == 1
    assert adjusted[0].check == "session_state_freshness"
    assert adjusted[0].blocking is True
    assert "authoritative PR base" in adjusted[0].details


def test_pr_that_modifies_session_state_cannot_use_pr_base_exception(tmp_path: Path) -> None:
    root, _ = build_repo(tmp_path)
    make_synthetic_pr_merge(root, feature_commits=12, edit_session_state=True)
    original = blocking_freshness()

    adjusted = ci_workspace_verify.adjust_pr_session_state_freshness(
        root,
        [original],
        pr_env(),
    )

    assert adjusted == [original]


def test_non_pr_context_keeps_standard_workspace_verifier_result(tmp_path: Path) -> None:
    root, _ = build_repo(tmp_path)
    make_synthetic_pr_merge(root, feature_commits=12)
    original = blocking_freshness()

    adjusted = ci_workspace_verify.adjust_pr_session_state_freshness(
        root,
        [original],
        {"GITHUB_EVENT_NAME": "push", "GITHUB_BASE_REF": ""},
    )

    assert adjusted == [original]

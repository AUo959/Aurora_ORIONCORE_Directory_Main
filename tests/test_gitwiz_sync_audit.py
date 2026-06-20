from __future__ import annotations

import builtins
import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "skills" / "gitwiz-github-manager" / "scripts" / "gitwiz_sync_audit.py"

_SPEC = importlib.util.spec_from_file_location("gitwiz_sync_audit", MODULE_PATH)
assert _SPEC and _SPEC.loader
gitwiz_sync_audit = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(gitwiz_sync_audit)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def copy_repo_file(source_relative: str, destination_root: Path) -> None:
    source = REPO_ROOT / source_relative
    destination = destination_root / source_relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def completed(args: list[str], stdout: str = "", returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["git", *args], returncode=returncode, stdout=stdout, stderr="")


def test_repo_rows_from_payload_raises_on_invalid_rows() -> None:
    payload = {
        "repos": [
            {"name": "root", "path": "."},
            "bad-row",
            17,
            {"name": "nested", "path": "Nested/Repo"},
        ]
    }

    with pytest.raises(ValueError, match="index\\(es\\): 1, 2"):
        gitwiz_sync_audit.repo_rows_from_payload(payload)


def test_load_repo_registry_reads_json_compatible_payload(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    registry_path = workspace_root / "catalog" / "repo_registry.yaml"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        '{"repos": [{"name": "nested", "path": "Nested/Repo"}]}\n',
        encoding="utf-8",
    )

    rows = gitwiz_sync_audit.load_repo_registry(workspace_root)

    assert rows == [{"name": "nested", "path": "Nested/Repo"}]


def test_nested_repo_selection_works_without_pyyaml(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    copy_repo_file("tools/_workspace_common.py", workspace_root)
    write_file(
        workspace_root / "catalog" / "repo_registry.yaml",
        """generated_at: '2026-03-10T00:00:00Z'
root: .
repos:
- name: aurora-cloudbank-symbolic-main
  path: GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main
  branch: main
  head_sha: 42e0b9fb9f1e0e10a9091d595cf2811f2c14eacf
  remote_status: configured
  validation_command: env -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE -u GIT_PREFIX
    git -C GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main rev-parse
    HEAD && env -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE -u GIT_PREFIX git -C
    GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main status --short
    --branch
  move_policy: frozen_until_registry_adoption
""",
    )

    original_import = builtins.__import__

    def blocked_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "yaml":
            raise ImportError("yaml disabled for test")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)

    repo_registry = gitwiz_sync_audit.load_repo_registry(workspace_root)
    targets = gitwiz_sync_audit.resolve_target_paths(workspace_root, None, repo_registry, "aurora-cloudbank-symbolic-main")

    assert [target["name"] for target in targets] == ["aurora-cloudbank-symbolic-main"]
    assert targets[0]["relative_path"] == "GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main"


def test_load_repo_registry_raises_on_malformed_repo_row(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    registry_path = workspace_root / "catalog" / "repo_registry.yaml"
    registry_path.parent.mkdir(parents=True)
    registry_path.write_text(
        '{"repos": [{"name": "nested", "path": "Nested/Repo"}, "ignore-me"]}\n',
        encoding="utf-8",
    )

    with pytest.raises(SystemExit, match="Malformed repo registry"):
        gitwiz_sync_audit.load_repo_registry(workspace_root)


def test_resolve_target_paths_matches_root_name_and_relative_path(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    canonical_root = tmp_path / "canonical"
    registry = [{"name": "nested", "path": "Nested/Repo"}]

    by_name = gitwiz_sync_audit.resolve_target_paths(workspace_root, canonical_root, registry, "nested")
    by_path = gitwiz_sync_audit.resolve_target_paths(workspace_root, canonical_root, registry, "Nested/Repo")
    root_target = gitwiz_sync_audit.resolve_target_paths(workspace_root, canonical_root, registry, "root")
    root_by_path = gitwiz_sync_audit.resolve_target_paths(workspace_root, canonical_root, registry, ".")

    assert by_name[0]["name"] == "nested"
    assert by_name[0]["candidate_paths"] == [
        workspace_root / "Nested/Repo",
        canonical_root / "Nested/Repo",
    ]
    assert by_path[0]["relative_path"] == "Nested/Repo"
    assert root_target[0]["name"] == "root"
    assert root_by_path[0]["relative_path"] == "."


def test_choose_existing_path_prefers_git_repo_over_plain_directory(tmp_path: Path) -> None:
    plain_dir = tmp_path / "plain"
    repo_dir = tmp_path / "repo"
    plain_dir.mkdir()
    (repo_dir / ".git").mkdir(parents=True)

    chosen = gitwiz_sync_audit.choose_existing_path([plain_dir, repo_dir])

    assert chosen == repo_dir.resolve()


def test_comparison_status_falls_back_to_origin_main_without_overwriting_upstream(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_run_git(repo_path: Path, args: list[str], check: bool = True):
        command = tuple(args)
        if command == ("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"):
            raise subprocess.CalledProcessError(returncode=128, cmd=["git", *args])
        if command == ("rev-parse", "--verify", "refs/remotes/origin/main"):
            return completed(args, stdout="origin/main\n")
        if command == ("rev-list", "--left-right", "--count", "origin/main...HEAD"):
            return completed(args, stdout="7\t3\n")
        raise AssertionError(f"unexpected git args: {args}")

    monkeypatch.setattr(gitwiz_sync_audit, "run_git", fake_run_git)

    status = gitwiz_sync_audit.comparison_status(tmp_path, "codex/gitwiz-sync-audit-overlap-2026-04-08")

    assert status["upstream"] == ""
    assert status["comparison_ref"] == "origin/main"
    assert status["comparison_mode"] == "fallback_origin_main"
    assert status["behind"] == 7
    assert status["ahead"] == 3


def test_suggest_actions_does_not_push_fallback_comparison_ref() -> None:
    actions = gitwiz_sync_audit.suggest_actions(
        {
            "exists": True,
            "remotes": {"origin": {"fetch": "git@example.test:owner/repo.git"}},
            "dirty": False,
            "status_counts": {"untracked": 0},
            "ahead": 3,
            "behind": 7,
            "branch": "codex/example-feature",
            "upstream": "",
            "comparison_ref": "origin/main",
            "overlap_paths": [],
        }
    )

    push_actions = [action for action in actions if action.startswith("Push ")]

    assert push_actions == [
        "Push codex/example-feature to origin/codex/example-feature so the remote matches local history."
    ]


def _build_repo_summary_with_git(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    status_output: str,
    rev_list_output: str,
    path_outputs: dict[tuple[str, ...], str] | None = None,
) -> tuple[dict[str, object], list[tuple[str, ...]]]:
    repo_path = tmp_path / "repo"
    (repo_path / ".git").mkdir(parents=True)
    calls: list[tuple[str, ...]] = []
    path_outputs = path_outputs or {}

    def fake_run_git(repo_path_arg: Path, args: list[str], check: bool = True):
        assert repo_path_arg == repo_path
        command = tuple(args)
        calls.append(command)
        if command == ("rev-parse", "--abbrev-ref", "HEAD"):
            return completed(args, stdout="feature-branch\n")
        if command == ("rev-parse", "HEAD"):
            return completed(args, stdout="abc123\n")
        if command == ("remote", "-v"):
            return completed(args, stdout="origin\tgit@example.test:owner/repo.git (fetch)\norigin\tgit@example.test:owner/repo.git (push)\n")
        if command == ("status", "--short"):
            return completed(args, stdout=status_output)
        if command == ("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"):
            return completed(args, stdout="origin/feature-branch\n")
        if command == ("rev-list", "--left-right", "--count", "origin/feature-branch...HEAD"):
            return completed(args, stdout=rev_list_output)
        if command in path_outputs:
            return completed(args, stdout=path_outputs[command])
        raise AssertionError(f"unexpected git args: {args}")

    monkeypatch.setattr(gitwiz_sync_audit, "run_git", fake_run_git)

    summary = gitwiz_sync_audit.build_repo_summary(
        {"name": "root", "relative_path": ".", "candidate_paths": [repo_path]},
        fetch=False,
    )
    return summary, calls


def test_build_repo_summary_skips_extra_path_collection_for_clean_repo(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    summary, calls = _build_repo_summary_with_git(
        monkeypatch,
        tmp_path,
        status_output="",
        rev_list_output="0\t0\n",
    )

    assert summary["local_dirty_paths"] == []
    assert summary["incoming_remote_paths"] == []
    assert summary["overlap_paths"] == []
    assert ("diff", "--name-only") not in calls
    assert ("ls-files", "--others", "--exclude-standard") not in calls


def test_build_repo_summary_reports_dirty_only_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    summary, _calls = _build_repo_summary_with_git(
        monkeypatch,
        tmp_path,
        status_output=" M local.txt\n?? new.txt\n",
        rev_list_output="0\t0\n",
        path_outputs={
            ("diff", "--name-only"): "local.txt\n",
            ("diff", "--cached", "--name-only"): "",
            ("ls-files", "--others", "--exclude-standard"): "new.txt\n",
        },
    )

    assert summary["local_dirty_paths"] == ["local.txt", "new.txt"]
    assert summary["incoming_remote_paths"] == []
    assert summary["overlap_paths"] == []


def test_build_repo_summary_reports_behind_only_paths(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    summary, calls = _build_repo_summary_with_git(
        monkeypatch,
        tmp_path,
        status_output="",
        rev_list_output="2\t0\n",
        path_outputs={
            ("diff", "--name-only", "HEAD..origin/feature-branch"): "incoming.txt\n",
        },
    )

    assert summary["local_dirty_paths"] == []
    assert summary["incoming_remote_paths"] == ["incoming.txt"]
    assert summary["overlap_paths"] == []
    assert ("diff", "--name-only") not in calls


def test_build_repo_summary_reports_dirty_behind_overlap(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    summary, _calls = _build_repo_summary_with_git(
        monkeypatch,
        tmp_path,
        status_output=" M overlap.txt\nM  staged.txt\n?? new.txt\n",
        rev_list_output="2\t1\n",
        path_outputs={
            ("diff", "--name-only"): "overlap.txt\nlocal.txt\n",
            ("diff", "--cached", "--name-only"): "overlap.txt\nstaged.txt\n",
            ("ls-files", "--others", "--exclude-standard"): "new.txt\n",
            ("diff", "--name-only", "HEAD..origin/feature-branch"): "other.txt\noverlap.txt\nstaged.txt\n",
        },
    )

    assert summary["local_dirty_paths"] == ["overlap.txt", "local.txt", "staged.txt", "new.txt"]
    assert summary["incoming_remote_paths"] == ["other.txt", "overlap.txt", "staged.txt"]
    assert summary["overlap_paths"] == ["overlap.txt", "staged.txt"]


def test_collect_gh_auth_context_skips_probe_when_not_requested() -> None:
    context = gitwiz_sync_audit.collect_gh_auth_context(False)

    assert context["checked"] is False
    assert context["status"] == "not_checked"


def test_markdown_report_includes_github_cli_context() -> None:
    report = {
        "generated_at_utc": "2026-06-19 00:00:00 UTC",
        "workspace_root": "/workspace",
        "canonical_root": "",
        "selection": "root",
        "github_cli_auth": {
            "checked": True,
            "status": "auth_failed_in_current_context",
            "next_step": "Rerun escalated before changing tokens.",
        },
        "repos": [],
    }

    markdown = gitwiz_sync_audit.markdown_report(report)

    assert "## GitHub CLI Context" in markdown
    assert "- Status: `auth_failed_in_current_context`" in markdown
    assert "Rerun escalated before changing tokens." in markdown

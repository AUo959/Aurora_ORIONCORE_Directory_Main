from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "skills" / "gitwiz-github-manager" / "scripts" / "gitwiz_sync_audit.py"

_SPEC = importlib.util.spec_from_file_location("gitwiz_sync_audit", MODULE_PATH)
assert _SPEC and _SPEC.loader
gitwiz_sync_audit = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(gitwiz_sync_audit)


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

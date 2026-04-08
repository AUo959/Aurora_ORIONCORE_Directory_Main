from __future__ import annotations

import builtins
import importlib.util
import shutil
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "skills" / "gitwiz-github-manager" / "scripts" / "gitwiz_sync_audit.py"


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def copy_repo_file(source_relative: str, destination_root: Path) -> None:
    source = REPO_ROOT / source_relative
    destination = destination_root / source_relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def load_gitwiz_sync_audit_module():
    spec = importlib.util.spec_from_file_location("gitwiz_sync_audit_test", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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

    module = load_gitwiz_sync_audit_module()
    repo_registry = module.load_repo_registry(workspace_root)
    targets = module.resolve_target_paths(workspace_root, None, repo_registry, "aurora-cloudbank-symbolic-main")

    assert [target["name"] for target in targets] == ["aurora-cloudbank-symbolic-main"]
    assert targets[0]["relative_path"] == "GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main"

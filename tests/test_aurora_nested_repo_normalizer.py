from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "aurora-nested-repo-normalizer" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import normalize_nested_repo  # noqa: E402


class AuroraNestedRepoNormalizerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="aurora-normalizer-test-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def run_git(self, args, cwd):
        subprocess.run(["git"] + args, cwd=str(cwd), check=True, text=True, capture_output=True)

    def make_remote_repo(self) -> Path:
        remote = self.tempdir / "remote"
        remote.mkdir()
        self.run_git(["init"], remote)
        self.run_git(["config", "user.name", "Test User"], remote)
        self.run_git(["config", "user.email", "test@example.com"], remote)
        self.run_git(["config", "commit.gpgsign", "false"], remote)
        (remote / "README.md").write_text("# Example\n", encoding="utf-8")
        (remote / "docs").mkdir()
        (remote / "docs" / "note.txt").write_text("hello\n", encoding="utf-8")
        self.run_git(["add", "."], remote)
        self.run_git(["commit", "-m", "initial"], remote)
        return remote

    def test_compare_trees_ignores_local_artifacts(self) -> None:
        left = self.tempdir / "left"
        right = self.tempdir / "right"
        left.mkdir()
        right.mkdir()
        (left / "README.md").write_text("same\n", encoding="utf-8")
        (right / "README.md").write_text("same\n", encoding="utf-8")
        (left / ".DS_Store").write_text("junk\n", encoding="utf-8")
        (right / "__pycache__").mkdir()
        (right / "__pycache__" / "x.pyc").write_text("junk\n", encoding="utf-8")

        result = normalize_nested_repo.compare_trees(left, right)
        self.assertTrue(result["matches"])

    def test_compare_trees_detects_mismatch(self) -> None:
        left = self.tempdir / "left"
        right = self.tempdir / "right"
        left.mkdir()
        right.mkdir()
        (left / "README.md").write_text("left\n", encoding="utf-8")
        (right / "README.md").write_text("right\n", encoding="utf-8")

        result = normalize_nested_repo.compare_trees(left, right)
        self.assertFalse(result["matches"])
        self.assertEqual(result["content_mismatches"], ["README.md"])

    def test_normalize_nested_repo_attaches_git_history(self) -> None:
        remote = self.make_remote_repo()
        target = self.tempdir / "target"
        shutil.copytree(remote, target, ignore=shutil.ignore_patterns(".git"))

        receipt = normalize_nested_repo.normalize_nested_repo(target=target, remote=str(remote))

        self.assertEqual(receipt["status"], "normalized")
        self.assertTrue((target / ".git").exists())
        self.assertTrue(normalize_nested_repo.is_git_repo(target))

        remote_head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(remote),
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()
        target_head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(target),
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()
        self.assertEqual(target_head, remote_head)

    def test_already_normalized_repo_returns_clean_status(self) -> None:
        remote = self.make_remote_repo()
        target = self.tempdir / "target"
        subprocess.run(["git", "clone", str(remote), str(target)], check=True, text=True, capture_output=True)

        receipt = normalize_nested_repo.normalize_nested_repo(target=target, remote=str(remote))

        self.assertEqual(receipt["status"], "already_normalized")

    def test_clone_if_missing_bootstraps_repo(self) -> None:
        remote = self.make_remote_repo()
        target = self.tempdir / "missing-target"

        receipt = normalize_nested_repo.normalize_nested_repo(
            target=target,
            remote=str(remote),
            clone_if_missing=True,
        )

        self.assertEqual(receipt["status"], "cloned_missing_target")
        self.assertTrue((target / ".git").exists())
        self.assertTrue(normalize_nested_repo.is_git_repo(target))

    def test_clone_if_missing_dry_run_is_non_mutating(self) -> None:
        remote = self.make_remote_repo()
        target = self.tempdir / "missing-target"

        receipt = normalize_nested_repo.normalize_nested_repo(
            target=target,
            remote=str(remote),
            clone_if_missing=True,
            dry_run=True,
        )

        self.assertEqual(receipt["status"], "would_clone_missing_target")
        self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()

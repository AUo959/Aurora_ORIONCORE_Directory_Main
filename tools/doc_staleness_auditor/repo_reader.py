"""Read a target repo's ground truth.

Two backends, one interface:

* :class:`GitRepoReader` reads content via ``git show HEAD:<path>`` and lists
  tracked files via ``git ls-tree`` -- so it works even in a shallow / sparse
  worktree where files are not materialised on disk.
* :class:`FsRepoReader` reads a plain checked-out directory from disk and uses
  git only for the HEAD sha (falling back to ``"WORKTREE"`` outside git).

Both expose the same surface used by the verifiers: :meth:`head_sha`,
:meth:`list_files`, :meth:`list_docs`, :meth:`read`, :meth:`exists`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


class RepoReader:
    def __init__(self, root: str):
        self.root = str(Path(root).resolve())
        self._sha: str | None = None
        self._files_cache: tuple[str, ...] | None = None

    def _git(self, *args: str) -> str:
        # fixed git command against a local repo root; no shell, no untrusted exe
        proc = subprocess.run(["git", "-C", self.root, *args], capture_output=True, text=True, check=False)  # noqa: S603, S607
        if proc.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
        return proc.stdout

    def head_sha(self) -> str:  # pragma: no cover - overridden
        raise NotImplementedError

    def list_files(self) -> list[str]:  # pragma: no cover - overridden
        raise NotImplementedError

    def list_docs(self) -> list[str]:
        return [f for f in self.list_files() if f.lower().endswith(".md")]

    def read(self, path: str) -> str | None:  # pragma: no cover - overridden
        raise NotImplementedError

    def exists(self, path: str) -> bool:
        return path in set(self.list_files())


class GitRepoReader(RepoReader):
    """Reads content and file listing straight from the git object store."""

    def head_sha(self) -> str:
        if self._sha is None:
            self._sha = self._git("rev-parse", "HEAD").strip()
        return self._sha

    def _tracked(self) -> tuple[str, ...]:
        if self._files_cache is None:
            out = self._git("ls-tree", "-r", "--name-only", "HEAD")
            self._files_cache = tuple(line for line in out.splitlines() if line)
        return self._files_cache

    def list_files(self) -> list[str]:
        return list(self._tracked())

    def read(self, path: str) -> str | None:
        # fixed git command against a local repo root; no shell, no untrusted exe
        proc = subprocess.run(["git", "-C", self.root, "show", f"HEAD:{path}"], capture_output=True, text=True, check=False)  # noqa: S603, S607
        if proc.returncode != 0:
            return None
        return proc.stdout


class FsRepoReader(RepoReader):
    """Reads a materialised working tree from disk."""

    def head_sha(self) -> str:
        if self._sha is None:
            try:
                self._sha = self._git("rev-parse", "HEAD").strip()
            except RuntimeError:
                self._sha = "WORKTREE"
        return self._sha

    def _tracked(self) -> tuple[str, ...]:
        if self._files_cache is None:
            files: list[str] = []
            root = Path(self.root)
            for p in root.rglob("*"):
                if p.is_file() and ".git/" not in str(p.relative_to(root)):
                    files.append(str(p.relative_to(root)))
            self._files_cache = tuple(sorted(files))
        return self._files_cache

    def list_files(self) -> list[str]:
        return list(self._tracked())

    def read(self, path: str) -> str | None:
        fp = Path(self.root) / path
        if not fp.is_file():
            return None
        try:
            return fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None


def make_reader(root: str, backend: str = "auto") -> RepoReader:
    """Pick a backend. ``auto`` prefers git when the tree looks sparse/shallow."""
    if backend == "git":
        return GitRepoReader(root)
    if backend == "fs":
        return FsRepoReader(root)
    # auto: use git backend if the checkout is sparse (files may be absent on disk)
    reader = GitRepoReader(root)
    try:
        info = reader._git("sparse-checkout", "list")
        if info.strip():
            return reader
    except RuntimeError:
        pass
    # Otherwise prefer the filesystem backend (faster, no per-file git show).
    try:
        FsRepoReader(root).head_sha()
        return FsRepoReader(root)
    except Exception:  # noqa: BLE001
        return reader

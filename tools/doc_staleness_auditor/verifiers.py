"""Ground-truth verifiers.

Every verifier reaches its verdict by reading a *primary* source (git tree,
actual file content, config/version files, or a recomputed count) -- never by
consulting another doc, and never by a bare filename ``exists()`` when the claim
is about content. A claim with no machine-checkable ground truth is returned as
``UNVERIFIABLE_BY_AUTOMATION`` rather than being optimistically confirmed.
"""

from __future__ import annotations

import ast
import json
import re
import tomllib
import warnings

from .models import Claim, ClaimType, Evidence, Finding, Status
from .repo_reader import RepoReader

_PY_EXT = (".py",)
_JS_EXT = (".js", ".jsx", ".ts", ".tsx", ".mjs")
_OTHER_CODE_EXT = (".swift", ".go", ".rs", ".rb", ".java")
_SOURCE_EXT = _PY_EXT + _JS_EXT + _OTHER_CODE_EXT

_JS_DEF_RE = re.compile(
    r"(?:function\s+([A-Za-z_$][\w$]*)|class\s+([A-Za-z_$][\w$]*)"
    r"|(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=)"
)
_GENERIC_DEF_RE = re.compile(
    r"(?:func|def|class|fn|function|public|private|static)\s+([A-Za-z_][\w]*)"
)


class Verifier:
    def __init__(self, reader: RepoReader):
        self.reader = reader
        self.sha = reader.head_sha()
        self._files = set(reader.list_files())
        self._top_dirs_cache: frozenset[str] | None = None
        self._basenames_cache: dict[str, list[str]] | None = None
        self._symbol_index_cache: dict[str, tuple[str, int]] | None = None

    # ---- dispatch -----------------------------------------------------------
    def verify(self, claim: Claim) -> Finding:
        if claim.type is ClaimType.PATH:
            return self._verify_path(claim)
        if claim.type is ClaimType.SYMBOL:
            return self._verify_symbol(claim)
        if claim.type is ClaimType.NUMERIC:
            return self._verify_numeric(claim)
        if claim.type is ClaimType.VERSION:
            return self._verify_version(claim)
        raise ValueError(f"unknown claim type {claim.type}")

    def verify_all(self, claims: list[Claim]) -> list[Finding]:
        return [self.verify(c) for c in claims]

    # ---- path ---------------------------------------------------------------
    def _top_dirs(self) -> frozenset[str]:
        if self._top_dirs_cache is None:
            self._top_dirs_cache = frozenset(
                f.split("/", 1)[0] for f in self._files if "/" in f)
        return self._top_dirs_cache

    def _basenames(self) -> dict:
        if self._basenames_cache is None:
            idx: dict[str, list[str]] = {}
            for f in self._files:
                idx.setdefault(f.rsplit("/", 1)[-1], []).append(f)
            self._basenames_cache = idx
        return self._basenames_cache

    def _resolve_path(self, claim: Claim) -> str | None:
        """Resolve a referenced token to a real tracked path, or None."""
        token = claim.value.strip("/")
        if token in self._files:
            return token
        doc_dir = claim.doc_path.rsplit("/", 1)[0] if "/" in claim.doc_path else ""
        cand = f"{doc_dir}/{token}".lstrip("/") if doc_dir else token
        if cand in self._files:
            return cand
        prefix = token.rstrip("/") + "/"
        if any(f.startswith(prefix) for f in self._files):
            return token.rstrip("/")
        # bare filename referenced without its directory: resolve by basename
        if "/" not in token:
            hits = self._basenames().get(token)
            if hits:
                return hits[0]
        return None

    def _verify_path(self, claim: Claim) -> Finding:
        token = claim.value
        bare = token.strip("/")
        if re.fullmatch(r"\d+\.\d+(?:\.\d+)?", bare):
            return self._unverifiable(claim, "token is a version string, not a path")
        if token.startswith(("/", "~")) or token.startswith("..") or re.match(r"^[A-Za-z]:", token):
            return self._unverifiable(
                claim, f"'{token}' is an absolute/relative out-of-tree path "
                       "(environment path, not a repo-tree claim)")

        resolved = self._resolve_path(claim)
        if resolved is not None:
            ev = Evidence(
                method="git_tree_lookup",
                detail=f"path present in git tree at HEAD as '{resolved}'",
                files=[resolved], sha=self.sha,
            )
            return Finding(claim, Status.CONFIRMED, observed=resolved, evidence=ev)

        # Unresolved. Only call it STALE when it is a *structural* intra-repo
        # claim: it has a directory component whose first segment is a real
        # top-level dir, so the doc is asserting a path that genuinely should
        # exist here but does not. Otherwise (bare filename, unknown root) we
        # cannot prove the doc wrong -> UNVERIFIABLE.
        if "/" in bare and bare.split("/", 1)[0] in self._top_dirs():
            ev = Evidence(
                method="git_tree_lookup",
                detail=f"no tracked path '{token}' in git tree at HEAD; first "
                       f"segment '{bare.split('/', 1)[0]}' is a real top-level dir "
                       "so this is a broken intra-repo reference",
                files=[], sha=self.sha,
            )
            return Finding(claim, Status.STALE, observed="<not found>", evidence=ev)
        return self._unverifiable(
            claim, f"path '{token}' does not resolve and is not a structural "
                   "intra-repo reference (bare filename or unknown root); "
                   "cannot prove the doc wrong from the tree alone")

    # ---- symbol -------------------------------------------------------------
    def _symbol_index(self) -> dict[str, tuple[str, int]]:
        """Map defined symbol name -> (file, 1-based line) across real source."""
        if self._symbol_index_cache is not None:
            return self._symbol_index_cache
        index: dict[str, tuple[str, int]] = {}
        for path in self.reader.list_files():
            if not path.endswith(_SOURCE_EXT):
                continue
            content = self.reader.read(path)
            if content is None:
                continue
            for name, line in self._defs_in(path, content):
                index.setdefault(name, (path, line))
        self._symbol_index_cache = index
        return index

    @staticmethod
    def _defs_in(path: str, content: str) -> list[tuple[str, int]]:
        defs: list[tuple[str, int]] = []
        if path.endswith(_PY_EXT):
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", SyntaxWarning)
                    tree = ast.parse(content)
            except (SyntaxError, ValueError):
                return defs
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    defs.append((node.name, node.lineno))
            return defs
        regex = _JS_DEF_RE if path.endswith(_JS_EXT) else _GENERIC_DEF_RE
        for i, line in enumerate(content.splitlines(), start=1):
            for m in regex.finditer(line):
                name = next((g for g in m.groups() if g), None)
                if name:
                    defs.append((name, i))
        return defs

    def _symbol_in_file(self, path: str, symbol: str) -> int | None:
        content = self.reader.read(path)
        if content is None:
            return None
        for name, line in self._defs_in(path, content):
            if name == symbol:
                return line
        # fall back to a definition-shaped occurrence in real content
        for i, line in enumerate(content.splitlines(), start=1):
            if re.search(rf"\b{re.escape(symbol)}\b", line) and (
                "def " in line or "class " in line or "function" in line or "=" in line
            ):
                return i
        return None

    def _verify_symbol(self, claim: Claim) -> Finding:
        symbol = claim.value.split(".")[-1]
        file_hint = claim.context.get("file_hint")
        if file_hint:
            resolved = self._resolve_hint(file_hint)
            if resolved is None:
                ev = Evidence(
                    method="git_tree_lookup",
                    detail=f"referenced file '{file_hint}' not in git tree at HEAD",
                    files=[], sha=self.sha,
                )
                return Finding(claim, Status.STALE, observed="<file missing>", evidence=ev)
            line = self._symbol_in_file(resolved, symbol)
            if line is not None:
                ev = Evidence(
                    method="python_ast_parse" if resolved.endswith(_PY_EXT)
                    else "source_content_read",
                    detail=f"symbol '{symbol}' defined in real source",
                    files=[resolved], lines=[str(line)], sha=self.sha,
                )
                return Finding(claim, Status.CONFIRMED, observed=f"{resolved}:{line}", evidence=ev)
            ev = Evidence(
                method="source_content_read",
                detail=f"read '{resolved}' at HEAD; symbol '{symbol}' not defined there",
                files=[resolved], sha=self.sha,
            )
            return Finding(claim, Status.STALE, observed="<symbol absent>", evidence=ev)

        # No file hint: only CONFIRM if it is a real definition somewhere in the
        # tree. Absence is NOT proof the doc is wrong (could be an external
        # symbol), so we return UNVERIFIABLE rather than STALE.
        hit = self._symbol_index().get(symbol)
        if hit is not None:
            path, line = hit
            ev = Evidence(
                method="python_ast_parse" if path.endswith(_PY_EXT) else "source_content_read",
                detail=f"symbol '{symbol}' defined in real source (repo symbol index)",
                files=[path], lines=[str(line)], sha=self.sha,
            )
            return Finding(claim, Status.CONFIRMED, observed=f"{path}:{line}", evidence=ev)
        return self._unverifiable(
            claim,
            f"symbol '{symbol}' not defined in indexed repo source and no file "
            f"reference given to pin it to a ground-truth site",
        )

    def _resolve_hint(self, file_hint: str) -> str | None:
        token = file_hint.strip("/")
        if token in self._files:
            return token
        for f in self._files:
            if f.endswith("/" + token) or f == token:
                return f
        return None

    # ---- numeric / counts ---------------------------------------------------
    _NOUN_EXT = {
        "docs": (".md",), "documents": (".md",), "specs": (".md",),
        "tests": (".py", ".js", ".ts"), "scripts": (".py", ".sh"),
        "modules": (".py",), "tools": (".py",), "files": (),
    }

    _HISTORICAL_SEGMENTS = frozenset(
        {"archive", "archived", "archives", "reports", "handoffs"}
    )

    def _is_historical(self, doc_path: str) -> bool:
        segs = set(doc_path.split("/"))
        return (
            bool(segs & self._HISTORICAL_SEGMENTS)
            or doc_path.startswith("catalog/session_")
        )

    def _verify_numeric(self, claim: Claim) -> Finding:
        noun = claim.context.get("noun", "")
        claimed = int(claim.value)
        # Point-in-time reports/handoffs record counts true at authoring time;
        # recomputing against current HEAD would mislabel them. Out of scope.
        if self._is_historical(claim.doc_path):
            return self._unverifiable(
                claim, "count appears in a dated report/handoff/log (point-in-time "
                       "snapshot); not a live claim about current HEAD")
        scope = self._count_scope(claim)
        if scope is None:
            return self._unverifiable(
                claim,
                f"count of {claimed} {noun} has no directory scope in the doc text; "
                f"cannot bind to a recomputable rule",
            )
        exts = self._NOUN_EXT.get(noun, ())
        prefix = scope.rstrip("/") + "/"
        matches = [
            f for f in self._files
            if f.startswith(prefix) and (not exts or f.endswith(exts))
        ]
        if noun in ("tests",):
            matches = [f for f in matches if "test" in f.rsplit("/", 1)[-1].lower()]
        observed = len(matches)
        ev = Evidence(
            method="recomputed_count",
            detail=f"counted tracked files under '{scope}' matching {noun} "
                   f"(ext={exts or 'any'}) at HEAD: {observed}",
            files=[scope], sha=self.sha,
        )
        status = Status.CONFIRMED if observed == claimed else Status.STALE
        return Finding(claim, status, observed=str(observed), evidence=ev)

    def _count_scope(self, claim: Claim) -> str | None:
        cands = []
        for m in re.finditer(r"`([A-Za-z0-9_.\-/]+/)`?", claim.raw_text):
            cand = m.group(1).strip("`").rstrip("/")
            if any(f.startswith(cand + "/") for f in self._files):
                cands.append(cand)
        # only a single, unambiguous directory scope is safe to recompute against
        return cands[0] if len(set(cands)) == 1 else None

    # ---- version ------------------------------------------------------------
    def _verify_version(self, claim: Claim) -> Finding:
        raw = claim.raw_text
        claimed = claim.value

        if self._is_historical(claim.doc_path):
            return self._unverifiable(
                claim, "version appears in a dated report/handoff/log (point-in-time "
                       "snapshot); not a live claim about current HEAD")

        # Only a python-version claim when the number is adjacent to python/py,
        # not merely on the same line as the word "python". The lookbehind keeps
        # library names that end in "py" (numpy, scipy) from matching.
        if re.search(rf"(?<![A-Za-z])(?:python|py)\s*v?\.?\s*{re.escape(claimed)}",
                     raw, re.IGNORECASE):
            return self._verify_python_version(claim)

        named = self._named_version_file(raw)
        if named:
            return self._compare_version_file(claim, named)

        if claim.doc_path.rsplit("/", 1)[-1].upper() == "CHANGELOG.MD":
            return self._verify_changelog_head(claim)

        return self._unverifiable(
            claim,
            f"version '{claimed}' is not bound to a version source (no version file "
            f"named on the line, not a python or changelog-headline version)",
        )

    _VERSION_FILES = ("VERSION", "package.json", "pyproject.toml", ".python-version")

    def _named_version_file(self, raw: str) -> str | None:
        # Match the actual filename form only (case-sensitive), so the English
        # word "version" in prose does not bind to the VERSION file.
        for vf in ("package.json", "pyproject.toml", ".python-version"):
            if vf in raw:
                return vf
        if re.search(r"\bVERSION\b", raw):  # uppercase file, not prose "version"
            return "VERSION"
        return None

    def _read_version_from(self, vf: str) -> tuple[str | None, str]:
        content = self.reader.read(vf)
        if content is None:
            return None, f"'{vf}' not present at HEAD"
        if vf == "VERSION" or vf == ".python-version":
            return content.strip().splitlines()[0].strip(), f"first line of {vf}"
        if vf == "package.json":
            try:
                return json.loads(content).get("version"), "package.json .version"
            except json.JSONDecodeError:
                return None, "package.json unparseable"
        if vf == "pyproject.toml":
            try:
                data = tomllib.loads(content)
            except tomllib.TOMLDecodeError:
                return None, "pyproject.toml unparseable"
            ver = (data.get("project", {}).get("version")
                   or data.get("tool", {}).get("poetry", {}).get("version"))
            return ver, "pyproject [project].version"
        return None, "unknown version file"

    def _compare_version_file(self, claim: Claim, vf: str) -> Finding:
        actual, how = self._read_version_from(vf)
        if actual is None:
            ev = Evidence(method="config_file_read", detail=how, files=[vf], sha=self.sha)
            return Finding(claim, Status.STALE, observed="<no version value>", evidence=ev)
        ev = Evidence(
            method="config_file_read",
            detail=f"read {how} at HEAD -> '{actual}'", files=[vf], sha=self.sha,
        )
        status = Status.CONFIRMED if actual == claim.value else Status.STALE
        return Finding(claim, status, observed=actual, evidence=ev)

    def _python_version_sources(self) -> list[tuple[str, str]]:
        """Collect (source-label, X.Y) python-version facts from real files."""
        sources: list[tuple[str, str]] = []
        pv = self.reader.read(".python-version")
        if pv:
            sources.append((".python-version", pv.strip().splitlines()[0].strip()))
        rt = self.reader.read("runtime.txt")
        if rt and (m := re.search(r"(\d+\.\d+)", rt)):
            sources.append(("runtime.txt", m.group(1)))
        sources.extend(self._pyproject_python_sources())
        return sources

    def _pyproject_python_sources(self) -> list[tuple[str, str]]:
        pj = self.reader.read("pyproject.toml")
        if not pj:
            return []
        try:
            data = tomllib.loads(pj)
        except tomllib.TOMLDecodeError:
            return []
        out: list[tuple[str, str]] = []
        rp = data.get("project", {}).get("requires-python")
        if rp and (m := re.search(r"(\d+\.\d+)", rp)):
            out.append(("pyproject.toml requires-python", m.group(1)))
        tv = (data.get("tool", {}).get("black", {}).get("target-version")
              or data.get("tool", {}).get("ruff", {}).get("target-version"))
        if tv:
            s = tv[0] if isinstance(tv, list) and tv else tv
            if m := re.search(r"(\d)(\d+)", str(s)):
                out.append((f"pyproject target-version {s}", f"{m.group(1)}.{m.group(2)}"))
        return out

    def _verify_python_version(self, claim: Claim) -> Finding:
        floor = ".".join(claim.value.split(".")[:2])
        sources = self._python_version_sources()
        if not sources:
            return self._unverifiable(
                claim, "no python-version ground-truth source (.python-version / "
                       "runtime.txt / pyproject) present at HEAD")
        src_file, actual = sources[0]
        ev = Evidence(
            method="config_file_read",
            detail=f"python floor '{floor}' vs {src_file} -> '{actual}'",
            files=[src_file.split()[0]], sha=self.sha,
        )
        status = Status.CONFIRMED if actual == floor else Status.STALE
        return Finding(claim, status, observed=f"{actual} (per {src_file})", evidence=ev)

    def _verify_changelog_head(self, claim: Claim) -> Finding:
        content = self.reader.read(claim.doc_path) or ""
        first_release = None
        for line in content.splitlines():
            m = re.match(r"##\s*\[(\d+\.\d+(?:\.\d+)?)\]", line.strip())
            if m:
                first_release = m.group(1)
                break
        if first_release != claim.value:
            return self._unverifiable(
                claim, "version is not the top-most released CHANGELOG heading")
        actual, how = self._read_version_from("VERSION")
        if actual is None:
            return self._unverifiable(claim, "no VERSION file to reconcile changelog head")
        ev = Evidence(
            method="config_file_read",
            detail=f"CHANGELOG latest release '{claim.value}' vs {how} -> '{actual}'",
            files=["VERSION", claim.doc_path], sha=self.sha,
        )
        status = Status.CONFIRMED if actual == claim.value else Status.STALE
        return Finding(claim, status, observed=f"VERSION={actual}", evidence=ev)

    # ---- helpers ------------------------------------------------------------
    @staticmethod
    def _unverifiable(claim: Claim, why: str) -> Finding:
        return Finding(
            claim, Status.UNVERIFIABLE, observed=None,
            evidence=Evidence(method="none", detail=why),
        )

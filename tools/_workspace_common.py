from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG_DIR = ROOT / "catalog"
DOCS_DIR = ROOT / "docs"
REPORTS_ANALYSIS_DIR = ROOT / "reports" / "analysis"
TRACKED_FILE_SIZE_LIMIT_BYTES = 1_000_000

ARCHIVE_EXTENSIONS = {
    ".zip",
    ".7z",
    ".rar",
    ".tar",
    ".gz",
    ".tgz",
    ".bz2",
    ".xz",
    ".dmg",
    ".iso",
}

BINARY_EXTENSIONS = {
    ".pkg",
    ".msi",
    ".exe",
    ".bin",
    ".img",
}

TEXT_LIKE_EXTENSIONS = {
    ".md",
    ".markdown",
    ".txt",
    ".json",
    ".jsonl",
    ".yaml",
    ".yml",
    ".csv",
    ".py",
    ".sh",
    ".toml",
}

MANAGED_ROOT_PATHS = {
    "AGENTS.md",
    "README.md",
    ".gitignore",
    ".gitattributes",
    ".githooks",
    "docs",
    "catalog",
    "tools",
    "tests",
    "skills",
    "reports",
    "archives",
    "intake",
    "repos",
    "projects",
    "_staging",
}

LOCAL_ARTIFACT_NAMES = {
    ".DS_Store",
    ".pytest_cache",
    ".gitwiz",
    ".codex_skill_edits",
}

ARCHIVE_ZONE_NAMES = (
    "au_archive",
    "zip_archives",
    "zipwiz",
    "complete archive",
    "unzipped archives",
    "archive",
)

SANCTIONED_ROOT_ANALYSIS_DOCS = {
    "aurora_cloudbank_symbolic_architecture_discovery_report.md",
}
ROOT_INTAKE_CLEANUP_BATCH_ID = "wave4_root_intake_cleanup_initial"


def now_iso_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resolve_root(root: str | None = None) -> Path:
    return Path(root).expanduser().resolve() if root else ROOT


def serialized_root(root: Path) -> str:
    del root
    return "."


def display_root(root: Path) -> str:
    return root.name or serialized_root(root)


def relpath(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _yaml_lines(text: str) -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        rows.append((len(raw_line) - len(raw_line.lstrip(" ")), raw_line.strip()))
    return rows


def _split_yaml_mapping_entry(content: str) -> tuple[str, str] | None:
    for index, char in enumerate(content):
        if char != ":":
            continue
        if index == 0:
            continue
        next_char = content[index + 1 : index + 2]
        if next_char and not next_char.isspace():
            continue
        key = content[:index].strip()
        if not key:
            continue
        return key, content[index + 1 :].strip()
    return None


def _parse_yaml_scalar(token: str) -> Any:
    if token in {"null", "Null", "NULL", "~"}:
        return None
    if token in {"true", "True", "TRUE"}:
        return True
    if token in {"false", "False", "FALSE"}:
        return False
    if token == "[]":
        return []
    if token == "{}":
        return {}
    if len(token) >= 2 and token[0] == token[-1] == "'":
        return token[1:-1].replace("''", "'")
    if len(token) >= 2 and token[0] == token[-1] == '"':
        return json.loads(token)
    if re.fullmatch(r"-?(0|[1-9]\d*)", token):
        return int(token)
    if re.fullmatch(r"-?(0|[1-9]\d*)\.\d+", token):
        return float(token)
    return token


def _consume_yaml_scalar_text(
    rows: list[tuple[int, str]],
    index: int,
    parent_indent: int,
    initial_text: str,
) -> tuple[str, int]:
    parts = [initial_text]
    while index < len(rows):
        indent, content = rows[index]
        if indent <= parent_indent or content == "-" or content.startswith("- "):
            break
        parts.append(content.strip())
        index += 1
    return " ".join(part for part in parts if part != ""), index


def _has_yaml_child_block(
    rows: list[tuple[int, str]],
    index: int,
    parent_indent: int,
) -> bool:
    if index >= len(rows):
        return False
    indent, content = rows[index]
    return indent > parent_indent or (indent == parent_indent and (content == "-" or content.startswith("- ")))


def _parse_yaml_block(rows: list[tuple[int, str]], index: int) -> tuple[Any, int]:
    if index >= len(rows):
        raise ValueError("Unexpected end of YAML content.")
    indent, content = rows[index]
    if content == "-" or content.startswith("- "):
        return _parse_yaml_sequence(rows, index, indent)
    return _parse_yaml_mapping(rows, index, indent)


def _parse_yaml_sequence(
    rows: list[tuple[int, str]],
    index: int,
    indent: int,
) -> tuple[list[Any], int]:
    items: list[Any] = []
    while index < len(rows):
        current_indent, content = rows[index]
        if current_indent != indent or not (content == "-" or content.startswith("- ")):
            break
        rest = content[1:].lstrip()
        index += 1
        if not rest:
            if _has_yaml_child_block(rows, index, current_indent):
                value, index = _parse_yaml_block(rows, index)
            else:
                value = None
            items.append(value)
            continue

        inline_mapping = _split_yaml_mapping_entry(rest)
        if inline_mapping is not None:
            key, value_text = inline_mapping
            item, index = _parse_yaml_inline_mapping(rows, index, current_indent + 2, key, value_text)
            items.append(item)
            continue

        scalar_text, index = _consume_yaml_scalar_text(rows, index, current_indent, rest)
        items.append(_parse_yaml_scalar(scalar_text))
    return items, index


def _parse_yaml_inline_mapping(
    rows: list[tuple[int, str]],
    index: int,
    indent: int,
    first_key: str,
    first_value_text: str,
) -> tuple[dict[str, Any], int]:
    item: dict[str, Any] = {}
    value_text = first_value_text.strip()
    if value_text:
        scalar_text, index = _consume_yaml_scalar_text(rows, index, indent, value_text)
        item[first_key] = _parse_yaml_scalar(scalar_text)
    elif _has_yaml_child_block(rows, index, indent):
        item[first_key], index = _parse_yaml_block(rows, index)
    else:
        item[first_key] = None

    while index < len(rows):
        current_indent, content = rows[index]
        if current_indent != indent or content == "-" or content.startswith("- "):
            break
        entry = _split_yaml_mapping_entry(content)
        if entry is None:
            raise ValueError(f"Unsupported YAML line: {content!r}")
        key, value_text = entry
        index += 1
        if value_text:
            scalar_text, index = _consume_yaml_scalar_text(rows, index, current_indent, value_text)
            item[key] = _parse_yaml_scalar(scalar_text)
            continue
        if _has_yaml_child_block(rows, index, current_indent):
            item[key], index = _parse_yaml_block(rows, index)
        else:
            item[key] = None
    return item, index


def _parse_yaml_mapping(
    rows: list[tuple[int, str]],
    index: int,
    indent: int,
) -> tuple[dict[str, Any], int]:
    mapping: dict[str, Any] = {}
    while index < len(rows):
        current_indent, content = rows[index]
        if current_indent != indent or content == "-" or content.startswith("- "):
            break
        entry = _split_yaml_mapping_entry(content)
        if entry is None:
            raise ValueError(f"Unsupported YAML line: {content!r}")
        key, value_text = entry
        index += 1
        if value_text:
            scalar_text, index = _consume_yaml_scalar_text(rows, index, current_indent, value_text)
            mapping[key] = _parse_yaml_scalar(scalar_text)
            continue
        if _has_yaml_child_block(rows, index, current_indent):
            mapping[key], index = _parse_yaml_block(rows, index)
        else:
            mapping[key] = None
    return mapping, index


def _load_yaml_without_dependency(text: str) -> Any:
    rows = _yaml_lines(text)
    if not rows:
        return None
    payload, index = _parse_yaml_block(rows, 0)
    if index != len(rows):
        raise ValueError("Unsupported trailing YAML content.")
    return payload


def _dump_yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(value)


def _render_yaml_like_lines(value: Any, indent: int = 0) -> list[str]:
    prefix = " " * indent
    if isinstance(value, dict):
        if not value:
            return [f"{prefix}{{}}"]
        lines: list[str] = []
        for key, child in value.items():
            if isinstance(child, dict):
                if child:
                    lines.append(f"{prefix}{key}:")
                    lines.extend(_render_yaml_like_lines(child, indent + 2))
                else:
                    lines.append(f"{prefix}{key}: {{}}")
            elif isinstance(child, list):
                if child:
                    lines.append(f"{prefix}{key}:")
                    lines.extend(_render_yaml_like_lines(child, indent + 2))
                else:
                    lines.append(f"{prefix}{key}: []")
            else:
                lines.append(f"{prefix}{key}: {_dump_yaml_scalar(child)}")
        return lines
    if isinstance(value, list):
        if not value:
            return [f"{prefix}[]"]
        lines: list[str] = []
        for child in value:
            if isinstance(child, dict):
                if not child:
                    lines.append(f"{prefix}- {{}}")
                    continue
                entries = list(child.items())
                first_key, first_value = entries[0]
                if isinstance(first_value, (dict, list)):
                    lines.append(f"{prefix}- {first_key}:")
                    lines.extend(_render_yaml_like_lines(first_value, indent + 4))
                else:
                    lines.append(f"{prefix}- {first_key}: {_dump_yaml_scalar(first_value)}")
                for key, grandchild in entries[1:]:
                    if isinstance(grandchild, dict):
                        if grandchild:
                            lines.append(f"{prefix}  {key}:")
                            lines.extend(_render_yaml_like_lines(grandchild, indent + 4))
                        else:
                            lines.append(f"{prefix}  {key}: {{}}")
                    elif isinstance(grandchild, list):
                        if grandchild:
                            lines.append(f"{prefix}  {key}:")
                            lines.extend(_render_yaml_like_lines(grandchild, indent + 4))
                        else:
                            lines.append(f"{prefix}  {key}: []")
                    else:
                        lines.append(f"{prefix}  {key}: {_dump_yaml_scalar(grandchild)}")
                continue
            if isinstance(child, list):
                if child:
                    lines.append(f"{prefix}-")
                    lines.extend(_render_yaml_like_lines(child, indent + 2))
                else:
                    lines.append(f"{prefix}- []")
                continue
            lines.append(f"{prefix}- {_dump_yaml_scalar(child)}")
        return lines
    return [f"{prefix}{_dump_yaml_scalar(value)}"]


def load_yaml_like(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text)
    except ModuleNotFoundError:
        pass

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return _load_yaml_without_dependency(text)


def dump_yaml_like(data: Any, path: Path) -> None:
    ensure_parent(path)
    try:
        import yaml  # type: ignore

        rendered = yaml.safe_dump(
            data,
            sort_keys=False,
            allow_unicode=False,
            default_flow_style=False,
        )
    except Exception:
        rendered = "\n".join(_render_yaml_like_lines(data)) + "\n"
    path.write_text(rendered, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=False) + "\n")


_SHA256_ERROR_SENTINEL = "error:unreadable"


def sha256_file(path: Path) -> str:
    """Return the SHA-256 hex digest of *path*.

    On platforms where large files live on a FUSE/cloud-backed mount (e.g.
    iCloud Drive via the macOS VM bridge), reading very large files can
    raise ``OSError: [Errno 35] Resource temporarily unavailable`` or
    ``Resource deadlock avoided``.  Rather than crashing the entire scan,
    we catch those errors and return a sentinel string so the rest of the
    inventory continues normally.  Callers that need a real hash can retry
    the specific file later.
    """
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return _SHA256_ERROR_SENTINEL


def sha256_tree(path: Path) -> str:
    rows: list[str] = []
    for child in sorted(path.rglob("*")):
        if not child.is_file():
            continue
        relative = child.relative_to(path).as_posix()
        rows.append(f"{relative}\t{sha256_file(child)}\t{child.stat().st_size}")
    payload = "\n".join(rows).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def sha256_path(path: Path) -> str:
    if path.is_file():
        return sha256_file(path)
    if path.is_dir():
        return sha256_tree(path)
    raise FileNotFoundError(path)


def detect_path_kind(path: Path) -> str:
    if path.is_dir():
        return "tree"
    if path.is_file():
        return "file"
    raise FileNotFoundError(path)


def git(
    args: list[str],
    cwd: Path,
    check: bool = True,
    text: bool = True,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX"):
        env.pop(key, None)
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=check,
        text=text,
        capture_output=True,
        env=env,
    )


def repo_validation_command(repo_rel: str) -> str:
    quoted_repo = shlex.quote(Path(repo_rel).as_posix())
    env_prefix = "env -u GIT_DIR -u GIT_WORK_TREE -u GIT_INDEX_FILE -u GIT_PREFIX"
    return (
        f"{env_prefix} git -C {quoted_repo} rev-parse HEAD && "
        f"{env_prefix} git -C {quoted_repo} status --short --branch"
    )


def discover_nested_repos(root: Path) -> list[str]:
    repos: set[str] = set()
    for current_root, dirnames, filenames in os.walk(root):
        current = Path(current_root)
        if current == root / ".git":
            dirnames[:] = []
            continue
        dirnames[:] = [
            name
            for name in sorted(dirnames)
            if name != ".git"
            and not name.startswith(".git_decommissioned")
            and name != "__pycache__"
        ]
        if current != root and (current / ".git").exists():
            repos.add(relpath(current, root))
            dirnames[:] = []
            continue
        if ".git" in filenames:
            repos.add(relpath(current, root))
            dirnames[:] = []
    return sorted(repos)


def top_level_entries(root: Path) -> list[Path]:
    return sorted(
        [path for path in root.iterdir() if path.name != ".git"],
        key=lambda item: item.name.lower(),
    )


def is_archive_or_binary(path: Path) -> bool:
    suffix = path.suffix.lower()
    return suffix in ARCHIVE_EXTENSIONS or suffix in BINARY_EXTENSIONS


def iter_archive_artifacts(root: Path) -> list[Path]:
    artifacts: list[Path] = []
    for current_root, dirnames, filenames in os.walk(root):
        current = Path(current_root)
        dirnames[:] = [
            name
            for name in sorted(dirnames)
            if name != ".git"
            and not name.startswith(".git_decommissioned")
            and name != "__pycache__"
            and name != "_entropy_quarantine"
        ]
        if current != root and (current / ".git").exists():
            # Nested repos are opaque to the root control-plane inventory.
            dirnames[:] = []
            continue
        for filename in sorted(filenames):
            path = current / filename
            if is_archive_or_binary(path):
                artifacts.append(path)
    return sorted(artifacts, key=lambda item: relpath(item, root))


def normalize_family(name: str) -> str:
    stem = Path(name).stem.lower()
    stem = re.sub(r"\(\d+\)", "", stem)
    stem = re.sub(r"\s+\d+$", "", stem)
    stem = re.sub(r"[_-]?copy$", "", stem)
    stem = re.sub(r"\b\d{4}[-_]\d{2}[-_]\d{2}\b", "", stem)
    stem = re.sub(r"\b\d{8}\b", "", stem)
    stem = re.sub(r"[^a-z0-9]+", "-", stem)
    return stem.strip("-") or "unclassified"


def canonical_candidate(paths: list[str]) -> str:
    def score(path: str) -> tuple[int, int, str]:
        lowered = path.lower()
        preferred = 0
        if any(token in lowered for token in ("au_archive", "zip_archives", "zipwiz", "deploy")):
            preferred += 20
        if any(token in lowered for token in ("complete archive 4_19 copy", "unzipped archives")):
            preferred -= 20
        return (-preferred, len(Path(path).parts), path)

    return sorted(paths, key=score)[0]


def load_classification_overrides(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    raw = load_yaml_like(path) or {}
    if isinstance(raw, dict):
        rows = raw.get("overrides", [])
    elif isinstance(raw, list):
        rows = raw
    else:
        raise ValueError(f"Unsupported overrides payload in {path}")
    overrides: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or "current_path" not in row:
            raise ValueError(f"Invalid override row in {path}: {row!r}")
        overrides[str(row["current_path"])] = dict(row)
    return overrides


def top_level_policy_records(
    root: Path,
    overrides: dict[str, dict[str, Any]] | None = None,
    nested_repo_roots: set[str] | None = None,
) -> list[dict[str, Any]]:
    effective_overrides = (
        overrides
        if overrides is not None
        else load_classification_overrides(root / "catalog" / "classification_overrides.yaml")
    )
    effective_nested_repo_roots = (
        nested_repo_roots if nested_repo_roots is not None else set(discover_nested_repos(root))
    )
    return [
        apply_classification_override(
            classify_top_level(entry, root=root, nested_repo_roots=effective_nested_repo_roots),
            effective_overrides,
        )
        for entry in top_level_entries(root)
    ]


def manifest_enforced_current_paths(entries: list[dict[str, Any]]) -> set[str]:
    return {
        str(entry["current_path"])
        for entry in entries
        if str(entry.get("status", "")).strip() != "ignored"
    }


def apply_classification_override(
    entry: dict[str, Any],
    overrides: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    override = overrides.get(str(entry["current_path"]))
    if not override:
        return entry
    merged = dict(entry)
    for key, value in override.items():
        if key == "current_path":
            continue
        merged[key] = value
    return merged


def classify_top_level(entry: Path, root: Path, nested_repo_roots: set[str]) -> dict[str, str]:
    relative = relpath(entry, root)
    name = entry.name
    lowered = name.lower()

    def base_record(
        kind: str,
        logical_zone: str,
        planned_path: str,
        git_boundary: str,
        storage_tier: str,
        retention_policy: str,
        owner: str,
        status: str,
        batch_id: str = "",
    ) -> dict[str, str]:
        record = {
            "id": normalize_family(relative),
            "kind": kind,
            "current_path": relative,
            "logical_zone": logical_zone,
            "planned_path": planned_path,
            "git_boundary": git_boundary,
            "storage_tier": storage_tier,
            "retention_policy": retention_policy,
            "owner": owner,
            "status": status,
        }
        if batch_id:
            record["batch_id"] = batch_id
        return record

    if name in {"docs", "catalog", "tools"}:
        return base_record(
            kind="control_surface",
            logical_zone=name,
            planned_path=relative,
            git_boundary="root",
            storage_tier="workspace-control",
            retention_policy="versioned",
            owner="workspace-admin",
            status="managed",
        )
    if name in {"tests", "skills"}:
        return base_record(
            kind="control_surface",
            logical_zone="tools",
            planned_path=relative,
            git_boundary="root",
            storage_tier="workspace-control",
            retention_policy="versioned",
            owner="workspace-admin",
            status="managed",
        )
    if name == "reports":
        return base_record(
            kind="report_zone",
            logical_zone="reports",
            planned_path=relative,
            git_boundary="root",
            storage_tier="workspace-control",
            retention_policy="versioned",
            owner="operations",
            status="managed",
        )
    if name in {"archives", "intake", "repos", "projects", "_staging"}:
        return base_record(
            kind="logical_zone",
            logical_zone=name,
            planned_path=relative,
            git_boundary="root",
            storage_tier="workspace-control",
            retention_policy="versioned",
            owner="workspace-admin",
            status="managed",
        )
    if name in {".gitignore", ".gitattributes"}:
        return base_record(
            kind="policy_file",
            logical_zone="docs",
            planned_path=relative,
            git_boundary="root",
            storage_tier="workspace-control",
            retention_policy="versioned",
            owner="workspace-admin",
            status="managed",
        )
    if name == ".githooks":
        return base_record(
            kind="hook_policy",
            logical_zone="tools",
            planned_path=relative,
            git_boundary="root",
            storage_tier="workspace-control",
            retention_policy="versioned",
            owner="workspace-admin",
            status="managed",
        )
    if name in {"README.md", "AGENTS.md"}:
        return base_record(
            kind="workspace_doc",
            logical_zone="docs",
            planned_path=relative,
            git_boundary="root",
            storage_tier="workspace-control",
            retention_policy="versioned",
            owner="workspace-admin",
            status="managed",
        )
    if relative in SANCTIONED_ROOT_ANALYSIS_DOCS:
        return base_record(
            kind="analysis_report",
            logical_zone="reports",
            planned_path=relative,
            git_boundary="root",
            storage_tier="operational-report",
            retention_policy="versioned",
            owner="operations",
            status="managed",
        )
    if name.startswith(".git_decommissioned"):
        return base_record(
            kind="rollback_artifact",
            logical_zone="_staging",
            planned_path=relative,
            git_boundary="none",
            storage_tier="workspace-meta",
            retention_policy="preserve",
            owner="workspace-admin",
            status="protected",
        )
    if relative in nested_repo_roots or any(
        repo == relative or repo.startswith(f"{relative}/") for repo in nested_repo_roots
    ):
        return base_record(
            kind="repo_hub",
            logical_zone="repos",
            planned_path=relative,
            git_boundary="nested",
            storage_tier="source",
            retention_policy="preserve",
            owner="repository-owner",
            status="protected",
        )
    if name in LOCAL_ARTIFACT_NAMES or lowered.startswith(".pytest"):
        return base_record(
            kind="cache_or_local_artifact",
            logical_zone="_staging",
            planned_path=relative,
            git_boundary="none",
            storage_tier="ephemeral",
            retention_policy="regenerate",
            owner="local-user",
            status="ignored",
        )
    if name == "Automation_Reports":
        return base_record(
            kind="report_collection",
            logical_zone="reports",
            planned_path="reports/automation/archive-entropy-guard/2026-03-07",
            git_boundary="none",
            storage_tier="operational-report",
            retention_policy="archive-after-migration",
            owner="operations",
            status="planned_move",
        )
    if entry.is_dir() and any(token in lowered for token in ARCHIVE_ZONE_NAMES):
        return base_record(
            kind="archive_family",
            logical_zone="archives",
            planned_path=relative,
            git_boundary="none",
            storage_tier="cold-archive",
            retention_policy="quarantine-before-delete",
            owner="archive-admin",
            status="deferred",
        )
    if entry.is_file() and is_archive_or_binary(entry):
        return base_record(
            kind="archive_artifact",
            logical_zone="archives",
            planned_path=relative,
            git_boundary="none",
            storage_tier="cold-archive",
            retention_policy="quarantine-before-delete",
            owner="archive-admin",
            status="deferred",
        )
    if entry.is_file() and entry.suffix.lower() == ".md" and "report" in lowered:
        return base_record(
            kind="analysis_report",
            logical_zone="reports",
            planned_path=f"reports/analysis/{name}",
            git_boundary="none",
            storage_tier="operational-report",
            retention_policy="versioned",
            owner="operations",
            status="planned_move",
        )
    if entry.is_file() and entry.suffix.lower() in {
        ".md",
        ".yaml",
        ".yml",
        ".json",
        ".csv",
        ".py",
        ".txt",
        ".vsig",
    }:
        if name == "REPO_BOUNDARY_NOTICE.md":
            return base_record(
                kind="workspace_doc",
                logical_zone="docs",
                planned_path="docs/repo-boundary-notice.md",
                git_boundary="none",
                storage_tier="workspace-control",
                retention_policy="versioned",
                owner="workspace-admin",
                status="planned_move",
            )
        return base_record(
            kind="intake_file",
            logical_zone="intake",
            planned_path=f"intake/{name}",
            git_boundary="none",
            storage_tier="review",
            retention_policy="review",
            owner="intake-review",
            status="planned_move",
            batch_id=ROOT_INTAKE_CLEANUP_BATCH_ID,
        )
    if entry.is_file():
        return base_record(
            kind="intake_file",
            logical_zone="intake",
            planned_path=f"intake/{name}",
            git_boundary="none",
            storage_tier="review",
            retention_policy="review",
            owner="intake-review",
            status="planned_move",
            batch_id=ROOT_INTAKE_CLEANUP_BATCH_ID,
        )
    return base_record(
        kind="intake_collection",
        logical_zone="intake",
        planned_path=f"intake/{name}",
        git_boundary="none",
        storage_tier="review",
        retention_policy="review",
        owner="intake-review",
        status="planned_move",
        batch_id=ROOT_INTAKE_CLEANUP_BATCH_ID,
    )


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shlex
import subprocess
import zipfile
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
MAX_PRIVACY_PROBE_BYTES = 4096
MAX_PRIVACY_PROBE_PATHS = 24

PRIVACY_PROBE_EXTENSIONS = {
    ".md",
    ".markdown",
    ".txt",
    ".csv",
    ".json",
    ".jsonl",
    ".yaml",
    ".yml",
    ".toml",
}

PRIVATE_PATH_TOKENS = {
    "bank",
    "billing",
    "consent",
    "credit",
    "cv",
    "family",
    "finance",
    "financial",
    "health",
    "insurance",
    "job",
    "jobs",
    "legal",
    "medical",
    "passport",
    "password",
    "patient",
    "payroll",
    "personal",
    "private",
    "resume",
    "school",
    "schoolspring",
    "ssn",
    "tax",
    "taxes",
    "therapy",
}

PRIVATE_CONTENT_TERMS = (
    "bank account",
    "consent form",
    "cover letter",
    "credit card",
    "curriculum vitae",
    "date of birth",
    "driver license",
    "medical record",
    "patient name",
    "policy number",
    "social security",
    "therapy options",
)

PRIVATE_CONTENT_REGEXES = (
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:ssn|social security number)\b"),
    re.compile(r"\b(?:dob|date of birth)\b"),
    re.compile(r"\bpatient name\b"),
)

APPROVED_SCOPE_TOKENS = {
    "aurora",
    "orion",
    "gumas",
    "qgia",
    "cloudbank",
    "canonrec",
    "duelsim",
    "threadcore",
    "zipwiz",
    "qem",
    "charforge",
    "forecast",
}

OFFICE_PROBE_MEMBER_NAMES = (
    "word/document.xml",
    "docProps/core.xml",
    "docProps/app.xml",
    "xl/sharedStrings.xml",
    "xl/workbook.xml",
    "ppt/slides/slide1.xml",
    "ppt/presentation.xml",
)


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


def _parse_yaml_scalar(value: str) -> Any:
    if value == "":
        return ""
    if value == "[]":
        return []
    if value == "{}":
        return {}

    lowered = value.lower()
    if lowered in {"null", "~"}:
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False

    if value.startswith("'") and value.endswith("'") and len(value) >= 2:
        return value[1:-1].replace("''", "'")
    if value.startswith('"') and value.endswith('"') and len(value) >= 2:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value[1:-1]

    if re.fullmatch(r"-?(0|[1-9]\d*)", value):
        return int(value)
    if re.fullmatch(r"-?(0|[1-9]\d*)\.\d+", value):
        return float(value)

    return value


def _yaml_key_value(text: str) -> tuple[str, str]:
    if ":" not in text:
        raise ValueError(f"Unsupported YAML line without key/value separator: {text!r}")
    key, value = text.split(":", 1)
    key = key.strip()
    if not key:
        raise ValueError(f"Unsupported YAML line with empty key: {text!r}")
    return key, value.lstrip()


def _yaml_folded_scalar(
    lines: list[tuple[int, str]],
    index: int,
    parent_indent: int,
    initial: str,
) -> tuple[Any, int]:
    parts = [initial.strip()]
    while index < len(lines):
        next_indent, next_content = lines[index]
        if next_indent <= parent_indent:
            break
        parts.append(next_content.strip())
        index += 1
    return _parse_yaml_scalar(" ".join(part for part in parts if part)), index


def _is_yaml_list_item(content: str) -> bool:
    return content == "-" or content.startswith("- ")


def _looks_like_yaml_mapping_entry(text: str) -> bool:
    if ":" not in text:
        return False
    key, remainder = text.split(":", 1)
    key = key.strip()
    return bool(key) and bool(_YAML_KEY_PATTERN.fullmatch(key)) and (remainder == "" or remainder.startswith(" "))


def _load_yaml_subset(text: str) -> Any:
    lines: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        stripped = raw_line.lstrip(" ")
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw_line) - len(stripped)
        lines.append((indent, stripped.rstrip()))

    def parse_block(source_lines: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
        if index >= len(source_lines):
            return None, index
        current_indent, current_content = source_lines[index]
        if current_indent < indent:
            return None, index
        if current_indent != indent:
            raise ValueError(f"Unsupported YAML indentation at line {index + 1}: expected {indent}, got {current_indent}")
        if _is_yaml_list_item(current_content):
            return parse_list(source_lines, index, indent)
        return parse_dict(source_lines, index, indent)

    def parse_dict(
        source_lines: list[tuple[int, str]],
        index: int,
        indent: int,
    ) -> tuple[dict[str, Any], int]:
        result: dict[str, Any] = {}
        while index < len(source_lines):
            current_indent, content = source_lines[index]
            if current_indent < indent:
                break
            if current_indent != indent:
                raise ValueError(f"Unsupported YAML indentation at line {index + 1}: expected {indent}, got {current_indent}")
            if _is_yaml_list_item(content):
                raise ValueError(f"Unexpected YAML sequence item in mapping at line {index + 1}")

            key, raw_value = _yaml_key_value(content)
            index += 1
            if raw_value == "":
                if index < len(source_lines):
                    next_indent, next_content = source_lines[index]
                    if next_indent > indent:
                        value, index = parse_block(source_lines, index, next_indent)
                    elif next_indent == indent and _is_yaml_list_item(next_content):
                        value, index = parse_list(source_lines, index, indent)
                    else:
                        value = None
                else:
                    value = None
            else:
                value, index = _yaml_folded_scalar(source_lines, index, indent, raw_value)
            result[key] = value
        return result, index

    def parse_list(
        source_lines: list[tuple[int, str]],
        index: int,
        indent: int,
    ) -> tuple[list[Any], int]:
        result: list[Any] = []
        while index < len(source_lines):
            current_indent, content = source_lines[index]
            if current_indent < indent:
                break
            if current_indent != indent:
                raise ValueError(f"Unsupported YAML indentation at line {index + 1}: expected {indent}, got {current_indent}")
            if not _is_yaml_list_item(content):
                break

            item_content = content[1:].strip()
            index += 1
            if item_content == "":
                if index < len(source_lines) and source_lines[index][0] > indent:
                    value, index = parse_block(source_lines, index, source_lines[index][0])
                else:
                    value = None
            elif _looks_like_yaml_mapping_entry(item_content):
                synthetic_indent = indent + 2
                synthetic_lines = [(synthetic_indent, item_content), *source_lines[index:]]
                value, consumed = parse_dict(synthetic_lines, 0, synthetic_indent)
                index += consumed - 1
            else:
                value, index = _yaml_folded_scalar(source_lines, index, indent, item_content)
            result.append(value)
        return result, index

    if not lines:
        return None
    parsed, next_index = parse_block(lines, 0, lines[0][0])
    if next_index != len(lines):
        raise ValueError("Unsupported trailing YAML content")
    return parsed


_YAML_KEY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")


def _yaml_key(key: str) -> str:
    if not _YAML_KEY_PATTERN.fullmatch(key):
        raise TypeError(f"Unsupported YAML key for fallback serializer: {key!r}")
    return key


def _dump_yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return json.dumps(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=True)
    if isinstance(value, list) and not value:
        return "[]"
    if isinstance(value, dict) and not value:
        return "{}"
    raise TypeError(f"Unsupported YAML scalar for fallback serializer: {type(value).__name__}")


def _dump_yaml_subset(value: Any, indent: int = 0) -> list[str]:
    prefix = " " * indent

    if isinstance(value, dict):
        if not value:
            return [prefix + "{}"]

        lines: list[str] = []
        for key, item in value.items():
            rendered_key = _yaml_key(str(key))
            if isinstance(item, (dict, list)) and item:
                lines.append(f"{prefix}{rendered_key}:")
                lines.extend(_dump_yaml_subset(item, indent + 2))
            else:
                lines.append(f"{prefix}{rendered_key}: {_dump_yaml_scalar(item)}")
        return lines

    if isinstance(value, list):
        if not value:
            return [prefix + "[]"]

        lines = []
        for item in value:
            if isinstance(item, (dict, list)) and item:
                lines.append(f"{prefix}-")
                lines.extend(_dump_yaml_subset(item, indent + 2))
            else:
                lines.append(f"{prefix}- {_dump_yaml_scalar(item)}")
        return lines

    return [prefix + _dump_yaml_scalar(value)]


def load_yaml_like(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        return yaml.safe_load(text)
    except Exception:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return _load_yaml_subset(text)


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
        # Keep generated control surfaces in a stable YAML subset even when PyYAML is unavailable.
        rendered = "\n".join(_dump_yaml_subset(data)) + "\n"
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
        if current != root and ".git" in filenames:
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


def stable_entry_id(name: str) -> str:
    lowered = name.lower()
    if lowered.startswith("."):
        lowered = f"dot-{lowered[1:]}"
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    return lowered.strip("-") or "unclassified"


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


def normalized_tokens(text: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", text.lower()) if token}


def iter_privacy_probe_paths(entry: Path) -> list[Path]:
    if not entry.exists():
        return []
    if entry.is_file():
        return [entry]

    samples = [entry]
    for current_root, dirnames, filenames in os.walk(entry):
        current = Path(current_root)
        dirnames[:] = [
            name
            for name in sorted(dirnames)
            if name != ".git"
            and not name.startswith(".git_decommissioned")
            and name != "__pycache__"
        ]
        if current != entry and (current / ".git").exists():
            dirnames[:] = []
            continue

        for name in sorted(dirnames):
            samples.append(current / name)
            if len(samples) >= MAX_PRIVACY_PROBE_PATHS:
                return samples
        for name in sorted(filenames):
            samples.append(current / name)
            if len(samples) >= MAX_PRIVACY_PROBE_PATHS:
                return samples
    return samples


def read_privacy_probe_text(path: Path) -> str:
    if not path.is_file():
        return ""
    suffix = path.suffix.lower()
    if suffix in {".docx", ".xlsx", ".pptx"}:
        return read_zip_privacy_probe_text(path)

    try:
        with path.open("rb") as handle:
            payload = handle.read(MAX_PRIVACY_PROBE_BYTES)
    except OSError:
        return ""
    if suffix in PRIVACY_PROBE_EXTENSIONS:
        return payload.decode("utf-8", errors="ignore").lower()
    if suffix == ".pdf" or payload.startswith(b"%PDF"):
        return extract_ascii_probe_text(payload)
    if payload.startswith(b"PK\x03\x04"):
        return read_zip_privacy_probe_text(path)
    return ""


def extract_ascii_probe_text(payload: bytes) -> str:
    decoded = payload.decode("utf-8", errors="ignore").lower()
    fragments = re.findall(r"[a-z][a-z0-9:/ _.\-]{3,}", decoded)
    return " ".join(fragments)


def read_zip_privacy_probe_text(path: Path) -> str:
    snippets: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            members = set(archive.namelist())
            for member in OFFICE_PROBE_MEMBER_NAMES:
                if member not in members:
                    continue
                with archive.open(member) as handle:
                    payload = handle.read(MAX_PRIVACY_PROBE_BYTES)
                text = extract_ascii_probe_text(payload)
                if text:
                    snippets.append(text)
    except (OSError, KeyError, zipfile.BadZipFile, RuntimeError):
        return ""
    return " ".join(snippets)


def detect_private_signal(entry: Path) -> str:
    saw_private_content = False
    for probe in iter_privacy_probe_paths(entry):
        relative_name = probe.name if probe == entry else probe.relative_to(entry).as_posix()
        if normalized_tokens(relative_name) & PRIVATE_PATH_TOKENS:
            return "auto_private_path"

        text = read_privacy_probe_text(probe)
        if not text:
            continue
        if any(pattern.search(text) for pattern in PRIVATE_CONTENT_REGEXES):
            saw_private_content = True
            break
        term_hits = sum(1 for term in PRIVATE_CONTENT_TERMS if term in text)
        if term_hits >= 2:
            saw_private_content = True
            break
    return "auto_private_content" if saw_private_content else ""


def detect_scope_signal(entry: Path) -> str:
    for probe in iter_privacy_probe_paths(entry):
        relative_name = probe.name if probe == entry else probe.relative_to(entry).as_posix()
        if normalized_tokens(relative_name) & APPROVED_SCOPE_TOKENS:
            return "approved_scope_path"

        text = read_privacy_probe_text(probe)
        if text and normalized_tokens(text) & APPROVED_SCOPE_TOKENS:
            return "approved_scope_content"
    return ""


def is_probably_private_path(entry: Path) -> bool:
    return bool(detect_private_signal(entry))


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


def scan_policy_for_entry(
    entry: Path,
    root: Path,
    overrides: dict[str, dict[str, Any]],
) -> str:
    candidate_record = apply_classification_override(
        classify_top_level(entry, root=root, nested_repo_roots=set()),
        overrides,
    )
    return privacy_decision_for_entry(
        entry,
        root,
        candidate_record,
        overrides,
    )["policy"]


def privacy_decision_for_entry(
    entry: Path,
    root: Path,
    candidate_record: dict[str, Any],
    overrides: dict[str, dict[str, Any]],
) -> dict[str, str]:
    current_path = relpath(entry, root)
    override = overrides.get(current_path)
    value = override.get("scan_policy") if override else None
    policy = str(value).strip().lower() if value is not None else ""
    if policy in {"include", "omit"}:
        return {
            "policy": policy,
            "reason": f"override_{policy}",
        }
    candidate_status = str(candidate_record.get("status", "")).strip()
    if candidate_status in {"managed", "protected"}:
        return {
            "policy": "",
            "reason": "",
        }
    signal = detect_private_signal(entry)
    if signal:
        return {
            "policy": "omit",
            "reason": signal,
        }
    if str(candidate_record.get("status", "")).strip() == "planned_move" and not detect_scope_signal(entry):
        return {
            "policy": "omit",
            "reason": "auto_scope_unknown",
        }
    return {
        "policy": "",
        "reason": "",
    }


def dedupe_policy_record_ids(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        grouped.setdefault(str(entry["id"]), []).append(entry)

    updated_entries: list[dict[str, Any]] = []
    for entry in entries:
        duplicates = grouped[str(entry["id"])]
        if len(duplicates) == 1:
            updated_entries.append(entry)
            continue
        updated = dict(entry)
        updated["id"] = stable_entry_id(str(entry["current_path"]))
        updated_entries.append(updated)

    deduped: list[dict[str, Any]] = []
    reassigned_counts: dict[str, int] = {}
    for entry in updated_entries:
        updated = dict(entry)
        key = str(updated["id"])
        count = reassigned_counts.get(key, 0) + 1
        reassigned_counts[key] = count
        if count > 1:
            updated["id"] = f"{key}-{count}"
        deduped.append(updated)
    return deduped


def top_level_policy_records_with_redaction(
    root: Path,
    overrides: dict[str, dict[str, Any]] | None = None,
    nested_repo_roots: set[str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, int], set[str]]:
    effective_overrides = (
        overrides
        if overrides is not None
        else load_classification_overrides(root / "catalog" / "classification_overrides.yaml")
    )
    effective_nested_repo_roots = (
        nested_repo_roots if nested_repo_roots is not None else set(discover_nested_repos(root))
    )
    redacted_counts: dict[str, int] = {}
    redacted_paths: set[str] = set()
    entries: list[dict[str, Any]] = []
    for entry in top_level_entries(root):
        candidate_record = apply_classification_override(
            classify_top_level(
                entry,
                root=root,
                nested_repo_roots=effective_nested_repo_roots,
            ),
            effective_overrides,
        )
        decision = privacy_decision_for_entry(entry, root, candidate_record, effective_overrides)
        if decision["policy"] == "omit":
            reason = decision["reason"] or "omit"
            redacted_counts[reason] = redacted_counts.get(reason, 0) + 1
            redacted_paths.add(relpath(entry, root))
            continue
        entries.append(candidate_record)
    return dedupe_policy_record_ids(entries), redacted_counts, redacted_paths


def top_level_policy_records(
    root: Path,
    overrides: dict[str, dict[str, Any]] | None = None,
    nested_repo_roots: set[str] | None = None,
) -> list[dict[str, Any]]:
    entries, _, _ = top_level_policy_records_with_redaction(
        root,
        overrides=overrides,
        nested_repo_roots=nested_repo_roots,
    )
    return entries


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
    if name in {".devcontainer", ".github", "Makefile"}:
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
    if name == ".pre-commit-config.yaml":
        return base_record(
            kind="policy_file",
            logical_zone="tools",
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
        canonical_report_path = root / "reports" / "analysis" / name
        if canonical_report_path.exists():
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

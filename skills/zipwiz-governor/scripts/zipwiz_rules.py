#!/usr/bin/env python3
"""Deterministic ZIPWIZ family detection and governance validation rules."""

from __future__ import annotations

import fnmatch
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_CANONICAL_ROOTS = [
    "projects/GUMAS_SIM_2.0/05_BUILD_TOOLS/ZipWiz_Packaging",
    "GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main",
    "GUMAS_SIM_2.5/SIM_HARVEST_26",
]

DEFAULT_REFERENCE_ROOTS = [
    "archives/unzipped/ZipWiz_Chamber_6_28/ZIPWIZ_Documents",
    "reports/analysis/non_can_reports/ZIPWIZ_CHAMBER_TECHNICAL_REFERENCE.md",
]

DEFAULT_EXCLUDE_PATTERNS = [
    "**/Unzipped Archives/**",
    "**/06_ARCHIVES/**",
    "**/_REDUNDANT_FILES_ARCHIVED/**",
    "**/docs/operational/archived/**",
    "**/.venv/**",
    "**/*.zip",
]

VALID_ANCHOR_SEED = "EOS_SEED_ORION"
VALID_ETHICS_PROTOCOL = "Picard_Delta_3"
REPORT_DOMAIN = "zipwiz"
SEVERITY_ORDER = {"BLOCK": 0, "WARN": 1, "INFO": 2}

_JSON_SUFFIX = ".json"
_TEXT_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".py", ".js"}
_CANDIDATE_SUFFIXES = _TEXT_SUFFIXES | {_JSON_SUFFIX}

_ZIPWIZ_TOKENS = (
    "zipwiz",
    "zipwizard",
    "bundle.manifest",
    "bundle_manifest",
    "staging_manifest",
    "beacon",
    "manifest",
    "packaging",
    "protocol",
    "zipcomm",
)

_RUNTIME_HINTS = (
    "scripts/zipwiz.py",
    "services/command_node/modules/zipwiz.js",
    "src/core/zipcomm.js",
)

_HANDSHAKE_SEQUENCE = "ZIPWIZ_BEACON -> ANCHOR_SYNC -> ETHICS_AUDIT -> DRIFT_VALIDATION"
_FRONTMATTER_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_\-]*)\s*:\s*(.+?)\s*$")
_DATE_RE = re.compile(r"(20\d{2}-\d{2}-\d{2})")
_VERSION_RE = re.compile(r"\bv\d+(?:\.\d+)*(?:[a-z])?\b", re.IGNORECASE)
_CANONICAL_ROLES = {"document_bundle", "index", "manifest", "beacon", "other"}
_ROLE_NORMALIZATION_MAP = {
    "asset": "manifest",
    "staging_manifest": "manifest",
    "schema": "manifest",
    "entrypoint": "index",
    "provenance": "other",
    "data": "document_bundle",
    "markdown": "document_bundle",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _to_path(repo_root: Path, raw_root: str) -> Path:
    p = Path(raw_root)
    if p.is_absolute():
        return p
    return (repo_root / p).resolve()


def _relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def _is_excluded(rel_path: str, exclusions: list[str]) -> bool:
    normalized = rel_path.replace("\\", "/")
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in exclusions)


def _looks_like_zipwiz(rel_path: str) -> bool:
    lowered = rel_path.lower()
    return any(token in lowered for token in _ZIPWIZ_TOKENS)


def _is_runtime_path(rel_path: str) -> bool:
    lowered = rel_path.lower()
    return any(lowered.endswith(hint) for hint in _RUNTIME_HINTS)


def _iter_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    if not root.exists() or not root.is_dir():
        return []
    return [path for path in root.rglob("*") if path.is_file()]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _load_json(text: str) -> tuple[Any | None, str | None]:
    try:
        return json.loads(text), None
    except json.JSONDecodeError as exc:
        return None, str(exc)


def _parse_frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    out: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = _FRONTMATTER_KEY_RE.match(line)
        if match:
            out[match.group(1).strip().lower()] = match.group(2).strip().strip('"').strip("'")
    return out


def _get_nested(data: dict[str, Any], dotted: str) -> Any:
    current: Any = data
    for key in dotted.split("."):
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _has_nonempty(data: dict[str, Any], dotted: str) -> bool:
    value = _get_nested(data, dotted)
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def _adjust_severity(base: str, strictness: str, kind: str, family: str) -> str:
    level = base.upper()
    mode = strictness.lower()
    if mode == "strict" and level == "WARN" and family != "evolution_evidence":
        return "BLOCK"
    if mode == "lenient" and level == "BLOCK" and kind not in {"parse", "frontmatter", "missing_core_identity"}:
        return "WARN"
    return level


def _routing_hint(family: str) -> str:
    if family == "runtime_alignment":
        return (
            "Keep ZIPWIZ runtime alignment local. If remediation expands into broad script hardening, "
            "handoff to aurora-script-governor or aurora-repo-stabilizer."
        )
    if family == "evolution_evidence":
        return "Reference-only timeline evidence. Do not treat as canonical blocking input."
    return "Handled within zipwiz-governor scope."


def _make_finding(
    *,
    strictness: str,
    source_class: str,
    severity: str,
    rule_id: str,
    family: str,
    file_path: str,
    message: str,
    suggested_fix: str,
    kind: str = "core",
) -> dict[str, Any]:
    adjusted = _adjust_severity(severity, strictness, kind, family)
    if source_class == "reference_only" and adjusted == "BLOCK":
        adjusted = "WARN"
    blocking_scope = "reference_only" if source_class == "reference_only" or family == "evolution_evidence" else "authoritative"
    return {
        "domain": REPORT_DOMAIN,
        "severity": adjusted,
        "rule_id": rule_id,
        "family": family,
        "file": file_path,
        "source_path": file_path,
        "message": message,
        "rationale": message,
        "evidence": "",
        "remediation": suggested_fix,
        "suggested_fix": suggested_fix,
        "routing_hint": _routing_hint(family),
        "blocking_scope": blocking_scope,
        "source_tool": "zipwiz-governance-scan",
    }


def _detect_family(path: Path, rel_path: str, text: str, payload: Any, source_class: str) -> str | None:
    if source_class == "reference_only":
        return "evolution_evidence"

    lowered = rel_path.lower()
    name = path.name.lower()
    suffix = path.suffix.lower()

    if _is_runtime_path(lowered):
        return "runtime_alignment"

    if suffix == ".md":
        fm = _parse_frontmatter(text)
        docid = fm.get("docid", "").lower()
        if "zipwiz" in docid and "packaging" in docid and "protocol" in docid:
            return "zipwiz_protocol_doc"
        if "zipwiz_packaging_protocol" in name:
            return "zipwiz_protocol_doc"

    if suffix != _JSON_SUFFIX or not isinstance(payload, dict):
        return None

    if name.endswith('.schema.json') or '.schema.' in name:
        return None

    if "bundle.manifest" in name or "bundle_manifest" in name:
        return "bundle_manifest"

    if name.startswith("staging_manifest") or "staging_manifest" in name:
        return "staging_manifest"

    if "beacon" in name and "capsule" in name:
        return "beacon_capsule"

    if str(payload.get("Output_Format", "")).lower() == ".beacon.json":
        return "beacon_capsule"

    if _looks_like_zipwiz(rel_path) and "bundle_id" in payload and ("contents" in payload or "files" in payload):
        return "bundle_manifest"

    return None


def _extract_identity(family: str, payload: Any) -> tuple[str | None, dict[str, Any]]:
    identity_fields: dict[str, Any] = {}
    if family == "bundle_manifest" and isinstance(payload, dict):
        identity_fields["bundle_id"] = payload.get("bundle_id")
        value = payload.get("bundle_id")
        return (str(value) if value else None, identity_fields)

    if family == "staging_manifest" and isinstance(payload, dict):
        identity_fields["bundle"] = payload.get("bundle")
        identity_fields["build"] = payload.get("build")
        value = payload.get("bundle")
        return (str(value) if value else None, identity_fields)

    if family == "zipwiz_protocol_doc" and isinstance(payload, dict):
        identity_fields["docid"] = payload.get("docid")
        value = payload.get("docid")
        return (str(value) if value else None, identity_fields)

    if family == "beacon_capsule" and isinstance(payload, dict):
        identity_fields["Designation"] = payload.get("Designation")
        identity_fields["Thread_Metadata.Thread_Name"] = _get_nested(payload, "Thread_Metadata.Thread_Name")
        value = payload.get("Designation")
        return (str(value) if value else None, identity_fields)

    if family == "evolution_evidence" and isinstance(payload, dict):
        value = payload.get("source_file")
        identity_fields["source_file"] = value
        return (str(value) if value else None, identity_fields)

    return (None, identity_fields)


def _validate_bundle_manifest(
    *,
    strictness: str,
    source_class: str,
    file_path: str,
    payload: dict[str, Any],
    findings: list[dict[str, Any]],
) -> None:
    if not _has_nonempty(payload, "bundle_id"):
        findings.append(
            _make_finding(
                strictness=strictness,
                source_class=source_class,
                severity="BLOCK",
                rule_id="B_BUNDLE_MANIFEST_MISSING_BUNDLE_ID",
                family="bundle_manifest",
                file_path=file_path,
                message="Bundle manifest is missing required key 'bundle_id'.",
                suggested_fix="Add a stable ZIPWIZ bundle_id string.",
            )
        )

    if not (_has_nonempty(payload, "created_at") or _has_nonempty(payload, "created_at_utc")):
        findings.append(
            _make_finding(
                strictness=strictness,
                source_class=source_class,
                severity="BLOCK",
                rule_id="B_BUNDLE_MANIFEST_MISSING_CREATED_AT",
                family="bundle_manifest",
                file_path=file_path,
                message="Bundle manifest must include created_at or created_at_utc.",
                suggested_fix="Set created_at (preferred ISO-8601) or created_at_utc.",
            )
        )

    if _has_nonempty(payload, "created_at_utc") and not _has_nonempty(payload, "created_at"):
        findings.append(
            _make_finding(
                strictness=strictness,
                source_class=source_class,
                severity="INFO",
                rule_id="I_BUNDLE_CREATED_AT_UTC_MAPPABLE",
                family="bundle_manifest",
                file_path=file_path,
                message="Using created_at_utc without created_at (schema variant).",
                suggested_fix="Optional normalization: add created_at while preserving created_at_utc.",
            )
        )

    anchor = payload.get("anchor_seed")
    if not anchor:
        findings.append(
            _make_finding(
                strictness=strictness,
                source_class=source_class,
                severity="BLOCK",
                rule_id="B_BUNDLE_MANIFEST_MISSING_ANCHOR",
                family="bundle_manifest",
                file_path=file_path,
                message="Bundle manifest is missing required key 'anchor_seed'.",
                suggested_fix=f"Set anchor_seed to '{VALID_ANCHOR_SEED}'.",
            )
        )
    elif str(anchor) != VALID_ANCHOR_SEED:
        findings.append(
            _make_finding(
                strictness=strictness,
                source_class=source_class,
                severity="BLOCK",
                rule_id="B_BUNDLE_MANIFEST_INVALID_ANCHOR",
                family="bundle_manifest",
                file_path=file_path,
                message=f"anchor_seed '{anchor}' is noncanonical.",
                suggested_fix=f"Use anchor_seed '{VALID_ANCHOR_SEED}'.",
            )
        )

    ethics = payload.get("ethics_protocol")
    if not ethics:
        findings.append(
            _make_finding(
                strictness=strictness,
                source_class=source_class,
                severity="BLOCK",
                rule_id="B_BUNDLE_MANIFEST_MISSING_ETHICS",
                family="bundle_manifest",
                file_path=file_path,
                message="Bundle manifest is missing required key 'ethics_protocol'.",
                suggested_fix=f"Set ethics_protocol to '{VALID_ETHICS_PROTOCOL}'.",
            )
        )
    elif str(ethics) != VALID_ETHICS_PROTOCOL:
        findings.append(
            _make_finding(
                strictness=strictness,
                source_class=source_class,
                severity="BLOCK",
                rule_id="B_BUNDLE_MANIFEST_INVALID_ETHICS",
                family="bundle_manifest",
                file_path=file_path,
                message=f"ethics_protocol '{ethics}' is noncanonical.",
                suggested_fix=f"Use ethics_protocol '{VALID_ETHICS_PROTOCOL}'.",
            )
        )

    entries = payload.get("contents")
    using_files_variant = False
    if not isinstance(entries, list):
        entries = payload.get("files")
        using_files_variant = isinstance(entries, list)

    if not isinstance(entries, list) or not entries:
        findings.append(
            _make_finding(
                strictness=strictness,
                source_class=source_class,
                severity="BLOCK",
                rule_id="B_BUNDLE_MANIFEST_MISSING_ENTRIES",
                family="bundle_manifest",
                file_path=file_path,
                message="Bundle manifest must include non-empty contents[] or files[].",
                suggested_fix="Add file entries with path, hash, and size fields.",
            )
        )
        return

    if using_files_variant:
        findings.append(
            _make_finding(
                strictness=strictness,
                source_class=source_class,
                severity="INFO",
                rule_id="I_BUNDLE_FILES_VARIANT_MAPPABLE",
                family="bundle_manifest",
                file_path=file_path,
                message="Using files[] variant instead of schema-native contents[].",
                suggested_fix="Optional normalization: convert files[] to contents[].",
            )
        )

    role_normalizations: Counter[str] = Counter()
    unknown_roles: set[str] = set()
    size_variant_mappable = 0
    size_variant_unmappable = 0

    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            findings.append(
                _make_finding(
                    strictness=strictness,
                    source_class=source_class,
                    severity="BLOCK",
                    rule_id="B_BUNDLE_ENTRY_NOT_OBJECT",
                    family="bundle_manifest",
                    file_path=file_path,
                    message=f"Entry {idx} in bundle manifest must be an object.",
                    suggested_fix="Replace malformed entry with object containing path/hash/size.",
                )
            )
            continue

        hash_value = entry.get("sha256")
        if not isinstance(hash_value, str) or not re.fullmatch(r"[A-Fa-f0-9]{64}", hash_value):
            findings.append(
                _make_finding(
                    strictness=strictness,
                    source_class=source_class,
                    severity="BLOCK",
                    rule_id="B_BUNDLE_HASH_INVALID",
                    family="bundle_manifest",
                    file_path=file_path,
                    message=f"Entry {idx} has invalid sha256 value.",
                    suggested_fix="Use 64-character hex SHA256 digests for all entries.",
                )
            )

        if using_files_variant and "size_bytes" not in entry:
            if isinstance(entry.get("bytes"), int) and entry.get("bytes", 0) >= 0:
                size_variant_mappable += 1
            else:
                size_variant_unmappable += 1

        role = entry.get("role")
        if isinstance(role, str):
            normalized = role.strip().lower()
            if normalized in _CANONICAL_ROLES:
                continue
            mapped = _ROLE_NORMALIZATION_MAP.get(normalized)
            if mapped:
                role_normalizations[f"{normalized}->{mapped}"] += 1
            else:
                unknown_roles.add(normalized)

    if using_files_variant:
        if size_variant_unmappable > 0:
            findings.append(
                _make_finding(
                    strictness=strictness,
                    source_class=source_class,
                    severity="WARN",
                    rule_id="W_BUNDLE_SIZE_BYTES_VARIANT",
                    family="bundle_manifest",
                    file_path=file_path,
                    message=(
                        f"{size_variant_unmappable} entry/entries use non-mappable size fields "
                        "while files[] variant is active."
                    ),
                    suggested_fix="Ensure each files[] entry has numeric bytes or canonical size_bytes.",
                )
            )
        elif size_variant_mappable > 0:
            findings.append(
                _make_finding(
                    strictness=strictness,
                    source_class=source_class,
                    severity="INFO",
                    rule_id="I_BUNDLE_SIZE_BYTES_MAPPABLE",
                    family="bundle_manifest",
                    file_path=file_path,
                    message=(
                        f"{size_variant_mappable} entry/entries use bytes instead of size_bytes; "
                        "mapping is straightforward."
                    ),
                    suggested_fix="Optional normalization: bytes -> size_bytes for schema parity.",
                )
            )

    if role_normalizations:
        mapping_text = ", ".join(f"{k} ({v})" for k, v in sorted(role_normalizations.items()))
        findings.append(
            _make_finding(
                strictness=strictness,
                source_class=source_class,
                severity="INFO",
                rule_id="I_BUNDLE_ROLE_NORMALIZED",
                family="bundle_manifest",
                file_path=file_path,
                message=f"Normalized legacy role aliases: {mapping_text}.",
                suggested_fix="Optional normalization applied in report only; source rewrite is not required.",
            )
        )

    if unknown_roles:
        sample = ", ".join(sorted(unknown_roles)[:6])
        findings.append(
            _make_finding(
                strictness=strictness,
                source_class=source_class,
                severity="WARN",
                rule_id="W_BUNDLE_ROLE_DRIFT",
                family="bundle_manifest",
                file_path=file_path,
                message=f"Detected unmapped noncanonical role value(s): {sample}.",
                suggested_fix="Map roles to document_bundle/index/manifest/beacon/other.",
            )
        )


def _validate_staging_manifest(
    *,
    strictness: str,
    source_class: str,
    file_path: str,
    payload: dict[str, Any],
    findings: list[dict[str, Any]],
) -> None:
    required = [
        "staging_bay",
        "bundle",
        "generated_at_local",
        "build",
        "classification.layer",
        "classification.domain",
        "files",
    ]
    for key in required:
        if not _has_nonempty(payload, key):
            findings.append(
                _make_finding(
                    strictness=strictness,
                    source_class=source_class,
                    severity="BLOCK",
                    rule_id="B_STAGING_MANIFEST_REQUIRED_FIELD",
                    family="staging_manifest",
                    file_path=file_path,
                    message=f"Staging manifest missing required field: {key}.",
                    suggested_fix=f"Populate staging manifest field '{key}'.",
                )
            )

    files = payload.get("files")
    if not isinstance(files, list):
        return

    for idx, entry in enumerate(files):
        if not isinstance(entry, dict):
            findings.append(
                _make_finding(
                    strictness=strictness,
                    source_class=source_class,
                    severity="BLOCK",
                    rule_id="B_STAGING_ENTRY_NOT_OBJECT",
                    family="staging_manifest",
                    file_path=file_path,
                    message=f"files[{idx}] must be an object.",
                    suggested_fix="Replace malformed files[] entry with object fields.",
                )
            )
            continue

        for key in ("path", "role", "sha256", "bytes"):
            if key not in entry:
                findings.append(
                    _make_finding(
                        strictness=strictness,
                        source_class=source_class,
                        severity="BLOCK",
                        rule_id="B_STAGING_ENTRY_REQUIRED_FIELD",
                        family="staging_manifest",
                        file_path=file_path,
                        message=f"files[{idx}] missing required key '{key}'.",
                        suggested_fix="Ensure each files[] entry includes path, role, sha256, and bytes.",
                    )
                )

        hash_value = entry.get("sha256")
        if isinstance(hash_value, str) and not re.fullmatch(r"[A-Fa-f0-9]{64}", hash_value):
            findings.append(
                _make_finding(
                    strictness=strictness,
                    source_class=source_class,
                    severity="BLOCK",
                    rule_id="B_STAGING_HASH_INVALID",
                    family="staging_manifest",
                    file_path=file_path,
                    message=f"files[{idx}] has invalid sha256 value.",
                    suggested_fix="Use 64-character hex SHA256 digests.",
                )
            )


def _validate_protocol_doc(
    *,
    strictness: str,
    source_class: str,
    file_path: str,
    frontmatter: dict[str, str],
    findings: list[dict[str, Any]],
) -> None:
    required = ["docid", "doctype", "version", "anchor_seed", "ethics_protocol"]
    for key in required:
        if not frontmatter.get(key):
            findings.append(
                _make_finding(
                    strictness=strictness,
                    source_class=source_class,
                    severity="BLOCK",
                    rule_id="B_PROTOCOL_FRONTMATTER_REQUIRED_FIELD",
                    family="zipwiz_protocol_doc",
                    file_path=file_path,
                    message=f"ZIPWIZ protocol frontmatter missing '{key}'.",
                    suggested_fix=f"Add frontmatter key '{key}' with canonical value.",
                    kind="frontmatter",
                )
            )

    anchor = frontmatter.get("anchor_seed")
    if anchor and anchor != VALID_ANCHOR_SEED:
        findings.append(
            _make_finding(
                strictness=strictness,
                source_class=source_class,
                severity="BLOCK",
                rule_id="B_PROTOCOL_ANCHOR_INVALID",
                family="zipwiz_protocol_doc",
                file_path=file_path,
                message=f"Protocol anchor_seed '{anchor}' is noncanonical.",
                suggested_fix=f"Use anchor_seed '{VALID_ANCHOR_SEED}'.",
            )
        )

    ethics = frontmatter.get("ethics_protocol")
    if ethics and ethics != VALID_ETHICS_PROTOCOL:
        findings.append(
            _make_finding(
                strictness=strictness,
                source_class=source_class,
                severity="BLOCK",
                rule_id="B_PROTOCOL_ETHICS_INVALID",
                family="zipwiz_protocol_doc",
                file_path=file_path,
                message=f"Protocol ethics_protocol '{ethics}' is noncanonical.",
                suggested_fix=f"Use ethics_protocol '{VALID_ETHICS_PROTOCOL}'.",
            )
        )

    if frontmatter.get("authority", "").lower() == "draft":
        findings.append(
            _make_finding(
                strictness=strictness,
                source_class=source_class,
                severity="WARN",
                rule_id="W_PROTOCOL_AUTHORITY_DRAFT",
                family="zipwiz_protocol_doc",
                file_path=file_path,
                message="Protocol authority is marked as draft.",
                suggested_fix="Promote authority status when governance review completes.",
            )
        )


def _validate_beacon_capsule(
    *,
    strictness: str,
    source_class: str,
    file_path: str,
    payload: dict[str, Any],
    findings: list[dict[str, Any]],
) -> None:
    core_keys = ["Designation", "Action_Request", "Thread_Metadata.Thread_Name"]
    for key in core_keys:
        if not _has_nonempty(payload, key):
            findings.append(
                _make_finding(
                    strictness=strictness,
                    source_class=source_class,
                    severity="BLOCK",
                    rule_id="B_BEACON_MISSING_CORE_IDENTITY",
                    family="beacon_capsule",
                    file_path=file_path,
                    message=f"Beacon capsule missing required identity field: {key}.",
                    suggested_fix=f"Populate beacon identity key '{key}'.",
                    kind="missing_core_identity",
                )
            )

    legacy = _get_nested(payload, "Thread_Identity_Affirmation.Ethics_Lock")
    canonical = _get_nested(payload, "Thread_Identity_Affirmation.ethics_protocol") or payload.get("ethics_protocol")

    if not legacy and not canonical:
        findings.append(
            _make_finding(
                strictness=strictness,
                source_class=source_class,
                severity="BLOCK",
                rule_id="B_BEACON_MISSING_ETHICS_MARKER",
                family="beacon_capsule",
                file_path=file_path,
                message="Beacon capsule missing both canonical and legacy ethics markers.",
                suggested_fix=(
                    "Provide Thread_Identity_Affirmation.ethics_protocol (preferred) "
                    "or legacy Ethics_Lock with mapping note."
                ),
            )
        )

    if legacy and not canonical:
        findings.append(
            _make_finding(
                strictness=strictness,
                source_class=source_class,
                severity="WARN",
                rule_id="W_BEACON_LEGACY_ETHICS_LOCK_ONLY",
                family="beacon_capsule",
                file_path=file_path,
                message="Beacon capsule uses legacy Ethics_Lock without canonical ethics_protocol.",
                suggested_fix=f"Map legacy Ethics_Lock to ethics_protocol='{VALID_ETHICS_PROTOCOL}'.",
            )
        )

    trust_anchor = _get_nested(payload, "Thread_Identity_Affirmation.Trust_Anchor")
    if not trust_anchor:
        findings.append(
            _make_finding(
                strictness=strictness,
                source_class=source_class,
                severity="WARN",
                rule_id="W_BEACON_MISSING_TRUST_ANCHOR",
                family="beacon_capsule",
                file_path=file_path,
                message="Beacon capsule is missing Thread_Identity_Affirmation.Trust_Anchor.",
                suggested_fix="Add a trust anchor marker (for example BeaconSeal::Auto-Named).",
            )
        )


def _runtime_is_stub(path: Path, text: str) -> bool:
    nonempty = [line for line in text.splitlines() if line.strip()]
    if path.suffix.lower() == ".js":
        return len(nonempty) < 80
    if path.suffix.lower() == ".py":
        return len(nonempty) < 70
    return False


def _extract_summary(text: str) -> str:
    for line in text.splitlines():
        candidate = line.strip().lstrip("#").strip()
        if candidate:
            return candidate[:180]
    return "ZIPWIZ evidence artifact"


def _signal_type(path: Path, text: str) -> str:
    lowered = path.as_posix().lower()
    body = text.lower()
    if "packaging and export protocol" in body:
        return "packaging_protocol"
    if "bundle_manifest" in lowered and ".schema.json" in lowered:
        return "bundle_schema"
    if "seedcard" in lowered or "zipwiz_chamber" in lowered:
        return "symbolic_chamber"
    if "functional_patch" in lowered or "threadcore_functional_focus" in body:
        return "functional_patch"
    return "evidence_doc"


def _extract_dates_versions(path: Path, text: str) -> tuple[str | None, str | None]:
    raw = f"{path.name}\n{text[:3000]}"
    date_match = _DATE_RE.search(raw)
    ver_match = _VERSION_RE.search(raw)
    date_value = date_match.group(1) if date_match else None
    version_value = ver_match.group(0).lower() if ver_match else None

    # Curated fallback: known functional-patch narrative references 2026-02-16 context
    # even when the file body omits an explicit date literal.
    lowered_name = path.name.lower()
    if not date_value and "meta_narrative_summary_zipwizard_threadcore_functional_patch_thread" in lowered_name:
        date_value = "2026-02-16"

    return (date_value, version_value)


def _findings_by_file(findings: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in findings:
        out[row["file"]].append(row)
    return out


def _build_l3_bridge(
    *,
    artifacts: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    evolution_map: list[dict[str, Any]],
) -> dict[str, Any]:
    protocol_rows = [a for a in artifacts if a["family"] == "zipwiz_protocol_doc"]
    bundle_rows = [a for a in artifacts if a["family"] in {"bundle_manifest", "staging_manifest"}]
    anchor_rows = [
        f
        for f in findings
        if f["rule_id"]
        in {
            "B_BUNDLE_MANIFEST_INVALID_ANCHOR",
            "B_BUNDLE_MANIFEST_MISSING_ANCHOR",
            "B_BUNDLE_MANIFEST_INVALID_ETHICS",
            "B_BUNDLE_MANIFEST_MISSING_ETHICS",
            "B_PROTOCOL_ANCHOR_INVALID",
            "B_PROTOCOL_ETHICS_INVALID",
            "W_BEACON_LEGACY_ETHICS_LOCK_ONLY",
        }
    ]

    return {
        "protocol_update": [
            {
                "entity_type": "protocol_update",
                "protocol": "zipwiz_packaging",
                "protocol_docs": [row["file"] for row in protocol_rows],
                "drift_rules": sorted({f["rule_id"] for f in findings if f["family"] == "zipwiz_protocol_doc"}),
                "generated_at": _now_iso(),
            }
        ],
        "schema_definition": [
            {
                "entity_type": "schema_definition",
                "schema_family": "zipwiz_manifests",
                "artifact_count": len(bundle_rows),
                "variant_rules": sorted(
                    {
                        f["rule_id"]
                        for f in findings
                        if f["rule_id"]
                        in {
                            "W_BUNDLE_FILES_VARIANT",
                            "W_BUNDLE_CREATED_AT_UTC_VARIANT",
                            "I_BUNDLE_FILES_VARIANT_MAPPABLE",
                            "I_BUNDLE_CREATED_AT_UTC_MAPPABLE",
                            "W_BUNDLE_SIZE_BYTES_VARIANT",
                            "W_BUNDLE_ROLE_DRIFT",
                            "I_BUNDLE_SIZE_BYTES_MAPPABLE",
                            "I_BUNDLE_ROLE_NORMALIZED",
                        }
                    }
                ),
                "generated_at": _now_iso(),
            }
        ],
        "anchor_rule": [
            {
                "entity_type": "anchor_rule",
                "anchor_seed_expected": VALID_ANCHOR_SEED,
                "ethics_protocol_expected": VALID_ETHICS_PROTOCOL,
                "violations": len(anchor_rows),
                "evolution_milestones": len(evolution_map),
                "generated_at": _now_iso(),
            }
        ],
    }


def scan_repo(
    repo_root: str,
    roots: list[str] | None = None,
    reference_roots: list[str] | None = None,
    strictness: str = "balanced",
    include_evolution: bool = True,
    exclusions: list[str] | None = None,
) -> dict[str, Any]:
    repo = Path(repo_root).resolve()
    canonical_paths = [_to_path(repo, raw) for raw in (roots or DEFAULT_CANONICAL_ROOTS)]
    reference_paths = [_to_path(repo, raw) for raw in (reference_roots or DEFAULT_REFERENCE_ROOTS)]
    exclusions = exclusions or list(DEFAULT_EXCLUDE_PATTERNS)

    findings: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    evolution_map: list[dict[str, Any]] = []
    bundle_by_parent: dict[str, dict[str, Any]] = {}
    staging_rows: list[dict[str, Any]] = []
    runtime_rows: list[dict[str, Any]] = []
    protocol_docs: list[str] = []
    handshake_hits: list[str] = []

    def _record_evolution(
        *,
        rel: str,
        source_class: str,
        date_value: str | None,
        version_value: str | None,
        signal: str,
        summary: str,
    ) -> None:
        evolution_map.append(
            {
                "date": date_value,
                "version": version_value,
                "source_file": rel,
                "signal_type": signal,
                "summary": summary,
                "source_class": source_class,
            }
        )
        artifacts.append(
            {
                "file": rel,
                "family": "evolution_evidence",
                "source_class": source_class,
                "identity": rel,
                "identity_fields": {
                    "date": date_value,
                    "version": version_value,
                    "signal_type": signal,
                },
                "status": "pending",
            }
        )

    def _governance_outcome(severity_counts: Counter[str]) -> tuple[str, str]:
        if severity_counts.get("BLOCK", 0) > 0:
            return ("BLOCK", "NOT_READY")
        if severity_counts.get("WARN", 0) > 0:
            return ("REVIEW", "CONDITIONAL")
        return ("PASS", "READY")

    def process_path(path: Path, source_class: str) -> None:
        rel = _relative(path, repo)
        is_zip = path.suffix.lower() == ".zip"

        if include_evolution and _looks_like_zipwiz(rel) and is_zip:
            date_value, version_value = _extract_dates_versions(path, path.name)
            if date_value or version_value:
                _record_evolution(
                    rel=rel,
                    source_class=source_class,
                    date_value=date_value,
                    version_value=version_value,
                    signal="archive_filename",
                    summary=f"Archive filename evidence (not unpacked): {path.name}",
                )

        if _is_excluded(rel, exclusions) and not (include_evolution and _looks_like_zipwiz(rel) and is_zip):
            return

        if is_zip:
            return

        if path.suffix.lower() not in _CANDIDATE_SUFFIXES:
            return
        if source_class == "canonical" and not (_looks_like_zipwiz(rel) or _is_runtime_path(rel)):
            return

        text = _read_text(path)
        payload: Any = None
        parse_error: str | None = None
        if path.suffix.lower() == _JSON_SUFFIX:
            payload, parse_error = _load_json(text)

        if _HANDSHAKE_SEQUENCE in text:
            handshake_hits.append(rel)

        family = _detect_family(path, rel, text, payload, source_class)

        if include_evolution and _looks_like_zipwiz(rel):
            date_value, version_value = _extract_dates_versions(path, text)
            if date_value or version_value:
                signal = _signal_type(path, text)
                _record_evolution(
                    rel=rel,
                    source_class=source_class,
                    date_value=date_value,
                    version_value=version_value,
                    signal=signal,
                    summary=_extract_summary(text),
                )

        if not family:
            return

        if path.suffix.lower() == _JSON_SUFFIX and parse_error:
            findings.append(
                _make_finding(
                    strictness=strictness,
                    source_class=source_class,
                    severity="BLOCK",
                    rule_id="B_MALFORMED_JSON",
                    family=family,
                    file_path=rel,
                    message=f"Malformed JSON: {parse_error}",
                    suggested_fix="Fix JSON syntax and rerun ZIPWIZ governance scan.",
                    kind="parse",
                )
            )
            return

        fm = _parse_frontmatter(text) if family == "zipwiz_protocol_doc" else {}
        identity_payload = payload if isinstance(payload, dict) else fm
        identity, identity_fields = _extract_identity(family, identity_payload)
        artifacts.append(
            {
                "file": rel,
                "family": family,
                "source_class": source_class,
                "identity": identity,
                "identity_fields": identity_fields,
                "status": "pending",
            }
        )

        if family == "bundle_manifest" and isinstance(payload, dict):
            _validate_bundle_manifest(
                strictness=strictness,
                source_class=source_class,
                file_path=rel,
                payload=payload,
                findings=findings,
            )
            parent_key = Path(rel).parent.as_posix()
            entries = payload.get("contents") if isinstance(payload.get("contents"), list) else payload.get("files")
            bundle_by_parent[parent_key] = {
                "bundle_id": payload.get("bundle_id"),
                "entry_count": len(entries) if isinstance(entries, list) else 0,
                "file": rel,
            }
        elif family == "staging_manifest" and isinstance(payload, dict):
            _validate_staging_manifest(
                strictness=strictness,
                source_class=source_class,
                file_path=rel,
                payload=payload,
                findings=findings,
            )
            entries = payload.get("files") if isinstance(payload.get("files"), list) else []
            staging_rows.append(
                {
                    "file": rel,
                    "parent": Path(rel).parent.as_posix(),
                    "bundle": payload.get("bundle"),
                    "entry_count": len(entries),
                }
            )
        elif family == "zipwiz_protocol_doc":
            _validate_protocol_doc(
                strictness=strictness,
                source_class=source_class,
                file_path=rel,
                frontmatter=fm,
                findings=findings,
            )
            protocol_docs.append(rel)
        elif family == "beacon_capsule" and isinstance(payload, dict):
            _validate_beacon_capsule(
                strictness=strictness,
                source_class=source_class,
                file_path=rel,
                payload=payload,
                findings=findings,
            )
        elif family == "runtime_alignment":
            runtime_rows.append({"file": rel, "path": path, "text": text})

    for root in sorted(canonical_paths):
        for path in sorted(_iter_files(root)):
            process_path(path, "canonical")

    if include_evolution:
        for root in sorted(reference_paths):
            for path in sorted(_iter_files(root)):
                process_path(path, "reference_only")

    for row in staging_rows:
        parent = row["parent"]
        bundle = bundle_by_parent.get(parent)
        if not bundle:
            continue
        if bundle.get("bundle_id") and row.get("bundle") and bundle["bundle_id"] != row["bundle"]:
            findings.append(
                _make_finding(
                    strictness=strictness,
                    source_class="canonical",
                    severity="WARN",
                    rule_id="W_STAGING_BUNDLE_ID_MISMATCH",
                    family="staging_manifest",
                    file_path=row["file"],
                    message=(
                        f"Staging bundle id '{row['bundle']}' does not match "
                        f"bundle manifest id '{bundle['bundle_id']}'."
                    ),
                    suggested_fix="Align staging manifest bundle value with bundle.manifest.json bundle_id.",
                )
            )
        if bundle.get("entry_count") and row.get("entry_count") and bundle["entry_count"] != row["entry_count"]:
            findings.append(
                _make_finding(
                    strictness=strictness,
                    source_class="canonical",
                    severity="WARN",
                    rule_id="W_STAGING_FILE_COUNT_MISMATCH",
                    family="staging_manifest",
                    file_path=row["file"],
                    message=(
                        f"Staging files count ({row['entry_count']}) differs from "
                        f"bundle manifest entries ({bundle['entry_count']})."
                    ),
                    suggested_fix="Reconcile staging/files list with bundle manifest entry set.",
                )
            )

    for runtime in runtime_rows:
        if protocol_docs and _runtime_is_stub(runtime["path"], runtime["text"]):
            findings.append(
                _make_finding(
                    strictness=strictness,
                    source_class="canonical",
                    severity="WARN",
                    rule_id="W_RUNTIME_ALIGNMENT_DRIFT",
                    family="runtime_alignment",
                    file_path=runtime["file"],
                    message="ZIPWIZ runtime module appears stub-like relative to declared protocol/tooling scope.",
                    suggested_fix="Implement missing runtime behavior or constrain protocol/runtime claims.",
                )
            )

    if handshake_hits:
        findings.append(
            _make_finding(
                strictness=strictness,
                source_class="canonical",
                severity="INFO",
                rule_id="I_HANDSHAKE_SEQUENCE_PRESENT",
                family="runtime_alignment",
                file_path=handshake_hits[0],
                message=f"Detected canonical handshake sequence: {_HANDSHAKE_SEQUENCE}",
                suggested_fix="No action required.",
            )
        )

    evolution_map = sorted(
        evolution_map,
        key=lambda item: (
            item.get("date") or "9999-12-31",
            item.get("version") or "zzzz",
            item.get("source_file") or "",
        ),
    )
    seen = set()
    deduped: list[dict[str, Any]] = []
    for event in evolution_map:
        key = (
            event.get("date"),
            event.get("version"),
            event.get("source_file"),
            event.get("signal_type"),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(event)
    evolution_map = deduped

    for event in evolution_map:
        findings.append(
            _make_finding(
                strictness=strictness,
                source_class=event.get("source_class", "reference_only"),
                severity="INFO",
                rule_id="I_EVOLUTION_MILESTONE",
                family="evolution_evidence",
                file_path=event["source_file"],
                message=(
                    f"ZIPWIZ milestone observed: date={event.get('date') or 'unknown'}, "
                    f"version={event.get('version') or 'unknown'}, signal={event.get('signal_type')}"
                ),
                suggested_fix="No action required.",
            )
        )

    version_dates: dict[str, set[str]] = defaultdict(set)
    for event in evolution_map:
        version = event.get("version")
        date = event.get("date")
        if version and date:
            version_dates[version].add(date)

    for version, dates in sorted(version_dates.items()):
        if len(dates) > 1:
            findings.append(
                _make_finding(
                    strictness=strictness,
                    source_class="reference_only",
                    severity="WARN",
                    rule_id="W_EVOLUTION_VERSION_DATE_CONTRADICTION",
                    family="evolution_evidence",
                    file_path="<evolution_map>",
                    message=f"Version {version} appears with multiple dates: {', '.join(sorted(dates))}",
                    suggested_fix="Reconcile version/date provenance in ZIPWIZ timeline references.",
                )
            )

    by_file = _findings_by_file(findings)
    for artifact in artifacts:
        rows = by_file.get(artifact["file"], [])
        severities = {
            row["severity"]
            for row in rows
            if row["family"] == artifact["family"] or row["family"] == "evolution_evidence"
        }
        if "BLOCK" in severities:
            artifact["status"] = "invalid"
        elif "WARN" in severities:
            artifact["status"] = "warning"
        elif "INFO" in severities:
            artifact["status"] = "info"
        else:
            artifact["status"] = "valid"

    findings.sort(key=lambda row: (SEVERITY_ORDER.get(row["severity"], 99), row["file"], row["rule_id"]))

    severity_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    for finding in findings:
        severity_counts[finding["severity"]] += 1
        family_counts[finding["family"]] += 1

    for level in ("BLOCK", "WARN", "INFO"):
        severity_counts.setdefault(level, 0)

    l3_bridge = _build_l3_bridge(artifacts=artifacts, findings=findings, evolution_map=evolution_map)

    verdict, promotion_readiness = _governance_outcome(severity_counts)

    return {
        "domain": REPORT_DOMAIN,
        "verdict": verdict,
        "promotion_readiness": promotion_readiness,
        "scan_meta": {
            "timestamp": _now_iso(),
            "repo": str(repo),
            "roots": [str(path) for path in canonical_paths],
            "reference_roots": [str(path) for path in reference_paths],
            "strictness": strictness,
            "include_evolution": include_evolution,
            "exclusions": exclusions,
        },
        "summary": {
            "total_artifacts": len(artifacts),
            "total_findings": len(findings),
            "by_severity": dict(severity_counts),
            "by_family": dict(family_counts),
        },
        "artifacts": artifacts,
        "findings": findings,
        "evolution_map": evolution_map,
        "cross_skill_routing": [
            {
                "skill": "aurora-script-governor",
                "when": "ZIPWIZ runtime warnings expand into broad script hazard remediation.",
                "reason": "Script governance and safe remediation specialization.",
            },
            {
                "skill": "aurora-repo-stabilizer",
                "when": "The request becomes repo-ops reliability hardening (hooks/CI/validation loops).",
                "reason": "Repository stabilization workflow specialization.",
            },
            {
                "skill": "threadcore-governor",
                "when": "The request targets THREADCORE artifact validation families.",
                "reason": "THREADCORE-specific family and rule model.",
            },
        ],
        "l3_bridge": l3_bridge,
    }

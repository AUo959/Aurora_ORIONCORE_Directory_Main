#!/usr/bin/env python3
"""Deterministic THREADCORE family detection and governance validation rules."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# Repo-relative; resolved against --repo at scan time (see scan_repo).
# Aurora_Sim_Architecture here is the root-level tree, kept disjoint from
# GUMAS_SIM_2.5 because _iter_candidate_files does not dedupe nested roots.
DEFAULT_CANONICAL_ROOTS = [
    "GUMAS_SIM_2.5",
    "projects/Aurora_Project_Cloudhub_Deploy",
    "projects/GUI_Cloudhub",
    "Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main",
]

VALID_ETHICS_PROTOCOL = "Picard_Delta_3"
REPORT_DOMAIN = "threadcore"
SEVERITY_ORDER = {"BLOCK": 0, "WARN": 1, "INFO": 2}

_JSON_SUFFIX = ".json"
_TEXT_SUFFIXES = {".md", ".txt"}
_CANDIDATE_SUFFIXES = {_JSON_SUFFIX, ".md", ".txt"}

_NAME_HINTS = (
    "threadcore",
    "threadreflect",
    "beacon",
    "checkpoint",
    "continuity",
    "delta",
    "capsule",
    "drift",
    "registry",
    "threadwake",
    "execution_log",
)

_REGISTRY_RE = re.compile(r"THREADCORE::VISIBLE_NODE\.ORION\.[^\s`]+")
_BEACON_HEADER_RE = re.compile(r"THREADCORE\s+BEACON::VISIBLE_THREAD", re.IGNORECASE)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def _get_nested(data: dict[str, Any], dotted_key: str) -> Any:
    current: Any = data
    for piece in dotted_key.split("."):
        if not isinstance(current, dict) or piece not in current:
            return None
        current = current[piece]
    return current


def _has_nonempty(data: dict[str, Any], dotted_key: str) -> bool:
    value = _get_nested(data, dotted_key)
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def _is_candidate(path: Path) -> bool:
    if path.suffix.lower() not in _CANDIDATE_SUFFIXES:
        return False
    name = path.name.lower()
    return any(token in name for token in _NAME_HINTS)


def _iter_candidate_files(roots: list[Path]) -> Iterable[Path]:
    for root in roots:
        if not root.exists() or not root.is_dir():
            continue
        for path in root.rglob("*"):
            if path.is_file() and _is_candidate(path):
                yield path


def _adjust_severity(base: str, strictness: str, kind: str = "core") -> str:
    base = base.upper()
    strictness = strictness.lower()
    if strictness == "strict" and base == "WARN":
        return "BLOCK"
    if strictness == "lenient" and base == "BLOCK" and kind not in {"parse", "mandatory_marker"}:
        return "WARN"
    return base


def _make_finding(
    *,
    strictness: str,
    severity: str,
    rule_id: str,
    file_path: str,
    message: str,
    suggested_fix: str,
    family: str,
    kind: str = "core",
) -> dict[str, Any]:
    adjusted = _adjust_severity(severity, strictness, kind=kind)
    return {
        "domain": REPORT_DOMAIN,
        "severity": adjusted,
        "rule_id": rule_id,
        "file": file_path,
        "source_path": file_path,
        "message": message,
        "rationale": message,
        "evidence": "",
        "remediation": suggested_fix,
        "suggested_fix": suggested_fix,
        "family": family,
        "blocking_scope": "authoritative",
        "source_tool": "threadcore-governance-scan",
    }


def detect_family(path: Path, text: str, payload: Any) -> str | None:
    suffix = path.suffix.lower()
    name = path.name.lower()

    if suffix in _TEXT_SUFFIXES:
        if _BEACON_HEADER_RE.search(text):
            return "beacon_markdown"
        if "beacon" in name or "registryseal" in name or "threadwake" in name:
            return "beacon_markdown"
        return None

    if suffix != _JSON_SUFFIX or not isinstance(payload, dict):
        return None

    keys = set(payload.keys())

    if "delta_chain_version" in keys or ("entries" in keys and isinstance(payload.get("entries"), list)):
        return "delta_chain"

    if "checkpoint" in keys and isinstance(payload.get("checkpoint"), dict):
        return "checkpoint"

    continuity_keys = {"symbolic_tool", "deployment_key", "activation_phrase"}
    if continuity_keys.issubset(keys):
        return "continuity_log"

    if "continuity_log" in name:
        return "continuity_log"

    payload_indicators = {
        "capsule_id",
        "threadcore_status",
        "augmentation",
        "threadcore_directives",
        "glyph_chain",
    }
    if keys.intersection(payload_indicators):
        return "payload_capsule"

    if "threadcore" in name or "capsule" in name or "drift" in name:
        return "payload_capsule"

    return None


def _extract_identity(family: str, payload: Any, text: str) -> tuple[str | None, dict[str, Any]]:
    identity_fields: dict[str, Any] = {}

    if family == "checkpoint" and isinstance(payload, dict):
        identity = _get_nested(payload, "checkpoint.id")
        identity_fields["checkpoint.id"] = identity
        return (str(identity) if identity else None, identity_fields)

    if family == "continuity_log" and isinstance(payload, dict):
        identity = payload.get("deployment_key") or payload.get("thread_identity") or payload.get("timestamp")
        identity_fields["deployment_key"] = payload.get("deployment_key")
        identity_fields["thread_identity"] = payload.get("thread_identity")
        return (str(identity) if identity else None, identity_fields)

    if family == "payload_capsule" and isinstance(payload, dict):
        identity = payload.get("capsule_id")
        if not identity and payload.get("augmentation") and payload.get("version"):
            identity = f"{payload.get('augmentation')}::{payload.get('version')}"
        identity_fields["capsule_id"] = payload.get("capsule_id")
        identity_fields["augmentation"] = payload.get("augmentation")
        identity_fields["version"] = payload.get("version")
        return (str(identity) if identity else None, identity_fields)

    if family == "delta_chain" and isinstance(payload, dict):
        first_cdk = None
        entries = payload.get("entries")
        if isinstance(entries, list) and entries and isinstance(entries[0], dict):
            first_cdk = entries[0].get("cdk")
        identity = first_cdk or payload.get("delta_chain_version")
        identity_fields["delta_chain_version"] = payload.get("delta_chain_version")
        identity_fields["first_entry.cdk"] = first_cdk
        return (str(identity) if identity else None, identity_fields)

    if family == "beacon_markdown":
        match = _REGISTRY_RE.search(text)
        identity = match.group(0) if match else None
        identity_fields["registry_marker"] = identity
        return (identity, identity_fields)

    return (None, identity_fields)


def _validate_ethics(
    *,
    strictness: str,
    family: str,
    file_path: str,
    findings: list[dict[str, Any]],
    payload: dict[str, Any],
    key_path: str,
) -> None:
    value = _get_nested(payload, key_path)
    if value is None:
        findings.append(
            _make_finding(
                strictness=strictness,
                severity="BLOCK",
                rule_id="B_MISSING_ETHICS_PROTOCOL",
                file_path=file_path,
                message=f"Missing required ethics protocol field: {key_path}.",
                suggested_fix=f"Set {key_path} to '{VALID_ETHICS_PROTOCOL}'.",
                family=family,
            )
        )
        return

    if str(value) != VALID_ETHICS_PROTOCOL:
        findings.append(
            _make_finding(
                strictness=strictness,
                severity="BLOCK",
                rule_id="B_INVALID_ETHICS_PROTOCOL",
                file_path=file_path,
                message=f"Invalid ethics protocol '{value}' in {key_path}.",
                suggested_fix=f"Use '{VALID_ETHICS_PROTOCOL}' for {key_path}.",
                family=family,
            )
        )


def _validate_checkpoint(
    *, strictness: str, file_path: str, payload: dict[str, Any], findings: list[dict[str, Any]]
) -> None:
    required = ["augmentation", "version", "threadcore_directives", "checkpoint.id", "checkpoint.anchor_seed"]
    for key in required:
        if not _has_nonempty(payload, key):
            findings.append(
                _make_finding(
                    strictness=strictness,
                    severity="BLOCK",
                    rule_id="B_CHECKPOINT_REQUIRED_FIELD",
                    file_path=file_path,
                    message=f"Checkpoint missing required field: {key}.",
                    suggested_fix=f"Populate checkpoint field '{key}'.",
                    family="checkpoint",
                )
            )

    _validate_ethics(
        strictness=strictness,
        family="checkpoint",
        file_path=file_path,
        findings=findings,
        payload=payload,
        key_path="checkpoint.ethics_protocol",
    )

    if not _has_nonempty(payload, "checkpoint.id"):
        findings.append(
            _make_finding(
                strictness=strictness,
                severity="BLOCK",
                rule_id="B_MISSING_IDENTITY",
                file_path=file_path,
                message="Checkpoint has no identity key (checkpoint.id).",
                suggested_fix="Add checkpoint.id with stable checkpoint identity.",
                family="checkpoint",
            )
        )

    if not _has_nonempty(payload, "beacon_contact"):
        findings.append(
            _make_finding(
                strictness=strictness,
                severity="WARN",
                rule_id="W_OPTIONAL_BEACON_CONTACT",
                file_path=file_path,
                message="Checkpoint missing optional beacon_contact block.",
                suggested_fix="Add beacon_contact to align with canonical thread coordination metadata.",
                family="checkpoint",
                kind="compat",
            )
        )


def _validate_continuity_log(
    *, strictness: str, file_path: str, payload: dict[str, Any], findings: list[dict[str, Any]]
) -> None:
    required = ["symbolic_tool", "deployment_key", "activation_phrase", "ethics_protocol", "timestamp", "status"]
    for key in required:
        if not _has_nonempty(payload, key):
            findings.append(
                _make_finding(
                    strictness=strictness,
                    severity="BLOCK",
                    rule_id="B_CONTINUITY_REQUIRED_FIELD",
                    file_path=file_path,
                    message=f"Continuity log missing required field: {key}.",
                    suggested_fix=f"Populate continuity log field '{key}'.",
                    family="continuity_log",
                )
            )

    _validate_ethics(
        strictness=strictness,
        family="continuity_log",
        file_path=file_path,
        findings=findings,
        payload=payload,
        key_path="ethics_protocol",
    )

    if not _has_nonempty(payload, "deployment_key"):
        findings.append(
            _make_finding(
                strictness=strictness,
                severity="BLOCK",
                rule_id="B_MISSING_IDENTITY",
                file_path=file_path,
                message="Continuity log has no identity key (deployment_key).",
                suggested_fix="Add deployment_key as stable identity for the continuity log.",
                family="continuity_log",
            )
        )

    if not _has_nonempty(payload, "verified_modules"):
        findings.append(
            _make_finding(
                strictness=strictness,
                severity="WARN",
                rule_id="W_OPTIONAL_VERIFIED_MODULES",
                file_path=file_path,
                message="Continuity log missing optional verified_modules list.",
                suggested_fix="Add verified_modules to improve module provenance traceability.",
                family="continuity_log",
                kind="compat",
            )
        )


def _validate_payload_capsule(
    *, strictness: str, file_path: str, payload: dict[str, Any], findings: list[dict[str, Any]]
) -> None:
    has_capsule_id = _has_nonempty(payload, "capsule_id")
    has_aug_version = _has_nonempty(payload, "augmentation") and _has_nonempty(payload, "version")

    if not (has_capsule_id or has_aug_version):
        findings.append(
            _make_finding(
                strictness=strictness,
                severity="BLOCK",
                rule_id="B_MISSING_IDENTITY",
                file_path=file_path,
                message="Payload capsule missing identity (capsule_id or augmentation+version).",
                suggested_fix="Add capsule_id or populate both augmentation and version fields.",
                family="payload_capsule",
            )
        )

    for key in ("role", "ethics_protocol"):
        if not _has_nonempty(payload, key):
            findings.append(
                _make_finding(
                    strictness=strictness,
                    severity="BLOCK",
                    rule_id="B_PAYLOAD_REQUIRED_FIELD",
                    file_path=file_path,
                    message=f"Payload capsule missing required field: {key}.",
                    suggested_fix=f"Populate payload field '{key}'.",
                    family="payload_capsule",
                )
            )

    _validate_ethics(
        strictness=strictness,
        family="payload_capsule",
        file_path=file_path,
        findings=findings,
        payload=payload,
        key_path="ethics_protocol",
    )

    capsule_type = str(payload.get("capsule_type", "")).upper()
    if capsule_type != "DRIFTPULSE" and not _has_nonempty(payload, "anchor_seed"):
        findings.append(
            _make_finding(
                strictness=strictness,
                severity="BLOCK",
                rule_id="B_MISSING_ANCHOR_SEED",
                file_path=file_path,
                message="Payload capsule missing anchor_seed outside DRIFTPULSE profile.",
                suggested_fix="Set anchor_seed for payload and capsule artifacts.",
                family="payload_capsule",
            )
        )

    if _has_nonempty(payload, "threadcore_version") and not _has_nonempty(payload, "version"):
        findings.append(
            _make_finding(
                strictness=strictness,
                severity="WARN",
                rule_id="W_LEGACY_KEY_VARIANT",
                file_path=file_path,
                message="Legacy key variant detected: threadcore_version without version.",
                suggested_fix="Map threadcore_version to version and keep compatibility note.",
                family="payload_capsule",
                kind="compat",
            )
        )

    if _has_nonempty(payload, "sidebar_alias"):
        alias = str(payload.get("sidebar_alias"))
        if "(" not in alias and "v" not in alias.lower():
            findings.append(
                _make_finding(
                    strictness=strictness,
                    severity="WARN",
                    rule_id="W_ALIAS_FORMAT_DRIFT",
                    file_path=file_path,
                    message="Sidebar alias appears to drift from canonical title format.",
                    suggested_fix="Use a title that includes version context for canonical continuity.",
                    family="payload_capsule",
                    kind="compat",
                )
            )

    if not _has_nonempty(payload, "beacon_contact"):
        findings.append(
            _make_finding(
                strictness=strictness,
                severity="WARN",
                rule_id="W_OPTIONAL_BEACON_SUBSTRUCTURE",
                file_path=file_path,
                message="Payload capsule missing optional beacon_contact substructure.",
                suggested_fix="Add beacon_contact for inter-module signaling consistency.",
                family="payload_capsule",
                kind="compat",
            )
        )

    if not _has_nonempty(payload, "threadreflect") and not _has_nonempty(payload, "augmentations"):
        findings.append(
            _make_finding(
                strictness=strictness,
                severity="WARN",
                rule_id="W_OPTIONAL_REFLECTION_SUBSTRUCTURE",
                file_path=file_path,
                message="Payload capsule missing optional reflection substructure.",
                suggested_fix="Add threadreflect or augmentations metadata for reflective diagnostics coverage.",
                family="payload_capsule",
                kind="compat",
            )
        )


def _validate_delta_chain(
    *, strictness: str, file_path: str, payload: dict[str, Any], findings: list[dict[str, Any]]
) -> None:
    if not _has_nonempty(payload, "delta_chain_version"):
        findings.append(
            _make_finding(
                strictness=strictness,
                severity="BLOCK",
                rule_id="B_DELTA_REQUIRED_FIELD",
                file_path=file_path,
                message="Delta chain missing required field: delta_chain_version.",
                suggested_fix="Set delta_chain_version for chain identity and compatibility checks.",
                family="delta_chain",
            )
        )

    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        findings.append(
            _make_finding(
                strictness=strictness,
                severity="BLOCK",
                rule_id="B_DELTA_REQUIRED_ENTRIES",
                file_path=file_path,
                message="Delta chain missing entries array with at least one item.",
                suggested_fix="Add entries with version, label, cdk, and ethics fields.",
                family="delta_chain",
            )
        )
        return

    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            findings.append(
                _make_finding(
                    strictness=strictness,
                    severity="BLOCK",
                    rule_id="B_DELTA_ENTRY_NOT_OBJECT",
                    file_path=file_path,
                    message=f"Delta chain entry {idx} is not an object.",
                    suggested_fix="Use object entries with version, label, cdk, ethics.",
                    family="delta_chain",
                )
            )
            continue

        for field in ("version", "label", "cdk", "ethics"):
            if not entry.get(field):
                findings.append(
                    _make_finding(
                        strictness=strictness,
                        severity="BLOCK",
                        rule_id="B_DELTA_ENTRY_REQUIRED_FIELD",
                        file_path=file_path,
                        message=f"Delta chain entry {idx} missing required field: {field}.",
                        suggested_fix=f"Populate entries[{idx}].{field}.",
                        family="delta_chain",
                    )
                )

        if entry.get("ethics") and str(entry.get("ethics")) != VALID_ETHICS_PROTOCOL:
            findings.append(
                _make_finding(
                    strictness=strictness,
                    severity="BLOCK",
                    rule_id="B_INVALID_ETHICS_PROTOCOL",
                    file_path=file_path,
                    message=f"Delta chain entry {idx} uses noncanonical ethics protocol '{entry.get('ethics')}'.",
                    suggested_fix=f"Set entries[{idx}].ethics to '{VALID_ETHICS_PROTOCOL}'.",
                    family="delta_chain",
                )
            )


def _validate_beacon_markdown(
    *, strictness: str, file_path: str, text: str, findings: list[dict[str, Any]]
) -> None:
    has_header = bool(_BEACON_HEADER_RE.search(text))
    if not has_header:
        findings.append(
            _make_finding(
                strictness=strictness,
                severity="BLOCK",
                rule_id="B_BEACON_HEADER_MISSING",
                file_path=file_path,
                message="Beacon artifact missing mandatory header marker.",
                suggested_fix="Add 'THREADCORE BEACON::VISIBLE_THREAD' at the top of the beacon file.",
                family="beacon_markdown",
                kind="mandatory_marker",
            )
        )

    has_identity_block = "Thread Identity Marker" in text or "Thread Title:" in text
    if not has_identity_block:
        findings.append(
            _make_finding(
                strictness=strictness,
                severity="BLOCK",
                rule_id="B_BEACON_IDENTITY_BLOCK_MISSING",
                file_path=file_path,
                message="Beacon artifact missing required identity block marker.",
                suggested_fix="Add 'Thread Identity Marker' or 'Thread Title:' section to the beacon body.",
                family="beacon_markdown",
                kind="mandatory_marker",
            )
        )

    registry = _REGISTRY_RE.search(text)
    if not registry:
        findings.append(
            _make_finding(
                strictness=strictness,
                severity="BLOCK",
                rule_id="B_BEACON_REGISTRY_MARKER_MISSING",
                file_path=file_path,
                message="Beacon artifact missing registry marker in required format.",
                suggested_fix="Add registry marker matching THREADCORE::VISIBLE_NODE.ORION.*.",
                family="beacon_markdown",
                kind="mandatory_marker",
            )
        )

    if "THREADREFLECT" not in text:
        findings.append(
            _make_finding(
                strictness=strictness,
                severity="WARN",
                rule_id="W_OPTIONAL_THREADREFLECT_BLOCK",
                file_path=file_path,
                message="Beacon artifact missing optional THREADREFLECT evaluation block.",
                suggested_fix="Add THREADREFLECT block to improve thread evaluation coverage.",
                family="beacon_markdown",
                kind="compat",
            )
        )


def _add_normalization_hints(
    *, strictness: str, artifact: dict[str, Any], payload: Any, findings: list[dict[str, Any]]
) -> None:
    if artifact["family"] != "payload_capsule" or not isinstance(payload, dict):
        return

    drift = payload.get("symbolic_drift")
    if isinstance(drift, str) and drift.endswith("%"):
        findings.append(
            _make_finding(
                strictness=strictness,
                severity="INFO",
                rule_id="I_NORMALIZE_DRIFT_NUMERIC",
                file_path=artifact["file"],
                message="symbolic_drift is percentage string; numeric normalization hint available.",
                suggested_fix="Consider adding a numeric drift field while preserving source symbolic representation.",
                family="payload_capsule",
                kind="advisory",
            )
        )


def _status_for_file(file_findings: list[dict[str, Any]]) -> str:
    if any(f["severity"] == "BLOCK" for f in file_findings):
        return "blocked"
    if any(f["severity"] == "WARN" for f in file_findings):
        return "warning"
    return "ok"


def _governance_outcome(severity_counts: Counter[str]) -> tuple[str, str]:
    if severity_counts.get("BLOCK", 0) > 0:
        return ("BLOCK", "NOT_READY")
    if severity_counts.get("WARN", 0) > 0:
        return ("REVIEW", "CONDITIONAL")
    return ("PASS", "READY")


def _build_l3_bridge(report: dict[str, Any]) -> dict[str, Any]:
    versions = []
    for artifact in report.get("artifacts", []):
        version = artifact.get("identity_fields", {}).get("version")
        if version:
            versions.append(str(version))

    block_count = report.get("summary", {}).get("by_severity", {}).get("BLOCK", 0)
    has_anchor_impact = any("anchor" in f.get("rule_id", "").lower() for f in report.get("findings", []))

    bridge = {
        "generated_at": report["scan_meta"]["timestamp"],
        "entities": {
            "protocol_update": {
                "protocol_name": VALID_ETHICS_PROTOCOL,
                "version": versions[0] if versions else "1.0",
                "change_description": (
                    "THREADCORE governance scan bridge generated from deterministic findings; "
                    f"BLOCK={block_count}, WARN={report.get('summary', {}).get('by_severity', {}).get('WARN', 0)}."
                ),
                "affected_layers": ["L3"],
                "backward_compatible": block_count == 0,
                "anchor_impact": has_anchor_impact,
            },
            "schema_definition": {
                "schema_name": "THREADCORE Governance Validation Snapshot",
                "version": "1.0",
                "fields": [
                    "family",
                    "identity",
                    "severity",
                    "rule_id",
                    "message",
                    "suggested_fix",
                ],
            },
            "anchor_rule": {
                "anchor_id": "THREADCORE::VISIBLE_NODE.ORION.*",
                "rule_description": (
                    "Beacon registry markers must use THREADCORE::VISIBLE_NODE.ORION.* and "
                    "preserve identity continuity under Picard_Delta_3 governance."
                ),
                "affected_layers": ["L3"],
            },
        },
    }
    return bridge


def scan_repo(repo_root: str, roots: list[str], strictness: str = "balanced") -> dict[str, Any]:
    repo_path = Path(repo_root).resolve()
    resolved_roots: list[Path] = []

    for raw_root in roots:
        candidate = Path(raw_root)
        if not candidate.is_absolute():
            candidate = (repo_path / candidate).resolve()
        else:
            candidate = candidate.resolve()
        resolved_roots.append(candidate)

    artifacts: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []

    for file_path in sorted(_iter_candidate_files(resolved_roots), key=lambda p: p.as_posix()):
        rel_file = _relative(file_path, repo_path)
        text = file_path.read_text(encoding="utf-8", errors="replace")
        payload: Any = None

        if file_path.suffix.lower() == _JSON_SUFFIX:
            try:
                payload = json.loads(text)
            except json.JSONDecodeError as exc:
                findings.append(
                    _make_finding(
                        strictness=strictness,
                        severity="BLOCK",
                        rule_id="B_MALFORMED_JSON",
                        file_path=rel_file,
                        message=f"Malformed JSON: {exc.msg} (line {exc.lineno}, col {exc.colno}).",
                        suggested_fix="Repair JSON syntax before governance validation.",
                        family="unknown",
                        kind="parse",
                    )
                )
                artifacts.append(
                    {
                        "file": rel_file,
                        "family": "unknown",
                        "identity": None,
                        "identity_fields": {},
                        "status": "blocked",
                    }
                )
                continue

        family = detect_family(file_path, text, payload)
        if family is None:
            continue

        identity, identity_fields = _extract_identity(family, payload, text)
        artifact = {
            "file": rel_file,
            "family": family,
            "identity": identity,
            "identity_fields": identity_fields,
            "status": "ok",
        }
        artifacts.append(artifact)

        file_findings: list[dict[str, Any]] = []

        if family == "checkpoint" and isinstance(payload, dict):
            _validate_checkpoint(strictness=strictness, file_path=rel_file, payload=payload, findings=file_findings)
        elif family == "continuity_log" and isinstance(payload, dict):
            _validate_continuity_log(strictness=strictness, file_path=rel_file, payload=payload, findings=file_findings)
        elif family == "payload_capsule" and isinstance(payload, dict):
            _validate_payload_capsule(strictness=strictness, file_path=rel_file, payload=payload, findings=file_findings)
            _add_normalization_hints(strictness=strictness, artifact=artifact, payload=payload, findings=file_findings)
        elif family == "delta_chain" and isinstance(payload, dict):
            _validate_delta_chain(strictness=strictness, file_path=rel_file, payload=payload, findings=file_findings)
        elif family == "beacon_markdown":
            _validate_beacon_markdown(strictness=strictness, file_path=rel_file, text=text, findings=file_findings)

        artifact["status"] = _status_for_file(file_findings)
        findings.extend(file_findings)

    by_identity: dict[tuple[str, str], list[str]] = defaultdict(list)
    for artifact in artifacts:
        if artifact.get("identity"):
            by_identity[(artifact["family"], str(artifact["identity"]))].append(artifact["file"])

    for (family, identity), files in sorted(by_identity.items()):
        unique_files = sorted(set(files))
        if len(unique_files) < 2:
            continue
        findings.append(
            _make_finding(
                strictness=strictness,
                severity="INFO",
                rule_id="I_DUPLICATE_IDENTITY",
                file_path=unique_files[0],
                message=(
                    f"Potential duplicate identity '{identity}' in family '{family}' across "
                    f"{len(unique_files)} artifacts."
                ),
                suggested_fix="Compare artifacts and keep one canonical source of truth in focused roots.",
                family=family,
                kind="advisory",
            )
        )

    findings.sort(key=lambda f: (SEVERITY_ORDER.get(f["severity"], 99), f["file"], f["rule_id"]))

    severity_counts = Counter(f["severity"] for f in findings)
    family_counts = Counter(a["family"] for a in artifacts)

    report = {
        "domain": REPORT_DOMAIN,
        "scan_meta": {
            "timestamp": _now_iso(),
            "repo": repo_path.as_posix(),
            "roots": [p.as_posix() for p in resolved_roots],
            "strictness": strictness,
        },
        "summary": {
            "total_artifacts": len(artifacts),
            "total_findings": len(findings),
            "by_severity": {
                "BLOCK": severity_counts.get("BLOCK", 0),
                "WARN": severity_counts.get("WARN", 0),
                "INFO": severity_counts.get("INFO", 0),
            },
            "by_family": dict(sorted(family_counts.items())),
        },
        "artifacts": artifacts,
        "findings": findings,
    }

    verdict, promotion_readiness = _governance_outcome(severity_counts)
    report["verdict"] = verdict
    report["promotion_readiness"] = promotion_readiness
    report["l3_bridge"] = _build_l3_bridge(report)
    return report

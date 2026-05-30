#!/usr/bin/env python3
"""Build an Aurora-focused executive brief from mixed data inputs."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import fnmatch
import io
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

SUPPORTED_EXTENSIONS = {".json", ".csv", ".md", ".zip"}
ANALYZABLE_EXTENSIONS = {".json", ".csv", ".md"}
DEFAULT_INCLUDE_GLOBS = "*.json,*.csv,*.md,*.zip"
MAX_READ_BYTES = 2_000_000
MAX_ZIP_MEMBERS_PER_ARCHIVE = 200
MAX_EVIDENCE_ITEMS = 200

FILENAME_SIGNAL_KEYWORDS = {
    "manifest": 4,
    "checkpoint": 4,
    "continuity": 4,
    "execution": 3,
    "log": 3,
    "status": 3,
    "report": 3,
    "risk": 3,
    "incident": 4,
    "deploy": 3,
    "patch": 3,
    "release": 3,
    "metadata": 2,
    "summary": 2,
    "thread": 2,
    "alignment": 2,
    "audit": 3,
    "index": 2,
}

EXTENSION_SIGNAL_WEIGHTS = {
    ".json": 4,
    ".csv": 3,
    ".md": 2,
    ".zip": 1,
}

RISK_CUE_TERMS = (
    "risk",
    "blocked",
    "degraded",
    "failed",
    "failure",
    "urgent",
    "drift",
    "rollback",
    "incident",
    "breach",
    "hotfix",
)

ACTION_CUE_TERMS = (
    "todo",
    "action",
    "next step",
    "owner",
    "follow up",
    "mitigate",
    "remediate",
)

SENSITIVE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("private_key_block", re.compile(r"-----BEGIN(?: [A-Z]+)? PRIVATE KEY-----", re.IGNORECASE)),
    ("api_key_assignment", re.compile(r"(?i)\b(api[_-]?key|token|secret|password)\b\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{12,})")),
    ("bearer_token", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9\-._~+/]+=*")),
    ("openai_style_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{12,24}\b")),
    ("long_token_like", re.compile(r"\b[A-Za-z0-9_\-]{32,}\b")),
]

REDACTION_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"-----BEGIN(?: [A-Z]+)? PRIVATE KEY-----", re.IGNORECASE), "<REDACTED:PRIVATE_KEY_BEGIN>"),
    (re.compile(r"-----END(?: [A-Z]+)? PRIVATE KEY-----", re.IGNORECASE), "<REDACTED:PRIVATE_KEY_END>"),
    (re.compile(r"(?i)(\bapi[_-]?key\b\s*[:=]\s*['\"]?)([A-Za-z0-9_\-]{8,})"), r"\1<REDACTED>"),
    (re.compile(r"(?i)(\btoken\b\s*[:=]\s*['\"]?)([A-Za-z0-9_\-]{8,})"), r"\1<REDACTED>"),
    (re.compile(r"(?i)(\bsecret\b\s*[:=]\s*['\"]?)([A-Za-z0-9_\-]{8,})"), r"\1<REDACTED>"),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9\-._~+/]+=*"), "Bearer <REDACTED>"),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), "sk-<REDACTED>"),
    (re.compile(r"\bAKIA[0-9A-Z]{12,24}\b"), "AKIA<REDACTED>"),
]


def now_utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan mixed Aurora data and produce an executive brief and JSON findings."
    )
    parser.add_argument("--input-dir", required=True, help="Directory to scan recursively")
    parser.add_argument(
        "--out-dir",
        help="Output directory (default: <input-dir>/reports)",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=200,
        help="Maximum source files to select after ranking (default: 200)",
    )
    parser.add_argument(
        "--include-globs",
        default=DEFAULT_INCLUDE_GLOBS,
        help="Comma-separated file globs to include (default: *.json,*.csv,*.md,*.zip)",
    )
    parser.add_argument(
        "--top-findings",
        type=int,
        default=12,
        help="Maximum number of top risks in final output (default: 12)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when high risks or parse failures are present",
    )
    parser.add_argument(
        "--emit-run-manifest",
        action="store_true",
        help="Write run_manifest.json with ranking and selection diagnostics",
    )
    return parser.parse_args()


def parse_globs(raw: str) -> list[str]:
    parts = [item.strip() for item in raw.split(",") if item.strip()]
    if not parts:
        return ["*.json", "*.csv", "*.md", "*.zip"]
    return parts


def is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def extension_from_name(name: str) -> str:
    return Path(name).suffix.lower()


def filename_signal_score(name: str) -> int:
    lowered = name.lower()
    score = 0
    for token, weight in FILENAME_SIGNAL_KEYWORDS.items():
        if token in lowered:
            score += weight
    return score


def extension_signal_score(path: Path) -> int:
    return EXTENSION_SIGNAL_WEIGHTS.get(path.suffix.lower(), 0)


def collect_candidates(input_dir: Path, include_globs: list[str], out_dir: Path) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for path in input_dir.rglob("*"):
        if not path.is_file():
            continue
        resolved = path.resolve()
        if is_relative_to(resolved, out_dir):
            continue

        rel = str(path.relative_to(input_dir))
        matched = any(fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(rel, pattern) for pattern in include_globs)
        if not matched:
            continue

        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            continue

        stat = path.stat()
        candidates.append(
            {
                "path": path,
                "relative_path": rel,
                "ext": ext,
                "mtime": float(stat.st_mtime),
                "size_bytes": int(stat.st_size),
                "filename_signal": filename_signal_score(path.name),
                "extension_signal": extension_signal_score(path),
            }
        )

    return candidates


def rank_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(candidates, key=lambda item: (-item["mtime"], item["relative_path"]))
    total = len(ordered)
    for idx, item in enumerate(ordered):
        recency_points = total - idx
        item["recency_points"] = recency_points
        item["score"] = (
            recency_points * 10
            + item["filename_signal"] * 4
            + item["extension_signal"] * 3
        )

    return sorted(
        ordered,
        key=lambda item: (
            -item["score"],
            -item["mtime"],
            item["relative_path"],
        ),
    )


def read_text_file(path: Path) -> tuple[str, bool]:
    with path.open("rb") as handle:
        raw = handle.read(MAX_READ_BYTES + 1)
    truncated = len(raw) > MAX_READ_BYTES
    if truncated:
        raw = raw[:MAX_READ_BYTES]
    return raw.decode("utf-8", errors="ignore"), truncated


def redact_text(text: str) -> str:
    result = text
    for pattern, replacement in REDACTION_RULES:
        result = pattern.sub(replacement, result)
    result = re.sub(r"\b[A-Za-z0-9_\-]{40,}\b", "<REDACTED:LONG_TOKEN>", result)
    return result


def detect_sensitive_patterns(text: str) -> Counter:
    counts: Counter = Counter()
    for name, pattern in SENSITIVE_PATTERNS:
        hits = list(pattern.finditer(text))
        if hits:
            counts[name] += len(hits)
    return counts


def compact_snippet(text: str, max_len: int = 220) -> str:
    one_line = " ".join(text.strip().split())
    redacted = redact_text(one_line)
    if len(redacted) <= max_len:
        return redacted
    return redacted[: max_len - 3].rstrip() + "..."


def add_evidence(
    evidence: list[dict[str, Any]],
    source: str,
    kind: str,
    signal: str,
    snippet: str,
) -> None:
    if len(evidence) >= MAX_EVIDENCE_ITEMS:
        return
    evidence.append(
        {
            "source": source,
            "type": kind,
            "signal": signal,
            "snippet": compact_snippet(snippet),
        }
    )


def count_json_structures(value: Any) -> tuple[int, int, int]:
    dict_count = 0
    list_count = 0
    key_count = 0

    def walk(node: Any) -> None:
        nonlocal dict_count, list_count, key_count
        if isinstance(node, dict):
            dict_count += 1
            key_count += len(node)
            for child in node.values():
                walk(child)
            return
        if isinstance(node, list):
            list_count += 1
            for child in node:
                walk(child)
            return

    walk(value)
    return dict_count, list_count, key_count


def analyze_json(
    source: str,
    text: str,
    aggregate: dict[str, Any],
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "source": source,
        "kind": "json",
        "parse_ok": True,
        "dict_count": 0,
        "list_count": 0,
        "key_count": 0,
        "key_density": 0.0,
    }

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        aggregate["parse_failures"] += 1
        result["parse_ok"] = False
        result["error"] = f"{exc.msg} (line {exc.lineno}, col {exc.colno})"
        aggregate["risks"].append(
            {
                "risk_id": "json_parse_failure",
                "severity": "high",
                "title": "JSON Parse Failures",
                "impact": "Malformed JSON artifacts can hide true operational state.",
                "recommendation": "Repair malformed JSON files and enforce export validation before ingest.",
                "evidence_count": 1,
                "source": source,
            }
        )
        line = text.splitlines()[max(exc.lineno - 1, 0)] if text.splitlines() else text[:200]
        add_evidence(aggregate["evidence"], source, "json", "parse_failure", line)
        return result

    dict_count, list_count, key_count = count_json_structures(parsed)
    result["dict_count"] = dict_count
    result["list_count"] = list_count
    result["key_count"] = key_count
    result["key_density"] = round(key_count / max(dict_count, 1), 4)

    if key_count == 0:
        aggregate["risks"].append(
            {
                "risk_id": "json_low_information_density",
                "severity": "low",
                "title": "Low-Information JSON Payloads",
                "impact": "Sparse JSON payloads may reduce decision confidence.",
                "recommendation": "Confirm whether sparse payloads are expected or exports are incomplete.",
                "evidence_count": 1,
                "source": source,
            }
        )
        add_evidence(aggregate["evidence"], source, "json", "low_information", text[:220])

    return result


def analyze_csv(
    source: str,
    text: str,
    aggregate: dict[str, Any],
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "source": source,
        "kind": "csv",
        "parse_ok": True,
        "rows": 0,
        "columns": 0,
        "header_quality": 0.0,
        "malformed_rows": 0,
        "sparse_columns": 0,
    }

    try:
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
    except csv.Error as exc:
        aggregate["parse_failures"] += 1
        result["parse_ok"] = False
        result["error"] = str(exc)
        aggregate["risks"].append(
            {
                "risk_id": "csv_parse_failure",
                "severity": "high",
                "title": "CSV Parse Failures",
                "impact": "Unreadable CSV data blocks trend and KPI extraction.",
                "recommendation": "Normalize CSV exports and validate delimiters before ingestion.",
                "evidence_count": 1,
                "source": source,
            }
        )
        add_evidence(aggregate["evidence"], source, "csv", "parse_failure", text[:220])
        return result

    if not rows:
        aggregate["risks"].append(
            {
                "risk_id": "csv_empty",
                "severity": "medium",
                "title": "Empty CSV Artifacts",
                "impact": "Empty tables indicate missing telemetry or failed data exports.",
                "recommendation": "Re-run upstream export jobs and verify expected row counts.",
                "evidence_count": 1,
                "source": source,
            }
        )
        add_evidence(aggregate["evidence"], source, "csv", "empty_csv", "<empty csv>")
        return result

    header = rows[0]
    body = rows[1:]
    expected_len = len(header)
    malformed_rows = 0
    if expected_len > 0:
        malformed_rows = sum(1 for row in body if len(row) != expected_len)

    header_nonempty = sum(1 for column in header if column.strip())
    header_quality = header_nonempty / max(len(header), 1)

    sparse_columns = 0
    if expected_len > 0 and body:
        for col_idx in range(expected_len):
            empty_cells = 0
            samples = 0
            for row in body:
                if col_idx >= len(row):
                    empty_cells += 1
                    samples += 1
                    continue
                samples += 1
                if not row[col_idx].strip():
                    empty_cells += 1
            if samples and (empty_cells / samples) >= 0.8:
                sparse_columns += 1

    result.update(
        {
            "rows": len(body),
            "columns": expected_len,
            "header_quality": round(header_quality, 4),
            "malformed_rows": malformed_rows,
            "sparse_columns": sparse_columns,
        }
    )

    if malformed_rows > 0:
        aggregate["risks"].append(
            {
                "risk_id": "csv_malformed_rows",
                "severity": "medium",
                "title": "Malformed CSV Rows",
                "impact": "Inconsistent row structure can skew aggregations and brief conclusions.",
                "recommendation": "Repair malformed rows and enforce schema checks during export.",
                "evidence_count": malformed_rows,
                "source": source,
            }
        )
        add_evidence(
            aggregate["evidence"],
            source,
            "csv",
            "malformed_rows",
            f"Malformed rows: {malformed_rows} of {len(body)}",
        )

    if header_quality < 0.6:
        aggregate["risks"].append(
            {
                "risk_id": "csv_low_header_quality",
                "severity": "low",
                "title": "Low Header Quality in CSV",
                "impact": "Weak column labels reduce confidence in interpretation and ownership.",
                "recommendation": "Standardize CSV headers with clear field names.",
                "evidence_count": 1,
                "source": source,
            }
        )
        add_evidence(
            aggregate["evidence"],
            source,
            "csv",
            "low_header_quality",
            f"Header quality: {header_quality:.2f}",
        )

    return result


def analyze_markdown(
    source: str,
    text: str,
    aggregate: dict[str, Any],
) -> dict[str, Any]:
    lines = text.splitlines()
    nonempty = [line for line in lines if line.strip()]
    heading_count = sum(1 for line in nonempty if line.lstrip().startswith("#"))

    action_hits = []
    risk_hits = []
    for line in nonempty:
        lowered = line.lower()
        if any(term in lowered for term in ACTION_CUE_TERMS):
            action_hits.append(line)
        if any(term in lowered for term in RISK_CUE_TERMS):
            risk_hits.append(line)

    heading_density = heading_count / max(len(nonempty), 1)

    result = {
        "source": source,
        "kind": "md",
        "line_count": len(lines),
        "heading_count": heading_count,
        "heading_density": round(heading_density, 4),
        "action_cues": len(action_hits),
        "risk_cues": len(risk_hits),
    }

    if len(risk_hits) >= 8:
        aggregate["risks"].append(
            {
                "risk_id": "markdown_risk_cue_surge",
                "severity": "medium",
                "title": "High Risk Signal Density in Markdown Logs",
                "impact": "Frequent risk language suggests unresolved operational instability.",
                "recommendation": "Review incidents in source markdown and assign owners for unresolved items.",
                "evidence_count": len(risk_hits),
                "source": source,
            }
        )
        add_evidence(
            aggregate["evidence"],
            source,
            "md",
            "risk_cue_surge",
            risk_hits[0],
        )

    if action_hits:
        add_evidence(
            aggregate["evidence"],
            source,
            "md",
            "action_queue",
            action_hits[0],
        )

    return result


def analyze_text_source(
    source: str,
    ext: str,
    text: str,
    aggregate: dict[str, Any],
) -> dict[str, Any]:
    sensitive = detect_sensitive_patterns(text)
    if sensitive:
        aggregate["sensitive_pattern_counts"].update(sensitive)
        total_hits = sum(sensitive.values())
        aggregate["risks"].append(
            {
                "risk_id": "sensitive_data_exposure",
                "severity": "high",
                "title": "Sensitive Token Pattern Exposure",
                "impact": "Potential secrets in source artifacts can create immediate security and compliance risk.",
                "recommendation": "Rotate exposed credentials, redact historical logs, and gate future exports.",
                "evidence_count": total_hits,
                "source": source,
            }
        )
        add_evidence(aggregate["evidence"], source, ext.lstrip("."), "sensitive_pattern", text[:240])

    if ext == ".json":
        return analyze_json(source, text, aggregate)
    if ext == ".csv":
        return analyze_csv(source, text, aggregate)
    if ext == ".md":
        return analyze_markdown(source, text, aggregate)

    return {"source": source, "kind": ext.lstrip("."), "parse_ok": True}


def analyze_zip_file(
    path: Path,
    rel: str,
    aggregate: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records: list[dict[str, Any]] = []
    zip_meta = {
        "source": rel,
        "kind": "zip",
        "members_total": 0,
        "members_scanned": 0,
        "members_skipped": 0,
    }

    try:
        with zipfile.ZipFile(path, "r") as zf:
            infos = [info for info in zf.infolist() if not info.is_dir()]
            zip_meta["members_total"] = len(infos)
            scanned = 0
            for info in infos:
                if scanned >= MAX_ZIP_MEMBERS_PER_ARCHIVE:
                    zip_meta["members_skipped"] = len(infos) - scanned
                    break

                member_ext = extension_from_name(info.filename)
                if member_ext not in ANALYZABLE_EXTENSIONS:
                    continue

                with zf.open(info, "r") as member_fp:
                    raw = member_fp.read(MAX_READ_BYTES + 1)
                truncated = len(raw) > MAX_READ_BYTES
                if truncated:
                    raw = raw[:MAX_READ_BYTES]

                text = raw.decode("utf-8", errors="ignore")
                source = f"{rel}::{info.filename}"
                record = analyze_text_source(source, member_ext, text, aggregate)
                record["truncated"] = truncated
                records.append(record)
                add_evidence(
                    aggregate["evidence"],
                    source,
                    member_ext.lstrip("."),
                    "zip_member_scanned",
                    text[:220] if text else "<empty zip member>",
                )
                scanned += 1

            zip_meta["members_scanned"] = scanned

            if zip_meta["members_skipped"] > 0:
                aggregate["risks"].append(
                    {
                        "risk_id": "zip_member_truncation",
                        "severity": "low",
                        "title": "ZIP Member Scan Cap Reached",
                        "impact": "Only a subset of archive members were scanned, reducing total coverage.",
                        "recommendation": "Increase caps for deep archives or split large bundles before analysis.",
                        "evidence_count": zip_meta["members_skipped"],
                        "source": rel,
                    }
                )
                add_evidence(
                    aggregate["evidence"],
                    rel,
                    "zip",
                    "member_scan_cap",
                    f"Skipped members: {zip_meta['members_skipped']}",
                )

    except (zipfile.BadZipFile, OSError) as exc:
        aggregate["parse_failures"] += 1
        aggregate["risks"].append(
            {
                "risk_id": "zip_parse_failure",
                "severity": "high",
                "title": "ZIP Parse Failures",
                "impact": "Unreadable archives prevent visibility into potentially critical artifacts.",
                "recommendation": "Rebuild corrupted ZIP files and verify archive integrity upstream.",
                "evidence_count": 1,
                "source": rel,
            }
        )
        add_evidence(aggregate["evidence"], rel, "zip", "parse_failure", str(exc))

    return records, zip_meta


def stale_days(mtime: float) -> int:
    then = dt.datetime.fromtimestamp(mtime, tz=dt.timezone.utc)
    now = dt.datetime.now(dt.timezone.utc)
    return max((now - then).days, 0)


def normalized_name_key(path_like: str) -> str:
    stem = Path(path_like).stem.lower()
    stem = re.sub(r"\d+", "", stem)
    stem = re.sub(r"[^a-z]+", "", stem)
    return stem


def cross_file_analysis(
    selected_candidates: list[dict[str, Any]],
    aggregate: dict[str, Any],
) -> None:
    if not selected_candidates:
        return

    stale_candidates = [item for item in selected_candidates if stale_days(item["mtime"]) >= 90]
    if stale_candidates:
        aggregate["risks"].append(
            {
                "risk_id": "stale_hotspot",
                "severity": "medium",
                "title": "Stale Operational Artifacts",
                "impact": "Aging artifacts can produce outdated leadership decisions.",
                "recommendation": "Prioritize refresh of stale manifests and reports before strategic decisions.",
                "evidence_count": len(stale_candidates),
                "source": stale_candidates[0]["relative_path"],
            }
        )
        add_evidence(
            aggregate["evidence"],
            stale_candidates[0]["relative_path"],
            stale_candidates[0]["ext"].lstrip("."),
            "stale_hotspot",
            f"Artifact is {stale_days(stale_candidates[0]['mtime'])} days old",
        )

    by_stem = Counter(item["path"].stem.lower() for item in selected_candidates)
    duplicate_stems = {name: count for name, count in by_stem.items() if count > 1}
    if duplicate_stems:
        aggregate["risks"].append(
            {
                "risk_id": "duplicate_filenames",
                "severity": "medium",
                "title": "Duplicate Artifact Names",
                "impact": "Duplicate filenames increase the chance of referencing stale or wrong variants.",
                "recommendation": "Consolidate duplicate artifacts or enforce date/version naming conventions.",
                "evidence_count": sum(duplicate_stems.values()),
                "source": next(iter(duplicate_stems.keys())),
            }
        )
        add_evidence(
            aggregate["evidence"],
            next(iter(duplicate_stems.keys())),
            "cross",
            "duplicate_filenames",
            f"Duplicate stems: {sorted(duplicate_stems.items())[:4]}",
        )

    by_norm = Counter(normalized_name_key(item["relative_path"]) for item in selected_candidates)
    near_duplicates = {name: count for name, count in by_norm.items() if name and count > 2}
    if near_duplicates:
        aggregate["risks"].append(
            {
                "risk_id": "near_duplicate_families",
                "severity": "low",
                "title": "Near-Duplicate Artifact Families",
                "impact": "Large variant families can create ambiguity over source-of-truth artifacts.",
                "recommendation": "Designate canonical variants and archive superseded copies.",
                "evidence_count": sum(near_duplicates.values()),
                "source": next(iter(near_duplicates.keys())),
            }
        )

    if aggregate["parse_failures"] > 0:
        ratio = aggregate["parse_failures"] / max(aggregate["analyzed_units"], 1)
        if ratio >= 0.1:
            aggregate["risks"].append(
                {
                    "risk_id": "parse_failure_concentration",
                    "severity": "high",
                    "title": "Parse Failure Concentration",
                    "impact": "A meaningful share of artifacts could not be parsed, reducing confidence in conclusions.",
                    "recommendation": "Stabilize export formats and enforce pre-brief validation checks.",
                    "evidence_count": aggregate["parse_failures"],
                    "source": "analysis_scope",
                }
            )


def consolidate_risks(risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    consolidated: dict[tuple[str, str, str], dict[str, Any]] = {}
    severity_weight = {"high": 3, "medium": 2, "low": 1}

    for risk in risks:
        key = (risk["risk_id"], risk["severity"], risk["title"])
        if key not in consolidated:
            consolidated[key] = {
                "risk_id": risk["risk_id"],
                "severity": risk["severity"],
                "title": risk["title"],
                "impact": risk["impact"],
                "recommendation": risk["recommendation"],
                "evidence_count": int(risk.get("evidence_count", 0)),
                "source_count": 1,
                "sources": [risk.get("source", "unknown")],
            }
            continue

        entry = consolidated[key]
        entry["evidence_count"] += int(risk.get("evidence_count", 0))
        entry["source_count"] += 1
        source = risk.get("source", "unknown")
        if source not in entry["sources"]:
            entry["sources"].append(source)

    ordered = sorted(
        consolidated.values(),
        key=lambda item: (
            -severity_weight.get(item["severity"], 0),
            -item["evidence_count"],
            item["title"],
        ),
    )
    return ordered


def build_key_signals(
    selected_candidates: list[dict[str, Any]],
    analysis_records: list[dict[str, Any]],
    aggregate: dict[str, Any],
) -> list[dict[str, Any]]:
    json_ok = sum(1 for item in analysis_records if item.get("kind") == "json" and item.get("parse_ok"))
    csv_ok = sum(1 for item in analysis_records if item.get("kind") == "csv" and item.get("parse_ok"))
    md_count = sum(1 for item in analysis_records if item.get("kind") == "md")
    stale_count = sum(1 for item in selected_candidates if stale_days(item["mtime"]) >= 90)

    return [
        {"signal": "selected_source_files", "value": len(selected_candidates)},
        {"signal": "analyzed_units", "value": aggregate["analyzed_units"]},
        {"signal": "json_parsed", "value": json_ok},
        {"signal": "csv_parsed", "value": csv_ok},
        {"signal": "markdown_scanned", "value": md_count},
        {"signal": "parse_failures", "value": aggregate["parse_failures"]},
        {"signal": "stale_hotspots", "value": stale_count},
        {"signal": "sensitive_pattern_total", "value": sum(aggregate["sensitive_pattern_counts"].values())},
    ]


def build_recommended_actions(risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    severity_priority = {"high": "P1", "medium": "P2", "low": "P3"}
    actions: list[dict[str, Any]] = []

    for risk in risks[:6]:
        actions.append(
            {
                "priority": severity_priority.get(risk["severity"], "P3"),
                "action": risk["recommendation"],
                "owner": "Ops Leadership",
                "rationale": risk["title"],
            }
        )

    if not actions:
        actions.append(
            {
                "priority": "P3",
                "action": "Maintain current ingestion cadence and continue periodic health scans.",
                "owner": "Ops Leadership",
                "rationale": "No major risk signal exceeded threshold in this run.",
            }
        )

    return actions


def render_markdown(payload: dict[str, Any], top_findings: int) -> str:
    summary = payload["summary"]
    lines: list[str] = []

    lines.append("# Executive Brief")
    lines.append("")
    lines.append("## Decision Snapshot")
    lines.append(f"- Generated at: `{summary['generated_at']}`")
    lines.append(f"- Audience: `{summary['audience']}`")
    lines.append(f"- Sources selected: `{summary['source_files_selected']}` of `{summary['source_files_considered']}` considered")
    lines.append(f"- Units analyzed: `{summary['files_scanned']}`")
    lines.append(f"- Parse failures: `{summary['parse_failures']}`")
    lines.append(f"- High risks: `{summary['high_risk_count']}`")
    lines.append("")

    lines.append("## Top Risks")
    top_risks = payload["top_risks"][:top_findings]
    if top_risks:
        for idx, risk in enumerate(top_risks, start=1):
            lines.append(
                f"{idx}. [{risk['severity'].upper()}] {risk['title']} (evidence={risk['evidence_count']}, sources={risk['source_count']})"
            )
            lines.append(f"   - Impact: {risk['impact']}")
            lines.append(f"   - Recommendation: {risk['recommendation']}")
    else:
        lines.append("No material risk signals detected.")
    lines.append("")

    lines.append("## Operational Signals")
    for signal in payload["key_signals"]:
        lines.append(f"- `{signal['signal']}`: `{signal['value']}`")
    lines.append("")

    lines.append("## Recommended Actions")
    for idx, action in enumerate(payload["recommended_actions"], start=1):
        lines.append(f"{idx}. [{action['priority']}] {action['action']}")
        lines.append(f"   - Owner: {action['owner']}")
        lines.append(f"   - Rationale: {action['rationale']}")
    lines.append("")

    lines.append("## Evidence Appendix")
    if payload["evidence"]:
        for evidence in payload["evidence"][:60]:
            lines.append(
                f"- `{evidence['source']}` | `{evidence['type']}` | `{evidence['signal']}` | {evidence['snippet']}"
            )
    else:
        lines.append("- No evidence entries captured.")
    lines.append("")

    return "\n".join(lines)


def build_output(
    args: argparse.Namespace,
    input_dir: Path,
    out_dir: Path,
    include_globs: list[str],
    candidates: list[dict[str, Any]],
    selected_candidates: list[dict[str, Any]],
    analysis_records: list[dict[str, Any]],
    aggregate: dict[str, Any],
    zip_metadata: list[dict[str, Any]],
) -> dict[str, Any]:
    consolidated_risks = consolidate_risks(aggregate["risks"])
    top_risks = consolidated_risks[: args.top_findings]
    key_signals = build_key_signals(selected_candidates, analysis_records, aggregate)
    actions = build_recommended_actions(top_risks)

    summary = {
        "generated_at": now_utc_iso(),
        "audience": "ops_leadership",
        "input_dir": str(input_dir),
        "out_dir": str(out_dir),
        "source_files_considered": len(candidates),
        "source_files_selected": len(selected_candidates),
        "files_scanned": aggregate["analyzed_units"],
        "parse_failures": aggregate["parse_failures"],
        "high_risk_count": sum(1 for item in top_risks if item["severity"] == "high"),
    }

    payload = {
        "summary": summary,
        "top_risks": top_risks,
        "key_signals": key_signals,
        "recommended_actions": actions,
        "evidence": aggregate["evidence"],
        "sensitive_pattern_counts": dict(aggregate["sensitive_pattern_counts"]),
        "analysis_scope": {
            "mode": "mixed_folder_scan",
            "include_globs": include_globs,
            "max_files": args.max_files,
            "ranking_strategy": "recency_plus_filename_signal_plus_extension_signal",
            "tie_breaker": "path_ascending",
            "excluded_paths": [str(out_dir)],
            "selected_sources": [item["relative_path"] for item in selected_candidates],
            "zip_members_scanned": sum(item.get("members_scanned", 0) for item in zip_metadata),
            "zip_archives": zip_metadata,
        },
    }
    return payload


def write_outputs(out_dir: Path, payload: dict[str, Any], top_findings: int) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "executive_brief.json"
    md_path = out_dir / "executive_brief.md"

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(payload, top_findings), encoding="utf-8")


def write_manifest(
    out_dir: Path,
    args: argparse.Namespace,
    candidates: list[dict[str, Any]],
    selected_candidates: list[dict[str, Any]],
) -> None:
    manifest = {
        "generated_at": now_utc_iso(),
        "args": {
            "input_dir": args.input_dir,
            "out_dir": args.out_dir,
            "max_files": args.max_files,
            "include_globs": args.include_globs,
            "top_findings": args.top_findings,
            "strict": args.strict,
            "emit_run_manifest": args.emit_run_manifest,
        },
        "candidate_count": len(candidates),
        "selected_count": len(selected_candidates),
        "candidates": [
            {
                "relative_path": item["relative_path"],
                "ext": item["ext"],
                "mtime": item["mtime"],
                "size_bytes": item["size_bytes"],
                "filename_signal": item["filename_signal"],
                "extension_signal": item["extension_signal"],
                "recency_points": item.get("recency_points", 0),
                "score": item.get("score", 0),
            }
            for item in candidates
        ],
        "selected_sources": [item["relative_path"] for item in selected_candidates],
    }

    manifest_path = out_dir / "run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()

    input_dir = Path(args.input_dir).expanduser().resolve()
    if not input_dir.exists() or not input_dir.is_dir():
        print(f"[ERROR] --input-dir is not a directory: {input_dir}", file=sys.stderr)
        return 1

    out_dir = Path(args.out_dir).expanduser().resolve() if args.out_dir else (input_dir / "reports").resolve()
    include_globs = parse_globs(args.include_globs)

    if args.max_files <= 0:
        print("[ERROR] --max-files must be greater than zero.", file=sys.stderr)
        return 1
    if args.top_findings <= 0:
        print("[ERROR] --top-findings must be greater than zero.", file=sys.stderr)
        return 1

    candidates = collect_candidates(input_dir=input_dir, include_globs=include_globs, out_dir=out_dir)
    ranked = rank_candidates(candidates)
    selected = ranked[: args.max_files]

    aggregate: dict[str, Any] = {
        "parse_failures": 0,
        "analyzed_units": 0,
        "risks": [],
        "evidence": [],
        "sensitive_pattern_counts": Counter(),
    }
    analysis_records: list[dict[str, Any]] = []
    zip_metadata: list[dict[str, Any]] = []

    for item in selected:
        path = item["path"]
        rel = item["relative_path"]
        ext = item["ext"]

        if ext == ".zip":
            records, zip_meta = analyze_zip_file(path, rel, aggregate)
            zip_metadata.append(zip_meta)
            analysis_records.extend(records)
            aggregate["analyzed_units"] += len(records)
            continue

        text, truncated = read_text_file(path)
        record = analyze_text_source(rel, ext, text, aggregate)
        record["truncated"] = truncated
        analysis_records.append(record)
        aggregate["analyzed_units"] += 1

        if truncated:
            aggregate["risks"].append(
                {
                    "risk_id": "file_truncated",
                    "severity": "low",
                    "title": "Large File Truncation",
                    "impact": "Only partial content was analyzed due to file-size limits.",
                    "recommendation": "Split oversized files or increase read caps for deep analysis.",
                    "evidence_count": 1,
                    "source": rel,
                }
            )
            add_evidence(aggregate["evidence"], rel, ext.lstrip("."), "file_truncated", "Content truncated at read cap")

    cross_file_analysis(selected, aggregate)

    payload = build_output(
        args=args,
        input_dir=input_dir,
        out_dir=out_dir,
        include_globs=include_globs,
        candidates=ranked,
        selected_candidates=selected,
        analysis_records=analysis_records,
        aggregate=aggregate,
        zip_metadata=zip_metadata,
    )

    write_outputs(out_dir, payload, args.top_findings)

    if args.emit_run_manifest:
        write_manifest(out_dir, args, ranked, selected)

    strict_violation = payload["summary"]["parse_failures"] > 0 or any(
        risk["severity"] == "high" for risk in payload["top_risks"]
    )
    if args.strict and strict_violation:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

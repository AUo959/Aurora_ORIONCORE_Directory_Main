#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from _workspace_common import (
    detect_private_signal,
    load_yaml_like,
    now_iso_utc,
    relpath,
    resolve_root,
    serialized_root,
    sha256_file,
    write_json,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "catalog" / "recovery_index_manifest.json"
DEFAULT_REPORT = ROOT / "reports" / "analysis" / "workspace_recovery_index_latest.json"


def load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Recovery manifest must be a JSON object: {path}")
    return payload


def as_set(values: Iterable[str] | None) -> set[str]:
    return {str(value).lower() for value in values or []}


def path_is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
    except ValueError:
        return False
    return True


def display_path(path: Path, root: Path) -> str:
    try:
        return relpath(path, root)
    except ValueError:
        return str(path)


def should_exclude_path(path: Path, root: Path, manifest: dict[str, Any]) -> bool:
    excluded_names = as_set(manifest.get("exclude_directory_names"))
    if path.name.lower() in excluded_names:
        return True

    relative = display_path(path, root)
    for excluded in manifest.get("exclude_subpaths", []):
        excluded_path = str(excluded).strip("/")
        if relative == excluded_path or relative.startswith(f"{excluded_path}/"):
            return True
    return False


def iter_scan_files(
    root: Path,
    scan_root: Path,
    scan_spec: dict[str, Any],
    manifest: dict[str, Any],
) -> tuple[list[Path], dict[str, Any]]:
    state = {
        "path": scan_spec.get("path", ""),
        "mode": scan_spec.get("mode", "tree"),
        "source_status": scan_spec.get("source_status", "recovered"),
        "priority": scan_spec.get("priority", "medium"),
        "reason": scan_spec.get("reason", ""),
        "exists": scan_root.exists(),
        "truncated": False,
        "scanned_file_count": 0,
        "candidate_count": 0,
    }
    if not scan_root.exists():
        return [], state

    max_files = int(scan_spec.get("max_files_per_root") or manifest.get("max_files_per_root") or 0)
    mode = str(scan_spec.get("mode", "tree"))
    files: list[Path] = []

    def add_file(path: Path) -> bool:
        if should_exclude_path(path, root, manifest):
            return True
        files.append(path)
        state["scanned_file_count"] = int(state["scanned_file_count"]) + 1
        if max_files and len(files) >= max_files:
            state["truncated"] = True
            return False
        return True

    if scan_root.is_file():
        add_file(scan_root)
        return files, state

    if mode == "top_level_files":
        for path in sorted(scan_root.iterdir(), key=lambda item: item.name.lower()):
            if path.is_file() and not add_file(path):
                break
        return files, state

    max_depth = scan_spec.get("max_depth")
    max_depth_int = int(max_depth) if max_depth is not None else None
    for current_root, dirnames, filenames in os.walk(scan_root):
        current = Path(current_root)
        if should_exclude_path(current, root, manifest):
            dirnames[:] = []
            continue
        if current != scan_root and ((current / ".git").exists() or ".git" in filenames):
            dirnames[:] = []
            continue
        if max_depth_int is not None:
            depth = len(current.relative_to(scan_root).parts)
            if depth >= max_depth_int:
                dirnames[:] = []
        dirnames[:] = [
            name
            for name in sorted(dirnames)
            if not should_exclude_path(current / name, root, manifest)
        ]
        for filename in sorted(filenames):
            path = current / filename
            if not path.is_file():
                continue
            if not add_file(path):
                return files, state
    return files, state


def allowed_file(path: Path, manifest: dict[str, Any]) -> bool:
    include_extensions = as_set(manifest.get("include_extensions"))
    include_filenames = {str(value) for value in manifest.get("include_filenames", [])}
    return path.suffix.lower() in include_extensions or path.name in include_filenames


def read_text_probe(path: Path, max_probe_bytes: int) -> tuple[str, bool]:
    try:
        payload = path.read_bytes()
    except OSError:
        return "", False
    if b"\x00" in payload[: min(len(payload), max_probe_bytes)]:
        return "", False
    text = payload[:max_probe_bytes].decode("utf-8", errors="ignore")
    return text, bool(text.strip())


def term_hit(terms: Iterable[str] | None, value: str) -> bool:
    lowered = value.lower()
    return any(str(term).lower() in lowered for term in terms or [])


def match_signal(signal: dict[str, Any], path: Path, relative: str, text: str) -> bool:
    suffixes = as_set(signal.get("extensions"))
    if suffixes and path.suffix.lower() in suffixes:
        return True
    if term_hit(signal.get("path_terms"), relative):
        return True
    if term_hit(signal.get("content_terms"), text):
        return True
    return False


def analyze_signals(
    path: Path,
    relative: str,
    text: str,
    manifest: dict[str, Any],
) -> tuple[list[str], int, bool]:
    matched: list[str] = []
    score = 0
    restricted = False
    for signal in manifest.get("value_signals", []):
        if not isinstance(signal, dict):
            continue
        if not match_signal(signal, path, relative, text):
            continue
        signal_id = str(signal.get("id", "unnamed_signal"))
        matched.append(signal_id)
        score += int(signal.get("weight", 1))
        restricted = restricted or bool(signal.get("restricted", False))
    return sorted(set(matched)), score, restricted


def route_hint(relative: str, text: str, manifest: dict[str, Any]) -> dict[str, str]:
    for route in manifest.get("route_hints", []):
        if not isinstance(route, dict):
            continue
        if term_hit(route.get("path_terms"), relative) or term_hit(route.get("content_terms"), text):
            return {
                "target": str(route.get("target", "review-required")),
                "owner_surface": str(route.get("owner_surface", "review")),
            }
    return {
        "target": "review-required",
        "owner_surface": "manual recovery review",
    }


def line_count(text: str) -> int:
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def load_recovery_objects(root: Path) -> dict[str, Any]:
    path = root / "catalog" / "recovery_objects_to_resolve.json"
    if not path.exists():
        return {
            "path": display_path(path, root),
            "exists": False,
            "count": 0,
            "open_count": 0,
            "objects": [],
        }
    payload = load_yaml_like(path) or {}
    objects = payload.get("objects", []) if isinstance(payload, dict) else []
    normalized = []
    for item in objects:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "object_id": item.get("object_id", ""),
                "category": item.get("category", ""),
                "status": item.get("status", ""),
                "priority": item.get("priority", ""),
                "title": item.get("title", ""),
            }
        )
    return {
        "path": display_path(path, root),
        "exists": True,
        "count": len(normalized),
        "open_count": sum(1 for item in normalized if str(item.get("status")) == "open"),
        "objects": normalized,
    }


def build_candidate(
    path: Path,
    root: Path,
    scan_spec: dict[str, Any],
    manifest: dict[str, Any],
) -> tuple[dict[str, Any] | None, str]:
    relative = display_path(path, root)
    if not allowed_file(path, manifest):
        return None, "extension"

    try:
        stat = path.stat()
    except OSError:
        return None, "stat_error"

    max_file_bytes = int(manifest.get("max_file_bytes", 2_000_000))
    if stat.st_size > max_file_bytes:
        return None, "size"

    private_signal = detect_private_signal(path)
    if private_signal:
        return None, private_signal

    text, readable = read_text_probe(path, int(manifest.get("max_probe_bytes", 65_536)))
    if not readable:
        return None, "unreadable_or_binary"

    signals, value_score, restricted = analyze_signals(path, relative, text, manifest)
    if value_score < int(manifest.get("min_value_score", 1)):
        return None, "below_threshold"

    route = route_hint(relative, text, manifest)
    digest = ""
    if stat.st_size <= int(manifest.get("max_hash_bytes", 5_000_000)):
        digest = sha256_file(path)

    candidate = {
        "path": relative,
        "source_root": str(scan_spec.get("path", "")),
        "source_status": str(scan_spec.get("source_status", "recovered")),
        "source_priority": str(scan_spec.get("priority", "medium")),
        "promotion_status": "pending_review",
        "canonical_status": "not_promoted",
        "target_repo_hint": route["target"],
        "owner_surface_hint": route["owner_surface"],
        "value_score": value_score,
        "signals": signals,
        "restricted_material_possible": restricted,
        "size_bytes": stat.st_size,
        "mtime": int(stat.st_mtime),
        "sha256": digest,
        "extension": path.suffix.lower(),
        "line_count": line_count(text),
        "notes": "restricted signal requires careful handling" if restricted else "",
    }
    return candidate, "candidate"


def build_report(
    root: Path,
    manifest_path: Path,
    generated_at: str | None = None,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    all_candidates: list[dict[str, Any]] = []
    scan_roots: list[dict[str, Any]] = []
    skip_counts: Counter[str] = Counter()

    for scan_spec in manifest.get("scan_roots", []):
        if not isinstance(scan_spec, dict):
            continue
        scan_root = (root / str(scan_spec.get("path", ""))).resolve()
        files, state = iter_scan_files(root, scan_root, scan_spec, manifest)
        for path in files:
            candidate, reason = build_candidate(path, root, scan_spec, manifest)
            if candidate is None:
                skip_counts[reason] += 1
                continue
            all_candidates.append(candidate)
        state["candidate_count"] = sum(
            1 for candidate in all_candidates if candidate["source_root"] == str(scan_spec.get("path", ""))
        )
        scan_roots.append(state)

    all_candidates = sorted(
        all_candidates,
        key=lambda item: (
            -int(item["value_score"]),
            str(item["target_repo_hint"]),
            str(item["path"]),
        ),
    )
    max_candidates = int(manifest.get("max_candidates", 100))
    retained_candidates = all_candidates[:max_candidates]
    truncated_candidates = len(all_candidates) > len(retained_candidates)
    route_counts = Counter(str(item["target_repo_hint"]) for item in retained_candidates)
    status_counts = Counter(str(item["source_status"]) for item in retained_candidates)
    signal_counts: Counter[str] = Counter()
    for item in retained_candidates:
        signal_counts.update(str(signal) for signal in item.get("signals", []))

    findings = []
    missing_roots = [str(item["path"]) for item in scan_roots if not item.get("exists")]
    if missing_roots:
        findings.append(
            {
                "severity": "warning",
                "id": "missing_scan_roots",
                "message": "Configured recovery scan roots are absent in this workspace.",
                "evidence": ", ".join(missing_roots),
                "next_step": "Run from the canonical root path before treating missing local archive surfaces as resolved.",
            }
        )
    truncated_roots = [str(item["path"]) for item in scan_roots if item.get("truncated")]
    if truncated_roots:
        findings.append(
            {
                "severity": "warning",
                "id": "scan_root_file_limit_applied",
                "message": "One or more scan roots hit max_files_per_root.",
                "evidence": ", ".join(truncated_roots),
                "next_step": "Increase the configured file limit or split the archive family into a scoped recovery pass.",
            }
        )

    status = "WARN" if findings else "READY"
    return {
        "schema_version": 1,
        "generated_at": generated_at or now_iso_utc(),
        "root": serialized_root(root),
        "tool": "workspace_recovery_index",
        "mode": "read_only",
        "manifest_path": display_path(manifest_path, root),
        "status": status,
        "summary": {
            "scan_root_count": len(scan_roots),
            "scanned_file_count": sum(int(item["scanned_file_count"]) for item in scan_roots),
            "candidate_count": len(retained_candidates),
            "discovered_candidate_count": len(all_candidates),
            "candidate_limit_applied": truncated_candidates,
            "skip_counts": dict(sorted(skip_counts.items())),
            "candidates_by_target_repo_hint": dict(sorted(route_counts.items())),
            "candidates_by_source_status": dict(sorted(status_counts.items())),
            "signal_counts": dict(sorted(signal_counts.items())),
        },
        "scan_roots": scan_roots,
        "tracked_recovery_objects": load_recovery_objects(root),
        "findings": findings,
        "candidates": retained_candidates,
        "validation_commands": manifest.get("validation_commands", []),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a read-only index of recoverable early local Aurora work.")
    parser.add_argument("--root", default=str(ROOT), help="Aurora root workspace path.")
    parser.add_argument("--manifest", help="Recovery index manifest path. Defaults to <root>/catalog/recovery_index_manifest.json.")
    parser.add_argument("--report-out", help="Write the JSON report to this path.")
    parser.add_argument("--persist-report", action="store_true", help="Write the configured latest recovery index report.")
    parser.add_argument("--json", action="store_true", dest="json_out", help="Print full JSON. This is the default output.")
    parser.add_argument("--summary", action="store_true", help="Print a compact text summary instead of JSON.")
    return parser.parse_args(argv)


def format_summary(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        f"Aurora Recovery Index: {report['status']}",
        f"- Mode: {report['mode']}",
        f"- Scanned files: {summary['scanned_file_count']}",
        f"- Candidates retained: {summary['candidate_count']} of {summary['discovered_candidate_count']}",
        f"- Target hints: {summary['candidates_by_target_repo_hint']}",
    ]
    if report["findings"]:
        lines.append("- Findings:")
        for finding in report["findings"]:
            lines.append(f"  - [{finding['severity']}] {finding['id']}: {finding['message']}")
    else:
        lines.append("- Findings: none")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    manifest_path = Path(args.manifest).expanduser().resolve() if args.manifest else root / "catalog" / "recovery_index_manifest.json"
    report = build_report(root, manifest_path)
    manifest = load_manifest(manifest_path)

    if args.persist_report:
        default_report = root / str(manifest.get("default_report_path", DEFAULT_REPORT.relative_to(ROOT)))
        write_json(default_report, report)

    if args.report_out:
        write_json(Path(args.report_out).expanduser().resolve(), report)

    if args.summary:
        print(format_summary(report))
    else:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

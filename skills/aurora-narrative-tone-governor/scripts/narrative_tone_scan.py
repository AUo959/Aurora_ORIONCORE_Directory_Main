#!/usr/bin/env python3
"""Narrative/tone governance scan CLI."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_CANONICAL_ROOTS = [
    "GUMAS_SIM_2.0/02_DEVELOPMENT/Project_Main/Project_Files_GUMAS2_0",
    "GUMAS_SIM_2.0/03_SIMULATION/Location_Data/Sim_Locations",
    "GUMAS_SIM_2.5/FORGE__GUMAS_v3.0__2026-02-19",
    "GUMAS_SIM_2.5/PROJECT_KNOWLEDGE",
]

TEXT_SUFFIXES = {".md", ".txt"}
NARRATIVE_HINTS = ("thread", "run", "recap", "scene", "story", "log", "report", "brief", "output")
SKIP_NAME_TOKENS = (
    "narrlint",
    "cadencetonelinter",
    "anti-flourish",
    "projectlibraryoverview",
    "promotion_queue",
    "staging_manifest",
    "_index_",
    "patch_notes",
    "canonical_files",
    "deduplication_report",
    "reorganization_manifest",
)

RULE_META_OR_CLOSER = re.compile(
    r"(?i)(logs?|history|record) (will|would) (remember|record|see)|"
    r"this (scene|moment|day) (is|was) (really )?about|"
    r"what we are seeing here is|"
    r"It (was|became) (a|the) (day|moment|scene) when|"
    r"In the end, this (was|became)"
)
RULE_EMPTY_CONTRAST = re.compile(
    r"(?i)not (just|only) [^,.]+, (but|also)|not only [^,.]+, (but|also)|both [^,.]+ and [^,.]+"
)
RULE_WARN_TOKENS = re.compile(r"(?i)\bquietly\b|\bsilently\b|\bsubtly\b|\bwordlessly\b|in the background")
RULE_HARD_BANS = re.compile(r"(?i)in the lived frame|beneath the surface|deep down|at some quieter level")
RULE_P001 = re.compile(r"(?i)\b(no|not)\b[^\n\.]{0,60}\b(no|not)\b[^\n\.]{0,60}\bjust\b")
RULE_P301 = re.compile(r"(?i)\b(always|never|guarantee|100%|cannot fail|fails?afe)\b")
IDENTIFIER_PATTERN = re.compile(r"\b[A-Z]{2,}(?:-[A-Z0-9]+)+\b")
STAKE_DECISION_PATTERN = re.compile(
    r"(?i)\b(risk|opportunity|cost|stake|decision|decided|approved|rejected|deferred|paused)\b"
)


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_csv(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def resolve_targets(repo_root: Path, roots: list[str], paths: list[str]) -> list[Path]:
    resolved: list[Path] = []
    raw_targets = paths if paths else roots
    for raw in raw_targets:
        path = Path(raw).expanduser()
        candidate = path if path.is_absolute() else (repo_root / path)
        if not candidate.exists():
            continue
        if candidate.is_file():
            resolved.append(candidate.resolve())
            continue
        for child in candidate.rglob("*"):
            if child.is_file():
                resolved.append(child.resolve())
    return sorted(set(resolved))


def should_skip(path: Path) -> bool:
    lowered = str(path).lower()
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return True
    return any(token in lowered for token in SKIP_NAME_TOKENS)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def strip_code_fences(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


def line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def line_excerpt(text: str, line_no: int) -> str:
    lines = text.splitlines()
    if 1 <= line_no <= len(lines):
        return lines[line_no - 1].strip()
    return ""


def make_finding(
    *,
    severity: str,
    rule_id: str,
    family: str,
    file: str,
    message: str,
    evidence: str,
    suggested_fix: str,
) -> dict[str, str]:
    return {
        "domain": "narrative_tone",
        "severity": severity,
        "rule_id": rule_id,
        "family": family,
        "file": file,
        "source_path": file,
        "message": message,
        "rationale": message,
        "evidence": evidence,
        "remediation": suggested_fix,
        "suggested_fix": suggested_fix,
        "blocking_scope": "authoritative",
        "source_tool": "narrative-tone-scan",
    }


def severity_for_warning(strictness: str) -> str:
    return "INFO" if strictness == "lenient" else "WARN"


def governance_outcome(severity_counts: Counter[str]) -> tuple[str, str]:
    if severity_counts.get("BLOCK", 0) > 0:
        return ("BLOCK", "NOT_READY")
    if severity_counts.get("WARN", 0) > 0:
        return ("REVIEW", "CONDITIONAL")
    return ("PASS", "READY")


def has_inline_explanation(line: str, identifier: str) -> bool:
    idx = line.find(identifier)
    if idx == -1:
        return False
    window = line[idx + len(identifier) : idx + len(identifier) + 48]
    lowered = line.lower()
    return "(" in window or "called" in lowered or "means" in lowered or "code for" in lowered


def looks_narrative_like(path: Path, text: str) -> bool:
    lowered_path = str(path).lower()
    if any(token in lowered_path for token in NARRATIVE_HINTS):
        return True
    return bool(re.search(r"\b\d{1,2}:\d{2}\b", text))


def scan_file(repo_root: Path, path: Path, strictness: str) -> list[dict[str, str]]:
    raw = read_text(path)
    if not raw.strip():
        return []

    text = strip_code_fences(raw)
    findings: list[dict[str, str]] = []
    seen: set[tuple[str, int]] = set()
    rel = str(path.relative_to(repo_root))

    def collect(pattern: re.Pattern[str], rule_id: str, severity: str, family: str, message: str, fix: str) -> None:
        for match in pattern.finditer(text):
            hit_line = line_number(text, match.start())
            key = (rule_id, hit_line)
            if key in seen:
                continue
            seen.add(key)
            findings.append(
                make_finding(
                    severity=severity,
                    rule_id=rule_id,
                    family=family,
                    file=f"{rel}:{hit_line}",
                    message=message,
                    evidence=line_excerpt(text, hit_line),
                    suggested_fix=fix,
                )
            )

    collect(
        RULE_META_OR_CLOSER,
        "LINT-NARR-001",
        "BLOCK",
        "narrative_style",
        "Meta-narration or thematic closer detected in strict narrative text.",
        "Replace thematic/log-aware phrasing with a direct operational statement.",
    )
    collect(
        RULE_EMPTY_CONTRAST,
        "LINT-NARR-002",
        "BLOCK",
        "narrative_style",
        "Contrast scaffold may lack new operational state.",
        "Collapse the scaffold and state the concrete difference directly.",
    )
    collect(
        RULE_WARN_TOKENS,
        "LINT-NARR-003",
        severity_for_warning(strictness),
        "narrative_style",
        "Atmospheric warning token detected.",
        "Replace the atmospheric token with explicit observable state or remove it.",
    )
    collect(
        RULE_HARD_BANS,
        "LINT-NARR-004",
        "BLOCK",
        "narrative_style",
        "Hard-banned narrative flourish detected.",
        "Replace the phrase with concrete operational language.",
    )
    collect(
        RULE_P001,
        "P001_NO_NO_JUST",
        "BLOCK",
        "tone_cadence",
        "CTL hard-override cadence pattern detected.",
        "Merge the triad into one direct sentence without the slogan pivot.",
    )
    collect(
        RULE_P301,
        "P301_CERTAINTY_INFLATION",
        "BLOCK",
        "tone_cadence",
        "Certainty inflation detected in factual narrative text.",
        "Calibrate the claim to available evidence and avoid absolutes.",
    )

    if looks_narrative_like(path, text):
        for match in IDENTIFIER_PATTERN.finditer(text):
            hit_line = line_number(text, match.start())
            key = ("LINT-NARR-005", hit_line)
            if key in seen:
                continue
            evidence = line_excerpt(text, hit_line)
            if has_inline_explanation(evidence, match.group(0)):
                continue
            seen.add(key)
            findings.append(
                make_finding(
                    severity=severity_for_warning(strictness),
                    rule_id="LINT-NARR-005",
                    family="audience_clarity",
                    file=f"{rel}:{hit_line}",
                    message="Non-obvious identifier appears without first-use explanation.",
                    evidence=evidence,
                    suggested_fix="Explain the first occurrence in human-readable language before reusing the identifier.",
                )
            )

        lowered_name = path.name.lower()
        if any(token in lowered_name for token in ("run", "recap", "log", "report")) and not STAKE_DECISION_PATTERN.search(text):
            findings.append(
                make_finding(
                    severity=severity_for_warning(strictness),
                    rule_id="LINT-NARR-006",
                    family="story_structure",
                    file=rel,
                    message="Narrative recap lacks explicit stake/decision vocabulary; verify recap metadata.",
                    evidence=path.name,
                    suggested_fix="Confirm the recap carries at least one explicit stake and one decision reference in prose or metadata.",
                )
            )

    return findings


def build_report(repo_root: Path, roots: list[str], paths: list[str], strictness: str) -> dict[str, object]:
    scanned_files = 0
    findings: list[dict[str, str]] = []

    for path in resolve_targets(repo_root, roots, paths):
        if should_skip(path):
            continue
        scanned_files += 1
        findings.extend(scan_file(repo_root, path, strictness))

    severity_counts = Counter(str(item.get("severity", "INFO")) for item in findings)
    verdict, promotion_readiness = governance_outcome(severity_counts)
    return {
        "domain": "narrative_tone",
        "verdict": verdict,
        "promotion_readiness": promotion_readiness,
        "scan_meta": {
            "generated_at": now_utc_iso(),
            "repo_root": str(repo_root),
            "strictness": strictness,
            "roots": roots,
            "paths": paths,
        },
        "summary": {
            "scanned_files": scanned_files,
            "total_findings": len(findings),
            "by_severity": {
                "BLOCK": severity_counts.get("BLOCK", 0),
                "WARN": severity_counts.get("WARN", 0),
                "INFO": severity_counts.get("INFO", 0),
            },
        },
        "findings": findings,
    }


def render_markdown(report: dict[str, object]) -> str:
    summary = report.get("summary") or {}
    findings = report.get("findings") or []

    lines = [
        "# Narrative Tone Scan Report",
        "",
        "## Summary",
        f"- Verdict: `{report.get('verdict', 'PASS')}`",
        f"- Promotion readiness: `{report.get('promotion_readiness', 'READY')}`",
        f"- Scanned files: `{summary.get('scanned_files', 0)}`",
        f"- Total findings: `{summary.get('total_findings', 0)}`",
        f"- By severity: `{json.dumps(summary.get('by_severity', {}), ensure_ascii=False)}`",
        "",
        "## Findings",
    ]

    if findings:
        for row in findings:
            lines.append(
                f"- [{row.get('severity')}] [{row.get('rule_id')}] `{row.get('file')}`: "
                f"{row.get('message')} Evidence: `{row.get('evidence')}` Remediation: `{row.get('remediation')}`"
            )
    else:
        lines.append("- None")

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run narrative/tone governance scan over Aurora text artifacts.")
    parser.add_argument("--repo", required=True, help="Repository root path")
    parser.add_argument("--roots", help="Optional CSV list of canonical scan roots")
    parser.add_argument("--paths", help="Optional CSV list of files/dirs to scan instead of roots")
    parser.add_argument(
        "--strictness",
        choices=["balanced", "strict", "lenient"],
        default="balanced",
        help="Severity profile for warning-class findings",
    )
    parser.add_argument("--out-json", required=True, help="Path to write JSON output")
    parser.add_argument("--out-md", required=True, help="Path to write markdown output")
    parser.add_argument("--fail-on-block", action="store_true", help="Return non-zero if any BLOCK findings exist")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo).expanduser().resolve()
    roots = parse_csv(args.roots) or list(DEFAULT_CANONICAL_ROOTS)
    paths = parse_csv(args.paths)

    report = build_report(repo_root, roots=roots, paths=paths, strictness=args.strictness)

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(render_markdown(report), encoding="utf-8")

    block_count = (report.get("summary") or {}).get("by_severity", {}).get("BLOCK", 0)
    if args.fail_on_block and block_count:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

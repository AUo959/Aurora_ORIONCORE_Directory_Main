#!/usr/bin/env python3
"""Scan Aurora repository scripts for governance and drift risks."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List

SCRIPT_SUFFIXES = {".py", ".sh", ".bash", ".zsh", ".js", ".cjs", ".mjs", ".ts"}

SETUP_NAME_PATTERN = re.compile(r"(?:^|[_-])(setup|bootstrap|init|initialize)(?:[_-]|$)", re.IGNORECASE)
SETUP_DIAGNOSTIC_MARKERS = [
    re.compile(r"diagnostic mode", re.IGNORECASE),
    re.compile(r"no-?op", re.IGNORECASE),
    re.compile(r"intentionally performs diagnostics", re.IGNORECASE),
    re.compile(r"guidance:", re.IGNORECASE),
]
SETUP_MUTATION_MARKERS = [
    re.compile(r"\bpip\s+install\b", re.IGNORECASE),
    re.compile(r"\bnpm\s+(?:install|ci)\b", re.IGNORECASE),
    re.compile(r"\byarn\s+install\b", re.IGNORECASE),
    re.compile(r"\bapt(?:-get)?\s+install\b", re.IGNORECASE),
    re.compile(r"\bbrew\s+install\b", re.IGNORECASE),
    re.compile(r"\bcp\s+[^\n]*\.env", re.IGNORECASE),
    re.compile(r"\bpython(?:3)?\s+-m\s+pip\s+install\b", re.IGNORECASE),
]

BRANCH_CLEANUP_PATTERN = re.compile(
    r"(?:branch[_-]?cleanup|cleanup[_-]?stale[_-]?branches|automated[_-]?branch[_-]?cleanup|branch[_-]?manager)",
    re.IGNORECASE,
)

HAZARD_PATTERNS = [
    {
        "kind": "brace_literal_print",
        "severity": "medium",
        "pattern": re.compile(r"print\(\s*[\"'][^\n\"']*\{[^\n\"']+\}[^\n\"']*[\"']\s*\)"),
        "message": "Likely missing f-string interpolation in print/log output.",
    },
    {
        "kind": "malformed_git_subcommand",
        "severity": "high",
        "pattern": re.compile(r"\bgit\s+di\b|[\"']git[\"']\s*,\s*[\"']di[\"']", re.IGNORECASE),
        "message": "Malformed git subcommand detected (for example, git di).",
    },
    {
        "kind": "subprocess_shell_true",
        "severity": "medium",
        "pattern": re.compile(
            r"subprocess\.(?:run|Popen|call|check_call|check_output)\([^\n)]*shell\s*=\s*True",
            re.IGNORECASE,
        ),
        "message": "subprocess with shell=True can introduce command-injection and quoting risks.",
    },
    {
        "kind": "curl_pipe_shell",
        "severity": "high",
        "pattern": re.compile(r"\bcurl\b[^\n|]*\|\s*(?:bash|sh)\b", re.IGNORECASE),
        "message": "Piping curl output directly to a shell is high-risk.",
    },
    {
        "kind": "broad_rm_rf",
        "severity": "high",
        "pattern": re.compile(r"\brm\s+-rf\s+(?:/|~|\$[A-Z_][A-Z0-9_]*)", re.IGNORECASE),
        "message": "Broad rm -rf target detected; validate guardrails and path safety.",
    },
]

NATIVE_TO_GOVERNANCE_SEVERITY = {
    "high": "BLOCK",
    "medium": "WARN",
    "low": "INFO",
}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def is_script_file(path: Path) -> bool:
    lower = path.name.lower()
    if lower.endswith(".disabled"):
        return True
    if path.suffix.lower() in SCRIPT_SUFFIXES:
        return True
    return path.name in {"pre-commit", "pre-push", "post-commit"}


def find_script_files(repo_root: Path, exclude_disabled: bool) -> List[Path]:
    scripts_dir = repo_root / "scripts"
    if not scripts_dir.exists() or not scripts_dir.is_dir():
        return []

    files: List[Path] = []
    for path in scripts_dir.rglob("*"):
        if not path.is_file() or not is_script_file(path):
            continue
        if exclude_disabled and path.name.lower().endswith(".disabled"):
            continue
        files.append(path)
    return sorted(files)


def line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def short_line(text: str, line_no: int) -> str:
    lines = text.splitlines()
    if 1 <= line_no <= len(lines):
        return lines[line_no - 1].strip()
    return ""


def setup_findings(path: Path, root: Path, text: str, size: int) -> Iterable[Dict[str, str]]:
    rel = str(path.relative_to(root))
    name = path.stem.lower()
    if not SETUP_NAME_PATTERN.search(name):
        return []

    has_diagnostic_marker = any(pattern.search(text) for pattern in SETUP_DIAGNOSTIC_MARKERS)
    has_mutation_marker = any(pattern.search(text) for pattern in SETUP_MUTATION_MARKERS)

    findings: List[Dict[str, str]] = []

    if size == 0:
        findings.append(
            {
                "kind": "setup_zero_byte",
                "severity": "high",
                "path": rel,
                "message": "Setup entrypoint is empty.",
                "remediation": "Convert to a diagnostic no-op script with environment checks and explicit next-step guidance.",
            }
        )
    elif has_mutation_marker and not has_diagnostic_marker:
        findings.append(
            {
                "kind": "setup_mutating_without_guidance",
                "severity": "medium",
                "path": rel,
                "message": "Setup script mutates environment without clear diagnostic/no-op framing.",
                "remediation": "Prefer safe diagnostics by default; require explicit user intent for install/write operations.",
            }
        )

    return findings


def branch_cleanup_report(files: List[Path], repo_root: Path) -> Dict:
    candidates = [path for path in files if BRANCH_CLEANUP_PATTERN.search(path.name)]

    canonical = None
    for path in candidates:
        if path.name == "branch_manager.py":
            canonical = path
            break

    if canonical is None and candidates:
        canonical = max(candidates, key=lambda p: p.stat().st_size)

    wrappers: List[str] = []
    duplicates: List[str] = []

    for path in candidates:
        if canonical and path == canonical:
            continue
        text = read_text(path)
        is_wrapper = (
            "delegating to" in text.lower()
            or "compatibility wrapper" in text.lower()
            or "exec python3" in text.lower() and "branch_manager.py" in text
            or "from automated_branch_cleanup import" in text
            or "from branch_manager import" in text
        )
        rel = str(path.relative_to(repo_root))
        if is_wrapper:
            wrappers.append(rel)
        else:
            duplicates.append(rel)

    findings: List[Dict[str, str]] = []
    if len(candidates) > 1 and canonical is None:
        findings.append(
            {
                "kind": "branch_cleanup_no_canonical",
                "severity": "high",
                "path": "scripts/",
                "message": "Duplicate branch-cleanup family exists with no clear canonical entrypoint.",
                "remediation": "Select a canonical branch manager script and convert alternates into wrappers.",
            }
        )
    if duplicates:
        findings.append(
            {
                "kind": "branch_cleanup_duplicate_implementations",
                "severity": "medium",
                "path": "scripts/",
                "message": "Multiple branch-cleanup implementations appear to be non-wrapper duplicates.",
                "remediation": "Keep one canonical implementation and reduce others to thin compatibility wrappers.",
            }
        )

    return {
        "canonical_entrypoint": str(canonical.relative_to(repo_root)) if canonical else None,
        "family_files": [str(path.relative_to(repo_root)) for path in candidates],
        "wrapper_files": sorted(wrappers),
        "duplicate_files": sorted(duplicates),
        "findings": findings,
    }


def hazard_findings(path: Path, root: Path, text: str, max_per_file: int) -> List[Dict[str, str]]:
    rel = str(path.relative_to(root))
    findings: List[Dict[str, str]] = []

    for pattern_info in HAZARD_PATTERNS:
        hits = 0
        for match in pattern_info["pattern"].finditer(text):
            hit_line = line_number(text, match.start())
            findings.append(
                {
                    "kind": str(pattern_info["kind"]),
                    "severity": str(pattern_info["severity"]),
                    "path": rel,
                    "line": hit_line,
                    "message": str(pattern_info["message"]),
                    "snippet": short_line(text, hit_line),
                    "remediation": hazard_remediation(str(pattern_info["kind"])),
                }
            )
            hits += 1
            if hits >= max_per_file:
                break

    return findings


def hazard_remediation(kind: str) -> str:
    mapping = {
        "brace_literal_print": "Use f-strings or .format() where interpolation is intended.",
        "malformed_git_subcommand": "Replace with a valid git command and add command-level tests where possible.",
        "subprocess_shell_true": "Prefer shell=False with argument arrays to avoid quoting/injection hazards.",
        "curl_pipe_shell": "Download artifacts, validate checksums/signatures, then execute explicitly.",
        "broad_rm_rf": "Scope delete targets to explicit repository subpaths and add guard checks.",
    }
    return mapping.get(kind, "Review and patch the pattern with safer command handling.")


def normalized_script_severity(level: str) -> str:
    return NATIVE_TO_GOVERNANCE_SEVERITY.get(str(level).lower(), "INFO")


def governance_outcome(severity_counts: Counter[str]) -> tuple[str, str]:
    if severity_counts.get("BLOCK", 0) > 0:
        return ("BLOCK", "NOT_READY")
    if severity_counts.get("WARN", 0) > 0:
        return ("REVIEW", "CONDITIONAL")
    return ("PASS", "READY")


def standardize_finding(row: Dict[str, object]) -> Dict[str, object]:
    native_severity = str(row.get("severity", "low")).lower()
    path = str(row.get("path", "<unknown>"))
    line = row.get("line")
    source_path = f"{path}:{line}" if line else path
    message = str(row.get("message", "No message provided."))
    remediation = str(row.get("remediation", ""))
    evidence = str(row.get("snippet") or source_path)
    kind = str(row.get("kind", "unknown"))

    standardized = dict(row)
    standardized.update(
        {
            "domain": "script_governor",
            "severity": normalized_script_severity(native_severity),
            "native_severity": native_severity,
            "rule_id": f"SG_{kind.upper()}",
            "file": source_path,
            "source_path": source_path,
            "message": message,
            "rationale": message,
            "evidence": evidence,
            "remediation": remediation,
            "suggested_fix": remediation,
            "blocking_scope": "authoritative",
            "source_tool": "script-governance-scan",
        }
    )
    return standardized


def build_report(repo_root: Path, exclude_disabled: bool, max_hazards_per_file: int) -> Dict:
    files = find_script_files(repo_root, exclude_disabled=exclude_disabled)

    setup_raw: List[Dict[str, str]] = []
    hazards_raw: List[Dict[str, str]] = []

    for path in files:
        text = read_text(path)
        size = path.stat().st_size
        setup_raw.extend(setup_findings(path, repo_root, text, size))
        hazards_raw.extend(hazard_findings(path, repo_root, text, max_hazards_per_file))

    branch = branch_cleanup_report(files, repo_root)
    branch_raw_findings = list(branch["findings"])

    setup = [standardize_finding(row) for row in setup_raw]
    branch["findings"] = [standardize_finding(row) for row in branch_raw_findings]
    hazards = [standardize_finding(row) for row in hazards_raw]

    all_findings = setup + branch["findings"] + hazards
    all_findings.sort(key=lambda row: (row["severity"], str(row.get("source_path", "")), str(row.get("rule_id", ""))))
    severity_counts = Counter(finding["severity"] for finding in all_findings)
    native_severity_counts = Counter(str(finding.get("native_severity", "low")) for finding in all_findings)
    kind_counts = Counter(str(finding.get("kind", "unknown")) for finding in all_findings)
    verdict, promotion_readiness = governance_outcome(severity_counts)

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "domain": "script_governor",
        "verdict": verdict,
        "promotion_readiness": promotion_readiness,
        "repo_root": str(repo_root),
        "scripts_dir": str(repo_root / "scripts"),
        "summary": {
            "scanned_script_files": len(files),
            "total_findings": len(all_findings),
            "by_severity": {
                "BLOCK": severity_counts.get("BLOCK", 0),
                "WARN": severity_counts.get("WARN", 0),
                "INFO": severity_counts.get("INFO", 0),
            },
            "native_severity_counts": dict(sorted(native_severity_counts.items())),
            "finding_kind_counts": dict(sorted(kind_counts.items())),
        },
        "setup_governance": {
            "findings": setup,
        },
        "branch_cleanup_governance": branch,
        "hazard_triage": {
            "findings": hazards,
        },
        "findings": all_findings,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan Aurora script surfaces for governance risks.")
    parser.add_argument("--repo", default=".", help="Repository root path")
    parser.add_argument("--out", help="Optional output file path for JSON report")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    parser.add_argument("--exclude-disabled", action="store_true", help="Skip *.disabled scripts")
    parser.add_argument(
        "--max-hazards-per-file",
        type=int,
        default=10,
        help="Limit hazard findings per pattern per file",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo).resolve()
    report = build_report(
        repo_root=repo_root,
        exclude_disabled=args.exclude_disabled,
        max_hazards_per_file=max(1, args.max_hazards_per_file),
    )

    indent = 2 if args.pretty else None
    payload = json.dumps(report, indent=indent, sort_keys=bool(indent))

    if args.out:
        out_path = Path(args.out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload + "\n", encoding="utf-8")

    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

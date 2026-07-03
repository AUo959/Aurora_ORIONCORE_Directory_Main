#!/usr/bin/env python3
"""Unified Aurora governance orchestration CLI."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ORCHESTRATOR_VERSION = "1.1.0"
REPO_MARKER = "/Aurora_ORIONCORE_Directory_Main/"

SKILLS_ROOT = Path("/Users/travisstreets/.codex/skills")

THREADCORE_SCAN_SCRIPT = SKILLS_ROOT / "threadcore-governor" / "scripts" / "threadcore_governance_scan.py"
THREADCORE_RULES_SCRIPT = SKILLS_ROOT / "threadcore-governor" / "scripts" / "threadcore_rules.py"

ZIPWIZ_SCAN_SCRIPT = SKILLS_ROOT / "zipwiz-governor" / "scripts" / "zipwiz_governance_scan.py"
ZIPWIZ_RULES_SCRIPT = SKILLS_ROOT / "zipwiz-governor" / "scripts" / "zipwiz_rules.py"

SCRIPT_GOVERNOR_SCAN_SCRIPT = SKILLS_ROOT / "aurora-script-governor" / "scripts" / "script_governance_scan.py"
REPO_STABILIZER_SCAN_SCRIPT = SKILLS_ROOT / "aurora-repo-stabilizer" / "scripts" / "repo_stabilizer_scan.py"
NARRATIVE_TONE_SCAN_SCRIPT = SKILLS_ROOT / "aurora-narrative-tone-governor" / "scripts" / "narrative_tone_scan.py"

CANON_VALIDATE_SCRIPT = SKILLS_ROOT / "aurora-canon-reconciler" / "scripts" / "validate_entity.py"

# Repo-relative fallbacks; resolve_roots() rebases them against --repo.
THREADCORE_DEFAULT_ROOTS_FALLBACK = [
    "GUMAS_SIM_2.5",
    "projects/Aurora_Project_Cloudhub_Deploy",
    "projects/GUI_Cloudhub",
    "Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main",
]

ZIPWIZ_DEFAULT_CANONICAL_ROOTS_FALLBACK = [
    "projects/GUMAS_SIM_2.0/05_BUILD_TOOLS/ZipWiz_Packaging",
    "GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main",
    "GUMAS_SIM_2.5/SIM_HARVEST_26",
]

ZIPWIZ_DEFAULT_REFERENCE_ROOTS_FALLBACK = [
    "archives/unzipped/ZipWiz_Chamber_6_28/ZIPWIZ_Documents",
    "reports/analysis/non_can_reports/ZIPWIZ_CHAMBER_TECHNICAL_REFERENCE.md",
]

NARRATIVE_TONE_DEFAULT_ROOTS_FALLBACK = [
    "projects/GUMAS_SIM_2.0/02_DEVELOPMENT/Project_Main/Project_Files_GUMAS2_0",
    "projects/GUMAS_SIM_2.0/03_SIMULATION/Location_Data/Sim_Locations",
    "GUMAS_SIM_2.5/FORGE__GUMAS_v3.0__2026-02-19",
    "GUMAS_SIM_2.5/PROJECT_KNOWLEDGE",
]

DOMAIN_ORDER = ["threadcore", "zipwiz", "script_governor", "narrative_tone", "repo_stabilizer", "canon"]
AUTHORITATIVE_DOMAINS = {"threadcore", "zipwiz", "script_governor", "narrative_tone", "canon"}
SEVERITY_ORDER = {"BLOCK": 0, "WARN": 1, "INFO": 2}

SCRIPT_GOVERNOR_SEVERITY_MAP = {
    "high": "BLOCK",
    "medium": "WARN",
    "low": "INFO",
}


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def unique_preserve(values: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def parse_csv(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [piece.strip() for piece in raw.split(",") if piece.strip()]


def parse_changed_paths(raw: str | None) -> list[str]:
    return parse_csv(raw)


def load_module_list_attribute(module_path: Path, attribute: str, fallback: list[str]) -> list[str]:
    if not module_path.exists():
        return list(fallback)

    module_name = f"orchestrator_{module_path.stem}_{attribute}"
    try:
        spec = importlib.util.spec_from_file_location(module_name, str(module_path))
        if spec is None or spec.loader is None:
            return list(fallback)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        value = getattr(module, attribute, fallback)
        if isinstance(value, (list, tuple)):
            return [str(item) for item in value]
    except Exception:
        return list(fallback)

    return list(fallback)


def default_threadcore_roots() -> list[str]:
    return load_module_list_attribute(
        THREADCORE_RULES_SCRIPT,
        "DEFAULT_CANONICAL_ROOTS",
        THREADCORE_DEFAULT_ROOTS_FALLBACK,
    )


def default_zipwiz_canonical_roots() -> list[str]:
    return load_module_list_attribute(
        ZIPWIZ_RULES_SCRIPT,
        "DEFAULT_CANONICAL_ROOTS",
        ZIPWIZ_DEFAULT_CANONICAL_ROOTS_FALLBACK,
    )


def default_zipwiz_reference_roots() -> list[str]:
    return load_module_list_attribute(
        ZIPWIZ_RULES_SCRIPT,
        "DEFAULT_REFERENCE_ROOTS",
        ZIPWIZ_DEFAULT_REFERENCE_ROOTS_FALLBACK,
    )


def default_narrative_tone_roots() -> list[str]:
    return load_module_list_attribute(
        NARRATIVE_TONE_SCAN_SCRIPT,
        "DEFAULT_CANONICAL_ROOTS",
        NARRATIVE_TONE_DEFAULT_ROOTS_FALLBACK,
    )


def rebase_candidate_root(raw_root: str, repo_root: Path) -> tuple[str, bool, bool, str]:
    text = raw_root.strip()
    parsed = Path(text).expanduser()

    if parsed.is_absolute() and parsed.exists():
        return str(parsed.resolve()), False, True, "as_configured"

    if not parsed.is_absolute():
        candidate = (repo_root / parsed).resolve()
        if candidate.exists():
            return str(candidate), False, True, "repo_relative"

    if REPO_MARKER in text:
        suffix = text.split(REPO_MARKER, 1)[1].lstrip("/")
        candidate = (repo_root / suffix).resolve()
        if candidate.exists():
            return str(candidate), True, True, "rebased_from_repo_marker"
        return str(candidate), True, False, "rebased_missing"

    if parsed.is_absolute():
        candidate = parsed.resolve()
    else:
        candidate = (repo_root / parsed).resolve()
    return str(candidate), False, False, "missing"


def resolve_roots(raw_roots: list[str], repo_root: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for raw_root in raw_roots:
        candidate_root, rebased, exists, reason = rebase_candidate_root(raw_root, repo_root)
        entries.append(
            {
                "configured_root": raw_root,
                "candidate_root": candidate_root,
                "exists": exists,
                "rebased": rebased,
                "resolution_reason": reason,
            }
        )
    return entries


def existing_roots(entries: list[dict[str, Any]]) -> list[str]:
    return [entry["candidate_root"] for entry in entries if entry.get("exists")]


def csv_for_entries(entries: list[dict[str, Any]]) -> str:
    roots = unique_preserve([entry["candidate_root"] for entry in entries])
    return ",".join(roots)


def make_finding(
    *,
    domain: str,
    severity: str,
    rule_id: str,
    file: str,
    message: str,
    suggested_fix: str,
    family: str | None,
    source_tool: str,
    blocking_scope: str,
    raw_ref: dict[str, Any],
    evidence: str | None = None,
) -> dict[str, Any]:
    evidence_text = (evidence or "").strip()
    if not evidence_text:
        source_hint = str(file or raw_ref.get("source_path") or "").strip()
        if source_hint:
            evidence_text = f"See {source_hint}"
        else:
            evidence_text = message

    return {
        "id": rule_id,
        "domain": domain,
        "severity": severity,
        "rule_id": rule_id,
        "file": file,
        "source_path": file,
        "message": message,
        "rationale": message,
        "suggested_fix": suggested_fix,
        "remediation": suggested_fix,
        "family": family,
        "evidence": evidence_text,
        "source_tool": source_tool,
        "scope": blocking_scope,
        "blocking_scope": blocking_scope,
        "raw_ref": raw_ref,
    }


def make_execution_failure_finding(domain: str, message: str, raw_ref: dict[str, Any]) -> dict[str, Any]:
    blocking = domain in AUTHORITATIVE_DOMAINS
    severity = "BLOCK" if blocking else "WARN"
    rule_id = "B_SCAN_EXECUTION_FAILED" if blocking else "W_SCAN_EXECUTION_FAILED"
    return make_finding(
        domain="orchestrator",
        severity=severity,
        rule_id=rule_id,
        file=f"<{domain}>",
        message=message,
        suggested_fix="Verify scanner script paths, inputs, and permissions, then rerun the orchestrator.",
        family=None,
        source_tool="aurora-governance-orchestrator",
        blocking_scope="execution_health",
        raw_ref=raw_ref,
    )


def make_unresolved_roots_finding(domain: str, entries: list[dict[str, Any]]) -> dict[str, Any]:
    configured = [entry["configured_root"] for entry in entries]
    return make_finding(
        domain="orchestrator",
        severity="BLOCK",
        rule_id="B_SCAN_ROOTS_UNRESOLVED",
        file=f"<{domain}_roots>",
        message=(
            f"All configured {domain} roots are unresolved for this repo root; authoritative scan cannot run. "
            f"Configured roots: {configured}"
        ),
        suggested_fix="Provide valid roots or run from the correct Aurora repository root.",
        family=None,
        source_tool="aurora-governance-orchestrator",
        blocking_scope="execution_health",
        raw_ref={"domain": domain, "entries": entries},
    )


def make_zero_artifact_warning(domain: str) -> dict[str, Any]:
    return make_finding(
        domain="orchestrator",
        severity="WARN",
        rule_id="W_ZERO_ARTIFACT_SCAN",
        file=f"<{domain}>",
        message=f"{domain} scan completed but found zero artifacts; verify scan roots and scope.",
        suggested_fix="Inspect root resolution diagnostics and confirm targeted artifacts exist.",
        family=None,
        source_tool="aurora-governance-orchestrator",
        blocking_scope="execution_health",
        raw_ref={"domain": domain},
    )


def make_reference_roots_warning(entries: list[dict[str, Any]]) -> dict[str, Any]:
    return make_finding(
        domain="orchestrator",
        severity="WARN",
        rule_id="W_REFERENCE_ROOTS_UNRESOLVED",
        file="<zipwiz_reference_roots>",
        message="All ZIPWIZ reference-only roots are unresolved; evolution evidence coverage is reduced.",
        suggested_fix="Update ZIPWIZ reference roots to existing paths under the active repo root.",
        family="evolution_evidence",
        source_tool="aurora-governance-orchestrator",
        blocking_scope="reference_only",
        raw_ref={"entries": entries},
    )


def run_subprocess(command: list[str]) -> dict[str, Any]:
    try:
        proc = subprocess.run(command, capture_output=True, text=True)
    except OSError as exc:
        return {
            "ok": False,
            "exit_code": None,
            "stdout": "",
            "stderr": str(exc),
            "error": str(exc),
        }

    return {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "error": None,
    }


def load_json_file(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def parse_json_text(raw: str) -> dict[str, Any] | None:
    if not raw.strip():
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def normalize_threadcore_findings(report: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for idx, row in enumerate(report.get("findings") or []):
        severity = str(row.get("severity", "INFO")).upper()
        if severity not in SEVERITY_ORDER:
            severity = "INFO"
        findings.append(
            make_finding(
                domain="threadcore",
                severity=severity,
                rule_id=str(row.get("rule_id", "THREADCORE_UNKNOWN")),
                file=str(row.get("source_path") or row.get("file", "<unknown>")),
                message=str(row.get("rationale") or row.get("message", "No message provided.")),
                suggested_fix=str(row.get("remediation") or row.get("suggested_fix", "")),
                family=row.get("family"),
                evidence=str(row.get("evidence", "")),
                source_tool="threadcore-governance-scan",
                blocking_scope="authoritative",
                raw_ref={"domain": "threadcore", "finding_index": idx},
            )
        )
    return findings


def normalize_zipwiz_findings(report: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for idx, row in enumerate(report.get("findings") or []):
        severity = str(row.get("severity", "INFO")).upper()
        if severity not in SEVERITY_ORDER:
            severity = "INFO"

        family = row.get("family")
        blocking_scope = "reference_only" if family == "evolution_evidence" else "authoritative"
        if severity == "BLOCK" and blocking_scope == "reference_only":
            severity = "WARN"

        findings.append(
            make_finding(
                domain="zipwiz",
                severity=severity,
                rule_id=str(row.get("rule_id", "ZIPWIZ_UNKNOWN")),
                file=str(row.get("source_path") or row.get("file", "<unknown>")),
                message=str(row.get("rationale") or row.get("message", "No message provided.")),
                suggested_fix=str(row.get("remediation") or row.get("suggested_fix", "")),
                family=family,
                evidence=str(row.get("evidence", "")),
                source_tool="zipwiz-governance-scan",
                blocking_scope=str(row.get("blocking_scope", blocking_scope)),
                raw_ref={"domain": "zipwiz", "finding_index": idx},
            )
        )
    return findings


def normalize_script_governor_findings(report: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for idx, row in enumerate(report.get("findings") or []):
        raw_severity = str(row.get("severity", "low"))
        severity = raw_severity if raw_severity in SEVERITY_ORDER else SCRIPT_GOVERNOR_SEVERITY_MAP.get(raw_severity.lower(), "INFO")

        file_path = str(row.get("source_path") or row.get("file") or row.get("path", "<unknown>"))

        findings.append(
            make_finding(
                domain="script_governor",
                severity=severity,
                rule_id=str(row.get("rule_id") or f"SG_{str(row.get('kind', 'UNKNOWN')).upper()}"),
                file=file_path,
                message=str(row.get("rationale") or row.get("message", "No message provided.")),
                suggested_fix=str(row.get("remediation") or row.get("suggested_fix", "")),
                family="script_governance",
                evidence=str(row.get("evidence") or row.get("snippet", "")),
                source_tool="script-governance-scan",
                blocking_scope=str(row.get("blocking_scope", "authoritative")),
                raw_ref={"domain": "script_governor", "finding_index": idx},
            )
        )

    scanned_count = int((report.get("summary") or {}).get("scanned_script_files", 0))
    if scanned_count == 0:
        findings.append(
            make_finding(
                domain="script_governor",
                severity="INFO",
                rule_id="I_SCRIPT_SURFACE_EMPTY",
                file="scripts/",
                message="No script files were discovered under scripts/.",
                suggested_fix="No action required unless script surface is expected in this repo.",
                family="script_governance",
                source_tool="script-governance-scan",
                blocking_scope="advisory",
                raw_ref={"domain": "script_governor", "summary": "scanned_script_files=0"},
            )
        )

    return findings


def normalize_repo_stabilizer_findings(report: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    for path in report.get("zero_byte_scripts") or []:
        findings.append(
            make_finding(
                domain="repo_stabilizer",
                severity="WARN",
                rule_id="RS_ZERO_BYTE_SCRIPT",
                file=str(path),
                message="Zero-byte script detected.",
                suggested_fix="Replace with an explicit diagnostic no-op or a real implementation.",
                family="script_surface",
                source_tool="repo-stabilizer-scan",
                blocking_scope="advisory",
                raw_ref={"domain": "repo_stabilizer", "zero_byte_script": path},
            )
        )

    for idx, row in enumerate(report.get("top_risky_scripts") or []):
        findings.append(
            make_finding(
                domain="repo_stabilizer",
                severity="WARN",
                rule_id="RS_RISKY_SCRIPT_SURFACE",
                file=str(row.get("path", "<unknown>")),
                message="Script flagged as risky by stabilization scanner.",
                suggested_fix="Review placeholder/hazard markers and reduce risk before promotion.",
                family="script_surface",
                source_tool="repo-stabilizer-scan",
                blocking_scope="advisory",
                raw_ref={"domain": "repo_stabilizer", "risky_index": idx},
            )
        )

    for idx, row in enumerate(report.get("duplicate_families") or []):
        paths = row.get("paths") or []
        findings.append(
            make_finding(
                domain="repo_stabilizer",
                severity="INFO",
                rule_id="RS_DUPLICATE_SCRIPT_FAMILY",
                file=str(paths[0]) if paths else "scripts/",
                message=f"Potential duplicate script family: {row.get('normalized_stem', 'unknown')}.",
                suggested_fix="Consolidate into one canonical entrypoint with compatibility wrappers.",
                family="script_surface",
                source_tool="repo-stabilizer-scan",
                blocking_scope="advisory",
                raw_ref={"domain": "repo_stabilizer", "duplicate_index": idx},
            )
        )

    total_scripts = int((report.get("summary") or {}).get("total_script_files", 0))
    if total_scripts == 0:
        findings.append(
            make_finding(
                domain="repo_stabilizer",
                severity="INFO",
                rule_id="I_REPO_SCRIPT_SURFACE_EMPTY",
                file="scripts/",
                message="Repo stabilizer found no script files in scripts/.",
                suggested_fix="No action required unless scripts are expected.",
                family="script_surface",
                source_tool="repo-stabilizer-scan",
                blocking_scope="advisory",
                raw_ref={"domain": "repo_stabilizer", "summary": "total_script_files=0"},
            )
        )

    return findings


def normalize_canon_findings(report: dict[str, Any], draft_input: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for report_idx, entity_report in enumerate(report.get("reports") or []):
        entity_name = str(entity_report.get("entity_name", "<entity>"))
        for finding_idx, row in enumerate(entity_report.get("findings") or []):
            severity = str(row.get("severity", "INFO")).upper()
            if severity not in SEVERITY_ORDER:
                severity = "INFO"

            field = row.get("field")
            message = str(row.get("message", "No message provided."))
            if field:
                message = f"{message} (field: {field})"

            findings.append(
                make_finding(
                domain="canon",
                severity=severity,
                rule_id=str(row.get("code", "CANON_UNKNOWN")),
                file=str(draft_input),
                message=f"{entity_name}: {message}",
                suggested_fix="Resolve canonical validation findings and rerun canon checks.",
                family=str(entity_report.get("entity_type", "entity")),
                evidence=str(field or ""),
                    source_tool="canon-validate-entity",
                    blocking_scope="authoritative",
                    raw_ref={
                        "domain": "canon",
                        "report_index": report_idx,
                        "finding_index": finding_idx,
                    },
                )
            )
    return findings


def normalize_narrative_tone_findings(report: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for idx, row in enumerate(report.get("findings") or []):
        severity = str(row.get("severity", "INFO")).upper()
        if severity not in SEVERITY_ORDER:
            severity = "INFO"

        findings.append(
            make_finding(
                domain="narrative_tone",
                severity=severity,
                rule_id=str(row.get("rule_id", "NARRATIVE_TONE_UNKNOWN")),
                file=str(row.get("source_path") or row.get("file", "<unknown>")),
                message=str(row.get("rationale") or row.get("message", "No message provided.")),
                suggested_fix=str(row.get("remediation") or row.get("suggested_fix", "")),
                family=str(row.get("family", "narrative_governance")),
                evidence=str(row.get("evidence", "")),
                source_tool="narrative-tone-scan",
                blocking_scope=str(row.get("blocking_scope", "authoritative")),
                raw_ref={"domain": "narrative_tone", "finding_index": idx},
            )
        )
    return findings


def should_block_finding(finding: dict[str, Any]) -> bool:
    if finding.get("severity") != "BLOCK":
        return False

    if finding.get("blocking_scope") == "execution_health":
        return True

    domain = finding.get("domain")
    if domain == "zipwiz" and finding.get("blocking_scope") == "reference_only":
        return False

    if domain in {"threadcore", "canon", "script_governor", "narrative_tone", "zipwiz"}:
        return True

    return False


def build_remediation_queue(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queue_candidates = [f for f in findings if f.get("severity") in {"BLOCK", "WARN"} and f.get("suggested_fix")]
    queue_candidates.sort(key=lambda row: (SEVERITY_ORDER.get(str(row.get("severity")), 99), str(row.get("domain")), str(row.get("rule_id"))))

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in queue_candidates:
        key = (
            str(item.get("rule_id", "")),
            str(item.get("file", "")),
            str(item.get("message", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(
            {
                "severity": item.get("severity"),
                "domain": item.get("domain"),
                "rule_id": item.get("rule_id"),
                "file": item.get("file"),
                "source_path": item.get("source_path") or item.get("file"),
                "message": item.get("message"),
                "rationale": item.get("rationale") or item.get("message"),
                "evidence": item.get("evidence"),
                "remediation": item.get("remediation") or item.get("suggested_fix"),
                "suggested_fix": item.get("suggested_fix"),
            }
        )
    return deduped


def build_summary(findings: list[dict[str, Any]], selected_domains: list[str]) -> dict[str, Any]:
    severity_counts = Counter(str(item.get("severity", "INFO")) for item in findings)
    domain_counts = Counter(str(item.get("domain", "unknown")) for item in findings)

    by_severity = {
        "BLOCK": severity_counts.get("BLOCK", 0),
        "WARN": severity_counts.get("WARN", 0),
        "INFO": severity_counts.get("INFO", 0),
    }

    return {
        "selected_domains": selected_domains,
        "total_findings": len(findings),
        "by_severity": by_severity,
        "by_domain": dict(sorted(domain_counts.items())),
    }


def compute_confidence(
    *,
    selected_domains: list[str],
    domain_reports: dict[str, dict[str, Any]],
    root_resolution: dict[str, Any],
    findings: list[dict[str, Any]],
) -> str:
    if any(
        finding.get("rule_id") in {"B_SCAN_EXECUTION_FAILED", "B_SCAN_ROOTS_UNRESOLVED"}
        and finding.get("severity") == "BLOCK"
        for finding in findings
    ):
        return "low"

    for domain in selected_domains:
        report = domain_reports.get(domain, {})
        if domain in AUTHORITATIVE_DOMAINS and report.get("status") == "failed":
            return "low"

    rebased_any = False
    threadcore_entries = root_resolution.get("threadcore") or []
    if any(bool(row.get("rebased")) for row in threadcore_entries):
        rebased_any = True

    zipwiz = root_resolution.get("zipwiz") or {}
    zipwiz_canonical = zipwiz.get("canonical") or []
    zipwiz_reference = zipwiz.get("reference") or []
    if any(bool(row.get("rebased")) for row in zipwiz_canonical + zipwiz_reference):
        rebased_any = True

    narrative_entries = root_resolution.get("narrative_tone") or []
    if any(bool(row.get("rebased")) for row in narrative_entries):
        rebased_any = True

    zero_artifact_warn = any(f.get("rule_id") == "W_ZERO_ARTIFACT_SCAN" for f in findings)
    if rebased_any or zero_artifact_warn:
        return "medium"

    return "high"


def build_verdict(
    findings: list[dict[str, Any]],
    selected_domains: list[str],
    domain_reports: dict[str, dict[str, Any]],
    root_resolution: dict[str, Any],
) -> dict[str, Any]:
    blocking = [item for item in findings if should_block_finding(item)]
    warning_count = sum(1 for item in findings if item.get("severity") == "WARN")

    if blocking:
        status = "BLOCKED"
        reason = f"{len(blocking)} blocking finding(s) detected in authoritative or execution-health scope."
    elif warning_count > 0:
        status = "PROMOTE_WITH_REMEDIATION"
        reason = f"No blocking findings. {warning_count} warning(s) require remediation follow-up."
    else:
        status = "PROMOTE"
        reason = "No blocking findings or warnings detected."

    confidence = compute_confidence(
        selected_domains=selected_domains,
        domain_reports=domain_reports,
        root_resolution=root_resolution,
        findings=findings,
    )

    blocking_findings = [
        {
            "domain": item.get("domain"),
            "rule_id": item.get("rule_id"),
            "file": item.get("file"),
            "source_path": item.get("source_path") or item.get("file"),
            "message": item.get("message"),
            "rationale": item.get("rationale") or item.get("message"),
            "evidence": item.get("evidence"),
            "remediation": item.get("remediation") or item.get("suggested_fix"),
            "blocking_scope": item.get("blocking_scope"),
        }
        for item in blocking
    ]

    return {
        "status": status,
        "promotion_readiness": (
            "NOT_READY" if status == "BLOCKED" else "CONDITIONAL" if status == "PROMOTE_WITH_REMEDIATION" else "READY"
        ),
        "reason": reason,
        "blocking_findings": blocking_findings,
        "confidence": confidence,
    }


def format_finding_line(finding: dict[str, Any]) -> str:
    return (
        f"- [{finding.get('severity')}] [{finding.get('rule_id')}] "
        f"`{finding.get('file')}` ({finding.get('domain')}): {finding.get('message')}"
    )


def render_markdown_report(payload: dict[str, Any]) -> str:
    routing = payload.get("routing") or {}
    root_resolution = payload.get("root_resolution") or {}
    domain_reports = payload.get("domain_reports") or {}
    findings = payload.get("findings") or []
    verdict = payload.get("verdict") or {}
    remediation_queue = (payload.get("summary") or {}).get("remediation_queue") or []

    blocking = [f for f in findings if should_block_finding(f)]
    warnings = [f for f in findings if f.get("severity") == "WARN"]

    lines: list[str] = []
    lines.append("# Aurora Governance Orchestrator Report")
    lines.append("")

    lines.append("## 1) Scope and Routing Decisions")
    lines.append(f"- Repo: `{payload.get('scan_meta', {}).get('repo_root', '<unknown>')}`")
    lines.append(f"- Mode requested: `{routing.get('mode_requested', '<unknown>')}`")
    lines.append(f"- Mode effective: `{routing.get('mode_effective', '<unknown>')}`")
    lines.append(f"- Fallback to full mode: `{routing.get('fallback_to_full', False)}`")
    lines.append(f"- Selected domains: `{', '.join(routing.get('selected_domains', [])) or '<none>'}`")
    if routing.get("changed_paths"):
        lines.append(f"- Changed paths: `{', '.join(routing.get('changed_paths'))}`")
    for note in routing.get("notes") or []:
        lines.append(f"- Note: {note}")
    lines.append("")

    lines.append("## 2) Root Resolution Diagnostics")
    threadcore_entries = root_resolution.get("threadcore") or []
    if threadcore_entries:
        lines.append("- Threadcore roots:")
        for row in threadcore_entries:
            lines.append(
                f"  - configured=`{row.get('configured_root')}` | candidate=`{row.get('candidate_root')}` | "
                f"exists={row.get('exists')} | rebased={row.get('rebased')}"
            )
    else:
        lines.append("- Threadcore roots: not evaluated")

    zipwiz = root_resolution.get("zipwiz") or {}
    zipwiz_canonical = zipwiz.get("canonical") or []
    zipwiz_reference = zipwiz.get("reference") or []
    if zipwiz_canonical:
        lines.append("- ZipWiz canonical roots:")
        for row in zipwiz_canonical:
            lines.append(
                f"  - configured=`{row.get('configured_root')}` | candidate=`{row.get('candidate_root')}` | "
                f"exists={row.get('exists')} | rebased={row.get('rebased')}"
            )
    else:
        lines.append("- ZipWiz canonical roots: not evaluated")

    if zipwiz_reference:
        lines.append("- ZipWiz reference roots:")
        for row in zipwiz_reference:
            lines.append(
                f"  - configured=`{row.get('configured_root')}` | candidate=`{row.get('candidate_root')}` | "
                f"exists={row.get('exists')} | rebased={row.get('rebased')}"
            )
    else:
        lines.append("- ZipWiz reference roots: not evaluated")

    narrative_entries = root_resolution.get("narrative_tone") or []
    if narrative_entries:
        lines.append("- Narrative/tone roots:")
        for row in narrative_entries:
            lines.append(
                f"  - configured=`{row.get('configured_root')}` | candidate=`{row.get('candidate_root')}` | "
                f"exists={row.get('exists')} | rebased={row.get('rebased')}"
            )
    else:
        lines.append("- Narrative/tone roots: not evaluated")
    lines.append("")

    lines.append("## 3) Domain Execution Summary")
    for domain in DOMAIN_ORDER:
        row = domain_reports.get(domain) or {}
        status = row.get("status", "not_selected")
        summary = row.get("summary") or {}
        lines.append(f"- `{domain}`: status=`{status}` summary=`{json.dumps(summary, ensure_ascii=False)}`")
    lines.append("")

    lines.append("## 4) Blocking Findings")
    if blocking:
        for row in blocking:
            lines.append(format_finding_line(row))
            if row.get("evidence"):
                lines.append(f"  Evidence: {row.get('evidence')}")
            if row.get("remediation") or row.get("suggested_fix"):
                lines.append(f"  Remediation: {row.get('remediation') or row.get('suggested_fix')}")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## 5) Warnings")
    if warnings:
        for row in warnings:
            lines.append(format_finding_line(row))
            if row.get("evidence"):
                lines.append(f"  Evidence: {row.get('evidence')}")
            if row.get("remediation") or row.get("suggested_fix"):
                lines.append(f"  Remediation: {row.get('remediation') or row.get('suggested_fix')}")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("## 6) Consolidated Remediation Queue")
    if remediation_queue:
        for idx, row in enumerate(remediation_queue, start=1):
            lines.append(
                f"{idx}. [{row.get('severity')}] {row.get('rule_id')} @ `{row.get('source_path') or row.get('file')}` ({row.get('domain')}): "
                f"{row.get('remediation') or row.get('suggested_fix')}"
            )
    else:
        lines.append("1. No remediation actions required.")
    lines.append("")

    lines.append("## 7) Final Verdict")
    lines.append(f"- Status: `{verdict.get('status', '<unknown>')}`")
    lines.append(f"- Confidence: `{verdict.get('confidence', '<unknown>')}`")
    lines.append(f"- Reason: {verdict.get('reason', '<no reason>')}")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def domain_enabled_map(args: argparse.Namespace) -> dict[str, bool]:
    return {
        "threadcore": not args.no_threadcore,
        "zipwiz": not args.no_zipwiz,
        "script_governor": not args.no_script_governor,
        "narrative_tone": not args.no_narrative_tone,
        "repo_stabilizer": not args.no_repo_stabilizer,
        "canon": not args.no_canon,
    }


def classify_changed_path(path: str) -> set[str]:
    lowered = path.lower().replace("\\", "/")
    domains: set[str] = set()

    if any(token in lowered for token in ["threadcore", "checkpoint", "continuity", "beacon", "delta"]):
        domains.add("threadcore")

    if any(token in lowered for token in ["zipwiz", "zipwizard", "bundle.manifest", "staging_manifest", "zipcomm"]):
        domains.add("zipwiz")

    if any(
        token in lowered
        for token in [
            "narr",
            "story",
            "scene",
            "recap",
            "thread",
            "modelog",
            "moderecap",
            "tone",
            "cadence",
            "anti-flourish",
        ]
    ):
        domains.add("narrative_tone")

    if (
        lowered.startswith("scripts/")
        or "/scripts/" in lowered
        or ".github/workflows" in lowered
        or lowered.endswith("pre-commit")
        or lowered.endswith("pre-push")
        or "hooks" in lowered
        or lowered.endswith(".sh")
    ):
        domains.add("script_governor")
        domains.add("repo_stabilizer")

    if any(token in lowered for token in ["canon", "entity", "entities", "worldbuilding", "l1", "l2", "l3"]):
        domains.add("canon")

    return domains


def select_domains(args: argparse.Namespace) -> dict[str, Any]:
    enabled = domain_enabled_map(args)
    changed_paths = parse_changed_paths(args.changed_paths)

    selected: set[str] = set()
    reasons: dict[str, list[str]] = {}
    notes: list[str] = []
    fallback_to_full = False
    mode_effective = args.mode

    if args.mode == "full":
        for domain in DOMAIN_ORDER:
            if domain in {"canon", "narrative_tone"}:
                continue
            if enabled.get(domain):
                selected.add(domain)
                reasons.setdefault(domain, []).append("mode_full")
    else:
        for path in changed_paths:
            for domain in classify_changed_path(path):
                if enabled.get(domain):
                    selected.add(domain)
                    reasons.setdefault(domain, []).append(f"changed_path:{path}")

        if not selected:
            fallback_to_full = True
            mode_effective = "full"
            notes.append("changed-path heuristics selected no domains; fell back to full mode")
            for domain in DOMAIN_ORDER:
                if domain in {"canon", "narrative_tone"}:
                    continue
                if enabled.get(domain):
                    selected.add(domain)
                    reasons.setdefault(domain, []).append("fallback_full")

    if args.draft_input and enabled.get("canon"):
        selected.add("canon")
        reasons.setdefault("canon", []).append("explicit_draft_input")
    elif "canon" in selected:
        selected.remove("canon")
        notes.append("canon-related changed paths detected but no --draft-input provided; canon scan skipped")

    selected_domains = [domain for domain in DOMAIN_ORDER if domain in selected and enabled.get(domain)]

    return {
        "mode_requested": args.mode,
        "mode_effective": mode_effective,
        "changed_paths": changed_paths,
        "selected_domains": selected_domains,
        "fallback_to_full": fallback_to_full,
        "selection_reasons": reasons,
        "notes": notes,
    }


def execute_threadcore(
    *,
    repo_root: Path,
    strictness: str,
    temp_dir: Path,
    root_resolution: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    report_info: dict[str, Any] = {
        "status": "failed",
        "summary": {},
        "exit_code": None,
    }
    findings: list[dict[str, Any]] = []

    roots = default_threadcore_roots()
    entries = resolve_roots(roots, repo_root)
    root_resolution["threadcore"] = entries

    if not entries or not existing_roots(entries):
        report_info["status"] = "failed"
        report_info["summary"] = {"reason": "all_roots_unresolved"}
        findings.append(make_unresolved_roots_finding("threadcore", entries))
        return report_info, findings

    out_json = temp_dir / "threadcore_scan.json"
    out_md = temp_dir / "threadcore_scan.md"

    command = [
        sys.executable,
        str(THREADCORE_SCAN_SCRIPT),
        "--repo",
        str(repo_root),
        "--roots",
        csv_for_entries(entries),
        "--strictness",
        strictness,
        "--out-json",
        str(out_json),
        "--out-md",
        str(out_md),
    ]
    report_info["command"] = command

    if not THREADCORE_SCAN_SCRIPT.exists():
        findings.append(
            make_execution_failure_finding(
                "threadcore",
                f"Missing scanner script: {THREADCORE_SCAN_SCRIPT}",
                {"domain": "threadcore", "reason": "missing_script"},
            )
        )
        report_info["summary"] = {"reason": "missing_script"}
        return report_info, findings

    run = run_subprocess(command)
    report_info["exit_code"] = run["exit_code"]

    parsed = load_json_file(out_json)
    if parsed is not None:
        report_info["summary"] = parsed.get("summary") or {}
        findings.extend(normalize_threadcore_findings(parsed))

        if int((parsed.get("summary") or {}).get("total_artifacts", 0)) == 0:
            findings.append(make_zero_artifact_warning("threadcore"))

    if run["error"] is not None or run["exit_code"] not in {0}:
        findings.append(
            make_execution_failure_finding(
                "threadcore",
                run["stderr"] or "threadcore scanner exited unexpectedly",
                {
                    "domain": "threadcore",
                    "exit_code": run["exit_code"],
                    "stderr": run["stderr"],
                },
            )
        )
        report_info["status"] = "failed"
    else:
        report_info["status"] = "executed"

    return report_info, findings


def execute_zipwiz(
    *,
    repo_root: Path,
    strictness: str,
    temp_dir: Path,
    root_resolution: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    report_info: dict[str, Any] = {
        "status": "failed",
        "summary": {},
        "exit_code": None,
    }
    findings: list[dict[str, Any]] = []

    canonical_entries = resolve_roots(default_zipwiz_canonical_roots(), repo_root)
    reference_entries = resolve_roots(default_zipwiz_reference_roots(), repo_root)
    root_resolution["zipwiz"] = {
        "canonical": canonical_entries,
        "reference": reference_entries,
    }

    if not canonical_entries or not existing_roots(canonical_entries):
        report_info["status"] = "failed"
        report_info["summary"] = {"reason": "all_canonical_roots_unresolved"}
        findings.append(make_unresolved_roots_finding("zipwiz", canonical_entries))
        return report_info, findings

    if not existing_roots(reference_entries):
        findings.append(make_reference_roots_warning(reference_entries))

    out_json = temp_dir / "zipwiz_scan.json"
    out_md = temp_dir / "zipwiz_scan.md"

    command = [
        sys.executable,
        str(ZIPWIZ_SCAN_SCRIPT),
        "--repo",
        str(repo_root),
        "--roots",
        csv_for_entries(canonical_entries),
        "--reference-roots",
        csv_for_entries(reference_entries),
        "--strictness",
        strictness,
        "--out-json",
        str(out_json),
        "--out-md",
        str(out_md),
    ]
    report_info["command"] = command

    if not ZIPWIZ_SCAN_SCRIPT.exists():
        findings.append(
            make_execution_failure_finding(
                "zipwiz",
                f"Missing scanner script: {ZIPWIZ_SCAN_SCRIPT}",
                {"domain": "zipwiz", "reason": "missing_script"},
            )
        )
        report_info["summary"] = {"reason": "missing_script"}
        return report_info, findings

    run = run_subprocess(command)
    report_info["exit_code"] = run["exit_code"]

    parsed = load_json_file(out_json)
    if parsed is not None:
        report_info["summary"] = parsed.get("summary") or {}
        report_info["cross_skill_routing"] = parsed.get("cross_skill_routing") or []
        findings.extend(normalize_zipwiz_findings(parsed))

        if int((parsed.get("summary") or {}).get("total_artifacts", 0)) == 0:
            findings.append(make_zero_artifact_warning("zipwiz"))

    if run["error"] is not None or run["exit_code"] not in {0}:
        findings.append(
            make_execution_failure_finding(
                "zipwiz",
                run["stderr"] or "zipwiz scanner exited unexpectedly",
                {
                    "domain": "zipwiz",
                    "exit_code": run["exit_code"],
                    "stderr": run["stderr"],
                },
            )
        )
        report_info["status"] = "failed"
    else:
        report_info["status"] = "executed"

    return report_info, findings


def execute_script_governor(*, repo_root: Path, temp_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    report_info: dict[str, Any] = {
        "status": "failed",
        "summary": {},
        "exit_code": None,
    }
    findings: list[dict[str, Any]] = []

    out_json = temp_dir / "script_governor_scan.json"
    command = [
        sys.executable,
        str(SCRIPT_GOVERNOR_SCAN_SCRIPT),
        "--repo",
        str(repo_root),
        "--out",
        str(out_json),
    ]
    report_info["command"] = command

    if not SCRIPT_GOVERNOR_SCAN_SCRIPT.exists():
        findings.append(
            make_execution_failure_finding(
                "script_governor",
                f"Missing scanner script: {SCRIPT_GOVERNOR_SCAN_SCRIPT}",
                {"domain": "script_governor", "reason": "missing_script"},
            )
        )
        report_info["summary"] = {"reason": "missing_script"}
        return report_info, findings

    run = run_subprocess(command)
    report_info["exit_code"] = run["exit_code"]

    parsed = load_json_file(out_json)
    if parsed is not None:
        report_info["summary"] = parsed.get("summary") or {}
        findings.extend(normalize_script_governor_findings(parsed))

    if run["error"] is not None or run["exit_code"] not in {0}:
        findings.append(
            make_execution_failure_finding(
                "script_governor",
                run["stderr"] or "script-governor scanner exited unexpectedly",
                {
                    "domain": "script_governor",
                    "exit_code": run["exit_code"],
                    "stderr": run["stderr"],
                },
            )
        )
        report_info["status"] = "failed"
    else:
        report_info["status"] = "executed"

    return report_info, findings


def execute_narrative_tone(
    *,
    repo_root: Path,
    strictness: str,
    temp_dir: Path,
    root_resolution: dict[str, Any],
    changed_paths: list[str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    report_info: dict[str, Any] = {
        "status": "failed",
        "summary": {},
        "exit_code": None,
    }
    findings: list[dict[str, Any]] = []

    entries = resolve_roots(default_narrative_tone_roots(), repo_root)
    root_resolution["narrative_tone"] = entries
    paths_csv = ",".join(changed_paths)

    if not paths_csv and (not entries or not existing_roots(entries)):
        report_info["status"] = "failed"
        report_info["summary"] = {"reason": "all_roots_unresolved"}
        findings.append(make_unresolved_roots_finding("narrative_tone", entries))
        return report_info, findings

    out_json = temp_dir / "narrative_tone_scan.json"
    out_md = temp_dir / "narrative_tone_scan.md"
    command = [
        sys.executable,
        str(NARRATIVE_TONE_SCAN_SCRIPT),
        "--repo",
        str(repo_root),
        "--strictness",
        strictness,
        "--out-json",
        str(out_json),
        "--out-md",
        str(out_md),
    ]
    if paths_csv:
        command.extend(["--paths", paths_csv])
    else:
        command.extend(["--roots", csv_for_entries(entries)])
    report_info["command"] = command

    if not NARRATIVE_TONE_SCAN_SCRIPT.exists():
        findings.append(
            make_execution_failure_finding(
                "narrative_tone",
                f"Missing scanner script: {NARRATIVE_TONE_SCAN_SCRIPT}",
                {"domain": "narrative_tone", "reason": "missing_script"},
            )
        )
        report_info["summary"] = {"reason": "missing_script"}
        return report_info, findings

    run = run_subprocess(command)
    report_info["exit_code"] = run["exit_code"]

    parsed = load_json_file(out_json)
    if parsed is not None:
        report_info["summary"] = parsed.get("summary") or {}
        findings.extend(normalize_narrative_tone_findings(parsed))

        if int((parsed.get("summary") or {}).get("scanned_files", 0)) == 0:
            findings.append(make_zero_artifact_warning("narrative_tone"))

    if run["error"] is not None or run["exit_code"] not in {0}:
        findings.append(
            make_execution_failure_finding(
                "narrative_tone",
                run["stderr"] or "narrative-tone scanner exited unexpectedly",
                {
                    "domain": "narrative_tone",
                    "exit_code": run["exit_code"],
                    "stderr": run["stderr"],
                },
            )
        )
        report_info["status"] = "failed"
    else:
        report_info["status"] = "executed"

    return report_info, findings


def execute_repo_stabilizer(*, repo_root: Path, temp_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    report_info: dict[str, Any] = {
        "status": "failed",
        "summary": {},
        "exit_code": None,
    }
    findings: list[dict[str, Any]] = []

    out_json = temp_dir / "repo_stabilizer_scan.json"
    command = [
        sys.executable,
        str(REPO_STABILIZER_SCAN_SCRIPT),
        "--repo",
        str(repo_root),
        "--out",
        str(out_json),
    ]
    report_info["command"] = command

    if not REPO_STABILIZER_SCAN_SCRIPT.exists():
        findings.append(
            make_execution_failure_finding(
                "repo_stabilizer",
                f"Missing scanner script: {REPO_STABILIZER_SCAN_SCRIPT}",
                {"domain": "repo_stabilizer", "reason": "missing_script"},
            )
        )
        report_info["summary"] = {"reason": "missing_script"}
        return report_info, findings

    run = run_subprocess(command)
    report_info["exit_code"] = run["exit_code"]

    parsed = load_json_file(out_json)
    if parsed is not None:
        report_info["summary"] = parsed.get("summary") or {}
        findings.extend(normalize_repo_stabilizer_findings(parsed))

    if run["error"] is not None or run["exit_code"] not in {0}:
        findings.append(
            make_execution_failure_finding(
                "repo_stabilizer",
                run["stderr"] or "repo-stabilizer scanner exited unexpectedly",
                {
                    "domain": "repo_stabilizer",
                    "exit_code": run["exit_code"],
                    "stderr": run["stderr"],
                },
            )
        )
        report_info["status"] = "failed"
    else:
        report_info["status"] = "executed"

    return report_info, findings


def execute_canon(
    *,
    repo_root: Path,
    temp_dir: Path,
    draft_input: Path,
    draft_layer: str | None,
    draft_type: str | None,
    draft_auto_detect: bool,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    del repo_root
    del temp_dir

    report_info: dict[str, Any] = {
        "status": "failed",
        "summary": {},
        "exit_code": None,
    }
    findings: list[dict[str, Any]] = []

    if not CANON_VALIDATE_SCRIPT.exists():
        findings.append(
            make_execution_failure_finding(
                "canon",
                f"Missing scanner script: {CANON_VALIDATE_SCRIPT}",
                {"domain": "canon", "reason": "missing_script"},
            )
        )
        report_info["summary"] = {"reason": "missing_script"}
        return report_info, findings

    if not draft_input.exists():
        findings.append(
            make_execution_failure_finding(
                "canon",
                f"Draft input file does not exist: {draft_input}",
                {"domain": "canon", "reason": "missing_draft_input"},
            )
        )
        report_info["summary"] = {"reason": "missing_draft_input"}
        return report_info, findings

    command = [
        sys.executable,
        str(CANON_VALIDATE_SCRIPT),
        "--input",
        str(draft_input),
        "--format",
        "json",
    ]

    if draft_auto_detect or not (draft_layer and draft_type):
        command.append("--auto-detect")
    else:
        command.extend(["--layer", draft_layer, "--type", draft_type])

    report_info["command"] = command

    run = run_subprocess(command)
    report_info["exit_code"] = run["exit_code"]

    parsed = parse_json_text(run.get("stdout") or "")
    if parsed is not None:
        validation_run = parsed.get("validation_run") or {}
        report_info["summary"] = {
            "entities_checked": validation_run.get("entities_checked"),
            "passed": validation_run.get("passed"),
            "blocked": validation_run.get("blocked"),
        }
        findings.extend(normalize_canon_findings(parsed, draft_input))

    # Canon validator exits 1 when BLOCK findings are present. Treat this as successful execution.
    canon_exit_ok = run["exit_code"] in {0, 1} and parsed is not None
    if run["error"] is not None or not canon_exit_ok:
        findings.append(
            make_execution_failure_finding(
                "canon",
                run["stderr"] or "canon validator exited unexpectedly",
                {
                    "domain": "canon",
                    "exit_code": run["exit_code"],
                    "stderr": run["stderr"],
                },
            )
        )
        report_info["status"] = "failed"
    else:
        report_info["status"] = "executed"

    return report_info, findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run unified Aurora governance orchestration and emit one verdict.")
    parser.add_argument("--repo", required=True, help="Repository root path")
    parser.add_argument("--mode", choices=["full", "changed-paths"], default="full", help="Domain routing mode")
    parser.add_argument("--changed-paths", help="Comma-separated changed paths (used with --mode changed-paths)")

    parser.add_argument("--draft-input", help="Optional draft input file for canon validation")
    parser.add_argument("--draft-layer", choices=["L1", "L2", "L3"], help="Draft layer for canon validation")
    parser.add_argument("--draft-type", help="Draft entity type for canon validation")
    parser.add_argument("--draft-auto-detect", action="store_true", help="Auto-detect canon layer/type")

    parser.add_argument(
        "--strictness",
        choices=["balanced", "strict", "lenient"],
        default="balanced",
        help="Strictness used for threadcore, zipwiz, and narrative/tone scans",
    )

    parser.add_argument(
        "--out-json",
        default="/tmp/aurora_governance_orchestrator.json",
        help="Path for unified JSON output",
    )
    parser.add_argument(
        "--out-md",
        default="/tmp/aurora_governance_orchestrator.md",
        help="Path for unified markdown output",
    )
    parser.add_argument("--tmp-dir", default="/tmp", help="Directory for intermediate scanner outputs")

    parser.add_argument("--no-threadcore", action="store_true", help="Disable threadcore-governor execution")
    parser.add_argument("--no-zipwiz", action="store_true", help="Disable zipwiz-governor execution")
    parser.add_argument("--no-script-governor", action="store_true", help="Disable aurora-script-governor execution")
    parser.add_argument("--no-narrative-tone", action="store_true", help="Disable aurora-narrative-tone-governor execution")
    parser.add_argument("--no-repo-stabilizer", action="store_true", help="Disable aurora-repo-stabilizer execution")
    parser.add_argument("--no-canon", action="store_true", help="Disable aurora-canon-reconciler execution")

    return parser.parse_args()


def run_orchestration(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path(args.repo).expanduser().resolve()
    if not repo_root.exists() or not repo_root.is_dir():
        raise FileNotFoundError(f"Invalid repo root: {repo_root}")

    draft_input = Path(args.draft_input).expanduser().resolve() if args.draft_input else None

    routing = select_domains(args)
    selected_domains = routing["selected_domains"]

    root_resolution: dict[str, Any] = {}
    domain_reports: dict[str, dict[str, Any]] = {
        domain: {"status": "not_selected", "summary": {}} for domain in DOMAIN_ORDER
    }

    all_findings: list[dict[str, Any]] = []

    temp_parent = Path(args.tmp_dir).expanduser().resolve()
    temp_parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="aurora_orchestrator_", dir=str(temp_parent)) as temp_workspace:
        temp_dir = Path(temp_workspace)

        for domain in DOMAIN_ORDER:
            if domain not in selected_domains:
                continue

            if domain == "threadcore":
                report, findings = execute_threadcore(
                    repo_root=repo_root,
                    strictness=args.strictness,
                    temp_dir=temp_dir,
                    root_resolution=root_resolution,
                )
            elif domain == "zipwiz":
                report, findings = execute_zipwiz(
                    repo_root=repo_root,
                    strictness=args.strictness,
                    temp_dir=temp_dir,
                    root_resolution=root_resolution,
                )
            elif domain == "script_governor":
                report, findings = execute_script_governor(repo_root=repo_root, temp_dir=temp_dir)
            elif domain == "narrative_tone":
                report, findings = execute_narrative_tone(
                    repo_root=repo_root,
                    strictness=args.strictness,
                    temp_dir=temp_dir,
                    root_resolution=root_resolution,
                    changed_paths=routing.get("changed_paths") or [],
                )
            elif domain == "repo_stabilizer":
                report, findings = execute_repo_stabilizer(repo_root=repo_root, temp_dir=temp_dir)
            elif domain == "canon":
                if draft_input is None:
                    report = {
                        "status": "skipped",
                        "summary": {"reason": "no_draft_input"},
                    }
                    findings = []
                else:
                    report, findings = execute_canon(
                        repo_root=repo_root,
                        temp_dir=temp_dir,
                        draft_input=draft_input,
                        draft_layer=args.draft_layer,
                        draft_type=args.draft_type,
                        draft_auto_detect=args.draft_auto_detect,
                    )
            else:
                report = {
                    "status": "failed",
                    "summary": {"reason": f"unsupported_domain:{domain}"},
                }
                findings = [
                    make_execution_failure_finding(
                        domain,
                        f"Unsupported orchestration domain: {domain}",
                        {"domain": domain, "reason": "unsupported_domain"},
                    )
                ]

            domain_reports[domain] = report
            all_findings.extend(findings)

    all_findings.sort(
        key=lambda row: (
            SEVERITY_ORDER.get(str(row.get("severity", "INFO")), 99),
            str(row.get("domain", "")),
            str(row.get("rule_id", "")),
            str(row.get("file", "")),
        )
    )

    summary = build_summary(all_findings, selected_domains)
    summary["remediation_queue"] = build_remediation_queue(all_findings)

    verdict = build_verdict(
        all_findings,
        selected_domains=selected_domains,
        domain_reports=domain_reports,
        root_resolution=root_resolution,
    )

    payload: dict[str, Any] = {
        "scan_meta": {
            "generated_at": now_utc_iso(),
            "orchestrator_version": ORCHESTRATOR_VERSION,
            "repo_root": str(repo_root),
            "strictness": args.strictness,
        },
        "routing": routing,
        "root_resolution": root_resolution,
        "domain_reports": domain_reports,
        "findings": all_findings,
        "summary": summary,
        "verdict": verdict,
    }

    return payload


def write_outputs(payload: dict[str, Any], out_json: Path, out_md: Path) -> None:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown_report(payload), encoding="utf-8")


def main() -> int:
    args = parse_args()

    try:
        payload = run_orchestration(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    out_json = Path(args.out_json).expanduser().resolve()
    out_md = Path(args.out_md).expanduser().resolve()
    write_outputs(payload, out_json, out_md)

    verdict = payload.get("verdict") or {}
    print(json.dumps({
        "status": verdict.get("status"),
        "confidence": verdict.get("confidence"),
        "reason": verdict.get("reason"),
        "out_json": str(out_json),
        "out_md": str(out_md),
    }, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

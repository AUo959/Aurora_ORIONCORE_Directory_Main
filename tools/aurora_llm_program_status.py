#!/usr/bin/env python3
"""Report the state of the Aurora LLM program from repository evidence."""

# Reads, never writes:
#
# * ``catalog/aurora_llm_program.json``  (program registry: tracks, task ids, owner gates)
# * ``catalog/contracts/aurora_state_model_contract_v0_1.json``  (ASM contract)
# * ``catalog/session_state.json``  (task queue status for each linked task id)
# * optionally a CloudBank checkout (``--cloudbank PATH``) for the model catalog in
#   ``modules/ai_core/unified_ai_interface.py``
#
# The output is an instrument reading for the aurora-llm-steward agent. It does not
# decide what to do next and it does not authorize anything.
#
# Usage:
#     python3 tools/aurora_llm_program_status.py
#     python3 tools/aurora_llm_program_status.py --json
#     python3 tools/aurora_llm_program_status.py --cloudbank ../aurora-cloudbank-symbolic
#     python3 tools/aurora_llm_program_status.py --today 2026-11-28
#
# Exit codes:
#     0  report produced, no findings that need action
#     1  report produced, at least one finding needs action (stale catalog claim,
#        missing surface, task id not in the queue, training flag flipped)
#     2  a required input file is missing or unreadable

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
PROGRAM_PATH = Path("catalog/aurora_llm_program.json")
CONTRACT_PATH = Path("catalog/contracts/aurora_state_model_contract_v0_1.json")
SESSION_STATE_PATH = Path("catalog/session_state.json")
CATALOG_SOURCE = Path("modules/ai_core/unified_ai_interface.py")

_CAPABILITY_BLOCK = re.compile(
    r"AIModel\.(?P<name>\w+):\s*ModelCapabilities\((?P<body>.*?)\n\s*\),",
    re.DOTALL,
)
_VERIFIED_ON = re.compile(r'verified_on="(?P<v>[^"]*)"')
_VERIFIED_SOURCE = re.compile(r'verified_source="(?P<v>[^"]*)"')
_AVAILABLE_FALSE = re.compile(r"\bavailable\s*=\s*False\b")


@dataclass
class Finding:
    severity: str  # "action" or "info"
    track: str
    message: str

    def to_dict(self) -> Dict[str, str]:
        return {"severity": self.severity, "track": self.track, "message": self.message}


@dataclass
class Report:
    today: str
    tracks: List[Dict[str, Any]] = field(default_factory=list)
    asm: Dict[str, Any] = field(default_factory=dict)
    catalog: Optional[Dict[str, Any]] = None
    findings: List[Finding] = field(default_factory=list)

    @property
    def needs_action(self) -> bool:
        return any(f.severity == "action" for f in self.findings)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "today": self.today,
            "needs_action": self.needs_action,
            "tracks": self.tracks,
            "asm": self.asm,
            "catalog": self.catalog,
            "findings": [f.to_dict() for f in self.findings],
        }


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _surface_exists(root: Path, surface: str, primary_repo: str, cloudbank: Optional[Path]) -> Optional[bool]:
    """Return True/False when checkable, None when the surface lives in an unavailable repo."""
    clean = surface.split(" (")[0].strip()
    if "(root)" in surface or primary_repo == "Aurora_ORIONCORE_Directory_Main":
        return (root / clean).exists()
    if primary_repo == "aurora-cloudbank-symbolic":
        if clean.startswith("catalog/backlog_archive/"):
            return (root / clean).exists()
        if cloudbank is None:
            return None
        return (cloudbank / clean).exists()
    return None


def _index_items(items: Any, index: Dict[str, Dict[str, Any]], where: str, default: Optional[str]) -> None:
    for item in items or []:
        if isinstance(item, dict) and item.get("id"):
            index.setdefault(item["id"], {"status": default or item.get("status"), "where": where})


def _task_index(session_state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    active = session_state.get("active_task")
    _index_items([active] if isinstance(active, dict) else [], index, "active_task", None)
    _index_items(session_state.get("task_queue"), index, "task_queue", None)
    _index_items(session_state.get("completed_tasks"), index, "completed_tasks", "completed")
    return index


def parse_catalog(source: str) -> List[Dict[str, Any]]:
    """Extract per-model availability and verification claims from the CloudBank catalog source."""
    entries: List[Dict[str, Any]] = []
    for match in _CAPABILITY_BLOCK.finditer(source):
        body = match.group("body")
        verified_on = _VERIFIED_ON.search(body)
        verified_source = _VERIFIED_SOURCE.search(body)
        entries.append(
            {
                "model": match.group("name"),
                "available": not _AVAILABLE_FALSE.search(body),
                "verified_on": verified_on.group("v") if verified_on else "",
                "verified_source": verified_source.group("v") if verified_source else "unverified",
            }
        )
    return entries


def _entry_finding(entry: Dict[str, Any], today: date, max_age: int) -> Optional[Finding]:
    model = entry["model"]
    if not entry["verified_on"] or entry["verified_source"] == "unverified":
        return Finding("action", "T1", f"{model} is available but unverified.")
    try:
        age = (today - date.fromisoformat(entry["verified_on"])).days
    except ValueError:
        return Finding("action", "T1", f"{model} has an unparseable verified_on date.")
    entry["age_days"] = age
    if age > max_age:
        return Finding("action", "T1", f"{model} catalog claim is {age} days old (limit {max_age}).")
    if age > max_age - 14:
        return Finding("info", "T1", f"{model} catalog claim expires in {max_age - age} days.")
    return None


def _catalog_findings(entries: List[Dict[str, Any]], today: date, max_age: int) -> List[Finding]:
    available = [e for e in entries if e["available"]]
    if not available:
        return [Finding("action", "T1", "No available model in the CloudBank catalog.")]
    findings = [_entry_finding(entry, today, max_age) for entry in available]
    return [f for f in findings if f is not None]


def _track_section(
    track: Dict[str, Any], root: Path, cloudbank: Optional[Path], tasks: Dict[str, Dict[str, Any]]
) -> Tuple[Dict[str, Any], List[Finding]]:
    findings: List[Finding] = []
    surfaces = []
    for surface in track.get("surfaces", []):
        exists = _surface_exists(root, surface, track.get("primary_repo", ""), cloudbank)
        surfaces.append({"path": surface, "exists": exists})
        if exists is False:
            findings.append(Finding("action", track["id"], f"Surface missing: {surface}"))
    linked = []
    for task_id in track.get("task_ids", []):
        state = tasks.get(task_id)
        linked.append({"id": task_id, "status": state["status"] if state else None})
        if state is None:
            findings.append(Finding("action", track["id"], f"Task id {task_id} is not in session_state.json."))
    section = {"id": track["id"], "name": track["name"], "surfaces": surfaces, "tasks": linked}
    return section, findings


def _asm_section(contract: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Finding]]:
    first_slice = contract.get("first_slice", {})
    roles = contract.get("repository_roles", {})
    asm = {
        "contract_status": contract.get("status"),
        "runtime_status": contract.get("runtime_status"),
        "adoption": {repo: info.get("adoption_status") for repo, info in roles.items()},
        "gates": [gate.get("id") for gate in contract.get("quality_gates", [])],
        "first_slice": first_slice.get("id"),
        "model_training_authorized": bool(first_slice.get("model_training_authorized")),
        "next_adoption_step": _next_adoption_step(contract),
    }
    findings: List[Finding] = []
    if asm["model_training_authorized"]:
        findings.append(
            Finding(
                "action",
                "T2",
                "first_slice.model_training_authorized is true; confirm an owner-approved training issue exists.",
            )
        )
    return asm, findings


def _catalog_section(
    cloudbank: Optional[Path], max_age: int, today: date
) -> Tuple[Optional[Dict[str, Any]], List[Finding]]:
    if cloudbank is None:
        return None, [Finding("info", "T1", "CloudBank checkout not given; catalog freshness not checked (--cloudbank).")]
    source_path = cloudbank / CATALOG_SOURCE
    if not source_path.exists():
        return None, [Finding("action", "T1", f"CloudBank catalog not found at {source_path}.")]
    entries = parse_catalog(source_path.read_text(encoding="utf-8"))
    findings = _catalog_findings(entries, today, max_age)
    return {"source": str(CATALOG_SOURCE), "entries": entries}, findings


def build_report(root: Path, cloudbank: Optional[Path], today: date) -> Report:
    program = _load_json(root / PROGRAM_PATH)
    contract = _load_json(root / CONTRACT_PATH)
    tasks = _task_index(_load_json(root / SESSION_STATE_PATH))
    report = Report(today=today.isoformat())

    for track in program.get("tracks", []):
        section, findings = _track_section(track, root, cloudbank, tasks)
        report.tracks.append(section)
        report.findings.extend(findings)

    report.asm, findings = _asm_section(contract)
    report.findings.extend(findings)

    max_age = int(program.get("catalog_max_claim_age_days", 90))
    report.catalog, findings = _catalog_section(cloudbank, max_age, today)
    report.findings.extend(findings)
    return report


def _next_adoption_step(contract: Dict[str, Any]) -> Optional[str]:
    """First adoption step whose owning repo has not adopted. Coarse by design: a reading, not a plan."""
    roles = contract.get("repository_roles", {})
    order = contract.get("adoption_order", [])
    if not order:
        return None
    root_status = roles.get("Aurora_ORIONCORE_Directory_Main", {}).get("adoption_status")
    if root_status in (None, "proposal_committed"):
        return order[0]
    cloudbank_status = roles.get("aurora-cloudbank-symbolic-main", {}).get("adoption_status")
    if len(order) > 1 and cloudbank_status in (None, "not_started"):
        return order[1]
    return order[-1]


def _render_asm(asm: Dict[str, Any]) -> List[str]:
    lines = [
        "## Aurora State Model (T2)",
        f"- Contract: {asm['contract_status']} · runtime: {asm['runtime_status']}",
        f"- Training authorized: {asm['model_training_authorized']}",
        f"- Next adoption step: {asm['next_adoption_step']}",
    ]
    lines.extend(f"  - {repo}: {status}" for repo, status in asm["adoption"].items())
    return lines


def _render_track_row(track: Dict[str, Any]) -> str:
    tasks = ", ".join(f"{t['id']} ({t['status'] or 'absent'})" for t in track["tasks"]) or "-"
    missing = ", ".join(s["path"] for s in track["surfaces"] if s["exists"] is False) or "none"
    return f"| {track['id']} {track['name']} | {tasks} | {missing} |"


def _render_catalog(catalog: Optional[Dict[str, Any]]) -> List[str]:
    if not catalog:
        return []
    lines = ["", "## Model catalog (T1)", "| Model | Available | Verified on | Source |", "| --- | --- | --- | --- |"]
    lines.extend(
        f"| {e['model']} | {e['available']} | {e['verified_on'] or '-'} | {e['verified_source']} |"
        for e in catalog["entries"]
    )
    return lines


def render_markdown(report: Report) -> str:
    lines = [f"# Aurora LLM program status — {report.today}", ""]
    lines.append(f"Needs action: **{'yes' if report.needs_action else 'no'}**")
    lines.append("")
    lines.extend(_render_asm(report.asm))
    lines.extend(["", "## Tracks", "| Track | Linked tasks | Missing surfaces |", "| --- | --- | --- |"])
    lines.extend(_render_track_row(track) for track in report.tracks)
    lines.extend(_render_catalog(report.catalog))
    lines.extend(["", "## Findings"])
    lines.extend(f"- [{f.severity}] {f.track}: {f.message}" for f in report.findings)
    if not report.findings:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="ORIONCORE checkout (default: this repo)")
    parser.add_argument("--cloudbank", type=Path, default=None, help="CloudBank checkout for catalog checks")
    parser.add_argument("--today", type=date.fromisoformat, default=None, help="Override today (YYYY-MM-DD)")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown")
    args = parser.parse_args(argv)

    today = args.today or date.today()
    try:
        report = build_report(args.root.resolve(), args.cloudbank.resolve() if args.cloudbank else None, today)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"aurora_llm_program_status: cannot read inputs: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(render_markdown(report), end="")
    return 1 if report.needs_action else 0


if __name__ == "__main__":
    sys.exit(main())

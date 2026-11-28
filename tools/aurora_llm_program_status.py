#!/usr/bin/env python3
"""Report the state of the Aurora LLM program from repository evidence.

Reads, never writes:

* ``catalog/aurora_llm_program.json``  (program registry: tracks, task ids, owner gates)
* ``catalog/contracts/aurora_state_model_contract_v0_1.json``  (ASM contract)
* ``catalog/session_state.json``  (task queue status for each linked task id)
* optionally a CloudBank checkout (``--cloudbank PATH``) for the model catalog in
  ``modules/ai_core/unified_ai_interface.py``

The output is an instrument reading for the aurora-llm-steward agent. It does not
decide what to do next and it does not authorize anything.

Usage:
    python3 tools/aurora_llm_program_status.py
    python3 tools/aurora_llm_program_status.py --json
    python3 tools/aurora_llm_program_status.py --cloudbank ../aurora-cloudbank-symbolic
    python3 tools/aurora_llm_program_status.py --today 2026-11-28

Exit codes:
    0  report produced, no findings that need action
    1  report produced, at least one finding needs action (stale catalog claim,
       missing surface, task id not in the queue, training flag flipped)
    2  a required input file is missing or unreadable
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

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


def _task_index(session_state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    for item in session_state.get("task_queue", []) or []:
        if isinstance(item, dict) and item.get("id"):
            index[item["id"]] = {"status": item.get("status"), "where": "task_queue"}
    for item in session_state.get("completed_tasks", []) or []:
        if isinstance(item, dict) and item.get("id"):
            index.setdefault(item["id"], {"status": "completed", "where": "completed_tasks"})
    active = session_state.get("active_task")
    if isinstance(active, dict) and active.get("id"):
        index[active["id"]] = {"status": active.get("status", "active"), "where": "active_task"}
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


def _catalog_findings(entries: List[Dict[str, Any]], today: date, max_age: int) -> List[Finding]:
    findings: List[Finding] = []
    available = [e for e in entries if e["available"]]
    if not available:
        findings.append(Finding("action", "T1", "No available model in the CloudBank catalog."))
    for entry in available:
        if not entry["verified_on"] or entry["verified_source"] == "unverified":
            findings.append(Finding("action", "T1", f"{entry['model']} is available but unverified."))
            continue
        try:
            age = (today - date.fromisoformat(entry["verified_on"])).days
        except ValueError:
            findings.append(Finding("action", "T1", f"{entry['model']} has an unparseable verified_on date."))
            continue
        entry["age_days"] = age
        if age > max_age:
            findings.append(
                Finding("action", "T1", f"{entry['model']} catalog claim is {age} days old (limit {max_age}).")
            )
        elif age > max_age - 14:
            findings.append(
                Finding("info", "T1", f"{entry['model']} catalog claim expires in {max_age - age} days.")
            )
    return findings


def build_report(root: Path, cloudbank: Optional[Path], today: date) -> Report:
    program = _load_json(root / PROGRAM_PATH)
    contract = _load_json(root / CONTRACT_PATH)
    session_state = _load_json(root / SESSION_STATE_PATH)
    tasks = _task_index(session_state)
    report = Report(today=today.isoformat())

    for track in program.get("tracks", []):
        surfaces = []
        for surface in track.get("surfaces", []):
            exists = _surface_exists(root, surface, track.get("primary_repo", ""), cloudbank)
            surfaces.append({"path": surface, "exists": exists})
            if exists is False:
                report.findings.append(Finding("action", track["id"], f"Surface missing: {surface}"))
        linked = []
        for task_id in track.get("task_ids", []):
            state = tasks.get(task_id)
            linked.append({"id": task_id, "status": state["status"] if state else None})
            if state is None:
                report.findings.append(
                    Finding("action", track["id"], f"Task id {task_id} is not in session_state.json.")
                )
        report.tracks.append(
            {"id": track["id"], "name": track["name"], "surfaces": surfaces, "tasks": linked}
        )

    first_slice = contract.get("first_slice", {})
    roles = contract.get("repository_roles", {})
    report.asm = {
        "contract_status": contract.get("status"),
        "runtime_status": contract.get("runtime_status"),
        "adoption": {repo: info.get("adoption_status") for repo, info in roles.items()},
        "gates": [gate.get("id") for gate in contract.get("quality_gates", [])],
        "first_slice": first_slice.get("id"),
        "model_training_authorized": bool(first_slice.get("model_training_authorized")),
        "next_adoption_step": _next_adoption_step(contract),
    }
    if report.asm["model_training_authorized"]:
        report.findings.append(
            Finding(
                "action",
                "T2",
                "first_slice.model_training_authorized is true; confirm an owner-approved training issue exists.",
            )
        )

    if cloudbank is not None:
        source_path = cloudbank / CATALOG_SOURCE
        if source_path.exists():
            entries = parse_catalog(source_path.read_text(encoding="utf-8"))
            report.findings.extend(
                _catalog_findings(entries, today, int(program.get("catalog_max_claim_age_days", 90)))
            )
            report.catalog = {"source": str(CATALOG_SOURCE), "entries": entries}
        else:
            report.findings.append(Finding("action", "T1", f"CloudBank catalog not found at {source_path}."))
    else:
        report.findings.append(
            Finding("info", "T1", "CloudBank checkout not given; catalog freshness not checked (--cloudbank).")
        )
    return report


def _next_adoption_step(contract: Dict[str, Any]) -> Optional[str]:
    """First adoption step whose owning repo has not adopted. Coarse by design: a reading, not a plan."""
    roles = contract.get("repository_roles", {})
    order = contract.get("adoption_order", [])
    root_status = roles.get("Aurora_ORIONCORE_Directory_Main", {}).get("adoption_status")
    if order and root_status in (None, "proposal_committed"):
        return order[0]
    cloudbank_status = roles.get("aurora-cloudbank-symbolic-main", {}).get("adoption_status")
    if len(order) > 1 and cloudbank_status in (None, "not_started"):
        return order[1]
    return order[-1] if order else None


def render_markdown(report: Report) -> str:
    lines = [f"# Aurora LLM program status — {report.today}", ""]
    lines.append(f"Needs action: **{'yes' if report.needs_action else 'no'}**")
    lines.append("")
    asm = report.asm
    lines.append("## Aurora State Model (T2)")
    lines.append(f"- Contract: {asm['contract_status']} · runtime: {asm['runtime_status']}")
    lines.append(f"- Training authorized: {asm['model_training_authorized']}")
    lines.append(f"- Next adoption step: {asm['next_adoption_step']}")
    for repo, status in asm["adoption"].items():
        lines.append(f"  - {repo}: {status}")
    lines.append("")
    lines.append("## Tracks")
    lines.append("| Track | Linked tasks | Missing surfaces |")
    lines.append("| --- | --- | --- |")
    for track in report.tracks:
        tasks = ", ".join(f"{t['id']} ({t['status'] or 'absent'})" for t in track["tasks"]) or "-"
        missing = [s["path"] for s in track["surfaces"] if s["exists"] is False]
        lines.append(f"| {track['id']} {track['name']} | {tasks} | {', '.join(missing) or 'none'} |")
    if report.catalog:
        lines.append("")
        lines.append("## Model catalog (T1)")
        lines.append("| Model | Available | Verified on | Source |")
        lines.append("| --- | --- | --- | --- |")
        for entry in report.catalog["entries"]:
            lines.append(
                f"| {entry['model']} | {entry['available']} | {entry['verified_on'] or '-'} | "
                f"{entry['verified_source']} |"
            )
    lines.append("")
    lines.append("## Findings")
    if not report.findings:
        lines.append("- none")
    for finding in report.findings:
        lines.append(f"- [{finding.severity}] {finding.track}: {finding.message}")
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

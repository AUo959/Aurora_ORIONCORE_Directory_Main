#!/usr/bin/env python3
"""Read-only lifecycle audit for the cross-platform Aurora task queue.

Structural validity remains owned by ``session_state_check.py``. This tool
adds the time- and actionability-aware layer needed by session start, workspace
verification, and Mission Control. It never mutates queue state.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _workspace_common import now_iso_utc, serialized_root, write_json

import session_state_check


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE = ROOT / "catalog" / "session_state.json"
DEFAULT_POLICY = ROOT / "catalog" / "session_queue_policy.json"
DEFAULT_REPORT = ROOT / "reports" / "analysis" / "session_queue_health_latest.json"

PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


def parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def finding(
    check: str,
    details: str,
    suggested_fix: str,
    *,
    task_id: str | None = None,
    blocking: bool = False,
) -> dict[str, Any]:
    return {
        "check": check,
        "severity": "error" if blocking else "warning",
        "blocking": blocking,
        "task_id": task_id,
        "details": details,
        "suggested_fix": suggested_fix,
    }


def _task_sort_key(item: dict[str, Any]) -> tuple[int, str, str]:
    return (
        PRIORITY_RANK.get(str(item.get("priority", "medium")), 9),
        str(item.get("review_at") or "9999"),
        str(item.get("id", "")),
    )


def _age_days(value: Any, now: datetime) -> float | None:
    parsed = parse_time(value)
    if parsed is None:
        return None
    return max(0.0, (now - parsed).total_seconds() / 86400)


def build_report(
    root: Path,
    *,
    state_path: Path | None = None,
    policy_path: Path | None = None,
    now: datetime | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    checked_at = now or utc_now()
    state_file = state_path or root / "catalog" / "session_state.json"
    policy_file = policy_path or root / "catalog" / "session_queue_policy.json"
    state = load_json(state_file)
    policy = load_json(policy_file)
    findings: list[dict[str, Any]] = []

    for detail in session_state_check.validate(state):
        findings.append(
            finding(
                "session_queue_contract",
                detail,
                "Repair the queue through tools/session_state_io.py, then rerun make session-state-check.",
                blocking=True,
            )
        )

    active = state.get("active_task")
    active_items = [active] if isinstance(active, dict) else []
    queue = [item for item in state.get("task_queue", []) if isinstance(item, dict)]
    legacy_pending = [
        item for item in state.get("pending_for_next_session", []) if isinstance(item, dict)
    ]
    all_open = active_items + queue
    by_status = Counter(str(item.get("status", "unknown")) for item in all_open)
    by_priority = Counter(str(item.get("priority", "unknown")) for item in all_open)
    owner_gates = [item for item in queue if item.get("approval_required") is True]
    due_review = [
        item
        for item in queue
        if parse_time(item.get("review_at")) is not None
        and parse_time(item.get("review_at")) <= checked_at
    ]

    warn_days = int(policy.get("suspended_warning_days", 7))
    review_days = int(policy.get("suspended_review_days", 14))
    if isinstance(active, dict) and active.get("status") == "suspended":
        age = _age_days(active.get("updated_at"), checked_at)
        task_id = str(active.get("id", "unknown"))
        resume_by = parse_time(active.get("resume_by"))
        if resume_by is not None and resume_by <= checked_at:
            findings.append(
                finding(
                    "suspended_task_review_due",
                    f"Suspended task '{task_id}' passed resume_by={active.get('resume_by')}.",
                    "Resume it now, complete it, or move it to waiting/parked with a concrete trigger and review date.",
                    task_id=task_id,
                )
            )
        elif age is not None and age >= review_days:
            findings.append(
                finding(
                    "suspended_task_review_due",
                    f"Suspended task '{task_id}' has not been triaged for {int(age)} days.",
                    "Resume it now, complete it, or move it to waiting/parked; do not renew suspension without an executable next action.",
                    task_id=task_id,
                )
            )
        elif age is not None and age >= warn_days:
            findings.append(
                finding(
                    "suspended_task_aging",
                    f"Suspended task '{task_id}' has been untouched for {int(age)} days.",
                    "Confirm the next action remains executable before its resume_by date.",
                    task_id=task_id,
                )
            )

    if due_review:
        ids = ", ".join(str(item.get("id")) for item in sorted(due_review, key=_task_sort_key)[:8])
        findings.append(
            finding(
                "queue_review_due",
                f"{len(due_review)} queued item(s) reached review_at: {ids}.",
                "Triage each due item: start, renew with evidence, move to a concrete wait trigger, park deliberately, complete, or cancel.",
            )
        )

    if legacy_pending:
        findings.append(
            finding(
                "legacy_pending_queue",
                f"{len(legacy_pending)} item(s) remain in deprecated pending_for_next_session.",
                "Migrate them into task_queue with explicit status, timestamps, next action, and definition of done.",
                blocking=True,
            )
        )

    allowed_scopes = set(policy.get("owner_gate", {}).get("allowed_scopes", []))
    for item in owner_gates:
        scope = str(item.get("gate_scope", ""))
        if scope not in allowed_scopes:
            findings.append(
                finding(
                    "owner_gate_scope_invalid",
                    f"Task '{item.get('id')}' uses owner gate scope '{scope}', which is not policy-approved.",
                    "Remove the gate from reversible work or select a policy-approved consequential decision scope.",
                    task_id=str(item.get("id", "unknown")),
                    blocking=True,
                )
            )

    ready = sorted(
        [item for item in queue if item.get("status") == "ready"],
        key=_task_sort_key,
    )
    waiting = sorted(
        [item for item in queue if item.get("status") == "waiting"],
        key=_task_sort_key,
    )
    parked = sorted(
        [item for item in queue if item.get("status") == "parked"],
        key=_task_sort_key,
    )
    status = "blocked" if any(item["blocking"] for item in findings) else (
        "attention" if findings else "ready"
    )
    return {
        "schema_version": 1,
        "generated_at": generated_at or now_iso_utc(),
        "checked_at": checked_at.isoformat().replace("+00:00", "Z"),
        "root": serialized_root(root),
        "tool": "session_queue_health",
        "run_mode": "read_only",
        "mutation_posture": "advisory_only",
        "status": status,
        "summary": {
            "active_count": len(active_items),
            "ready_count": len(ready),
            "waiting_count": len(waiting),
            "parked_count": len(parked),
            "owner_gate_count": len(owner_gates),
            "due_review_count": len(due_review),
            "legacy_pending_count": len(legacy_pending),
            "open_count": len(all_open),
            "finding_count": len(findings),
            "blocking_count": sum(1 for item in findings if item["blocking"]),
            "by_status": dict(sorted(by_status.items())),
            "by_priority": dict(sorted(by_priority.items())),
        },
        "active_task": active,
        "next_ready": ready[:5],
        "waiting_decisions": owner_gates[:5],
        "due_review": sorted(due_review, key=_task_sort_key)[:8],
        "findings": findings,
    }


def format_summary(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        f"Aurora Session Queue: {report['status']}",
        f"- Active: {summary['active_count']} | Ready: {summary['ready_count']} | Waiting: {summary['waiting_count']} | Parked: {summary['parked_count']}",
        f"- Owner gates: {summary['owner_gate_count']} | Reviews due: {summary['due_review_count']} | Legacy pending: {summary['legacy_pending_count']}",
    ]
    if report.get("active_task"):
        active = report["active_task"]
        lines.append(f"- Active task: [{active.get('status')}] {active.get('id')} — {active.get('next_action', active.get('description', ''))}")
    if report.get("next_ready"):
        lines.append("- Next ready:")
        for item in report["next_ready"][:3]:
            lines.append(f"  - [{item.get('priority')}] {item.get('id')}: {item.get('next_action')}")
    if report.get("findings"):
        lines.append("- Lifecycle findings:")
        for item in report["findings"][:5]:
            lines.append(f"  - [{item['severity']}] {item['details']}")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--state")
    parser.add_argument("--policy")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--persist-report", action="store_true")
    parser.add_argument("--report-out")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    state = Path(args.state).expanduser().resolve() if args.state else None
    policy = Path(args.policy).expanduser().resolve() if args.policy else None
    report = build_report(root, state_path=state, policy_path=policy)
    if args.persist_report or args.report_out:
        report_path = Path(args.report_out).expanduser().resolve() if args.report_out else root / DEFAULT_REPORT.relative_to(ROOT)
        write_json(report_path, report)
    print(format_summary(report) if args.summary else json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())

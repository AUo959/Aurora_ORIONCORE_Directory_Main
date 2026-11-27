#!/usr/bin/env python3
"""Read-only, allowlisted Aurora Mission Control snapshot for interactive UIs."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "reports/analysis/aurora_mission_control_latest.json"
SOURCE_REFERENCE = "reports/analysis/aurora_mission_control_latest.json"
REPOSITORY = "AUo959/Aurora_ORIONCORE_Directory_Main"
STATUS = ("ready", "attention", "blocked")
PRIORITY = ("P0", "P1", "P2", "P3")


class BridgeError(ValueError):
    """Unsafe or inconsistent input, which must not be presented as valid."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BridgeError(message)


def timestamp(value: Any, name: str) -> datetime:
    require(isinstance(value, str), f"{name}: missing ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BridgeError(f"{name}: malformed ISO-8601 timestamp") from exc
    require(parsed.tzinfo is not None and parsed.utcoffset() is not None,
            f"{name}: UTC offset required")
    return parsed.astimezone(timezone.utc)


def label(value: Any, name: str, size: int = 300) -> str:
    require(isinstance(value, str) and value.strip(), f"{name}: nonempty text required")
    return value.strip()[:size]


def nonnegative(value: Any, name: str) -> int:
    require(type(value) is int and value >= 0, f"{name}: nonnegative integer required")
    return value


def refs(value: Any) -> list[str]:
    require(isinstance(value, list), "evidence_refs: list required")
    safe = []
    for item in value[:12]:
        if (isinstance(item, str)
                and item.startswith(("catalog/", "docs/", "reports/", "tools/", "tests/"))
                and ".." not in item and "\n" not in item):
            safe.append(item[:240])
    return safe


def build_snapshot(
    report: dict[str, Any], *,
    input_sha256: str,
    now: datetime | None = None,
    max_age_hours: int = 48,
) -> dict[str, Any]:
    """Transform a saved report into a UI-only contract without side effects."""
    require(isinstance(report, dict), "report must be a JSON object")
    require(report.get("schema_version") == 1, "unsupported source schema_version")
    require(report.get("tool") == "aurora_mission_control", "unexpected source producer")
    require(report.get("run_mode") == "read_only", "source is not read-only")
    require(report.get("mutation_posture") == "advisory_only", "source is not advisory-only")
    require(report.get("nested_repo_mutation") is False, "source permits nested mutation")
    require(report.get("status") in STATUS, "unrecognized source health")
    require(isinstance(input_sha256, str) and len(input_sha256) == 64
            and all(c in "0123456789abcdef" for c in input_sha256), "invalid SHA-256")
    require(type(max_age_hours) is int and max_age_hours > 0, "invalid max age")
    current = now if now is not None else datetime.now(timezone.utc)
    require(current.tzinfo is not None and current.utcoffset() is not None,
            "current time requires UTC offset")
    current = current.astimezone(timezone.utc)
    source_time = timestamp(report.get("generated_at"), "generated_at")
    require(source_time <= current + timedelta(minutes=5), "source timestamp in future")
    age = max(0, int((current - source_time).total_seconds()))

    raw_inbox, raw_lanes = report.get("operator_inbox"), report.get("build_lanes")
    summary, sources = report.get("summary"), report.get("source_reports")
    require(isinstance(raw_inbox, list) and isinstance(raw_lanes, list),
            "missing inbox or lanes")
    require(isinstance(summary, dict) and isinstance(sources, dict),
            "missing summary or source reports")

    inbox = []
    for index, item in enumerate(raw_inbox):
        require(isinstance(item, dict), f"inbox[{index}] is not an object")
        require(item.get("mutation_posture") == "advisory_only",
                f"inbox[{index}] would cross an authority boundary")
        require(item.get("priority") in PRIORITY, f"inbox[{index}] priority invalid")
        require(type(item.get("approval_required")) is bool
                and type(item.get("blocking")) is bool, "inbox boolean flags required")
        category = label(item.get("category"), "category", 80)
        restricted = category == "recovery_review" or "restricted" in str(item.get("title", "")).lower()
        inbox.append({
            "id": label(item.get("item_id"), "item_id", 240),
            "title": label(item.get("title"), "title"),
            "priority": item["priority"],
            "status": label(item.get("status"), "inbox status", 40),
            "category": category,
            "source": label(item.get("source"), "source", 100),
            "target_repo": label(item.get("target_repo"), "target_repo", 100),
            "approval_required": item["approval_required"],
            "blocking": item["blocking"],
            "evidence_restricted": restricted,
            "evidence_refs": [] if restricted else refs(item.get("evidence_refs", [])),
            "next_action": (
                "Review in governed source workspace; evidence not exported."
                if restricted else label(item.get("recommended_next_action"), "next_action", 600)
            ),
        })

    lanes = []
    for index, item in enumerate(raw_lanes):
        require(isinstance(item, dict), f"lane[{index}] is not an object")
        require(item.get("mutation_posture") == "readiness_only",
                f"lane[{index}] would cross an authority boundary")
        require(item.get("status") in STATUS, f"lane[{index}] status invalid")
        missing = item.get("missing_required_tools")
        require(isinstance(missing, list) and all(isinstance(x, str) for x in missing),
                "missing_required_tools invalid")
        lanes.append({
            "id": label(item.get("lane_id"), "lane_id", 120),
            "title": label(item.get("title"), "lane title", 180),
            "status": item["status"],
            "missing_required_tools": [x[:80] for x in missing[:30]],
            "evidence_refs": refs(item.get("evidence_refs", [])),
        })

    lane_totals = summary.get("build_lanes")
    require(isinstance(lane_totals, dict), "lane totals missing")
    for key, expected in (
        ("operator_inbox_count", len(inbox)),
        ("approval_required_count", sum(x["approval_required"] for x in inbox)),
        ("blocking_count", sum(x["blocking"] for x in inbox)),
        ("source_count", len(sources)),
    ):
        require(nonnegative(summary.get(key), key) == expected, f"{key}: summary mismatch")
    for state in STATUS:
        require(nonnegative(lane_totals.get(state), "lane count") ==
                sum(x["status"] == state for x in lanes),
                f"{state}: lane count mismatch")
    errors = nonnegative(summary.get("source_error_count"), "source_error_count")
    require(errors <= len(sources), "source error count invalid")
    return {
        "schema_version": 1,
        "kind": "aurora.mission_control.snapshot",
        "generated_at": current.isoformat(),
        "authority": {
            "mode": "read_only",
            "mutation_posture": "advisory_only",
            "canon_write": False,
            "runtime_execution": False,
            "nested_repo_mutation": False,
        },
        "source": {
            "repository": REPOSITORY,
            "report_ref": SOURCE_REFERENCE,
            "generated_at": source_time.isoformat(),
            "sha256": input_sha256,
            "freshness": "stale" if age > max_age_hours * 3600 else "fresh",
            "age_seconds": age,
            "max_age_hours": max_age_hours,
        },
        "health": {
            "status": report["status"],
            "sources": len(sources),
            "source_errors": errors,
            "inbox_items": len(inbox),
            "approval_required": sum(x["approval_required"] for x in inbox),
            "blocking_items": sum(x["blocking"] for x in inbox),
            "lanes": {state: sum(x["status"] == state for x in lanes) for state in STATUS},
        },
        "operator_inbox": inbox,
        "build_lanes": lanes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Aurora Intelligent UI snapshot.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT,
                        help="Existing Mission Control report; does not regenerate.")
    parser.add_argument("--output", type=Path, help="Optional explicit JSON export path.")
    parser.add_argument("--max-age-hours", type=int, default=48)
    args = parser.parse_args(argv)
    try:
        raw = args.input.read_bytes()
        payload = build_snapshot(json.loads(raw), input_sha256=hashlib.sha256(raw).hexdigest(),
                                 max_age_hours=args.max_age_hours)
        output = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        if args.output is None:
            sys.stdout.write(output)
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output, encoding="utf-8")
    except (OSError, UnicodeError, json.JSONDecodeError, BridgeError) as exc:
        print(f"intelligent-ui bridge: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build a selective integration capsule from protocol + module manifests."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

VALID_DECISIONS = {"include", "backup_only", "reject"}


def now_utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    lowered = value.lower()
    lowered = re.sub(r"[^a-z0-9]+", "_", lowered)
    lowered = re.sub(r"_+", "_", lowered).strip("_")
    return lowered or "source"


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"JSON file not found: {path}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc.msg} (line {exc.lineno}, col {exc.colno})")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Aurora Selective Integration capsules with deterministic triage decisions."
    )
    parser.add_argument("--protocol-json", required=True, help="Path to Aurora Selective Integration protocol JSON")
    parser.add_argument("--modules-json", required=True, help="Path to module manifest JSON (array of modules)")
    parser.add_argument("--triage-json", help="Optional triage override JSON (array with module_id decisions)")

    parser.add_argument("--source-json", help="Optional JSON file for source metadata")
    parser.add_argument("--source-name", help="Source name when --source-json is not provided")
    parser.add_argument("--source-type", help="Source type (zip, folder, api, etc.)")
    parser.add_argument("--source-uri", help="Source URI/path")
    parser.add_argument("--source-hash", help="Source hash, example sha256:...")

    parser.add_argument("--capsule-id", help="Capsule id override")
    parser.add_argument("--created-utc", help="Capsule timestamp override (ISO-8601 UTC)")

    parser.add_argument("--alex-approval", default="pending", help="Alex approval status (default: pending)")
    parser.add_argument("--aurora-approval", default="prepared", help="Aurora approval status (default: prepared)")
    parser.add_argument("--pilot-approval", default="not_required", help="Pilot approval status (default: not_required)")

    parser.add_argument("--merge-uri", help="Canon merge URI override")
    parser.add_argument("--meta-retro-ref", help="Meta retro reference override")

    parser.add_argument("--out-json", required=True, help="Output path for generated capsule JSON")
    parser.add_argument("--out-md", help="Optional output path for markdown triage report")

    parser.add_argument(
        "--fail-on-reject",
        action="store_true",
        help="Exit 2 when any module is rejected",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Require protocol + module required fields and fail on malformed module entries",
    )
    return parser.parse_args()


def normalize_decision(raw: str | None) -> str | None:
    if raw is None:
        return None
    normalized = raw.strip().lower()
    aliases = {
        "backup": "backup_only",
        "backup-only": "backup_only",
        "backup only": "backup_only",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized in VALID_DECISIONS:
        return normalized
    return None


def clamp(value: Any, *, low: float = 0.0, high: float = 1.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    if number < low:
        return low
    if number > high:
        return high
    return number


def compute_source_hash(source: dict[str, Any], modules: list[dict[str, Any]]) -> str:
    if source.get("hash"):
        return str(source["hash"])
    digest_material = json.dumps(
        {
            "source_name": source.get("name"),
            "source_type": source.get("type"),
            "source_uri": source.get("uri"),
            "module_ids": [str(item.get("id", "")) for item in modules],
        },
        sort_keys=True,
        ensure_ascii=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(digest_material).hexdigest()


def validate_protocol(protocol: dict[str, Any], strict: bool) -> None:
    required = ["protocol_id", "version", "purpose", "decision_thresholds", "workflow"]
    missing = [key for key in required if key not in protocol]
    if missing:
        raise ValueError(f"Protocol missing required key(s): {', '.join(missing)}")

    if strict:
        if not isinstance(protocol.get("decision_thresholds"), dict):
            raise ValueError("Protocol decision_thresholds must be an object")
        if not isinstance(protocol.get("workflow"), list):
            raise ValueError("Protocol workflow must be an array")


def validate_modules(modules: Any, strict: bool) -> list[dict[str, Any]]:
    if not isinstance(modules, list):
        raise ValueError("modules-json must be an array")

    out: list[dict[str, Any]] = []
    for idx, raw in enumerate(modules):
        if not isinstance(raw, dict):
            if strict:
                raise ValueError(f"Module at index {idx} must be an object")
            continue

        module_id = str(raw.get("id", "")).strip() or f"module_{idx + 1}"
        category = str(raw.get("category", "unspecified")).strip() or "unspecified"
        path = str(raw.get("path", "")).strip() or "unknown"
        integration_path = str(raw.get("integration_path", "")).strip() or "staging/"
        notes = str(raw.get("notes", "")).strip()

        if strict:
            missing = [
                key
                for key in ("id", "category", "path", "integration_path")
                if not str(raw.get(key, "")).strip()
            ]
            if missing:
                raise ValueError(f"Module '{module_id}' missing required key(s): {', '.join(missing)}")

        telemetry = raw.get("telemetry", [])
        if not isinstance(telemetry, list):
            telemetry = []
        telemetry = [str(item) for item in telemetry]

        out.append(
            {
                "id": module_id,
                "category": category,
                "path": path,
                "integration_path": integration_path,
                "redundancy_flag": int(raw.get("redundancy_flag", 0) or 0),
                "telemetry": telemetry,
                "notes": notes,
                "utility_score": clamp(raw.get("utility_score", 0.5)),
                "improvement_score": clamp(raw.get("improvement_score", 0.5)),
                "maintenance_burden": clamp(raw.get("maintenance_burden", 0.5)),
                "conflict_risk": clamp(raw.get("conflict_risk", 0.2)),
                "specialist": str(raw.get("specialist", "Unassigned")).strip() or "Unassigned",
                "risk_notes": str(raw.get("risk_notes", "")).strip(),
                "backout_plan": str(raw.get("backout_plan", "")).strip(),
                "decision_override": normalize_decision(raw.get("decision")),
            }
        )

    if strict and not out:
        raise ValueError("No valid module entries found in modules-json")
    return out


def triage_override_map(raw: Any) -> dict[str, dict[str, str]]:
    if raw is None:
        return {}
    if not isinstance(raw, list):
        raise ValueError("triage-json must be an array when provided")

    out: dict[str, dict[str, str]] = {}
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        module_id = str(item.get("module_id", "")).strip()
        if not module_id:
            module_id = str(item.get("id", "")).strip()
        if not module_id:
            module_id = f"triage_item_{idx + 1}"

        decision = normalize_decision(item.get("decision"))
        out[module_id] = {
            "specialist": str(item.get("specialist", "Unassigned")).strip() or "Unassigned",
            "decision": decision or "",
            "risk_notes": str(item.get("risk_notes", "")).strip(),
            "backout_plan": str(item.get("backout_plan", "")).strip(),
        }
    return out


def auto_decision(module: dict[str, Any]) -> tuple[str, str]:
    if module["decision_override"] in VALID_DECISIONS:
        return str(module["decision_override"]), "manual_override"

    utility = module["utility_score"]
    improvement = module["improvement_score"]
    maintenance = module["maintenance_burden"]
    conflict = module["conflict_risk"]
    redundancy = module["redundancy_flag"]

    if utility >= 0.70 and improvement >= 0.60 and maintenance <= 0.40 and conflict <= 0.30 and redundancy == 0:
        return "include", "meets_include_threshold"

    if redundancy == 1 and utility < 0.75:
        return "backup_only", "redundant_with_resilience_value"

    if utility >= 0.45 and conflict <= 0.60 and maintenance <= 0.75:
        return "backup_only", "partial_value_with_moderate_risk"

    return "reject", "fails_threshold_or_high_risk"


def default_risk_notes(module: dict[str, Any], decision: str) -> str:
    if module["risk_notes"]:
        return module["risk_notes"]
    if decision == "include":
        return "Low risk if scoped to declared integration_path and monitored via telemetry."
    if decision == "backup_only":
        return "Store as disabled fallback; avoid active merge without specialist retest."
    return "Reject due to low net value or elevated conflict/maintenance risk."


def default_backout_plan(module: dict[str, Any], decision: str) -> str:
    if module["backout_plan"]:
        return module["backout_plan"]
    return (
        f"Remove integrated artifacts for {module['id']} from {module['integration_path']} "
        f"and restore prior state from rollback capsule."
    )


def build_source(args: argparse.Namespace, modules: list[dict[str, Any]]) -> dict[str, Any]:
    if args.source_json:
        source = load_json(Path(args.source_json))
        if not isinstance(source, dict):
            raise ValueError("source-json must contain an object")
    else:
        if not (args.source_name and args.source_type and args.source_uri):
            raise ValueError("Provide --source-json or all of --source-name --source-type --source-uri")
        source = {
            "name": args.source_name,
            "type": args.source_type,
            "uri": args.source_uri,
        }

    if args.source_hash:
        source["hash"] = args.source_hash
    source["hash"] = compute_source_hash(source, modules)

    source.setdefault("name", "unknown_source")
    source.setdefault("type", "unknown")
    source.setdefault("uri", "unknown")
    return source


def build_capsule(
    args: argparse.Namespace,
    protocol: dict[str, Any],
    modules: list[dict[str, Any]],
    triage_overrides: dict[str, dict[str, str]],
    source: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, int]]:
    created_utc = args.created_utc or now_utc_iso()

    if args.capsule_id:
        capsule_id = args.capsule_id
    else:
        base = slugify(str(source.get("name", "source")))
        capsule_id = f"AURORA_SI_{base.upper()}_{created_utc[:10].replace('-', '')}"

    extracted_modules: list[dict[str, Any]] = []
    triage_rows: list[dict[str, Any]] = []
    counts = {"include": 0, "backup_only": 0, "reject": 0}

    for module in modules:
        decision, rationale = auto_decision(module)
        override = triage_overrides.get(module["id"], {})

        if override.get("decision"):
            forced = normalize_decision(override.get("decision"))
            if forced:
                decision = forced
                rationale = "triage_override"

        specialist = override.get("specialist") or module["specialist"]
        risk_notes = override.get("risk_notes") or default_risk_notes(module, decision)
        backout_plan = override.get("backout_plan") or default_backout_plan(module, decision)

        counts[decision] += 1

        extracted_modules.append(
            {
                "id": module["id"],
                "category": module["category"],
                "path": module["path"],
                "integration_path": module["integration_path"],
                "redundancy_flag": module["redundancy_flag"],
                "telemetry": module["telemetry"],
                "notes": module["notes"],
                "decision": decision,
                "decision_rationale": rationale,
                "scores": {
                    "utility_score": module["utility_score"],
                    "improvement_score": module["improvement_score"],
                    "maintenance_burden": module["maintenance_burden"],
                    "conflict_risk": module["conflict_risk"],
                },
            }
        )

        triage_rows.append(
            {
                "module_id": module["id"],
                "specialist": specialist,
                "decision": decision,
                "risk_notes": risk_notes,
                "backout_plan": backout_plan,
            }
        )

    merge_uri = args.merge_uri or f"@mesh://canon/aurora/si/{slugify(capsule_id)}"
    meta_retro_ref = args.meta_retro_ref or f"@mesh://meta_retro/entries/{created_utc[:10]}-{slugify(capsule_id)}"

    average = lambda key: round(sum(m[key] for m in modules) / max(len(modules), 1), 4)
    capsule = {
        "capsule_id": capsule_id,
        "created_utc": created_utc,
        "protocol_ref": protocol["protocol_id"],
        "protocol_version": protocol.get("version"),
        # THREADCORE payload validators require these identity/governance fields.
        "anchor_seed": protocol.get("anchor_seed", "EOS_SEED_ORION"),
        "ethics_protocol": protocol.get("ethics_protocol", "Picard_Delta_3"),
        "role": protocol.get("role", "SelectiveIntegration"),
        "source": source,
        "extracted_modules": extracted_modules,
        "triage": triage_rows,
        "approvals": {
            "alex": args.alex_approval,
            "aurora": args.aurora_approval,
            "pilot": args.pilot_approval,
        },
        "canonization": {
            "merge_uri": merge_uri,
            "rollback_capsule_id": f"{capsule_id}_ROLLBACK",
            "meta_retro_ref": meta_retro_ref,
        },
        "metrics": {
            "modules_total": len(modules),
            "modules_included": counts["include"],
            "modules_backup_only": counts["backup_only"],
            "modules_rejected": counts["reject"],
            "redundancy_ratio": round(
                sum(1 for m in modules if m["redundancy_flag"] == 1) / max(len(modules), 1),
                4,
            ),
            "average_utility_score": average("utility_score"),
            "average_improvement_score": average("improvement_score"),
            "average_maintenance_burden": average("maintenance_burden"),
            "average_conflict_risk": average("conflict_risk"),
        },
        "references": {
            "schema_uri": protocol.get("schema_uri", "selective_integration_capsule.schema.json"),
            "example_uri": protocol.get("example_uri", "example_selective_integration_capsule.json"),
        },
    }
    return capsule, counts


def render_markdown(protocol: dict[str, Any], capsule: dict[str, Any], counts: dict[str, int]) -> str:
    lines: list[str] = []
    lines.append("# Selective Integration Report")
    lines.append("")
    lines.append("## Decision Snapshot")
    lines.append(f"- Protocol: `{protocol.get('protocol_id', 'unknown')}` v`{protocol.get('version', 'unknown')}`")
    lines.append(f"- Capsule: `{capsule['capsule_id']}`")
    lines.append(f"- Created UTC: `{capsule['created_utc']}`")
    lines.append(f"- Source: `{capsule['source'].get('name', 'unknown')}` ({capsule['source'].get('type', 'unknown')})")
    lines.append(f"- Include: `{counts['include']}` | Backup Only: `{counts['backup_only']}` | Reject: `{counts['reject']}`")
    lines.append("")

    lines.append("## Threshold Reference")
    thresholds = protocol.get("decision_thresholds", {})
    for key in ("include", "backup_only", "reject"):
        lines.append(f"- `{key}`: {thresholds.get(key, 'not specified')}")
    lines.append("")

    lines.append("## Workflow Reference")
    for idx, step in enumerate(protocol.get("workflow", []), start=1):
        lines.append(f"{idx}. {step}")
    lines.append("")

    lines.append("## Module Decisions")
    for row in capsule.get("triage", []):
        lines.append(f"- `{row['module_id']}` -> `{row['decision']}` ({row['specialist']})")
        lines.append(f"  Risk: {row['risk_notes']}")
        lines.append(f"  Backout: {row['backout_plan']}")
    lines.append("")

    lines.append("## Canonization Plan")
    canon = capsule.get("canonization", {})
    lines.append(f"- Merge URI: `{canon.get('merge_uri', '')}`")
    lines.append(f"- Rollback Capsule: `{canon.get('rollback_capsule_id', '')}`")
    lines.append(f"- Meta Retro Ref: `{canon.get('meta_retro_ref', '')}`")
    lines.append("")

    lines.append("## Approvals")
    approvals = capsule.get("approvals", {})
    lines.append(f"- Alex: `{approvals.get('alex', 'pending')}`")
    lines.append(f"- Aurora: `{approvals.get('aurora', 'prepared')}`")
    lines.append(f"- Pilot: `{approvals.get('pilot', 'not_required')}`")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    args = parse_args()

    protocol_path = Path(args.protocol_json).expanduser().resolve()
    modules_path = Path(args.modules_json).expanduser().resolve()
    out_json = Path(args.out_json).expanduser().resolve()
    out_md = Path(args.out_md).expanduser().resolve() if args.out_md else None

    try:
        protocol = load_json(protocol_path)
        if not isinstance(protocol, dict):
            raise ValueError("protocol-json must contain an object")
        validate_protocol(protocol, args.strict)

        modules = validate_modules(load_json(modules_path), args.strict)
        triage_overrides = triage_override_map(load_json(Path(args.triage_json).expanduser().resolve()) if args.triage_json else None)

        source = build_source(args, modules)
        capsule, counts = build_capsule(args, protocol, modules, triage_overrides, source)

        write_json(out_json, capsule)
        if out_md is not None:
            write_text(out_md, render_markdown(protocol, capsule, counts))

        if args.fail_on_reject and counts["reject"] > 0:
            return 2
        return 0

    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

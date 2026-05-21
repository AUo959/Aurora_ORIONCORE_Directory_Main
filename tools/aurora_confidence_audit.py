#!/usr/bin/env python3
"""Attach auditable confidence metadata to Aurora outputs.

This is root control-plane tooling. It scores structured claims for audit and
alerting, but it does not validate real-world truth or execute runtime actions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Optional

from _workspace_common import now_iso_utc, write_json


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_REF = "catalog/schemas/aurora_confidence_record.schema.json"
CONTRACT_REF = "catalog/contracts/aurora_confidence_audit_contract_v1.json"
DEFAULT_REPORT = ROOT / "reports" / "analysis" / "aurora_confidence_audit_latest.json"
TOOL_NAME = "aurora_confidence_audit"
DEFAULT_THRESHOLD = 0.70
DEFAULT_CALIBRATION_PROFILE = "bootstrap_default_v1"

CLAIM_TYPES = {
    "conclusion",
    "analysis",
    "prediction",
    "recommendation",
}

VISIBILITY_VALUES = {
    "internal",
    "user_facing",
    "background",
    "receipt_only",
}

EVIDENCE_LEVEL_BASE = {
    "verified_artifact": 0.88,
    "direct_observation": 0.80,
    "deterministic_check": 0.84,
    "corroborated_inference": 0.72,
    "inference": 0.62,
    "projection": 0.54,
    "speculation": 0.36,
    "unsupported": 0.18,
}


class ConfidenceInputError(ValueError):
    """Raised when a claim cannot be normalized into an audit record."""


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def round_score(value: float) -> float:
    return round(clamp01(value), 3)


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item is not None and str(item) != ""]
    if isinstance(value, tuple):
        return [str(item) for item in value if item is not None and str(item) != ""]
    if value == "":
        return []
    return [str(value)]


def require_float(value: Any, field: str) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError) as exc:
        raise ConfidenceInputError(f"{field} must be a number between 0 and 1") from exc
    if not 0 <= score <= 1:
        raise ConfidenceInputError(f"{field} must be between 0 and 1")
    return score


def require_adjustment(value: Any, field: str) -> float:
    try:
        adjustment = float(value)
    except (TypeError, ValueError) as exc:
        raise ConfidenceInputError(f"{field} must be a number between -1 and 1") from exc
    if not -1 <= adjustment <= 1:
        raise ConfidenceInputError(f"{field} must be between -1 and 1")
    return adjustment


def stable_suffix(parts: list[Any]) -> str:
    canonical = json.dumps(parts, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def confidence_band(score: float) -> str:
    if score >= 0.85:
        return "high"
    if score >= 0.70:
        return "substantial"
    if score >= 0.50:
        return "limited"
    if score >= 0.30:
        return "low"
    return "unsupported"


def alert_level(score: float, threshold: float) -> str:
    if score >= threshold:
        return "none"
    gap = threshold - score
    if gap >= 0.30:
        return "critical"
    if gap >= 0.15:
        return "warning"
    return "notice"


def pick_explicit_score(payload: dict[str, Any]) -> Optional[float]:
    if payload.get("score") is not None:
        return require_float(payload["score"], "score")
    if payload.get("confidence_score") is not None:
        return require_float(payload["confidence_score"], "confidence_score")

    confidence = payload.get("confidence")
    if isinstance(confidence, (int, float, str)):
        return require_float(confidence, "confidence")
    if isinstance(confidence, dict) and "score" in confidence:
        return require_float(confidence["score"], "confidence.score")
    return None


def nested_confidence_value(payload: dict[str, Any], field: str) -> Any:
    confidence = payload.get("confidence")
    if isinstance(confidence, dict):
        return confidence.get(field)
    return None


def normalize_claim_input(payload: dict[str, Any], default_threshold: float) -> dict[str, Any]:
    if "claim" in payload and isinstance(payload["claim"], dict):
        claim_payload = dict(payload["claim"])
        merged = dict(payload)
        merged.pop("claim", None)
        claim_payload.update({key: value for key, value in merged.items() if key not in claim_payload})
        payload = claim_payload

    text = str(payload.get("text") or payload.get("claim_text") or "").strip()
    if not text:
        raise ConfidenceInputError("claim text is required")

    claim_type = str(payload.get("claim_type") or payload.get("type") or "analysis").strip()
    if claim_type not in CLAIM_TYPES:
        raise ConfidenceInputError(f"claim_type must be one of {sorted(CLAIM_TYPES)}")

    visibility = str(payload.get("visibility") or payload.get("audience_visibility") or "internal").strip()
    if visibility not in VISIBILITY_VALUES:
        raise ConfidenceInputError(f"visibility must be one of {sorted(VISIBILITY_VALUES)}")

    evidence_level = str(
        payload.get("evidence_level")
        or nested_confidence_value(payload, "evidence_level")
        or "inference"
    ).strip()
    if evidence_level not in EVIDENCE_LEVEL_BASE:
        raise ConfidenceInputError(f"evidence_level must be one of {sorted(EVIDENCE_LEVEL_BASE)}")

    threshold_value = payload.get("threshold", nested_confidence_value(payload, "threshold"))
    threshold = require_float(threshold_value, "threshold") if threshold_value is not None else default_threshold

    calibration_value = payload.get(
        "calibration_adjustment",
        nested_confidence_value(payload, "calibration_adjustment"),
    )
    calibration_adjustment = (
        require_adjustment(calibration_value, "calibration_adjustment")
        if calibration_value is not None
        else 0.0
    )

    explicit_score = pick_explicit_score(payload)
    claim_id = str(payload.get("claim_id") or "").strip()
    if not claim_id:
        claim_id = "aurora.claim." + stable_suffix([claim_type, text, payload.get("source_ref")])

    return {
        "claim_id": claim_id,
        "claim_type": claim_type,
        "text": text,
        "producer": str(payload.get("producer") or "aurora-system"),
        "visibility": visibility,
        "source_ref": payload.get("source_ref"),
        "subject_refs": as_list(payload.get("subject_refs")),
        "authority_refs": as_list(payload.get("authority_refs")),
        "evidence_refs": as_list(payload.get("evidence_refs")),
        "receipt_refs": as_list(payload.get("receipt_refs")),
        "assumptions": as_list(payload.get("assumptions")),
        "uncertainty_factors": as_list(payload.get("uncertainty_factors")),
        "contradiction_refs": as_list(payload.get("contradiction_refs")),
        "resolution_policy_ref": payload.get("resolution_policy_ref"),
        "explicit_score": explicit_score,
        "threshold": threshold,
        "evidence_level": evidence_level,
        "calibration_profile": str(
            payload.get("calibration_profile")
            or nested_confidence_value(payload, "calibration_profile")
            or DEFAULT_CALIBRATION_PROFILE
        ),
        "calibration_adjustment": calibration_adjustment,
        "run_mode": str(payload.get("run_mode") or "audit_scoring_only"),
    }


def rubric_adjustments(claim: dict[str, Any]) -> list[dict[str, Any]]:
    adjustments: list[dict[str, Any]] = []
    evidence_count = len(claim["evidence_refs"])
    authority_count = len(claim["authority_refs"])

    if evidence_count:
        adjustments.append(
            {
                "code": "evidence_refs",
                "delta": round_score(min(0.09, evidence_count * 0.03)),
                "reason": "linked evidence references strengthen audit confidence",
            }
        )
    else:
        penalty = -0.12 if claim["evidence_level"] in {"verified_artifact", "direct_observation"} else -0.08
        adjustments.append(
            {
                "code": "missing_evidence_refs",
                "delta": penalty,
                "reason": "claim has no linked evidence reference in the audit record",
            }
        )

    if authority_count:
        adjustments.append(
            {
                "code": "authority_refs",
                "delta": round_score(min(0.04, authority_count * 0.02)),
                "reason": "authority references make the basis easier to inspect",
            }
        )
    else:
        adjustments.append(
            {
                "code": "missing_authority_refs",
                "delta": -0.03,
                "reason": "no authority reference was supplied",
            }
        )

    for index, _item in enumerate(claim["assumptions"], start=1):
        adjustments.append(
            {
                "code": f"assumption_{index}",
                "delta": -0.03,
                "reason": "unverified assumption lowers confidence",
            }
        )

    for index, _item in enumerate(claim["uncertainty_factors"], start=1):
        adjustments.append(
            {
                "code": f"uncertainty_factor_{index}",
                "delta": -0.04,
                "reason": "explicit uncertainty factor lowers confidence",
            }
        )

    for index, _item in enumerate(claim["contradiction_refs"], start=1):
        adjustments.append(
            {
                "code": f"contradiction_ref_{index}",
                "delta": -0.10,
                "reason": "contradictory evidence must be resolved or surfaced",
            }
        )

    if claim["claim_type"] == "prediction" and not claim["resolution_policy_ref"]:
        adjustments.append(
            {
                "code": "prediction_without_resolution_policy",
                "delta": -0.07,
                "reason": "prediction lacks an explicit resolution policy for later calibration",
            }
        )

    if claim["visibility"] == "user_facing" and claim["claim_type"] == "recommendation":
        adjustments.append(
            {
                "code": "user_facing_recommendation",
                "delta": -0.02,
                "reason": "user-facing recommendations need slightly stronger audit support",
            }
        )

    return adjustments


def score_claim(claim: dict[str, Any]) -> dict[str, Any]:
    adjustments: list[dict[str, Any]]
    if claim["explicit_score"] is not None:
        raw_score = claim["explicit_score"]
        adjustments = []
        score_source = "explicit_score"
    else:
        base_score = EVIDENCE_LEVEL_BASE[claim["evidence_level"]]
        adjustments = rubric_adjustments(claim)
        raw_score = base_score + sum(float(item["delta"]) for item in adjustments)
        score_source = "rubric_default"

    if claim["calibration_adjustment"]:
        adjustments.append(
            {
                "code": "calibration_adjustment",
                "delta": round(claim["calibration_adjustment"], 3),
                "reason": f"calibration profile {claim['calibration_profile']} adjustment",
            }
        )

    final_score = round_score(raw_score + claim["calibration_adjustment"])
    threshold = claim["threshold"]
    below_threshold = final_score < threshold
    level = alert_level(final_score, threshold)

    return {
        "score": final_score,
        "threshold": round_score(threshold),
        "band": confidence_band(final_score),
        "evidence_level": claim["evidence_level"],
        "score_source": score_source,
        "scoring_method": "aurora_confidence_audit_v1",
        "calibration_profile": claim["calibration_profile"],
        "calibration_adjustment": round(claim["calibration_adjustment"], 3),
        "adjustments": adjustments,
        "below_threshold": below_threshold,
        "alert_level": level,
    }


def user_alert_message(claim: dict[str, Any], confidence: dict[str, Any]) -> str:
    return (
        f"Confidence {confidence['score']:.3f} is below threshold "
        f"{confidence['threshold']:.3f} for this {claim['claim_type']}."
    )


def recommended_next_action(claim: dict[str, Any], confidence: dict[str, Any]) -> str:
    if confidence["below_threshold"]:
        if claim["claim_type"] == "prediction":
            return "Surface uncertainty, attach resolution criteria, and gather stronger evidence before relying on this prediction."
        return "Surface uncertainty to the user when relevant and gather stronger evidence before relying on this output."
    return "Keep confidence metadata in the audit trail; no user-facing alert is required by the current threshold."


def build_confidence_record(
    payload: dict[str, Any],
    default_threshold: float = DEFAULT_THRESHOLD,
    generated_at: Optional[str] = None,
    calibration_adjustment: Optional[float] = None,
) -> dict[str, Any]:
    claim = normalize_claim_input(payload, default_threshold=default_threshold)
    if calibration_adjustment is not None:
        claim["calibration_adjustment"] = require_adjustment(calibration_adjustment, "calibration_adjustment")

    confidence = score_claim(claim)
    assessment_id = "aurora.confidence." + stable_suffix(
        [claim["claim_id"], confidence["score"], confidence["threshold"], claim["calibration_profile"]]
    )
    created_at = generated_at or now_iso_utc()
    alert_required = bool(confidence["below_threshold"])

    public_claim = {
        "claim_id": claim["claim_id"],
        "claim_type": claim["claim_type"],
        "text": claim["text"],
        "producer": claim["producer"],
        "visibility": claim["visibility"],
        "source_ref": claim["source_ref"],
        "subject_refs": claim["subject_refs"],
        "authority_refs": claim["authority_refs"],
        "evidence_refs": claim["evidence_refs"],
        "receipt_refs": claim["receipt_refs"],
        "assumptions": claim["assumptions"],
        "uncertainty_factors": claim["uncertainty_factors"],
        "contradiction_refs": claim["contradiction_refs"],
        "resolution_policy_ref": claim["resolution_policy_ref"],
    }

    return {
        "schema_version": "1.0.0",
        "record_type": "confidence_assessment",
        "assessment_id": assessment_id,
        "created_at": created_at,
        "tool": TOOL_NAME,
        "authority_refs": [SCHEMA_REF, CONTRACT_REF],
        "claim": public_claim,
        "confidence": {
            key: value
            for key, value in confidence.items()
            if key not in {"below_threshold", "alert_level"}
        },
        "audit": {
            "requires_user_alert": alert_required,
            "alert_level": confidence["alert_level"],
            "alert_reason": "confidence_below_threshold" if alert_required else "meets_threshold",
            "user_facing_message": user_alert_message(claim, confidence) if alert_required else None,
            "recommended_next_action": recommended_next_action(claim, confidence),
            "run_mode": claim["run_mode"],
            "live_runtime_execution": False,
            "nested_repo_mutation": False,
        },
    }


def parse_json_records(text: str, jsonl: bool = False) -> list[dict[str, Any]]:
    stripped = text.strip()
    if not stripped:
        return []

    if jsonl:
        return [json.loads(line) for line in stripped.splitlines() if line.strip()]

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return [json.loads(line) for line in stripped.splitlines() if line.strip()]

    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and payload.get("artifact_type") == "confidence_audit_batch":
        return list(payload.get("records", []))
    if isinstance(payload, dict) and "records" in payload and isinstance(payload["records"], list):
        return list(payload["records"])
    if isinstance(payload, dict):
        return [payload]
    raise ConfidenceInputError("input must be a JSON object, JSON array, or JSONL stream")


def read_input(path: Optional[str]) -> str:
    if path:
        return Path(path).expanduser().read_text(encoding="utf-8")
    return sys.stdin.read()


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_type: dict[str, int] = {}
    for record in records:
        claim_type = record["claim"]["claim_type"]
        by_type[claim_type] = by_type.get(claim_type, 0) + 1

    scores = [record["confidence"]["score"] for record in records]
    alerts = [record for record in records if record["audit"]["requires_user_alert"]]
    return {
        "record_count": len(records),
        "user_alert_count": len(alerts),
        "below_threshold_count": len(alerts),
        "claim_type_counts": by_type,
        "minimum_score": min(scores) if scores else None,
        "maximum_score": max(scores) if scores else None,
        "thresholds": sorted({record["confidence"]["threshold"] for record in records}),
        "verdict": "alert_required" if alerts else "pass",
    }


def build_batch(
    payloads: list[dict[str, Any]],
    default_threshold: float = DEFAULT_THRESHOLD,
    generated_at: Optional[str] = None,
    calibration_adjustment: Optional[float] = None,
) -> dict[str, Any]:
    timestamp = generated_at or now_iso_utc()
    records = [
        build_confidence_record(
            payload,
            default_threshold=default_threshold,
            generated_at=timestamp,
            calibration_adjustment=calibration_adjustment,
        )
        for payload in payloads
    ]
    return {
        "schema_version": "1.0.0",
        "artifact_type": "confidence_audit_batch",
        "generated_at": timestamp,
        "tool": TOOL_NAME,
        "run_mode": "audit_scoring_only",
        "live_runtime_execution": False,
        "nested_repo_mutation": False,
        "default_threshold": round_score(default_threshold),
        "schema_ref": SCHEMA_REF,
        "contract_ref": CONTRACT_REF,
        "summary": summarize(records),
        "records": records,
    }


def format_summary(batch: dict[str, Any]) -> str:
    summary = batch["summary"]
    lines = [
        f"Aurora Confidence Audit: {summary['verdict']}",
        f"- Records: {summary['record_count']}",
        f"- User alerts: {summary['user_alert_count']}",
        f"- Score range: {summary['minimum_score']}..{summary['maximum_score']}",
        f"- Thresholds: {', '.join(str(item) for item in summary['thresholds']) or 'none'}",
    ]
    for claim_type, count in sorted(summary["claim_type_counts"].items()):
        lines.append(f"- {claim_type}: {count}")
    return "\n".join(lines)


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def write_report(path: Path, batch: dict[str, Any]) -> None:
    write_json(path, batch)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Attach confidence scores and alert metadata to Aurora conclusions, analyses, predictions, and recommendations."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    score = subparsers.add_parser("score", help="Score one structured claim.")
    score.add_argument("--claim-id")
    score.add_argument("--claim-type", choices=sorted(CLAIM_TYPES), default="analysis")
    score.add_argument("--text", required=True)
    score.add_argument("--producer", default="aurora-system")
    score.add_argument("--visibility", choices=sorted(VISIBILITY_VALUES), default="internal")
    score.add_argument("--source-ref")
    score.add_argument("--subject-ref", dest="subject_refs", action="append", default=[])
    score.add_argument("--authority-ref", dest="authority_refs", action="append", default=[])
    score.add_argument("--evidence-ref", dest="evidence_refs", action="append", default=[])
    score.add_argument("--receipt-ref", dest="receipt_refs", action="append", default=[])
    score.add_argument("--assumption", dest="assumptions", action="append", default=[])
    score.add_argument("--uncertainty-factor", dest="uncertainty_factors", action="append", default=[])
    score.add_argument("--contradiction-ref", dest="contradiction_refs", action="append", default=[])
    score.add_argument("--resolution-policy-ref")
    score.add_argument("--evidence-level", choices=sorted(EVIDENCE_LEVEL_BASE), default="inference")
    score.add_argument("--score", type=float, help="Explicit confidence score in [0, 1].")
    score.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    score.add_argument("--calibration-profile", default=DEFAULT_CALIBRATION_PROFILE)
    score.add_argument("--calibration-adjustment", type=float)
    score.add_argument("--generated-at")
    score.add_argument("--summary", action="store_true", help="Print a compact batch summary instead of a single record.")
    score.add_argument("--report-out", help="Write a single-record batch report to this path.")
    score.add_argument("--persist-report", action="store_true", help=f"Write {DEFAULT_REPORT.relative_to(ROOT)}.")
    score.add_argument("--fail-on-alert", action="store_true", help="Exit 2 when the score requires a user alert.")

    audit = subparsers.add_parser("audit", help="Score JSON, JSON array, or JSONL claim records.")
    audit.add_argument("--input", help="Input JSON/JSONL path. Reads stdin if omitted.")
    audit.add_argument("--jsonl", action="store_true", help="Force JSONL input parsing.")
    audit.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    audit.add_argument("--calibration-adjustment", type=float)
    audit.add_argument("--generated-at")
    audit.add_argument("--summary", action="store_true", help="Print a compact text summary instead of JSON.")
    audit.add_argument("--report-out", help="Write the JSON batch report to this path.")
    audit.add_argument("--persist-report", action="store_true", help=f"Write {DEFAULT_REPORT.relative_to(ROOT)}.")
    audit.add_argument("--fail-on-alert", action="store_true", help="Exit 2 when any record requires a user alert.")

    return parser


def claim_from_args(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "claim_id": args.claim_id,
        "claim_type": args.claim_type,
        "text": args.text,
        "producer": args.producer,
        "visibility": args.visibility,
        "source_ref": args.source_ref,
        "subject_refs": args.subject_refs,
        "authority_refs": args.authority_refs,
        "evidence_refs": args.evidence_refs,
        "receipt_refs": args.receipt_refs,
        "assumptions": args.assumptions,
        "uncertainty_factors": args.uncertainty_factors,
        "contradiction_refs": args.contradiction_refs,
        "resolution_policy_ref": args.resolution_policy_ref,
        "evidence_level": args.evidence_level,
        "score": args.score,
        "threshold": args.threshold,
        "calibration_profile": args.calibration_profile,
        "calibration_adjustment": args.calibration_adjustment,
    }


def handle_score(args: argparse.Namespace) -> int:
    record = build_confidence_record(
        claim_from_args(args),
        default_threshold=args.threshold,
        generated_at=args.generated_at,
        calibration_adjustment=args.calibration_adjustment,
    )
    batch = build_batch(
        [claim_from_args(args)],
        default_threshold=args.threshold,
        generated_at=args.generated_at,
        calibration_adjustment=args.calibration_adjustment,
    )
    if args.report_out:
        write_report(Path(args.report_out).expanduser().resolve(), batch)
    if args.persist_report:
        write_report(DEFAULT_REPORT, batch)

    if args.summary:
        print(format_summary(batch))
    else:
        print_json(record)
    return 2 if args.fail_on_alert and record["audit"]["requires_user_alert"] else 0


def handle_audit(args: argparse.Namespace) -> int:
    payloads = parse_json_records(read_input(args.input), jsonl=args.jsonl)
    batch = build_batch(
        payloads,
        default_threshold=args.threshold,
        generated_at=args.generated_at,
        calibration_adjustment=args.calibration_adjustment,
    )
    if args.report_out:
        write_report(Path(args.report_out).expanduser().resolve(), batch)
    if args.persist_report:
        write_report(DEFAULT_REPORT, batch)

    if args.summary:
        print(format_summary(batch))
    else:
        print_json(batch)
    return 2 if args.fail_on_alert and batch["summary"]["user_alert_count"] else 0


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "score":
            return handle_score(args)
        return handle_audit(args)
    except ConfidenceInputError as exc:
        print(f"{TOOL_NAME}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

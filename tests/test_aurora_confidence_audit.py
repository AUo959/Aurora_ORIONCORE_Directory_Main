from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"

sys.path.insert(0, str(TOOLS_ROOT))

import aurora_confidence_audit as confidence  # noqa: E402


def test_low_confidence_recommendation_requires_user_alert() -> None:
    record = confidence.build_confidence_record(
        {
            "claim_type": "recommendation",
            "text": "Promote this draft as canonical immediately.",
            "visibility": "user_facing",
            "score": 0.42,
            "threshold": 0.70,
            "authority_refs": ["docs/example.md"],
        },
        generated_at="2026-05-21T00:00:00Z",
    )

    assert record["confidence"]["score"] == 0.42
    assert record["audit"]["requires_user_alert"] is True
    assert record["audit"]["alert_reason"] == "confidence_below_threshold"
    assert "below threshold" in record["audit"]["user_facing_message"]
    assert record["audit"]["live_runtime_execution"] is False
    assert record["audit"]["nested_repo_mutation"] is False


def test_verified_artifact_with_refs_passes_default_threshold() -> None:
    record = confidence.build_confidence_record(
        {
            "claim_type": "conclusion",
            "text": "The root workspace verification report exists.",
            "evidence_level": "verified_artifact",
            "authority_refs": ["README.md"],
            "evidence_refs": ["reports/analysis/workspace_verify_latest.json"],
        },
        generated_at="2026-05-21T00:00:00Z",
    )

    assert record["confidence"]["score"] >= confidence.DEFAULT_THRESHOLD
    assert record["confidence"]["score_source"] == "rubric_default"
    assert record["audit"]["requires_user_alert"] is False
    assert record["audit"]["alert_level"] == "none"


def test_prediction_without_resolution_policy_is_penalized() -> None:
    record = confidence.build_confidence_record(
        {
            "claim_type": "prediction",
            "text": "The next validation run will pass.",
            "evidence_level": "projection",
            "authority_refs": ["tools/workspace_verify.py"],
            "evidence_refs": ["tests/test_workspace_verify.py"],
        },
        generated_at="2026-05-21T00:00:00Z",
    )

    adjustment_codes = {item["code"] for item in record["confidence"]["adjustments"]}
    assert "prediction_without_resolution_policy" in adjustment_codes
    assert record["audit"]["requires_user_alert"] is True


def test_batch_summary_counts_alerts() -> None:
    batch = confidence.build_batch(
        [
            {
                "claim_type": "analysis",
                "text": "This is a weak inference.",
                "score": 0.40,
            },
            {
                "claim_type": "conclusion",
                "text": "This is supported by a deterministic check.",
                "evidence_level": "deterministic_check",
                "authority_refs": ["tools/workspace_verify.py"],
                "evidence_refs": ["reports/analysis/workspace_verify_latest.json"],
            },
        ],
        generated_at="2026-05-21T00:00:00Z",
    )

    assert batch["artifact_type"] == "confidence_audit_batch"
    assert batch["summary"]["record_count"] == 2
    assert batch["summary"]["user_alert_count"] == 1
    assert batch["summary"]["verdict"] == "alert_required"


def test_cli_audit_jsonl_outputs_batch() -> None:
    input_text = "\n".join(
        [
            json.dumps({"claim_type": "analysis", "text": "Weak analysis", "score": 0.30}),
            json.dumps(
                {
                    "claim_type": "conclusion",
                    "text": "Supported conclusion",
                    "evidence_level": "verified_artifact",
                    "authority_refs": ["README.md"],
                    "evidence_refs": ["reports/analysis/workspace_verify_latest.json"],
                }
            ),
        ]
    )
    result = subprocess.run(
        [
            sys.executable,
            str(TOOLS_ROOT / "aurora_confidence_audit.py"),
            "audit",
            "--jsonl",
            "--generated-at",
            "2026-05-21T00:00:00Z",
        ],
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["summary"]["record_count"] == 2
    assert payload["summary"]["user_alert_count"] == 1
    assert payload["records"][0]["audit"]["requires_user_alert"] is True


def test_cli_score_without_explicit_score_uses_rubric() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(TOOLS_ROOT / "aurora_confidence_audit.py"),
            "score",
            "--claim-type",
            "conclusion",
            "--text",
            "Rubric scoring is available.",
            "--evidence-level",
            "verified_artifact",
            "--authority-ref",
            "docs/AURORA_CONFIDENCE_AUDIT_WORKFLOW_v1.md",
            "--evidence-ref",
            "tools/aurora_confidence_audit.py",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["confidence"]["score_source"] == "rubric_default"
    assert payload["audit"]["requires_user_alert"] is False


def test_report_out_writes_batch(tmp_path: Path) -> None:
    report = tmp_path / "confidence-report.json"
    result = subprocess.run(
        [
            sys.executable,
            str(TOOLS_ROOT / "aurora_confidence_audit.py"),
            "score",
            "--claim-type",
            "analysis",
            "--text",
            "A scored analysis record.",
            "--score",
            "0.75",
            "--report-out",
            str(report),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["artifact_type"] == "confidence_audit_batch"
    assert payload["summary"]["record_count"] == 1


def test_schema_and_contract_load() -> None:
    schema = json.loads((REPO_ROOT / confidence.SCHEMA_REF).read_text(encoding="utf-8"))
    contract = json.loads((REPO_ROOT / confidence.CONTRACT_REF).read_text(encoding="utf-8"))

    assert schema["title"] == "Aurora Confidence Audit Record"
    assert contract["contract_id"] == "aurora_confidence_audit_contract"
    assert contract["schema_path"] == confidence.SCHEMA_REF

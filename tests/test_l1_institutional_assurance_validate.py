from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "l1_institutional_assurance_validate.py"
SPEC = importlib.util.spec_from_file_location("l1_assurance_validator", MODULE_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)

BASE_SHA = "a" * 40


def simulated_event() -> dict:
    return {
        "event_id": "GATE-001A-security-review-rehearsal",
        "run_id": "run-seed-808",
        "canon_status": "current_canon",
        "layer": "L1",
        "execution_mode": "l1_simulated_institutional_rehearsal",
        "evidence_authority": "operational_simulation_evidence",
        "data_treatment": "first_class_operational_data",
        "gate_track": "GATE-001A",
        "real_world_interaction": False,
        "independent_external_assurance": False,
        "substitutes_for_real_world_review": False,
        "provenance": {
            "scenario_id": "external-security-review-v1",
            "baseline_commit": BASE_SHA,
            "tool": "tools/hour_aboard.py",
            "tool_version": "1.0",
            "executed_at": "2026-07-27T05:00:00Z",
            "operator": "Aurora GitHubOps",
            "deterministic": True,
            "seed": 808,
        },
        "institutional_roles": [
            {
                "role_id": "assessor-lead",
                "label": "External Assessor Lead",
                "representation": "simulated_role",
            }
        ],
        "evidence_references": [
            {
                "origin": "simulation_primary_evidence",
                "reference": "reports/simulation/gate-001a/run-seed-808.json",
            }
        ],
    }


def external_event() -> dict:
    return {
        "event_id": "GATE-001B-external-review-2027",
        "run_id": "engagement-001",
        "canon_status": "current_canon",
        "layer": "L1",
        "execution_mode": "real_world_external_engagement",
        "evidence_authority": "independent_external_assurance",
        "data_treatment": "first_class_operational_data",
        "gate_track": "GATE-001B",
        "real_world_interaction": True,
        "independent_external_assurance": True,
        "substitutes_for_real_world_review": False,
        "provenance": {
            "scenario_id": "external-security-review-scope-v2",
            "baseline_commit": BASE_SHA,
            "tool": "external-engagement-record",
            "tool_version": "1.0",
            "executed_at": "2027-01-15T12:00:00Z",
            "operator": "verified-owner",
        },
        "institutional_roles": [
            {
                "role_id": "external-firm",
                "label": "Verified Security Firm",
                "representation": "verified_external_organization",
            }
        ],
        "evidence_references": [
            {
                "origin": "external_primary_evidence",
                "reference": "controlled://engagement/scope-and-findings-001",
            },
            {
                "origin": "simulation_primary_evidence",
                "reference": "reports/simulation/gate-001a/run-seed-808.json",
            },
        ],
    }


def test_committed_simulated_output_is_valid_first_class_data():
    assert validator.validate_event(simulated_event()) == []


def test_external_engagement_with_external_primary_evidence_is_valid():
    assert validator.validate_event(external_event()) == []


def test_simulation_cannot_claim_real_world_interaction_or_assurance():
    event = simulated_event()
    event["real_world_interaction"] = True
    event["independent_external_assurance"] = True
    errors = validator.validate_event(event)
    assert any("real_world_interaction" in error for error in errors)
    assert any("independent_external_assurance" in error for error in errors)


def test_simulation_cannot_be_treated_as_secondary_data():
    event = simulated_event()
    event["data_treatment"] = "reference_data"
    errors = validator.validate_event(event)
    assert any("first_class_operational_data" in error for error in errors)


def test_simulated_roles_cannot_be_relabelled_as_verified_external_entities():
    event = simulated_event()
    event["institutional_roles"][0]["representation"] = "verified_external_organization"
    errors = validator.validate_event(event)
    assert any("not allowed" in error for error in errors)


def test_gate_001b_requires_external_primary_evidence():
    event = external_event()
    event["evidence_references"] = [
        {
            "origin": "simulation_primary_evidence",
            "reference": "reports/simulation/gate-001a/run-seed-808.json",
        }
    ]
    errors = validator.validate_event(event)
    assert any("external_primary_evidence" in error for error in errors)


def test_non_substitution_flag_must_always_be_false():
    event = simulated_event()
    event["substitutes_for_real_world_review"] = True
    errors = validator.validate_event(event)
    assert any("must be false" in error for error in errors)


def test_simulation_requires_replay_provenance():
    event = simulated_event()
    event["provenance"].pop("seed")
    event["provenance"]["deterministic"] = False
    errors = validator.validate_event(event)
    assert any("deterministic=true" in error for error in errors)
    assert any("provenance.seed" in error for error in errors)

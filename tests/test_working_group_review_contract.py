"""Synthetic fixtures only; do not execute historical or current group runtimes."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import uuid

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from working_group_review_contract import ReviewContractError, validate_review_packet  # noqa: E402


def uid(n: int) -> str:
    return str(uuid.UUID(int=n, version=4))


def actor(n: int) -> dict[str, str]:
    return {"id": f"SYNTH.ENTITY.{n:04d}", "kind": "human"}


def resolve(ref: str, kind: str) -> bool:
    return kind == "human" and ref in {
        "SYNTH.ENTITY.0001", "SYNTH.ENTITY.0002", "SYNTH.ENTITY.0003"
    }


def fixture() -> dict:
    group = uid(100)
    return {
        "schema_version": "0.1.0",
        "record_type": "working_group_review_packet",
        "review_status": "pending_review",
        "authority": "none",
        "snapshot": {
            "group_id": group, "name": "Synthetic review group",
            "purpose": "Exercise review contracts", "status": "proposed",
            "version": 0, "member_refs": [actor(1)],
            "created_at": "2026-10-15T18:00:00Z",
            "policy_ref": "TEST.POLICY.1",
            "provenance_ref": "SYNTH.FIXTURE.1",
        },
        "proposed_events": [{
            "event_id": uid(101), "group_id": group, "event_type": "add_member",
            "occurred_at": "2026-10-15T18:01:00Z", "actor_ref": actor(1),
            "member_ref": actor(2), "expected_version": 0, "new_version": 1,
            "consent_receipt_ref": "SYNTH.CONSENT.1",
            "audit_ref": "SYNTH.AUDIT.1"
        }],
    }


def check(packet: dict) -> dict:
    return validate_review_packet(packet, resolve_identity=resolve)


def test_valid_synthetic_packet_does_not_claim_consent_verified():
    result = check(fixture())
    assert result["status"] == "reviewable_synthetic_contract_only"
    assert result["final_hypothetical_version"] == 1
    assert result["consent_verified"] == "no"


def test_missing_consent_reference_rejected():
    p = fixture()
    p["proposed_events"][0]["consent_receipt_ref"] = ""
    with pytest.raises(ReviewContractError, match="consent_receipt_ref"):
        check(p)


def test_stale_version_rejected():
    p = fixture()
    p["proposed_events"][0]["expected_version"] = 9
    with pytest.raises(ReviewContractError, match="stale"):
        check(p)


def test_unknown_member_rejected():
    p = fixture()
    p["proposed_events"][0]["member_ref"] = {"id": "SYNTH.ENTITY.9999", "kind": "human"}
    with pytest.raises(ReviewContractError, match="unresolved identity"):
        check(p)


def test_duplicate_event_rejected():
    p = fixture()
    p["proposed_events"].append(deepcopy(p["proposed_events"][0]))
    with pytest.raises(ReviewContractError, match="duplicate event ID"):
        check(p)


def test_corrupt_snapshot_rejected():
    p = fixture()
    p["snapshot"]["member_refs"] = "not-an-array"
    with pytest.raises(ReviewContractError, match="bounded list"):
        check(p)


def test_future_event_after_dissolution_rejected():
    p = fixture()
    dissolve = deepcopy(p["proposed_events"][0])
    dissolve.update({"event_id": uid(102), "event_type": "dissolve", "member_ref": None, "expected_version": 1, "new_version": 2})
    p["proposed_events"].append(dissolve)
    later = deepcopy(p["proposed_events"][0])
    later.update({"event_id": uid(103), "expected_version": 2, "new_version": 3, "member_ref": actor(3)})
    p["proposed_events"].append(later)
    with pytest.raises(ReviewContractError, match="after hypothetical dissolution"):
        check(p)


def test_untrusted_actor_rejected():
    p = fixture()
    p["proposed_events"][0]["actor_ref"] = {"id": "UNKNOWN", "kind": "human"}
    with pytest.raises(ReviewContractError, match="unresolved identity"):
        check(p)


def test_invented_authority_rejected():
    p = fixture()
    p["authority"] = "canonical"
    with pytest.raises(ReviewContractError, match="review markers"):
        check(p)


def test_bool_versions_and_untrusted_fields_rejected():
    p = fixture()
    p["snapshot"]["version"] = True
    with pytest.raises(ReviewContractError, match="nonnegative"):
        check(p)
    p = fixture()
    p["snapshot"]["owner_has_approved"] = True
    with pytest.raises(ReviewContractError, match="expected exact fields"):
        check(p)

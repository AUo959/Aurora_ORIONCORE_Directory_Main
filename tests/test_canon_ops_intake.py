import hashlib
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from unittest import TestCase

import pytest

from tools import canon_ops_intake as bridge
from tools import canon_ops_journal as journal
from tools import canon_ops_query as query


CHECK = TestCase()
GATES = (
    "evidence", "layer_integrity", "schema_validation", "identity_collision",
    "authorization_approval", "final_reconciliation",
)
ORIGIN = {"repository": "Fixture/Gates", "commit": "b" * 40}


def make_request(request_id="request-one", *, state="approved", operation="create_staging_claim",
                 revision=None):
    approval = {"state": state}
    if state != "pending":
        approval["authority"] = "reviewer"
    request = {
        "version": "1.0",
        "request_id": request_id,
        "submitter": {"system": "QGIA", "actor_id": "forecaster", "relay_id": "l1-relay"},
        "layer": "L1",
        "operation": operation,
        "targets": [{"layer": "L1", "kind": "forecast", "record_id": "forecast-a",
                     "expected_state": revision}],
        "sources": [],
        "approval": approval,
        "execution_mode": "reference",
    }
    subject = bridge.subject_digest(request)
    blobs = {}
    references = {}
    for gate in GATES:
        path = f"gates/{gate}.json"
        payload = {
            "gate": gate, "receipt_id": gate, "subject_sha256": subject, "verdict": "PASS",
        }
        if gate == "authorization_approval":
            payload.update(decision=state, authority=approval.get("authority"))
        if gate == "final_reconciliation":
            payload["recommendation"] = "STAGING"
        data = journal.canonical_json(payload).encode()
        blobs[path] = data
        references[gate] = {"receipt_id": gate, "artifact": {
            **ORIGIN, "layer": "L1", "path": path, "sha256": hashlib.sha256(data).hexdigest(),
        }}
    request["gate_receipts"] = references
    request["content_hash"] = journal.request_digest(request)
    return request, blobs


def validate_fixture(request, read_artifact):
    if journal.request_digest(request) != request["content_hash"]:
        raise bridge.IntakeError("/content_hash: digest mismatch")
    for receipt in request["gate_receipts"].values():
        artifact = receipt["artifact"]
        if hashlib.sha256(read_artifact(artifact)).hexdigest() != artifact["sha256"]:
            raise bridge.IntakeError("/gate_receipts: digest mismatch")


@pytest.fixture
def run_intake(tmp_path):
    path = tmp_path / "staging.db"
    policy = {
        "version": "1.0", "canon_commit": "a" * 40, "approvers": {"L1": ["reviewer"]},
        "gate_origins": {gate: [ORIGIN] for gate in GATES},
        "grants": [
            {"principal": "l1-relay", "actor_id": "forecaster", "system": "QGIA",
             "layer": "L1", "operation": operation}
            for operation in ("create_staging_claim", "amend_staging_claim", "request_promotion_review")
        ],
    }

    def run(request, blobs, **overrides):
        inputs = {
            "policy": policy, "principal": "l1-relay", "journal_path": path,
            "validate": validate_fixture, "read_artifact": lambda ref: blobs[ref["path"]],
            "resolve_target": lambda _: None,
        }
        return bridge.submit(request, **{**inputs, **overrides})

    return run, path, policy


def test_duplicate_delivery_has_one_disposition_and_preserves_gate_receipts(run_intake):
    run, path, _ = run_intake
    request, blobs = make_request()
    with ThreadPoolExecutor(max_workers=2) as executor:
        tasks = [executor.submit(run, request, blobs) for _ in range(2)]
        results = [task.result() for task in tasks]
    CHECK.assertEqual({result["status"] for result in results}, {"ACCEPTED", "DUPLICATE"})
    CHECK.assertEqual(results[0]["receipt"], results[1]["receipt"])
    entry, = journal.read_entries(path)
    CHECK.assertEqual(entry["receipt"]["gate_receipts"], request["gate_receipts"])
    CHECK.assertEqual(journal.read_request(path, request["request_id"]), entry)


def test_same_request_id_with_verified_but_changed_content_conflicts(run_intake):
    run, _, _ = run_intake
    request, blobs = make_request()
    run(request, blobs)
    changed, new_blobs = make_request(state="pending")
    with pytest.raises(journal.JournalError, match="different content"):
        run(changed, new_blobs)


def test_pending_and_rejected_approval_create_receipts_without_staging_records(run_intake):
    run, path, _ = run_intake
    for state, expected in (("pending", "NEEDS_REVIEW"), ("rejected", "REJECTED")):
        response = run(*make_request(state, state=state))
        CHECK.assertEqual(response["status"], expected)
    CHECK.assertEqual(journal.staging_state(journal.read_entries(path)), {})


def test_unauthorized_principal_and_untrusted_gate_origin_fail_closed(run_intake):
    run, path, policy = run_intake
    request, blobs = make_request()
    with pytest.raises(bridge.IntakeError, match="authenticated identity"):
        run(request, blobs, principal="other")
    policy["gate_origins"]["evidence"] = []
    with pytest.raises(bridge.IntakeError, match="/gate_receipts/evidence"):
        run(request, blobs)
    CHECK.assertFalse(path.exists())


def test_tampering_and_valid_receipts_from_a_different_subject_are_rejected(run_intake):
    run, path, _ = run_intake
    request, blobs = make_request()
    wrong_bytes = {**blobs, "gates/evidence.json": b'{}'}
    with pytest.raises(bridge.IntakeError, match="digest mismatch"):
        run(request, wrong_bytes)

    other, other_blobs = make_request("other-subject")
    request["gate_receipts"]["evidence"] = other["gate_receipts"]["evidence"]
    request["content_hash"] = journal.request_digest(request)
    with pytest.raises(bridge.IntakeError, match="another request subject"):
        run(request, {**blobs, "gates/evidence.json": other_blobs["gates/evidence.json"]})
    CHECK.assertFalse(path.exists())


def test_amendment_checks_and_advances_the_current_local_staging_revision(run_intake):
    run, path, _ = run_intake
    initial, blobs = make_request()
    run(initial, blobs)
    prior = {"revision": initial["content_hash"], "certainty": "STAGING"}
    current, current_blobs = make_request("amend", operation="amend_staging_claim", revision=prior)
    CHECK.assertEqual(run(current, current_blobs)["status"], "ACCEPTED")
    again = make_request("stale", operation="amend_staging_claim", revision=prior)
    with pytest.raises(bridge.IntakeError, match="stale CanonRec or staging revision"):
        run(*again)
    state = journal.staging_state(journal.read_entries(path))
    CHECK.assertEqual(state[("L1", "forecast", "forecast-a")]["revision"], current["content_hash"])


def test_pinned_existing_record_blocks_create_with_null_expected_state(run_intake):
    run, path, _ = run_intake
    with pytest.raises(bridge.IntakeError, match="stale CanonRec or staging revision"):
        run(*make_request(), resolve_target=lambda _: {"certainty": "CANON", "revision": "a" * 64})
    CHECK.assertEqual(journal.read_entries(path), [])


def test_journal_rebuild_checks_history_and_reconstructs_state(run_intake, tmp_path):
    run, path, _ = run_intake
    run(*make_request())
    run(*make_request("pending", state="pending"))
    entries = journal.read_entries(path)
    tip = entries[-1]["sha256"]
    tampered = deepcopy(entries)
    tampered[0]["receipt"]["reason"] = "different"
    destination = tmp_path / "reconstructed.db"
    with pytest.raises(journal.JournalError, match="history digest"):
        journal.rebuild(destination, tampered, expected_tip=tip)
    CHECK.assertFalse(destination.exists())
    journal.rebuild(destination, entries, expected_tip=tip)
    CHECK.assertEqual(journal.read_entries(destination), entries)
    CHECK.assertEqual(journal.staging_state(journal.read_entries(destination)), journal.staging_state(entries))


def test_snapshot_lookup_fails_when_canonrec_is_unavailable(tmp_path):
    missing = query.CanonRec(tmp_path / "missing-canonrec")
    with pytest.raises(query.QueryError, match="CanonRec Git data unavailable"):
        bridge.snapshot_targets(missing, {"canon_commit": "a" * 40})

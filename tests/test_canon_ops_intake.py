import hashlib
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from copy import deepcopy
from unittest import TestCase

import pytest

from tools import canon_ops_intake as bridge
from tools import canon_ops_events as events
from tools import canon_ops_journal as journal
from tools import canon_ops_query as query


CHECK = TestCase()
GATES = (
    "evidence", "layer_integrity", "schema_validation", "identity_collision",
    "authorization_approval", "final_reconciliation",
)
ORIGIN = {"repository": "Fixture/Gates", "commit": "b" * 40}


def gate_payload(gate, subject, approval, run, profile):
    payload = {"gate": gate, "receipt_id": gate, "subject_sha256": subject, "verdict": "PASS"}
    if gate == "authorization_approval":
        payload.update(decision=approval["state"], authority=approval.get("authority"))
    if gate == "final_reconciliation":
        payload["recommendation"] = "STAGING"
        if profile is not None:
            payload["entity_profile"] = profile
    if gate == "deterministic_run":
        payload["run"] = run
    return payload


def make_request(
    request_id="request-one", *, state="approved", operation="create_staging_claim",
    revision=None, layer="L1", run=None, sources=None, profile=None,
):
    approval = {"state": state}
    if state != "pending":
        approval["authority"] = "reviewer"
    request = {
        "version": "1.0",
        "request_id": request_id,
        "submitter": {"system": "QGIA", "actor_id": "forecaster", "relay_id": "l1-relay"},
        "layer": layer,
        "operation": operation,
        "targets": [{"layer": layer, "kind": "forecast", "record_id": "forecast-a",
                     "expected_state": revision}],
        "sources": list(sources or []),
        "approval": approval,
        "execution_mode": "deterministic_simulation" if run else "reference",
    }
    subject = bridge.subject_digest(request)
    blobs = {}
    references = {}
    required_gates = (*GATES, "deterministic_run") if run else GATES
    for gate in required_gates:
        path = f"gates/{gate}.json"
        payload = gate_payload(gate, subject, approval, run, profile)
        data = journal.canonical_json(payload).encode()
        blobs[path] = data
        references[gate] = {"receipt_id": gate, "artifact": {
            **ORIGIN, "layer": layer, "path": path, "sha256": hashlib.sha256(data).hexdigest(),
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
    for source in request["sources"]:
        if hashlib.sha256(read_artifact(source)).hexdigest() != source["sha256"]:
            raise bridge.IntakeError("/sources: digest mismatch")


@pytest.fixture
def run_intake(tmp_path):
    path = tmp_path / "staging.db"
    policy = {
        "version": "1.0", "canon_commit": "a" * 40,
        "approvers": {"L1": ["reviewer"], "L2": ["reviewer"]},
        "gate_origins": {gate: [ORIGIN] for gate in (*GATES, "deterministic_run")},
        "grants": [
            {"principal": "l1-relay", "actor_id": "forecaster", "system": "QGIA",
             "layer": layer, "operation": operation}
            for layer in ("L1", "L2")
            for operation in (
                "create_staging_claim", "amend_staging_claim", "request_promotion_review", "attach_outcome",
            )
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


def test_record_provenance_joins_pinned_source_and_exact_target_history(run_intake, monkeypatch):
    run, path, policy = run_intake
    source = {"sha256": "d" * 64, "commit": policy["canon_commit"], "path": "canon/L1/forecast.json"}
    pinned = {"record_id": "forecast-a", "certainty": "STAGING", "source": source}
    monkeypatch.setattr(bridge, "_snapshot_records", lambda *_: lambda _: pinned)
    target = {"layer": "L1", "kind": "forecast", "record_id": "forecast-a"}
    create, create_blobs = make_request(
        revision={"revision": source["sha256"], "certainty": "STAGING"},
    )
    run(create, create_blobs, resolve_target=lambda _: create["targets"][0]["expected_state"])
    run(*make_request("other-layer", layer="L2"))
    amend = make_request(
        "amend", operation="amend_staging_claim",
        revision={"revision": create["content_hash"], "certainty": "STAGING"},
    )
    run(*amend)

    repo = query.CanonRec(path.parent)
    result = bridge.record_provenance(repo, policy, path, target)
    CHECK.assertEqual(result["record"], pinned)
    CHECK.assertEqual([entry["sequence"] for entry in result["entries"]], [1, 3])
    CHECK.assertEqual(result["entries"][1]["request"]["targets"][0]["expected_state"]["revision"],
                      create["content_hash"])
    with pytest.raises(bridge.IntakeError, match="different CanonRec snapshot"):
        bridge.record_provenance(repo, {**policy, "canon_commit": "b" * 40}, path, target)


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


def test_qgia_outcome_links_to_accepted_revision_without_advancing_it(run_intake):
    run, path, _ = run_intake
    origin, blobs = make_request()
    run(origin, blobs)
    state = {"revision": origin["content_hash"], "certainty": "STAGING"}
    source_bytes = b'{"kind":"calibration_fixture"}'
    source = {**ORIGIN, "layer": "L1", "path": "outcome.json",
              "sha256": hashlib.sha256(source_bytes).hexdigest()}
    outcome, artifacts = make_request(
        "qgia-outcome", operation="attach_outcome", revision=state, sources=[source],
    )
    artifacts["outcome.json"] = source_bytes
    registered, = run(outcome, artifacts)["receipt"]["events"]
    CHECK.assertEqual(registered["kind"], "outcome_attachment")
    CHECK.assertEqual(registered["origins"][0]["request_id"], origin["request_id"])
    CHECK.assertEqual(registered["sources"], [source])
    CHECK.assertEqual(journal.staging_state(journal.read_entries(path))[("L1", "forecast", "forecast-a")], state)


def make_run(origin):
    return {
        "version": "1.0", "run_id": "run-fixture",
        "origin_request_id": origin["request_id"], "origin_content_hash": origin["content_hash"],
        "engine_commit": "c" * 40, "seed": 51, "event_count": 3,
        "completed_at": "2026-07-01T06:00:00-04:00",
    }


def test_chronicle_registration_binds_native_receipt_identity(run_intake):
    run_intake_request, path, _ = run_intake
    origin, blobs = make_request(layer="L2")
    run_intake_request(origin, blobs)
    summary = make_run(origin)
    native = {
        "run_id": summary["run_id"], "origin_request_id": origin["request_id"],
        "origin_content_hash": origin["content_hash"], "layer": "L2", "canonical_promotion": False,
        "approval": {"actor": origin["approval"]["authority"], "relay": origin["submitter"]["relay_id"]},
        "layer_gate": {"status": "PASS", "event_count": summary["event_count"]},
        "seed": {"engine": {"commit": summary["engine_commit"]}, "parameters": {"seed": summary["seed"]}},
    }
    semantic = journal.digest(native)
    raw = journal.canonical_json({**native, "semantic_sha256": semantic}).encode()
    source = {**ORIGIN, "layer": "L2", "path": "native-receipt.json", "sha256": hashlib.sha256(raw).hexdigest()}
    revision = {"revision": origin["content_hash"], "certainty": "STAGING"}

    def attachment(run_summary):
        request, artifacts = make_request(
            "register-native", operation="attach_outcome", revision=revision,
            layer="L2", run=run_summary, sources=[source],
        )
        artifacts[source["path"]] = raw
        artifact = request["gate_receipts"]["deterministic_run"]["artifact"]
        gate = gate_payload("deterministic_run", bridge.subject_digest(request), request["approval"], run_summary, None)
        gate["run_receipt"] = source
        data = journal.canonical_json(gate).encode()
        artifacts[artifact["path"]] = data
        artifact["sha256"] = hashlib.sha256(data).hexdigest()
        request["content_hash"] = journal.request_digest(request)
        return request, artifacts

    with pytest.raises(journal.JournalError, match="differs from the approved run"):
        run_intake_request(*attachment({**summary, "seed": summary["seed"] + 1}))
    accepted = run_intake_request(*attachment(summary))
    event, = accepted["receipt"]["events"]
    CHECK.assertEqual(event["source"], source)
    CHECK.assertEqual(event["semantic_sha256"], semantic)
    chronicle, = events.chronicle_atoms(journal.read_entries(path))
    CHECK.assertIn(f"#sha256={source['sha256']}", journal.canonical_json(chronicle))


def test_gumas_registration_and_chronicle_projection_rebuild_from_the_journal(run_intake, tmp_path):
    run, path, _ = run_intake
    origin, blobs = make_request(layer="L2")
    run(origin, blobs)
    state = {"revision": origin["content_hash"], "certainty": "STAGING"}
    request, artifacts = make_request(
        "register-run", operation="attach_outcome", revision=state, layer="L2", run=make_run(origin),
    )
    CHECK.assertEqual(run(request, artifacts)["status"], "ACCEPTED")
    CHECK.assertEqual(run(request, artifacts)["status"], "DUPLICATE")
    history = journal.read_entries(path)
    projection = events.chronicle_atoms(history)
    entry, = projection
    CHECK.assertEqual(entry["tier"], "STAGING")
    CHECK.assertEqual(entry["occurred_at"], "2026-07-01T10:00:00Z")
    CHECK.assertIn("deterministic_run.json", entry["source"])
    restored = tmp_path / "restored.db"
    journal.rebuild(restored, history, expected_tip=history[-1]["sha256"])
    CHECK.assertEqual(events.chronicle_atoms(journal.read_entries(restored)), projection)


def test_gumas_registration_denies_wrong_provenance_and_duplicate_run_ids(run_intake):
    run, path, _ = run_intake
    origin, blobs = make_request(layer="L2")
    run(origin, blobs)
    state = {"revision": origin["content_hash"], "certainty": "STAGING"}
    fields = {"operation": "attach_outcome", "revision": state, "layer": "L2"}
    incorrect = {**make_run(origin), "origin_request_id": "different-request"}
    with pytest.raises(journal.JournalError, match="origin must match"):
        run(*make_request("incorrect", **fields, run=incorrect))
    run(*make_request("register", **fields, run=make_run(origin)))
    with pytest.raises(journal.JournalError, match="already registered"):
        run(*make_request("register-again", **fields, run=make_run(origin)))
    CHECK.assertEqual(len(journal.read_entries(path)), 2)


def test_projection_rejects_changed_journal_records(run_intake):
    run, path, _ = run_intake
    run(*make_request())
    entry, = journal.read_entries(path)
    entry["receipt"]["reason"] = "edited after intake"
    with closing(sqlite3.connect(path)) as connection:
        with connection:
            connection.execute(
                "UPDATE intake SET packet = ? WHERE sequence = 1", (journal.canonical_json(entry),)
            )
    with pytest.raises(journal.JournalError, match="history digest"):
        events.chronicle_atoms(journal.read_entries(path))


def test_receipt_records_advisor_output_and_does_not_recalculate_on_replay(run_intake):
    run, path, _ = run_intake
    profile = {"readiness": 0.9}
    request, blobs = make_request(profile=profile)
    calls = []

    def advisor(supplied, target):
        calls.append((supplied, target))
        return {"recommended_tag": "UNCONFIRMED", "confidence": 0.4}

    first = run(request, blobs, advisor=advisor)
    replay = run(request, blobs, advisor=advisor)
    CHECK.assertEqual(calls, [(profile, "forecast-a")])
    CHECK.assertEqual(replay["status"], "DUPLICATE")
    CHECK.assertEqual(first["receipt"], replay["receipt"])
    CHECK.assertEqual(first["receipt"]["reconciliation_advisory"]["recommended_tag"], "UNCONFIRMED")
    entry, = journal.read_entries(path)
    CHECK.assertEqual(entry["receipt"]["target_updates"][0]["state"]["certainty"], "STAGING")

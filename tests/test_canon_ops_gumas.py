import hashlib
from pathlib import Path
from unittest import TestCase

import pytest

from tools import canon_ops_gumas as gumas
from tools import canon_ops_journal as journal
from tools.canon_ops_intake import subject_digest


CHECK = TestCase()
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def approved(tmp_path):
    repo = gumas.CanonRec(ROOT)
    revision = repo.git("rev-parse", "HEAD").decode().strip()
    source_commit = "a" * 40
    blobs = {}

    def artifact(path, payload):
        content = journal.canonical_json(payload).encode()
        blobs[path] = content
        return {
            "repository": "Fixture/Gumas", "commit": source_commit, "layer": "L2", "path": path,
            "sha256": hashlib.sha256(content).hexdigest(),
        }

    seed = artifact("scenario.json", {
        "version": "1.0", "seed_id": "fixture-42", "forecast_id": "forecast-7",
        "parameters": {"scenario_id": gumas.SCENARIO_ID, "seed": 42, "turns": 5},
        "engine": {"version": gumas.ENGINE_VERSION, "commit": revision},
    })
    identity = {"record_id": "fixture-42", "kind": "scenario_seed", "layer": "L2"}
    proposal = {
        "version": "1.0", "request_id": "origin-42", "layer": "L2", "operation": "create_staging_claim",
        "submitter": {"system": "AuroraOS", "actor_id": "actor-1", "relay_id": "l1-relay"},
        "approval": {"state": "approved", "authority": "reviewer"},
        "targets": [{**identity, "expected_state": None}], "execution_mode": "reference", "sources": [seed],
    }
    gate = artifact("approval.json", {
        "subject_sha256": subject_digest(proposal), "decision": "approved", "authority": "reviewer",
    })
    proposal["gate_receipts"] = {"authorization_approval": {"artifact": gate}}
    proposal["content_hash"] = journal.request_digest(proposal)
    snapshot = "b" * 40
    policy = {
        "canon_commit": snapshot, "engine_commit": revision, "l1_relays": ["l1-relay"],
        "approvers": {"L2": ["reviewer"]},
        "gate_origins": {"authorization_approval": [{"repository": "Fixture/Gumas", "commit": source_commit}]},
    }
    journal_path = tmp_path / "staging.db"
    journal.append_request(journal_path, snapshot, proposal, lambda _: {
        "request_id": proposal["request_id"], "content_hash": proposal["content_hash"],
        "canon_commit": snapshot, "status": "ACCEPTED",
        "target_updates": [{**identity, "state": {"revision": proposal["content_hash"], "certainty": "STAGING"}}],
    })
    spec = {
        "version": "1.0", "layer": "L2", "origin_request_id": proposal["request_id"],
        "origin_content_hash": proposal["content_hash"], "scenario_seed": seed,
    }
    tip = journal.read_entries(journal_path)[-1]["sha256"]

    def prepare(run=None, override=None, expected_tip=None):
        return gumas.prepare_run(
            run or spec, {**policy, **(override or {})}, journal_path, expected_tip or tip,
            lambda reference: blobs[reference["path"]],
        )

    return prepare, spec, blobs, repo


def test_approved_native_run_publishes_and_replays_identical_receipts(approved, tmp_path):
    prepare, _, _, repo = approved
    scope = prepare()
    CHECK.assertEqual(scope, prepare())
    root = tmp_path / "runs"
    run = gumas.execute(scope, repo, root)
    CHECK.assertEqual(run["status"], "COMPLETED")
    receipt = run["receipt"]
    CHECK.assertEqual(receipt["states"]["start"]["turn"], 0)
    CHECK.assertEqual(receipt["states"]["end"]["turn"], 5)
    CHECK.assertGreater(receipt["layer_gate"]["event_count"], 0)
    CHECK.assertFalse(receipt["canonical_promotion"])
    CHECK.assertEqual(gumas.execute(scope, repo, root), {"status": "DUPLICATE", "receipt": receipt})
    replay = gumas.execute(scope, repo, root, replay=True)
    CHECK.assertEqual(replay, {"status": "REPLAY_MATCH", "receipt": receipt})
    state = root / scope["run_id"] / "state.json"
    state.write_bytes(state.read_bytes() + b"\n")
    with pytest.raises(gumas.RunError, match="differs from its receipt"):
        gumas.execute(scope, repo, root)


def test_run_requires_exact_layer_relay_approval_digest_and_engine_pin(approved):
    prepare, spec, blobs, _ = approved
    with pytest.raises(gumas.RunError, match="run/layer"):
        prepare({**spec, "layer": "L1"})
    with pytest.raises(gumas.RunError, match="L1 actor or relay"):
        prepare(override={"l1_relays": []})
    with pytest.raises(gumas.RunError, match="terminal digest"):
        prepare(expected_tip="c" * 64)
    with pytest.raises(gumas.RunError, match="allowed GUMAS engine commit"):
        prepare(override={"engine_commit": "d" * 40})
    blobs["approval.json"] += b" "
    with pytest.raises(gumas.RunError, match="Artifact digest mismatch for approval.json"):
        prepare()

import hashlib
from pathlib import Path
from unittest import TestCase

import pytest

from tools import canon_ops_gumas as gumas
from tools import canon_ops_journal as journal
from tools._workspace_common import git
from tools.canon_ops_intake import subject_digest


CHECK = TestCase()
ROOT = Path(__file__).resolve().parents[1]


def pinned_canonrec(path, status):
    path.mkdir()
    git(["init", "-q"], path)
    entity = path / "canon/L2/entities/fixture.json"
    entity.parent.mkdir(parents=True)
    entity.write_text(journal.canonical_json({
        "entity_kind": "character", "entity_id": "example", "allegiance": "galactic_union", "status": status,
    }), encoding="utf-8")
    git(["add", "."], path)
    git(["-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
         "commit", "--no-gpg-sign", "-qm", "Fabric fixture"], path)
    return gumas.CanonRec(path), git(["rev-parse", "HEAD"], path).stdout.strip()


def stage_fixture(path, snapshot, proposal, identity, certainty):
    proposal["content_hash"] = journal.request_digest(proposal)
    journal.append_request(path, snapshot, proposal, lambda _: {
        "request_id": proposal["request_id"], "content_hash": proposal["content_hash"],
        "canon_commit": snapshot, "status": "ACCEPTED", "target_updates": [
            {**identity, "state": {"revision": proposal["content_hash"], "certainty": certainty}},
        ],
    })


@pytest.fixture
def approved(tmp_path, request):
    repo = gumas.CanonRec(ROOT)
    revision = repo.git("rev-parse", "HEAD").decode().strip()
    source_commit = "a" * 40
    blobs = {}
    overrides = getattr(request, "param", {})

    def artifact(path, payload):
        content = journal.canonical_json(payload).encode()
        blobs[path] = content
        return {
            "repository": "Fixture/Gumas", "commit": source_commit, "layer": "L2", "path": path,
            "sha256": hashlib.sha256(content).hexdigest(),
        }

    seed = artifact("scenario.json", {
        "version": "1.0", "seed_id": "fixture-42", "forecast_id": "forecast-7",
        "parameters": {"scenario_id": gumas.SCENARIO_ID, "seed": 42, "turns": 5, "fabric_domain": "union"},
        "engine": {"version": overrides.get("engine_version", gumas.ENGINE_VERSION), "commit": revision},
    })
    identity = {"record_id": "fixture-42", "kind": "scenario_seed", "layer": "L2"}
    proposal = {
        "version": "1.0", "request_id": "origin-42", "layer": "L2", "operation": "create_staging_claim",
        "submitter": overrides.get(
            "submitter", {"system": "AuroraOS", "actor_id": "actor-1", "relay_id": "l1-relay"},
        ),
        "approval": {"state": overrides.get("approval", "approved"), "authority": "reviewer"},
        "targets": [{**identity, "expected_state": None}], "execution_mode": "reference", "sources": [seed],
    }
    gate = artifact("approval.json", {
        "subject_sha256": subject_digest(proposal), "decision": proposal["approval"]["state"], "authority": "reviewer",
    })
    proposal["gate_receipts"] = {"authorization_approval": {"artifact": gate}}
    canonrec, snapshot = pinned_canonrec(tmp_path / "canonrec", overrides.get("canon_status", "active"))
    policy = {
        "canon_commit": snapshot, "engine_commit": revision, "l1_relays": ["l1-relay"],
        "approvers": {"L2": ["reviewer"]},
        "gate_origins": {"authorization_approval": [{"repository": "Fixture/Gumas", "commit": source_commit}]},
    }
    journal_path = tmp_path / "staging.db"
    stage_fixture(journal_path, snapshot, proposal, identity, "STAGING")
    if overrides.get("superseded"):
        withdrawn = {**proposal, "request_id": "withdraw-fixture", "operation": "supersede_staging_record"}
        stage_fixture(journal_path, snapshot, withdrawn, identity, "SUPERSEDED")
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

    return prepare, spec, blobs, repo, canonrec


def test_approved_native_run_publishes_and_replays_identical_receipts(approved, tmp_path):
    prepare, _, _, repo, canonrec = approved
    scope = prepare()
    CHECK.assertEqual(scope, prepare())
    root = tmp_path / "runs"
    run = gumas.execute(scope, repo, canonrec, root)
    CHECK.assertEqual(run["status"], "COMPLETED")
    receipt = run["receipt"]
    CHECK.assertEqual(receipt["states"]["start"]["turn"], 0)
    CHECK.assertEqual(receipt["states"]["end"]["turn"], 5)
    CHECK.assertGreater(receipt["layer_gate"]["event_count"], 0)
    CHECK.assertFalse(receipt["canonical_promotion"])
    CHECK.assertEqual(receipt["fabric_invariants"]["counts"]["VIOLATION"], 0)
    CHECK.assertEqual(gumas.execute(scope, repo, canonrec, root), {"status": "DUPLICATE", "receipt": receipt})
    replay = gumas.execute(scope, repo, canonrec, root, replay=True)
    CHECK.assertEqual(replay, {"status": "REPLAY_MATCH", "receipt": receipt})
    state = root / scope["run_id"] / "state.json"
    state.write_bytes(state.read_bytes() + b"\n")
    with pytest.raises(gumas.RunError, match="differs from its receipt"):
        gumas.execute(scope, repo, canonrec, root)


def test_run_requires_exact_layer_relay_approval_digest_and_engine_pin(approved):
    prepare, spec, blobs, _, _ = approved
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


@pytest.mark.parametrize("approved", [{"canon_status": ["active", "deceased"]}], indirect=True)
def test_fabric_violation_requires_review_without_publishing_output(approved, tmp_path):
    prepare, _, _, repo, canonrec = approved
    scope = prepare()
    root = tmp_path / "runs"
    with pytest.raises(gumas.FabricReview) as exc:
        gumas.execute(scope, repo, canonrec, root)
    CHECK.assertEqual(exc.value.findings["counts"]["VIOLATION"], 1)
    CHECK.assertFalse((root / scope["run_id"]).exists())


@pytest.mark.parametrize("approved", [{"submitter": {"system": "QGIA", "actor_id": "l1-relay"}}], indirect=True)
def test_direct_qgia_cannot_execute_an_approved_staging_seed(approved):
    prepare, *_ = approved
    with pytest.raises(gumas.RunError, match="L1 actor or relay"):
        prepare()


@pytest.mark.parametrize(("approved", "finding"), [
    ({"superseded": True}, "absent or stale"),
    ({"approval": "rejected"}, "lacks approval"),
    ({"engine_version": "unsupported"}, "scenario_seed/engine/version"),
], indirect=["approved"])
def test_ineligible_seed_is_rejected_before_execution(approved, finding):
    prepare, *_ = approved
    with pytest.raises(gumas.RunError, match=finding):
        prepare()


def test_interrupted_run_can_retry_without_partial_publication(approved, tmp_path, monkeypatch):
    prepare, _, _, repo, canonrec = approved
    scope = prepare()
    root = tmp_path / "runs"

    def interrupt(_workspace, output, _seed, _turns):
        output.parent.mkdir(exist_ok=True)
        output.write_text("partial", encoding="utf-8")
        raise gumas.RunError("interrupted fixture")

    with monkeypatch.context() as scoped:
        scoped.setattr(gumas, "_run_engine", interrupt)
        with pytest.raises(gumas.RunError, match="interrupted fixture"):
            gumas.execute(scope, repo, canonrec, root)
    CHECK.assertFalse((root / scope["run_id"]).exists())
    CHECK.assertEqual(gumas.execute(scope, repo, canonrec, root)["status"], "COMPLETED")

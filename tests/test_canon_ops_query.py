import hashlib
import json

from jsonschema import Draft202012Validator
import pytest

from tools import canon_ops_query as bridge
from tools._workspace_common import git


def put(repo_path, path, data):
    target = repo_path / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(data, encoding="utf-8")


def commit(repo_path):
    git(["add", "."], repo_path)
    git(
        [
            "-c", "user.name=Test", "-c",
            "user.email=test@example.invalid", "commit", "--no-gpg-sign", "-qm", "Fixture",
        ],
        repo_path,
    )
    return git(["rev-parse", "HEAD"], repo_path).stdout.strip()


@pytest.fixture
def snapshot(tmp_path, monkeypatch):
    git(["init", "-q"], tmp_path)
    put(tmp_path, "canon/L2/entities/01.json", json.dumps({
        "entity_id": "vessel-a", "vessel_id": "VSL-A", "entity_kind": "vessel",
        "certainty": "CANON", "aliases": ["Dawn"], "captain_id": "person-a",
    }))
    put(tmp_path, "canon/L2/entities/02.json", json.dumps({
        "entity_id": "vessel-b", "entity_kind": "vessel", "certainty": "CANON",
    }))
    put(tmp_path, "canon/L1/station/chronicle/chronicle.ndjson", "\n".join(
        json.dumps({"event_id": event_id, "occurred_at": date})
        for event_id, date in (("event-a", "2026-01-01T00:00:00Z"), ("event-b", "2026-02-01T00:00:00Z"))
    ))
    sha = commit(tmp_path)
    # Actual pinned schemas are exercised against CanonRec separately. Each
    # isolated fixture here tests Git reads and query semantics without a clone.
    validator = Draft202012Validator({"type": "object"})
    monkeypatch.setattr(bridge, "_validator_pair", lambda *_: (validator, validator))
    return bridge.CanonRec(tmp_path), {
        "version": "1.0", "query_id": "vessels", "idempotency_key": "vessels-read",
        "layer": "L2", "commit": sha, "source_paths": ["canon/L2/entities"],
        "page": {"limit": 1},
    }


def test_query_pins_blob_bytes_and_paginates(snapshot):
    repo, request = snapshot
    path = "canon/L2/entities/01.json"
    committed = repo.blob(f"{request['commit']}:{path}")
    put(repo.path, path, '{"entity_id": "working-tree-only"}')
    first = bridge.query(repo, request)
    item, = first["results"]["canonical_facts"]
    assert item["record_id"] == "vessel-a"  # nosec B101 - pytest assertion
    assert item["source"] == {  # nosec B101 - pytest assertion
        "commit": request["commit"], "layer": "L2", "path": path,
        "repository": "AUo959/CanonRec", "sha256": hashlib.sha256(committed).hexdigest(),
    }
    request["page"]["after"] = first["next_after"]
    second = bridge.query(repo, request)
    assert [item["record_id"] for item in second["results"]["canonical_facts"]] == ["vessel-b"]  # nosec B101 - pytest assertion
    assert second["next_after"] is None  # nosec B101 - pytest assertion


def test_query_combines_identity_alias_and_relationship_filters(snapshot):
    repo, request = snapshot
    request["filters"] = {
        "entity_ids": ["vessel-a"], "aliases": ["vsl-a"], "certainty_states": ["CANON"],
        "relationships": [{"kind": "captain_id", "target_id": "person-a"}],
    }
    result = bridge.query(repo, request)
    assert [item["record_id"] for item in result["results"]["canonical_facts"]] == ["vessel-a"]  # nosec B101 - pytest assertion
    assert result["next_after"] is None  # nosec B101 - pytest assertion


def test_query_chronicle_date_bounds_preserve_operational_classification(snapshot):
    repo, request = snapshot
    request.update(layer="L1", source_paths=["canon/L1/station/chronicle"])
    request["filters"] = {"since": "2026-02-01T00:00:00Z", "until": "2026-02-01T00:00:00Z"}
    result = bridge.query(repo, request)
    item, = result["results"]["operational_atoms"]
    assert item["record_id"] == "event-b"  # nosec B101 - pytest assertion
    assert item["certainty"] == "UNCONFIRMED"  # nosec B101 - pytest assertion
    assert result["results"]["canonical_facts"] == []  # nosec B101 - pytest assertion


def test_query_rejects_scope_in_a_different_layer(snapshot):
    repo, request = snapshot
    request["source_paths"].append("canon/L1/station")
    with pytest.raises(bridge.QueryError, match="/source_paths/1"):
        bridge.query(repo, request)


def test_query_reports_unavailable_commit(snapshot):
    repo, request = snapshot
    request["commit"] = "f" * 40
    with pytest.raises(bridge.QueryError, match="Git data unavailable"):
        bridge.query(repo, request)

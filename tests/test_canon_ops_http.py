import hashlib
import json
import secrets
from unittest import TestCase

import pytest
from jsonschema import Draft202012Validator

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from tools import canon_ops_http, canon_ops_journal, canon_ops_query
from tools._workspace_common import git


CHECK = TestCase()
TOKEN = secrets.token_urlsafe(32)  # per-run fixture bearer, never a stored credential
HEADERS = {"Authorization": f"Bearer {TOKEN}"}


@pytest.fixture
def reader(tmp_path, monkeypatch):
    repo = tmp_path / "canonrec"
    repo.mkdir()
    git(["init", "-q"], repo)
    path = repo / "canon/L2/entities/fixture.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"kind": "character", "record_id": "fixture", "certainty": "CANON"}), encoding="utf-8")
    git(["add", "."], repo)
    git(["-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
         "commit", "--no-gpg-sign", "-qm", "CanonRec fixture"], repo)
    snapshot = git(["rev-parse", "HEAD"], repo).stdout.strip()
    journal = tmp_path / "staging.db"
    request = {"request_id": "fixture-request", "layer": "L2", "targets": []}
    request["content_hash"] = canon_ops_journal.request_digest(request)
    canon_ops_journal.append_request(journal, snapshot, request, lambda _: {
        "request_id": request["request_id"], "content_hash": request["content_hash"],
        "canon_commit": snapshot, "status": "NEEDS_REVIEW", "target_updates": [],
    })
    validator = Draft202012Validator({"type": "object"})
    monkeypatch.setattr(canon_ops_query, "_validator_pair", lambda *_: (validator, validator))
    app = canon_ops_http.create_app(
        canonrec=canon_ops_query.CanonRec(repo), journal_path=journal,
        policy={"canon_commit": snapshot, "target_paths": {"L2": ["canon/L2/entities"]}},
        principals=[{"principal": "reader", "token_sha256": hashlib.sha256(TOKEN.encode()).hexdigest(),
                     "scopes": ["ace:read"], "authority_refs": []}],
        browser_origins=("http://localhost:4177",),
    )
    query = {"version": "1.0", "query_id": "fixture-query", "layer": "L2", "commit": snapshot,
             "source_paths": ["canon/L2/entities"], "page": {"limit": 1}}
    return TestClient(app, base_url="http://127.0.0.1"), query


def test_query_authenticates_and_keeps_the_configured_snapshot_and_scope(reader):
    client, query = reader
    CHECK.assertEqual(client.post("/v1/query", json=query).status_code, 401)
    reply = client.post("/v1/query", json=query, headers=HEADERS)
    CHECK.assertEqual(reply.status_code, 200)
    record, = reply.json()["results"]["canonical_facts"]
    CHECK.assertEqual(record["source"]["commit"], query["commit"])
    CHECK.assertEqual(record["certainty"], "CANON")
    wrong_ref = client.post("/v1/query", json={**query, "commit": "a" * 40}, headers=HEADERS)
    CHECK.assertEqual(wrong_ref.json()["detail"]["code"], "snapshot_denied")
    wrong_path = client.post("/v1/query", json={**query, "source_paths": ["canon/L2"]}, headers=HEADERS)
    CHECK.assertEqual(wrong_path.json()["detail"]["code"], "path_denied")


def test_provenance_status_and_unknown_results_are_read_only(reader):
    client, _ = reader
    target = {"layer": "L2", "kind": "character", "record_id": "fixture"}
    provenance = client.post("/v1/provenance", json=target, headers=HEADERS).json()
    CHECK.assertEqual(provenance["record"]["record_id"], "fixture")
    status = client.post("/v1/status", json={"request_id": "fixture-request"}, headers=HEADERS)
    CHECK.assertEqual(status.json()["receipt"]["status"], "NEEDS_REVIEW")
    missing = client.post("/v1/status", json={"request_id": "unknown"}, headers=HEADERS)
    CHECK.assertEqual(missing.status_code, 404)
    CHECK.assertEqual(missing.json()["detail"]["code"], "unknown")
    CHECK.assertEqual(client.post("/v1/submit", json={}, headers=HEADERS).status_code, 404)


def test_reader_rejects_invalid_bodies_and_browser_origins(reader):
    client, _ = reader
    reply = client.post("/v1/query", content=b'{"layer":"L2","layer":"L1"}', headers=HEADERS)
    CHECK.assertEqual(reply.json()["detail"]["code"], "invalid_json")
    oversized = client.post("/v1/query", content=b" " * (canon_ops_http.MAX_REQUEST_BYTES + 1), headers=HEADERS)
    CHECK.assertEqual(oversized.status_code, 413)
    for origin, expected in (("http://localhost:4177", 200), ("https://example.invalid", 400)):
        response = client.options("/v1/query", headers={"Origin": origin, "Access-Control-Request-Method": "POST"})
        CHECK.assertEqual(response.status_code, expected)

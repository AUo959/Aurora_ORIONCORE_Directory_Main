from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from ace import remote_service, runtime_binding  # noqa: E402
from ace.remote_auth import RemoteAuthError, load_remote_principals  # noqa: E402

TOKEN = "ace-test-token-not-a-secret"
TOKEN_SHA = hashlib.sha256(TOKEN.encode()).hexdigest()
AUTHORITY_REF = "owner:test:ace-v0.12"


def principal_env(*, scopes: list[str] | None = None, authority_refs: list[str] | None = None) -> dict[str, str]:
    return {
        "ACE_REMOTE_PRINCIPALS_JSON": json.dumps(
            [
                {
                    "principal": "test-agent",
                    "token_sha256": TOKEN_SHA,
                    "scopes": scopes or ["ace:read", "ace:resolve"],
                    "authority_refs": authority_refs or [],
                }
            ]
        )
    }


def auth_header(token: str = TOKEN) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _expect(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def test_remote_auth_requires_hash_only_configuration() -> None:
    bad = {
        "ACE_REMOTE_PRINCIPALS_JSON": json.dumps(
            [{"principal": "x", "token": "plaintext", "token_sha256": TOKEN_SHA, "scopes": ["ace:read"]}]
        )
    }
    with pytest.raises(RemoteAuthError):
        load_remote_principals(bad)


def test_remote_service_requires_auth_and_binds_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(remote_service, "_ace_capabilities", lambda **kwargs: {"record_type": "test-capabilities"})
    app = remote_service.create_app(environ=principal_env())
    client = TestClient(app)

    assert client.get("/healthz").status_code == 200
    assert client.get("/v1/capabilities").status_code == 401
    assert client.get("/v1/capabilities", headers=auth_header("wrong")).status_code == 401
    response = client.get("/v1/capabilities", headers=auth_header())
    assert response.status_code == 200
    assert response.json()["remote_principal"] == "test-agent"
    assert response.json()["transport"] == "https_json"


def test_remote_materialization_requires_scope_and_bound_authority(monkeypatch: pytest.MonkeyPatch) -> None:
    app = remote_service.create_app(
        environ=principal_env(scopes=["ace:materialize"], authority_refs=[AUTHORITY_REF])
    )
    client = TestClient(app)

    denied = client.post(
        "/v1/materialize/preview",
        headers=auth_header(),
        json={"output_name": "packet", "authority_ref": "owner:other"},
    )
    assert denied.status_code == 403

    monkeypatch.setattr(
        remote_service,
        "_ace_materialize_preview",
        lambda output_name, authority_ref, **kwargs: {
            "record_type": "preview",
            "output_name": output_name,
            "authority_ref": authority_ref,
        },
    )
    allowed = client.post(
        "/v1/materialize/preview",
        headers=auth_header(),
        json={"output_name": "packet", "authority_ref": AUTHORITY_REF},
    )
    assert allowed.status_code == 200
    assert allowed.json()["authority_ref"] == AUTHORITY_REF


def test_remote_autonomic_mode_requires_explicit_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(remote_service, "validate_invocation_envelope", lambda value: None)
    invocation = {
        "invocation_mode": "autonomic",
        "query": {"record_type": "ace_query_envelope"},
        "caller": {"parent_invocation_ref": None},
        "trigger": {
            "kind": "coherence_seam",
            "reason": "test",
            "seam_ref": "seam:test",
            "trigger_policy_ref": "policy:test",
        },
    }
    with pytest.raises(RemoteAuthError):
        remote_service._bind_remote_invocation(
            invocation,
            {"principal": "test-agent", "scopes": ["ace:resolve"], "authority_refs": []},
        )


def test_remote_delegated_publication_requires_scope_intersection_and_authority(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_publisher(output_name: str, authority_ref: str, principal: dict, **kwargs):
        return {
            "record_type": "ace_delegated_publication_receipt",
            "status": "review_pending",
            "output_name": output_name,
            "authority_ref": authority_ref,
            "authenticated_principal": principal["principal"],
            "mainline_canon_advanced": False,
        }

    monkeypatch.setattr(remote_service, "_delegated_publisher", lambda root: fake_publisher)

    partial = remote_service.create_app(
        environ=principal_env(scopes=["ace:publish"], authority_refs=[AUTHORITY_REF])
    )
    denied_scopes = TestClient(partial).post(
        "/v1/publish/delegated",
        headers=auth_header(),
        json={"output_name": "packet", "authority_ref": AUTHORITY_REF},
    )
    _expect(denied_scopes.status_code == 403, "ace:publish alone must not authorize delegated publication")

    full_scopes = ["ace:publish", "ace:autonomic", "ace:materialize"]
    bound = remote_service.create_app(
        environ=principal_env(scopes=full_scopes, authority_refs=[AUTHORITY_REF])
    )
    denied_authority = TestClient(bound).post(
        "/v1/publish/delegated",
        headers=auth_header(),
        json={"output_name": "packet", "authority_ref": "owner:other"},
    )
    _expect(denied_authority.status_code == 403, "unbound authority_ref must be refused")

    allowed = TestClient(bound).post(
        "/v1/publish/delegated",
        headers=auth_header(),
        json={"output_name": "packet", "authority_ref": AUTHORITY_REF},
    )
    body = allowed.json()
    _expect(allowed.status_code == 200, "fully authorized publication call should reach verified publisher")
    _expect(body["status"] == "review_pending", "delegated publication must remain review pending")
    _expect(body["authenticated_principal"] == "test-agent", "publication receipt must bind authenticated principal")
    _expect(body["mainline_canon_advanced"] is False, "remote publication must not advance main")
    _expect(body["transport"] == "https_json", "remote publication must identify transport")


def test_runtime_binding_registry_pins_exact_source_blobs() -> None:
    registry = runtime_binding.load_runtime_binding_registry(root=REPO_ROOT)
    assert set(registry) == {
        "ace.capability.invoke.character.retrieve",
        "ace.capability.invoke.character.complete",
        "ace.capability.invoke.facility",
        "ace.capability.invoke.canon_fact",
        "ace.capability.invoke.entity.complete",
        "ace.capability.canonrec.publish.delegated_pr",
    }
    for binding in registry.values():
        source = REPO_ROOT / binding["path"]
        assert runtime_binding._git_blob_sha(source) == binding["git_blob_sha"]


def test_runtime_binding_rejects_catalog_only_arbitrary_python(tmp_path: Path) -> None:
    payload = {
        "schema_version": "1.0.0",
        "record_type": "ace_verified_runtime_binding_registry",
        "bindings": [
            {
                "capability_id": "ace.capability.evil",
                "repository": "root",
                "path": "tools/ace/core.py",
                "module": "os",
                "callable": "system",
                "git_blob_sha": "0" * 40,
            }
        ],
    }
    path = tmp_path / "bindings.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(Exception):
        runtime_binding.load_runtime_binding_registry(root=REPO_ROOT, binding_path=path)

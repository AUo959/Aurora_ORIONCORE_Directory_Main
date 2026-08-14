"""Authentication policy for the ACE remote service.

Secrets are never read from repository files. Operators provide a JSON array in
ACE_REMOTE_PRINCIPALS_JSON containing only SHA-256 token digests, principal
identifiers, scopes, and optional materialization authority references.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from typing import Any, Mapping

from .core import ACEError

REMOTE_PRINCIPALS_ENV = "ACE_REMOTE_PRINCIPALS_JSON"
KNOWN_SCOPES = frozenset({"ace:read", "ace:resolve", "ace:materialize", "ace:autonomic", "ace:runtime"})
_PRINCIPAL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:@/-]{0,127}$")
_SHA256 = re.compile(r"^[a-f0-9]{64}$")


class RemoteAuthError(ACEError):
    def __init__(self, message: str, *, code: str = "remote_auth_failed", status_code: int = 401) -> None:
        super().__init__(message, code=code)
        self.status_code = status_code


def load_remote_principals(environ: Mapping[str, str] | None = None) -> list[dict[str, Any]]:
    env = environ or os.environ
    raw = env.get(REMOTE_PRINCIPALS_ENV)
    if not raw:
        raise RemoteAuthError(
            f"{REMOTE_PRINCIPALS_ENV} is required before ACE remote service startup",
            code="remote_auth_unconfigured",
            status_code=503,
        )
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RemoteAuthError("ACE remote principal configuration is invalid JSON", code="remote_auth_unconfigured", status_code=503) from exc
    if not isinstance(payload, list) or not payload:
        raise RemoteAuthError("ACE remote principal configuration must be a non-empty array", code="remote_auth_unconfigured", status_code=503)

    seen_principals: set[str] = set()
    seen_digests: set[str] = set()
    out: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, Mapping):
            raise RemoteAuthError("ACE remote principal entry must be an object", code="remote_auth_unconfigured", status_code=503)
        if "token" in item or "secret" in item:
            raise RemoteAuthError("ACE remote config must contain token digests, never plaintext secrets", code="remote_auth_unconfigured", status_code=503)
        principal = item.get("principal")
        digest = item.get("token_sha256")
        scopes = item.get("scopes")
        authority_refs = item.get("authority_refs", [])
        if not isinstance(principal, str) or _PRINCIPAL.fullmatch(principal) is None:
            raise RemoteAuthError("ACE remote principal identifier is invalid", code="remote_auth_unconfigured", status_code=503)
        if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
            raise RemoteAuthError("ACE remote token_sha256 must be a lowercase SHA-256 digest", code="remote_auth_unconfigured", status_code=503)
        if not isinstance(scopes, list) or not scopes or any(scope not in KNOWN_SCOPES for scope in scopes):
            raise RemoteAuthError("ACE remote principal has invalid scopes", code="remote_auth_unconfigured", status_code=503)
        if not isinstance(authority_refs, list) or any(not isinstance(ref, str) or not ref.strip() for ref in authority_refs):
            raise RemoteAuthError("ACE remote materialization authority_refs are invalid", code="remote_auth_unconfigured", status_code=503)
        if principal in seen_principals or digest in seen_digests:
            raise RemoteAuthError("ACE remote principal configuration contains duplicate identity/token material", code="remote_auth_unconfigured", status_code=503)
        seen_principals.add(principal)
        seen_digests.add(digest)
        out.append(
            {
                "principal": principal,
                "token_sha256": digest,
                "scopes": sorted(set(scopes)),
                "authority_refs": sorted(set(ref.strip() for ref in authority_refs)),
            }
        )
    return out


def authenticate_bearer(
    authorization_header: str | None,
    required_scope: str,
    *,
    principals: list[dict[str, Any]] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    if required_scope not in KNOWN_SCOPES:
        raise RemoteAuthError("ACE remote endpoint requested an unknown scope", code="remote_auth_policy_error", status_code=500)
    if not isinstance(authorization_header, str) or not authorization_header.startswith("Bearer "):
        raise RemoteAuthError("ACE remote service requires Bearer authentication")
    token = authorization_header[7:].strip()
    if not token or len(token) > 4096:
        raise RemoteAuthError("ACE remote bearer token is malformed")
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    configured = principals if principals is not None else load_remote_principals(environ)
    selected = None
    for principal in configured:
        if hmac.compare_digest(digest, principal["token_sha256"]):
            selected = principal
    if selected is None:
        raise RemoteAuthError("ACE remote bearer token is not recognized")
    if required_scope not in selected["scopes"]:
        raise RemoteAuthError(
            f"ACE remote principal lacks required scope {required_scope}",
            code="remote_scope_denied",
            status_code=403,
        )
    return {
        "principal": selected["principal"],
        "scopes": list(selected["scopes"]),
        "authority_refs": list(selected["authority_refs"]),
        "authenticated": True,
    }

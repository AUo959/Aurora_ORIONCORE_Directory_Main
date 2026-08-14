"""Authenticated HTTP transport for the Aurora Canon Engine (ACE).

This module is a transport adapter. It does not implement a second resolver,
truth model, materializer, or runtime. Every request is authenticated, rebound
to the authenticated principal, and delegated to existing ACE contracts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from fastapi import FastAPI, HTTPException, Request

from .core import ACEError, ROOT
from .invocation import build_invocation_envelope, validate_invocation_envelope
from .mcp_adapter import (
    _safe_output_dir,
    ace_capabilities as _ace_capabilities,
    ace_inspect as _ace_inspect,
    ace_materialize_commit as _ace_materialize_commit,
    ace_materialize_preview as _ace_materialize_preview,
    ace_plan as _ace_plan,
)
from .remote_auth import RemoteAuthError, authenticate_bearer, load_remote_principals
from .runtime_binding import resolve_verified_invocation

REMOTE_SERVICE_VERSION = "0.10.0"
REMOTE_RUNTIME_REL = Path("reports/ace/remote_runtime")
MAX_REQUEST_BYTES = 1_048_576


def _remote_runtime_root(root: Path = ROOT) -> Path:
    root_resolved = root.resolve()
    target = (root_resolved / REMOTE_RUNTIME_REL).resolve()
    if target == root_resolved or root_resolved not in target.parents:
        raise ACEError("ACE remote runtime root escaped OrionCore", code="target_unavailable")
    return target


def _bind_remote_invocation(invocation: Mapping[str, Any], principal: Mapping[str, Any]) -> dict[str, Any]:
    validate_invocation_envelope(invocation)
    mode = str(invocation["invocation_mode"])
    if mode == "autonomic" and "ace:autonomic" not in principal["scopes"]:
        raise RemoteAuthError(
            "ACE remote autonomic invocation requires ace:autonomic scope",
            code="remote_scope_denied",
            status_code=403,
        )
    caller_ref = f"remote:{principal['principal']}"
    trigger = invocation["trigger"]
    caller = invocation["caller"]
    return build_invocation_envelope(
        invocation["query"],
        invocation_mode=mode,
        caller_kind="agent",
        caller_ref=caller_ref,
        parent_invocation_ref=caller.get("parent_invocation_ref"),
        trigger_kind=trigger.get("kind"),
        trigger_reason=trigger.get("reason"),
        seam_ref=trigger.get("seam_ref"),
        trigger_policy_ref=trigger.get("trigger_policy_ref"),
    )


def _authority_allowed(principal: Mapping[str, Any], authority_ref: str) -> None:
    if authority_ref not in principal.get("authority_refs", []):
        raise RemoteAuthError(
            "authenticated ACE remote principal is not bound to the requested authority_ref",
            code="remote_authority_ref_denied",
            status_code=403,
        )


def _http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, RemoteAuthError):
        return HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": str(exc)})
    if isinstance(exc, ACEError):
        return HTTPException(status_code=409, detail={"code": exc.code, "message": str(exc)})
    return HTTPException(status_code=500, detail={"code": "remote_runtime_failure", "message": str(exc)})


def create_app(*, environ: Mapping[str, str] | None = None, root: Path = ROOT) -> FastAPI:
    principals = load_remote_principals(environ)
    runtime_root = _remote_runtime_root(root)
    app = FastAPI(
        title="Aurora Canon Engine",
        version=REMOTE_SERVICE_VERSION,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    @app.middleware("http")
    async def request_limit(request: Request, call_next):  # type: ignore[no-untyped-def]
        raw_length = request.headers.get("content-length")
        if raw_length is not None:
            try:
                length = int(raw_length)
            except ValueError:
                return HTTPException(status_code=400, detail="invalid content-length")
            if length > MAX_REQUEST_BYTES:
                from fastapi.responses import JSONResponse
                return JSONResponse(status_code=413, content={"detail": {"code": "request_too_large", "message": "ACE remote request exceeds 1 MiB"}})
        return await call_next(request)

    def auth(request: Request, scope: str) -> dict[str, Any]:
        return authenticate_bearer(request.headers.get("authorization"), scope, principals=principals)

    @app.get("/healthz")
    def healthz() -> dict[str, Any]:
        return {
            "status": "ok",
            "service": "aurora-ace",
            "version": REMOTE_SERVICE_VERSION,
            "authentication": "required_for_v1",
            "canonical_authority": "unchanged",
        }

    @app.get("/v1/capabilities")
    def capabilities(request: Request) -> dict[str, Any]:
        try:
            principal = auth(request, "ace:read")
            payload = _ace_capabilities(root=root)
            payload["remote_principal"] = principal["principal"]
            payload["transport"] = "https_json"
            return payload
        except Exception as exc:
            raise _http_error(exc) from exc

    @app.post("/v1/plan")
    def plan(payload: dict[str, Any], request: Request) -> dict[str, Any]:
        try:
            principal = auth(request, "ace:read")
            bound = _bind_remote_invocation(payload["invocation"], principal)
            result = _ace_plan(bound)
            result["remote_principal"] = principal["principal"]
            result["transport"] = "https_json"
            return result
        except Exception as exc:
            raise _http_error(exc) from exc

    @app.post("/v1/resolve")
    def resolve(payload: dict[str, Any], request: Request) -> dict[str, Any]:
        try:
            principal = auth(request, "ace:resolve")
            bound = _bind_remote_invocation(payload["invocation"], principal)
            output_name = str(payload["output_name"])
            output_dir = _safe_output_dir(output_name, root=root, runtime_root=runtime_root)
            output_dir.parent.mkdir(parents=True, exist_ok=True)
            result = resolve_verified_invocation(bound, output_dir, control_root=root)
            return {
                "schema_version": REMOTE_SERVICE_VERSION,
                "record_type": "ace_remote_resolution",
                "transport": "https_json",
                "remote_principal": principal["principal"],
                "output_name": output_name,
                "packet_ref": str(output_dir),
                **result,
            }
        except Exception as exc:
            raise _http_error(exc) from exc

    @app.post("/v1/inspect")
    def inspect(payload: dict[str, Any], request: Request) -> dict[str, Any]:
        try:
            principal = auth(request, "ace:read")
            result = _ace_inspect(
                invocation_id=payload.get("invocation_id"),
                determination_id=payload.get("determination_id"),
                root=root,
                runtime_root=runtime_root,
            )
            result["remote_principal"] = principal["principal"]
            result["transport"] = "https_json"
            return result
        except Exception as exc:
            raise _http_error(exc) from exc

    @app.post("/v1/materialize/preview")
    def materialize_preview(payload: dict[str, Any], request: Request) -> dict[str, Any]:
        try:
            principal = auth(request, "ace:materialize")
            authority_ref = str(payload["authority_ref"])
            _authority_allowed(principal, authority_ref)
            result = _ace_materialize_preview(
                str(payload["output_name"]),
                authority_ref,
                root=root,
                runtime_root=runtime_root,
            )
            result["remote_principal"] = principal["principal"]
            result["transport"] = "https_json"
            return result
        except Exception as exc:
            raise _http_error(exc) from exc

    @app.post("/v1/materialize/commit")
    def materialize_commit(payload: dict[str, Any], request: Request) -> dict[str, Any]:
        try:
            principal = auth(request, "ace:materialize")
            authority_ref = str(payload["authority_ref"])
            _authority_allowed(principal, authority_ref)
            result = _ace_materialize_commit(
                str(payload["output_name"]),
                authority_ref,
                str(payload["authorization_token"]),
                payload.get("side_effects_acknowledged") is True,
                payload.get("commit_message"),
                root=root,
                runtime_root=runtime_root,
            )
            result["remote_principal"] = principal["principal"]
            result["transport"] = "https_json"
            return result
        except Exception as exc:
            raise _http_error(exc) from exc

    return app

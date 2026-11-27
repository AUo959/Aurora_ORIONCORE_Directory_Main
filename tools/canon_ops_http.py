"""Serve pinned Canon Operations reads over authenticated loopback HTTP."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

if __package__:
    from . import canon_ops_journal as journal
    from .ace.remote_auth import RemoteAuthError, authenticate_bearer, load_remote_principals
    from .canon_ops_intake import _object, _require_commit, _unique_object, record_provenance
    from .canon_ops_query import CanonRec, query
else:
    import canon_ops_journal as journal
    from ace.remote_auth import RemoteAuthError, authenticate_bearer, load_remote_principals
    from canon_ops_intake import _object, _require_commit, _unique_object, record_provenance
    from canon_ops_query import CanonRec, query


MAX_REQUEST_BYTES = 1_048_576


def _http_error(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message})


def _authorize(request: Request, principals: list[dict]) -> None:
    try:
        authenticate_bearer(request.headers.get("authorization"), "ace:read", principals=principals)
    except RemoteAuthError as exc:
        raise _http_error(exc.status_code, exc.code, str(exc)) from exc


async def _body(request: Request) -> dict:
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > MAX_REQUEST_BYTES:
            raise _http_error(413, "request_too_large", "Canon Operations requests are limited to 1 MiB")
        body.extend(chunk)
    try:
        payload = json.loads(bytes(body), object_pairs_hook=_unique_object)
    except (ValueError, UnicodeError) as exc:
        raise _http_error(400, "invalid_json", "Expected a single JSON request object") from exc
    if not isinstance(payload, dict):
        raise _http_error(400, "invalid_json", "Expected a single JSON request object")
    return payload


def _path_in_scope(path: object, allowed: list[str]) -> bool:
    if not isinstance(path, str):
        return False
    return any(path == root or path.startswith(root + "/") for root in allowed)


def _allow_query(payload: dict, policy: dict) -> None:
    if payload.get("commit") != policy["canon_commit"]:
        raise _http_error(403, "snapshot_denied", "Use the configured CanonRec snapshot")
    layer, paths = payload.get("layer"), payload.get("source_paths")
    if not isinstance(layer, str) or not isinstance(paths, list):
        raise _http_error(400, "invalid_query", "Expected a layer and source path list")
    allowed = policy["target_paths"].get(layer, [])
    if not all(_path_in_scope(path, allowed) for path in paths):
        raise _http_error(403, "path_denied", "A requested source path is outside the configured layer scope")


def _request_status(path: Path, request_id: str, policy: dict) -> dict:
    entries = journal.read_entries(path)
    if entries and entries[0]["receipt"]["canon_commit"] != policy["canon_commit"]:
        raise _http_error(409, "snapshot_mismatch", "The journal uses a different CanonRec snapshot")
    entry = next((value for value in entries if value["request"]["request_id"] == request_id), None)
    if entry is None:
        raise _http_error(404, "unknown", "The request is absent from the pinned journal")
    if entry["request"]["layer"] not in policy["target_paths"]:
        raise _http_error(403, "layer_denied", "The request layer is outside the configured scope")
    return entry


def create_app(
    *, canonrec: CanonRec, journal_path: Path, policy: dict, principals: list[dict],
    browser_origins: tuple[str, ...] = (),
) -> FastAPI:
    """Expose read-only operations for one operator-configured source scope."""
    _require_commit(canonrec, policy["canon_commit"])
    if "*" in browser_origins:
        raise ValueError("Supply exact browser origins for the local Canon Operations reader")
    app = FastAPI(title="Canon Operations Reader", version="1.0", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])
    app.add_middleware(
        CORSMiddleware, allow_origins=list(browser_origins),
        allow_methods=["POST"], allow_headers=["Authorization", "Content-Type"],
    )

    @app.post("/v1/query")
    async def read_query(request: Request) -> dict:
        _authorize(request, principals)
        payload = await _body(request)
        _allow_query(payload, policy)
        try:
            return await run_in_threadpool(query, canonrec, payload)
        except (ValueError, OSError) as exc:
            raise _http_error(400, "query_rejected", str(exc)) from exc

    @app.post("/v1/provenance")
    async def read_provenance(request: Request) -> dict:
        _authorize(request, principals)
        target = await _body(request)
        if set(target) != {"layer", "kind", "record_id"} or not all(isinstance(value, str) for value in target.values()):
            raise _http_error(400, "invalid_target", "Expected the exact layer, kind and record ID")
        if target["layer"] not in policy["target_paths"]:
            raise _http_error(403, "layer_denied", "The record layer is outside the configured scope")
        try:
            return await run_in_threadpool(record_provenance, canonrec, policy, journal_path, target)
        except (ValueError, OSError, sqlite3.Error) as exc:
            raise _http_error(409, "provenance_unavailable", str(exc)) from exc

    @app.post("/v1/status")
    async def read_status(request: Request) -> dict:
        _authorize(request, principals)
        payload = await _body(request)
        request_id = payload.get("request_id")
        if not isinstance(request_id, str) or not 0 < len(request_id) <= 256:
            raise _http_error(400, "invalid_request_id", "Expected a Canon Operations request ID")
        try:
            return await run_in_threadpool(_request_status, journal_path, request_id, policy)
        except (ValueError, OSError, sqlite3.Error) as exc:
            raise _http_error(409, "journal_unavailable", str(exc)) from exc

    return app


def main() -> None:
    """Launch the reader on local loopback with the existing ACE bearer policy."""
    import uvicorn

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonrec", required=True, type=Path)
    parser.add_argument("--journal", required=True, type=Path)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--browser-origin", action="append", default=[])
    args = parser.parse_args()
    app = create_app(
        canonrec=CanonRec(args.canonrec), journal_path=args.journal, policy=_object(args.policy),
        principals=load_remote_principals(), browser_origins=tuple(args.browser_origin),
    )
    uvicorn.run(app, host="127.0.0.1", port=args.port, access_log=False)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Local-only, authenticated read endpoint for the Aurora Intelligent UI snapshot.

This module serves a *saved* Mission Control report through the existing,
allowlisted snapshot adapter. It never runs a report collector or another
Aurora runtime, and grants no simulation or canon permissions.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse

import aurora_intelligent_ui_bridge as bridge

TOKEN_HASH_ENV = "AURORA_UI_READ_TOKEN_SHA256"
TOKEN_DIGEST_FORMAT = re.compile(r"^[0-9a-f]{64}$")
MAX_REPORT_BYTES = 2 * 1024 * 1024


class AuthConfigurationError(ValueError):
    """Service must not start without a valid dedicated read credential."""


def configured_digest(environ: Mapping[str, str] | None = None) -> str:
    config = os.environ if environ is None else environ
    digest = config.get(TOKEN_HASH_ENV)
    if not isinstance(digest, str) or TOKEN_DIGEST_FORMAT.fullmatch(digest) is None:
        raise AuthConfigurationError(
            "AURORA_UI_READ_TOKEN_SHA256 must be a lowercase SHA-256 digest of "
            "a high-entropy bearer token; the service fails closed without it"
        )
    return digest


def authenticate(header: str | None, expected_digest: str) -> None:
    if not isinstance(header, str) or not header.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Bearer authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = header[len("Bearer "):]
    if not token or len(token) > 4096 or token != token.strip():
        raise HTTPException(
            status_code=401, detail="Invalid bearer credential",
            headers={"WWW-Authenticate": "Bearer"},
        )
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    if not hmac.compare_digest(digest, expected_digest):
        raise HTTPException(
            status_code=401, detail="Invalid bearer credential",
            headers={"WWW-Authenticate": "Bearer"},
        )


def read_snapshot(
    root: Path, *, max_age_hours: int = 48, now: datetime | None = None
) -> dict[str, Any]:
    """Read the one fixed report inside root; reject oversized/escaped paths."""
    resolved_root = root.resolve()
    path = resolved_root / bridge.SOURCE_REFERENCE
    # Fail closed on file symlinks and on paths traversing outside the owner repo.
    if path.is_symlink() or resolved_root not in path.resolve().parents:
        raise bridge.BridgeError("untrusted report path")
    with path.open("rb") as handle:
        data = handle.read(MAX_REPORT_BYTES + 1)
    if len(data) > MAX_REPORT_BYTES:
        raise bridge.BridgeError("report exceeds read limit")
    return bridge.build_snapshot(
        json.loads(data), input_sha256=hashlib.sha256(data).hexdigest(),
        max_age_hours=max_age_hours, now=now,
    )


def create_app(
    *, root: Path = bridge.ROOT, environ: Mapping[str, str] | None = None,
    max_age_hours: int = 48,
) -> FastAPI:
    """Construct a service with one explicitly read-only authenticated route."""
    digest = configured_digest(environ)
    if type(max_age_hours) is not int or max_age_hours < 1:
        raise AuthConfigurationError("max_age_hours must be a positive integer")
    app = FastAPI(
        title="Aurora Intelligent UI Snapshot",
        version="1.0.0",
        docs_url=None, redoc_url=None, openapi_url=None,
    )

    @app.middleware("http")
    async def no_cache(request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.get("/v1/mission-control/snapshot")
    def mission_control_snapshot(request: Request) -> dict[str, Any]:
        # Authenticate *before* reading report bytes, even when unavailable.
        authenticate(request.headers.get("authorization"), digest)
        try:
            return read_snapshot(root, max_age_hours=max_age_hours)
        except (OSError, UnicodeError, json.JSONDecodeError, bridge.BridgeError) as exc:
            # Log no raw report, credential, or path; do not expose internals.
            raise HTTPException(
                status_code=503, detail="Validated snapshot unavailable"
            ) from exc

    return app


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Serve Aurora UI snapshots with a local-only read credential."
    )
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--root", type=Path, default=bridge.ROOT)
    args = parser.parse_args(argv)
    if args.port < 1 or args.port > 65535:
        parser.error("port must be between 1 and 65535")
    try:
        app = create_app(root=args.root)
    except AuthConfigurationError as exc:
        print("Aurora UI service is not configured: " + str(exc), file=sys.stderr)
        return 2
    import uvicorn
    # Never silently bind to a public interface. External access requires a
    # separately reviewed, TLS-terminated authenticated integration.
    uvicorn.run(
        app, host="127.0.0.1", port=args.port, proxy_headers=False,
        server_header=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

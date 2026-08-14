#!/usr/bin/env python3
"""Run the authenticated ACE HTTP service.

Non-loopback binding is refused unless the operator provides a TLS certificate
and private key. Authentication configuration is loaded by the application from
ACE_REMOTE_PRINCIPALS_JSON; no credential material is accepted on the CLI.
"""

from __future__ import annotations

import argparse
import ipaddress

import uvicorn

from ace.remote_service import create_app


def _is_loopback(host: str) -> bool:
    if host in {"localhost"}:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run authenticated Aurora ACE remote service.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--ssl-certfile", default=None)
    parser.add_argument("--ssl-keyfile", default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not 1 <= args.port <= 65535:
        raise SystemExit("--port must be between 1 and 65535")
    if not _is_loopback(args.host) and not (args.ssl_certfile and args.ssl_keyfile):
        raise SystemExit("ACE remote service refuses non-loopback binding without --ssl-certfile and --ssl-keyfile")
    app = create_app()
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        ssl_certfile=args.ssl_certfile,
        ssl_keyfile=args.ssl_keyfile,
        server_header=False,
    )


if __name__ == "__main__":
    main()

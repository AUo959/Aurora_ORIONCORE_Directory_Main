#!/usr/bin/env python3
"""stdio MCP server for the Aurora Canon Engine (ACE) v0.8 surface."""

from __future__ import annotations

from typing import Any

from mcp.server import MCPServer

from ace.mcp_adapter import (
    MCP_TOOL_NAMES,
    ace_capabilities as _ace_capabilities,
    ace_inspect as _ace_inspect,
    ace_materialize_commit as _ace_materialize_commit,
    ace_materialize_preview as _ace_materialize_preview,
    ace_plan as _ace_plan,
    ace_resolve as _ace_resolve,
)

mcp = MCPServer(
    "Aurora ACE",
    instructions=(
        "Aurora Canon Engine transport surface. MCP delegates to the existing ACE "
        "invocation, manifest-routing, determination, provenance, and native materializer "
        "contracts. Canonical materialization is available only through the two-phase "
        "owner-gated preview/commit tools against the registered CanonRec checkout; "
        "arbitrary repository paths, protected-branch writes, and dynamic runtime binding "
        "are not exposed."
    ),
)


@mcp.tool()
def ace_capabilities() -> dict[str, Any]:
    """Return the validated manifest-derived ACE capability index."""
    return _ace_capabilities()


@mcp.tool()
def ace_plan(invocation: dict[str, Any]) -> dict[str, Any]:
    """Select the ACE runtime capability for an inspectable invocation without executing it."""
    return _ace_plan(invocation)


@mcp.tool()
def ace_resolve(invocation: dict[str, Any], output_name: str) -> dict[str, Any]:
    """Run the shared ACE resolver inside the bounded MCP runtime directory."""
    return _ace_resolve(invocation, output_name)


@mcp.tool()
def ace_inspect(
    invocation_id: str | None = None,
    determination_id: str | None = None,
) -> dict[str, Any]:
    """Inspect an ACE invocation or determination and its recorded provenance."""
    return _ace_inspect(
        invocation_id=invocation_id,
        determination_id=determination_id,
    )


@mcp.tool()
def ace_materialize_preview(output_name: str, authority_ref: str) -> dict[str, Any]:
    """Preview one owner-gated CanonRec materialization and return its state-bound token."""
    return _ace_materialize_preview(output_name, authority_ref)


@mcp.tool()
def ace_materialize_commit(
    output_name: str,
    authority_ref: str,
    authorization_token: str,
    side_effects_acknowledged: bool,
    commit_message: str | None = None,
) -> dict[str, Any]:
    """Commit one previewed native materialization after explicit side-effect acknowledgement."""
    return _ace_materialize_commit(
        output_name,
        authority_ref,
        authorization_token,
        side_effects_acknowledged,
        commit_message,
    )


def main() -> None:
    """Run the ACE MCP transport over stdio only."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

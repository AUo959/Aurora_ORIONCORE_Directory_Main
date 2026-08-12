#!/usr/bin/env python3
"""stdio MCP server for the Aurora Canon Engine (ACE) v0.7 surface."""

from __future__ import annotations

from typing import Any

from mcp.server import MCPServer

from ace.mcp_adapter import (
    MCP_TOOL_NAMES,
    ace_capabilities as _ace_capabilities,
    ace_inspect as _ace_inspect,
    ace_plan as _ace_plan,
    ace_resolve as _ace_resolve,
)

mcp = MCPServer(
    "Aurora ACE",
    instructions=(
        "Aurora Canon Engine transport surface. MCP is an adapter over the existing "
        "ACE invocation, manifest-routing, determination, and provenance contracts. "
        "This server does not expose canonical materialization."
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


def main() -> None:
    """Run the ACE MCP transport over stdio only."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

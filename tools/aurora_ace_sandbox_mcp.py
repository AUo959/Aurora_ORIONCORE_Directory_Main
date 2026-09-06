#!/usr/bin/env python3
"""Three-tool stdio transport for one explicitly provisioned ACE sandbox."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from mcp.server import MCPServer

from ace.sandbox import World


def create_server(directory: Path) -> MCPServer:
    world = World(directory)
    server = MCPServer(
        "Aurora isolated world",
        instructions=(
            "Persistent isolated Aurora character world. Call aurora_world_status first. "
            "Use retrieve for questions, preview for exploration, create only for explicit creation "
            "requests. Supply character names/IDs in context. Reuse request IDs only for identical retries. "
            "Ground answers in returned fields. Saved canon belongs to this world only. "
            "No source-world, publication, or Orion runtime authority."
        ),
    )

    @server.tool()
    def aurora_world_status() -> dict[str, Any]:
        """Read world identity, integrity, source revisions, and permitted operations."""
        return world.status()

    @server.tool()
    def aurora_character(
        question: str,
        context: dict[str, Any],
        request_id: str,
        operation: str = "retrieve",
    ) -> dict[str, Any]:
        """
        Retrieve, preview, or explicitly create a character in this isolated world.

        Lookups use context.name or context.canonical_id. Creation requires role,
        faction_id, location_type and optional observed_behavior. Only an explicit
        creation request authorizes operation=create. Returns durable identity,
        determination and provenance; missing facts are never invented for retrieval.
        """
        return world.character(question, context, request_id, operation)

    @server.tool()
    def aurora_inspect(
        invocation_id: str | None = None, determination_id: str | None = None
    ) -> dict[str, Any]:
        """Inspect exactly one invocation or determination in this world's history."""
        return world.inspect(invocation_id, determination_id)

    return server


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world", required=True, type=Path)
    args = parser.parse_args()
    create_server(args.world).run(transport="stdio")


if __name__ == "__main__":
    main()

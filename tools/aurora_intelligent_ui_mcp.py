#!/usr/bin/env python3
"""Read-only Aurora Mission Control MCP transport for a Secure MCP Tunnel.

One tool and stdio only. The tunnel-client mediates remote access to this
private process. No HTTP listener, web deployment, ACE or simulation tools.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from mcp.server import MCPServer
from mcp.types import ToolAnnotations

import aurora_intelligent_ui_bridge as bridge
import aurora_intelligent_ui_service as service

ROOT_ENV = "AURORA_UI_ROOT"
TOOL_NAME = "get_mission_control_snapshot"

mcp = MCPServer(
    "Aurora Mission Control (Read Only)",
    instructions=(
        "Use the one read-only tool to inspect a saved Aurora Mission Control "
        "snapshot. Always distinguish source.generated_at from retrieval "
        "time and honor source.freshness. A retrieved report is NOT evidence "
        "of current live runtime status. This server cannot run simulations, "
        "make decisions, promote canon, modify repos, or execute commands."
    ),
)


def read_bounded_snapshot(*, root: Path | None = None) -> dict[str, Any]:
    """Read one fixed report; runtime root is operator config, not a tool argument."""
    configured = os.environ.get(ROOT_ENV)
    if root is None:
        source_root = Path(configured).expanduser() if configured else bridge.ROOT
    else:
        source_root = root
    return service.read_snapshot(source_root)


@mcp.tool(
    title="Read Aurora Mission Control snapshot",
    annotations=ToolAnnotations(read_only_hint=True, open_world_hint=False),
)
def get_mission_control_snapshot() -> dict[str, Any]:
    """Read the saved, provenance-labeled Mission Control status, inbox, and build lanes.

    Source freshness is explicit. This never regenerates a report or performs an
    Aurora operational action. Restricted evidence is withheld by the bridge.
    """
    try:
        return read_bounded_snapshot()
    except (OSError, UnicodeError, json.JSONDecodeError, bridge.BridgeError) as exc:
        # SDK reports a generic tool failure without surfacing file paths or contents.
        raise ValueError(
            "Aurora Mission Control snapshot unavailable or invalid; "
            "no current operational status can be inferred."
        ) from exc


def main() -> None:
    """Run the stdio-only transport for an approved private MCP tunnel."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

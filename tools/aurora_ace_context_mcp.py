#!/usr/bin/env python3
"""Narrow simulation-needs interface with a durable background ACE worker."""

from __future__ import annotations

import argparse
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from mcp.server import MCPServer

from ace.contextual import ContextQueue
from ace.core import ACEError


def create_server(directory: Path) -> MCPServer:
    queue = ContextQueue(directory)
    worker_state: dict[str, Any] = {"running": False, "error": None}

    @asynccontextmanager
    async def lifespan(server):
        stop = threading.Event()

        def work():
            worker_state["running"] = True
            try:
                while not stop.is_set():
                    try:
                        if queue.work_once() is not None:
                            continue
                        worker_state["error"] = None
                    except (ACEError, OSError, ValueError, KeyError) as exc:
                        worker_state["error"] = str(exc)
                    stop.wait(0.25)
            finally:
                worker_state["running"] = False

        thread = threading.Thread(
            target=work, name="aurora-context-worker", daemon=True
        )
        thread.start()
        try:
            yield {}
        finally:
            stop.set()
            thread.join(timeout=2)

    server = MCPServer(
        "Aurora contextual simulation",
        lifespan=lifespan,
        instructions=(
            "Discover authorized assignments with aurora_context_status. A simulation need inside "
            "an authorized assignment may be submitted without a per-character creation request. "
            "Use a stable need ID and grounded structured context. The worker retrieves first, "
            "reconciles through existing ACE tools, and saves valid L2 character completions. "
            "L3 rules govern both L1 and L2: L1 needs are evidence-bound read-only fact resolution; "
            "L2 facts belong to their isolated world and settings. Never claim L2 output establishes "
            "L1 truth or that retrieved L1 records independently prove external reality. "
            "Inspect jobs for results; surface conflicts or blocked jobs. Routine results can remain "
            "quiet until relevant. No assignment grant, publication, or runtime progression tools."
        ),
    )

    @server.tool()
    def aurora_context_status() -> dict[str, Any]:
        """Discover world identity, authorized assignments, queued needs, and worker health."""
        return {**queue.status(), "worker": dict(worker_state)}

    @server.tool()
    def aurora_simulation_need(
        assignment_id: str, need_id: str, question: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Queue detail required by an authorized assignment; not a new authority grant.

        L2 context accepts role, name/canonical_id, and observed_behavior; faction
        and location are grounded in assignment settings. L1 selects field_path
        from the assignment's permitted evidence fields. Reuse need IDs on retry.
        """
        return queue.submit(assignment_id, need_id, question, context)

    @server.tool()
    def aurora_need_inspect(job_id: str) -> dict[str, Any]:
        """Read job outcome, L3 decision, settings, and linked native ACE receipt."""
        return queue.inspect(job_id)

    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--world", type=Path, required=True)
    create_server(parser.parse_args().world).run(transport="stdio")

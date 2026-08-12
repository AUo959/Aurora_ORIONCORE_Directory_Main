"""Transport-only MCP adapter for the Aurora Canon Engine (ACE).

This module deliberately contains no MCP SDK dependency so OrionCore's Python
3.9 compatibility lane can exercise the trust boundary. The actual MCP server
lives in ``tools/aurora_ace_mcp.py`` and delegates every operation here.

MCP is an entry surface, never an alternate ACE engine:
MCP -> invocation envelope -> manifest router -> shared ACE resolver.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from .capability_discovery import build_capability_index, select_invocation_capability
from .core import ACEError, ROOT
from .invocation import resolve_invocation, validate_invocation_envelope

MCP_ADAPTER_VERSION = "0.7.0"
MCP_RUNTIME_REL = Path("reports/ace/mcp_runtime")
MCP_LEDGER_REL = Path("reports/ace/determinations")
MCP_TOOL_NAMES = (
    "ace_capabilities",
    "ace_plan",
    "ace_resolve",
    "ace_inspect",
)
MAX_INSPECT_JSON_FILES = 2048
_OUTPUT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _runtime_root(root: Path, runtime_root: Path | None = None) -> Path:
    base = (runtime_root or (root / MCP_RUNTIME_REL)).expanduser().resolve()
    if runtime_root is None and not _is_relative_to(base, root.expanduser().resolve()):
        raise ACEError("ACE MCP runtime root escaped OrionCore", code="target_unavailable")
    return base


def _safe_output_dir(
    output_name: str,
    *,
    root: Path = ROOT,
    runtime_root: Path | None = None,
) -> Path:
    if not isinstance(output_name, str) or _OUTPUT_NAME.fullmatch(output_name) is None:
        raise ACEError(
            "MCP output_name must be a simple 1-128 character identifier "
            "containing only letters, digits, dot, underscore, or hyphen",
            code="input_validation_failed",
        )
    if output_name in {".", ".."}:
        raise ACEError("MCP output_name cannot be a relative-path token", code="input_validation_failed")

    base = _runtime_root(root, runtime_root)
    target = (base / output_name).resolve()
    if target.parent != base:
        raise ACEError("MCP output target escaped the bounded runtime directory", code="target_unavailable")
    return target


def ace_capabilities(*, root: Path = ROOT) -> dict[str, Any]:
    """Return ACE's manifest-derived capability index through the MCP surface."""
    return {
        "schema_version": MCP_ADAPTER_VERSION,
        "record_type": "ace_mcp_capabilities",
        "transport": "stdio",
        "materialization_exposed": False,
        "tools": list(MCP_TOOL_NAMES),
        "capability_index": build_capability_index(root),
    }


def ace_plan(invocation: Mapping[str, Any]) -> dict[str, Any]:
    """Select the manifest-backed runtime capability without executing it."""
    validate_invocation_envelope(invocation)
    query = invocation["query"]
    capability = select_invocation_capability(query)
    preferred_capability_refs = sorted(
        {
            str(ref)
            for output in query.get("requested_outputs", [])
            if isinstance(output, Mapping)
            for ref in output.get("preferred_capability_refs", [])
        }
    )
    return {
        "schema_version": MCP_ADAPTER_VERSION,
        "record_type": "ace_mcp_plan",
        "transport": "stdio",
        "materialization_exposed": False,
        "invocation_id": invocation["invocation_id"],
        "query_id": query.get("query_id"),
        "preferred_capability_refs": preferred_capability_refs,
        "selected_runtime_capability": capability,
    }


def ace_resolve(
    invocation: Mapping[str, Any],
    output_name: str,
    *,
    root: Path = ROOT,
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    """Execute the normal ACE resolver into the MCP-bounded packet directory."""
    validate_invocation_envelope(invocation)
    output_dir = _safe_output_dir(output_name, root=root, runtime_root=runtime_root)
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    result = resolve_invocation(invocation, output_dir, root=root)
    return {
        "schema_version": MCP_ADAPTER_VERSION,
        "record_type": "ace_mcp_resolution",
        "transport": "stdio",
        "materialization_exposed": False,
        "output_name": output_name,
        "packet_ref": str(output_dir),
        "invocation": result["invocation"],
        "determination": result["determination"],
        "invocation_sidecar": result["invocation_sidecar"],
    }


def _load_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _inspect_roots(
    *,
    root: Path,
    runtime_root: Path | None,
) -> list[tuple[str, Path]]:
    return [
        ("mcp_runtime", _runtime_root(root, runtime_root)),
        ("determination_ledger", (root / MCP_LEDGER_REL).expanduser().resolve()),
    ]


def ace_inspect(
    *,
    invocation_id: str | None = None,
    determination_id: str | None = None,
    root: Path = ROOT,
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    """Find inspectable ACE provenance without granting any mutation authority."""
    supplied = [value for value in (invocation_id, determination_id) if value is not None]
    if len(supplied) != 1:
        raise ACEError(
            "ace_inspect requires exactly one of invocation_id or determination_id",
            code="input_validation_failed",
        )
    lookup_kind = "invocation_id" if invocation_id is not None else "determination_id"
    lookup_value = invocation_id if invocation_id is not None else determination_id
    if not isinstance(lookup_value, str) or not lookup_value.strip():
        raise ACEError("ACE inspect reference must be a non-empty string", code="input_validation_failed")

    matches: list[dict[str, Any]] = []
    inspected = 0
    for source_kind, source_root in _inspect_roots(root=root, runtime_root=runtime_root):
        if not source_root.exists():
            continue
        source_root_resolved = source_root.resolve()
        for path in sorted(source_root.rglob("*.json")):
            inspected += 1
            if inspected > MAX_INSPECT_JSON_FILES:
                raise ACEError(
                    "ACE MCP inspect exceeded its bounded JSON scan limit",
                    code="target_unavailable",
                )
            resolved = path.resolve()
            if not _is_relative_to(resolved, source_root_resolved):
                continue
            payload = _load_object(resolved)
            if payload is None:
                continue

            direct_match = payload.get(lookup_kind) == lookup_value
            linked_match = (
                determination_id is not None
                and payload.get("determination_ref") == determination_id
            )
            if not (direct_match or linked_match):
                continue
            matches.append(
                {
                    "source_kind": source_kind,
                    "source_ref": str(resolved),
                    "record_type": payload.get("record_type"),
                    "payload": payload,
                }
            )

    matches.sort(key=lambda item: (str(item["source_kind"]), str(item["source_ref"])))
    return {
        "schema_version": MCP_ADAPTER_VERSION,
        "record_type": "ace_mcp_inspection",
        "transport": "stdio",
        "materialization_exposed": False,
        "lookup": {"kind": lookup_kind, "value": lookup_value},
        "found": bool(matches),
        "match_count": len(matches),
        "matches": matches,
    }

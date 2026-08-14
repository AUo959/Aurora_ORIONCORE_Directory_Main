"""Two-phase state-bound publication gate for generic native L2 entities."""

from __future__ import annotations

import hmac
from pathlib import Path
from typing import Any

from . import generic_entity as engine
from .core import ACEError, ROOT
from .generic_entity_validation import (
    assert_native_entity_tree_readable,
    payload_validator_binding,
)
from .mcp_adapter import (
    MCP_ADAPTER_VERSION,
    MCP_CANONREC_NAME,
    MCP_MATERIALIZATION_AUTHORITY_MODE,
    _materialization_preview,
)


def generic_entity_preview(
    output_name: str,
    authority_ref: str,
    *,
    root: Path = ROOT,
    runtime_root: Path | None = None,
    target_repo: Path | None = None,
) -> dict[str, Any]:
    preview, packet, repo = _materialization_preview(
        output_name,
        authority_ref,
        root=root,
        runtime_root=runtime_root,
        target_repo=target_repo,
    )
    if not (packet / "candidate_entity.json").is_file():
        raise ACEError("generic entity publication requires candidate_entity.json", code="target_unavailable")
    assert_native_entity_tree_readable(repo)
    result = dict(preview)
    result["record_type"] = "ace_generic_entity_materialization_preview"
    result["entity_surface"] = "native_canonrec_l2_flat_record"
    return result


def generic_entity_commit(
    output_name: str,
    authority_ref: str,
    authorization_token: str,
    side_effects_acknowledged: bool,
    commit_message: str | None = None,
    *,
    root: Path = ROOT,
    runtime_root: Path | None = None,
    target_repo: Path | None = None,
) -> dict[str, Any]:
    if side_effects_acknowledged is not True:
        raise ACEError("generic entity publication requires explicit side-effect acknowledgement", code="materialization_authority_missing")
    if not isinstance(authorization_token, str) or not authorization_token.startswith("ace-mcp-auth:"):
        raise ACEError("generic entity publication requires a preview authorization token", code="materialization_authority_missing")
    preview, packet, repo = _materialization_preview(
        output_name,
        authority_ref,
        root=root,
        runtime_root=runtime_root,
        target_repo=target_repo,
    )
    if not (packet / "candidate_entity.json").is_file():
        raise ACEError("generic entity publication requires candidate_entity.json", code="target_unavailable")
    assert_native_entity_tree_readable(repo)
    if not hmac.compare_digest(authorization_token, preview["authorization_token"]):
        raise ACEError("generic entity authorization token no longer matches current state", code="materialization_authority_missing")
    with payload_validator_binding(engine):
        determination = engine.materialize_generic_entity_packet(
            packet,
            repo,
            authority_mode=MCP_MATERIALIZATION_AUTHORITY_MODE,
            authority_ref=preview["authority_ref"],
            root=root,
            commit_message=commit_message,
        )
    return {
        "schema_version": MCP_ADAPTER_VERSION,
        "record_type": "ace_generic_entity_materialization_result",
        "transport": "local_or_authenticated_remote",
        "authorization": {
            "mode": MCP_MATERIALIZATION_AUTHORITY_MODE,
            "authority_ref": preview["authority_ref"],
            "token_binding": preview["token_binding"],
            "side_effects_acknowledged": True,
        },
        "output_name": output_name,
        "packet_ref": str(packet),
        "target_repository": MCP_CANONREC_NAME,
        "materialized_determination": determination,
    }

"""First-class invocation facade for the Aurora Canon Engine (ACE).

This module keeps interactive, embedded, and autonomic entry paths on the same
ACE engine. It adds invocation provenance without changing the normalized ACE
query or allowing automatic invocation to become invisible background logic.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .core import (
    ACEError,
    SCHEMA_VERSION,
    compile_character_query,
    semantic_sha256,
    utc_now,
    write_json,
)
from .engine import resolve_character_query

INVOCATION_SCHEMA_VERSION = "0.2.0"
INVOCATION_MODES = frozenset({"interactive", "embedded", "autonomic"})
CALLER_KINDS = frozenset({"user", "operations", "agent", "system", "capability"})
TRIGGER_KINDS = frozenset({"direct_query", "capability_call", "coherence_seam", "policy_event"})


def _nonempty(value: str | None, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ACEError(f"{field} must be a non-empty string", code="input_validation_failed")
    return value.strip()


def validate_invocation_envelope(payload: Mapping[str, Any]) -> None:
    """Fail closed on invocation provenance that could hide or blur an ACE call."""

    if payload.get("schema_version") != INVOCATION_SCHEMA_VERSION:
        raise ACEError("unsupported ACE invocation schema version", code="input_validation_failed")
    if payload.get("record_type") != "ace_invocation_envelope":
        raise ACEError("record_type must be ace_invocation_envelope", code="input_validation_failed")

    mode = payload.get("invocation_mode")
    if mode not in INVOCATION_MODES:
        raise ACEError(f"unsupported ACE invocation mode: {mode!r}", code="input_validation_failed")
    if payload.get("visibility") != "inspectable":
        raise ACEError("ACE invocation visibility must remain inspectable", code="input_validation_failed")
    if payload.get("automatic") is not (mode == "autonomic"):
        raise ACEError("automatic flag must match invocation mode", code="input_validation_failed")

    caller = payload.get("caller")
    if not isinstance(caller, Mapping):
        raise ACEError("caller must be an object", code="input_validation_failed")
    if caller.get("kind") not in CALLER_KINDS:
        raise ACEError("caller.kind is not recognized", code="input_validation_failed")
    _nonempty(caller.get("caller_ref"), "caller.caller_ref")

    trigger = payload.get("trigger")
    if not isinstance(trigger, Mapping):
        raise ACEError("trigger must be an object", code="input_validation_failed")
    if trigger.get("kind") not in TRIGGER_KINDS:
        raise ACEError("trigger.kind is not recognized", code="input_validation_failed")
    _nonempty(trigger.get("reason"), "trigger.reason")

    if mode == "embedded" and caller.get("kind") not in {"agent", "system", "capability", "operations"}:
        raise ACEError(
            "embedded ACE invocation requires an agent, operations, system, or capability caller",
            code="input_validation_failed",
        )

    if mode == "autonomic":
        if caller.get("kind") not in {"system", "capability", "agent"}:
            raise ACEError(
                "autonomic ACE invocation requires a system, capability, or agent caller",
                code="input_validation_failed",
            )
        _nonempty(trigger.get("seam_ref"), "trigger.seam_ref")
        _nonempty(trigger.get("trigger_policy_ref"), "trigger.trigger_policy_ref")
        if trigger.get("kind") not in {"coherence_seam", "policy_event"}:
            raise ACEError(
                "autonomic invocation must be triggered by a coherence_seam or policy_event",
                code="input_validation_failed",
            )

    query = payload.get("query")
    if not isinstance(query, Mapping):
        raise ACEError("invocation query must be an ACE query object", code="input_validation_failed")
    if query.get("record_type") != "ace_query_envelope" or query.get("schema_version") != SCHEMA_VERSION:
        raise ACEError(
            "invocation must wrap the normal supported ACE query envelope",
            code="input_validation_failed",
        )
    expected_query_digest = semantic_sha256(query)
    if payload.get("query_sha256") != expected_query_digest:
        raise ACEError("invocation query digest does not match query", code="input_validation_failed")
    if query.get("generation_policy", {}).get("prefer_existing_specialists") is not True:
        raise ACEError(
            "first-class ACE invocation requires specialist-first routing",
            code="input_validation_failed",
        )


def build_invocation_envelope(
    query: Mapping[str, Any],
    *,
    invocation_mode: str = "interactive",
    caller_kind: str = "user",
    caller_ref: str = "ORION.ROLE.PILOT",
    parent_invocation_ref: str | None = None,
    trigger_kind: str | None = None,
    trigger_reason: str | None = None,
    seam_ref: str | None = None,
    trigger_policy_ref: str | None = None,
) -> dict[str, Any]:
    """Wrap one normalized ACE query in inspectable invocation provenance."""

    if invocation_mode not in INVOCATION_MODES:
        raise ACEError(
            f"unsupported ACE invocation mode: {invocation_mode}",
            code="input_validation_failed",
        )
    if caller_kind not in CALLER_KINDS:
        raise ACEError(f"unsupported caller kind: {caller_kind}", code="input_validation_failed")

    default_trigger = {
        "interactive": "direct_query",
        "embedded": "capability_call",
        "autonomic": "coherence_seam",
    }[invocation_mode]
    default_reason = {
        "interactive": "Direct human or agent ACE query.",
        "embedded": "Registered Aurora workflow invoked ACE as a service.",
        "autonomic": "Registered Aurora policy detected a coherence seam requiring ACE determination.",
    }[invocation_mode]
    trigger_kind = trigger_kind or default_trigger
    trigger_reason = trigger_reason or default_reason

    query_dict = dict(query)
    query_sha256 = semantic_sha256(query_dict)
    caller = {
        "kind": caller_kind,
        "caller_ref": _nonempty(caller_ref, "caller_ref"),
        "parent_invocation_ref": parent_invocation_ref,
    }
    trigger = {
        "kind": trigger_kind,
        "reason": trigger_reason,
        "seam_ref": seam_ref,
        "trigger_policy_ref": trigger_policy_ref,
    }
    invocation_suffix = semantic_sha256(
        {
            "invocation_mode": invocation_mode,
            "caller": caller,
            "trigger": trigger,
            "query_sha256": query_sha256,
        }
    )[:20]
    envelope = {
        "schema_version": INVOCATION_SCHEMA_VERSION,
        "record_type": "ace_invocation_envelope",
        "invocation_id": f"ace.invocation.{invocation_mode}.{invocation_suffix}",
        "created_at": utc_now(),
        "invocation_mode": invocation_mode,
        "visibility": "inspectable",
        "automatic": invocation_mode == "autonomic",
        "caller": caller,
        "trigger": trigger,
        "query_sha256": query_sha256,
        "query": query_dict,
    }
    validate_invocation_envelope(envelope)
    return envelope


def compile_character_invocation(
    question: str,
    context: Mapping[str, Any],
    *,
    seed: int | str = 808,
    mode: str = "commit_ready",
    invocation_mode: str = "interactive",
    caller_kind: str = "user",
    caller_ref: str = "ORION.ROLE.PILOT",
    parent_invocation_ref: str | None = None,
    trigger_kind: str | None = None,
    trigger_reason: str | None = None,
    seam_ref: str | None = None,
    trigger_policy_ref: str | None = None,
    session_ref: str | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Compile a character query through the shared ACE engine and wrap its invocation."""

    requester_kind = caller_kind if caller_kind in {"user", "operations", "agent", "system"} else "system"
    kwargs: dict[str, Any] = {
        "seed": seed,
        "mode": mode,
        "requester_kind": requester_kind,
        "requester_id": caller_ref,
        "session_ref": session_ref,
    }
    if root is not None:
        kwargs["root"] = root
    query = compile_character_query(question, context, **kwargs)
    return build_invocation_envelope(
        query,
        invocation_mode=invocation_mode,
        caller_kind=caller_kind,
        caller_ref=caller_ref,
        parent_invocation_ref=parent_invocation_ref,
        trigger_kind=trigger_kind,
        trigger_reason=trigger_reason,
        seam_ref=seam_ref,
        trigger_policy_ref=trigger_policy_ref,
    )


def resolve_invocation(
    invocation: Mapping[str, Any],
    output_dir: Path,
    *,
    root: Path | None = None,
) -> dict[str, Any]:
    """Execute one invocation with the normal ACE engine and persist an inspectable sidecar."""

    validate_invocation_envelope(invocation)
    query = dict(invocation["query"])
    output = output_dir.expanduser().resolve()
    sidecar = output.parent / f"{output.name}.ace-invocation.json"
    if sidecar.exists():
        raise ACEError(f"invocation sidecar already exists: {sidecar}", code="target_unavailable")

    if root is None:
        determination = resolve_character_query(query, output_dir)
    else:
        determination = resolve_character_query(query, output_dir, root=root)

    payload = dict(invocation)
    payload["determination_ref"] = determination["determination_id"]
    payload["packet_ref"] = str(output)
    payload["determination_status"] = determination["status"]
    write_json(sidecar, payload)
    return {
        "invocation": payload,
        "determination": determination,
        "invocation_sidecar": str(sidecar),
    }

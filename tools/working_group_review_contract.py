"""Read-only checker for *proposed* Aurora working-group review packets.

No state writes, no network, no runtime action, no canonical authority.
Identity resolution is injected; a consent receipt reference is not proof
that permission was actually granted by a trusted authority.
"""
from __future__ import annotations

from datetime import datetime
import re
import uuid
from typing import Any, Callable, Mapping


class ReviewContractError(ValueError):
    """Proposed packet cannot pass design-only review."""


_UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-8][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$")
_KINDS = frozenset(("human", "relay_agent", "system_entity", "research_agent"))
_EVENTS = frozenset(("add_member", "remove_member", "dissolve"))


def _obj(value: Any, required: set[str], where: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != required:
        raise ReviewContractError(f"{where}: expected exact fields: {sorted(required)}")
    return value


def _text(value: Any, where: str, limit: int = 256) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ReviewContractError(f"{where}: required nonempty bounded text")
    return value


def _uuid(value: Any, where: str) -> str:
    if not isinstance(value, str) or not _UUID.fullmatch(value):
        raise ReviewContractError(f"{where}: expected UUID")
    try:
        uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise ReviewContractError(f"{where}: malformed UUID") from exc
    return value


def _when(value: Any, where: str) -> None:
    if not isinstance(value, str):
        raise ReviewContractError(f"{where}: expected timezone-aware ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReviewContractError(f"{where}: invalid timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ReviewContractError(f"{where}: timezone required")


def _entity(value: Any, where: str, resolver: Callable[[str, str], bool]) -> tuple[str, str]:
    ref = _obj(value, {"id", "kind"}, where)
    entity_id = _text(ref["id"], f"{where}.id", 128)
    kind = ref["kind"]
    if kind not in _KINDS:
        raise ReviewContractError(f"{where}: unsupported kind")
    if not resolver(entity_id, kind):
        raise ReviewContractError(f"{where}: unresolved identity")
    return entity_id, kind


def validate_review_packet(
    packet: Mapping[str, Any],
    *,
    resolve_identity: Callable[[str, str], bool],
) -> dict[str, object]:
    """Validate a hypothetical sequence, changing no external state.

    A successful result never asserts real consent or canonical identity.
    """
    if not callable(resolve_identity):
        raise ReviewContractError("trusted identity resolver required")
    item = _obj(packet, {"schema_version", "record_type", "review_status", "authority", "snapshot", "proposed_events"}, "packet")
    if (item["schema_version"], item["record_type"], item["review_status"], item["authority"]) != (
        "0.1.0", "working_group_review_packet", "pending_review", "none"
    ):
        raise ReviewContractError("packet: non-promoted review markers required")
    snapshot = _obj(item["snapshot"], {
        "group_id", "name", "purpose", "status", "version", "member_refs", "created_at", "policy_ref", "provenance_ref"
    }, "snapshot")
    group_id = _uuid(snapshot["group_id"], "snapshot.group_id")
    _text(snapshot["name"], "snapshot.name", 120)
    _text(snapshot["purpose"], "snapshot.purpose", 600)
    _text(snapshot["policy_ref"], "snapshot.policy_ref")
    _text(snapshot["provenance_ref"], "snapshot.provenance_ref")
    _when(snapshot["created_at"], "snapshot.created_at")
    if snapshot["status"] != "proposed":
        raise ReviewContractError("snapshot.status: only proposed snapshots are reviewable")
    version = snapshot["version"]
    if type(version) is not int or version < 0:
        raise ReviewContractError("snapshot.version: nonnegative integer required")
    members = snapshot["member_refs"]
    if not isinstance(members, list) or len(members) > 200:
        raise ReviewContractError("snapshot.member_refs: bounded list required")
    member_set: set[tuple[str, str]] = set()
    for ref in members:
        resolved = _entity(ref, "snapshot.member_refs", resolve_identity)
        if resolved in member_set:
            raise ReviewContractError("snapshot.member_refs: duplicate member")
        member_set.add(resolved)
    events = item["proposed_events"]
    if not isinstance(events, list) or len(events) > 100:
        raise ReviewContractError("proposed_events: bounded list required")
    seen: set[str] = set()
    dissolved = False
    for index, event in enumerate(events):
        where = f"proposed_events[{index}]"
        e = _obj(event, {
            "event_id", "group_id", "event_type", "occurred_at", "actor_ref",
            "member_ref", "expected_version", "new_version", "consent_receipt_ref", "audit_ref"
        }, where)
        event_id = _uuid(e["event_id"], where + ".event_id")
        if event_id in seen:
            raise ReviewContractError(where + ": duplicate event ID")
        seen.add(event_id)
        if e["group_id"] != group_id:
            raise ReviewContractError(where + ": group mismatch")
        if e["event_type"] not in _EVENTS:
            raise ReviewContractError(where + ": invalid event type")
        _when(e["occurred_at"], where + ".occurred_at")
        _entity(e["actor_ref"], where + ".actor_ref", resolve_identity)
        _text(e["consent_receipt_ref"], where + ".consent_receipt_ref")
        _text(e["audit_ref"], where + ".audit_ref")
        if dissolved:
            raise ReviewContractError(where + ": event after hypothetical dissolution")
        if type(e["expected_version"]) is not int or e["expected_version"] != version:
            raise ReviewContractError(where + ": stale or noninteger expected_version")
        if type(e["new_version"]) is not int or e["new_version"] != version + 1:
            raise ReviewContractError(where + ": invalid next version")
        if e["event_type"] == "dissolve":
            if e["member_ref"] is not None:
                raise ReviewContractError(where + ": dissolution has no member delta")
            dissolved = True
        else:
            member = _entity(e["member_ref"], where + ".member_ref", resolve_identity)
            if e["event_type"] == "add_member":
                if member in member_set:
                    raise ReviewContractError(where + ": member already present")
                member_set.add(member)
            elif e["event_type"] == "remove_member":
                if member not in member_set:
                    raise ReviewContractError(where + ": missing member")
                member_set.remove(member)
        version += 1
    return {
        "status": "reviewable_synthetic_contract_only",
        "proposed_event_count": len(events),
        "final_hypothetical_version": version,
        "consent_verified": "no",
        "identity_authority_changed": "no",
    }

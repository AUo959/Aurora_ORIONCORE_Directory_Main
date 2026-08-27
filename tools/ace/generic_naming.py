"""CanonRec naming-admission support for ACE generic L2 entities."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .core import (
    ACEError,
    CANONREC_REL,
    CANONREC_TOOL_REL,
    NAME_SERVICE_REL,
    ROOT,
    build_name_reservation_projection,
    load_module,
)

_NAME_TYPE_BY_KIND = {
    "ship": "SHIP",
    "fleet": "SHIP",
    "mobile_asset": "SHIP",
    "ship_class": "SHIP",
    "location": "LOCATION",
    "place": "LOCATION",
    "facility": "LOCATION",
    "domain": "LOCATION",
    "anomaly": "LOCATION",
    "polity": "FACTION",
    "organization": "FACTION",
    "conflict": "CONFLICT",
    "event": "OPERATION",
    "report": "OPERATION",
}


def _name_registry(root: Path) -> tuple[Any, dict[str, Any]]:
    export_module = load_module(
        root / CANONREC_TOOL_REL / "export_name_registry.py",
        "ace_generic_name_registry_export",
    )
    raw_registry = export_module.build_registry((root / CANONREC_REL).resolve())
    if not isinstance(raw_registry, Mapping) or not isinstance(raw_registry.get("entries"), list):
        raise ACEError("CanonRec name registry export is invalid", code="output_validation_failed")
    naming = load_module(root / NAME_SERVICE_REL, "ace_generic_gumas_naming")
    projection = build_name_reservation_projection(raw_registry["entries"])
    entries = [naming.RegistryEntry(**row) for row in projection["reservations"]]
    return naming.NameRegistry(entries), dict(raw_registry)


def _query_context(query: Mapping[str, Any]) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    subject = query.get("subject", {})
    if not isinstance(subject, Mapping):
        raise ACEError("generic entity query subject is invalid", code="input_validation_failed")
    context = subject.get("context", {})
    if not isinstance(context, Mapping):
        raise ACEError("generic entity query context is invalid", code="input_validation_failed")
    return subject, context


def _first_text(mapping: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = mapping.get(key)
        if value is not None:
            text = str(value).strip()
            if text:
                return text
    return ""


def _optional_text(mapping: Mapping[str, Any], key: str) -> str | None:
    text = _first_text(mapping, key)
    return text or None


def _stable_seed(query: Mapping[str, Any]) -> int | None:
    generation_policy = query.get("generation_policy", {})
    if not isinstance(generation_policy, Mapping):
        return None
    value = generation_policy.get("stable_seed")
    return value if isinstance(value, int) else None


def _naming_inputs(query: Mapping[str, Any]) -> dict[str, Any]:
    subject, context = _query_context(query)
    entity_id = _first_text(context, "entity_id") or _first_text(subject, "subject_ref")
    name = _first_text(context, "name", "canonical_name")
    kind = _first_text(subject, "entity_type").casefold()
    if not all((entity_id, name, kind)):
        raise ACEError("generic entity naming requires entity_id, name, and entity_type", code="input_validation_failed")
    return {
        "entity_id": entity_id,
        "name": name,
        "kind": kind,
        "faction_context": _optional_text(context, "faction_id"),
        "region_context": _optional_text(context, "region_context"),
        "seed_hint": _stable_seed(query),
    }


def _entity_type(naming: Any, kind: str) -> Any:
    enum_name = _NAME_TYPE_BY_KIND.get(kind, "CUSTOM")
    try:
        return getattr(naming.NameEntityType, enum_name)
    except AttributeError as exc:
        raise ACEError(f"NameService does not support mapped entity type {enum_name}", code="tool_unavailable") from exc


def _name_request(naming: Any, inputs: Mapping[str, Any]) -> Any:
    return naming.NameRequest(
        entity_type=_entity_type(naming, str(inputs["kind"])),
        entity_id=str(inputs["entity_id"]),
        faction_context=inputs.get("faction_context"),
        region_context=inputs.get("region_context"),
        register=naming.NameRegister.FORMAL,
        constraints={"candidate": str(inputs["name"]), "max_warnings": 128},
        seed_hint=inputs.get("seed_hint"),
        candidate_count=1,
    )


def _resolve_name(naming: Any, registry: Any, request: Any) -> Any:
    try:
        return naming.NameService(registry).resolve(request)
    except (RuntimeError, ValueError) as exc:
        raise ACEError(
            f"generic entity name could not be admitted by NameService: {exc}",
            code="transaction_conflict",
        ) from exc


def mint_generic_naming_receipt(
    query: Mapping[str, Any],
    *,
    root: Path = ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Mint a deterministic NameService receipt for the query's selected name.

    Caller-supplied names are forced NameService candidates, never implicit
    exemptions. The same collision and crowding analysis used by the character
    pipeline therefore applies to generic L2 referents.
    """
    inputs = _naming_inputs(query)
    registry, raw_registry = _name_registry(root)
    naming = load_module(root / NAME_SERVICE_REL, "ace_generic_gumas_naming_request")
    resolution = _resolve_name(naming, registry, _name_request(naming, inputs))
    receipt = resolution.naming_receipt()
    candidate = {
        "entity_id": inputs["entity_id"],
        "name": inputs["name"],
        "naming_receipt": receipt,
    }
    return receipt, validate_generic_naming_receipt(candidate, raw_registry=raw_registry, root=root)


def _receipt_findings(
    candidate: Mapping[str, Any],
    receipt: Mapping[str, Any],
    raw_registry: Mapping[str, Any],
    *,
    root: Path,
) -> list[dict[str, Any]]:
    validator = load_module(
        root / CANONREC_TOOL_REL / "validate_naming_receipts.py",
        "ace_generic_naming_receipt_validator",
    )
    synthetic_path = Path("canon/L2/entities") / f"{candidate.get('entity_id', 'unknown')}.json"
    return validator.validate_receipt(dict(candidate), dict(receipt), synthetic_path, dict(raw_registry))


def _findings_report(findings: list[dict[str, Any]]) -> dict[str, Any]:
    blocks = [item for item in findings if item.get("level") == "BLOCK"]
    warnings = [item for item in findings if item.get("level") == "WARN"]
    if blocks:
        codes = "; ".join(str(item.get("code")) for item in blocks[:5])
        raise ACEError(
            f"generic entity failed CanonRec naming admission: {codes}",
            code="output_validation_failed",
        )
    return {
        "passed": True,
        "blocks": [],
        "warnings": warnings,
        "findings": findings,
        "validator_ref": "aurora-canon-reconciler/scripts/validate_naming_receipts.py",
    }


def validate_generic_naming_receipt(
    candidate: Mapping[str, Any],
    *,
    raw_registry: Mapping[str, Any] | None = None,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Run CanonRec's owner naming gate against one generic candidate."""
    receipt = candidate.get("naming_receipt")
    if not isinstance(receipt, Mapping):
        raise ACEError(
            "new named generic L2 entities require a CanonRec naming_receipt",
            code="output_validation_failed",
        )
    registry = raw_registry
    if registry is None:
        _, registry = _name_registry(root)
    findings = _receipt_findings(candidate, receipt, registry, root=root)
    return _findings_report(findings)

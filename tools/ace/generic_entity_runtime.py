"""Registered runtime wrapper for generic native L2 entity completion.

The wrapper injects exact discovered capability digests, mints CanonRec naming
admission evidence, and adapts the generic engine's in-memory determination to
ACE's existing path-based schema validator.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Mapping

from . import generic_entity as engine
from .capability_discovery import load_capability_manifests
from .core import ACEError, ROOT
from .generic_entity_validation import (
    assert_native_entity_tree_readable,
    payload_validator_binding,
)
from .generic_naming import mint_generic_naming_receipt
from .runtime_binding import _git_blob_sha

_GENERIC_NAMING_REL = Path("tools/ace/generic_naming.py")
_GENERIC_NAMING_BLOB = "3059542cfd051427464f3ef88c127c8bb463e8e9"


def _manifest_digest(capability_id: str, *, root: Path) -> str:
    matches = [
        record["manifest"]
        for record in load_capability_manifests(root)
        if record["manifest"].get("capability_id") == capability_id
    ]
    if len(matches) != 1:
        raise ACEError(
            f"generic entity execution requires exactly one manifest for {capability_id}",
            code="invalid_manifest",
        )
    return str(matches[0]["trust"]["manifest_sha256"])


def _assert_naming_dependency(root: Path) -> None:
    source = (root / _GENERIC_NAMING_REL).resolve()
    if not source.is_file() or _git_blob_sha(source) != _GENERIC_NAMING_BLOB:
        raise ACEError(
            "generic naming helper changed without an updated runtime binding",
            code="stale_manifest",
        )


def _inject_naming_receipt(query: Mapping[str, Any], *, root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    _assert_naming_dependency(root)
    payload = copy.deepcopy(dict(query))
    receipt, validation = mint_generic_naming_receipt(payload, root=root)
    subject = payload.get("subject")
    if not isinstance(subject, dict):
        raise ACEError("generic entity query subject must be mutable object data", code="input_validation_failed")
    context = subject.get("context")
    if not isinstance(context, dict):
        raise ACEError("generic entity query context must be mutable object data", code="input_validation_failed")
    fields = context.get("canonical_fields", {})
    if not isinstance(fields, dict):
        raise ACEError("generic entity canonical_fields must be object data", code="input_validation_failed")
    fields.pop("naming_exemption", None)
    fields["naming_receipt"] = receipt
    context["canonical_fields"] = fields
    return payload, validation


def resolve_generic_entity_query(
    query: Mapping[str, Any],
    output_dir: Path,
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    payload, _naming_validation = _inject_naming_receipt(query, root=root)
    payload["runtime_manifest_sha256"] = _manifest_digest(engine.GENERIC_RESOLVER_CAPABILITY, root=root)
    payload["materializer_manifest_sha256"] = _manifest_digest(engine.GENERIC_MATERIALIZER_CAPABILITY, root=root)
    output = output_dir.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    assert_native_entity_tree_readable(root / engine.CANONREC_REL)
    with payload_validator_binding(engine):
        return engine.resolve_generic_entity_query(payload, output, root=root)

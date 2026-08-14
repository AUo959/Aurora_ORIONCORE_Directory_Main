"""Registered runtime wrapper for generic native L2 entity completion.

The wrapper injects exact discovered capability digests and adapts the generic
engine's in-memory determination to ACE's existing path-based schema validator.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from . import generic_entity as engine
from .capability_discovery import load_capability_manifests
from .core import ACEError, ROOT
from .generic_entity_validation import (
    assert_native_entity_tree_readable,
    payload_validator_binding,
)


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


def resolve_generic_entity_query(
    query: Mapping[str, Any],
    output_dir: Path,
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    payload = dict(query)
    payload["runtime_manifest_sha256"] = _manifest_digest(engine.GENERIC_RESOLVER_CAPABILITY, root=root)
    payload["materializer_manifest_sha256"] = _manifest_digest(engine.GENERIC_MATERIALIZER_CAPABILITY, root=root)
    output = output_dir.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    assert_native_entity_tree_readable(root / engine.CANONREC_REL)
    with payload_validator_binding(engine):
        return engine.resolve_generic_entity_query(payload, output, root=root)

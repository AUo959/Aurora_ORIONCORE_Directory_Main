"""Adapters that preserve ACE's path-based JSON Schema validation contract."""

from __future__ import annotations

import json
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping

from .core import ACEError, ROOT, validate_json_schema as validate_json_schema_file, write_json

_VALIDATOR_BINDING_LOCK = threading.RLock()
_NATIVE_ENTITY_ROOT = Path("canon/L2/entities")


def validate_json_payload(
    payload: Mapping[str, Any],
    schema: Path,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Validate an in-memory payload through ACE's existing artifact validator."""
    with tempfile.TemporaryDirectory(prefix="ace-generic-validation-") as directory:
        artifact = Path(directory) / "artifact.json"
        write_json(artifact, payload)
        return validate_json_schema_file(artifact, schema, root)


@contextmanager
def payload_validator_binding(engine_module: Any) -> Iterator[None]:
    """Temporarily bind payload validation without leaking process-global state.

    The generic engine predates its in-memory validation adapter and imports the
    path-based validator into module scope. Until that engine signature is
    widened, serialize the compatibility binding and always restore the original
    function, including on exceptions. Public generic resolver/materializer
    paths use this context so concurrent remote calls cannot race on the binding.
    """
    with _VALIDATOR_BINDING_LOCK:
        original = engine_module.validate_json_schema
        engine_module.validate_json_schema = validate_json_payload
        try:
            yield
        finally:
            engine_module.validate_json_schema = original


def assert_native_entity_tree_readable(
    canonrec: Path,
    target_root: Path = _NATIVE_ENTITY_ROOT,
) -> None:
    """Fail closed if an existing native entity record cannot be inspected.

    Identity collision checks are a publication safety boundary. Treat malformed
    or non-object canonical records as repository-integrity failures rather than
    silently skipping them and potentially missing a collision.
    """
    entity_root = canonrec.expanduser().resolve() / target_root
    if not entity_root.exists():
        return
    if not entity_root.is_dir():
        raise ACEError("CanonRec native entity surface is not a directory", code="invalid_manifest")
    for path in sorted(entity_root.rglob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ACEError(
                f"CanonRec native entity record is unreadable: {path.relative_to(canonrec).as_posix()}",
                code="invalid_manifest",
            ) from exc
        if not isinstance(payload, Mapping):
            raise ACEError(
                f"CanonRec native entity record must be a JSON object: {path.relative_to(canonrec).as_posix()}",
                code="invalid_manifest",
            )

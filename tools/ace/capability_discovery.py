"""Validated capability-manifest discovery for the Aurora Canon Engine (ACE).

Capability manifests are declarative metadata. They can describe an executable
surface, but they never select or import arbitrary code. Runtime binding remains
an explicit allowlist in the invocation layer.
"""

from __future__ import annotations

import copy
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

from .core import (
    ACEError,
    CANONREC_REL,
    CLOUDBANK_REL,
    ENGINE_VERSION,
    ROOT,
    SCHEMA_VERSION,
    file_sha256,
    repository_baselines,
    semantic_sha256,
    utc_now,
)

CAPABILITY_MANIFEST_DIR = Path("catalog/ace/capability_manifests")
CAPABILITY_SCHEMA_REL = Path("catalog/schemas/aurora_ace_capability_manifest.schema.json")
MANIFEST_HASH_PLACEHOLDER = "0" * 64


def _schema_type_matches(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "object":
        return isinstance(value, Mapping)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    return False


def _resolve_local_ref(root_schema: Mapping[str, Any], reference: str) -> Mapping[str, Any]:
    if not reference.startswith("#/"):
        raise ACEError(
            f"ACE capability schema uses unsupported non-local reference: {reference}",
            code="invalid_manifest",
        )
    node: Any = root_schema
    for token in reference[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, Mapping) or token not in node:
            raise ACEError(
                f"ACE capability schema reference cannot be resolved: {reference}",
                code="invalid_manifest",
            )
        node = node[token]
    if not isinstance(node, Mapping):
        raise ACEError(
            f"ACE capability schema reference is not an object: {reference}",
            code="invalid_manifest",
        )
    return node


def _validate_schema_node(
    value: Any,
    schema: Mapping[str, Any],
    root_schema: Mapping[str, Any],
    *,
    path: str,
) -> None:
    if "$ref" in schema:
        _validate_schema_node(
            value,
            _resolve_local_ref(root_schema, str(schema["$ref"])),
            root_schema,
            path=path,
        )
        return

    if "const" in schema and value != schema["const"]:
        raise ACEError(
            f"capability manifest {path} must equal {schema['const']!r}",
            code="invalid_manifest",
        )
    if "enum" in schema and value not in schema["enum"]:
        raise ACEError(
            f"capability manifest {path} has unsupported value {value!r}",
            code="invalid_manifest",
        )

    expected = schema.get("type")
    if expected is not None:
        choices = [expected] if isinstance(expected, str) else list(expected)
        if not any(_schema_type_matches(value, str(choice)) for choice in choices):
            raise ACEError(
                f"capability manifest {path} has invalid type",
                code="invalid_manifest",
            )

    if isinstance(value, Mapping):
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                raise ACEError(
                    f"capability manifest {path}.{key} is required",
                    code="invalid_manifest",
                )
        if schema.get("additionalProperties") is False:
            extras = sorted(set(value) - set(properties))
            if extras:
                raise ACEError(
                    f"capability manifest {path} contains unsupported fields: {extras}",
                    code="invalid_manifest",
                )
        for key, child in value.items():
            child_schema = properties.get(key)
            if isinstance(child_schema, Mapping):
                _validate_schema_node(child, child_schema, root_schema, path=f"{path}.{key}")

    if isinstance(value, list):
        minimum = schema.get("minItems")
        if isinstance(minimum, int) and len(value) < minimum:
            raise ACEError(
                f"capability manifest {path} requires at least {minimum} item(s)",
                code="invalid_manifest",
            )
        if schema.get("uniqueItems"):
            canonical = [
                json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                for item in value
            ]
            if len(canonical) != len(set(canonical)):
                raise ACEError(
                    f"capability manifest {path} must contain unique items",
                    code="invalid_manifest",
                )
        item_schema = schema.get("items")
        if isinstance(item_schema, Mapping):
            for index, item in enumerate(value):
                _validate_schema_node(item, item_schema, root_schema, path=f"{path}[{index}]")

    if isinstance(value, str):
        minimum = schema.get("minLength")
        if isinstance(minimum, int) and len(value) < minimum:
            raise ACEError(
                f"capability manifest {path} must not be empty",
                code="invalid_manifest",
            )
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.search(pattern, value) is None:
            raise ACEError(
                f"capability manifest {path} does not match required pattern",
                code="invalid_manifest",
            )
        if schema.get("format") == "date-time":
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ACEError(
                    f"capability manifest {path} must be an RFC 3339 date-time",
                    code="invalid_manifest",
                ) from exc

    if isinstance(value, int) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        if isinstance(minimum, int) and value < minimum:
            raise ACEError(
                f"capability manifest {path} must be >= {minimum}",
                code="invalid_manifest",
            )


def manifest_semantic_sha256(payload: Mapping[str, Any]) -> str:
    """Hash a manifest without a self-referential trust digest."""
    normalized = copy.deepcopy(dict(payload))
    trust = normalized.get("trust")
    if not isinstance(trust, dict):
        raise ACEError("capability manifest trust must be an object", code="invalid_manifest")
    trust["manifest_sha256"] = MANIFEST_HASH_PLACEHOLDER
    return semantic_sha256(normalized)


def validate_capability_manifest(
    payload: Mapping[str, Any],
    *,
    root: Path = ROOT,
    schema_path: Path | None = None,
) -> None:
    """Validate one capability record against the committed v0.1.1 schema."""
    schema_file = schema_path or (root / CAPABILITY_SCHEMA_REL)
    try:
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ACEError(
            f"ACE capability schema cannot be loaded: {schema_file}",
            code="invalid_manifest",
        ) from exc
    if not isinstance(schema, Mapping):
        raise ACEError("ACE capability schema must be an object", code="invalid_manifest")
    _validate_schema_node(payload, schema, schema, path="$")

    if payload["tool"]["tool_id"] != payload["capability_id"]:
        raise ACEError(
            f"capability manifest tool_id must match capability_id: {payload.get('capability_id')}",
            code="invalid_manifest",
        )
    trust = payload["trust"]
    if CAPABILITY_SCHEMA_REL.as_posix() not in trust["validation_refs"]:
        raise ACEError(
            f"capability manifest omits the ACE capability schema validation ref: {payload.get('capability_id')}",
            code="invalid_manifest",
        )
    if CAPABILITY_MANIFEST_DIR.as_posix() not in trust["discovery_sources"]:
        raise ACEError(
            f"capability manifest omits the canonical discovery source: {payload.get('capability_id')}",
            code="invalid_manifest",
        )

    expected_digest = manifest_semantic_sha256(payload)
    if trust["manifest_sha256"] != expected_digest:
        raise ACEError(
            f"capability manifest digest mismatch for {payload.get('capability_id')}",
            code="invalid_manifest",
        )


def _manifest_sources(root: Path, manifest_path: Path | None) -> list[Path]:
    source = manifest_path or (root / CAPABILITY_MANIFEST_DIR)
    if source.is_file():
        return [source]
    if source.is_dir():
        files = sorted(path for path in source.glob("*.jsonl") if path.is_file())
        if files:
            return files
    raise ACEError(f"ACE capability manifest catalog is missing: {source}", code="missing_tool")


def _manifest_source_ref(source: Path, root: Path) -> str:
    try:
        return source.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(source)


def load_capability_manifests(
    root: Path = ROOT,
    *,
    manifest_path: Path | None = None,
    schema_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Load, validate, de-duplicate, and deterministically order manifest records."""
    records: list[dict[str, Any]] = []
    seen: dict[str, str] = {}
    for source in _manifest_sources(root, manifest_path):
        for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ACEError(
                    f"invalid capability manifest JSON at {source}:{line_number}",
                    code="invalid_manifest",
                ) from exc
            if not isinstance(payload, Mapping):
                raise ACEError(
                    f"capability manifest at {source}:{line_number} must be an object",
                    code="invalid_manifest",
                )
            validate_capability_manifest(payload, root=root, schema_path=schema_path)
            capability_id = str(payload["capability_id"])
            location = f"{source}:{line_number}"
            if capability_id in seen:
                raise ACEError(
                    f"duplicate ACE capability_id {capability_id!r} at {seen[capability_id]} and {location}",
                    code="invalid_manifest",
                )
            seen[capability_id] = location
            records.append(
                {
                    "manifest": dict(payload),
                    "manifest_source": _manifest_source_ref(source, root),
                    "manifest_line": line_number,
                }
            )
    if not records:
        raise ACEError("ACE capability manifest catalog contains no records", code="invalid_manifest")
    records.sort(key=lambda item: str(item["manifest"]["capability_id"]))
    return records


def _repository_roots(root: Path) -> dict[str, Path]:
    return {
        "root": root,
        "CanonRec": root / CANONREC_REL,
        "aurora-cloudbank-symbolic-main": root / CLOUDBANK_REL,
    }


def _verify_selected_manifest(
    manifest: Mapping[str, Any],
    *,
    root: Path,
) -> None:
    trust = manifest["trust"]
    if trust["allowlisted"] is not True:
        raise ACEError(
            f"ACE capability is not allowlisted: {manifest['capability_id']}",
            code="tool_unavailable",
        )
    repository = str(manifest["tool"]["repository"])
    roots = _repository_roots(root)
    if repository not in roots:
        raise ACEError(
            f"ACE capability references an unregistered runtime repository: {repository}",
            code="invalid_manifest",
        )
    source = roots[repository] / str(manifest["tool"]["path"])
    if not source.exists():
        raise ACEError(
            f"allowlisted ACE capability source is missing: {source}",
            code="missing_tool",
        )
    freshness = manifest["freshness"]
    if freshness["current_head_required"]:
        heads = {
            item["repository"]: item["commit_sha"]
            for item in repository_baselines(root)
        }
        if freshness["repository_sha"] != heads.get(repository):
            raise ACEError(
                f"ACE capability manifest is stale for {manifest['capability_id']}",
                code="stale_manifest",
            )


def build_capability_index(root: Path = ROOT) -> dict[str, Any]:
    """Build the warm ACE index exclusively from validated committed manifests."""
    baselines = repository_baselines(root)
    heads = {item["repository"]: item["commit_sha"] for item in baselines}
    roots = _repository_roots(root)
    capabilities: list[dict[str, Any]] = []

    for record in load_capability_manifests(root):
        manifest = record["manifest"]
        repository = str(manifest["tool"]["repository"])
        if repository not in roots or repository not in heads:
            raise ACEError(
                f"capability {manifest['capability_id']} references unregistered repository {repository}",
                code="invalid_manifest",
            )
        freshness = manifest["freshness"]
        if freshness["current_head_required"] and freshness["repository_sha"] != heads[repository]:
            raise ACEError(
                f"capability manifest is stale for {manifest['capability_id']}: "
                f"manifest={freshness['repository_sha']}, observed={heads[repository]}",
                code="stale_manifest",
            )

        source = roots[repository] / str(manifest["tool"]["path"])
        lifecycle = str(manifest["lifecycle"]["status"])
        reason = str(manifest["lifecycle"]["status_reason"])
        if lifecycle == "active" and not source.exists():
            lifecycle = "unavailable"
            reason = f"Allowlisted source is missing: {source}"
        descriptor = {
            "capability_id": manifest["capability_id"],
            "name": manifest["name"],
            "repository": repository,
            "repository_sha": heads[repository],
            "path": manifest["tool"]["path"],
            "entrypoint": manifest["tool"]["entrypoint"],
            "source_sha256": file_sha256(source) if source.is_file() else None,
            "operations": list(manifest["domain"]["operations"]),
            "entity_types": list(manifest["domain"]["entity_types"]),
            "capability_tags": list(manifest["domain"]["capability_tags"]),
            "mutation_model": manifest["contract"]["mutation_model"],
            "lifecycle": lifecycle,
            "status_reason": reason,
            "selection_priority": manifest["composition"]["selection_priority"],
            "allowlisted": manifest["trust"]["allowlisted"],
            "manifest_sha256": manifest["trust"]["manifest_sha256"],
            "manifest_source": record["manifest_source"],
            "manifest_line": record["manifest_line"],
        }
        capabilities.append(descriptor)

    capabilities.sort(key=lambda item: str(item["capability_id"]))
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "ace_warm_capability_index",
        "engine_version": ENGINE_VERSION,
        "generated_at": utc_now(),
        "manifest_schema_ref": CAPABILITY_SCHEMA_REL.as_posix(),
        "manifest_catalog_ref": CAPABILITY_MANIFEST_DIR.as_posix(),
        "baselines": baselines,
        "capabilities": capabilities,
    }


def select_invocation_capability(
    query: Mapping[str, Any],
    *,
    root: Path | None = None,
    manifest_path: Path | None = None,
    schema_path: Path | None = None,
) -> dict[str, Any]:
    """Select one active invocation resolver from manifests, never from code discovery."""
    selected_root = root or ROOT
    subject = query.get("subject")
    if isinstance(subject, Mapping):
        entity_type = str(subject.get("entity_type") or "character")
    else:
        entity_type = "character"
    query_kind = str(query.get("query_kind") or "complete")

    candidates: list[tuple[tuple[int, int], dict[str, Any]]] = []
    for record in load_capability_manifests(
        selected_root,
        manifest_path=manifest_path,
        schema_path=schema_path,
    ):
        manifest = record["manifest"]
        if manifest["lifecycle"]["status"] != "active" or manifest["trust"]["allowlisted"] is not True:
            continue
        domain = manifest["domain"]
        tags = set(domain["capability_tags"])
        if "invocation_resolver" not in tags or "resolve_query" not in domain["operations"]:
            continue
        if entity_type not in domain["entity_types"]:
            continue
        exact = f"query_kind:{query_kind}" in tags
        wildcard = "query_kind:*" in tags
        if not exact and not wildcard:
            continue
        rank = (1 if exact else 0, int(manifest["composition"]["selection_priority"]))
        candidates.append((rank, record))

    if not candidates:
        raise ACEError(
            f"no discovered ACE resolver capability matches entity_type={entity_type!r}, query_kind={query_kind!r}",
            code="input_validation_failed",
        )
    candidates.sort(
        key=lambda item: (
            -item[0][0],
            -item[0][1],
            str(item[1]["manifest"]["capability_id"]),
        )
    )
    best_rank = candidates[0][0]
    tied = [item for item in candidates if item[0] == best_rank]
    if len(tied) != 1:
        ids = sorted(str(item[1]["manifest"]["capability_id"]) for item in tied)
        raise ACEError(
            f"ambiguous ACE resolver capability selection for {entity_type}/{query_kind}: {ids}",
            code="invalid_manifest",
        )

    record = candidates[0][1]
    manifest = record["manifest"]
    _verify_selected_manifest(manifest, root=selected_root)
    return {
        "capability_id": manifest["capability_id"],
        "entrypoint": manifest["tool"]["entrypoint"],
        "manifest_sha256": manifest["trust"]["manifest_sha256"],
        "manifest_source": record["manifest_source"],
        "manifest_line": record["manifest_line"],
    }

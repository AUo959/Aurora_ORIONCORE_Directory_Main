"""Verified dynamic runtime binding for ACE capability manifests.

A capability manifest is necessary but never sufficient to execute Python. A
second committed binding registry names the importable module/callable and pins
the exact Git blob. New executable capabilities can therefore be registered
without editing the invocation router while catalog mutation alone cannot turn
into arbitrary code execution.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import re
from pathlib import Path
from typing import Any, Callable, Mapping

from .capability_discovery import load_capability_manifests, select_invocation_capability
from .core import ACEError, ROOT, write_json
from .invocation import validate_invocation_envelope

BINDING_REGISTRY_REL = Path("catalog/ace/runtime_bindings.json")
BINDING_REGISTRY_VERSION = "1.0.0"
_MODULE = re.compile(r"^ace(?:\.[A-Za-z_][A-Za-z0-9_]*)+$")
_CALLABLE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_SHA1 = re.compile(r"^[a-f0-9]{40}$")


def _git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()  # noqa: S324 - Git object identity, not cryptographic auth


def _safe_source(root: Path, rel_value: str) -> Path:
    rel = Path(rel_value)
    if rel.is_absolute() or ".." in rel.parts or rel_value.startswith("~"):
        raise ACEError("ACE runtime binding source path is unsafe", code="invalid_manifest")
    root_resolved = root.resolve()
    source = (root_resolved / rel).resolve()
    if source == root_resolved or root_resolved not in source.parents:
        raise ACEError("ACE runtime binding source escaped OrionCore", code="invalid_manifest")
    return source


def load_runtime_binding_registry(
    *,
    root: Path = ROOT,
    binding_path: Path | None = None,
) -> dict[str, dict[str, Any]]:
    path = binding_path or (root / BINDING_REGISTRY_REL)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ACEError("ACE runtime binding registry cannot be loaded", code="invalid_manifest") from exc
    if not isinstance(payload, Mapping):
        raise ACEError("ACE runtime binding registry must be an object", code="invalid_manifest")
    if payload.get("schema_version") != BINDING_REGISTRY_VERSION or payload.get("record_type") != "ace_verified_runtime_binding_registry":
        raise ACEError("unsupported ACE runtime binding registry", code="invalid_manifest")
    bindings = payload.get("bindings")
    if not isinstance(bindings, list) or not bindings:
        raise ACEError("ACE runtime binding registry has no bindings", code="invalid_manifest")

    out: dict[str, dict[str, Any]] = {}
    for item in bindings:
        if not isinstance(item, Mapping):
            raise ACEError("ACE runtime binding entry must be an object", code="invalid_manifest")
        capability_id = item.get("capability_id")
        module = item.get("module")
        callable_name = item.get("callable")
        repo = item.get("repository")
        rel = item.get("path")
        blob = item.get("git_blob_sha")
        if not all(isinstance(value, str) and value for value in (capability_id, module, callable_name, repo, rel, blob)):
            raise ACEError("ACE runtime binding entry is incomplete", code="invalid_manifest")
        if capability_id in out:
            raise ACEError(f"duplicate ACE runtime binding {capability_id!r}", code="invalid_manifest")
        if _MODULE.fullmatch(module) is None or _CALLABLE.fullmatch(callable_name) is None or _SHA1.fullmatch(blob) is None:
            raise ACEError(f"ACE runtime binding {capability_id!r} has an unsafe module/callable/blob", code="invalid_manifest")
        if repo != "root":
            raise ACEError(
                f"ACE v0.10 verified loader currently permits root-owned Python bindings only: {capability_id}",
                code="invalid_manifest",
            )
        _safe_source(root, rel)
        out[str(capability_id)] = dict(item)
    return out


def _manifest_for_capability(capability_id: str, *, root: Path) -> Mapping[str, Any]:
    matches = [
        record["manifest"]
        for record in load_capability_manifests(root)
        if record["manifest"].get("capability_id") == capability_id
    ]
    if len(matches) != 1:
        raise ACEError(f"ACE runtime binding requires exactly one manifest for {capability_id!r}", code="invalid_manifest")
    return matches[0]


def load_verified_runtime_binding(
    capability: Mapping[str, Any],
    *,
    root: Path = ROOT,
    binding_path: Path | None = None,
) -> Callable[..., dict[str, Any]]:
    capability_id = str(capability.get("capability_id") or "")
    registry = load_runtime_binding_registry(root=root, binding_path=binding_path)
    binding = registry.get(capability_id)
    if binding is None:
        raise ACEError(
            f"no verified ACE runtime binding exists for discovered capability {capability_id!r}",
            code="tool_unavailable",
        )

    manifest = _manifest_for_capability(capability_id, root=root)
    if manifest["lifecycle"]["status"] != "active" or manifest["trust"]["allowlisted"] is not True:
        raise ACEError(f"ACE runtime capability is not active and allowlisted: {capability_id}", code="tool_unavailable")
    if capability.get("manifest_sha256") != manifest["trust"]["manifest_sha256"]:
        raise ACEError(f"ACE selected capability manifest digest drifted: {capability_id}", code="stale_manifest")
    if binding["repository"] != manifest["tool"]["repository"]:
        raise ACEError(f"ACE runtime binding repository disagrees with manifest: {capability_id}", code="invalid_manifest")
    if binding["path"] != manifest["tool"]["path"]:
        raise ACEError(f"ACE runtime binding path disagrees with manifest: {capability_id}", code="invalid_manifest")
    if binding["callable"] != manifest["tool"]["entrypoint"] or capability.get("entrypoint") != binding["callable"]:
        raise ACEError(f"ACE runtime binding entrypoint disagrees with manifest: {capability_id}", code="invalid_manifest")

    source = _safe_source(root, binding["path"])
    if not source.is_file():
        raise ACEError(f"ACE runtime binding source is missing: {source}", code="missing_tool")
    observed_blob = _git_blob_sha(source)
    if observed_blob != binding["git_blob_sha"]:
        raise ACEError(
            f"ACE runtime binding source changed without an updated binding receipt: {capability_id}",
            code="stale_manifest",
        )

    module = importlib.import_module(binding["module"])
    module_file = getattr(module, "__file__", None)
    if not isinstance(module_file, str) or Path(module_file).resolve() != source:
        raise ACEError(f"ACE runtime module provenance mismatch: {capability_id}", code="tool_unavailable")
    resolver = getattr(module, binding["callable"], None)
    if not callable(resolver):
        raise ACEError(f"ACE runtime entrypoint is unavailable: {capability_id}", code="tool_unavailable")
    return resolver


def resolve_verified_invocation(
    invocation: Mapping[str, Any],
    output_dir: Path,
    *,
    execution_root: Path | None = None,
    control_root: Path = ROOT,
    binding_path: Path | None = None,
) -> dict[str, Any]:
    """Execute the normal invocation envelope through the verified binding registry."""
    validate_invocation_envelope(invocation)
    query = dict(invocation["query"])
    output = output_dir.expanduser().resolve()
    sidecar = output.parent / f"{output.name}.ace-invocation.json"
    if sidecar.exists():
        raise ACEError(f"invocation sidecar already exists: {sidecar}", code="target_unavailable")

    capability = select_invocation_capability(query)
    resolver = load_verified_runtime_binding(capability, root=control_root, binding_path=binding_path)
    if execution_root is None:
        determination = resolver(query, output_dir)
    else:
        determination = resolver(query, output_dir, root=execution_root)

    payload = dict(invocation)
    payload["determination_ref"] = determination["determination_id"]
    payload["packet_ref"] = str(output)
    payload["determination_status"] = determination["status"]
    payload["runtime_binding"] = {
        "mode": "verified_dynamic",
        "capability_id": capability["capability_id"],
        "manifest_sha256": capability["manifest_sha256"],
        "binding_registry_ref": BINDING_REGISTRY_REL.as_posix(),
    }
    write_json(sidecar, payload)
    return {
        "invocation": payload,
        "determination": determination,
        "invocation_sidecar": str(sidecar),
    }

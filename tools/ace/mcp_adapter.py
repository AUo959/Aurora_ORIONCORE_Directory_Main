"""Bounded MCP adapter for the Aurora Canon Engine (ACE).

The adapter deliberately has no MCP SDK dependency so OrionCore's normal ACE
package remains independent of the transport implementation. MCP is an entry
surface, never an alternate ACE engine:

MCP -> invocation envelope -> manifest router -> shared ACE resolver
MCP -> two-phase authorization gate -> registered native ACE materializer

v0.8 adds canonical materialization only through an owner-gated, state-bound
preview/commit handshake. The MCP caller cannot provide an arbitrary target
repository path, bypass ACE packet validation, or widen the native materializer.
"""

from __future__ import annotations

import hmac
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping

import yaml

from .capability_discovery import build_capability_index, select_invocation_capability
from .character_materialize import materialize_packet
from .core import ACEError, ROOT, load_json, semantic_sha256
from .invocation import resolve_invocation, validate_invocation_envelope

MCP_ADAPTER_VERSION = "0.8.0"
MCP_RUNTIME_REL = Path("reports/ace/mcp_runtime")
MCP_LEDGER_REL = Path("reports/ace/determinations")
MCP_REGISTRY_REL = Path("catalog/repo_registry.yaml")
MCP_CANONREC_NAME = "CanonRec"
MCP_MATERIALIZATION_AUTHORITY_MODE = "owner_gated_materialize"
MCP_TOOL_NAMES = (
    "ace_capabilities",
    "ace_plan",
    "ace_resolve",
    "ace_inspect",
    "ace_materialize_preview",
    "ace_materialize_commit",
)
MAX_INSPECT_JSON_FILES = 2048
_OUTPUT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_SHA40 = re.compile(r"^[a-f0-9]{40}$")


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


def _registered_canonrec_repo(root: Path, target_repo: Path | None = None) -> Path:
    """Resolve the one registry-owned CanonRec checkout allowed to MCP."""
    if target_repo is not None:
        return target_repo.expanduser().resolve()

    registry_path = (root / MCP_REGISTRY_REL).resolve()
    try:
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ACEError("ACE MCP cannot read the repository registry", code="target_unavailable") from exc
    if not isinstance(registry, Mapping) or not isinstance(registry.get("repos"), list):
        raise ACEError("ACE MCP repository registry is malformed", code="invalid_manifest")

    matches = [
        item
        for item in registry["repos"]
        if isinstance(item, Mapping) and item.get("name") == MCP_CANONREC_NAME
    ]
    if len(matches) != 1:
        raise ACEError("ACE MCP requires exactly one registered CanonRec checkout", code="invalid_manifest")
    record = matches[0]
    rel_value = record.get("path")
    if record.get("remote_status") != "configured" or not isinstance(rel_value, str):
        raise ACEError("registered CanonRec checkout is not locally configured", code="target_unavailable")
    rel = Path(rel_value)
    if rel.is_absolute() or ".." in rel.parts or rel_value.startswith("~"):
        raise ACEError("registered CanonRec path is unsafe", code="target_unavailable")
    root_resolved = root.expanduser().resolve()
    repo = (root_resolved / rel).resolve()
    if repo == root_resolved or not _is_relative_to(repo, root_resolved):
        raise ACEError("registered CanonRec path escaped OrionCore", code="target_unavailable")
    return repo


def _git_read(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ACEError(
            f"git {' '.join(args)} failed in registered CanonRec: {completed.stderr.strip()}",
            code="target_unavailable",
        )
    return completed.stdout.strip()


def _normalize_authority_ref(authority_ref: str) -> str:
    if not isinstance(authority_ref, str):
        raise ACEError("MCP materialization requires an authority_ref string", code="materialization_authority_missing")
    value = authority_ref.strip()
    if not value or len(value) > 256 or any(ord(ch) < 32 for ch in value):
        raise ACEError(
            "MCP materialization authority_ref must be a non-empty printable string of at most 256 characters",
            code="materialization_authority_missing",
        )
    return value


def _canonrec_baseline(receipt: Mapping[str, Any]) -> str:
    for item in receipt.get("baselines", []):
        if isinstance(item, Mapping) and item.get("repository") == MCP_CANONREC_NAME:
            value = item.get("commit_sha")
            if isinstance(value, str) and _SHA40.fullmatch(value):
                return value
    raise ACEError("MCP materialization packet has no valid CanonRec baseline", code="input_validation_failed")


def _materialization_preview(
    output_name: str,
    authority_ref: str,
    *,
    root: Path = ROOT,
    runtime_root: Path | None = None,
    target_repo: Path | None = None,
) -> tuple[dict[str, Any], Path, Path]:
    packet = _safe_output_dir(output_name, root=root, runtime_root=runtime_root)
    receipt_path = packet / "determination_receipt.json"
    if not receipt_path.is_file():
        raise ACEError("MCP materialization packet has no determination_receipt.json", code="target_unavailable")
    receipt = load_json(receipt_path)
    if not isinstance(receipt, Mapping):
        raise ACEError("MCP materialization determination must be a JSON object", code="input_validation_failed")
    if receipt.get("materialization", {}).get("status") != "commit_ready":
        raise ACEError("MCP materialization requires a commit-ready ACE packet", code="input_validation_failed")

    authority = _normalize_authority_ref(authority_ref)
    repo = _registered_canonrec_repo(root, target_repo)
    if not repo.is_dir():
        raise ACEError("registered CanonRec checkout is unavailable", code="target_unavailable")
    if _git_read(repo, "rev-parse", "--is-inside-work-tree") != "true":
        raise ACEError("registered CanonRec target is not a Git worktree", code="target_unavailable")
    if _git_read(repo, "status", "--porcelain"):
        raise ACEError("MCP materialization requires a clean CanonRec worktree", code="transaction_conflict")
    branch = _git_read(repo, "branch", "--show-current")
    if not branch or branch in {"main", "master"}:
        raise ACEError(
            "MCP materialization requires CanonRec to be on a non-protected feature branch",
            code="materialization_authority_missing",
        )
    head = _git_read(repo, "rev-parse", "HEAD")
    expected_head = _canonrec_baseline(receipt)
    if head != expected_head:
        raise ACEError(
            f"CanonRec baseline advanced ({expected_head} -> {head}); recompile before materialization",
            code="registry_baseline_advanced",
        )

    token_payload = {
        "schema_version": MCP_ADAPTER_VERSION,
        "kind": "ace_mcp_materialization_authorization",
        "output_name": output_name,
        "packet_digest": semantic_sha256(receipt),
        "authority_mode": MCP_MATERIALIZATION_AUTHORITY_MODE,
        "authority_ref": authority,
        "target_repository": MCP_CANONREC_NAME,
        "target_branch": branch,
        "target_head": head,
        "expected_baseline": expected_head,
    }
    token = "ace-mcp-auth:" + semantic_sha256(token_payload)
    preview = {
        "schema_version": MCP_ADAPTER_VERSION,
        "record_type": "ace_mcp_materialization_preview",
        "transport": "stdio",
        "materialization_exposed": True,
        "output_name": output_name,
        "packet_ref": str(packet),
        "packet_digest": token_payload["packet_digest"],
        "target_repository": MCP_CANONREC_NAME,
        "target_branch": branch,
        "target_head": head,
        "expected_baseline": expected_head,
        "authority_mode": MCP_MATERIALIZATION_AUTHORITY_MODE,
        "authority_ref": authority,
        "declared_side_effects": [
            "write_declared_canonical_target(s)_inside_registered_CanonRec",
            "create_one_CanonRec_git_commit",
            "append_pre_and_post_materialization_ACE_determinations",
        ],
        "authorization_token": token,
        "confirmation_required": True,
        "token_binding": "packet+authority+registered-target+feature-branch+baseline",
        "token_reuse_after_commit": False,
    }
    return preview, packet, repo


def ace_capabilities(*, root: Path = ROOT) -> dict[str, Any]:
    """Return ACE's manifest-derived capability index through the MCP surface."""
    return {
        "schema_version": MCP_ADAPTER_VERSION,
        "record_type": "ace_mcp_capabilities",
        "transport": "stdio",
        "materialization_exposed": True,
        "materialization_policy": "owner_gated_two_phase_registered_canonrec_only",
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
        "side_effect_class": "read_only",
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
        "side_effect_class": "bounded_runtime_artifact_write",
        "output_name": output_name,
        "packet_ref": str(output_dir),
        "invocation": result["invocation"],
        "determination": result["determination"],
        "invocation_sidecar": result["invocation_sidecar"],
    }


def ace_materialize_preview(
    output_name: str,
    authority_ref: str,
    *,
    root: Path = ROOT,
    runtime_root: Path | None = None,
    target_repo: Path | None = None,
) -> dict[str, Any]:
    """Preview one owner-gated native materialization without changing canon."""
    preview, _, _ = _materialization_preview(
        output_name,
        authority_ref,
        root=root,
        runtime_root=runtime_root,
        target_repo=target_repo,
    )
    return preview


def ace_materialize_commit(
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
    """Execute one state-bound native materialization after explicit confirmation."""
    if side_effects_acknowledged is not True:
        raise ACEError(
            "MCP materialization requires explicit acknowledgement of the previewed side effects",
            code="materialization_authority_missing",
        )
    if not isinstance(authorization_token, str) or not authorization_token.startswith("ace-mcp-auth:"):
        raise ACEError("MCP materialization requires a preview authorization token", code="materialization_authority_missing")

    preview, packet, repo = _materialization_preview(
        output_name,
        authority_ref,
        root=root,
        runtime_root=runtime_root,
        target_repo=target_repo,
    )
    if not hmac.compare_digest(authorization_token, preview["authorization_token"]):
        raise ACEError(
            "MCP materialization authorization token does not match current packet/authority/target state",
            code="materialization_authority_missing",
        )

    determination = materialize_packet(
        packet,
        repo,
        authority_mode=MCP_MATERIALIZATION_AUTHORITY_MODE,
        authority_ref=preview["authority_ref"],
        root=root,
        commit_message=commit_message,
    )
    return {
        "schema_version": MCP_ADAPTER_VERSION,
        "record_type": "ace_mcp_materialization_result",
        "transport": "stdio",
        "materialization_exposed": True,
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
    """Find inspectable ACE provenance without granting mutation authority."""
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
            linked_match = determination_id is not None and payload.get("determination_ref") == determination_id
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
        "side_effect_class": "read_only",
        "lookup": {"kind": lookup_kind, "value": lookup_value},
        "found": bool(matches),
        "match_count": len(matches),
        "matches": matches,
    }

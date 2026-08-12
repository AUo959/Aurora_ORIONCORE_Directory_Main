"""Local operator transaction choreography for ACE's bounded MCP materialization.

This layer is deliberately not another materializer and does not widen the MCP
protocol surface. It records the human/operator lifecycle around the existing
v0.8 primitives:

resolve -> preview -> explicit authorization -> commit -> inspect

Canonical mutation still occurs only through ``ace_materialize_commit`` and the
registered native ACE materializer. The operator receipt is durable control-plane
provenance; it is not canon and its authorization token is not an identity
credential.
"""

from __future__ import annotations

import hmac
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Mapping

from .core import ACEError, ROOT, semantic_sha256, utc_now
from .mcp_adapter import (
    ace_inspect,
    ace_materialize_commit,
    ace_materialize_preview,
    ace_resolve,
)

OPERATOR_TRANSACTION_VERSION = "0.9.0"
OPERATOR_TRANSACTION_REL = Path("reports/ace/mcp_transactions")
_TRANSACTION_ID = re.compile(r"^ace\.mcp\.operator\.[a-f0-9]{24}$")


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _transaction_root(root: Path, transaction_root: Path | None = None) -> Path:
    root_resolved = root.expanduser().resolve()
    base = (transaction_root or (root_resolved / OPERATOR_TRANSACTION_REL)).expanduser().resolve()
    if transaction_root is None and not _is_relative_to(base, root_resolved):
        raise ACEError("ACE MCP transaction root escaped OrionCore", code="target_unavailable")
    return base


def _transaction_path(
    transaction_id: str,
    *,
    root: Path,
    transaction_root: Path | None,
) -> Path:
    if not isinstance(transaction_id, str) or _TRANSACTION_ID.fullmatch(transaction_id) is None:
        raise ACEError("invalid ACE MCP operator transaction id", code="input_validation_failed")
    base = _transaction_root(root, transaction_root)
    path = (base / f"{transaction_id}.json").resolve()
    if path.parent != base:
        raise ACEError("ACE MCP operator transaction path escaped its receipt root", code="target_unavailable")
    return path


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".ace-mcp-operator-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def _load_transaction(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ACEError("ACE MCP operator transaction does not exist", code="target_unavailable") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ACEError("ACE MCP operator transaction receipt is unreadable", code="target_unavailable") from exc
    if not isinstance(payload, dict) or payload.get("record_type") != "ace_mcp_operator_transaction":
        raise ACEError("ACE MCP operator transaction receipt is malformed", code="input_validation_failed")
    return payload


def prepare_operator_transaction(
    invocation: Mapping[str, Any],
    output_name: str,
    authority_ref: str,
    *,
    root: Path = ROOT,
    runtime_root: Path | None = None,
    transaction_root: Path | None = None,
    target_repo: Path | None = None,
) -> dict[str, Any]:
    """Resolve and preview one transaction, then persist its confirmation receipt."""

    resolution = ace_resolve(
        invocation,
        output_name,
        root=root,
        runtime_root=runtime_root,
    )
    preview = ace_materialize_preview(
        output_name,
        authority_ref,
        root=root,
        runtime_root=runtime_root,
        target_repo=target_repo,
    )
    determination = resolution.get("determination")
    if not isinstance(determination, Mapping):
        raise ACEError("ACE MCP resolution did not return a determination", code="output_validation_failed")
    determination_id = determination.get("determination_id")
    invocation_id = resolution.get("invocation", {}).get("invocation_id")
    if not isinstance(determination_id, str) or not isinstance(invocation_id, str):
        raise ACEError("ACE MCP resolution provenance is incomplete", code="output_validation_failed")

    prepared_basis = {
        "schema_version": OPERATOR_TRANSACTION_VERSION,
        "invocation_id": invocation_id,
        "determination_id": determination_id,
        "output_name": output_name,
        "packet_digest": preview["packet_digest"],
        "authority_mode": preview["authority_mode"],
        "authority_ref": preview["authority_ref"],
        "target_repository": preview["target_repository"],
        "target_branch": preview["target_branch"],
        "target_head": preview["target_head"],
        "expected_baseline": preview["expected_baseline"],
    }
    prepared_digest = semantic_sha256(prepared_basis)
    transaction_id = f"ace.mcp.operator.{prepared_digest[:24]}"
    path = _transaction_path(
        transaction_id,
        root=root,
        transaction_root=transaction_root,
    )

    if path.exists():
        existing = _load_transaction(path)
        if existing.get("prepared_digest") != prepared_digest:
            raise ACEError("ACE MCP operator transaction digest collision", code="transaction_conflict")
        return existing

    now = utc_now()
    receipt: dict[str, Any] = {
        "schema_version": OPERATOR_TRANSACTION_VERSION,
        "record_type": "ace_mcp_operator_transaction",
        "transaction_id": transaction_id,
        "created_at": now,
        "updated_at": now,
        "status": "awaiting_confirmation",
        "transport": "stdio",
        "operator_layer": "local_explicit_authorization",
        "prepared_digest": prepared_digest,
        "resolution": {
            "invocation_id": invocation_id,
            "determination_id": determination_id,
            "determination_digest": semantic_sha256(determination),
            "output_name": output_name,
            "packet_ref": resolution.get("packet_ref"),
        },
        "preview": preview,
        "authorization": {
            "required": True,
            "authority_mode": preview["authority_mode"],
            "authority_ref": preview["authority_ref"],
            "side_effects_acknowledged": False,
        },
        "required_operator_action": (
            "Review declared_side_effects, then commit using this transaction_id, "
            "the exact preview authorization_token, and side_effects_acknowledged=true."
        ),
        "result": None,
        "post_commit_inspection": None,
        "refusal": None,
        "replay_guard": {
            "closed": False,
            "authorization_token_reuse_permitted": False,
        },
    }
    _write_json_atomic(path, receipt)
    return receipt


def commit_operator_transaction(
    transaction_id: str,
    authorization_token: str,
    side_effects_acknowledged: bool,
    commit_message: str | None = None,
    *,
    root: Path = ROOT,
    runtime_root: Path | None = None,
    transaction_root: Path | None = None,
    target_repo: Path | None = None,
) -> dict[str, Any]:
    """Commit one prepared transaction exactly once, then inspect its provenance."""

    path = _transaction_path(
        transaction_id,
        root=root,
        transaction_root=transaction_root,
    )
    receipt = _load_transaction(path)
    if receipt.get("transaction_id") != transaction_id:
        raise ACEError("ACE MCP operator transaction id mismatch", code="input_validation_failed")
    if receipt.get("status") != "awaiting_confirmation":
        raise ACEError(
            f"ACE MCP operator transaction is not awaiting confirmation: {receipt.get('status')}",
            code="transaction_conflict",
        )
    if side_effects_acknowledged is not True:
        raise ACEError(
            "ACE MCP operator commit requires explicit side-effect acknowledgement",
            code="materialization_authority_missing",
        )

    preview = receipt.get("preview")
    if not isinstance(preview, Mapping):
        raise ACEError("ACE MCP operator transaction has no valid preview", code="input_validation_failed")
    expected_token = preview.get("authorization_token")
    if not isinstance(expected_token, str) or not isinstance(authorization_token, str):
        raise ACEError("ACE MCP operator transaction requires its preview token", code="materialization_authority_missing")
    if not hmac.compare_digest(expected_token, authorization_token):
        raise ACEError(
            "ACE MCP operator authorization token does not match the prepared transaction",
            code="materialization_authority_missing",
        )

    receipt["status"] = "commit_in_progress"
    receipt["updated_at"] = utc_now()
    receipt["commit_started_at"] = receipt["updated_at"]
    receipt["authorization"]["side_effects_acknowledged"] = True
    _write_json_atomic(path, receipt)

    try:
        result = ace_materialize_commit(
            str(receipt["resolution"]["output_name"]),
            str(receipt["authorization"]["authority_ref"]),
            authorization_token,
            True,
            commit_message,
            root=root,
            runtime_root=runtime_root,
            target_repo=target_repo,
        )
    except Exception as exc:
        receipt["status"] = "refused"
        receipt["updated_at"] = utc_now()
        receipt["refusal"] = {
            "at": receipt["updated_at"],
            "error_type": type(exc).__name__,
            "error_code": getattr(exc, "code", None),
            "message": str(exc),
        }
        receipt["replay_guard"]["closed"] = True
        _write_json_atomic(path, receipt)
        raise

    materialized = result.get("materialized_determination")
    if not isinstance(materialized, Mapping) or not isinstance(materialized.get("determination_id"), str):
        raise ACEError("ACE MCP materialization returned incomplete provenance", code="output_validation_failed")

    inspection: dict[str, Any]
    try:
        inspection = ace_inspect(
            determination_id=str(materialized["determination_id"]),
            root=root,
            runtime_root=runtime_root,
        )
    except Exception as exc:  # commit already succeeded; preserve that fact.
        inspection = {
            "record_type": "ace_mcp_operator_post_commit_inspection",
            "found": False,
            "status": "error",
            "error_type": type(exc).__name__,
            "error_code": getattr(exc, "code", None),
            "message": str(exc),
        }

    receipt["status"] = "committed"
    receipt["updated_at"] = utc_now()
    receipt["completed_at"] = receipt["updated_at"]
    receipt["result"] = result
    receipt["post_commit_inspection"] = inspection
    receipt["replay_guard"]["closed"] = True
    _write_json_atomic(path, receipt)
    return receipt


def inspect_operator_transaction(
    transaction_id: str,
    *,
    root: Path = ROOT,
    transaction_root: Path | None = None,
) -> dict[str, Any]:
    """Read one durable local operator transaction receipt without side effects."""

    return _load_transaction(
        _transaction_path(
            transaction_id,
            root=root,
            transaction_root=transaction_root,
        )
    )

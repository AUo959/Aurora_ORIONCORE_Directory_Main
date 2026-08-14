"""Governed single-tick Orion L1 progression for ACE v0.13."""

from __future__ import annotations

import hashlib
import importlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

from .core import ACEError, ROOT, semantic_sha256, utc_now
from .runtime_binding import _git_blob_sha

ORION_PROGRESSION_VERSION = "0.13.0"
ORION_PROGRESSION_CAPABILITY_ID = "ace.runtime.orion.l1.advance.governed"
ORION_PROGRESSION_POLICY_REL = Path("catalog/ace/policies/orion_progression_v0_13.json")
_AUTHORITY_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:@/-]{0,255}$")
_OWNER_HELPER_REL = Path("tools/ace/orion_runtime_owner.py")
_OWNER_HELPER_BLOB = "6e0f897097105de27b0421f17053b3e0ca69f9a6"
_STATE_HELPER_REL = Path("tools/ace/orion_progression_state.py")
_STATE_HELPER_BLOB = "4d090dbe55b56be8211da10498ddabea029bc521"


class OrionProgressionStateUncertain(ACEError):
    """The L1 persistence boundary may have advanced and must not be retried."""


def _assert_internal_helpers(root: Path) -> None:
    expected = {
        _OWNER_HELPER_REL: _OWNER_HELPER_BLOB,
        _STATE_HELPER_REL: _STATE_HELPER_BLOB,
    }
    for relative, expected_blob in expected.items():
        source = (root / relative).resolve()
        if not source.is_file() or _git_blob_sha(source) != expected_blob:
            raise ACEError(
                f"Orion progression dependency changed without an updated binding: {relative}",
                code="stale_manifest",
            )


def _helper_modules(root: Path) -> Tuple[Any, Any]:
    _assert_internal_helpers(root)
    owner = importlib.import_module("ace.orion_runtime_owner")
    state = importlib.import_module("ace.orion_progression_state")
    return owner, state


def _load_policy(root: Path) -> Dict[str, Any]:
    owner, _state = _helper_modules(root)
    return owner.load_orion_policy(root)


def _load_owner_runtime(root: Path) -> Dict[str, Any]:
    owner, _state = _helper_modules(root)
    return owner.load_owner_runtime(root)


def _validate_authority(
    authority_ref: str,
    principal_id: str,
    policy: Mapping[str, Any],
) -> None:
    malformed_ref = (
        not isinstance(authority_ref, str)
        or _AUTHORITY_REF.fullmatch(authority_ref) is None
    )
    if malformed_ref:
        raise ACEError(
            "Orion progression authority_ref is malformed",
            code="materialization_authority_missing",
        )
    if principal_id != policy["required_principal"]:
        raise ACEError(
            "Orion progression requires the bound Pilot principal",
            code="materialization_authority_missing",
        )


def _readiness_gate(
    report: Any,
    policy: Mapping[str, Any],
) -> Mapping[str, Any]:
    if not isinstance(report, Mapping):
        raise ACEError(
            "Orion owner preflight returned invalid evidence",
            code="output_validation_failed",
        )
    if policy["require_preflight_ready"] and report.get("ready") is not True:
        blockers = report.get("blockers", [])
        raise ACEError(
            "Orion owner preflight is not ready: "
            + "; ".join(str(item) for item in blockers),
            code="execution_blocked",
        )
    if policy["require_resume_ready"] and report.get("resume_ready") is not True:
        embodiment = report.get("embodiment", {})
        blockers = (
            embodiment.get("resume_blockers", [])
            if isinstance(embodiment, Mapping)
            else []
        )
        raise ACEError(
            "Orion owner resume gate is not ready: "
            + json.dumps(blockers, sort_keys=True, default=str),
            code="execution_blocked",
        )
    return report


def _load_snapshot(
    runtime: Any,
    run_id: str,
    run_root: Path,
    state_path: Path,
    before_sha: str,
    state: Any,
) -> Dict[str, Any]:
    runtime.load_run(run_id, run_root=run_root)
    after_load_raw, _payload = state.read_state(state_path)
    if state.sha256_bytes(after_load_raw) != before_sha:
        raise OrionProgressionStateUncertain(
            "Orion load_run mutated persisted state during a non-mutating preview",
            code="runtime_failure",
        )
    exported = runtime.export_state()
    if not isinstance(exported, Mapping):
        raise ACEError(
            "Orion runtime export is invalid",
            code="output_validation_failed",
        )
    snapshot = state.snapshot(exported, before_sha)
    if snapshot["run_id"] != run_id:
        raise ACEError(
            "Orion runtime export run_id mismatch",
            code="output_validation_failed",
        )
    return snapshot


def _authorization_payload(
    snapshot: Mapping[str, Any],
    authority_ref: str,
    principal_id: str,
    owner: Mapping[str, Any],
) -> Dict[str, Any]:
    policy = owner["policy"]
    return {
        "policy_id": policy["policy_id"],
        "capability_id": ORION_PROGRESSION_CAPABILITY_ID,
        "principal_id": principal_id,
        "authority_ref": authority_ref,
        "run": dict(snapshot),
        "execution_owner": {
            "repository": policy["cloudbank_repository"],
            "repository_sha": owner["cloudbank_sha"],
            "source_path": policy["owner"]["path"],
            "source_git_blob": owner["owner_blob_sha"],
            "class": policy["owner"]["class"],
            "advance_method": policy["owner"]["advance_method"],
        },
        "elapsed_minutes": policy["elapsed_minutes"],
        "ticks_authorized": policy["ticks_per_authorization"],
    }


def _preview_record(
    authorization: Mapping[str, Any],
    report: Mapping[str, Any],
) -> Dict[str, Any]:
    token = semantic_sha256(
        {
            "authorization": authorization,
            "receipt": "state_bound_confirmation_v1",
        }
    )
    return {
        "schema_version": ORION_PROGRESSION_VERSION,
        "record_type": "ace_orion_progression_preview",
        "created_at": utc_now(),
        "status": "ready_for_authorization",
        "authorization_token": token,
        "authorization": dict(authorization),
        "preflight": dict(report),
        "side_effects": [
            "advance_existing_orion_run_one_tick",
            "persist_orion_run_state",
        ],
        "init_allowed": False,
        "provider_activation_allowed": False,
        "remote_exposed": False,
        "mcp_exposed": False,
        "automatic_retry_allowed": False,
    }


def _prepare(
    run_id: str,
    authority_ref: str,
    principal_id: str,
    root: Path,
    run_root: Optional[Path],
) -> Tuple[Dict[str, Any], Any, Path, Dict[str, Any], Path]:
    state = _helper_modules(root)[1]
    normalized_run_id = state.canonical_run_id(run_id)
    owner = _load_owner_runtime(root)
    policy = owner["policy"]
    _validate_authority(authority_ref, principal_id, policy)
    resolved_run_root = state.resolve_run_root(run_root)
    persisted_path = state.state_path(resolved_run_root, normalized_run_id)
    before_raw, _payload = state.read_state(persisted_path)
    before_sha = state.sha256_bytes(before_raw)
    runtime = owner["runtime_class"]()
    report = _readiness_gate(runtime.preflight(), policy)
    snapshot = _load_snapshot(
        runtime,
        normalized_run_id,
        resolved_run_root,
        persisted_path,
        before_sha,
        state,
    )
    authorization = _authorization_payload(
        snapshot,
        authority_ref,
        principal_id,
        owner,
    )
    return (
        _preview_record(authorization, report),
        runtime,
        persisted_path,
        owner,
        resolved_run_root,
    )


def preview_orion_advance(
    run_id: str,
    authority_ref: str,
    principal_id: str = "ORION.ROLE.PILOT",
    *,
    root: Path = ROOT,
    run_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Return a non-mutating, state-bound preview for one native L1 tick."""
    preview, _runtime, _path, _owner, _run_root = _prepare(
        run_id,
        authority_ref,
        principal_id,
        root,
        run_root,
    )
    return preview


def _advance_owner(
    runtime: Any,
    state_path: Path,
    before: Mapping[str, Any],
    elapsed_minutes: int,
    state: Any,
) -> Any:
    try:
        return runtime.advance(elapsed_minutes=elapsed_minutes)
    except Exception as exc:
        try:
            current_raw, _payload = state.read_state(state_path)
        except Exception as read_exc:
            raise OrionProgressionStateUncertain(
                "Orion advance failed and persisted state cannot be reconciled",
                code="runtime_failure",
            ) from read_exc
        if state.sha256_bytes(current_raw) != before["state_file_sha256"]:
            raise OrionProgressionStateUncertain(
                "Orion advance raised after persisted state changed; "
                "automatic retry is forbidden",
                code="runtime_failure",
            ) from exc
        raise ACEError(
            "Orion owner advance failed before persisted state changed",
            code="runtime_failure",
        ) from exc


def _validated_after_state(
    owner: Mapping[str, Any],
    persisted_path: Path,
    run_id: str,
    run_root: Path,
    state: Any,
) -> Dict[str, Any]:
    try:
        raw, _payload = state.read_state(persisted_path)
        runtime = owner["runtime_class"]()
        _readiness_gate(runtime.preflight(), owner["policy"])
        runtime.load_run(run_id, run_root=run_root)
        exported = runtime.export_state()
        if not isinstance(exported, Mapping):
            raise RuntimeError("post-advance owner export is invalid")
        return state.snapshot(exported, state.sha256_bytes(raw))
    except OrionProgressionStateUncertain:
        raise
    except Exception as exc:
        raise OrionProgressionStateUncertain(
            "Orion persisted state changed but post-advance validation is uncertain",
            code="runtime_failure",
        ) from exc


def _progression_receipt(
    run_id: str,
    authorization_token: str,
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    event: Any,
    preview: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> Dict[str, Any]:
    authorization = preview["authorization"]
    progression_id = semantic_sha256(
        {
            "run_id": run_id,
            "after_tick": after["tick"],
            "after_state": after["state_file_sha256"],
        }
    )[:20]
    return {
        "schema_version": ORION_PROGRESSION_VERSION,
        "record_type": "ace_orion_progression_receipt",
        "progression_id": f"ace.orion.progression.{progression_id}",
        "created_at": utc_now(),
        "status": "advanced",
        "state_certainty": "confirmed",
        "capability_id": ORION_PROGRESSION_CAPABILITY_ID,
        "policy_id": policy["policy_id"],
        "principal_id": authorization["principal_id"],
        "authority_ref": authorization["authority_ref"],
        "authorization_token_sha256": hashlib.sha256(
            authorization_token.encode("ascii")
        ).hexdigest(),
        "before": dict(before),
        "after": dict(after),
        "owner": authorization["execution_owner"],
        "event": event,
        "ticks_consumed": 1,
        "automatic_retry_allowed": False,
        "canon_mutated": False,
        "provider_activation_performed": False,
        "init_performed": False,
    }


def _seal_receipt(
    receipt: Mapping[str, Any],
    run_id: str,
    tick: int,
    receipt_root: Optional[Path],
    root: Path,
    state: Any,
) -> Dict[str, Any]:
    external_root = state.resolve_receipt_root(receipt_root, root)
    path = state.receipt_path(external_root, run_id, tick)
    try:
        state.write_receipt(path, receipt)
    except Exception as exc:
        raise OrionProgressionStateUncertain(
            "Orion state advanced but ACE could not seal the external progression receipt",
            code="runtime_failure",
        ) from exc
    result = dict(receipt)
    result["receipt_path"] = str(path)
    return result


def _authorized_commit_context(
    run_id: str,
    authorization_token: str,
    authority_ref: str,
    acknowledge_side_effects: bool,
    principal_id: str,
    root: Path,
    run_root: Optional[Path],
) -> Tuple[Any, Dict[str, Any], Any, Path, Dict[str, Any], Path]:
    if acknowledge_side_effects is not True:
        raise ACEError(
            "Orion progression requires explicit side-effect acknowledgement",
            code="materialization_authority_missing",
        )
    state = _helper_modules(root)[1]
    preview, runtime, persisted_path, owner, resolved_run_root = _prepare(
        run_id,
        authority_ref,
        principal_id,
        root,
        run_root,
    )
    if authorization_token != preview["authorization_token"]:
        raise ACEError(
            "Orion progression authorization token is stale or invalid",
            code="transaction_conflict",
        )
    return state, preview, runtime, persisted_path, owner, resolved_run_root


def _execute_authorized_tick(
    run_id: str,
    authorization_token: str,
    state: Any,
    preview: Mapping[str, Any],
    runtime: Any,
    persisted_path: Path,
    owner: Mapping[str, Any],
    resolved_run_root: Path,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    before = preview["authorization"]["run"]
    policy = owner["policy"]
    event = _advance_owner(
        runtime,
        persisted_path,
        before,
        int(policy["elapsed_minutes"]),
        state,
    )
    after = _validated_after_state(
        owner,
        persisted_path,
        run_id,
        resolved_run_root,
        state,
    )
    failure = state.verify_single_advance(
        before,
        after,
        ticks=int(policy["ticks_per_authorization"]),
        elapsed_minutes=int(policy["elapsed_minutes"]),
    )
    if failure is not None:
        raise OrionProgressionStateUncertain(failure, code="runtime_failure")
    receipt = _progression_receipt(
        run_id,
        authorization_token,
        before,
        after,
        event,
        preview,
        policy,
    )
    return receipt, after


def commit_orion_advance(
    run_id: str,
    authorization_token: str,
    authority_ref: str,
    acknowledge_side_effects: bool,
    principal_id: str = "ORION.ROLE.PILOT",
    *,
    root: Path = ROOT,
    run_root: Optional[Path] = None,
    receipt_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Consume one fresh state-bound authorization and delegate one native tick."""
    context = _authorized_commit_context(
        run_id,
        authorization_token,
        authority_ref,
        acknowledge_side_effects,
        principal_id,
        root,
        run_root,
    )
    state, preview, runtime, persisted_path, owner, resolved_run_root = context
    receipt, after = _execute_authorized_tick(
        run_id,
        authorization_token,
        state,
        preview,
        runtime,
        persisted_path,
        owner,
        resolved_run_root,
    )
    return _seal_receipt(
        receipt,
        run_id,
        int(after["tick"]),
        receipt_root,
        root,
        state,
    )


def inspect_orion_progression(
    run_id: str,
    tick: int,
    *,
    root: Path = ROOT,
    receipt_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Read one external progression receipt without touching L1 state."""
    state = _helper_modules(root)[1]
    normalized_run_id = state.canonical_run_id(run_id)
    if isinstance(tick, bool) or not isinstance(tick, int) or tick < 1:
        raise ACEError(
            "tick must be a positive integer",
            code="input_validation_failed",
        )
    external_root = state.resolve_receipt_root(receipt_root, root)
    path = state.receipt_path(external_root, normalized_run_id, tick)
    return state.read_receipt(path)


def registered_owner_preflight(*, root: Path = ROOT) -> Dict[str, Any]:
    """Validate the exact owner and call preflight only; never load/advance a run."""
    owner = _load_owner_runtime(root)
    runtime = owner["runtime_class"]()
    report = runtime.preflight()
    if not isinstance(report, Mapping):
        raise ACEError(
            "registered Orion owner returned an invalid preflight report",
            code="output_validation_failed",
        )
    return {
        "owner_repository": owner["policy"]["cloudbank_repository"],
        "owner_repository_sha": owner["cloudbank_sha"],
        "owner_source": owner["policy"]["owner"]["path"],
        "owner_source_git_blob": owner["owner_blob_sha"],
        "preflight": dict(report),
        "run_loaded": False,
        "run_advanced": False,
    }

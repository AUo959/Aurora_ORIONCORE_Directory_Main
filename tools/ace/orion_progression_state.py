"""State fingerprints and external receipts for governed Orion L1 progression."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

from .core import ACEError, ROOT, semantic_sha256

ORION_PROGRESSION_RECEIPT_ENV = "ACE_ORION_RECEIPT_ROOT"
ORION_RUN_ROOT_ENV = "AURORA_L1_RUN_ROOT"
DEFAULT_RECEIPT_ROOT = Path.home() / ".aurora" / "ace" / "orion-progression"
DEFAULT_RUN_ROOT = Path.home() / ".aurora" / "l1-runs"
_MAX_STATE_BYTES = 64 * 1024 * 1024


def canonical_run_id(run_id: str) -> str:
    """Require canonical UUID spelling for an existing persisted run."""
    try:
        normalized = str(uuid.UUID(run_id))
    except (AttributeError, TypeError, ValueError) as exc:
        raise ACEError(
            "run_id must be a canonical UUID",
            code="input_validation_failed",
        ) from exc
    if normalized != run_id:
        raise ACEError(
            "run_id must be a canonical UUID",
            code="input_validation_failed",
        )
    return normalized


def resolve_run_root(value: Optional[Path]) -> Path:
    """Resolve the operator's external L1 run root."""
    if value is not None:
        return value.expanduser().resolve()
    configured = os.environ.get(ORION_RUN_ROOT_ENV, "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return DEFAULT_RUN_ROOT.expanduser().resolve()


def resolve_receipt_root(value: Optional[Path], root: Path = ROOT) -> Path:
    """Resolve an external ACE receipt root and reject repository-local storage."""
    if value is None:
        configured = os.environ.get(ORION_PROGRESSION_RECEIPT_ENV, "").strip()
        value = Path(configured) if configured else DEFAULT_RECEIPT_ROOT
    resolved = value.expanduser().resolve()
    control = root.resolve()
    if resolved == control or control in resolved.parents:
        raise ACEError(
            "Orion progression receipts must remain outside OrionCore",
            code="input_validation_failed",
        )
    return resolved


def state_path(run_root: Path, run_id: str) -> Path:
    """Return one existing run state path without allowing path escape/symlinks."""
    root = run_root.expanduser().resolve()
    path = (root / run_id / "state.json").resolve()
    if root not in path.parents or path.is_symlink():
        raise ACEError(
            "Orion run state path is unsafe",
            code="target_unavailable",
        )
    if not path.is_file():
        raise ACEError(
            "existing Orion run state is unavailable",
            code="target_unavailable",
        )
    return path


def _read_state_bytes(path: Path) -> bytes:
    try:
        size = path.stat().st_size
        raw = path.read_bytes()
    except OSError as exc:
        raise ACEError(
            "Orion run state cannot be read",
            code="target_unavailable",
        ) from exc
    if size <= 0 or size > _MAX_STATE_BYTES or len(raw) != size:
        raise ACEError(
            "Orion run state size is outside the governed limit",
            code="input_validation_failed",
        )
    return raw


def _decode_state(raw: bytes) -> Dict[str, Any]:
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ACEError(
            "Orion run state cannot be decoded",
            code="target_unavailable",
        ) from exc
    if not isinstance(payload, dict):
        raise ACEError(
            "Orion run state must be a JSON object",
            code="input_validation_failed",
        )
    return payload


def read_state(path: Path) -> Tuple[bytes, Dict[str, Any]]:
    """Read one bounded JSON state file and return exact bytes plus object data."""
    raw = _read_state_bytes(path)
    return raw, _decode_state(raw)


def sha256_bytes(raw: bytes) -> str:
    """Return the byte-level persisted-state fingerprint."""
    return hashlib.sha256(raw).hexdigest()


def _manifest(exported: Mapping[str, Any]) -> Mapping[str, Any]:
    manifest = exported.get("manifest")
    if not isinstance(manifest, Mapping):
        raise ACEError(
            "Orion runtime export lacks a manifest",
            code="output_validation_failed",
        )
    return manifest


def _required_counters(
    manifest: Mapping[str, Any],
) -> Tuple[int, int, int, int]:
    values = (
        manifest.get("seed"),
        manifest.get("tick"),
        manifest.get("station_cycle_minute"),
        manifest.get("station_cycle_length_minutes"),
    )
    invalid = any(
        isinstance(value, bool) or not isinstance(value, int) for value in values
    )
    if invalid:
        raise ACEError(
            "Orion runtime manifest counters are invalid",
            code="output_validation_failed",
        )
    seed, tick, station_minute, cycle_length = values
    return int(seed), int(tick), int(station_minute), int(cycle_length)


def _event_ledger(exported: Mapping[str, Any]) -> list[Any]:
    events = exported.get("events")
    if not isinstance(events, list):
        raise ACEError(
            "Orion runtime export lacks an event ledger",
            code="output_validation_failed",
        )
    return events


def _replay_position(events: list[Any]) -> int:
    return sum(
        1
        for event in events
        if isinstance(event, Mapping)
        and event.get("cause") == "autonomous_world_process"
    )


def _rng_fingerprint(seed: int, replay_position: int) -> str:
    return semantic_sha256(
        {
            "policy": "ace.policy.orion.replay-position.v1",
            "seed": seed,
            "position": replay_position,
        }
    )


def snapshot(exported: Mapping[str, Any], state_sha256: str) -> Dict[str, Any]:
    """Build the state/replay fingerprint bound into an authorization token."""
    manifest = _manifest(exported)
    seed, tick, station_minute, cycle_length = _required_counters(manifest)
    replay_position = _replay_position(_event_ledger(exported))
    if replay_position != tick:
        raise ACEError(
            "Orion replay position does not match tick",
            code="output_validation_failed",
        )
    return {
        "run_id": manifest.get("run_id"),
        "tick": tick,
        "station_cycle_minute": station_minute,
        "station_cycle_length_minutes": cycle_length,
        "status": manifest.get("status"),
        "seed": seed,
        "run_cloudbank_revision": manifest.get("cloudbank_revision"),
        "run_canonrec_revision": manifest.get("canonrec_revision"),
        "state_file_sha256": state_sha256,
        "state_semantic_sha256": semantic_sha256(exported),
        "replay_position": replay_position,
        "rng_fingerprint": _rng_fingerprint(seed, replay_position),
    }


def verify_single_advance(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    *,
    ticks: int,
    elapsed_minutes: int,
) -> Optional[str]:
    """Return an invariant error message, or None when one tick is proven."""
    checks = [
        (
            after["run_id"] == before["run_id"],
            "Orion run identity changed during advancement",
        ),
        (
            after["tick"] == before["tick"] + ticks,
            "Orion advancement did not produce exactly one tick",
        ),
        (
            after["replay_position"] == before["replay_position"] + ticks,
            "Orion replay position advanced unexpectedly",
        ),
        (
            after["state_file_sha256"] != before["state_file_sha256"],
            "Orion advance returned without a persisted state change",
        ),
    ]
    expected_minute = (
        int(before["station_cycle_minute"]) + elapsed_minutes
    ) % int(before["station_cycle_length_minutes"])
    checks.append(
        (
            after["station_cycle_minute"] == expected_minute,
            "Orion station-cycle minute advanced unexpectedly",
        )
    )
    failures = [message for passed, message in checks if not passed]
    return failures[0] if failures else None


def receipt_path(receipt_root: Path, run_id: str, tick: int) -> Path:
    """Return the immutable external receipt path for one resulting tick."""
    root = receipt_root.resolve()
    run_dir = (root / run_id).resolve()
    if root not in run_dir.parents:
        raise ACEError(
            "Orion progression receipt path escaped its root",
            code="input_validation_failed",
        )
    return run_dir / f"tick-{tick:08d}.json"


def _receipt_text(payload: Mapping[str, Any]) -> str:
    return json.dumps(
        dict(payload),
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    ) + "\n"


def _write_temporary_receipt(path: Path, data: str) -> Path:
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix=".receipt-",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    ) as handle:
        temporary_path = Path(handle.name)
        os.chmod(temporary_path, 0o600)
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    return temporary_path


def _replace_receipt(temporary_path: Path, path: Path) -> None:
    try:
        os.replace(temporary_path, path)
        os.chmod(path, 0o600)
    except Exception:
        if temporary_path.exists():
            temporary_path.unlink()
        raise


def write_receipt(path: Path, payload: Mapping[str, Any]) -> None:
    """Atomically seal one external receipt without overwrite."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.exists():
        raise ACEError(
            "Orion progression receipt already exists; replay is refused",
            code="transaction_conflict",
        )
    temporary_path = _write_temporary_receipt(path, _receipt_text(payload))
    _replace_receipt(temporary_path, path)


def read_receipt(path: Path) -> Dict[str, Any]:
    """Read and minimally validate one external progression receipt."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ACEError(
            "Orion progression receipt is unavailable",
            code="target_unavailable",
        ) from exc
    valid = (
        isinstance(payload, dict)
        and payload.get("record_type") == "ace_orion_progression_receipt"
    )
    if not valid:
        raise ACEError(
            "Orion progression receipt is invalid",
            code="output_validation_failed",
        )
    return payload

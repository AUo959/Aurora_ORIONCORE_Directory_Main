"""Append-only determination ledger for the Aurora Canon Engine.

The ledger stores immutable determination receipts as individual JSON objects.
Queryability is derived from receipt content rather than from a mutable index,
which keeps the first implementation deliberately small and append-only while
still supporting the lookup dimensions required by ACE spec section 6.13.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping

from .core import ACEError, ROOT, load_json, semantic_sha256, validate_json_schema

LEDGER_VERSION = "0.1.0"
DEFAULT_LEDGER_REL = Path("reports/ace/determinations")


def _receipt_filename(determination_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", determination_id).strip("._")
    if not safe:
        raise ACEError("determination_id cannot be converted to a ledger filename", code="input_validation_failed")
    return safe + ".json"


def _validate_receipt(receipt: Mapping[str, Any], *, root: Path) -> None:
    if receipt.get("record_type") != "ace_determination_receipt":
        raise ACEError("ledger accepts ACE determination receipts only", code="input_validation_failed")
    determination_id = receipt.get("determination_id")
    if not isinstance(determination_id, str) or not determination_id:
        raise ACEError("determination receipt requires determination_id", code="input_validation_failed")

    schema = root / "catalog/schemas/aurora_ace_determination_receipt.schema.json"
    if schema.is_file():
        with tempfile.TemporaryDirectory(prefix="ace-ledger-schema-") as temp:
            candidate = Path(temp) / "receipt.json"
            candidate.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            report = validate_json_schema(candidate, schema, root)
        if not report["ok"]:
            raise ACEError(
                "determination receipt cannot enter ledger because schema validation failed: "
                + json.dumps(report["errors"][:3]),
                code="output_validation_failed",
            )


def append_determination(
    receipt: Mapping[str, Any],
    ledger_dir: Path | None = None,
    *,
    root: Path = ROOT,
) -> Path:
    """Append one immutable receipt to the ledger.

    Re-appending the exact same receipt is idempotent. Reusing a determination
    ID for different content is rejected so a later determination must receive
    its own ID and use ``answer.supersedes_determination_refs`` for lineage.
    """

    _validate_receipt(receipt, root=root)
    ledger = (ledger_dir or (root / DEFAULT_LEDGER_REL)).expanduser().resolve()
    ledger.mkdir(parents=True, exist_ok=True)
    target = ledger / _receipt_filename(str(receipt["determination_id"]))
    serialized = json.dumps(receipt, indent=2, sort_keys=True) + "\n"

    if target.exists():
        existing = load_json(target)
        if semantic_sha256(existing) == semantic_sha256(receipt):
            return target
        raise ACEError(
            f"append-only ledger collision for {receipt['determination_id']}",
            code="transaction_conflict",
        )

    fd, temp_name = tempfile.mkstemp(prefix=".ace-ledger-", suffix=".json", dir=ledger)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(serialized)
        os.replace(temp_name, target)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise
    return target


def _contains(items: Iterable[Any], value: str) -> bool:
    return any(str(item) == value for item in items)


def query_ledger(
    ledger_dir: Path | None = None,
    *,
    root: Path = ROOT,
    subject: str | None = None,
    query: str | None = None,
    capability: str | None = None,
    tool_run: str | None = None,
    canonical_target: str | None = None,
    commit: str | None = None,
) -> list[dict[str, Any]]:
    """Query immutable receipts by every dimension required by ACE section 6.13."""

    ledger = (ledger_dir or (root / DEFAULT_LEDGER_REL)).expanduser().resolve()
    if not ledger.exists():
        return []

    matches: list[dict[str, Any]] = []
    for path in sorted(ledger.glob("*.json")):
        try:
            receipt = load_json(path)
        except Exception:
            continue
        if not isinstance(receipt, dict) or receipt.get("record_type") != "ace_determination_receipt":
            continue
        if subject is not None and not _contains(receipt.get("subject_refs", []), subject):
            continue
        if query is not None and receipt.get("query_id") != query:
            continue
        if capability is not None:
            steps = receipt.get("plan", {}).get("steps", [])
            if not any(step.get("capability_id") == capability for step in steps if isinstance(step, dict)):
                continue
        if tool_run is not None:
            steps = receipt.get("plan", {}).get("steps", [])
            if not any(step.get("tool_run_id") == tool_run for step in steps if isinstance(step, dict)):
                continue
        if canonical_target is not None:
            targets = receipt.get("materialization", {}).get("target_paths", [])
            field_targets = [
                field.get("canon_target_ref")
                for field in receipt.get("answer", {}).get("fields", [])
                if isinstance(field, dict)
            ]
            if canonical_target not in targets and canonical_target not in field_targets:
                continue
        if commit is not None and receipt.get("materialization", {}).get("commit_sha") != commit:
            continue
        matches.append(receipt)
    return matches

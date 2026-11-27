"""Append-only local journal and reconstruction for Canon Operations staging."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from collections.abc import Callable, Iterable, Iterator
from contextlib import closing, contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory


class JournalError(ValueError):
    """A journal operation would violate history or request identity."""


def canonical_json(value: object) -> str:
    """Encode the stable JSON used for receipt and history digests."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


def digest(value: object) -> str:
    """Return the lowercase SHA-256 digest of canonical UTF-8 JSON."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def request_digest(request: dict) -> str:
    """Hash a CanonRec request with its self-referential digest omitted."""
    return digest({key: value for key, value in request.items() if key != "content_hash"})


def encode_entry(sequence: int, previous: str | None, request: dict, receipt: dict) -> dict:
    """Bind a request and its disposition to one position in the journal."""
    entry = {
        "sequence": sequence,
        "previous_sha256": previous,
        "request": request,
        "receipt": receipt,
    }
    return {**entry, "sha256": digest(entry)}


def _record_key(record: dict) -> tuple[str, str, str]:
    return record["layer"], record["kind"], record["record_id"]


def staging_state(entries: Iterable[dict]) -> dict[tuple[str, str, str], dict]:
    """Rebuild the latest staging revision per target from accepted receipts."""
    state = {}
    for entry in entries:
        for target in entry["receipt"]["target_updates"]:
            state[_record_key(target)] = target["state"]
    return state


def entries_for_target(entries: Iterable[dict], target: dict) -> list[dict]:
    """Select the ordered history for an exact layer, kind, and record ID."""
    identity = _record_key(target)
    return [
        entry for entry in entries
        if any(_record_key(item) == identity for item in entry["request"]["targets"])
    ]


def _connection(path: Path, *, writable: bool) -> sqlite3.Connection:
    if writable:
        path.touch(mode=0o600, exist_ok=True)
        return sqlite3.connect(path)
    return sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)


def _create_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        "CREATE TABLE IF NOT EXISTS intake ("
        "sequence INTEGER PRIMARY KEY, request_id TEXT UNIQUE NOT NULL, packet TEXT NOT NULL)"
    )


@contextmanager
def _write_transaction(path: Path) -> Iterator[sqlite3.Connection]:
    with closing(_connection(path, writable=True)) as connection:
        _create_table(connection)
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            yield connection


def _entry_rows(connection: sqlite3.Connection) -> list[dict]:
    return [
        json.loads(packet)
        for (packet,) in connection.execute("SELECT packet FROM intake ORDER BY sequence")
    ]


def _insert(connection: sqlite3.Connection, entry: dict) -> None:
    connection.execute(
        "INSERT INTO intake VALUES (?, ?, ?)",
        (entry["sequence"], entry["request"]["request_id"], canonical_json(entry)),
    )


def append_request(
    path: Path,
    snapshot: str,
    request: dict,
    evaluate: Callable[[dict[tuple[str, str, str], dict]], dict],
    *,
    project_events: Callable[[list[dict]], list[dict]] | None = None,
) -> dict:
    """Serialize disposition and optimistic state checks in a single write transaction."""
    with _write_transaction(path) as connection:
        history = _entry_rows(connection)
        if history and history[0]["receipt"]["canon_commit"] != snapshot:
            raise JournalError("Use a separate journal for a different CanonRec snapshot")
        previous = _verify_history(history, snapshot)
        existing = connection.execute(
            "SELECT packet FROM intake WHERE request_id = ?", (request["request_id"],)
        ).fetchone()
        if existing:
            receipt = json.loads(existing[0])["receipt"]
            if receipt["content_hash"] != request["content_hash"]:
                raise JournalError("/request_id: previously recorded with different content")
            return {"status": "DUPLICATE", "receipt": receipt}

        receipt = evaluate(staging_state(history))
        if receipt["status"] == "ACCEPTED" and project_events is not None:
            receipt["events"] = project_events(history)
        entry = encode_entry(len(history) + 1, previous, request, receipt)
        _insert(connection, entry)
        return {"status": receipt["status"], "receipt": receipt}


def read_entries(path: Path) -> list[dict]:
    """Read the request and receipt artifacts in journal order."""
    with closing(_connection(path, writable=False)) as connection:
        history = _entry_rows(connection)
    if history:
        _verify_history(history, history[0]["receipt"]["canon_commit"])
    return history


def read_request(path: Path, request_id: str) -> dict | None:
    """Fetch the request and receipt associated with an exact request ID."""
    with closing(_connection(path, writable=False)) as connection:
        match = connection.execute(
            "SELECT sequence, packet FROM intake WHERE request_id = ?", (request_id,)
        ).fetchone()
    if not match:
        return None
    sequence, packet = match
    entry = json.loads(packet)
    _validate_packet(entry, sequence, entry["previous_sha256"])
    if entry["request"]["request_id"] != request_id:
        raise JournalError("Stored request ID differs from the journal index")
    return entry


def _validate_packet(entry: dict, index: int, previous: str | None) -> str:
    request, receipt = entry["request"], entry["receipt"]
    expected = encode_entry(index, previous, request, receipt)
    if entry != expected:
        raise JournalError(f"Journal entry {index} fails its history digest")
    if request_digest(request) != request["content_hash"]:
        raise JournalError(f"Journal entry {index} fails its request digest")
    if (receipt["request_id"], receipt["content_hash"]) != (
        request["request_id"], request["content_hash"],
    ):
        raise JournalError(f"Journal entry {index} has a mismatched receipt")
    return expected["sha256"]


def _verify_history(entries: list[dict], snapshot: str) -> str | None:
    previous = None
    for index, entry in enumerate(entries, 1):
        previous = _validate_packet(entry, index, previous)
        if entry["receipt"]["canon_commit"] != snapshot:
            raise JournalError(f"Journal entry {index} uses a different snapshot")
    return previous


def rebuild(path: Path, entries: list[dict], *, expected_tip: str) -> None:
    """Restore verified artifacts to a new journal using a trusted terminal digest."""
    if path.exists() or not entries:
        raise JournalError("Rebuild requires an absent destination and a nonempty export")
    if _verify_history(entries, entries[0]["receipt"]["canon_commit"]) != expected_tip:
        raise JournalError("Export fails the expected terminal digest")

    with TemporaryDirectory(dir=path.parent, prefix=".restore-") as directory:
        temporary = Path(directory) / "intake.sqlite3"
        with _write_transaction(temporary) as connection:
            for entry in entries:
                _insert(connection, entry)
        os.link(temporary, path)

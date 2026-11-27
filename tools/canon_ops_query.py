"""Read Canon Operations v1 queries from pinned, local CanonRec Git objects."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, cast

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

if __package__:
    from ._workspace_common import git
else:
    from _workspace_common import git


CONTRACT_COMMIT = "778ba3b3aced338f30bc4b35accecf14ecf419a3"
CONTRACT_PATH = "contracts/canon-ops/v1"
SOURCE_REPOSITORY = "AUo959/CanonRec"
READABLE_SUFFIXES = {".json", ".jsonl", ".ndjson"}
COLLECTIONS = (
    "canonical_facts",
    "operational_atoms",
    "staging_material",
    "assumptions",
    "unknowns",
)


class QueryError(ValueError):
    """A query or local source cannot satisfy the contract."""


class CanonRec:
    def __init__(self, path: Path):
        """Attach to the specified local CanonRec repository."""
        self.path = path

    def git(self, *arguments: str) -> bytes:
        message = f"CanonRec Git data unavailable for {arguments[0]}"
        try:
            response = git(
                ["--literal-pathspecs", *arguments], self.path,
                check=False, text=False, local_objects_only=True,
            )
        except OSError as exc:
            raise QueryError(message) from exc
        if response.returncode:
            raise QueryError(message)
        return cast(bytes, response.stdout)

    def blob(self, reference: str) -> bytes:
        return self.git("cat-file", "blob", reference)

    def records(self, commit: str, source_paths: list[str]) -> Iterator[tuple[str, str, dict]]:
        if self.git("cat-file", "-t", commit).strip() != b"commit":
            raise QueryError("/commit: expected a CanonRec commit")
        tree = self.git("ls-tree", "-rz", "--full-tree", commit, "--", *source_paths)
        for entry in tree.split(b"\0"):
            if not entry:
                continue
            metadata, raw_path = entry.split(b"\t", 1)
            mode, kind, object_id = metadata.decode("ascii").split()
            path = raw_path.decode("utf-8")
            if kind != "blob" or mode == "120000" or Path(path).suffix not in READABLE_SUFFIXES:
                continue
            data = self.blob(object_id)
            digest = hashlib.sha256(data).hexdigest()
            for record in _read_records(path, data):
                yield path, digest, record


def _validator_pair(repo: CanonRec, contract_commit: str) -> tuple[Draft202012Validator, ...]:
    schemas = [
        json.loads(repo.blob(f"{contract_commit}:{CONTRACT_PATH}/{name}.schema.json"))
        for name in ("common", "canon-query", "canon-query-result")
    ]
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )
    return tuple(
        Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
        for schema in schemas[1:]
    )


def _read_records(path: str, data: bytes) -> Iterator[dict]:
    try:
        if Path(path).suffix == ".json":
            root = json.loads(data)
            records = root if isinstance(root, list) else [root]
        else:
            records = [json.loads(line) for line in data.splitlines() if line.strip()]
    except ValueError as exc:
        raise QueryError(f"{path}: expected UTF-8 JSON records") from exc
    yield from (record for record in records if isinstance(record, dict))


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _timestamp(value: str) -> datetime:
    instant = datetime.fromisoformat(value.upper().replace("Z", "+00:00"))
    if instant.tzinfo is None:
        return instant.replace(tzinfo=timezone.utc)
    return instant


def _record_time(record: dict) -> datetime | None:
    value = record.get("occurred_at") or record.get("timestamp") or record.get("updated_at")
    if not isinstance(value, str):
        return None
    try:
        return _timestamp(value)
    except ValueError:
        return None


def _matches_time(record: dict, filters: dict) -> bool:
    if not {"since", "until"}.intersection(filters):
        return True
    value = _record_time(record)
    if value is None:
        return False
    return (
        ("since" not in filters or _timestamp(filters["since"]) <= value)
        and ("until" not in filters or value <= _timestamp(filters["until"]))
    )


def _relationship_matches(record: dict, relationship: dict) -> bool:
    kind = relationship["kind"]
    relationships = record.get("relationships")
    if isinstance(relationships, list) and relationship in relationships:
        return True
    return kind.endswith(("_id", "_ids")) and relationship["target_id"] in _strings(record.get(kind))


def _matches_aliases(record: dict, identities: list[str], expected: list[str] | None) -> bool:
    if expected is None:
        return True
    aliases = identities[1:] + _strings(record.get("aliases")) + _strings(record.get("name"))
    aliases.extend(_strings(record.get("canonical_name")))
    return bool({alias.casefold() for alias in aliases} & {alias.casefold() for alias in expected})


def _matches(record: dict, identities: list[str], kind: str, certainty: str, filters: dict) -> bool:
    for key, value in (
        ("entity_kinds", kind),
        ("entity_ids", identities[0]),
        ("certainty_states", certainty),
    ):
        if key in filters and value not in filters[key]:
            return False
    if not _matches_aliases(record, identities, filters.get("aliases")):
        return False
    return all(
        _relationship_matches(record, related) for related in filters.get("relationships", [])
    ) and _matches_time(record, filters)


def _collection(chronicle: bool, native_certainty: str) -> str:
    if chronicle:
        return "operational_atoms"
    if native_certainty == "CANON":
        return "canonical_facts"
    if native_certainty in {"APPROX", "LEGEND_CONTESTED"}:
        return "assumptions"
    return "staging_material" if native_certainty else "unknowns"


def _identities(record: dict) -> list[str]:
    return [
        identity
        for field in ("canonical_id", "entity_id", "vessel_id", "record_id", "event_id", "id")
        for identity in _strings(record.get(field))
        if identity
    ]


def _record_kind(path: str, record: dict) -> tuple[str | None, bool]:
    if path.startswith("canon/L1/station/chronicle/") and record.get("event_id"):
        return "chronicle_atom", True
    kind = record.get("entity_kind") or record.get("kind")
    return (kind if isinstance(kind, str) and kind else None), False


def _entry(path: str, digest: str, record: dict, request: dict) -> tuple[dict, dict] | None:
    identities = _identities(record)
    if not identities:
        return None
    layer = request["layer"]
    if record.get("layer", layer) not in (None, layer):
        raise QueryError(f"{path}: source record declares another layer")
    kind, is_chronicle = _record_kind(path, record)
    if kind is None:
        return None
    native_certainty = record.get("certainty") or ""
    certainty = native_certainty or "UNCONFIRMED"
    if not _matches(record, identities, kind, certainty, request.get("filters", {})):
        return None
    cursor = {
        "collection": _collection(is_chronicle, native_certainty),
        "kind": kind,
        "record_id": identities[0],
        "source_path": path,
    }
    result = {
        "kind": kind,
        "record_id": identities[0],
        "certainty": certainty,
        "source": {
            "repository": SOURCE_REPOSITORY,
            "commit": request["commit"],
            "path": path,
            "layer": layer,
            "sha256": digest,
        },
        "data": record,
    }
    return cursor, result


def _cursor_key(cursor: dict) -> tuple[int, str, str, str]:
    return (
        COLLECTIONS.index(cursor["collection"]),
        cursor["kind"],
        cursor["record_id"],
        cursor["source_path"],
    )


def _validate(validator: Draft202012Validator, document: dict) -> None:
    error = next(validator.iter_errors(document), None)
    if error:
        pointer = "/" + "/".join(str(part) for part in error.absolute_path)
        raise QueryError(f"{pointer}: {error.message}")


def _validate_scope(request: dict) -> None:
    expected_root = f"canon/{request['layer']}"
    for index, path in enumerate(request["source_paths"]):
        if path != expected_root and not path.startswith(expected_root + "/"):
            raise QueryError(f"/source_paths/{index}: expected a path in {expected_root}")
    filters = request.get("filters", {})
    if {"since", "until"} <= filters.keys():
        if _timestamp(filters["since"]) > _timestamp(filters["until"]):
            raise QueryError("/filters/until: precedes the lower time bound")


def _ordered_entries(repo: CanonRec, request: dict) -> list[tuple[dict, dict]]:
    entries = (
        _entry(path, digest, record, request)
        for path, digest, record in repo.records(request["commit"], request["source_paths"])
    )
    pairs = sorted((entry for entry in entries if entry is not None), key=lambda entry: _cursor_key(entry[0]))
    keys = [_cursor_key(cursor) for cursor, _ in pairs]
    if len(keys) != len(set(keys)):
        raise QueryError("CanonRec returned repeated result identities in the same source")
    return pairs


def _result_page(pairs: list[tuple[dict, dict]], request: dict) -> dict:
    page = request["page"]
    if "after" in page:
        after = _cursor_key(page["after"])
        pairs = [entry for entry in pairs if _cursor_key(entry[0]) > after]
    result = {key: request[key] for key in ("version", "query_id", "layer", "commit")}
    result["results"] = {collection: [] for collection in COLLECTIONS}
    for cursor, item in pairs[: page["limit"]]:
        result["results"][cursor["collection"]].append(item)
    result["next_after"] = pairs[page["limit"] - 1][0] if len(pairs) > page["limit"] else None
    return result


def query(repo: CanonRec, request: dict, *, contract_commit: str = CONTRACT_COMMIT) -> dict:
    query_validator, result_validator = _validator_pair(repo, contract_commit)
    _validate(query_validator, request)
    _validate_scope(request)
    result = _result_page(_ordered_entries(repo, request), request)
    _validate(result_validator, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonrec", required=True, type=Path)
    parser.add_argument("query", type=Path)
    args = parser.parse_args()
    try:
        request = json.loads(args.query.read_text(encoding="utf-8"))
        result = query(CanonRec(args.canonrec), request)
        output = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

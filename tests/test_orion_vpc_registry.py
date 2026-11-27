from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "catalog" / "schemas" / "orion_vpc.schema.json"
REGISTRY_PATH = REPO_ROOT / "catalog" / "orion_vpc_registry.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator() -> Draft202012Validator:
    schema = _load(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _registry() -> dict[str, object]:
    return _load(REGISTRY_PATH)


def _record(registry: dict[str, object], record_id: str) -> dict[str, object]:
    records = registry["records"]
    assert isinstance(records, list)
    for item in records:
        assert isinstance(item, dict)
        if item["id"] == record_id:
            return item
    raise AssertionError(f"missing VPC record: {record_id}")


def _immutable_evidence(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    patterns = (
        r"^[0-9a-f]{40}$",
        r"^[0-9a-f]{64}$",
        r"^release:[A-Za-z0-9_.+/-]+$",
        r"^registry:[A-Za-z0-9_.:/-]+$",
        r"^https://github\.com/[^/]+/[^/]+/commit/[0-9a-f]{40}$",
    )
    return any(re.fullmatch(pattern, value) for pattern in patterns)


def test_registry_schema_and_seed_records_validate() -> None:
    registry = _registry()
    _validator().validate(registry)
    records = registry["records"]
    assert isinstance(records, list)
    assert len(records) == 5


def test_vpc_ids_are_unique() -> None:
    records = _registry()["records"]
    assert isinstance(records, list)
    ids = [item["id"] for item in records]
    assert len(ids) == len(set(ids))


def test_process_status_is_distinct_from_authority_class() -> None:
    registry = _registry()
    record = _record(registry, "ORION.VPC.GOVERNANCE.0002")
    assert record["status"] == "ACCEPTED"
    assert record["authority_class"] == "IMPLEMENTED"

    invalid = copy.deepcopy(registry)
    invalid_record = _record(invalid, "ORION.VPC.GOVERNANCE.0002")
    invalid_record["status"] = "IMPLEMENTED"
    with pytest.raises(ValidationError):
        _validator().validate(invalid)


def test_promoted_records_require_target_owner_and_immutable_evidence() -> None:
    registry = _registry()
    promoted = copy.deepcopy(_record(registry, "ORION.VPC.GOVERNANCE.0001"))
    promoted["status"] = "PROMOTED"
    promoted["promotion_target"] = "docs/example.md"
    promoted["owner"] = "Aurora root control plane"
    promoted["promotion_evidence"] = None

    invalid_registry = copy.deepcopy(registry)
    invalid_registry["records"] = [promoted]
    with pytest.raises(ValidationError):
        _validator().validate(invalid_registry)

    promoted["promotion_evidence"] = "a" * 40
    valid_registry = copy.deepcopy(registry)
    valid_registry["records"] = [promoted]
    _validator().validate(valid_registry)
    assert _immutable_evidence(promoted["promotion_evidence"])


def test_no_promoted_seed_record_has_weak_promotion_evidence() -> None:
    records = _registry()["records"]
    assert isinstance(records, list)
    for item in records:
        if item["status"] == "PROMOTED":
            assert item["promotion_target"]
            assert item["owner"]
            assert _immutable_evidence(item["promotion_evidence"])

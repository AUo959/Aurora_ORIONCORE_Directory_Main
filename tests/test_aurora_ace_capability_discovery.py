from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from ace import core  # noqa: E402
from ace import capability_discovery as discovery  # noqa: E402
from ace import invocation  # noqa: E402


def _records() -> list[dict[str, object]]:
    return discovery.load_capability_manifests(REPO_ROOT)


def test_committed_manifest_catalog_is_valid_unique_and_deterministic() -> None:
    first = _records()
    second = _records()
    first_ids = [str(item["manifest"]["capability_id"]) for item in first]
    second_ids = [str(item["manifest"]["capability_id"]) for item in second]

    assert first_ids == sorted(first_ids)
    assert first_ids == second_ids
    assert len(first_ids) == len(set(first_ids)) == 17
    assert {
        "ace.capability.invoke.character.retrieve",
        "ace.capability.invoke.character.complete",
        "ace.capability.invoke.facility",
        "ace.capability.invoke.canon_fact",
    } <= set(first_ids)


def test_committed_manifests_conform_to_draft_2020_12_schema() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (
            REPO_ROOT
            / "catalog/schemas/aurora_ace_capability_manifest.schema.json"
        ).read_text(encoding="utf-8")
    )
    validator = jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    )
    for record in _records():
        errors = sorted(
            validator.iter_errors(record["manifest"]),
            key=lambda error: list(error.path),
        )
        assert not errors, [
            {
                "path": list(error.path),
                "message": error.message,
            }
            for error in errors
        ]


def test_character_materializer_manifest_reflects_v05_authority() -> None:
    manifests = {
        str(item["manifest"]["capability_id"]): item["manifest"]
        for item in _records()
    }
    materializer = manifests["ace.capability.canonrec.materialize.entity"]

    assert materializer["lifecycle"]["status"] == "active"
    assert materializer["tool"]["path"] == "tools/ace/character_materialize.py"
    assert materializer["tool"]["entrypoint"] == "materialize_character_packet"
    assert materializer["domain"]["entity_types"] == ["character"]
    assert materializer["execution"]["transaction_required"] is True
    assert materializer["execution"]["supported_modes"] == [
        "delegated_materialize",
        "owner_gated_materialize",
    ]


def test_manifest_digest_rejects_tampering() -> None:
    payload = copy.deepcopy(_records()[0]["manifest"])
    payload["name"] = f"{payload['name']} tampered"

    with pytest.raises(core.ACEError, match="digest mismatch"):
        discovery.validate_capability_manifest(payload, root=REPO_ROOT)


def test_duplicate_ids_fail_closed(tmp_path: Path) -> None:
    payload = _records()[0]["manifest"]
    catalog = tmp_path / "duplicate.jsonl"
    row = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    catalog.write_text(f"{row}\n{row}\n", encoding="utf-8")

    with pytest.raises(core.ACEError, match="duplicate ACE capability_id"):
        discovery.load_capability_manifests(
            REPO_ROOT,
            manifest_path=catalog,
        )


def test_record_order_does_not_change_discovery(tmp_path: Path) -> None:
    records = [item["manifest"] for item in _records()]
    catalog = tmp_path / "reversed.jsonl"
    catalog.write_text(
        "\n".join(
            json.dumps(item, sort_keys=True, separators=(",", ":"))
            for item in reversed(records)
        )
        + "\n",
        encoding="utf-8",
    )

    reordered = discovery.load_capability_manifests(
        REPO_ROOT,
        manifest_path=catalog,
    )
    assert [item["manifest"]["capability_id"] for item in reordered] == sorted(
        item["capability_id"] for item in records
    )


@pytest.mark.parametrize(
    ("entity_type", "query_kind", "expected"),
    [
        (
            "character",
            "retrieve",
            "ace.capability.invoke.character.retrieve",
        ),
        (
            "character",
            "complete",
            "ace.capability.invoke.character.complete",
        ),
        (
            "facility",
            "complete",
            "ace.capability.invoke.facility",
        ),
        (
            "canon_fact",
            "resolve",
            "ace.capability.invoke.canon_fact",
        ),
    ],
)
def test_manifest_router_selects_native_resolvers(
    entity_type: str,
    query_kind: str,
    expected: str,
) -> None:
    selected = discovery.select_invocation_capability(
        {
            "subject": {"entity_type": entity_type},
            "query_kind": query_kind,
        },
        root=REPO_ROOT,
    )
    assert selected["capability_id"] == expected


def test_unknown_subject_fails_closed() -> None:
    with pytest.raises(core.ACEError, match="no discovered ACE resolver capability"):
        discovery.select_invocation_capability(
            {
                "subject": {"entity_type": "vessel"},
                "query_kind": "complete",
            },
            root=REPO_ROOT,
        )


def test_manifest_metadata_cannot_create_runtime_binding(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    query = {
        "schema_version": core.SCHEMA_VERSION,
        "record_type": "ace_query_envelope",
        "generation_policy": {"prefer_existing_specialists": True},
    }
    envelope = invocation.build_invocation_envelope(query)
    monkeypatch.setattr(
        invocation,
        "select_invocation_capability",
        lambda _query, root=None: {
            "capability_id": "ace.capability.invoke.untrusted.dynamic",
            "entrypoint": "arbitrary.module:execute",
        },
    )

    with pytest.raises(core.ACEError, match="no allowlisted ACE runtime binding"):
        invocation.resolve_invocation(
            envelope,
            tmp_path / "packet",
        )

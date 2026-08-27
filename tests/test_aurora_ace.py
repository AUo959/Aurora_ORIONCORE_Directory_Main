from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from ace import core  # noqa: E402
from ace.engine import _safe_output_path, resolve_character_query  # noqa: E402


BASELINES = [
    {
        "repository": "root",
        "path": ".",
        "commit_sha": "a" * 40,
        "authority_role": "control_plane",
    },
    {
        "repository": "CanonRec",
        "path": core.CANONREC_REL.as_posix(),
        "commit_sha": "b" * 40,
        "authority_role": "canon",
    },
    {
        "repository": "aurora-cloudbank-symbolic-main",
        "path": core.CLOUDBANK_REL.as_posix(),
        "commit_sha": "c" * 40,
        "authority_role": "runtime",
    },
]


def character_context() -> dict[str, object]:
    return {
        "role": "logistics_officer",
        "faction_id": "org_galactic_union",
        "faction_name": "Galactic Union",
        "location_type": "judicator_class_vessel",
        "observed_behavior": [
            "coordinated emergency supply allocation",
            "deferred correctly to the ship chain of command",
        ],
        "contextual_refs": ["scenario.ace.test.001"],
    }


def test_compile_character_query_is_semantically_stable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(core, "repository_baselines", lambda _root: BASELINES)
    first = core.compile_character_query(
        "What is this character's name and background?",
        character_context(),
        seed=808,
    )
    second = core.compile_character_query(
        "What is this character's name and background?",
        character_context(),
        seed=808,
    )

    assert first["query_id"] == second["query_id"]
    assert first["scope"]["target_paths"] == second["scope"]["target_paths"]
    assert first["subject"]["existence_status"] == "confirmed_unrecorded"
    assert first["answer_contract"]["coverage_policy"] == "all_mandatory_semantics_satisfied"
    assert first["execution_policy"]["mode"] == "commit_ready"
    assert first["created_at"] != ""


def test_compile_rejects_incomplete_context(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(core, "repository_baselines", lambda _root: BASELINES)
    with pytest.raises(core.ACEError, match="location_type"):
        core.compile_character_query(
            "What is this character's name?",
            {"role": "officer", "faction_id": "org_galactic_union"},
        )


def test_name_projection_preserves_membership_and_collapses_occupancy() -> None:
    raw = [
        {
            "canonical_name": "Ari Vale",
            "entity_id": "char_1",
            "entity_type": "CHARACTER",
            "aliases": ["A. Vale"],
            "source_path": "canon/L2/entities/char_1.json",
        },
        {
            "canonical_name": "A. Vale",
            "entity_id": "legacy_char_1",
            "entity_type": "CHARACTER",
            "aliases": [],
            "source_path": "canon/L2/entities/legacy_char_1.json",
        },
        {
            "canonical_name": "Bex Orr",
            "entity_id": "char_2",
            "entity_type": "CHARACTER",
            "aliases": [],
            "source_path": "canon/L2/entities/char_2.json",
        },
    ]
    projection = core.build_name_reservation_projection(raw)

    assert projection["source_member_count"] == 3
    assert projection["projected_member_count"] == 2
    assert projection["collapsed_row_count"] == 1
    assert projection["unresolved_relation_count"] == 1
    assert sum(len(component["members"]) for component in projection["membership"]) == 3
    occupied = {
        core.normalize_name(name)
        for entry in projection["reservations"]
        for name in [entry["canonical_name"], *entry["aliases"]]
    }
    assert {"arivale", "avale", "bexorr"} <= occupied


def test_safe_output_rejects_nested_repository_targets(tmp_path: Path) -> None:
    root = tmp_path / "root"
    canonrec = root / core.CANONREC_REL
    canonrec.mkdir(parents=True)
    with pytest.raises(core.ACEError, match="nested repository"):
        _safe_output_path(canonrec / "canon/L2/entities/new", root)


def test_warm_index_uses_registered_heads() -> None:
    nested_repos = [REPO_ROOT / core.CANONREC_REL, REPO_ROOT / core.CLOUDBANK_REL]
    if not all((path / ".git").exists() for path in nested_repos):
        pytest.skip("requires the CI lane to provision registered CanonRec and CloudBank repositories")

    index = core.build_capability_index(REPO_ROOT)
    active = {item["capability_id"] for item in index["capabilities"] if item["lifecycle"] == "active"}
    assert index["manifest_catalog_ref"] == "catalog/ace/capability_manifests"
    assert "ace.capability.gumas.naming.resolve" in active
    assert "ace.capability.quantum_forge.charforge.generate_capsule" in active
    assert "ace.capability.invoke.character.complete" in active
    materializer = next(
        item
        for item in index["capabilities"]
        if item["capability_id"] == "ace.capability.canonrec.materialize.entity"
    )
    assert materializer["lifecycle"] == "active"
    assert materializer["path"] == "tools/ace/character_materialize.py"
    assert materializer["entity_types"] == ["character"]
    assert materializer["allowlisted"] is True


@pytest.mark.skipif(
    os.environ.get("AURORA_ACE_LIVE_TESTS") != "1",
    reason="set AURORA_ACE_LIVE_TESTS=1 to run the registered-repository vertical slice",
)
def test_live_character_resolution_is_semantically_replayable(tmp_path: Path) -> None:
    query = core.compile_character_query(
        "What is this character's name and background?",
        character_context(),
        seed=808,
    )
    first = resolve_character_query(query, tmp_path / "first")
    second = resolve_character_query(query, tmp_path / "second")

    assert first["status"] == "EXECUTION_BLOCKED"
    assert first["materialization"]["status"] == "commit_ready"
    assert first["answer_contract"]["overall_status"] == "complete"
    assert first["validation"]["overall_status"] == "pass"
    assert first["integrity"]["semantic_answer_sha256"] == second["integrity"]["semantic_answer_sha256"]
    first_forge = next(step for step in first["plan"]["steps"] if step["step_id"].endswith("charforge"))
    second_forge = next(step for step in second["plan"]["steps"] if step["step_id"].endswith("charforge"))
    assert first_forge["semantic_output_sha256"] == second_forge["semantic_output_sha256"]
    assert json.loads((tmp_path / "first/receipts/determination_schema_validation.json").read_text())["ok"]
    naming_validation_text = (tmp_path / "first/receipts/naming_validation.json").read_text()
    assert ".ace-character-" not in naming_validation_text
    artifact_index = json.loads((tmp_path / "first/artifact_index.json").read_text())
    assert "receipts/determination_schema_validation.json" in artifact_index
    for relative_path, expected_sha in artifact_index.items():
        assert core.file_sha256(tmp_path / "first" / relative_path) == expected_sha

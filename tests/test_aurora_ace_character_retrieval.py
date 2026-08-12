from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from ace import character_retrieval, core, invocation  # noqa: E402


BASELINES = [
    {"repository": "root", "path": ".", "commit_sha": "a" * 40, "authority_role": "control_plane"},
    {"repository": "CanonRec", "path": core.CANONREC_REL.as_posix(), "commit_sha": "b" * 40, "authority_role": "canon"},
    {"repository": "aurora-cloudbank-symbolic-main", "path": core.CLOUDBANK_REL.as_posix(), "commit_sha": "c" * 40, "authority_role": "runtime"},
]


def _write_character(
    root: Path,
    canonical_id: str,
    name: str,
    *,
    aliases: list[str] | None = None,
    role: str = "Survey Officer",
    faction_id: str = "galactic_union",
    location_type: str = "organization",
    location_ref: str = "org_survey_corps",
) -> None:
    capsule = root / core.CANONREC_REL / "canon/L2/entities" / canonical_id / "capsule"
    capsule.mkdir(parents=True, exist_ok=True)
    (capsule / "identity.json").write_text(
        json.dumps(
            {
                "canonical_id": canonical_id,
                "name": name,
                "aliases": aliases or [],
                "role": role,
                "faction_id": faction_id,
                "certainty": "CANON",
                "status": "active",
                "location_binding": {
                    "type": location_type,
                    "target_id": location_ref,
                    "basis": "test relation evidence",
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (capsule / "traits.json").write_text(
        json.dumps({"traits": ["methodical", "calm"]}, indent=2) + "\n",
        encoding="utf-8",
    )
    (capsule / "knowledge.jsonl").write_text(
        json.dumps({"text": f"{name} serves as {role}.", "tags": ["identity"]}) + "\n",
        encoding="utf-8",
    )


def _capability_index() -> dict[str, object]:
    return {
        "schema_version": core.SCHEMA_VERSION,
        "record_type": "ace_warm_capability_index",
        "engine_version": core.ENGINE_VERSION,
        "baselines": BASELINES,
        "capabilities": [
            {
                "capability_id": character_retrieval.RETRIEVAL_CAPABILITY,
                "repository": "root",
                "repository_sha": "a" * 40,
                "manifest_sha256": "1" * 64,
                "lifecycle": "active",
            },
            {
                "capability_id": character_retrieval.RELATION_CAPABILITY,
                "repository": "root",
                "repository_sha": "a" * 40,
                "manifest_sha256": "2" * 64,
                "lifecycle": "active",
            },
        ],
    }


def _patch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(core, "repository_baselines", lambda _root: BASELINES)
    monkeypatch.setattr(character_retrieval, "repository_baselines", lambda _root: BASELINES)
    monkeypatch.setattr(character_retrieval, "build_capability_index", lambda _root: _capability_index())


def test_name_lookup_returns_existing_character_without_generation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_character(tmp_path, "char_ada_north", "Ada North")
    _patch(monkeypatch)

    query = character_retrieval.compile_existing_character_query_if_applicable(
        "Who is Ada North?",
        {"name": "Ada North", "existence_status": "known"},
        seed=808,
        mode="commit_ready",
        requester_kind="user",
        requester_id="ORION.ROLE.PILOT",
        session_ref=None,
        root=tmp_path,
    )
    assert query is not None
    receipt = character_retrieval.resolve_existing_character_query(query, tmp_path / "packet", root=tmp_path)

    assert receipt["status"] == "RETRIEVED_CANON"
    identity = receipt["answer"]["fields"][0]["value"]
    assert identity["canonical_id"] == "char_ada_north"
    assert receipt["transactions"] == []
    summary = json.loads((tmp_path / "packet/receipts/execution_summary.json").read_text(encoding="utf-8"))
    assert summary["generator_invoked"] is False
    assert summary["canon_mutation"] is False


def test_alias_lookup_resolves_existing_character(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_character(tmp_path, "char_ada_north", "Ada North", aliases=["Northstar"])
    _patch(monkeypatch)
    query = character_retrieval.compile_existing_character_query_if_applicable(
        "Who is Northstar?",
        {"name": "Northstar", "existence_status": "unknown"},
        seed=808,
        mode="commit_ready",
        requester_kind="user",
        requester_id="pilot",
        session_ref=None,
        root=tmp_path,
    )
    receipt = character_retrieval.resolve_existing_character_query(query, tmp_path / "packet", root=tmp_path)
    assert receipt["status"] == "RETRIEVED_CANON"
    assert receipt["answer"]["fields"][0]["value"]["canonical_id"] == "char_ada_north"


def test_same_name_is_disambiguated_by_committed_faction_relation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_character(tmp_path, "char_one", "Morgan Vale", faction_id="galactic_union")
    _write_character(tmp_path, "char_two", "Morgan Vale", faction_id="vorran")
    _patch(monkeypatch)
    query = character_retrieval.compile_existing_character_query_if_applicable(
        "Who is Morgan Vale?",
        {"name": "Morgan Vale", "faction_id": "vorran", "existence_status": "known"},
        seed=808,
        mode="commit_ready",
        requester_kind="user",
        requester_id="pilot",
        session_ref=None,
        root=tmp_path,
    )
    receipt = character_retrieval.resolve_existing_character_query(query, tmp_path / "packet", root=tmp_path)
    assert receipt["status"] == "RETRIEVED_CANON"
    assert receipt["answer"]["fields"][0]["value"]["canonical_id"] == "char_two"


def test_unresolved_same_name_blocks_instead_of_declaring_true_conflict_or_generating(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_character(tmp_path, "char_one", "Morgan Vale", faction_id="galactic_union")
    _write_character(tmp_path, "char_two", "Morgan Vale", faction_id="vorran")
    _patch(monkeypatch)
    query = character_retrieval.compile_existing_character_query_if_applicable(
        "Who is Morgan Vale?",
        {"name": "Morgan Vale", "existence_status": "known"},
        seed=808,
        mode="commit_ready",
        requester_kind="user",
        requester_id="pilot",
        session_ref=None,
        root=tmp_path,
    )
    receipt = character_retrieval.resolve_existing_character_query(query, tmp_path / "packet", root=tmp_path)
    assert receipt["status"] == "EXECUTION_BLOCKED"
    assert receipt["blockers"][0]["kind"] == "referent_ambiguous"
    assert receipt["conflicts"] == []


def test_relation_only_candidate_blocks_duplicate_generation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_character(
        tmp_path,
        "char_existing",
        "Existing Person",
        role="Survey Officer",
        faction_id="galactic_union",
        location_type="organization",
        location_ref="org_survey_corps",
    )
    _patch(monkeypatch)
    discovery = character_retrieval.discover_character_candidates(
        {
            "role": "Survey Officer",
            "faction_id": "galactic_union",
            "location_type": "organization",
            "location_ref": "org_survey_corps",
        },
        tmp_path,
    )
    assert [item["canonical_id"] for item in discovery["relation_only_candidates"]] == ["char_existing"]

    query = character_retrieval.compile_existing_character_query_if_applicable(
        "Complete the encountered survey officer.",
        {
            "role": "Survey Officer",
            "faction_id": "galactic_union",
            "location_type": "organization",
            "location_ref": "org_survey_corps",
            "existence_status": "confirmed_unrecorded",
        },
        seed=808,
        mode="commit_ready",
        requester_kind="system",
        requester_id="test",
        session_ref=None,
        root=tmp_path,
    )
    assert query is not None
    receipt = character_retrieval.resolve_existing_character_query(query, tmp_path / "packet", root=tmp_path)
    assert receipt["status"] == "EXECUTION_BLOCKED"
    assert receipt["blockers"][0]["kind"] == "possible_existing_referent"


def test_no_existing_match_allows_normal_generation_compiler(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch(monkeypatch)
    monkeypatch.setattr(core, "repository_baselines", lambda _root: BASELINES)
    query = core.compile_character_query(
        "Complete this new officer.",
        {
            "role": "New Survey Officer",
            "faction_id": "galactic_union",
            "location_type": "survey_vessel",
            "observed_behavior": [],
            "existence_status": "confirmed_unrecorded",
        },
        root=tmp_path,
    )
    assert query["query_kind"] == "complete"
    assert query["subject"]["existence_status"] == "confirmed_unrecorded"


def test_shared_invocation_facade_routes_character_retrieval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_character(tmp_path, "char_ada_north", "Ada North")
    _patch(monkeypatch)
    monkeypatch.setattr(invocation, "compile_character_query", core.compile_character_query)

    envelope = invocation.compile_character_invocation(
        "Who is Ada North?",
        {"name": "Ada North", "existence_status": "known"},
        invocation_mode="embedded",
        caller_kind="capability",
        caller_ref="ace.test.lookup",
        root=tmp_path,
    )
    assert envelope["query"]["query_kind"] == "retrieve"

    result = invocation.resolve_invocation(envelope, tmp_path / "packet", root=tmp_path)
    assert result["determination"]["status"] == "RETRIEVED_CANON"
    assert Path(result["invocation_sidecar"]).is_file()


def test_explicit_unknown_name_does_not_silently_generate_different_person(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch(monkeypatch)
    query = character_retrieval.compile_existing_character_query_if_applicable(
        "Who is Nobody Recorded?",
        {"name": "Nobody Recorded", "existence_status": "unknown"},
        seed=808,
        mode="commit_ready",
        requester_kind="user",
        requester_id="pilot",
        session_ref=None,
        root=tmp_path,
    )
    assert query is not None
    receipt = character_retrieval.resolve_existing_character_query(query, tmp_path / "packet", root=tmp_path)
    assert receipt["status"] == "EXECUTION_BLOCKED"
    assert receipt["blockers"][0]["kind"] == "semantic_coverage_incomplete"

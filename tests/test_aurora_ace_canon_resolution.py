from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from ace import canon_resolution, core, invocation  # noqa: E402


BASELINES = [
    {"repository": "root", "path": ".", "commit_sha": "a" * 40, "authority_role": "control_plane"},
    {"repository": "CanonRec", "path": core.CANONREC_REL.as_posix(), "commit_sha": "b" * 40, "authority_role": "canon"},
    {"repository": "aurora-cloudbank-symbolic-main", "path": core.CLOUDBANK_REL.as_posix(), "commit_sha": "c" * 40, "authority_role": "runtime"},
]


def _capability_index() -> dict[str, object]:
    return {
        "schema_version": core.SCHEMA_VERSION,
        "record_type": "ace_warm_capability_index",
        "engine_version": core.ENGINE_VERSION,
        "baselines": BASELINES,
        "capabilities": [
            {
                "capability_id": canon_resolution.RETRIEVAL_CAPABILITY,
                "repository": "root",
                "repository_sha": "a" * 40,
                "manifest_sha256": "1" * 64,
                "lifecycle": "active",
            },
            {
                "capability_id": canon_resolution.DERIVATION_CAPABILITY,
                "repository": "root",
                "repository_sha": "a" * 40,
                "manifest_sha256": "2" * 64,
                "lifecycle": "active",
            },
        ],
    }


def _write_claim(root: Path, name: str, value: object, *, certainty: str = "CANON") -> str:
    rel = Path("canon/L1/station/test_facts") / f"{name}.json"
    path = root / core.CANONREC_REL / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"certainty": certainty, "fact": {"value": value}}, indent=2) + "\n",
        encoding="utf-8",
    )
    return rel.as_posix()


def _patch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(canon_resolution, "repository_baselines", lambda _root: BASELINES)
    monkeypatch.setattr(canon_resolution, "build_capability_index", lambda _root: _capability_index())


def _query(
    root: Path,
    refs: list[str],
    *,
    derivation_rule: str | None = None,
) -> dict[str, object]:
    return canon_resolution.compile_canon_query(
        "What is the canonical test value?",
        {"evidence_refs": refs, "layers": ["L1"]},
        subject_ref="test.subject",
        field_path="fact.value",
        claim_path="fact.value",
        derivation_rule=derivation_rule,
        root=root,
    )


def test_retrieved_canon_returns_existing_value_without_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch(monkeypatch)
    refs = [
        _write_claim(tmp_path, "a", "non-rotating core"),
        _write_claim(tmp_path, "b", "non-rotating core"),
    ]
    query = _query(tmp_path, refs)
    receipt = canon_resolution.resolve_canon_query(query, tmp_path / "packet", root=tmp_path)

    assert receipt["status"] == "RETRIEVED_CANON"
    assert receipt["answer"]["fields"][0]["value"] == "non-rotating core"
    assert receipt["answer"]["fields"][0]["origin"] == "retrieved"
    assert receipt["materialization"]["status"] == "not_required"
    assert receipt["transactions"] == []
    assert receipt["conflicts"] == []


def test_derived_canon_uses_only_allowlisted_deterministic_rule(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch(monkeypatch)
    refs = [
        _write_claim(tmp_path, "a", ["hydroponics", "galley"]),
        _write_claim(tmp_path, "b", ["galley", "recreation"]),
    ]
    query = _query(tmp_path, refs, derivation_rule="sorted_unique_union")
    receipt = canon_resolution.resolve_canon_query(query, tmp_path / "packet", root=tmp_path)

    assert receipt["status"] == "DERIVED_CANON"
    assert receipt["answer"]["fields"][0]["value"] == ["galley", "hydroponics", "recreation"]
    assert receipt["answer"]["fields"][0]["origin"] == "deterministic_derivation"
    assert receipt["materialization"]["status"] == "not_required"
    derivation = json.loads((tmp_path / "packet/receipts/derivation.json").read_text(encoding="utf-8"))
    assert derivation["rule"] == "sorted_unique_union"


def test_true_conflict_never_selects_winner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch(monkeypatch)
    refs = [
        _write_claim(tmp_path, "a", "Deck D"),
        _write_claim(tmp_path, "b", "Central Core"),
    ]
    query = _query(tmp_path, refs)
    receipt = canon_resolution.resolve_canon_query(query, tmp_path / "packet", root=tmp_path)

    assert receipt["status"] == "TRUE_CONFLICT"
    assert receipt["answer"]["fields"][0]["value"] is None
    assert len(receipt["conflicts"]) == 1
    assert receipt["conflicts"][0]["kind"] == "mutually_exclusive_committed_claims"
    assert len(receipt["conflicts"][0]["claim_refs"]) == 2
    assert receipt["materialization"]["status"] == "blocked"


def test_missing_authoritative_claim_routes_to_completion_instead_of_fake_retrieval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch(monkeypatch)
    ref = _write_claim(tmp_path, "staging", "possible value", certainty="STAGING")
    query = _query(tmp_path, [ref])
    receipt = canon_resolution.resolve_canon_query(query, tmp_path / "packet", root=tmp_path)

    assert receipt["status"] == "EXECUTION_BLOCKED"
    assert receipt["answer"]["no_prior_record"] is True
    assert receipt["blockers"][0]["kind"] == "semantic_coverage_incomplete"
    assert "completion/generation" in receipt["blockers"][0]["recovery_action"]


def test_baseline_advance_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch(monkeypatch)
    ref = _write_claim(tmp_path, "a", "value")
    query = _query(tmp_path, [ref])
    monkeypatch.setattr(
        canon_resolution,
        "repository_baselines",
        lambda _root: [*BASELINES[:-1], {**BASELINES[-1], "commit_sha": "d" * 40}],
    )
    with pytest.raises(core.ACEError, match="baseline no longer matches"):
        canon_resolution.resolve_canon_query(query, tmp_path / "packet", root=tmp_path)


def test_canon_fact_uses_shared_first_class_invocation_facade(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch(monkeypatch)
    ref = _write_claim(tmp_path, "a", "value")
    query = _query(tmp_path, [ref])
    envelope = invocation.build_invocation_envelope(
        query,
        invocation_mode="embedded",
        caller_kind="capability",
        caller_ref="ace.test.caller",
    )
    result = invocation.resolve_invocation(envelope, tmp_path / "packet", root=tmp_path)

    assert result["determination"]["status"] == "RETRIEVED_CANON"
    sidecar = json.loads(Path(result["invocation_sidecar"]).read_text(encoding="utf-8"))
    assert sidecar["visibility"] == "inspectable"
    assert sidecar["determination_status"] == "RETRIEVED_CANON"


def test_canon_query_rejects_path_escape_and_unregistered_derivation(tmp_path: Path) -> None:
    with pytest.raises(core.ACEError, match="unsafe CanonRec evidence path"):
        canon_resolution.compile_canon_query(
            "question",
            {"evidence_refs": ["../escape.json"]},
            subject_ref="subject",
            field_path="fact.value",
            root=tmp_path,
        )
    with pytest.raises(core.ACEError, match="unsupported derivation_rule"):
        canon_resolution.compile_canon_query(
            "question",
            {"evidence_refs": ["canon/example.json"]},
            subject_ref="subject",
            field_path="fact.value",
            derivation_rule="pick_first",
            root=tmp_path,
        )

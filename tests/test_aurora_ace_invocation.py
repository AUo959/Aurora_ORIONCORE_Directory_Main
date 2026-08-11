from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from ace import core  # noqa: E402
from ace import invocation  # noqa: E402


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
        "observed_behavior": ["coordinated emergency supply allocation"],
        "contextual_refs": ["scenario.ace.invocation.001"],
    }


def minimal_query(*, specialist_first: bool = True) -> dict[str, object]:
    return {
        "schema_version": core.SCHEMA_VERSION,
        "record_type": "ace_query_envelope",
        "generation_policy": {"prefer_existing_specialists": specialist_first},
    }


def _compile(monkeypatch: pytest.MonkeyPatch, **kwargs: object) -> dict[str, object]:
    monkeypatch.setattr(core, "repository_baselines", lambda _root: BASELINES)
    return invocation.compile_character_invocation(
        "What is this character's name and background?",
        character_context(),
        seed=808,
        **kwargs,
    )


def test_interactive_invocation_is_first_class_and_inspectable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    envelope = _compile(monkeypatch)

    assert envelope["invocation_mode"] == "interactive"
    assert envelope["automatic"] is False
    assert envelope["visibility"] == "inspectable"
    assert envelope["caller"]["kind"] == "user"
    assert envelope["trigger"]["kind"] == "direct_query"
    assert envelope["query"]["generation_policy"]["prefer_existing_specialists"] is True
    assert envelope["query_sha256"] == core.semantic_sha256(envelope["query"])


def test_embedded_invocation_uses_the_same_query_engine_and_preserves_parent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    envelope = _compile(
        monkeypatch,
        invocation_mode="embedded",
        caller_kind="capability",
        caller_ref="ace.capability.example.workflow",
        parent_invocation_ref="aurora.workflow.example.001",
    )

    assert envelope["invocation_mode"] == "embedded"
    assert envelope["automatic"] is False
    assert envelope["caller"] == {
        "kind": "capability",
        "caller_ref": "ace.capability.example.workflow",
        "parent_invocation_ref": "aurora.workflow.example.001",
    }
    # The nested query is still a normal ACE query; embedded use does not fork a private engine.
    assert envelope["query"]["record_type"] == "ace_query_envelope"
    assert envelope["query"]["requester"]["kind"] == "system"


def test_autonomic_invocation_is_automatic_but_never_invisible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    envelope = _compile(
        monkeypatch,
        invocation_mode="autonomic",
        caller_kind="system",
        caller_ref="orion.l1.embodiment.registry",
        seam_ref="L1-EMB-MCP-SHUTTLE-BAY:canonical_location",
        trigger_policy_ref="ace.policy.coherence-seam.v1",
    )

    assert envelope["automatic"] is True
    assert envelope["visibility"] == "inspectable"
    assert envelope["trigger"]["kind"] == "coherence_seam"
    assert envelope["trigger"]["seam_ref"] == "L1-EMB-MCP-SHUTTLE-BAY:canonical_location"
    assert envelope["trigger"]["trigger_policy_ref"] == "ace.policy.coherence-seam.v1"
    assert envelope["invocation_id"].startswith("ace.invocation.autonomic.")


def test_autonomic_invocation_fails_closed_without_seam_and_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(core.ACEError, match="trigger.seam_ref"):
        _compile(
            monkeypatch,
            invocation_mode="autonomic",
            caller_kind="system",
            caller_ref="orion.l1.embodiment.registry",
        )


def test_invocation_rejects_synthesis_around_specialist_tooling() -> None:
    with pytest.raises(core.ACEError, match="specialist-first"):
        invocation.build_invocation_envelope(minimal_query(specialist_first=False))


def test_invocation_rejects_private_non_ace_query() -> None:
    query = minimal_query()
    query["record_type"] = "private_resolver_query"
    with pytest.raises(core.ACEError, match="normal supported ACE query envelope"):
        invocation.build_invocation_envelope(query)


def test_resolve_links_invocation_to_shared_determination_and_sidecar(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    query = minimal_query()
    envelope = invocation.build_invocation_envelope(query)

    calls: list[dict[str, object]] = []

    def fake_resolve(
        payload: dict[str, object], output_dir: Path, *, root: Path = core.ROOT
    ) -> dict[str, object]:
        calls.append({"payload": payload, "output_dir": output_dir, "root": root})
        return {
            "determination_id": "ace.determination.example.001",
            "status": "RETRIEVED_CANON",
        }

    monkeypatch.setattr(invocation, "resolve_character_query", fake_resolve)
    output = tmp_path / "packet"
    result = invocation.resolve_invocation(envelope, output)

    assert calls[0]["payload"] == query
    assert result["determination"]["determination_id"] == "ace.determination.example.001"
    sidecar = Path(result["invocation_sidecar"])
    persisted = json.loads(sidecar.read_text(encoding="utf-8"))
    assert persisted["invocation_id"] == envelope["invocation_id"]
    assert persisted["determination_ref"] == "ace.determination.example.001"
    assert persisted["visibility"] == "inspectable"

    report = core.validate_json_schema(
        sidecar,
        REPO_ROOT / "catalog/schemas/aurora_ace_invocation_envelope.schema.json",
        REPO_ROOT,
    )
    assert report["ok"] is True


def test_contract_declares_automatic_not_invisible() -> None:
    contract = json.loads(
        (REPO_ROOT / "catalog/contracts/aurora_ace_invocation_contract_v0_2.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["invocation_modes"]["autonomic"]["automatic"] is True
    assert contract["inspectability"]["automatic_invocation_may_hide_provenance"] is False
    assert contract["tooling_first"]["registered_specialist_precedence"] is True
    assert contract["tooling_first"]["free_synthesis_as_shortcut"] is False

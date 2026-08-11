from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS = REPO_ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from ace import facility, invocation  # noqa: E402
from ace import core  # noqa: E402


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


def facility_context() -> dict[str, object]:
    return {
        "subject_ref": "L1-EMB-MCP-SHUTTLE-BAY",
        "component": "MCP Security / Shuttle Bay",
        "l1_kind": "controlled_admission_facility",
        "current_location": "unresolved",
        "location_certainty": "UNCONFIRMED",
        "authority_class": "admission_and_security",
        "evidence_class": "recoverable_historical_implementation",
        "source_refs": ["owner_mcp_embodiment_ruling", "cloudbank_history:4f17e6c3"],
        "provider_status": "unbound",
        "required_for_resume": True,
        "causal_use_permitted": False,
        "blockers": [
            "canonical_location",
            "reviewed_routing_registry",
            "quarantine_state_machine",
            "actor_bound_approval",
        ],
    }


def coherence_seam() -> dict[str, object]:
    context = facility_context()
    return {
        "schema_version": "0.1.0",
        "record_type": "ace_coherence_seam",
        "target_engine": "ACE",
        "invocation_mode": "autonomic",
        "caller": {
            "kind": "system",
            "caller_ref": "cloudbank.l1.embodiment_registry",
        },
        "trigger": {
            "kind": "coherence_seam",
            "reason": "The audited L1 embodiment registry contains a routine canonical-location gap.",
            "seam_ref": "L1-EMB-MCP-SHUTTLE-BAY:canonical_location",
            "trigger_policy_ref": "ace.policy.l1-embodiment-coherence-seam.v1",
        },
        "query_kind": "facility_topology",
        "question": "Determine the canonical L1 facility location for MCP Security / Shuttle Bay.",
        "subject": {
            "entity_type": "facility",
            "subject_ref": "L1-EMB-MCP-SHUTTLE-BAY",
            "existence_status": "confirmed_unrecorded_attribute",
            "context": context,
        },
        "requested_output": "canonical_location",
        "constraints": {
            "specialist_first": True,
            "inspectable": True,
            "activation_authority": False,
            "runtime_mutation_allowed": False,
            "canon_materialization_authority": False,
            "experiment_advance_allowed": False,
        },
    }


def _write_fixture_evidence(root: Path) -> None:
    contract = root / "catalog/contracts/orion_l1_embodiment_registry.v0_1.json"
    purpose = root / core.CANONREC_REL / facility.STATION_PURPOSE_REL
    physical = root / core.CANONREC_REL / facility.PHYSICAL_SPACE_README_REL
    technical = root / core.CANONREC_REL / facility.TECHNICAL_REFERENCE_REL
    contract.parent.mkdir(parents=True, exist_ok=True)
    purpose.parent.mkdir(parents=True, exist_ok=True)
    physical.parent.mkdir(parents=True, exist_ok=True)
    technical.parent.mkdir(parents=True, exist_ok=True)
    contract.write_text(
        json.dumps(
            {
                "embodiments": [
                    {
                        "id": "L1-EMB-MCP-SHUTTLE-BAY",
                        "gaps": ["canonical location"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    purpose.write_text(
        "Owner ruling: L1 is the chassis. The station includes ring, core, crew, dispatch, and life support.\n",
        encoding="utf-8",
    )
    physical.write_text(
        "STAGING physical topology: non-rotating zero-g core cylinder with the docking complex.\n",
        encoding="utf-8",
    )
    technical.write_text(
        "Reference constraint: docking is located in the non-rotating core; exact bay geometry is unresolved.\n",
        encoding="utf-8",
    )


def _fake_capability_index() -> dict[str, object]:
    return {
        "schema_version": core.SCHEMA_VERSION,
        "record_type": "ace_warm_capability_index",
        "engine_version": core.ENGINE_VERSION,
        "baselines": BASELINES,
        "capabilities": [
            {
                "capability_id": "ace.capability.context.resolve",
                "repository": "root",
                "manifest_sha256": "1" * 64,
                "lifecycle": "active",
            },
            {
                "capability_id": "ace.capability.canonrec.materialize.entity",
                "repository": "CanonRec",
                "manifest_sha256": "2" * 64,
                "lifecycle": "blocked",
            },
        ],
    }


@pytest.mark.unit
def test_compile_facility_query_preserves_specialist_first_and_l1_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(facility, "repository_baselines", lambda _root: BASELINES)

    query = facility.compile_facility_query(
        "Where is the MCP Security / Shuttle Bay?",
        facility_context(),
        subject_ref="L1-EMB-MCP-SHUTTLE-BAY",
        root=REPO_ROOT,
    )

    assert query["subject"]["entity_type"] == "facility"
    assert query["subject"]["existence_status"] == "known"
    assert query["scope"]["layers"] == ["L1"]
    assert query["generation_policy"]["prefer_existing_specialists"] is True
    assert query["generation_policy"]["connective_synthesis_policy"] == "bounded_completion"
    assert query["generation_policy"]["constitutive_simulation_allowed"] is False
    assert query["execution_policy"]["budgets"]["max_new_entities"] == 0
    location_output = next(
        item
        for item in query["requested_outputs"]
        if item["field_path"] == "facility.canonical_location"
    )
    assert location_output["preferred_capability_refs"] == []


@pytest.mark.unit
def test_cloudbank_seam_becomes_the_same_inspectable_autonomic_ace_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(facility, "repository_baselines", lambda _root: BASELINES)

    envelope = invocation.compile_facility_invocation_from_seam(
        coherence_seam(),
        root=REPO_ROOT,
    )

    assert envelope["invocation_mode"] == "autonomic"
    assert envelope["automatic"] is True
    assert envelope["visibility"] == "inspectable"
    assert envelope["caller"]["caller_ref"] == "cloudbank.l1.embodiment_registry"
    assert envelope["trigger"]["seam_ref"] == "L1-EMB-MCP-SHUTTLE-BAY:canonical_location"
    assert envelope["trigger"]["trigger_policy_ref"] == "ace.policy.l1-embodiment-coherence-seam.v1"
    assert envelope["query"]["record_type"] == "ace_query_envelope"
    assert envelope["query"]["subject"]["entity_type"] == "facility"


@pytest.mark.unit
def test_cloudbank_seam_fails_closed_if_it_attempts_to_widen_authority() -> None:
    seam = coherence_seam()
    seam["constraints"]["runtime_mutation_allowed"] = True

    with pytest.raises(core.ACEError, match="widen authority"):
        facility.validate_coherence_seam(seam)


@pytest.mark.unit
def test_facility_resolution_returns_complete_commit_ready_noncausal_packet(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _write_fixture_evidence(tmp_path)
    monkeypatch.setattr(facility, "repository_baselines", lambda _root: BASELINES)
    monkeypatch.setattr(facility, "build_capability_index", lambda _root: _fake_capability_index())

    envelope = invocation.compile_facility_invocation_from_seam(
        coherence_seam(),
        root=tmp_path,
    )
    out = tmp_path / "packets" / "mcp-location"
    result = invocation.resolve_invocation(envelope, out, root=tmp_path)
    receipt = result["determination"]

    assert receipt["status"] == "EXECUTION_BLOCKED"
    assert receipt["answer_contract"]["overall_status"] == "complete"
    assert receipt["validation"]["overall_status"] == "pass"
    assert receipt["materialization"]["status"] == "commit_ready"
    assert receipt["materialization"]["commit_sha"] is None
    assert receipt["blockers"][0]["kind"] == "materialization_authority_missing"
    location = next(
        field["value"]
        for field in receipt["answer"]["fields"]
        if field["field_path"] == "facility.canonical_location"
    )
    causal = next(
        field["value"]
        for field in receipt["answer"]["fields"]
        if field["field_path"] == "facility.causal_use_permitted"
    )
    assert location.startswith("Non-rotating core docking complex")
    assert causal is False
    candidate = json.loads((out / "candidate_facility_binding.json").read_text(encoding="utf-8"))
    assert candidate["activation_authority"] is False
    assert candidate["causal_use_permitted"] is False
    assert candidate["exact_geometry_authorized"] is False
    assert "exact_deck" in json.loads(
        (out / "receipts/facility_topology_selection.json").read_text(encoding="utf-8")
    )["forbidden_precision"]
    sidecar = json.loads(Path(result["invocation_sidecar"]).read_text(encoding="utf-8"))
    assert sidecar["visibility"] == "inspectable"
    assert sidecar["determination_ref"] == receipt["determination_id"]


@pytest.mark.unit
def test_facility_policy_rejects_unowned_l1_kind_instead_of_free_synthesis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(facility, "repository_baselines", lambda _root: BASELINES)
    context = facility_context()
    context["l1_kind"] = "human_command_authority_interface"
    query = facility.compile_facility_query(
        "Where is this command authority interface?",
        context,
        subject_ref="L1-EMB-COMMAND-BRIDGE",
        root=REPO_ROOT,
    )

    with pytest.raises(core.ACEError, match="No registered specialist or bounded facility policy"):
        facility._bounded_location(query["subject"]["context"], {"constraint_summary": {"core_docking_topology_supported": True}})

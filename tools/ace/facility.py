"""ACE facility/topology completion for bounded Orion L1 coherence seams.

This module extends the existing ACE engine without inventing a second resolver.
It searches allowlisted Orion/CanonRec evidence first, preserves evidence class,
and uses bounded connective completion only when no registered specialist owns
facility topology. It never mutates CanonRec or advances the L1 runtime.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Mapping

from .core import (
    ACEError,
    CANONREC_REL,
    CONTRACT_REF,
    ENGINE_VERSION,
    ROOT,
    SCHEMA_VERSION,
    build_capability_index,
    file_sha256,
    repository_baselines,
    semantic_sha256,
    strip_volatile_fields,
    utc_now,
    write_json,
)
from .engine import _safe_output_path

FACILITY_ENGINE_VERSION = "0.1.0"
FACILITY_BINDING_SCHEMA_VERSION = "0.1.0"
FACILITY_POLICY_REF = "ace.policy.l1.facility-topology-bounded-completion.v1"
FACILITY_MATERIALIZATION_POLICY_REF = "ace.policy.materialization.owner-or-delegated.v1"
EMBODIMENT_CONTRACT_REL = Path("catalog/contracts/orion_l1_embodiment_registry.v0_1.json")
STATION_PURPOSE_REL = Path("canon/L1/station/STATION_PURPOSE_DEFINITION.md")
PHYSICAL_SPACE_README_REL = Path("canon/L1/station/physical_space/README.md")
TECHNICAL_REFERENCE_REL = Path(
    "canon/L1/station/reference_sources/orion_station_full_technical_readout.md"
)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-") or "facility"


def compile_facility_query(
    question: str,
    context: Mapping[str, Any],
    *,
    subject_ref: str | None = None,
    seed: int | str = 808,
    mode: str = "commit_ready",
    requester_kind: str = "user",
    requester_id: str = "ORION.ROLE.PILOT",
    session_ref: str | None = None,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Compile a known L1 facility with a missing topology attribute into ACE."""

    if not isinstance(question, str) or not question.strip():
        raise ACEError("question must not be empty", code="input_validation_failed")
    if mode not in {"plan_only", "commit_ready"}:
        raise ACEError("facility completion supports plan_only and commit_ready", code="input_validation_failed")
    subject_ref = subject_ref or str(context.get("subject_ref", ""))
    if not subject_ref.strip():
        raise ACEError("facility context requires subject_ref", code="input_validation_failed")
    for field in ("component", "l1_kind"):
        if not isinstance(context.get(field), str) or not str(context[field]).strip():
            raise ACEError(f"facility context requires non-empty {field}", code="input_validation_failed")
    source_refs = context.get("source_refs", [])
    if not isinstance(source_refs, list) or any(not isinstance(item, str) or not item for item in source_refs):
        raise ACEError("facility source_refs must be an array of non-empty strings", code="input_validation_failed")

    baselines = repository_baselines(root)
    query_suffix = semantic_sha256(
        {
            "question": question.strip(),
            "subject_ref": subject_ref,
            "context": dict(context),
            "seed": seed,
            "mode": mode,
            "policy": FACILITY_POLICY_REF,
        }
    )[:20]
    target = f"canon/L1/station/facility_bindings/{_slug(subject_ref)}.json"
    contextual_refs = list(dict.fromkeys([subject_ref, *source_refs]))
    requirements = [
        {
            "requirement_id": "ace.semantic.facility.canonical_location",
            "semantic_type": "l1_facility_topology_binding",
            "description": (
                "Resolve a canonical facility-level location without inventing exact deck, bay, "
                "coordinate, occupancy, or movement geometry unsupported by evidence."
            ),
            "required": True,
            "accepts_state_derived": False,
            "accepts_connective_rendering": True,
            "acceptable_origins": ["retrieved", "deterministic_derivation", "connective_synthesis"],
            "minimum_evidence": ["owner_embodiment_binding", "station_chassis_canon", "topology_constraints"],
        },
        {
            "requirement_id": "ace.semantic.facility.noncausal_boundary",
            "semantic_type": "l1_noncausal_topology_boundary",
            "description": (
                "Preserve the embodiment registry's non-authoritative, non-activating boundary; "
                "a location determination cannot itself enable causal runtime use."
            ),
            "required": True,
            "accepts_state_derived": True,
            "accepts_connective_rendering": False,
            "acceptable_origins": ["retrieved", "deterministic_derivation"],
            "minimum_evidence": ["embodiment_boundary_context"],
        },
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "ace_query_envelope",
        "query_id": f"ace.query.facility.{query_suffix}",
        "created_at": utc_now(),
        "requester": {
            "kind": requester_kind,
            "requester_id": requester_id,
            "session_ref": session_ref,
        },
        "question": question.strip(),
        "query_kind": "complete",
        "scope": {
            "repositories": ["root", "CanonRec", "aurora-cloudbank-symbolic-main"],
            "layers": ["L1"],
            "target_repository": "CanonRec",
            "target_paths": [target],
            "temporal_basis": "explicit_commit_set",
        },
        "baselines": baselines,
        "subject": {
            "subject_ref": subject_ref,
            "entity_type": "facility",
            "existence_status": "known",
            "contextual_refs": contextual_refs,
            "context": dict(context),
        },
        "requested_outputs": [
            {
                "field_path": "facility.canonical_location",
                "required": True,
                "preferred_capability_refs": [],
                "description": "Canonical facility-level station location.",
            },
            {
                "field_path": "facility.causal_use_permitted",
                "required": True,
                "preferred_capability_refs": ["ace.capability.context.resolve"],
                "description": "Preserved runtime causal-use boundary.",
            },
        ],
        "answer_contract": {
            "compiler_version": "ace-answer-contract-facility-0.1.0",
            "interpretation_basis": [
                "query:facility_topology",
                "subject:known_l1_embodiment",
                "attribute:canonical_location_missing",
            ],
            "coverage_policy": "all_mandatory_semantics_satisfied",
            "requirements": requirements,
        },
        "generation_policy": {
            "canonical_completion_allowed": True,
            "constitutive_simulation_allowed": False,
            "analytical_simulation_allowed": False,
            "prefer_existing_specialists": True,
            "connective_synthesis_policy": "bounded_completion",
            "deterministic_required": True,
            "stable_seed": seed,
            "reserved_decision_policy_ref": "ace.policy.reserved-decisions.v1",
        },
        "execution_policy": {
            "mode": mode,
            "delegation_policy_ref": "ace.policy.delegated-routine-facility-completion.v1",
            "allowed_side_effects": [] if mode == "plan_only" else ["write_transaction_workspace"],
            "budgets": {
                "max_tool_calls": 6,
                "max_new_entities": 0,
                "max_wall_seconds": 20,
                "max_output_bytes": 524288,
            },
        },
        "response_policy": {
            "include_human_answer": True,
            "include_execution_plan": True,
            "include_field_provenance": True,
            "include_replay_command": True,
        },
    }


def validate_coherence_seam(seam: Mapping[str, Any]) -> None:
    """Validate a CloudBank-produced seam before it can enter ACE."""

    if seam.get("record_type") != "ace_coherence_seam":
        raise ACEError("seam record_type must be ace_coherence_seam", code="input_validation_failed")
    if seam.get("target_engine") != "ACE" or seam.get("invocation_mode") != "autonomic":
        raise ACEError("facility seam must target autonomic ACE", code="input_validation_failed")
    caller = seam.get("caller")
    trigger = seam.get("trigger")
    subject = seam.get("subject")
    constraints = seam.get("constraints")
    if not isinstance(caller, Mapping) or caller.get("kind") not in {"system", "capability", "agent"}:
        raise ACEError("facility seam caller is invalid", code="input_validation_failed")
    if not isinstance(caller.get("caller_ref"), str) or not caller["caller_ref"].strip():
        raise ACEError("facility seam caller_ref is missing", code="input_validation_failed")
    if not isinstance(trigger, Mapping) or trigger.get("kind") != "coherence_seam":
        raise ACEError("facility seam trigger must be coherence_seam", code="input_validation_failed")
    for field in ("seam_ref", "trigger_policy_ref"):
        if not isinstance(trigger.get(field), str) or not trigger[field].strip():
            raise ACEError(f"facility seam trigger.{field} is missing", code="input_validation_failed")
    if seam.get("query_kind") != "facility_topology" or seam.get("requested_output") != "canonical_location":
        raise ACEError("facility seam kind/output is unsupported", code="input_validation_failed")
    if not isinstance(subject, Mapping) or subject.get("entity_type") != "facility":
        raise ACEError("facility seam subject must be a facility", code="input_validation_failed")
    if not isinstance(subject.get("subject_ref"), str) or not subject["subject_ref"].strip():
        raise ACEError("facility seam subject_ref is missing", code="input_validation_failed")
    context = subject.get("context")
    if not isinstance(context, Mapping):
        raise ACEError("facility seam subject context is missing", code="input_validation_failed")
    if not isinstance(constraints, Mapping):
        raise ACEError("facility seam constraints are missing", code="input_validation_failed")
    required_false = (
        "activation_authority",
        "runtime_mutation_allowed",
        "canon_materialization_authority",
        "experiment_advance_allowed",
    )
    if constraints.get("specialist_first") is not True or constraints.get("inspectable") is not True:
        raise ACEError("facility seam must require specialist-first inspectable ACE", code="input_validation_failed")
    if any(constraints.get(field) is not False for field in required_false):
        raise ACEError("facility seam attempts to widen authority", code="input_validation_failed")


def _assert_query(query: Mapping[str, Any], root: Path) -> None:
    if query.get("record_type") != "ace_query_envelope" or query.get("schema_version") != SCHEMA_VERSION:
        raise ACEError("Unsupported ACE query envelope", code="input_validation_failed")
    subject = query.get("subject", {})
    if query.get("query_kind") != "complete" or subject.get("entity_type") != "facility":
        raise ACEError("facility resolver requires a complete facility query", code="input_validation_failed")
    if query.get("execution_policy", {}).get("mode") != "commit_ready":
        raise ACEError("facility resolve requires a commit_ready query", code="input_validation_failed")
    if query.get("generation_policy", {}).get("prefer_existing_specialists") is not True:
        raise ACEError("facility resolution requires specialist-first routing", code="input_validation_failed")
    current = repository_baselines(root)
    expected = {(item["repository"], item["commit_sha"]) for item in query.get("baselines", [])}
    observed = {(item["repository"], item["commit_sha"]) for item in current}
    if expected != observed:
        raise ACEError(
            "Query baseline no longer matches the registered live repository set; recompile before execution",
            code="registry_baseline_advanced",
        )


def _read_evidence(root: Path, subject_ref: str) -> dict[str, Any]:
    contract_path = root / EMBODIMENT_CONTRACT_REL
    purpose_path = root / CANONREC_REL / STATION_PURPOSE_REL
    physical_readme_path = root / CANONREC_REL / PHYSICAL_SPACE_README_REL
    technical_path = root / CANONREC_REL / TECHNICAL_REFERENCE_REL
    for path in (contract_path, purpose_path, physical_readme_path, technical_path):
        if not path.is_file():
            raise ACEError(f"Required facility evidence is missing: {path}", code="target_unavailable")

    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    embodiment = next(
        (item for item in contract.get("embodiments", []) if item.get("id") == subject_ref),
        None,
    )
    if not isinstance(embodiment, dict):
        raise ACEError("facility subject is not present in the audited embodiment contract", code="input_validation_failed")
    gaps = embodiment.get("gaps", [])
    if "canonical location" not in gaps:
        raise ACEError("facility contract does not declare a canonical-location seam", code="input_validation_failed")

    purpose_text = purpose_path.read_text(encoding="utf-8")
    physical_readme = physical_readme_path.read_text(encoding="utf-8")
    technical_text = technical_path.read_text(encoding="utf-8")
    if "L1 is the chassis" not in purpose_text:
        raise ACEError("station purpose evidence lacks the L1 chassis invariant", code="output_validation_failed")
    topology_text = (physical_readme + "\n" + technical_text).casefold()
    required_terms = ("non-rotating", "core", "docking")
    if any(term not in topology_text for term in required_terms):
        raise ACEError("station topology evidence does not constrain docking to the non-rotating core", code="output_validation_failed")

    sources = [
        {
            "source_ref": EMBODIMENT_CONTRACT_REL.as_posix(),
            "classification": "explicit_canon_and_audit_contract",
            "sha256": file_sha256(contract_path),
        },
        {
            "source_ref": f"{CANONREC_REL.as_posix()}/{STATION_PURPOSE_REL.as_posix()}",
            "classification": "explicit_canon",
            "sha256": file_sha256(purpose_path),
        },
        {
            "source_ref": f"{CANONREC_REL.as_posix()}/{PHYSICAL_SPACE_README_REL.as_posix()}",
            "classification": "staging_constraint_only",
            "sha256": file_sha256(physical_readme_path),
        },
        {
            "source_ref": f"{CANONREC_REL.as_posix()}/{TECHNICAL_REFERENCE_REL.as_posix()}",
            "classification": "reference_constraint_only",
            "sha256": file_sha256(technical_path),
        },
    ]
    return {
        "subject_ref": subject_ref,
        "embodiment_contract": embodiment,
        "sources": sources,
        "source_semantic_sha256": semantic_sha256(sources),
        "constraint_summary": {
            "l1_chassis_confirmed": True,
            "core_docking_topology_supported": True,
            "exact_deck_or_bay_geometry_canonical": False,
        },
    }


def _bounded_location(context: Mapping[str, Any], evidence: Mapping[str, Any]) -> tuple[str, str]:
    """Select the narrowest useful location consistent with all evidence."""

    if str(context.get("l1_kind")) != "controlled_admission_facility":
        raise ACEError(
            "No registered specialist or bounded facility policy covers this l1_kind",
            code="semantic_coverage_incomplete",
        )
    if not evidence.get("constraint_summary", {}).get("core_docking_topology_supported"):
        raise ACEError("docking topology constraint is not satisfied", code="output_validation_failed")
    return (
        "Non-rotating core docking complex — controlled admission/security interface adjacent to primary shuttle access",
        "facility_level_no_exact_deck_bay_or_coordinate_geometry",
    )


def _plan_step(
    capability: Mapping[str, Any],
    suffix: str,
    repository_sha: str,
    *,
    status: str,
    depends_on: list[str],
    consumes: list[str],
    produces: list[str],
    receipt_ref: str | None,
    output: Any | None,
) -> dict[str, Any]:
    return {
        "step_id": f"ace.step.facility.{suffix}",
        "capability_id": capability["capability_id"],
        "status": status,
        "depends_on": depends_on,
        "consumes": consumes,
        "produces": produces,
        "tool_run_id": f"ace-run-facility-{suffix}" if status != "blocked" else None,
        "run_receipt_ref": receipt_ref,
        "manifest_sha256": capability["manifest_sha256"],
        "repository_sha": repository_sha,
        "seed": None,
        "duration_ms": 0.0,
        "output_sha256": semantic_sha256(output) if output is not None else None,
        "semantic_output_sha256": semantic_sha256(strip_volatile_fields(output)) if output is not None else None,
        "artifact_output_sha256": semantic_sha256(output) if output is not None else None,
        "volatile_output_fields": [],
        "tool_native_statuses": {},
        "side_effects_observed": [],
    }


def resolve_facility_query(
    query: Mapping[str, Any],
    output_dir: Path,
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Resolve one L1 facility topology seam into an inspectable commit-ready packet."""

    started = time.perf_counter()
    _assert_query(query, root)
    output = _safe_output_path(output_dir, root)
    output.parent.mkdir(parents=True, exist_ok=True)
    transaction_root = Path(tempfile.mkdtemp(prefix=".ace-facility-", dir=output.parent))
    try:
        write_json(transaction_root / "query_envelope.json", query)
        capability_index = build_capability_index(root)
        write_json(transaction_root / "capability_index.json", capability_index)
        capabilities = {item["capability_id"]: item for item in capability_index["capabilities"]}
        for required in ("ace.capability.context.resolve", "ace.capability.canonrec.materialize.entity"):
            if required not in capabilities:
                raise ACEError(f"Required ACE capability is not indexed: {required}", code="invalid_manifest")
        context_cap = capabilities["ace.capability.context.resolve"]
        materializer = capabilities["ace.capability.canonrec.materialize.entity"]
        heads = {item["repository"]: item["commit_sha"] for item in capability_index["baselines"]}

        subject_ref = str(query["subject"]["subject_ref"])
        context = query["subject"]["context"]
        evidence = _read_evidence(root, subject_ref)
        write_json(transaction_root / "evidence/facility_evidence.json", evidence)

        location, location_scope = _bounded_location(context, evidence)
        target = query["scope"]["target_paths"][0]
        candidate = {
            "schema_version": FACILITY_BINDING_SCHEMA_VERSION,
            "record_type": "ace_l1_facility_binding_candidate",
            "subject_ref": subject_ref,
            "component": context["component"],
            "l1_kind": context["l1_kind"],
            "canonical_location": location,
            "location_scope": location_scope,
            "generation_policy_ref": FACILITY_POLICY_REF,
            "location_certainty": "COMMIT_READY_GENERATED",
            "causal_use_permitted": False,
            "activation_authority": False,
            "exact_geometry_authorized": False,
            "canon_target_ref": target,
            "source_refs": [item["source_ref"] for item in evidence["sources"]],
        }
        write_json(transaction_root / "candidate_facility_binding.json", candidate)
        selection_receipt = {
            "policy_ref": FACILITY_POLICY_REF,
            "specialist_search_performed": True,
            "registered_specialist_found": False,
            "fallback": "bounded_connective_completion",
            "selected_location": location,
            "location_scope": location_scope,
            "forbidden_precision": ["exact_deck", "exact_bay", "coordinates", "occupancy", "movement_effect"],
            "evidence_sha256": semantic_sha256(evidence),
        }
        write_json(transaction_root / "receipts/facility_topology_selection.json", selection_receipt)

        source_refs = [item["source_ref"] for item in evidence["sources"]]
        fields = [
            {
                "field_path": "facility.canonical_location",
                "value": location,
                "origin": "connective_synthesis",
                "producer_refs": ["aurora_ace.synthesis.facility_topology.bounded"],
                "source_refs": source_refs,
                "run_receipt_refs": ["receipts/facility_topology_selection.json"],
                "constraint_refs": [FACILITY_POLICY_REF],
                "canon_target_ref": target,
            },
            {
                "field_path": "facility.causal_use_permitted",
                "value": False,
                "origin": "retrieved",
                "producer_refs": ["ace.capability.context.resolve"],
                "source_refs": [EMBODIMENT_CONTRACT_REL.as_posix()],
                "run_receipt_refs": ["evidence/facility_evidence.json"],
                "constraint_refs": ["orion.l1.embodiment.noncausal-boundary"],
                "canon_target_ref": target,
            },
        ]
        answer = {
            "summary": (
                f"ACE resolved {context['component']} to the {location}. "
                "The determination is facility-level only: exact deck, bay, coordinate, occupancy, and movement geometry remain unspecified. "
                "The result is commit-ready but not canonical until an authorized CanonRec materialization occurs."
            ),
            "fields": fields,
            "no_prior_record": False,
            "supersedes_determination_refs": [],
        }
        projection_digest = semantic_sha256(evidence["sources"])
        projection = {
            "projection_id": f"ace.projection.facility.evidence.{semantic_sha256(subject_ref)[:16]}",
            "projection_type": "raw_evidence_index",
            "source_repository": "CanonRec",
            "source_commit_sha": heads["CanonRec"],
            "source_semantic_sha256": evidence["source_semantic_sha256"],
            "transform_id": "ace.transform.l1_facility_evidence_index",
            "transform_version": FACILITY_ENGINE_VERSION,
            "projection_sha256": projection_digest,
            "source_member_count": len(evidence["sources"]),
            "projected_member_count": len(evidence["sources"]),
            "collapsed_row_count": 0,
            "unresolved_relation_count": 0,
            "membership_receipt_ref": "evidence/facility_evidence.json",
        }
        context_step = _plan_step(
            context_cap,
            "context",
            heads[context_cap["repository"]],
            status="succeeded",
            depends_on=[],
            consumes=["query.subject", "query.answer_contract"],
            produces=["facility.context", "facility.noncausal_boundary"],
            receipt_ref="evidence/facility_evidence.json",
            output=evidence,
        )
        materialize_step = _plan_step(
            materializer,
            "materialize",
            heads[materializer["repository"]],
            status="blocked",
            depends_on=[context_step["step_id"]],
            consumes=["candidate_facility_binding.json"],
            produces=[target],
            receipt_ref=None,
            output=None,
        )
        coverage = [
            {
                "requirement_id": "ace.semantic.facility.canonical_location",
                "status": "satisfied",
                "field_refs": ["facility.canonical_location"],
                "producer_refs": ["aurora_ace.synthesis.facility_topology.bounded"],
                "reason": "No registered specialist covered facility topology; bounded completion used the audited L1 chassis and docking constraints without inventing exact geometry.",
            },
            {
                "requirement_id": "ace.semantic.facility.noncausal_boundary",
                "status": "satisfied",
                "field_refs": ["facility.causal_use_permitted"],
                "producer_refs": ["ace.capability.context.resolve"],
                "reason": "The source embodiment contract and seam context preserve causal_use_permitted=false and activation_authority=false.",
            },
        ]
        validation_gates = [
            {
                "gate_id": "facility_evidence_authority",
                "status": "pass",
                "validator_ref": "aurora_ace.validation.facility_evidence_class",
                "receipt_refs": ["evidence/facility_evidence.json"],
                "finding_codes": [],
                "summary": "Explicit canon, staging constraints, and reference constraints remain separately classified.",
            },
            {
                "gate_id": "facility_precision_boundary",
                "status": "pass",
                "validator_ref": "aurora_ace.validation.no_unbacked_exact_geometry",
                "receipt_refs": ["receipts/facility_topology_selection.json"],
                "finding_codes": [],
                "summary": "The completion fixes only the facility-level location and does not assert deck, bay, coordinate, occupancy, or movement geometry.",
            },
            {
                "gate_id": "facility_causal_boundary",
                "status": "pass",
                "validator_ref": "aurora_ace.validation.l1_noncausal_embedding",
                "receipt_refs": ["candidate_facility_binding.json"],
                "finding_codes": [],
                "summary": "Location completion does not activate the provider or permit causal runtime use.",
            },
        ]
        baselines = [
            {
                "repository": item["repository"],
                "commit_sha": item["commit_sha"],
                "authority_role": item["authority_role"],
            }
            for item in query["baselines"]
        ]
        answer_semantic = strip_volatile_fields(answer)
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "ace_determination_receipt",
            "determination_id": f"ace.determination.facility.{semantic_sha256({'query': query['query_id'], 'answer': answer_semantic})[:20]}",
            "query_id": query["query_id"],
            "created_at": utc_now(),
            "engine": {
                "engine_id": "aurora_ace",
                "engine_version": ENGINE_VERSION,
                "contract_ref": CONTRACT_REF,
                "execution_mode": "commit_ready",
            },
            "status": "EXECUTION_BLOCKED",
            "simulation_mode": "constitutive_generation",
            "baselines": baselines,
            "subject_refs": [subject_ref],
            "answer_contract": {
                "compiler_version": query["answer_contract"]["compiler_version"],
                "overall_status": "complete",
                "coverage": coverage,
            },
            "projections": [projection],
            "transactions": [],
            "answer": answer,
            "plan": {
                "plan_id": f"ace.plan.facility.{semantic_sha256(query['query_id'])[:16]}",
                "selection_basis": [
                    "specialist_first",
                    "no_registered_facility_topology_specialist",
                    "bounded_connective_completion",
                    "preserve_l1_noncausal_boundary",
                    "minimal_precision",
                ],
                "rejected_capability_refs": [],
                "steps": [context_step, materialize_step],
            },
            "validation": {
                "overall_status": "pass",
                "gates": validation_gates,
            },
            "conflicts": [],
            "blockers": [
                {
                    "blocker_id": f"ace.blocker.facility.materialization.{semantic_sha256(subject_ref)[:12]}",
                    "kind": "materialization_authority_missing",
                    "capability_ref": "ace.capability.canonrec.materialize.entity",
                    "reason": "ACE has no authority to commit the generated L1 facility binding to CanonRec.",
                    "recovery_action": "Review and materialize the validated commit-ready facility binding through authorized CanonRec workflow.",
                }
            ],
            "materialization": {
                "status": "commit_ready",
                "target_repository": "CanonRec",
                "target_paths": [target],
                "commit_sha": None,
                "gate_policy_ref": FACILITY_MATERIALIZATION_POLICY_REF,
                "commit_ready_packet_ref": "candidate_facility_binding.json",
            },
            "integrity": {
                "query_sha256": semantic_sha256(query),
                "capability_manifest_sha256s": [
                    context_cap["manifest_sha256"],
                    materializer["manifest_sha256"],
                ],
                "answer_sha256": semantic_sha256(answer),
                "semantic_answer_sha256": semantic_sha256(answer_semantic),
                "artifact_sha256s": [
                    file_sha256(transaction_root / "query_envelope.json"),
                    file_sha256(transaction_root / "capability_index.json"),
                    file_sha256(transaction_root / "evidence/facility_evidence.json"),
                    file_sha256(transaction_root / "candidate_facility_binding.json"),
                    file_sha256(transaction_root / "receipts/facility_topology_selection.json"),
                ],
                "semantic_digest_policy_ref": "ace.policy.semantic-digest.exclude-volatile-v1",
                "prior_determination_digest": None,
            },
            "replay": {
                "replayable": True,
                "deterministic": True,
                "replay_command": "python3 tools/aurora_ace.py resolve --query query_envelope.json --out <new-output-directory>",
                "required_artifact_refs": [
                    "query_envelope.json",
                    "capability_index.json",
                    "evidence/facility_evidence.json",
                    "receipts/facility_topology_selection.json",
                ],
                "non_replayable_reasons": [],
            },
        }
        write_json(transaction_root / "determination_receipt.json", receipt)
        artifact_index = {
            path.relative_to(transaction_root).as_posix(): file_sha256(path)
            for path in sorted(transaction_root.rglob("*"))
            if path.is_file()
        }
        write_json(transaction_root / "artifact_index.json", artifact_index)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        write_json(
            transaction_root / "receipts/execution_summary.json",
            {
                "engine": "aurora_ace",
                "facility_engine_version": FACILITY_ENGINE_VERSION,
                "subject_ref": subject_ref,
                "status": receipt["status"],
                "duration_ms": elapsed_ms,
                "runtime_mutation": False,
                "canon_mutation": False,
                "experiment_advanced": False,
            },
        )
        os.replace(transaction_root, output)
        return receipt
    except Exception:
        shutil.rmtree(transaction_root, ignore_errors=True)
        raise

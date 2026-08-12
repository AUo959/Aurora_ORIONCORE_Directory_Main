"""Read-only CanonRec retrieval, derivation, and true-conflict determination for ACE.

This module implements the non-mutating terminal states that precede generation:

- ``RETRIEVED_CANON`` when authoritative committed evidence already contains one
  unambiguous value for the requested field;
- ``DERIVED_CANON`` when an explicitly allowlisted deterministic derivation rule
  combines authoritative committed values without inventing new world facts;
- ``TRUE_CONFLICT`` when mutually exclusive committed scalar claims remain and no
  authorized deterministic reconciliation rule applies.

The resolver never mutates CanonRec, activates L1 providers, or advances any
simulation. It reads only explicitly scoped JSON evidence paths supplied by the
query and records every source hash in the determination receipt.
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
    canonical_json_bytes,
    file_sha256,
    repository_baselines,
    semantic_sha256,
    strip_volatile_fields,
    utc_now,
    write_json,
)
from .engine import _safe_output_path

CANON_RESOLUTION_VERSION = "0.3.0"
RETRIEVAL_CAPABILITY = "ace.capability.canonrec.retrieve.claims"
DERIVATION_CAPABILITY = "ace.capability.canonrec.derive.claims"
CONFLICT_POLICY_REF = "ace.policy.true-conflict.fail-closed.v1"
DERIVATION_POLICY_REF = "ace.policy.canon-deterministic-derivation.v1"
ALLOWED_DERIVATION_RULES = frozenset({"sorted_unique_union"})
DEFAULT_CANON_CERTAINTIES = ("CANON",)


def _safe_rel_path(value: str) -> Path:
    rel = Path(value)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        raise ACEError(f"unsafe CanonRec evidence path: {value!r}", code="input_validation_failed")
    if rel.suffix.casefold() != ".json":
        raise ACEError(
            "ACE v0.3 canon resolution currently accepts JSON CanonRec evidence only",
            code="input_validation_failed",
        )
    return rel


def _dot_get(payload: Any, path: str) -> Any:
    current = payload
    for part in path.split("."):
        if not part:
            raise ACEError("claim path contains an empty segment", code="input_validation_failed")
        if not isinstance(current, Mapping) or part not in current:
            raise KeyError(path)
        current = current[part]
    return current


def compile_canon_query(
    question: str,
    context: Mapping[str, Any],
    *,
    subject_ref: str,
    field_path: str,
    claim_path: str | None = None,
    certainty_path: str = "certainty",
    derivation_rule: str | None = None,
    mode: str = "read_only",
    requester_kind: str = "user",
    requester_id: str = "ORION.ROLE.PILOT",
    session_ref: str | None = None,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Compile one explicitly scoped CanonRec fact determination.

    ``evidence_refs`` in ``context`` is mandatory and contains paths relative to
    the CanonRec repository root. ACE deliberately does not crawl the entire
    repository in this slice; callers or upstream retrieval tooling define the
    bounded evidence set, and ACE determines what that committed set supports.
    """

    if not isinstance(question, str) or not question.strip():
        raise ACEError("question must not be empty", code="input_validation_failed")
    if not isinstance(subject_ref, str) or not subject_ref.strip():
        raise ACEError("subject_ref must be a non-empty string", code="input_validation_failed")
    if not isinstance(field_path, str) or not re.fullmatch(r"[A-Za-z0-9_.\[\]-]+", field_path):
        raise ACEError("field_path is invalid", code="input_validation_failed")
    if mode != "read_only":
        raise ACEError("canon retrieval/derivation/conflict resolution is read-only", code="input_validation_failed")

    evidence_refs = context.get("evidence_refs")
    if not isinstance(evidence_refs, list) or not evidence_refs:
        raise ACEError("canon resolution requires non-empty context.evidence_refs", code="input_validation_failed")
    normalized_refs: list[str] = []
    for item in evidence_refs:
        if not isinstance(item, str) or not item.strip():
            raise ACEError("evidence_refs must contain non-empty strings", code="input_validation_failed")
        normalized_refs.append(_safe_rel_path(item.strip()).as_posix())
    normalized_refs = list(dict.fromkeys(normalized_refs))

    claim_path = claim_path or str(context.get("claim_path") or field_path)
    if not isinstance(claim_path, str) or not claim_path.strip():
        raise ACEError("claim_path must be a non-empty dotted path", code="input_validation_failed")
    if not isinstance(certainty_path, str) or not certainty_path.strip():
        raise ACEError("certainty_path must be a non-empty dotted path", code="input_validation_failed")
    if derivation_rule is not None and derivation_rule not in ALLOWED_DERIVATION_RULES:
        raise ACEError(
            f"unsupported derivation_rule {derivation_rule!r}; allowed={sorted(ALLOWED_DERIVATION_RULES)}",
            code="input_validation_failed",
        )

    canonical_values = context.get("canonical_certainty_values", list(DEFAULT_CANON_CERTAINTIES))
    if not isinstance(canonical_values, list) or not canonical_values or any(
        not isinstance(item, str) or not item for item in canonical_values
    ):
        raise ACEError("canonical_certainty_values must be a non-empty string array", code="input_validation_failed")

    layers = context.get("layers", ["L1"])
    if not isinstance(layers, list) or not layers:
        raise ACEError("context.layers must be a non-empty array", code="input_validation_failed")

    baselines = repository_baselines(root)
    query_material = {
        "question": question.strip(),
        "subject_ref": subject_ref,
        "field_path": field_path,
        "claim_path": claim_path,
        "certainty_path": certainty_path,
        "evidence_refs": normalized_refs,
        "canonical_certainty_values": canonical_values,
        "derivation_rule": derivation_rule,
        "baselines": baselines,
    }
    suffix = semantic_sha256(query_material)[:20]
    requirements = [
        {
            "requirement_id": "ace.semantic.canon.authoritative_evidence",
            "semantic_type": "committed_canonical_evidence",
            "description": "Resolve the requested field only from explicitly scoped committed CanonRec evidence.",
            "required": True,
            "accepts_state_derived": False,
            "accepts_connective_rendering": False,
            "acceptable_origins": ["retrieved", "deterministic_derivation"],
            "minimum_evidence": ["canonrec_commit_baseline", "source_file_hash", "claim_path"],
        },
        {
            "requirement_id": "ace.semantic.canon.conflict_integrity",
            "semantic_type": "mutually_exclusive_claim_detection",
            "description": "Do not choose among incompatible committed canonical scalar claims without an authorized rule.",
            "required": True,
            "accepts_state_derived": False,
            "accepts_connective_rendering": False,
            "acceptable_origins": ["retrieved", "deterministic_derivation"],
            "minimum_evidence": ["all_scoped_canonical_claims"],
        },
    ]
    preferred = [RETRIEVAL_CAPABILITY]
    if derivation_rule is not None:
        preferred.append(DERIVATION_CAPABILITY)

    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "ace_query_envelope",
        "query_id": f"ace.query.canon.{suffix}",
        "created_at": utc_now(),
        "requester": {
            "kind": requester_kind,
            "requester_id": requester_id,
            "session_ref": session_ref,
        },
        "question": question.strip(),
        "query_kind": "derive" if derivation_rule else "retrieve",
        "scope": {
            "repositories": ["CanonRec"],
            "layers": layers,
            "target_repository": None,
            "target_paths": [],
            "temporal_basis": "explicit_commit_set",
        },
        "baselines": baselines,
        "subject": {
            "subject_ref": subject_ref,
            "entity_type": "canon_fact",
            "existence_status": "known",
            "contextual_refs": normalized_refs,
            "context": {
                **dict(context),
                "evidence_refs": normalized_refs,
                "field_path": field_path,
                "claim_path": claim_path,
                "certainty_path": certainty_path,
                "canonical_certainty_values": canonical_values,
                "derivation_rule": derivation_rule,
            },
        },
        "requested_outputs": [
            {
                "field_path": field_path,
                "required": True,
                "preferred_capability_refs": preferred,
                "description": "Canonical value, deterministic derivation, or explicit true-conflict determination.",
            }
        ],
        "answer_contract": {
            "compiler_version": "ace-answer-contract-canon-resolution-0.3.0",
            "interpretation_basis": [
                "query:canon_resolution",
                "evidence:explicit_canonrec_paths",
                f"claim_path:{claim_path}",
                f"derivation_rule:{derivation_rule or 'none'}",
            ],
            "coverage_policy": "all_mandatory_semantics_satisfied",
            "requirements": requirements,
        },
        "generation_policy": {
            "canonical_completion_allowed": False,
            "constitutive_simulation_allowed": False,
            "analytical_simulation_allowed": False,
            "prefer_existing_specialists": True,
            "connective_synthesis_policy": "disabled",
            "deterministic_required": True,
            "stable_seed": None,
            "reserved_decision_policy_ref": CONFLICT_POLICY_REF,
        },
        "execution_policy": {
            "mode": "read_only",
            "delegation_policy_ref": None,
            "allowed_side_effects": [],
            "budgets": {
                "max_tool_calls": max(2, len(normalized_refs) + 1),
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


def _assert_query(query: Mapping[str, Any], root: Path) -> None:
    if query.get("record_type") != "ace_query_envelope" or query.get("schema_version") != SCHEMA_VERSION:
        raise ACEError("unsupported ACE query envelope", code="input_validation_failed")
    subject = query.get("subject", {})
    if subject.get("entity_type") != "canon_fact" or query.get("query_kind") not in {"retrieve", "derive"}:
        raise ACEError("canon resolver requires retrieve/derive canon_fact query", code="input_validation_failed")
    if query.get("execution_policy", {}).get("mode") != "read_only":
        raise ACEError("canon resolver is read-only", code="input_validation_failed")
    if query.get("generation_policy", {}).get("prefer_existing_specialists") is not True:
        raise ACEError("canon resolution requires specialist-first routing", code="input_validation_failed")
    if query.get("generation_policy", {}).get("canonical_completion_allowed") is not False:
        raise ACEError("canon resolution cannot generate missing facts", code="input_validation_failed")

    current = repository_baselines(root)
    expected = {(item["repository"], item["commit_sha"]) for item in query.get("baselines", [])}
    observed = {(item["repository"], item["commit_sha"]) for item in current}
    if expected != observed:
        raise ACEError(
            "Query baseline no longer matches the registered repository set; recompile before execution",
            code="registry_baseline_advanced",
        )


def _load_claims(query: Mapping[str, Any], root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    context = query["subject"]["context"]
    claim_path = str(context["claim_path"])
    certainty_path = str(context["certainty_path"])
    canonical_values = {str(item) for item in context["canonical_certainty_values"]}
    canon_root = (root / CANONREC_REL).resolve()
    claims: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for ref in context["evidence_refs"]:
        rel = _safe_rel_path(str(ref))
        path = (canon_root / rel).resolve()
        if path == canon_root or canon_root not in path.parents:
            raise ACEError("CanonRec evidence path escapes repository", code="target_unavailable")
        if not path.is_file():
            raise ACEError(f"CanonRec evidence is missing: {rel.as_posix()}", code="target_unavailable")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ACEError(
                f"CanonRec evidence is not readable JSON: {rel.as_posix()}",
                code="input_validation_failed",
            ) from exc
        try:
            value = _dot_get(payload, claim_path)
        except KeyError:
            skipped.append({"source_ref": rel.as_posix(), "reason": f"missing claim_path {claim_path}"})
            continue
        try:
            certainty = str(_dot_get(payload, certainty_path))
        except KeyError:
            skipped.append({"source_ref": rel.as_posix(), "reason": f"missing certainty_path {certainty_path}"})
            continue
        claim = {
            "claim_ref": f"CanonRec:{rel.as_posix()}#{claim_path}",
            "source_ref": rel.as_posix(),
            "source_sha256": file_sha256(path),
            "claim_path": claim_path,
            "certainty_path": certainty_path,
            "certainty": certainty,
            "value": value,
            "value_sha256": semantic_sha256(value),
            "canonical": certainty in canonical_values,
        }
        claims.append(claim)
    return claims, skipped


def _unique_claim_values(claims: list[dict[str, Any]]) -> list[Any]:
    by_digest: dict[str, Any] = {}
    for claim in claims:
        by_digest.setdefault(str(claim["value_sha256"]), claim["value"])
    return [by_digest[key] for key in sorted(by_digest)]


def _derive(rule: str, claims: list[dict[str, Any]]) -> Any:
    if rule != "sorted_unique_union":
        raise ACEError(f"unsupported derivation rule: {rule}", code="input_validation_failed")
    if not claims or any(not isinstance(claim["value"], list) for claim in claims):
        raise ACEError(
            "sorted_unique_union requires one or more canonical list-valued claims",
            code="semantic_coverage_incomplete",
        )
    values: dict[str, Any] = {}
    for claim in claims:
        for item in claim["value"]:
            values.setdefault(semantic_sha256(item), item)
    return [values[key] for key in sorted(values, key=lambda digest: canonical_json_bytes(values[digest]))]


def _plan_step(
    capability: Mapping[str, Any],
    suffix: str,
    *,
    repository_sha: str,
    status: str,
    depends_on: list[str],
    consumes: list[str],
    produces: list[str],
    receipt_ref: str,
    output: Any,
) -> dict[str, Any]:
    digest = semantic_sha256(output)
    return {
        "step_id": f"ace.step.canon.{suffix}",
        "capability_id": capability["capability_id"],
        "status": status,
        "depends_on": depends_on,
        "consumes": consumes,
        "produces": produces,
        "tool_run_id": f"ace-run-canon-{suffix}",
        "run_receipt_ref": receipt_ref,
        "manifest_sha256": capability["manifest_sha256"],
        "repository_sha": repository_sha,
        "seed": None,
        "duration_ms": 0.0,
        "output_sha256": digest,
        "semantic_output_sha256": digest,
        "artifact_output_sha256": digest,
        "volatile_output_fields": [],
        "tool_native_statuses": {},
        "side_effects_observed": [],
    }


def resolve_canon_query(
    query: Mapping[str, Any],
    output_dir: Path,
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Resolve one read-only canonical fact request into an ACE terminal state."""

    started = time.perf_counter()
    _assert_query(query, root)
    output = _safe_output_path(output_dir, root)
    output.parent.mkdir(parents=True, exist_ok=True)
    transaction_root = Path(tempfile.mkdtemp(prefix=".ace-canon-resolution-", dir=output.parent))
    try:
        write_json(transaction_root / "query_envelope.json", query)
        index = build_capability_index(root)
        write_json(transaction_root / "capability_index.json", index)
        capabilities = {item["capability_id"]: item for item in index["capabilities"]}
        if RETRIEVAL_CAPABILITY not in capabilities:
            raise ACEError("CanonRec retrieval capability is not indexed", code="invalid_manifest")
        retrieval_cap = capabilities[RETRIEVAL_CAPABILITY]
        if retrieval_cap.get("lifecycle") != "active":
            raise ACEError("CanonRec retrieval capability is unavailable", code="tool_unavailable")
        derivation_cap = capabilities.get(DERIVATION_CAPABILITY)

        heads = {item["repository"]: item["commit_sha"] for item in index["baselines"]}
        claims, skipped = _load_claims(query, root)
        canonical_claims = [claim for claim in claims if claim["canonical"]]
        evidence = {
            "subject_ref": query["subject"]["subject_ref"],
            "field_path": query["subject"]["context"]["field_path"],
            "claims": claims,
            "canonical_claim_count": len(canonical_claims),
            "skipped_sources": skipped,
        }
        write_json(transaction_root / "evidence/canon_claims.json", evidence)

        field_path = str(query["subject"]["context"]["field_path"])
        derivation_rule = query["subject"]["context"].get("derivation_rule")
        conflicts: list[dict[str, Any]] = []
        blockers: list[dict[str, Any]] = []
        answer_value: Any = None
        origin = "retrieved"
        producers = [RETRIEVAL_CAPABILITY]
        selection_basis = ["specialist_first", "explicit_canonrec_evidence", "read_only"]
        overall_status = "complete"
        validation_status = "pass"

        if not canonical_claims:
            status = "EXECUTION_BLOCKED"
            overall_status = "incomplete"
            validation_status = "blocked"
            blockers.append(
                {
                    "blocker_id": f"ace.blocker.canon.no-authoritative-claim.{semantic_sha256(query['query_id'])[:12]}",
                    "kind": "semantic_coverage_incomplete",
                    "capability_ref": RETRIEVAL_CAPABILITY,
                    "reason": "The explicitly scoped evidence set contains no claim with an accepted canonical certainty.",
                    "recovery_action": "Route the unresolved field into the appropriate ACE completion/generation capability; do not invent a retrieved answer.",
                }
            )
            summary = "ACE found no authoritative committed claim for the requested field in the scoped evidence set."
        elif derivation_rule is not None:
            if derivation_cap is None or derivation_cap.get("lifecycle") != "active":
                raise ACEError("CanonRec derivation capability is unavailable", code="tool_unavailable")
            answer_value = _derive(str(derivation_rule), canonical_claims)
            status = "DERIVED_CANON"
            origin = "deterministic_derivation"
            producers.append(DERIVATION_CAPABILITY)
            selection_basis.extend(["allowlisted_derivation_rule", str(derivation_rule)])
            summary = (
                f"ACE deterministically derived {field_path} from {len(canonical_claims)} committed canonical claim(s) "
                f"using {derivation_rule}; no repository mutation occurred."
            )
        else:
            unique_values = _unique_claim_values(canonical_claims)
            if len(unique_values) == 1:
                answer_value = unique_values[0]
                status = "RETRIEVED_CANON"
                summary = (
                    f"ACE retrieved one unambiguous committed canonical value for {field_path} from "
                    f"{len(canonical_claims)} supporting claim(s); no repository mutation occurred."
                )
            else:
                status = "TRUE_CONFLICT"
                overall_status = "incomplete"
                selection_basis.append("fail_closed_on_mutually_exclusive_committed_claims")
                conflict_id = f"ace.conflict.canon.{semantic_sha256({'query': query['query_id'], 'claims': canonical_claims})[:16]}"
                conflicts.append(
                    {
                        "conflict_id": conflict_id,
                        "kind": "mutually_exclusive_committed_claims",
                        "claim_refs": [str(claim["claim_ref"]) for claim in canonical_claims],
                        "source_refs": [str(claim["source_ref"]) for claim in canonical_claims],
                        "reason": (
                            f"The scoped CanonRec evidence contains {len(unique_values)} mutually exclusive committed values "
                            f"for scalar field {field_path}; ACE has no authorized rule that selects a winner."
                        ),
                        "minimal_decision": (
                            "Reconcile or revise the conflicting committed claims, or provide an explicit authorized deterministic "
                            "selection/derivation rule."
                        ),
                    }
                )
                summary = (
                    f"ACE detected a true canonical conflict for {field_path}: committed authoritative claims disagree, "
                    "so no value was selected."
                )

        source_refs = [str(claim["source_ref"]) for claim in canonical_claims]
        answer = {
            "summary": summary,
            "fields": [
                {
                    "field_path": field_path,
                    "value": answer_value,
                    "origin": origin,
                    "producer_refs": producers,
                    "source_refs": source_refs,
                    "run_receipt_refs": ["evidence/canon_claims.json"],
                    "constraint_refs": [
                        DERIVATION_POLICY_REF if status == "DERIVED_CANON" else CONFLICT_POLICY_REF
                    ],
                    "canon_target_ref": None,
                }
            ],
            "no_prior_record": not canonical_claims,
            "supersedes_determination_refs": [],
        }

        retrieval_step = _plan_step(
            retrieval_cap,
            "retrieve",
            repository_sha=heads[retrieval_cap["repository"]],
            status="succeeded",
            depends_on=[],
            consumes=["query.subject.context.evidence_refs"],
            produces=["evidence/canon_claims.json"],
            receipt_ref="evidence/canon_claims.json",
            output=evidence,
        )
        steps = [retrieval_step]
        if status == "DERIVED_CANON" and derivation_cap is not None:
            steps.append(
                _plan_step(
                    derivation_cap,
                    "derive",
                    repository_sha=heads[derivation_cap["repository"]],
                    status="succeeded",
                    depends_on=[retrieval_step["step_id"]],
                    consumes=["evidence/canon_claims.json"],
                    produces=[field_path],
                    receipt_ref="receipts/derivation.json",
                    output={"rule": derivation_rule, "value": answer_value},
                )
            )
            write_json(
                transaction_root / "receipts/derivation.json",
                {
                    "policy_ref": DERIVATION_POLICY_REF,
                    "rule": derivation_rule,
                    "input_claim_refs": [claim["claim_ref"] for claim in canonical_claims],
                    "result": answer_value,
                    "result_sha256": semantic_sha256(answer_value),
                },
            )
        if status == "TRUE_CONFLICT":
            write_json(transaction_root / "receipts/conflict.json", conflicts[0])

        coverage = [
            {
                "requirement_id": "ace.semantic.canon.authoritative_evidence",
                "status": "satisfied" if canonical_claims else "missing",
                "field_refs": [field_path],
                "producer_refs": [RETRIEVAL_CAPABILITY],
                "reason": (
                    "At least one accepted committed canonical claim was found."
                    if canonical_claims
                    else "No accepted canonical claim exists in the scoped evidence set."
                ),
            },
            {
                "requirement_id": "ace.semantic.canon.conflict_integrity",
                "status": "satisfied",
                "field_refs": [field_path],
                "producer_refs": producers,
                "reason": (
                    "Mutually exclusive authoritative values were surfaced as TRUE_CONFLICT without selecting a winner."
                    if status == "TRUE_CONFLICT"
                    else "No unresolved mutually exclusive authoritative scalar claim was silently selected."
                ),
            },
        ]
        validation_gates = [
            {
                "gate_id": "canon_evidence_scope",
                "status": "pass",
                "validator_ref": "aurora_ace.validation.explicit_canonrec_scope",
                "receipt_refs": ["evidence/canon_claims.json"],
                "finding_codes": [],
                "summary": "Only explicitly declared CanonRec JSON paths were read and every source hash was recorded.",
            },
            {
                "gate_id": "canon_mutation_boundary",
                "status": "pass",
                "validator_ref": "aurora_ace.validation.read_only_no_materialization",
                "receipt_refs": ["evidence/canon_claims.json"],
                "finding_codes": [],
                "summary": "Retrieval, derivation, and conflict detection performed no repository or runtime mutation.",
            },
            {
                "gate_id": "canon_answer_coverage",
                "status": "blocked" if validation_status == "blocked" else "pass",
                "validator_ref": "aurora_ace.validation.canon_answer_contract",
                "receipt_refs": ["evidence/canon_claims.json"],
                "finding_codes": ["no_authoritative_claim"] if not canonical_claims else [],
                "summary": (
                    "No authoritative claim exists; generation/completion routing is required."
                    if not canonical_claims
                    else "The terminal state accounts for every accepted canonical claim in the scoped evidence set."
                ),
            },
        ]

        canon_head = heads["CanonRec"]
        projection_payload = {
            "claims": canonical_claims,
            "skipped": skipped,
            "field_path": field_path,
        }
        projection = {
            "projection_id": f"ace.projection.canon.claims.{semantic_sha256(projection_payload)[:16]}",
            "projection_type": "raw_evidence_index",
            "source_repository": "CanonRec",
            "source_commit_sha": canon_head,
            "source_semantic_sha256": semantic_sha256(projection_payload),
            "transform_id": "ace.transform.explicit_canon_claim_projection",
            "transform_version": CANON_RESOLUTION_VERSION,
            "projection_sha256": semantic_sha256(projection_payload),
            "source_member_count": len(claims) + len(skipped),
            "projected_member_count": len(canonical_claims),
            "collapsed_row_count": max(0, len(canonical_claims) - len(_unique_claim_values(canonical_claims))),
            "unresolved_relation_count": len(conflicts),
            "membership_receipt_ref": "evidence/canon_claims.json",
        }
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
            "determination_id": f"ace.determination.canon.{semantic_sha256({'query': query['query_id'], 'status': status, 'answer': answer_semantic, 'conflicts': conflicts})[:20]}",
            "query_id": query["query_id"],
            "created_at": utc_now(),
            "engine": {
                "engine_id": "aurora_ace",
                "engine_version": ENGINE_VERSION,
                "contract_ref": CONTRACT_REF,
                "execution_mode": "read_only",
            },
            "status": status,
            "simulation_mode": "not_applicable",
            "baselines": baselines,
            "subject_refs": [str(query["subject"]["subject_ref"])],
            "answer_contract": {
                "compiler_version": query["answer_contract"]["compiler_version"],
                "overall_status": overall_status,
                "coverage": coverage,
            },
            "projections": [projection],
            "transactions": [],
            "answer": answer,
            "plan": {
                "plan_id": f"ace.plan.canon.{semantic_sha256(query['query_id'])[:16]}",
                "selection_basis": selection_basis,
                "rejected_capability_refs": [],
                "steps": steps,
            },
            "validation": {
                "overall_status": validation_status,
                "gates": validation_gates,
            },
            "conflicts": conflicts,
            "blockers": blockers,
            "materialization": {
                "status": "blocked" if status in {"TRUE_CONFLICT", "EXECUTION_BLOCKED"} else "not_required",
                "target_repository": None,
                "target_paths": [],
                "commit_sha": None,
                "gate_policy_ref": CONFLICT_POLICY_REF if status == "TRUE_CONFLICT" else None,
                "commit_ready_packet_ref": None,
            },
            "integrity": {
                "query_sha256": semantic_sha256(query),
                "capability_manifest_sha256s": sorted(
                    {
                        retrieval_cap["manifest_sha256"],
                        *(
                            [derivation_cap["manifest_sha256"]]
                            if status == "DERIVED_CANON" and derivation_cap is not None
                            else []
                        ),
                    }
                ),
                "answer_sha256": semantic_sha256(answer),
                "semantic_answer_sha256": semantic_sha256(answer_semantic),
                "artifact_sha256s": [
                    file_sha256(transaction_root / "query_envelope.json"),
                    file_sha256(transaction_root / "capability_index.json"),
                    file_sha256(transaction_root / "evidence/canon_claims.json"),
                ],
                "semantic_digest_policy_ref": "ace.policy.semantic-digest.exclude-volatile-v1",
                "prior_determination_digest": None,
            },
            "replay": {
                "replayable": True,
                "deterministic": True,
                "replay_command": "python3 tools/aurora_ace.py resolve --query query_envelope.json --out <new-output-directory>",
                "required_artifact_refs": ["query_envelope.json", "capability_index.json", "evidence/canon_claims.json"],
                "non_replayable_reasons": [],
            },
        }
        write_json(transaction_root / "determination_receipt.json", receipt)
        write_json(
            transaction_root / "receipts/execution_summary.json",
            {
                "engine": "aurora_ace",
                "canon_resolution_version": CANON_RESOLUTION_VERSION,
                "status": status,
                "duration_ms": round((time.perf_counter() - started) * 1000, 3),
                "canon_mutation": False,
                "runtime_mutation": False,
                "experiment_advanced": False,
            },
        )
        artifact_index = {
            path.relative_to(transaction_root).as_posix(): file_sha256(path)
            for path in sorted(transaction_root.rglob("*"))
            if path.is_file()
        }
        write_json(transaction_root / "artifact_index.json", artifact_index)
        os.replace(transaction_root, output)
        return receipt
    except Exception:
        shutil.rmtree(transaction_root, ignore_errors=True)
        raise

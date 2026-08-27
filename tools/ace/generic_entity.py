"""Generic native L2 entity completion and atomic CanonRec publication for ACE.

Characters retain CharForge's richer multi-artifact serializer and L1 facility
bindings retain their dedicated materializer. Every other currently canonical
L2 entity kind can use this native flat-record path, validated by the existing
Aurora Canon Reconciler rather than by a new ACE-only schema.
"""

from __future__ import annotations

import copy
import json
import os
import re
import shutil
import subprocess
import sys
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
    file_sha256,
    repository_baselines,
    semantic_sha256,
    strip_volatile_fields,
    utc_now,
    validate_json_schema,
    write_json,
)
from .ledger import append_determination
from .materialize import (
    AUTHORITY_MODES,
    SUPPORTED_TARGET_REPOSITORY,
    _assert_clean_feature_branch,
    _assert_commit_ready,
    _canonrec_baseline,
    _git,
    _validate_receipt,
    _write_json_atomic,
)

GENERIC_ENTITY_VERSION = "0.11.0"
GENERIC_ENTITY_POLICY_REF = "ace.policy.l2.generic-native-entity-completion.v1"
GENERIC_MATERIALIZATION_POLICY_REF = "ace.policy.materialization.generic-native-owner-or-delegated.v1"
GENERIC_RESOLVER_CAPABILITY = "ace.capability.invoke.entity.complete"
GENERIC_MATERIALIZER_CAPABILITY = "ace.capability.canonrec.materialize.generic_entity"
GENERIC_TARGET_ROOT = Path("canon/L2/entities")
VALIDATOR_REL = Path("skills/aurora-canon-reconciler/scripts/validate_entity.py")
DETERMINATION_SCHEMA_REL = Path("catalog/schemas/aurora_ace_determination_receipt.schema.json")

CANONICAL_L2_KINDS = frozenset(
    {
        "location", "ship", "fleet", "anomaly", "megafauna", "facility",
        "domain", "polity", "species", "character", "organization",
        "mobile_asset", "ship_class", "equipment", "place", "conflict",
        "event", "report",
    }
)
GENERIC_L2_KINDS = CANONICAL_L2_KINDS - {"character"}

NAME_LEXICON = {
    "location": (["Aster", "Cinder", "Helix", "Meridian", "Orison"], ["Reach", "Haven", "Basin", "Crossing", "March"]),
    "ship": (["Quiet", "Resolute", "Far", "Silver", "Patient"], ["Horizon", "Vector", "Lantern", "Promise", "Current"]),
    "fleet": (["Auric", "Sentinel", "Meridian", "Vanguard", "Concord"], ["Flotilla", "Group", "Wing", "Formation", "Command"]),
    "anomaly": (["Violet", "Silent", "Fractal", "Echo", "Glass"], ["Nexus", "Veil", "Fold", "Rift", "Bloom"]),
    "megafauna": (["Star", "Void", "Luminous", "Deep", "Crown"], ["Leviathan", "Ray", "Drifter", "Whale", "Grazer"]),
    "facility": (["Aster", "Meridian", "Kepler", "Orion", "Concord"], ["Station", "Relay", "Depot", "Array", "Hub"]),
    "domain": (["Outer", "Shrouded", "Harmonic", "Emergent", "Ancient"], ["Domain", "Region", "Reach", "Zone", "Expanse"]),
    "polity": (["Aster", "Meridian", "Concord", "Sable", "Helian"], ["Compact", "Assembly", "Union", "Council", "League"]),
    "species": (["Ael", "Vor", "Sera", "Tal", "Iri"], ["ari", "eth", "uun", "ori", "ai"]),
    "organization": (["Aster", "Meridian", "Concord", "Frontier", "Helix"], ["Collective", "Institute", "Consortium", "Guild", "Assembly"]),
    "mobile_asset": (["Quiet", "Resolute", "Far", "Silver", "Patient"], ["Horizon", "Vector", "Lantern", "Promise", "Current"]),
    "ship_class": (["Aurora", "Sentinel", "Meridian", "Concord", "Vanguard"], ["Class", "Pattern", "Series", "Frame", "Line"]),
    "equipment": (["Aster", "Helix", "Orion", "Vector", "Concord"], ["Array", "Suite", "Module", "Rig", "System"]),
    "place": (["Cinder", "Aster", "Orison", "Meridian", "Glass"], ["Reach", "Haven", "Crossing", "Field", "March"]),
    "conflict": (["Broken", "Silent", "Crimson", "Outer", "Fractured"], ["Accord", "Front", "Crisis", "Schism", "War"]),
    "event": (["First", "Quiet", "Meridian", "Concord", "Turning"], ["Contact", "Passage", "Convergence", "Accord", "Transit"]),
    "report": (["Meridian", "Frontier", "Continuity", "Survey", "Canon"], ["Report", "Assessment", "Record", "Review", "Dossier"]),
}


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_") or "entity"


def _generated_name(kind: str, seed: int | str, context: Mapping[str, Any]) -> str:
    digest = semantic_sha256({"kind": kind, "seed": seed, "context": dict(context)})
    left, right = NAME_LEXICON[kind]
    a = int(digest[:8], 16) % len(left)
    b = int(digest[8:16], 16) % len(right)
    if kind == "species":
        return f"{left[a]}{right[b]}"
    return f"{left[a]} {right[b]}"


def _validate_context(kind: str, context: Mapping[str, Any]) -> None:
    if kind not in GENERIC_L2_KINDS:
        if kind == "character":
            raise ACEError("character generation must use the registered CharForge specialist path", code="input_validation_failed")
        raise ACEError(f"unsupported CanonRec L2 entity kind: {kind}", code="input_validation_failed")
    if not isinstance(context, Mapping):
        raise ACEError("generic entity context must be an object", code="input_validation_failed")
    aliases = context.get("aliases", [])
    if not isinstance(aliases, list) or any(not isinstance(item, str) or not item.strip() for item in aliases):
        raise ACEError("generic entity aliases must be non-empty strings", code="input_validation_failed")
    source_refs = context.get("source_refs", [])
    if not isinstance(source_refs, list) or any(not isinstance(item, str) or not item.strip() for item in source_refs):
        raise ACEError("generic entity source_refs must be non-empty strings", code="input_validation_failed")
    fields = context.get("canonical_fields", {})
    if not isinstance(fields, Mapping):
        raise ACEError("generic entity canonical_fields must be an object", code="input_validation_failed")


def compile_generic_entity_query(
    question: str,
    entity_kind: str,
    context: Mapping[str, Any],
    *,
    seed: int | str = 808,
    mode: str = "commit_ready",
    requester_kind: str = "user",
    requester_id: str = "ORION.ROLE.PILOT",
    session_ref: str | None = None,
    root: Path = ROOT,
) -> dict[str, Any]:
    if not isinstance(question, str) or not question.strip():
        raise ACEError("question must not be empty", code="input_validation_failed")
    kind = str(entity_kind).strip().casefold()
    _validate_context(kind, context)
    if mode not in {"plan_only", "commit_ready"}:
        raise ACEError("generic entity completion supports plan_only and commit_ready", code="input_validation_failed")
    name = str(context.get("name") or context.get("canonical_name") or _generated_name(kind, seed, context)).strip()
    identity_digest = semantic_sha256({"kind": kind, "name": name, "seed": seed, "context": dict(context)})
    entity_id = str(context.get("entity_id") or f"{kind}_{_slug(name)}_{identity_digest[:8]}")
    if re.fullmatch(r"[a-z0-9][a-z0-9_-]{2,127}", entity_id) is None:
        raise ACEError("generic entity_id must be a safe lowercase canonical identifier", code="input_validation_failed")
    target = (GENERIC_TARGET_ROOT / f"{entity_id}.json").as_posix()
    query_suffix = semantic_sha256({"question": question.strip(), "kind": kind, "entity_id": entity_id, "context": dict(context), "seed": seed})[:20]
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "ace_query_envelope",
        "query_id": f"ace.query.entity.{query_suffix}",
        "created_at": utc_now(),
        "requester": {"kind": requester_kind, "requester_id": requester_id, "session_ref": session_ref},
        "question": question.strip(),
        "query_kind": "complete",
        "scope": {
            "repositories": ["root", "CanonRec"],
            "layers": ["L2"],
            "target_repository": "CanonRec",
            "target_paths": [target],
            "temporal_basis": "explicit_commit_set",
        },
        "baselines": repository_baselines(root),
        "subject": {
            "subject_ref": entity_id,
            "entity_type": kind,
            "existence_status": "unresolved",
            "contextual_refs": list(context.get("source_refs", [])),
            "context": {**dict(context), "name": name, "entity_id": entity_id},
        },
        "requested_outputs": [
            {
                "field_path": "entity.record",
                "required": True,
                "preferred_capability_refs": [GENERIC_RESOLVER_CAPABILITY],
                "description": f"Native CanonRec L2 {kind} entity record.",
            }
        ],
        "answer_contract": {
            "compiler_version": "ace-answer-contract-generic-entity-0.11.0",
            "interpretation_basis": ["subject:new_or_existing_l2_entity", f"entity_kind:{kind}", "native_canonrec_record"],
            "coverage_policy": "all_mandatory_semantics_satisfied",
            "requirements": [
                {
                    "requirement_id": "ace.semantic.entity.native_record",
                    "semantic_type": "canonrec_l2_entity_record",
                    "description": "Produce one validator-clean native CanonRec L2 entity record while preserving specialist-first routing.",
                    "required": True,
                    "accepts_state_derived": True,
                    "accepts_connective_rendering": True,
                    "acceptable_origins": ["retrieved", "deterministic_derivation", "connective_synthesis"],
                    "minimum_evidence": ["entity_kind", "identity", "provenance", "canon_reconciler_validation"],
                }
            ],
        },
        "generation_policy": {
            "canonical_completion_allowed": True,
            "constitutive_simulation_allowed": False,
            "analytical_simulation_allowed": False,
            "prefer_existing_specialists": True,
            "connective_synthesis_policy": "registered_generic_native_policy",
            "deterministic_required": True,
            "stable_seed": seed,
            "reserved_decision_policy_ref": "ace.policy.reserved-decisions.v1",
        },
        "execution_policy": {
            "mode": mode,
            "delegation_policy_ref": "ace.policy.delegated-routine-generic-entity-completion.v1",
            "allowed_side_effects": [] if mode == "plan_only" else ["write_transaction_workspace"],
            "budgets": {"max_tool_calls": 6, "max_new_entities": 1, "max_wall_seconds": 20, "max_output_bytes": 524288},
        },
        "response_policy": {
            "include_human_answer": True,
            "include_execution_plan": True,
            "include_field_provenance": True,
            "include_replay_command": True,
        },
    }


def _candidate_from_query(query: Mapping[str, Any]) -> dict[str, Any]:
    subject = query["subject"]
    context = dict(subject["context"])
    kind = str(subject["entity_type"])
    _validate_context(kind, context)
    name = str(context["name"]).strip()
    source_refs = list(context.get("source_refs", [])) or [f"ACE:{query['query_id']}"]
    candidate: dict[str, Any] = {
        "entity_id": str(context["entity_id"]),
        "name": name,
        "aliases": list(context.get("aliases", [])),
        "entity_kind": kind,
        "certainty": "CANON_PROMOTE",
        "doc_sources": source_refs,
        "notes": f"Constitutive ACE completion under {GENERIC_ENTITY_POLICY_REF}.",
    }
    protected = {"entity_id", "name", "aliases", "entity_kind", "certainty", "doc_sources"}
    for key, value in dict(context.get("canonical_fields", {})).items():
        if key in protected:
            raise ACEError(f"canonical_fields cannot override protected identity field {key}", code="input_validation_failed")
        candidate[str(key)] = copy.deepcopy(value)
    if kind == "location" and not any(key in candidate for key in ("location_type", "subtype")):
        candidate["location_type"] = "unknown"
    if kind == "domain" and not any(key in candidate for key in ("subtype", "location_type")):
        candidate["subtype"] = "unknown"
    if kind == "polity":
        candidate.setdefault("subtype", "active_faction")
        if not any(key in candidate for key in ("government", "government_type", "org_type")):
            candidate["government"] = "council"
    return candidate


def _validator_report(candidate: Mapping[str, Any], kind: str, *, root: Path = ROOT) -> dict[str, Any]:
    validator = root / VALIDATOR_REL
    if not validator.is_file():
        raise ACEError("Aurora Canon Reconciler validator is unavailable", code="missing_tool")
    completed = subprocess.run(
        [sys.executable, str(validator), "--json", json.dumps(candidate, sort_keys=True), "--layer", "L2", "--type", kind],
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
        cwd=root,
    )
    try:
        report = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ACEError("Aurora Canon Reconciler returned a non-JSON validation result", code="output_validation_failed") from exc
    if completed.returncode != 0:
        raise ACEError(
            f"generic entity candidate failed Canon Reconciler validation: {completed.stderr.strip() or report}",
            code="output_validation_failed",
        )
    return report


def _identity_collisions(candidate: Mapping[str, Any], canonrec: Path) -> list[str]:
    entity_id = str(candidate["entity_id"])
    names = {_slug(str(candidate["name"])), *(_slug(str(item)) for item in candidate.get("aliases", []))}
    collisions: list[str] = []
    root = canonrec / GENERIC_TARGET_ROOT
    if not root.is_dir():
        return collisions
    for path in sorted(root.rglob("*.json")):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(row, Mapping):
            continue
        if str(row.get("entity_id") or "") == entity_id:
            collisions.append(path.relative_to(canonrec).as_posix())
            continue
        row_names = {_slug(str(row.get("name") or "")), *(_slug(str(item)) for item in row.get("aliases", []) if isinstance(item, str))}
        row_names.discard("entity")
        if names & row_names:
            collisions.append(path.relative_to(canonrec).as_posix())
    return sorted(set(collisions))


def _plan_step(capability_id: str, manifest_sha: str, repository_sha: str, *, status: str, produces: list[str], consumes: list[str]) -> dict[str, Any]:
    suffix = semantic_sha256({"capability": capability_id, "produces": produces})[:12]
    return {
        "step_id": f"ace.step.generic.{suffix}",
        "capability_id": capability_id,
        "status": status,
        "depends_on": [],
        "consumes": consumes,
        "produces": produces,
        "tool_run_id": None,
        "run_receipt_ref": None,
        "manifest_sha256": manifest_sha,
        "repository_sha": repository_sha,
        "seed": None,
        "duration_ms": None,
        "output_sha256": None,
        "semantic_output_sha256": None,
        "artifact_output_sha256": None,
        "volatile_output_fields": [],
        "tool_native_statuses": {},
        "side_effects_observed": [],
    }


def resolve_generic_entity_query(query: Mapping[str, Any], output_dir: Path, *, root: Path = ROOT) -> dict[str, Any]:
    output = output_dir.expanduser().resolve()
    if output.exists():
        raise ACEError(f"output directory already exists: {output}", code="target_unavailable")
    kind = str(query.get("subject", {}).get("entity_type") or "")
    _validate_context(kind, query.get("subject", {}).get("context", {}))
    candidate = _candidate_from_query(query)
    canonrec = root / CANONREC_REL
    collisions = _identity_collisions(candidate, canonrec)
    if collisions:
        raise ACEError(
            "generic entity identity collides with committed CanonRec and must return through retrieval/reconciliation: " + ", ".join(collisions[:10]),
            code="transaction_conflict",
        )
    report = _validator_report(candidate, kind, root=root)

    transaction_root = Path(tempfile.mkdtemp(prefix=".ace-generic-", dir=output.parent if output.parent.exists() else None))
    try:
        write_json(transaction_root / "query_envelope.json", query)
        write_json(transaction_root / "candidate_entity.json", candidate)
        write_json(transaction_root / "validation/entity_validation.json", report)
        baselines = [{"repository": item["repository"], "commit_sha": item["commit_sha"], "authority_role": item["authority_role"]} for item in query["baselines"]]
        root_sha = next(item["commit_sha"] for item in baselines if item["repository"] == "root")
        canon_sha = next(item["commit_sha"] for item in baselines if item["repository"] == "CanonRec")
        target = query["scope"]["target_paths"][0]
        resolver_manifest = str(query.get("runtime_manifest_sha256") or semantic_sha256({"capability": GENERIC_RESOLVER_CAPABILITY}))
        materializer_manifest = str(query.get("materializer_manifest_sha256") or semantic_sha256({"capability": GENERIC_MATERIALIZER_CAPABILITY}))
        answer = {
            "summary": f"Generated validator-clean native L2 {kind} candidate {candidate['name']} pending canonical materialization.",
            "fields": [
                {
                    "field_path": "entity.record",
                    "value": candidate,
                    "origin": "connective_synthesis",
                    "producer_refs": [GENERIC_RESOLVER_CAPABILITY],
                    "source_refs": list(candidate["doc_sources"]),
                    "run_receipt_refs": ["validation/entity_validation.json"],
                    "constraint_refs": [GENERIC_ENTITY_POLICY_REF],
                    "canon_target_ref": f"CanonRec:{target}",
                }
            ],
            "no_prior_record": True,
            "supersedes_determination_refs": [],
        }
        answer_semantic = strip_volatile_fields(answer)
        projection_hash = semantic_sha256(candidate)
        resolver_step = _plan_step(GENERIC_RESOLVER_CAPABILITY, resolver_manifest, root_sha, status="succeeded", produces=["candidate_entity.json"], consumes=["query_envelope.json"])
        resolver_step["tool_run_id"] = f"ace-run-generic-{projection_hash[:12]}"
        resolver_step["run_receipt_ref"] = "validation/entity_validation.json"
        resolver_step["output_sha256"] = projection_hash
        resolver_step["semantic_output_sha256"] = projection_hash
        resolver_step["artifact_output_sha256"] = file_sha256(transaction_root / "candidate_entity.json")
        materialize_step = _plan_step(GENERIC_MATERIALIZER_CAPABILITY, materializer_manifest, canon_sha, status="blocked", produces=[target], consumes=["candidate_entity.json"])
        materialize_step["depends_on"] = [resolver_step["step_id"]]
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "ace_determination_receipt",
            "determination_id": f"ace.determination.entity.{semantic_sha256({'query': query['query_id'], 'candidate': candidate})[:20]}",
            "query_id": query["query_id"],
            "created_at": utc_now(),
            "engine": {"engine_id": "aurora_ace", "engine_version": ENGINE_VERSION, "contract_ref": CONTRACT_REF, "execution_mode": "commit_ready"},
            "status": "EXECUTION_BLOCKED",
            "simulation_mode": "constitutive_generation",
            "baselines": baselines,
            "subject_refs": [candidate["entity_id"]],
            "answer_contract": {
                "compiler_version": "ace-answer-contract-generic-entity-0.11.0",
                "overall_status": "complete",
                "coverage": [
                    {
                        "requirement_id": "ace.semantic.entity.native_record",
                        "status": "satisfied",
                        "field_refs": ["entity.record"],
                        "producer_refs": [GENERIC_RESOLVER_CAPABILITY],
                        "reason": "The native L2 candidate passed the existing Aurora Canon Reconciler validator.",
                    }
                ],
            },
            "projections": [
                {
                    "projection_id": f"ace.projection.entity.{projection_hash[:16]}",
                    "projection_type": "tool_input",
                    "source_repository": "root",
                    "source_commit_sha": root_sha,
                    "source_semantic_sha256": semantic_sha256(query),
                    "transform_id": "ace.generic_entity.native_record",
                    "transform_version": GENERIC_ENTITY_VERSION,
                    "projection_sha256": projection_hash,
                    "source_member_count": 1,
                    "projected_member_count": 1,
                    "collapsed_row_count": 0,
                    "unresolved_relation_count": 0,
                    "membership_receipt_ref": "validation/entity_validation.json",
                }
            ],
            "transactions": [],
            "answer": answer,
            "plan": {
                "plan_id": f"ace.plan.entity.{semantic_sha256(query['query_id'])[:16]}",
                "selection_basis": ["specialist_first", "native_canonrec_l2_record", "canon_reconciler_validation", "deterministic_completion"],
                "rejected_capability_refs": [],
                "steps": [resolver_step, materialize_step],
            },
            "validation": {
                "overall_status": "pass",
                "gates": [
                    {
                        "gate_id": "generic_entity_canon_reconciler",
                        "status": "pass",
                        "validator_ref": VALIDATOR_REL.as_posix(),
                        "receipt_refs": ["validation/entity_validation.json"],
                        "finding_codes": [],
                        "summary": "Candidate accepted by the existing Aurora Canon Reconciler L2 entity validator.",
                    }
                ],
            },
            "conflicts": [],
            "blockers": [
                {
                    "blocker_id": f"ace.blocker.entity.materialization.{semantic_sha256(candidate['entity_id'])[:12]}",
                    "kind": "materialization_authority_missing",
                    "capability_ref": GENERIC_MATERIALIZER_CAPABILITY,
                    "reason": "The generic native entity is complete but has not crossed the CanonRec persistence gate.",
                    "recovery_action": "Materialize through an authorized ACE generic-entity publication transaction.",
                }
            ],
            "materialization": {
                "status": "commit_ready",
                "target_repository": "CanonRec",
                "target_paths": [target],
                "commit_sha": None,
                "gate_policy_ref": GENERIC_MATERIALIZATION_POLICY_REF,
                "commit_ready_packet_ref": "candidate_entity.json",
            },
            "integrity": {
                "query_sha256": semantic_sha256(query),
                "capability_manifest_sha256s": [resolver_manifest, materializer_manifest],
                "answer_sha256": semantic_sha256(answer),
                "semantic_answer_sha256": semantic_sha256(answer_semantic),
                "artifact_sha256s": [file_sha256(transaction_root / "query_envelope.json"), file_sha256(transaction_root / "candidate_entity.json"), file_sha256(transaction_root / "validation/entity_validation.json")],
                "semantic_digest_policy_ref": "ace.policy.semantic-digest.exclude-volatile-v1",
                "prior_determination_digest": None,
            },
            "replay": {
                "replayable": True,
                "deterministic": True,
                "replay_command": "python3 tools/aurora_ace_entity.py resolve --query query_envelope.json --out <new-output-directory>",
                "required_artifact_refs": ["query_envelope.json", "candidate_entity.json", "validation/entity_validation.json"],
                "non_replayable_reasons": [],
            },
        }
        write_json(transaction_root / "determination_receipt.json", receipt)
        validate_json_schema(receipt, root / DETERMINATION_SCHEMA_REL)
        os.replace(transaction_root, output)
        return receipt
    except Exception:
        shutil.rmtree(transaction_root, ignore_errors=True)
        raise


def _canonical_record(candidate: Mapping[str, Any], receipt: Mapping[str, Any], authority_ref: str) -> dict[str, Any]:
    canonical = copy.deepcopy(dict(candidate))
    canonical["certainty"] = "CANON"
    canonical["ace_provenance"] = {
        "query_id": receipt["query_id"],
        "source_determination_id": receipt["determination_id"],
        "generation_policy_ref": GENERIC_ENTITY_POLICY_REF,
        "materializer_version": GENERIC_ENTITY_VERSION,
        "materialization_authority_ref": authority_ref,
    }
    return canonical


def _generic_final_receipt(original: Mapping[str, Any], *, commit_sha: str, target_path: str, target_hash: str, baseline_hash: str, authority_mode: str, authority_ref: str, elapsed_ms: float) -> dict[str, Any]:
    final = copy.deepcopy(dict(original))
    prior_id = str(original["determination_id"])
    final["determination_id"] = f"{prior_id}.materialized.{commit_sha[:12]}"
    final["created_at"] = utc_now()
    final["engine"]["execution_mode"] = authority_mode
    final["status"] = "GENERATED_CANON"
    final["answer"]["supersedes_determination_refs"] = [*final["answer"].get("supersedes_determination_refs", []), prior_id]
    final["blockers"] = []
    final["materialization"]["status"] = "committed"
    final["materialization"]["commit_sha"] = commit_sha
    final["materialization"]["gate_policy_ref"] = f"{GENERIC_MATERIALIZATION_POLICY_REF}; authority_ref={authority_ref}"
    final["transactions"] = [
        *final.get("transactions", []),
        {
            "transaction_id": f"ace.transaction.materialization.{commit_sha[:16]}",
            "kind": "materialization",
            "scope": f"CanonRec:{target_path}",
            "baseline_sha256": baseline_hash,
            "result_sha256": target_hash,
            "concurrency_policy": "optimistic_compare_and_swap",
            "revalidation_status": "pass",
            "side_effects": ["wrote_canonical_target", "created_git_commit"],
            "receipt_ref": f"CanonRec:{target_path}@{commit_sha}",
        },
    ]
    step = next((item for item in final["plan"]["steps"] if item.get("capability_id") == GENERIC_MATERIALIZER_CAPABILITY), None)
    if step is None:
        raise ACEError("generic determination plan has no materializer step", code="invalid_manifest")
    step.update(
        {
            "status": "succeeded",
            "tool_run_id": f"ace-run-generic-materialization-{commit_sha[:12]}",
            "run_receipt_ref": f"CanonRec:{target_path}@{commit_sha}",
            "duration_ms": elapsed_ms,
            "output_sha256": target_hash,
            "semantic_output_sha256": target_hash,
            "artifact_output_sha256": target_hash,
            "side_effects_observed": ["wrote_canonical_target", "created_git_commit"],
        }
    )
    final["integrity"]["prior_determination_digest"] = semantic_sha256(original)
    final["integrity"]["artifact_sha256s"] = sorted(set([*final["integrity"].get("artifact_sha256s", []), target_hash]))
    final["replay"] = {
        "replayable": False,
        "deterministic": True,
        "replay_command": None,
        "required_artifact_refs": ["determination_receipt.json", "candidate_entity.json"],
        "non_replayable_reasons": ["Git publication metadata is non-semantic; replay the prior deterministic candidate instead."],
    }
    return final


def materialize_generic_entity_packet(
    packet_dir: Path,
    target_repo: Path,
    *,
    authority_mode: str,
    authority_ref: str,
    ledger_dir: Path | None = None,
    root: Path = ROOT,
    commit_message: str | None = None,
) -> dict[str, Any]:
    if authority_mode not in AUTHORITY_MODES:
        raise ACEError(f"authority_mode must be one of {sorted(AUTHORITY_MODES)}", code="materialization_authority_missing")
    if not isinstance(authority_ref, str) or not authority_ref.strip():
        raise ACEError("generic materialization requires authority_ref", code="materialization_authority_missing")
    packet = packet_dir.expanduser().resolve()
    repo = target_repo.expanduser().resolve()
    receipt_path = packet / "determination_receipt.json"
    candidate_path = packet / "candidate_entity.json"
    if not receipt_path.is_file() or not candidate_path.is_file():
        raise ACEError("generic entity packet is incomplete", code="target_unavailable")
    receipt = _validate_receipt(receipt_path, root=root)
    _assert_commit_ready(receipt)
    _, baseline_head = _assert_clean_feature_branch(repo)
    expected_head = _canonrec_baseline(receipt)
    if baseline_head != expected_head:
        raise ACEError(f"CanonRec baseline advanced ({expected_head} -> {baseline_head}); recompile before publication", code="registry_baseline_advanced")
    paths = receipt["materialization"]["target_paths"]
    if receipt["materialization"]["target_repository"] != SUPPORTED_TARGET_REPOSITORY or len(paths) != 1:
        raise ACEError("generic entity packet must target exactly one CanonRec path", code="target_unavailable")
    target_rel = str(paths[0])
    rel = Path(target_rel)
    if rel.is_absolute() or ".." in rel.parts or rel.parent != GENERIC_TARGET_ROOT:
        raise ACEError("generic entity target must be a flat native L2 entity record", code="target_unavailable")
    target = (repo / rel).resolve()
    if target.exists():
        raise ACEError("generic entity materialization is new-entity-only; existing targets require reconciliation", code="transaction_conflict")
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    if not isinstance(candidate, Mapping) or candidate.get("entity_kind") not in GENERIC_L2_KINDS:
        raise ACEError("generic entity candidate kind is unsupported", code="input_validation_failed")
    if _identity_collisions(candidate, repo):
        raise ACEError("generic entity identity now collides with CanonRec; recompile/reconcile", code="transaction_conflict")
    _validator_report(candidate, str(candidate["entity_kind"]), root=root)
    canonical = _canonical_record(candidate, receipt, authority_ref)
    _validator_report(canonical, str(candidate["entity_kind"]), root=root)
    baseline_hash = semantic_sha256({"target": target_rel, "state": "absent"})
    append_determination(receipt, ledger_dir, root=root)
    started = time.perf_counter()
    final_sidecar = packet / "determination_receipt.materialized.json"
    try:
        _write_json_atomic(target, canonical)
        target_hash = file_sha256(target)
        _git(repo, "add", "--", target_rel)
        staged = _git(repo, "diff", "--cached", "--name-only").splitlines()
        if staged != [target_rel]:
            raise ACEError(f"generic materializer expected exactly one staged target, observed {staged}", code="runtime_failure")
        _git(
            repo,
            "-c", "user.name=Aurora ACE Materializer",
            "-c", "user.email=ace@aurora.local",
            "commit", "-m", commit_message or f"feat(canon): materialize ACE {candidate['entity_kind']} {candidate['entity_id']}",
        )
        commit_sha = _git(repo, "rev-parse", "HEAD")
        final = _generic_final_receipt(
            receipt,
            commit_sha=commit_sha,
            target_path=target_rel,
            target_hash=target_hash,
            baseline_hash=baseline_hash,
            authority_mode=authority_mode,
            authority_ref=authority_ref,
            elapsed_ms=round((time.perf_counter() - started) * 1000, 3),
        )
        validate_json_schema(final, root / DETERMINATION_SCHEMA_REL)
        _write_json_atomic(final_sidecar, final)
        append_determination(final, ledger_dir, root=root)
        return final
    except Exception:
        try:
            _git(repo, "reset", "--hard", baseline_head)
            _git(repo, "clean", "-fd", "--", target_rel)
        finally:
            try:
                final_sidecar.unlink()
            except FileNotFoundError:
                pass
        raise

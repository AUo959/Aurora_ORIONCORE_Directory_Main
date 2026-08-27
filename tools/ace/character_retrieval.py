"""Retrieval-first existing-character resolution for ACE.

This slice prevents character generation from racing ahead of committed CanonRec
identity evidence. It builds a deterministic index over canonical character
capsule identities, enriches candidate matching with committed relationship
fields, and returns either:

- ``RETRIEVED_CANON`` for one sufficiently identified existing referent;
- ``EXECUTION_BLOCKED`` with ``referent_ambiguous`` when several committed
  identities remain plausible;
- ``EXECUTION_BLOCKED`` with ``possible_existing_referent`` when relation-only
  evidence indicates an existing character but no identity anchor is strong
  enough to claim equivalence.

The module performs no CanonRec mutation and does not invoke CharForge or
NameService. Generation remains a separate downstream path used only after the
retrieval preflight finds no plausible existing referent.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import time
from dataclasses import dataclass
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
    normalize_name,
    repository_baselines,
    semantic_sha256,
    strip_volatile_fields,
    utc_now,
    write_json,
)
from .engine import _safe_output_path

CHARACTER_RETRIEVAL_VERSION = "0.4.0"
RETRIEVAL_CAPABILITY = "ace.capability.canonrec.retrieve.character"
RELATION_CAPABILITY = "ace.capability.canonrec.enrich.character_relations"
RETRIEVAL_POLICY_REF = "ace.policy.character-retrieval-first.v1"
RELATION_POLICY_REF = "ace.policy.character-relation-evidence.v1"
ACCEPTED_CERTAINTIES = frozenset({"CANON"})


@dataclass(frozen=True)
class CharacterRecord:
    canonical_id: str
    name: str
    aliases: tuple[str, ...]
    role: str | None
    faction_id: str | None
    status: str | None
    certainty: str
    location_type: str | None
    location_ref: str | None
    location_basis: str | None
    identity_ref: str
    identity_sha256: str
    traits_ref: str | None
    traits_sha256: str | None
    knowledge_ref: str | None
    knowledge_sha256: str | None

    def public_identity(self) -> dict[str, Any]:
        return {
            "canonical_id": self.canonical_id,
            "name": self.name,
            "aliases": list(self.aliases),
            "role": self.role,
            "faction_id": self.faction_id,
            "status": self.status,
            "certainty": self.certainty,
            "location_binding": {
                "type": self.location_type,
                "target_id": self.location_ref,
                "basis": self.location_basis,
            },
            "source_ref": self.identity_ref,
            "source_sha256": self.identity_sha256,
        }


def _safe_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ACEError(f"canonical character evidence is unreadable JSON: {path}", code="input_validation_failed") from exc


def _relative_to_canonrec(path: Path, canon_root: Path) -> str:
    return path.resolve().relative_to(canon_root.resolve()).as_posix()



def _capsule_for_entity(entity: dict[str, object], canon_root: Path) -> Path | None:
    capsule_ref = entity.get("capsule_ref")
    if isinstance(capsule_ref, str) and capsule_ref.strip():
        candidate = (canon_root / capsule_ref.strip() / "identity.json").resolve()
        if candidate.is_file() and canon_root in candidate.parents:
            return candidate
    for key in ("capsule_id", "entity_id"):
        value = entity.get(key)
        if isinstance(value, str) and value.strip():
            candidate = canon_root / "canon/L2/entities" / value.strip() / "capsule/identity.json"
            if candidate.is_file():
                return candidate
    return None


def _capsule_value(payload: dict[str, object], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _record_from_flat_entity(entity_path: Path, canon_root: Path) -> tuple[CharacterRecord | None, str | None]:
    payload = _load_json(entity_path)
    if not isinstance(payload, dict) or payload.get("entity_kind") != "character":
        return None, None
    canonical_id = _safe_string(payload.get("entity_id"))
    entity_name = _safe_string(payload.get("name"))
    certainty = _safe_string(payload.get("certainty"))
    if not canonical_id or not entity_name or certainty not in ACCEPTED_CERTAINTIES:
        return None, None

    capsule_path = _capsule_for_entity(payload, canon_root)
    capsule_payload: dict[str, object] = {}
    if capsule_path is not None:
        loaded = _load_json(capsule_path)
        if isinstance(loaded, dict) and _safe_string(loaded.get("certainty")) in ACCEPTED_CERTAINTIES:
            capsule_payload = loaded

    aliases: list[str] = []
    for source in (payload.get("aliases"), capsule_payload.get("aliases")):
        if isinstance(source, list):
            for item in source:
                if isinstance(item, str) and item.strip() and item.strip() not in aliases:
                    aliases.append(item.strip())

    factions = payload.get("faction_bindings", [])
    faction_id = _capsule_value(capsule_payload, "faction_id")
    if not faction_id and isinstance(factions, list):
        faction_id = next((item.strip() for item in factions if isinstance(item, str) and item.strip()), None)

    binding = capsule_payload.get("location_binding", {})
    if not isinstance(binding, dict):
        binding = {}
    location_type = _safe_string(binding.get("type")) or _safe_string(payload.get("location_type"))
    location_ref = (
        _safe_string(binding.get("target_id"))
        or _safe_string(payload.get("region_id"))
        or _safe_string(payload.get("parent_org_id"))
    )
    location_basis = _safe_string(binding.get("basis"))

    capsule_dir = capsule_path.parent if capsule_path is not None else None
    traits = capsule_dir / "traits.json" if capsule_dir is not None else None
    knowledge = capsule_dir / "knowledge.jsonl" if capsule_dir is not None else None
    entity_ref = _relative_to_canonrec(entity_path, canon_root)
    return (
        CharacterRecord(
            canonical_id=canonical_id,
            name=_capsule_value(capsule_payload, "name", "character_name") or entity_name,
            aliases=tuple(aliases),
            role=_capsule_value(capsule_payload, "role", "character_role") or _safe_string(payload.get("role")),
            faction_id=faction_id,
            status=_safe_string(payload.get("status")) or _safe_string(capsule_payload.get("status")),
            certainty=certainty,
            location_type=location_type,
            location_ref=location_ref,
            location_basis=location_basis,
            identity_ref=entity_ref,
            identity_sha256=file_sha256(entity_path),
            traits_ref=_relative_to_canonrec(traits, canon_root) if traits is not None and traits.is_file() else None,
            traits_sha256=file_sha256(traits) if traits is not None and traits.is_file() else None,
            knowledge_ref=_relative_to_canonrec(knowledge, canon_root) if knowledge is not None and knowledge.is_file() else None,
            knowledge_sha256=file_sha256(knowledge) if knowledge is not None and knowledge.is_file() else None,
        ),
        _relative_to_canonrec(capsule_path, canon_root) if capsule_path is not None else None,
    )


def _record_from_capsule(identity_path: Path, canon_root: Path) -> CharacterRecord | None:
    payload = _load_json(identity_path)
    if not isinstance(payload, dict):
        return None
    certainty = _safe_string(payload.get("certainty"))
    canonical_id = _capsule_value(payload, "canonical_id", "capsule_id")
    name = _capsule_value(payload, "name", "character_name")
    if certainty not in ACCEPTED_CERTAINTIES or not canonical_id or not name:
        return None
    binding = payload.get("location_binding", {})
    if not isinstance(binding, dict):
        binding = {}
    aliases = payload.get("aliases", [])
    if not isinstance(aliases, list):
        aliases = []
    capsule_dir = identity_path.parent
    traits = capsule_dir / "traits.json"
    knowledge = capsule_dir / "knowledge.jsonl"
    return CharacterRecord(
        canonical_id=canonical_id,
        name=name,
        aliases=tuple(item.strip() for item in aliases if isinstance(item, str) and item.strip()),
        role=_capsule_value(payload, "role", "character_role"),
        faction_id=_capsule_value(payload, "faction_id"),
        status=_safe_string(payload.get("status")),
        certainty=certainty,
        location_type=_safe_string(binding.get("type")),
        location_ref=_safe_string(binding.get("target_id")),
        location_basis=_safe_string(binding.get("basis")),
        identity_ref=_relative_to_canonrec(identity_path, canon_root),
        identity_sha256=file_sha256(identity_path),
        traits_ref=_relative_to_canonrec(traits, canon_root) if traits.is_file() else None,
        traits_sha256=file_sha256(traits) if traits.is_file() else None,
        knowledge_ref=_relative_to_canonrec(knowledge, canon_root) if knowledge.is_file() else None,
        knowledge_sha256=file_sha256(knowledge) if knowledge.is_file() else None,
    )


def _records(root: Path) -> list[CharacterRecord]:
    canon_root = (root / CANONREC_REL).resolve()
    entities_root = canon_root / "canon/L2/entities"
    registry_root = entities_root / "characters"
    records: list[CharacterRecord] = []
    seen_ids: set[str] = set()
    consumed_capsules: set[str] = set()

    if registry_root.is_dir():
        for entity_path in sorted(registry_root.glob("*.json")):
            record, capsule_ref = _record_from_flat_entity(entity_path, canon_root)
            if record is None:
                continue
            if record.canonical_id in seen_ids:
                raise ACEError(
                    f"duplicate canonical character entity id in registry: {record.canonical_id}",
                    code="projection_invalid",
                )
            records.append(record)
            seen_ids.add(record.canonical_id)
            if capsule_ref:
                consumed_capsules.add(capsule_ref)

    # Compatibility fallback for canonical capsules that have not yet been
    # bridged into the flat entity registry.
    if entities_root.is_dir():
        for identity_path in sorted(entities_root.glob("*/capsule/identity.json")):
            rel = _relative_to_canonrec(identity_path, canon_root)
            if rel in consumed_capsules:
                continue
            record = _record_from_capsule(identity_path, canon_root)
            if record is None or record.canonical_id in seen_ids:
                continue
            records.append(record)
            seen_ids.add(record.canonical_id)

    return sorted(records, key=lambda item: (item.canonical_id.casefold(), item.name.casefold()))


def build_character_index(root: Path = ROOT) -> dict[str, Any]:
    """Build the deterministic registry-complete CanonRec character index."""

    public = [item.public_identity() for item in _records(root)]
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "ace_character_identity_index",
        "index_version": CHARACTER_RETRIEVAL_VERSION,
        "record_count": len(public),
        "records": public,
        "index_sha256": semantic_sha256(public),
        "discovery_surfaces": [
            "canon/L2/entities/characters/*.json",
            "canon/L2/entities/*/capsule/identity.json",
        ],
    }


def _norm_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _identity_anchors(context: Mapping[str, Any]) -> tuple[str | None, set[str]]:
    subject_ref = _safe_string(context.get("subject_ref"))
    names: set[str] = set()
    for key in ("name", "canonical_name"):
        value = _safe_string(context.get(key))
        if value:
            names.add(normalize_name(value))
    aliases = context.get("aliases", [])
    if isinstance(aliases, list):
        names.update(normalize_name(item) for item in aliases if isinstance(item, str) and item.strip())
    names.discard("")
    return subject_ref, names


def _relation_matches(record: CharacterRecord, context: Mapping[str, Any]) -> dict[str, bool]:
    role = _safe_string(context.get("role"))
    faction = _safe_string(context.get("faction_id"))
    location_ref = _safe_string(context.get("location_ref"))
    location_type = _safe_string(context.get("location_type"))
    contextual_refs = {
        str(item).strip()
        for item in context.get("contextual_refs", [])
        if isinstance(item, str) and item.strip()
    } if isinstance(context.get("contextual_refs", []), list) else set()
    if faction:
        contextual_refs.add(faction)
    if location_ref:
        contextual_refs.add(location_ref)

    return {
        "role": bool(role and record.role and _norm_text(role) == _norm_text(record.role)),
        "faction": bool(faction and record.faction_id and faction.casefold() == record.faction_id.casefold()),
        "location_ref": bool(
            record.location_ref
            and any(record.location_ref.casefold() == ref.casefold() for ref in contextual_refs)
        ),
        "location_type": bool(
            location_type and record.location_type and location_type.casefold() == record.location_type.casefold()
        ),
    }


def discover_character_candidates(context: Mapping[str, Any], root: Path = ROOT) -> dict[str, Any]:
    """Return identity-anchored matches plus non-authoritative relation candidates."""

    subject_ref, name_anchors = _identity_anchors(context)
    direct: list[dict[str, Any]] = []
    relation_only: list[dict[str, Any]] = []
    for record in _records(root):
        candidate_names = {normalize_name(record.name), *[normalize_name(item) for item in record.aliases]}
        id_match = bool(subject_ref and subject_ref.casefold() == record.canonical_id.casefold())
        name_match = bool(name_anchors & candidate_names)
        relations = _relation_matches(record, context)
        relation_count = sum(1 for value in relations.values() if value)
        payload = {
            **record.public_identity(),
            "match": {
                "canonical_id": id_match,
                "name_or_alias": name_match,
                "relations": relations,
                "relation_match_count": relation_count,
            },
        }
        if id_match or name_match:
            direct.append(payload)
        elif relation_count >= 3:
            relation_only.append(payload)

    direct.sort(
        key=lambda item: (
            -int(item["match"]["canonical_id"]),
            -int(item["match"]["name_or_alias"]),
            -int(item["match"]["relation_match_count"]),
            str(item["canonical_id"]).casefold(),
        )
    )
    relation_only.sort(
        key=lambda item: (-int(item["match"]["relation_match_count"]), str(item["canonical_id"]).casefold())
    )
    return {
        "identity_anchor_present": bool(subject_ref or name_anchors),
        "subject_ref": subject_ref,
        "normalized_name_anchors": sorted(name_anchors),
        "direct_candidates": direct,
        "relation_only_candidates": relation_only,
        "candidate_digest": semantic_sha256({"direct": direct, "relation_only": relation_only}),
    }


def _retrieval_is_applicable(context: Mapping[str, Any], discovery: Mapping[str, Any]) -> bool:
    existence = str(context.get("existence_status", "confirmed_unrecorded"))
    if discovery["direct_candidates"] or discovery["relation_only_candidates"]:
        return True
    if discovery["identity_anchor_present"]:
        # An explicit identity/name lookup that found nothing should report that
        # fact rather than silently minting a different person.
        return existence != "confirmed_unrecorded"
    return existence in {"known", "existing", "possible_existing", "unknown"}


def compile_existing_character_query_if_applicable(
    question: str,
    context: Mapping[str, Any],
    *,
    seed: int | str,
    mode: str,
    requester_kind: str,
    requester_id: str,
    session_ref: str | None,
    root: Path,
) -> dict[str, Any] | None:
    """Return a retrieval query when existing-canon evidence must be resolved first."""

    discovery = discover_character_candidates(context, root)
    if not _retrieval_is_applicable(context, discovery):
        return None
    baselines = repository_baselines(root)
    material = {
        "question": question.strip(),
        "context": context,
        "discovery_digest": discovery["candidate_digest"],
        "baselines": baselines,
    }
    suffix = semantic_sha256(material)[:20]
    raw_contextual_refs = context.get("contextual_refs", [])
    base_contextual_refs = (
        [str(item) for item in raw_contextual_refs if str(item)]
        if isinstance(raw_contextual_refs, list)
        else []
    )
    contextual_refs = list(dict.fromkeys(
        [
            *base_contextual_refs,
            *[str(item["canonical_id"]) for item in discovery["direct_candidates"]],
            *[str(item["canonical_id"]) for item in discovery["relation_only_candidates"]],
        ]
    ))
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "ace_query_envelope",
        "query_id": f"ace.query.character.retrieve.{suffix}",
        "created_at": utc_now(),
        "requester": {
            "kind": requester_kind,
            "requester_id": requester_id,
            "session_ref": session_ref,
        },
        "question": question.strip(),
        "query_kind": "retrieve",
        "scope": {
            "repositories": ["root", "CanonRec"],
            "layers": ["L2"],
            "target_repository": None,
            "target_paths": [],
            "temporal_basis": "explicit_commit_set",
        },
        "baselines": baselines,
        "subject": {
            "subject_ref": context.get("subject_ref"),
            "entity_type": "character",
            "existence_status": "contextual_unresolved",
            "contextual_refs": contextual_refs,
            "context": {
                **dict(context),
                "retrieval_preflight": discovery,
            },
        },
        "requested_outputs": [
            {
                "field_path": "character.identity",
                "required": True,
                "preferred_capability_refs": [RETRIEVAL_CAPABILITY],
                "description": "Existing canonical identity and naming data if the referent is established.",
            },
            {
                "field_path": "character.relations",
                "required": True,
                "preferred_capability_refs": [RELATION_CAPABILITY],
                "description": "Committed role, faction, location, and contextual relation evidence used for disambiguation.",
            },
            {
                "field_path": "character.background_and_traits",
                "required": False,
                "preferred_capability_refs": [RETRIEVAL_CAPABILITY],
                "description": "Existing capsule knowledge/traits evidence where present; never generated on this path.",
            },
        ],
        "answer_contract": {
            "compiler_version": "ace-answer-contract-character-retrieval-0.4.0",
            "interpretation_basis": [
                "question:existing_character_identity",
                "retrieval:first",
                "evidence:canonrec_character_capsules",
                "relations:role_faction_location",
            ],
            "coverage_policy": "all_mandatory_semantics_satisfied",
            "requirements": [
                {
                    "requirement_id": "ace.semantic.character.existing_identity",
                    "semantic_type": "existing_character_identity",
                    "description": "Resolve a unique committed identity before any character generation is allowed.",
                    "required": True,
                    "accepts_state_derived": False,
                    "accepts_connective_rendering": False,
                    "acceptable_origins": ["retrieved"],
                    "minimum_evidence": ["canonical_identity_record", "identity_source_hash"],
                },
                {
                    "requirement_id": "ace.semantic.character.relation_disambiguation",
                    "semantic_type": "committed_relation_evidence",
                    "description": "Use role/faction/location relations to disambiguate identity anchors; never use relation-only evidence as silent identity equivalence.",
                    "required": True,
                    "accepts_state_derived": False,
                    "accepts_connective_rendering": False,
                    "acceptable_origins": ["retrieved"],
                    "minimum_evidence": ["relation_match_receipt"],
                },
            ],
        },
        "generation_policy": {
            "canonical_completion_allowed": False,
            "constitutive_simulation_allowed": False,
            "analytical_simulation_allowed": False,
            "prefer_existing_specialists": True,
            "connective_synthesis_policy": "disabled",
            "deterministic_required": True,
            "stable_seed": seed,
            "reserved_decision_policy_ref": RETRIEVAL_POLICY_REF,
        },
        "execution_policy": {
            "mode": "read_only",
            "delegation_policy_ref": None,
            "allowed_side_effects": [],
            "budgets": {
                "max_tool_calls": 4,
                "max_new_entities": 0,
                "max_wall_seconds": 20,
                "max_output_bytes": 1048576,
            },
        },
        "response_policy": {
            "include_human_answer": True,
            "include_execution_plan": True,
            "include_field_provenance": True,
            "include_replay_command": True,
        },
    }


def _load_supporting_artifacts(record: CharacterRecord, root: Path) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    canon_root = (root / CANONREC_REL).resolve()
    traits: dict[str, Any] | None = None
    knowledge: list[dict[str, Any]] = []
    if record.traits_ref:
        payload = _load_json(canon_root / record.traits_ref)
        if isinstance(payload, Mapping):
            traits = dict(payload)
    if record.knowledge_ref:
        path = canon_root / record.knowledge_ref
        try:
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if not line.strip():
                    continue
                payload = json.loads(line)
                if isinstance(payload, Mapping):
                    item = dict(payload)
                    item["source_line"] = line_number
                    knowledge.append(item)
        except (OSError, json.JSONDecodeError) as exc:
            raise ACEError(f"character knowledge evidence is unreadable: {path}", code="input_validation_failed") from exc
    return traits, knowledge


def _choose_direct_candidate(discovery: Mapping[str, Any]) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    candidates = list(discovery["direct_candidates"])
    if not candidates:
        return None, []
    id_matches = [item for item in candidates if item["match"]["canonical_id"]]
    if len(id_matches) == 1:
        return id_matches[0], candidates
    if len(id_matches) > 1:
        return None, candidates

    # Same-name/alias collisions may be resolved by committed relation evidence,
    # but only when one candidate has a strictly higher relation score and that
    # score is non-zero. A tie remains ambiguity, not TRUE_CONFLICT.
    scored = sorted(
        candidates,
        key=lambda item: (-int(item["match"]["relation_match_count"]), str(item["canonical_id"]).casefold()),
    )
    if len(scored) == 1:
        return scored[0], candidates
    top = int(scored[0]["match"]["relation_match_count"])
    second = int(scored[1]["match"]["relation_match_count"])
    if top > second and top > 0:
        return scored[0], candidates
    return None, candidates


def _record_by_id(canonical_id: str, root: Path) -> CharacterRecord:
    for record in _records(root):
        if record.canonical_id == canonical_id:
            return record
    raise ACEError("retrieved character disappeared from current baseline", code="registry_baseline_advanced")


def resolve_existing_character_query(
    query: Mapping[str, Any],
    output_dir: Path,
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Resolve a retrieval-first character query without invoking generation."""

    started = time.perf_counter()
    if query.get("record_type") != "ace_query_envelope" or query.get("schema_version") != SCHEMA_VERSION:
        raise ACEError("unsupported ACE query envelope", code="input_validation_failed")
    if query.get("query_kind") != "retrieve" or query.get("subject", {}).get("entity_type") != "character":
        raise ACEError("existing-character resolver requires retrieve character query", code="input_validation_failed")
    if query.get("execution_policy", {}).get("mode") != "read_only":
        raise ACEError("existing-character retrieval is read-only", code="input_validation_failed")
    current = repository_baselines(root)
    expected = {(item["repository"], item["commit_sha"]) for item in query.get("baselines", [])}
    observed = {(item["repository"], item["commit_sha"]) for item in current}
    if expected != observed:
        raise ACEError("query baseline advanced; recompile character retrieval", code="registry_baseline_advanced")

    output = _safe_output_path(output_dir, root)
    output.parent.mkdir(parents=True, exist_ok=True)
    transaction_root = Path(tempfile.mkdtemp(prefix=".ace-character-retrieval-", dir=output.parent))
    try:
        write_json(transaction_root / "query_envelope.json", query)
        capability_index = build_capability_index(root)
        write_json(transaction_root / "capability_index.json", capability_index)
        capabilities = {item["capability_id"]: item for item in capability_index["capabilities"]}
        for capability_id in (RETRIEVAL_CAPABILITY, RELATION_CAPABILITY):
            if capability_id not in capabilities or capabilities[capability_id]["lifecycle"] != "active":
                raise ACEError(f"character retrieval capability unavailable: {capability_id}", code="tool_unavailable")

        context = dict(query["subject"]["context"])
        context.pop("retrieval_preflight", None)
        discovery = discover_character_candidates(context, root)
        index = build_character_index(root)
        evidence = {"index": index, "discovery": discovery}
        write_json(transaction_root / "evidence/character_retrieval.json", evidence)

        selected, direct = _choose_direct_candidate(discovery)
        relation_only = list(discovery["relation_only_candidates"])
        blockers: list[dict[str, Any]] = []
        conflicts: list[dict[str, Any]] = []
        status = "EXECUTION_BLOCKED"
        overall_status = "incomplete"
        validation_status = "blocked"
        answer_fields: list[dict[str, Any]] = []
        summary: str

        if selected is not None:
            record = _record_by_id(str(selected["canonical_id"]), root)
            traits, knowledge = _load_supporting_artifacts(record, root)
            source_refs = [record.identity_ref]
            if record.traits_ref:
                source_refs.append(record.traits_ref)
            if record.knowledge_ref:
                source_refs.append(record.knowledge_ref)
            answer_value = {
                "identity": record.public_identity(),
                "relation_match": selected["match"],
                "traits": traits,
                "knowledge": knowledge,
            }
            status = "RETRIEVED_CANON"
            overall_status = "complete"
            validation_status = "pass"
            summary = (
                f"ACE resolved the existing canonical character {record.name} ({record.canonical_id}) "
                "before generation; no character was created or modified."
            )
            answer_fields = [
                {
                    "field_path": "character.identity",
                    "value": record.public_identity(),
                    "origin": "retrieved",
                    "producer_refs": [RETRIEVAL_CAPABILITY],
                    "source_refs": [record.identity_ref],
                    "run_receipt_refs": ["evidence/character_retrieval.json"],
                    "constraint_refs": [RETRIEVAL_POLICY_REF],
                    "canon_target_ref": f"CanonRec:{record.identity_ref}",
                },
                {
                    "field_path": "character.relations",
                    "value": selected["match"],
                    "origin": "retrieved",
                    "producer_refs": [RELATION_CAPABILITY],
                    "source_refs": [record.identity_ref],
                    "run_receipt_refs": ["evidence/character_retrieval.json"],
                    "constraint_refs": [RELATION_POLICY_REF],
                    "canon_target_ref": f"CanonRec:{record.identity_ref}",
                },
                {
                    "field_path": "character.background_and_traits",
                    "value": {"traits": traits, "knowledge": knowledge},
                    "origin": "retrieved",
                    "producer_refs": [RETRIEVAL_CAPABILITY],
                    "source_refs": source_refs,
                    "run_receipt_refs": ["evidence/character_retrieval.json"],
                    "constraint_refs": [RETRIEVAL_POLICY_REF],
                    "canon_target_ref": None,
                },
            ]
            answer_semantic = strip_volatile_fields(answer_value)
        elif direct:
            candidate_refs = [str(item["canonical_id"]) for item in direct]
            summary = "ACE found multiple committed identities matching the supplied identity anchor; relation evidence did not uniquely disambiguate them."
            blockers.append(
                {
                    "blocker_id": f"ace.blocker.character.referent-ambiguous.{semantic_sha256(candidate_refs)[:12]}",
                    "kind": "semantic_coverage_incomplete",
                    "capability_ref": RELATION_CAPABILITY,
                    "reason": f"Identity/name evidence matches multiple canonical characters: {', '.join(candidate_refs)}.",
                    "recovery_action": "Gather additional committed relation evidence (faction, role, location, relation, or explicit canonical ID) before generation or identity selection.",
                }
            )
            answer_semantic = {"ambiguous_candidates": direct}
        elif relation_only:
            candidate_refs = [str(item["canonical_id"]) for item in relation_only]
            summary = "ACE found one or more strongly related existing canonical characters but no direct identity anchor; generation is blocked to prevent a duplicate referent."
            blockers.append(
                {
                    "blocker_id": f"ace.blocker.character.possible-existing.{semantic_sha256(candidate_refs)[:12]}",
                    "kind": "semantic_coverage_incomplete",
                    "capability_ref": RELATION_CAPABILITY,
                    "reason": f"Role/faction/location evidence strongly overlaps existing character(s): {', '.join(candidate_refs)}.",
                    "recovery_action": "Acquire an identity anchor or invoke a registered reconciliation capability before treating the encountered person as unrecorded.",
                }
            )
            answer_semantic = {"possible_existing_candidates": relation_only}
        else:
            summary = "ACE found no existing canonical character matching the supplied lookup evidence; this retrieval query cannot itself generate a new character."
            blockers.append(
                {
                    "blocker_id": f"ace.blocker.character.no-existing-record.{semantic_sha256(query['query_id'])[:12]}",
                    "kind": "semantic_coverage_incomplete",
                    "capability_ref": RETRIEVAL_CAPABILITY,
                    "reason": "No matching canonical character identity is present at the registered CanonRec baseline.",
                    "recovery_action": "If the referent is confirmed unrecorded, compile the normal specialist-first character completion flow.",
                }
            )
            answer_semantic = {"no_existing_record": True}

        if not answer_fields:
            unresolved_sources = [
                str(item["source_ref"])
                for item in [*direct, *relation_only]
                if isinstance(item.get("source_ref"), str)
            ]
            answer_fields = [
                {
                    "field_path": "character.identity",
                    "value": None,
                    "origin": "retrieved",
                    "producer_refs": [RETRIEVAL_CAPABILITY, RELATION_CAPABILITY],
                    "source_refs": list(dict.fromkeys(unresolved_sources)),
                    "run_receipt_refs": ["evidence/character_retrieval.json"],
                    "constraint_refs": [RETRIEVAL_POLICY_REF, RELATION_POLICY_REF],
                    "canon_target_ref": None,
                }
            ]

        answer = {
            "summary": summary,
            "fields": answer_fields,
            "no_prior_record": not bool(direct or relation_only),
            "supersedes_determination_refs": [],
        }
        baselines = [
            {
                "repository": item["repository"],
                "commit_sha": item["commit_sha"],
                "authority_role": item["authority_role"],
            }
            for item in query["baselines"]
        ]
        canon_head = next(item["commit_sha"] for item in baselines if item["repository"] == "CanonRec")
        projection_payload = {
            "index_sha256": index["index_sha256"],
            "direct_candidates": direct,
            "relation_only_candidates": relation_only,
        }
        retrieval_cap = capabilities[RETRIEVAL_CAPABILITY]
        relation_cap = capabilities[RELATION_CAPABILITY]
        steps = [
            {
                "step_id": "ace.step.character.retrieve_existing",
                "capability_id": RETRIEVAL_CAPABILITY,
                "status": "succeeded",
                "depends_on": [],
                "consumes": ["CanonRec:canon/L2/entities/*/capsule/identity.json"],
                "produces": ["evidence/character_retrieval.json"],
                "tool_run_id": "ace-run-character-retrieve-existing",
                "run_receipt_ref": "evidence/character_retrieval.json",
                "manifest_sha256": retrieval_cap["manifest_sha256"],
                "repository_sha": retrieval_cap["repository_sha"],
                "seed": None,
                "duration_ms": 0.0,
                "output_sha256": semantic_sha256(index),
                "semantic_output_sha256": semantic_sha256(strip_volatile_fields(index)),
                "artifact_output_sha256": semantic_sha256(index),
                "volatile_output_fields": [],
                "tool_native_statuses": {},
                "side_effects_observed": [],
            },
            {
                "step_id": "ace.step.character.enrich_relations",
                "capability_id": RELATION_CAPABILITY,
                "status": "succeeded",
                "depends_on": ["ace.step.character.retrieve_existing"],
                "consumes": ["evidence/character_retrieval.json", "query.subject.context"],
                "produces": ["character.relations"],
                "tool_run_id": "ace-run-character-relations",
                "run_receipt_ref": "evidence/character_retrieval.json",
                "manifest_sha256": relation_cap["manifest_sha256"],
                "repository_sha": relation_cap["repository_sha"],
                "seed": None,
                "duration_ms": 0.0,
                "output_sha256": semantic_sha256(discovery),
                "semantic_output_sha256": semantic_sha256(discovery),
                "artifact_output_sha256": semantic_sha256(discovery),
                "volatile_output_fields": [],
                "tool_native_statuses": {},
                "side_effects_observed": [],
            },
        ]
        coverage = [
            {
                "requirement_id": "ace.semantic.character.existing_identity",
                "status": "satisfied" if status == "RETRIEVED_CANON" else "missing",
                "field_refs": ["character.identity"],
                "producer_refs": [RETRIEVAL_CAPABILITY],
                "reason": "Unique committed identity resolved." if status == "RETRIEVED_CANON" else "No uniquely established existing identity is available.",
            },
            {
                "requirement_id": "ace.semantic.character.relation_disambiguation",
                "status": "satisfied",
                "field_refs": ["character.relations"],
                "producer_refs": [RELATION_CAPABILITY],
                "reason": "Committed role/faction/location evidence was evaluated and relation-only evidence was not promoted to identity equivalence.",
            },
        ]
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "ace_determination_receipt",
            "determination_id": f"ace.determination.character.retrieve.{semantic_sha256({'query': query['query_id'], 'status': status, 'answer': answer_semantic, 'blockers': blockers})[:20]}",
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
            "subject_refs": [str(query["subject"].get("subject_ref") or "character:unresolved")],
            "answer_contract": {
                "compiler_version": query["answer_contract"]["compiler_version"],
                "overall_status": overall_status,
                "coverage": coverage,
            },
            "projections": [
                {
                    "projection_id": f"ace.projection.character.existing.{semantic_sha256(projection_payload)[:16]}",
                    "projection_type": "raw_evidence_index",
                    "source_repository": "CanonRec",
                    "source_commit_sha": canon_head,
                    "source_semantic_sha256": index["index_sha256"],
                    "transform_id": "ace.transform.character.identity_relation_index",
                    "transform_version": CHARACTER_RETRIEVAL_VERSION,
                    "projection_sha256": semantic_sha256(projection_payload),
                    "source_member_count": index["record_count"],
                    "projected_member_count": len(direct) + len(relation_only),
                    "collapsed_row_count": 0,
                    "unresolved_relation_count": 0 if status == "RETRIEVED_CANON" else len(direct) + len(relation_only),
                    "membership_receipt_ref": "evidence/character_retrieval.json",
                }
            ],
            "transactions": [],
            "answer": answer,
            "plan": {
                "plan_id": f"ace.plan.character.retrieve.{semantic_sha256(query['query_id'])[:16]}",
                "selection_basis": ["retrieval_first", "canonical_identity_anchor", "relation_evidence_before_generation"],
                "rejected_capability_refs": [
                    "ace.capability.gumas.naming.resolve",
                    "ace.capability.quantum_forge.charforge.generate_capsule",
                ],
                "steps": steps,
            },
            "validation": {
                "overall_status": validation_status,
                "gates": [
                    {
                        "gate_id": "character_retrieval_read_only",
                        "status": "pass",
                        "validator_ref": "aurora_ace.validation.character_retrieval_read_only",
                        "receipt_refs": ["evidence/character_retrieval.json"],
                        "finding_codes": [],
                        "summary": "Existing-character retrieval produced no repository, generator, runtime, or simulation side effects.",
                    },
                    {
                        "gate_id": "character_identity_resolution",
                        "status": "pass" if status == "RETRIEVED_CANON" else "blocked",
                        "validator_ref": "aurora_ace.validation.character_identity_resolution",
                        "receipt_refs": ["evidence/character_retrieval.json"],
                        "finding_codes": [] if status == "RETRIEVED_CANON" else [str(blockers[0]["kind"])],
                        "summary": "Unique existing referent resolved." if status == "RETRIEVED_CANON" else blockers[0]["reason"],
                    },
                ],
            },
            "conflicts": conflicts,
            "blockers": blockers,
            "materialization": {
                "status": "not_required" if status == "RETRIEVED_CANON" else "blocked",
                "target_repository": None,
                "target_paths": [],
                "commit_sha": None,
                "gate_policy_ref": RETRIEVAL_POLICY_REF,
                "commit_ready_packet_ref": None,
            },
            "integrity": {
                "query_sha256": semantic_sha256(query),
                "capability_manifest_sha256s": sorted({retrieval_cap["manifest_sha256"], relation_cap["manifest_sha256"]}),
                "answer_sha256": semantic_sha256(answer),
                "semantic_answer_sha256": semantic_sha256(strip_volatile_fields(answer)),
                "artifact_sha256s": [
                    file_sha256(transaction_root / "query_envelope.json"),
                    file_sha256(transaction_root / "capability_index.json"),
                    file_sha256(transaction_root / "evidence/character_retrieval.json"),
                ],
                "semantic_digest_policy_ref": "ace.policy.semantic-digest.exclude-volatile-v1",
                "prior_determination_digest": None,
            },
            "replay": {
                "replayable": True,
                "deterministic": True,
                "replay_command": "python3 tools/aurora_ace.py resolve --query query_envelope.json --out <new-output-directory>",
                "required_artifact_refs": ["query_envelope.json", "capability_index.json", "evidence/character_retrieval.json"],
                "non_replayable_reasons": [],
            },
        }
        write_json(transaction_root / "determination_receipt.json", receipt)
        write_json(
            transaction_root / "receipts/execution_summary.json",
            {
                "engine": "aurora_ace",
                "character_retrieval_version": CHARACTER_RETRIEVAL_VERSION,
                "status": status,
                "duration_ms": round((time.perf_counter() - started) * 1000, 3),
                "canon_mutation": False,
                "generator_invoked": False,
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

"""Deterministic contracts, capability routing, and projections for ACE."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

ENGINE_VERSION = "0.1.0"
SCHEMA_VERSION = "0.1.1"
ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "catalog" / "repo_registry.yaml"
CONTRACT_REF = "catalog/contracts/aurora_ace_contract_v0_1.json"
CANONREC_REL = Path("GUMAS_SIM_2.5/CanonRec")
CLOUDBANK_REL = Path(
    "GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main"
)
CHARFORGE_REL = Path("GUMAS_SIM_2.5/FORGE__GUMAS_v3.0__2026-02-19/charforge.py")
NAME_SERVICE_REL = CLOUDBANK_REL / "modules/gumas/naming.py"
CANONREC_TOOL_REL = CANONREC_REL / "aurora-canon-reconciler/scripts"


class ACEError(RuntimeError):
    """An evidence-backed ACE planning or execution failure."""

    def __init__(self, message: str, *, code: str = "runtime_failure") -> None:
        super().__init__(message)
        self.code = code


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")


def semantic_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(path: Path, namespace: str) -> Any:
    """Load one allowlisted source file without turning discovery into execution."""
    if not path.is_file():
        raise ACEError(f"Allowlisted capability source is missing: {path}", code="missing_tool")
    module_name = f"ace_{namespace}_{file_sha256(path)[:12]}"
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ACEError(f"Unable to load capability source: {path}", code="tool_unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


def _git_head(repo: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )
    head = completed.stdout.strip()
    if completed.returncode != 0 or not re.fullmatch(r"[a-f0-9]{40}", head):
        raise ACEError(
            f"Could not observe repository HEAD for {repo}: {completed.stderr.strip()}",
            code="target_unavailable",
        )
    return head


def repository_baselines(root: Path = ROOT, *, require_registered_heads: bool = True) -> list[dict[str, str]]:
    registry = yaml.safe_load((root / "catalog/repo_registry.yaml").read_text(encoding="utf-8"))
    registered = {row["name"]: row for row in registry.get("repos", [])}
    required = {
        "CanonRec": (CANONREC_REL, "canon"),
        "aurora-cloudbank-symbolic-main": (CLOUDBANK_REL, "runtime"),
    }
    baselines = [
        {
            "repository": "root",
            "path": ".",
            "commit_sha": _git_head(root),
            "authority_role": "control_plane",
        }
    ]
    for name, (relative_path, authority_role) in required.items():
        row = registered.get(name)
        if not row or Path(row.get("path", "")) != relative_path:
            raise ACEError(
                f"Required repository is not registered at its allowlisted path: {name}",
                code="invalid_manifest",
            )
        observed = _git_head(root / relative_path)
        registered_head = str(row.get("head_sha", ""))
        if require_registered_heads and observed != registered_head:
            raise ACEError(
                f"Registered baseline advanced for {name}: registry={registered_head}, observed={observed}",
                code="stale_manifest",
            )
        baselines.append(
            {
                "repository": name,
                "path": relative_path.as_posix(),
                "commit_sha": observed,
                "authority_role": authority_role,
            }
        )
    return baselines


def build_capability_index(root: Path = ROOT) -> dict[str, Any]:
    """Build the ACE capability index from validated committed manifests."""
    from .capability_discovery import build_capability_index as build_discovered_index

    return build_discovered_index(root)


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")
    return normalized or "character"


def allocate_character_id(question: str, context: Mapping[str, Any], seed: int | str) -> str:
    material = {
        "question": question.strip(),
        "context": context,
        "seed": seed,
        "policy": "ace.policy.contextual-referent-id.v1",
    }
    suffix = semantic_sha256(material)[:12]
    return f"char_{_slug(str(context.get('role', 'character')))[:32]}_{suffix}"


def compile_character_query(
    question: str,
    context: Mapping[str, Any],
    *,
    seed: int | str = 808,
    mode: str = "commit_ready",
    requester_kind: str = "user",
    requester_id: str = "ORION.ROLE.PILOT",
    session_ref: str | None = None,
    root: Path = ROOT,
) -> dict[str, Any]:
    if not question.strip():
        raise ACEError("question must not be empty", code="input_validation_failed")
    if mode not in {"plan_only", "commit_ready"}:
        raise ACEError("ACE MVP supports plan_only and commit_ready modes", code="input_validation_failed")
    observed = context.get("observed_behavior", [])
    if not isinstance(observed, list) or any(not isinstance(item, str) for item in observed):
        raise ACEError("observed_behavior must be an array of strings", code="input_validation_failed")

    # Retrieval is constitutive precedence, not an optional optimization. An
    # existing canonical referent must be resolved (or explicitly blocked as
    # ambiguous) before identity allocation, NameService, or CharForge can run.
    from .character_retrieval import compile_existing_character_query_if_applicable

    retrieval_query = compile_existing_character_query_if_applicable(
        question,
        context,
        seed=seed,
        mode=mode,
        requester_kind=requester_kind,
        requester_id=requester_id,
        session_ref=session_ref,
        root=root,
    )
    if retrieval_query is not None:
        return retrieval_query

    for field in ("role", "faction_id", "location_type"):
        if not isinstance(context.get(field), str) or not str(context[field]).strip():
            raise ACEError(f"character context requires non-empty {field}", code="input_validation_failed")

    baselines = repository_baselines(root)
    entity_id = allocate_character_id(question, context, seed)
    query_suffix = semantic_sha256(
        {"question": question.strip(), "context": context, "seed": seed, "mode": mode}
    )[:20]
    query_id = f"ace.query.character.{query_suffix}"
    target = f"canon/L2/entities/{entity_id}"
    contextual_refs = list(dict.fromkeys(
        [
            *[str(item) for item in context.get("contextual_refs", []) if str(item)],
            str(context["faction_id"]),
            str(context["location_type"]),
        ]
    ))
    outputs = [
        ("character.canonical_id", "ace.capability.identity.allocate", "Stable character identity for repeat resolution."),
        ("character.canonical_name", "ace.capability.gumas.naming.resolve", "Collision-safe canonical person name."),
        ("character.role", "ace.capability.context.resolve", "Resolved current duty role."),
        ("character.background", "ace.capability.quantum_forge.charforge.generate_capsule", "State-grounded operational background."),
        ("character.traits", "ace.capability.quantum_forge.charforge.generate_capsule", "Character voice, values, bias, and constraints."),
        ("character.naming_receipt", "ace.capability.gumas.naming.resolve", "Naming protocol and collision receipt."),
        ("character.canonical_target", "ace.capability.canonrec.materialize.entity", "Exact commit target for the entity."),
    ]
    requirements = [
        {
            "requirement_id": "ace.semantic.character.identity",
            "semantic_type": "stable_character_identity",
            "description": "Return a stable character ID and collision-safe canonical name.",
            "required": True,
            "accepts_state_derived": False,
            "accepts_connective_rendering": False,
            "acceptable_origins": ["deterministic_derivation", "specialist_tool_output"],
            "minimum_evidence": ["identity_allocation_receipt", "naming_receipt"],
        },
        {
            "requirement_id": "ace.semantic.character.current_context",
            "semantic_type": "current_role_and_faction_context",
            "description": "State the character's current role, faction, and duty context.",
            "required": True,
            "accepts_state_derived": True,
            "accepts_connective_rendering": True,
            "acceptable_origins": ["retrieved", "specialist_tool_output", "connective_synthesis"],
            "minimum_evidence": ["resolved_context", "leader_state", "faction_state"],
        },
        {
            "requirement_id": "ace.semantic.character.operational_background",
            "semantic_type": "state_derived_operational_background",
            "description": "Describe role, decision profile, stressors, and relationships supported by generated state.",
            "required": True,
            "accepts_state_derived": True,
            "accepts_connective_rendering": True,
            "acceptable_origins": ["specialist_tool_output", "connective_synthesis"],
            "minimum_evidence": ["charforge_identity_synopsis", "charforge_bias_pattern"],
        },
        {
            "requirement_id": "ace.semantic.character.behavioral_profile",
            "semantic_type": "traits_and_decision_profile",
            "description": "Return tool-produced traits, values, and decision tendencies.",
            "required": True,
            "accepts_state_derived": True,
            "accepts_connective_rendering": False,
            "acceptable_origins": ["specialist_tool_output"],
            "minimum_evidence": ["charforge_traits", "charforge_state_vector"],
        },
        {
            "requirement_id": "ace.semantic.character.formative_biography",
            "semantic_type": "origin_education_and_formative_events",
            "description": "A fuller formative biography if explicitly requested beyond operational background.",
            "required": False,
            "accepts_state_derived": False,
            "accepts_connective_rendering": False,
            "acceptable_origins": ["retrieved", "specialist_tool_output"],
            "minimum_evidence": ["history_producer_receipt"],
        },
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "ace_query_envelope",
        "query_id": query_id,
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
            "layers": ["L2"],
            "target_repository": "CanonRec",
            "target_paths": [target],
            "temporal_basis": "explicit_commit_set",
        },
        "baselines": baselines,
        "subject": {
            "subject_ref": context.get("subject_ref"),
            "entity_type": "character",
            "existence_status": str(context.get("existence_status", "confirmed_unrecorded")),
            "contextual_refs": contextual_refs,
            "context": dict(context),
        },
        "requested_outputs": [
            {
                "field_path": field,
                "required": True,
                "preferred_capability_refs": [capability],
                "description": description,
            }
            for field, capability, description in outputs
        ],
        "answer_contract": {
            "compiler_version": "ace-answer-contract-0.1.1",
            "interpretation_basis": [
                "question:name_and_background",
                "subject:confirmed_unrecorded_character",
                "context:operational_encounter",
            ],
            "coverage_policy": "all_mandatory_semantics_satisfied",
            "requirements": requirements,
        },
        "generation_policy": {
            "canonical_completion_allowed": True,
            "constitutive_simulation_allowed": True,
            "analytical_simulation_allowed": True,
            "prefer_existing_specialists": True,
            "connective_synthesis_policy": "connective_only",
            "deterministic_required": True,
            "stable_seed": seed,
            "reserved_decision_policy_ref": "ace.policy.reserved-decisions.v1",
        },
        "execution_policy": {
            "mode": mode,
            "delegation_policy_ref": "ace.policy.delegated-routine-character-completion.v1",
            "allowed_side_effects": [] if mode == "plan_only" else ["write_transaction_workspace"],
            "budgets": {
                "max_tool_calls": 12,
                "max_new_entities": 1,
                "max_wall_seconds": 30,
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


def normalize_name(value: str) -> str:
    import unicodedata

    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch)).casefold()
    return re.sub(r"[^a-z0-9]+", "", value)


class _UnionFind:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))

    def find(self, item: int) -> int:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left: int, right: int) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root != right_root:
            self.parent[max(left_root, right_root)] = min(left_root, right_root)


def build_name_reservation_projection(entries: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Collapse name occupancy, never source identity or membership evidence."""
    rows = [dict(row) for row in entries]
    union = _UnionFind(len(rows))
    first_by_name: dict[str, int] = {}
    for index, row in enumerate(rows):
        names = [str(row.get("canonical_name", "")), *[str(x) for x in row.get("aliases", [])]]
        for name in names:
            key = normalize_name(name)
            if not key:
                continue
            previous = first_by_name.setdefault(key, index)
            union.union(index, previous)

    grouped: dict[int, list[dict[str, Any]]] = {}
    for index, row in enumerate(rows):
        grouped.setdefault(union.find(index), []).append(row)

    reservations: list[dict[str, Any]] = []
    components: list[dict[str, Any]] = []
    unresolved_count = 0
    for members in grouped.values():
        members.sort(key=lambda row: (str(row.get("canonical_name", "")).casefold(), str(row.get("entity_id", ""))))
        names = sorted(
            {
                str(name).strip()
                for row in members
                for name in [row.get("canonical_name", ""), *row.get("aliases", [])]
                if str(name).strip()
            },
            key=lambda name: (name.casefold(), name),
        )
        canonical = names[0]
        member_ids = sorted({str(row.get("entity_id", "unknown")) for row in members})
        component_hash = semantic_sha256(
            {"names": [normalize_name(name) for name in names], "member_ids": member_ids}
        )[:16]
        reservation_id = f"ace.occupancy.{component_hash}"
        relation_state = "unresolved" if len(member_ids) > 1 else "proven_equivalent"
        if relation_state == "unresolved":
            unresolved_count += 1
        reservations.append(
            {
                "canonical_name": canonical,
                "entity_id": reservation_id,
                "entity_type": "CUSTOM",
                "aliases": [name for name in names[1:] if normalize_name(name) != normalize_name(canonical)],
            }
        )
        components.append(
            {
                "component_id": reservation_id,
                "canonical_name": canonical,
                "relation_state": relation_state,
                "members": members,
            }
        )
    reservations.sort(key=lambda row: (row["canonical_name"].casefold(), row["entity_id"]))
    components.sort(key=lambda row: row["component_id"])
    raw_semantic = [
        {
            "canonical_name": row.get("canonical_name"),
            "entity_id": row.get("entity_id"),
            "entity_type": row.get("entity_type", "CUSTOM"),
            "aliases": sorted(row.get("aliases", [])),
            "source_path": row.get("source_path"),
        }
        for row in sorted(rows, key=lambda row: (str(row.get("canonical_name", "")).casefold(), str(row.get("entity_id", ""))))
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "projection_id": "ace.projection.name_reservation_occupancy.v0.1.1",
        "transform_id": "ace.transform.connected_name_occupancy",
        "transform_version": "0.1.1",
        "source_semantic_sha256": semantic_sha256(raw_semantic),
        "projection_sha256": semantic_sha256(reservations),
        "source_member_count": len(rows),
        "projected_member_count": len(reservations),
        "collapsed_row_count": len(rows) - len(reservations),
        "unresolved_relation_count": unresolved_count,
        "reservations": reservations,
        "membership": components,
    }


def strip_volatile_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: strip_volatile_fields(item)
            for key, item in value.items()
            if key not in {"generated_at", "created_at", "timestamp"}
        }
    if isinstance(value, list):
        return [strip_volatile_fields(item) for item in value]
    return value


def validate_json_schema(artifact: Path, schema: Path, root: Path = ROOT) -> dict[str, Any]:
    """Use an installed validator, including the registered CloudBank venv fallback."""
    # The probe reports an unusable runtime on stdout instead of dying on an
    # AttributeError, so the caller can fall through to the next candidate.
    #
    # A runtime can be unusable two ways, and only one of them used to be
    # handled. jsonschema may be absent, or it may be present and too old:
    # Draft202012Validator arrived in jsonschema 4.0, so a 3.x install passes the
    # import and then fails on attribute access. For this function's purpose
    # those are the same condition — this runtime cannot validate — but the
    # original skip matched only "No module named 'jsonschema'", so an old
    # install raised instead of deferring to the CloudBank venv that has 4.25.
    #
    # It survived because of an accident of environment: the Mac's system python
    # has no jsonschema at all, so the missing-module path always fired there.
    # Any runtime carrying a 3.x install breaks it.
    script = (
        "import json,sys; from pathlib import Path; import jsonschema; "
        "V=getattr(jsonschema,'Draft202012Validator',None); "
        "print(json.dumps({'unusable':'jsonschema %s lacks Draft202012Validator "
        "(requires jsonschema>=4)' % getattr(jsonschema,'__version__','?')})) "
        "or sys.exit(0) if V is None else None; "
        "schema=json.loads(Path(sys.argv[1]).read_text()); "
        "data=json.loads(Path(sys.argv[2]).read_text()); "
        "V.check_schema(schema); "
        "errors=sorted(V(schema, "
        "format_checker=jsonschema.FormatChecker()).iter_errors(data), key=lambda e:list(e.path)); "
        "print(json.dumps({'ok':not errors,'errors':[{'path':list(e.path),'message':e.message} for e in errors]})); "
        "raise SystemExit(0 if not errors else 1)"
    )
    candidates = [Path(sys.executable), root / CLOUDBANK_REL / ".venv/bin/python"]
    attempts: list[str] = []
    for python in candidates:
        if not python.exists():
            continue
        completed = subprocess.run(
            [str(python), "-c", script, str(schema), str(artifact)],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if "No module named 'jsonschema'" in completed.stderr:
            attempts.append(f"{python}: jsonschema not installed")
            continue
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise ACEError(f"Schema validator failed: {completed.stderr.strip()}") from exc
        if payload.get("unusable"):
            attempts.append(f"{python}: {payload['unusable']}")
            continue
        payload["validator_python"] = str(python)
        payload["artifact"] = str(artifact)
        payload["schema"] = str(schema)
        return payload
    detail = "; ".join(attempts) if attempts else "no candidate runtime exists"
    raise ACEError(
        f"No registered local runtime can validate JSON Schema ({detail})",
        code="tool_unavailable",
    )

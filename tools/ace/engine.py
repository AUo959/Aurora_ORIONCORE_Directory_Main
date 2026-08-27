"""Transactional ACE character-resolution vertical slice."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping

from .core import (
    ACEError,
    CANONREC_REL,
    CANONREC_TOOL_REL,
    CHARFORGE_REL,
    CLOUDBANK_REL,
    CONTRACT_REF,
    ENGINE_VERSION,
    NAME_SERVICE_REL,
    ROOT,
    SCHEMA_VERSION,
    build_capability_index,
    build_name_reservation_projection,
    canonical_json_bytes,
    file_sha256,
    load_json,
    load_module,
    normalize_name,
    repository_baselines,
    semantic_sha256,
    strip_volatile_fields,
    utc_now,
    validate_json_schema,
    write_json,
)


def _enum(value: str) -> SimpleNamespace:
    return SimpleNamespace(value=value)


def _stable_float(material: Mapping[str, Any], label: str, low: float, high: float) -> float:
    digest = semantic_sha256({"material": material, "label": label})
    ratio = int(digest[:12], 16) / float(0xFFFFFFFFFFFF)
    return round(low + (high - low) * ratio, 4)


def _faction_name(value: str) -> str:
    return " ".join(token.capitalize() for token in value.replace("-", "_").split("_") if token)


def _build_states(entity_id: str, name: str, context: Mapping[str, Any], seed: int | str) -> tuple[Any, Any, dict[str, Any]]:
    material = {"entity_id": entity_id, "context": context, "seed": seed}
    observed = " ".join(str(item).casefold() for item in context.get("observed_behavior", []))
    biases = [
        "status_quo_bias",
        "hyper_rationalism_bias",
        "confirmation_bias",
        "survivorship_bias",
    ]
    if "chain of command" in observed or "deferred" in observed:
        dominant_bias = "status_quo_bias"
    elif "allocat" in observed or "coordinat" in observed:
        dominant_bias = "hyper_rationalism_bias"
    else:
        dominant_bias = biases[int(semantic_sha256(material)[:4], 16) % len(biases)]
    faction_id = str(context["faction_id"])
    faction_type = "federation" if "galactic_union" in faction_id.casefold() else str(context.get("faction_type", "federation"))
    role = str(context["role"]).replace("_", " ").title()
    leader_values = {
        "bias_intensity": _stable_float(material, "bias_intensity", 0.35, 0.8),
        "plasticity": _stable_float(material, "plasticity", 0.25, 0.7),
        "evidence_gain_multiplier": _stable_float(material, "evidence_gain_multiplier", 0.8, 1.5),
        "risk_tolerance": _stable_float(material, "risk_tolerance", 0.25, 0.7),
        "diplomacy_openness": _stable_float(material, "diplomacy_openness", 0.4, 0.85),
        "escalation_threshold": _stable_float(material, "escalation_threshold", 0.4, 0.8),
        "oversight_resistance": _stable_float(material, "oversight_resistance", 0.2, 0.65),
        "public_legitimacy": _stable_float(material, "public_legitimacy", 0.5, 0.85),
        "elite_support": _stable_float(material, "elite_support", 0.45, 0.8),
        "institutional_control": _stable_float(material, "institutional_control", 0.4, 0.8),
        "war_pressure": float(context.get("war_pressure", _stable_float(material, "war_pressure", 0.05, 0.5))),
        "economic_shock": float(context.get("economic_shock", _stable_float(material, "economic_shock", 0.0, 0.3))),
    }
    faction_values = {
        "military_strength": _stable_float(material, "military_strength", 0.35, 0.8),
        "economic_strength": _stable_float(material, "economic_strength", 0.35, 0.8),
        "technology_level": _stable_float(material, "technology_level", 0.4, 0.85),
        "population_stability": _stable_float(material, "population_stability", 0.5, 0.9),
        "reputation": _stable_float(material, "reputation", 0.4, 0.85),
        "verification_demand": _stable_float(material, "verification_demand", 0.3, 0.75),
        "deal_discount": _stable_float(material, "deal_discount", 0.0, 0.2),
        "coalition_invite_weight": _stable_float(material, "coalition_invite_weight", 0.35, 0.8),
        "economic_potential": _stable_float(material, "economic_potential", 0.45, 0.9),
    }
    leader = SimpleNamespace(
        leader_id=entity_id,
        name=name,
        role=role,
        faction_id=faction_id,
        dominant_bias=_enum(dominant_bias),
        secondary_biases=[],
        war_losses=int(context.get("war_losses", 0)),
        betrayals=int(context.get("betrayals", 0)),
        scandals=int(context.get("scandals", 0)),
        certainty=_enum("CANON_PROMOTE"),
        **leader_values,
    )
    faction = SimpleNamespace(
        faction_id=faction_id,
        name=str(context.get("faction_name", _faction_name(faction_id))),
        faction_type=_enum(faction_type),
        trust_scores=dict(context.get("trust_scores", {})),
        **faction_values,
    )
    receipt = {
        "adapter": "ace.adapter.charforge_state.v0.1.0",
        "policy": "deterministic_context_to_state",
        "seed": seed,
        "leader": {"dominant_bias": dominant_bias, **leader_values},
        "faction": {"faction_type": faction_type, **faction_values},
        "explicit_stressors": {
            "war_losses": leader.war_losses,
            "betrayals": leader.betrayals,
            "scandals": leader.scandals,
        },
    }
    return leader, faction, receipt


def _run_json(command: list[str], *, cwd: Path, timeout: int = 20) -> tuple[dict[str, Any], float, int, str]:
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    duration = round((time.perf_counter() - started) * 1000, 3)
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ACEError(
            f"Capability returned non-JSON output: {' '.join(command)}: {completed.stderr.strip()}",
            code="output_validation_failed",
        ) from exc
    return payload, duration, completed.returncode, completed.stderr


def _safe_output_path(output_dir: Path, root: Path) -> Path:
    output = output_dir.expanduser().resolve()
    protected = [(root / CANONREC_REL).resolve(), (root / CLOUDBANK_REL).resolve()]
    for repo in protected:
        if output == repo or repo in output.parents:
            raise ACEError(
                f"ACE commit-ready output cannot be written inside a nested repository: {repo}",
                code="target_unavailable",
            )
    if output == root.resolve():
        raise ACEError("ACE output cannot replace the root workspace", code="target_unavailable")
    if output.exists():
        raise ACEError(f"Output already exists: {output}", code="target_unavailable")
    return output


def _background(name: str, context: Mapping[str, Any], knowledge: list[dict[str, Any]]) -> str:
    identity = next((item["text"] for item in knowledge if "identity" in item.get("tags", [])), "")
    decision = next((item["text"] for item in knowledge if "decision_making" in item.get("tags", [])), "")
    observed = [str(item).rstrip(".") for item in context.get("observed_behavior", [])]
    location = str(context["location_type"]).replace("_", " ")
    observed_sentence = ""
    if observed:
        observed_sentence = f" In the observed encounter aboard the {location}, {name} " + "; and ".join(observed) + "."
    return (identity + " " + decision + observed_sentence).strip()


def _step(
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
    seed: int | str | None,
    duration_ms: float | None,
    side_effects: list[str] | None = None,
    tool_statuses: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "step_id": f"ace.step.character.{suffix}",
        "capability_id": capability["capability_id"],
        "status": status,
        "depends_on": depends_on,
        "consumes": consumes,
        "produces": produces,
        "tool_run_id": f"ace-run-character-{suffix}" if status != "blocked" else None,
        "run_receipt_ref": receipt_ref,
        "manifest_sha256": capability["manifest_sha256"],
        "repository_sha": repository_sha,
        "seed": seed,
        "duration_ms": duration_ms,
        "output_sha256": semantic_sha256(output) if output is not None else None,
        "semantic_output_sha256": semantic_sha256(strip_volatile_fields(output)) if output is not None else None,
        "artifact_output_sha256": semantic_sha256(output) if output is not None else None,
        "volatile_output_fields": ["generated_at"] if suffix == "charforge" else [],
        "tool_native_statuses": dict(tool_statuses or {}),
        "side_effects_observed": list(side_effects or []),
    }


def _tree_artifacts(root: Path, *, exclude: set[str]) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): file_sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.relative_to(root).as_posix() not in exclude
    }


def _replace_path_prefix(value: Any, source: Path, replacement: str = ".") -> Any:
    """Remove disposable transaction paths from durable receipts."""
    prefix = str(source)
    if isinstance(value, str):
        return replacement + value[len(prefix):] if value.startswith(prefix) else value
    if isinstance(value, list):
        return [_replace_path_prefix(item, source, replacement) for item in value]
    if isinstance(value, dict):
        return {
            key: _replace_path_prefix(item, source, replacement)
            for key, item in value.items()
        }
    return value


def _semantic_capsule_digest(bundle: Path) -> str:
    semantic: dict[str, Any] = {}
    for path in sorted(bundle.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(bundle).as_posix()
        if path.suffix in {".json", ".yaml"}:
            semantic[rel] = strip_volatile_fields(load_json(path))
        elif path.suffix == ".jsonl":
            semantic[rel] = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        else:
            semantic[rel] = file_sha256(path)
    return semantic_sha256(semantic)


def _assert_query(query: Mapping[str, Any], root: Path) -> None:
    if query.get("record_type") != "ace_query_envelope" or query.get("schema_version") != SCHEMA_VERSION:
        raise ACEError("Unsupported ACE query envelope", code="input_validation_failed")
    if query.get("query_kind") != "complete" or query.get("subject", {}).get("entity_type") != "character":
        raise ACEError("ACE MVP resolves complete-character queries only", code="input_validation_failed")
    if query.get("execution_policy", {}).get("mode") != "commit_ready":
        raise ACEError("resolve requires a commit_ready query envelope", code="input_validation_failed")
    current = repository_baselines(root)
    expected = {(item["repository"], item["commit_sha"]) for item in query.get("baselines", [])}
    observed = {(item["repository"], item["commit_sha"]) for item in current}
    if expected != observed:
        raise ACEError(
            "Query baseline no longer matches the registered live repository set; recompile before execution",
            code="registry_baseline_advanced",
        )


def resolve_character_query(query: Mapping[str, Any], output_dir: Path, *, root: Path = ROOT) -> dict[str, Any]:
    """Execute the specialist-first character completion into an atomic packet."""
    execution_started = time.perf_counter()
    _assert_query(query, root)
    output = _safe_output_path(output_dir, root)
    output.parent.mkdir(parents=True, exist_ok=True)
    transaction_root = Path(tempfile.mkdtemp(prefix=".ace-character-", dir=output.parent))
    try:
        write_json(transaction_root / "query_envelope.json", query)
        capability_index = build_capability_index(root)
        write_json(transaction_root / "capability_index.json", capability_index)
        capabilities = {item["capability_id"]: item for item in capability_index["capabilities"]}
        required = [
            "ace.capability.context.resolve",
            "ace.capability.identity.allocate",
            "ace.capability.canonrec.project.name_reservations",
            "ace.capability.gumas.naming.resolve",
            "ace.capability.gumas.state.build_character",
            "ace.capability.quantum_forge.charforge.generate_capsule",
            "ace.capability.canonrec.validate.entity",
            "ace.capability.canonrec.validate.naming_receipt",
        ]
        unavailable = [item for item in required if capabilities[item]["lifecycle"] != "active"]
        if unavailable:
            raise ACEError(f"Required capabilities are not active: {', '.join(unavailable)}", code="tool_unavailable")
        heads = {item["repository"]: item["commit_sha"] for item in capability_index["baselines"]}
        context = query["subject"]["context"]
        seed = query["generation_policy"]["stable_seed"]
        entity_id = query["scope"]["target_paths"][0].rstrip("/").split("/")[-1]

        export_module = load_module(
            root / CANONREC_TOOL_REL / "export_name_registry.py",
            "canonrec_name_export",
        )
        raw_registry = export_module.build_registry((root / CANONREC_REL).resolve())
        write_json(transaction_root / "evidence/canonrec_name_registry.json", raw_registry)
        projection = build_name_reservation_projection(raw_registry["entries"])
        write_json(transaction_root / "evidence/name_reservation_projection.json", {
            key: value for key, value in projection.items() if key != "membership"
        })
        write_json(transaction_root / "evidence/name_projection_membership.json", {
            "projection_id": projection["projection_id"],
            "membership": projection["membership"],
        })

        naming = load_module(root / NAME_SERVICE_REL, "gumas_naming")
        registry_entries = [naming.RegistryEntry(**entry) for entry in projection["reservations"]]
        working_registry = naming.NameRegistry(registry_entries)
        pre_digest = working_registry.digest
        name_started = time.perf_counter()
        name_request = naming.NameRequest(
            entity_type=naming.NameEntityType.PERSON,
            entity_id=entity_id,
            faction_context=str(context["faction_id"]),
            region_context=str(context["location_type"]),
            register=naming.NameRegister.FORMAL,
            seed_hint=int(seed),
        )
        resolution = naming.NameService(working_registry).resolve(name_request)
        name_duration = round((time.perf_counter() - name_started) * 1000, 3)
        post_digest = working_registry.digest
        naming_receipt = resolution.naming_receipt()
        write_json(transaction_root / "receipts/naming_receipt.json", naming_receipt)
        naming_transaction = {
            "transaction_id": f"ace.transaction.naming.{query['query_id'].split('.')[-1]}",
            "kind": "naming_reservation",
            "scope": "CanonRec:L2:canonical_name_reservations",
            "baseline_sha256": pre_digest,
            "result_sha256": post_digest,
            "concurrency_policy": "sequential_working_state",
            "revalidation_status": "pass",
            "side_effects": ["reserved_generated_name_in_isolated_working_registry"],
            "receipt_ref": "receipts/naming_transaction.json",
        }
        write_json(transaction_root / "receipts/naming_transaction.json", naming_transaction)

        state_started = time.perf_counter()
        leader, faction, state_receipt = _build_states(
            entity_id, resolution.canonical_name, context, seed
        )
        state_duration = round((time.perf_counter() - state_started) * 1000, 3)
        write_json(transaction_root / "receipts/character_state.json", state_receipt)

        charforge = load_module(root / CHARFORGE_REL, "charforge")
        forge_started = time.perf_counter()
        bundle = charforge.generate_capsule(
            leader,
            faction,
            transaction_root / "artifacts/charforge",
            overwrite=False,
        )
        if not charforge.verify_capsule(bundle):
            raise ACEError("CharForge emitted a capsule that failed verification", code="output_validation_failed")
        forge_duration = round((time.perf_counter() - forge_started) * 1000, 3)
        identity = load_json(bundle / "capsule/identity.json")
        traits = load_json(bundle / "capsule/traits.json")
        knowledge = [
            json.loads(line)
            for line in (bundle / "capsule/knowledge.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        background = _background(resolution.canonical_name, context, knowledge)
        canonical_target = query["scope"]["target_paths"][0]
        candidate = {
            "canonical_id": entity_id,
            "canonical_name": resolution.canonical_name,
            "aliases": resolution.aliases,
            "entity_kind": "character",
            "certainty": "CANON_PROMOTE",
            "doc_sources": [query["query_id"], *query["subject"]["contextual_refs"]],
            "notes": "ACE constitutive completion; commit-ready and not yet written to CanonRec.",
            "role": str(context["role"]).replace("_", " ").title(),
            "faction": str(context["faction_id"]),
            "sources": list(query["subject"]["contextual_refs"]),
            "background_summary": background,
            "traits": traits,
            "naming_receipt": naming_receipt,
            "ace_query_id": query["query_id"],
            "ace_capsule_ref": f"artifacts/charforge/{entity_id}",
        }
        candidate_path = transaction_root / f"candidate/{entity_id}.json"
        write_json(candidate_path, candidate)

        current_registry = export_module.build_registry((root / CANONREC_REL).resolve())
        current_projection = build_name_reservation_projection(current_registry["entries"])
        if current_projection["source_semantic_sha256"] != projection["source_semantic_sha256"]:
            raise ACEError(
                "CanonRec name registry advanced during allocation; the candidate must be replanned",
                code="registry_baseline_advanced",
            )
        selected_normalized = normalize_name(resolution.canonical_name)
        if any(
            selected_normalized == normalize_name(str(existing))
            for row in current_registry["entries"]
            for existing in [row.get("canonical_name", ""), *row.get("aliases", [])]
        ):
            raise ACEError("Selected name collides after live registry revalidation", code="transaction_conflict")

        canonrec = (root / CANONREC_REL).resolve()
        entity_validation, entity_duration, entity_rc, entity_stderr = _run_json(
            [
                sys.executable,
                str(root / CANONREC_TOOL_REL / "validate_entity.py"),
                "--input",
                str(candidate_path),
                "--layer",
                "L2",
                "--type",
                "character",
                "--format",
                "json",
                "--context-root",
                str(canonrec),
            ],
            cwd=canonrec,
        )
        naming_validation, naming_duration, naming_rc, naming_stderr = _run_json(
            [
                sys.executable,
                str(root / CANONREC_TOOL_REL / "validate_naming_receipts.py"),
                str(candidate_path),
                "--registry",
                str(transaction_root / "evidence/canonrec_name_registry.json"),
                "--require-receipt",
                "--json",
            ],
            cwd=canonrec,
        )
        entity_validation = _replace_path_prefix(entity_validation, transaction_root)
        naming_validation = _replace_path_prefix(naming_validation, transaction_root)
        write_json(transaction_root / "receipts/entity_validation.json", entity_validation)
        write_json(transaction_root / "receipts/naming_validation.json", naming_validation)
        if entity_rc != 0 or entity_validation["validation_run"]["blocked"]:
            raise ACEError(f"CanonRec entity validation failed: {entity_stderr}", code="output_validation_failed")
        if naming_rc != 0 or naming_validation["blocks"]:
            raise ACEError(f"CanonRec naming validation failed: {naming_stderr}", code="output_validation_failed")

        query_schema_result = validate_json_schema(
            transaction_root / "query_envelope.json",
            root / "catalog/schemas/aurora_ace_query_envelope.schema.json",
            root,
        )
        query_schema_result = _replace_path_prefix(query_schema_result, transaction_root)
        write_json(transaction_root / "receipts/query_schema_validation.json", query_schema_result)
        if not query_schema_result["ok"]:
            raise ACEError("Compiled query failed its declared schema", code="output_validation_failed")

        answer = {
            "summary": (
                f"No prior character record was supplied. ACE instantiated {resolution.canonical_name} "
                f"as {candidate['role']} for {faction.name}, generated a verified CharForge capsule, "
                "and produced a CanonRec-valid commit-ready entity packet."
            ),
            "fields": [
                {
                    "field_path": "character.canonical_id",
                    "value": entity_id,
                    "origin": "deterministic_derivation",
                    "producer_refs": ["ace.capability.identity.allocate"],
                    "source_refs": [query["query_id"]],
                    "run_receipt_refs": ["receipts/character_state.json"],
                    "constraint_refs": ["ace.policy.contextual-referent-id.v1"],
                    "canon_target_ref": f"CanonRec:{canonical_target}",
                },
                {
                    "field_path": "character.canonical_name",
                    "value": resolution.canonical_name,
                    "origin": "specialist_tool_output",
                    "producer_refs": ["ace.capability.gumas.naming.resolve"],
                    "source_refs": list(query["subject"]["contextual_refs"]),
                    "run_receipt_refs": ["receipts/naming_receipt.json"],
                    "constraint_refs": ["GUMAS_NAMING_PROTOCOL_v0.1"],
                    "canon_target_ref": f"CanonRec:{canonical_target}",
                },
                {
                    "field_path": "character.role",
                    "value": candidate["role"],
                    "origin": "retrieved",
                    "producer_refs": ["ace.capability.context.resolve"],
                    "source_refs": list(query["subject"]["contextual_refs"]),
                    "run_receipt_refs": ["query_envelope.json"],
                    "constraint_refs": [str(context["faction_id"])],
                    "canon_target_ref": f"CanonRec:{canonical_target}",
                },
                {
                    "field_path": "character.background",
                    "value": background,
                    "origin": "connective_synthesis",
                    "producer_refs": [
                        "ace.capability.quantum_forge.charforge.generate_capsule",
                        "ace.capability.context.resolve",
                    ],
                    "source_refs": ["artifacts/charforge", *query["subject"]["contextual_refs"]],
                    "run_receipt_refs": ["receipts/character_state.json"],
                    "constraint_refs": ["ace.policy.connective-synthesis.v1"],
                    "canon_target_ref": f"CanonRec:{canonical_target}",
                },
                {
                    "field_path": "character.traits",
                    "value": traits,
                    "origin": "specialist_tool_output",
                    "producer_refs": ["ace.capability.quantum_forge.charforge.generate_capsule"],
                    "source_refs": [f"artifacts/charforge/{entity_id}/capsule/traits.json"],
                    "run_receipt_refs": [f"artifacts/charforge/{entity_id}/BUILD_RECEIPT.json"],
                    "constraint_refs": ["ORION Capsule Bundle Standard v0.2.0"],
                    "canon_target_ref": f"CanonRec:{canonical_target}/capsule/traits.json",
                },
                {
                    "field_path": "character.naming_receipt",
                    "value": naming_receipt,
                    "origin": "specialist_tool_output",
                    "producer_refs": ["ace.capability.gumas.naming.resolve"],
                    "source_refs": ["evidence/name_reservation_projection.json"],
                    "run_receipt_refs": ["receipts/naming_receipt.json"],
                    "constraint_refs": ["GUMAS_NAMING_PROTOCOL_v0.1"],
                    "canon_target_ref": f"CanonRec:{canonical_target}/naming_receipt.json",
                },
                {
                    "field_path": "character.canonical_target",
                    "value": canonical_target,
                    "origin": "deterministic_derivation",
                    "producer_refs": ["ace.capability.canonrec.materialize.entity"],
                    "source_refs": ["query_envelope.json"],
                    "run_receipt_refs": ["candidate/" + entity_id + ".json"],
                    "constraint_refs": ["ace.policy.delegated-routine-character-completion.v1"],
                    "canon_target_ref": f"CanonRec:{canonical_target}",
                },
            ],
            "no_prior_record": True,
            "supersedes_determination_refs": [],
        }
        coverage = [
            {
                "requirement_id": "ace.semantic.character.identity",
                "status": "satisfied",
                "field_refs": ["character.canonical_id", "character.canonical_name"],
                "producer_refs": ["ace.capability.identity.allocate", "ace.capability.gumas.naming.resolve"],
                "reason": "Stable ID allocation and the live naming receipt cover identity.",
            },
            {
                "requirement_id": "ace.semantic.character.current_context",
                "status": "satisfied",
                "field_refs": ["character.role", "character.background"],
                "producer_refs": ["ace.capability.context.resolve", "ace.capability.quantum_forge.charforge.generate_capsule"],
                "reason": "Resolved context and the CharForge identity synopsis cover role, faction, and duty context.",
            },
            {
                "requirement_id": "ace.semantic.character.operational_background",
                "status": "satisfied",
                "field_refs": ["character.background"],
                "producer_refs": ["ace.capability.quantum_forge.charforge.generate_capsule"],
                "reason": "The background is rendered only from context and CharForge knowledge records.",
            },
            {
                "requirement_id": "ace.semantic.character.behavioral_profile",
                "status": "satisfied",
                "field_refs": ["character.traits"],
                "producer_refs": ["ace.capability.quantum_forge.charforge.generate_capsule"],
                "reason": "CharForge traits and state vector cover values and decision tendencies.",
            },
            {
                "requirement_id": "ace.semantic.character.formative_biography",
                "status": "not_applicable",
                "field_refs": [],
                "producer_refs": [],
                "reason": "This MVP query requests operational background, not a separate formative biography.",
            },
        ]
        findings = [item["code"] for item in naming_validation["findings"]]
        projection_receipt = {
            "projection_id": projection["projection_id"],
            "projection_type": "name_reservation_occupancy",
            "source_repository": "CanonRec",
            "source_commit_sha": heads["CanonRec"],
            "source_semantic_sha256": projection["source_semantic_sha256"],
            "transform_id": projection["transform_id"],
            "transform_version": projection["transform_version"],
            "projection_sha256": projection["projection_sha256"],
            "source_member_count": projection["source_member_count"],
            "projected_member_count": projection["projected_member_count"],
            "collapsed_row_count": projection["collapsed_row_count"],
            "unresolved_relation_count": projection["unresolved_relation_count"],
            "membership_receipt_ref": "evidence/name_projection_membership.json",
        }
        steps = [
            _step(capabilities["ace.capability.context.resolve"], "context", heads["root"], status="succeeded", depends_on=[], consumes=["query.question", "query.subject.context"], produces=["resolved_context"], receipt_ref="query_envelope.json", output=context, seed=None, duration_ms=0.0),
            _step(capabilities["ace.capability.identity.allocate"], "identity", heads["root"], status="succeeded", depends_on=["ace.step.character.context"], consumes=["resolved_context"], produces=["character.canonical_id"], receipt_ref="receipts/character_state.json", output=entity_id, seed=seed, duration_ms=0.0),
            _step(capabilities["ace.capability.canonrec.project.name_reservations"], "name-projection", heads["root"], status="succeeded", depends_on=["ace.step.character.context"], consumes=["canonrec_raw_name_registry"], produces=["name_reservation_projection", "projection_membership_map"], receipt_ref="evidence/name_projection_membership.json", output={key: value for key, value in projection.items() if key != "membership"}, seed=None, duration_ms=0.0),
            _step(capabilities["ace.capability.gumas.naming.resolve"], "name", heads["aurora-cloudbank-symbolic-main"], status="succeeded", depends_on=["ace.step.character.identity", "ace.step.character.name-projection"], consumes=["character.canonical_id", "name_reservation_projection"], produces=["character.canonical_name", "character.naming_receipt"], receipt_ref="receipts/naming_receipt.json", output=naming_receipt, seed=seed, duration_ms=name_duration, side_effects=["reserved_generated_name_in_isolated_working_registry"]),
            _step(capabilities["ace.capability.gumas.state.build_character"], "state", heads["root"], status="succeeded", depends_on=["ace.step.character.identity", "ace.step.character.name"], consumes=["resolved_context", "character.canonical_name"], produces=["leader_state", "faction_state"], receipt_ref="receipts/character_state.json", output=state_receipt, seed=seed, duration_ms=state_duration),
            _step(capabilities["ace.capability.quantum_forge.charforge.generate_capsule"], "charforge", heads["root"], status="succeeded", depends_on=["ace.step.character.state"], consumes=["leader_state", "faction_state"], produces=["character.capsule", "character.traits", "character.background_knowledge"], receipt_ref=f"artifacts/charforge/{entity_id}/BUILD_RECEIPT.json", output={"semantic_capsule_sha256": _semantic_capsule_digest(bundle)}, seed=seed, duration_ms=forge_duration, side_effects=["wrote_capsule_bundle_to_transaction_workspace"], tool_statuses={"identity.certainty": identity["certainty"]}),
            _step(capabilities["ace.capability.canonrec.validate.entity"], "validate-entity", heads["CanonRec"], status="succeeded", depends_on=["ace.step.character.charforge"], consumes=["canonical_entity_candidate"], produces=["entity_validation_receipt"], receipt_ref="receipts/entity_validation.json", output=entity_validation, seed=None, duration_ms=entity_duration),
            _step(capabilities["ace.capability.canonrec.validate.naming_receipt"], "validate-name", heads["CanonRec"], status="succeeded", depends_on=["ace.step.character.name", "ace.step.character.validate-entity"], consumes=["canonical_entity_candidate", "canonrec_raw_name_registry"], produces=["naming_validation_receipt"], receipt_ref="receipts/naming_validation.json", output=naming_validation, seed=None, duration_ms=naming_duration),
            _step(capabilities["ace.capability.canonrec.materialize.entity"], "materialize", heads["CanonRec"], status="blocked", depends_on=["ace.step.character.validate-entity", "ace.step.character.validate-name"], consumes=["canonical_entity_candidate", "entity_validation_receipt", "naming_validation_receipt"], produces=[], receipt_ref=None, output=None, seed=None, duration_ms=None),
        ]
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "ace_determination_receipt",
            "determination_id": f"ace.determination.character.{query['query_id'].split('.')[-1]}",
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
            "baselines": [
                {key: item[key] for key in ("repository", "commit_sha", "authority_role")}
                for item in capability_index["baselines"]
            ],
            "subject_refs": [entity_id, *query["subject"]["contextual_refs"]],
            "answer_contract": {
                "compiler_version": query["answer_contract"]["compiler_version"],
                "overall_status": "complete",
                "coverage": coverage,
            },
            "projections": [projection_receipt],
            "transactions": [naming_transaction],
            "answer": answer,
            "plan": {
                "plan_id": f"ace.plan.character.{query['query_id'].split('.')[-1]}",
                "selection_basis": ["specialist_first", "registered_fleet_only", "deterministic_replay", "minimal_connective_synthesis"],
                "rejected_capability_refs": [],
                "steps": steps,
            },
            "validation": {
                "overall_status": "pass",
                "gates": [
                    {
                        "gate_id": "query_schema",
                        "status": "pass",
                        "validator_ref": "catalog/schemas/aurora_ace_query_envelope.schema.json",
                        "receipt_refs": ["receipts/query_schema_validation.json"],
                        "finding_codes": [],
                        "summary": "The compiled query satisfies the ACE query-envelope schema.",
                    },
                    {
                        "gate_id": "entity_schema",
                        "status": "pass",
                        "validator_ref": "ace.capability.canonrec.validate.entity",
                        "receipt_refs": ["receipts/entity_validation.json"],
                        "finding_codes": [],
                        "summary": "CanonRec accepted the L2 character candidate without blocking findings.",
                    },
                    {
                        "gate_id": "naming_protocol",
                        "status": "pass",
                        "validator_ref": "ace.capability.canonrec.validate.naming_receipt",
                        "receipt_refs": ["receipts/naming_validation.json", "receipts/naming_transaction.json"],
                        "finding_codes": findings,
                        "summary": "The name passed the live raw-registry collision gate; non-blocking crowding or projection-digest findings remain visible.",
                    },
                    {
                        "gate_id": "capsule_integrity",
                        "status": "pass",
                        "validator_ref": "ace.capability.quantum_forge.charforge.generate_capsule",
                        "receipt_refs": [f"artifacts/charforge/{entity_id}/BUILD_RECEIPT.json"],
                        "finding_codes": [],
                        "summary": "CharForge verified all emitted capsule hashes.",
                    },
                    {
                        "gate_id": "semantic_coverage",
                        "status": "pass",
                        "validator_ref": "ace.answer_contract.coverage.v0.1.1",
                        "receipt_refs": ["receipts/character_state.json", f"artifacts/charforge/{entity_id}/capsule/knowledge.jsonl"],
                        "finding_codes": [],
                        "summary": "All mandatory identity, context, operational-background, and behavioral semantics are satisfied.",
                    },
                ],
            },
            "conflicts": [],
            "blockers": [
                {
                    "blocker_id": "ace.blocker.materialization-authority",
                    "kind": "materialization_authority_missing",
                    "capability_ref": "ace.capability.canonrec.materialize.entity",
                    "reason": "This invocation was authorized to implement and test ACE, not to write or commit CanonRec canon.",
                    "recovery_action": "Review and commit the exact commit-ready packet through the authorized CanonRec workflow.",
                }
            ],
            "materialization": {
                "status": "commit_ready",
                "target_repository": "CanonRec",
                "target_paths": [canonical_target],
                "commit_sha": None,
                "gate_policy_ref": "ace.policy.delegated-routine-character-completion.v1",
                "commit_ready_packet_ref": ".",
            },
            "integrity": {},
            "replay": {
                "replayable": True,
                "deterministic": True,
                "replay_command": (
                    "python3 tools/aurora_ace.py resolve --query "
                    + shlex.quote(str(output / "query_envelope.json"))
                    + " --out "
                    + shlex.quote(str(output) + "-replay")
                ),
                "required_artifact_refs": ["query_envelope.json", "capability_index.json"],
                "non_replayable_reasons": [],
            },
        }
        artifact_index = _tree_artifacts(
            transaction_root,
            exclude={"determination_receipt.json", "artifact_index.json"},
        )
        write_json(transaction_root / "artifact_index.json", artifact_index)
        artifact_index_hash = file_sha256(transaction_root / "artifact_index.json")
        receipt["integrity"] = {
            "query_sha256": semantic_sha256(query),
            "capability_manifest_sha256s": sorted({capabilities[item]["manifest_sha256"] for item in required}),
            "answer_sha256": semantic_sha256(answer),
            "semantic_answer_sha256": semantic_sha256(strip_volatile_fields(answer)),
            "artifact_sha256s": sorted([*artifact_index.values(), artifact_index_hash]),
            "semantic_digest_policy_ref": "ace.policy.semantic-digest.v1",
            "prior_determination_digest": None,
        }
        write_json(transaction_root / "determination_receipt.json", receipt)
        receipt_schema_result = validate_json_schema(
            transaction_root / "determination_receipt.json",
            root / "catalog/schemas/aurora_ace_determination_receipt.schema.json",
            root,
        )
        receipt_schema_result = _replace_path_prefix(receipt_schema_result, transaction_root)
        write_json(transaction_root / "receipts/determination_schema_validation.json", receipt_schema_result)
        if not receipt_schema_result["ok"]:
            raise ACEError(
                "Determination receipt failed its declared schema: "
                + json.dumps(receipt_schema_result["errors"][:3]),
                code="output_validation_failed",
            )
        # The schema receipt is itself durable evidence. Add it to the artifact
        # index, then rewrite and revalidate the final integrity block. The
        # schema report contains only validation outcome and stable packet paths,
        # so the second validation is byte-identical to the first.
        artifact_index = _tree_artifacts(
            transaction_root,
            exclude={"determination_receipt.json", "artifact_index.json"},
        )
        write_json(transaction_root / "artifact_index.json", artifact_index)
        artifact_index_hash = file_sha256(transaction_root / "artifact_index.json")
        receipt["integrity"]["artifact_sha256s"] = sorted(
            [*artifact_index.values(), artifact_index_hash]
        )
        write_json(transaction_root / "determination_receipt.json", receipt)
        final_schema_result = validate_json_schema(
            transaction_root / "determination_receipt.json",
            root / "catalog/schemas/aurora_ace_determination_receipt.schema.json",
            root,
        )
        final_schema_result = _replace_path_prefix(final_schema_result, transaction_root)
        if not final_schema_result["ok"]:
            raise ACEError("Final determination integrity rewrite failed schema validation", code="output_validation_failed")
        write_json(transaction_root / "receipts/determination_schema_validation.json", final_schema_result)

        budgets = query["execution_policy"]["budgets"]
        elapsed = time.perf_counter() - execution_started
        if elapsed > budgets["max_wall_seconds"]:
            raise ACEError(
                f"ACE execution exceeded max_wall_seconds ({elapsed:.3f}s > {budgets['max_wall_seconds']}s)",
                code="budget_exhausted",
            )
        output_bytes = sum(path.stat().st_size for path in transaction_root.rglob("*") if path.is_file())
        if output_bytes > budgets["max_output_bytes"]:
            raise ACEError(
                f"ACE packet exceeded max_output_bytes ({output_bytes} > {budgets['max_output_bytes']})",
                code="budget_exhausted",
            )
        os.replace(transaction_root, output)
        return receipt
    except Exception:
        shutil.rmtree(transaction_root, ignore_errors=True)
        raise

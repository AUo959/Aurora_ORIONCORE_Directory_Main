"""Atomic native CanonRec materialization for ACE character packets.

ACE v0.5 publishes an already validated, genuinely new character as one Git
transaction. It does not generate truth during publication. The source
``EXECUTION_BLOCKED`` determination must already be complete, validation-clean,
and blocked only on materialization authority.

The transaction writes the native CanonRec character surfaces together:

- the full seven-file CharForge capsule;
- ``bundle.manifest.json`` and ``BUILD_RECEIPT.json``;
- the GUMAS naming receipt;
- the flat ``canon/L2/entities/characters/<id>.json`` discovery record with an
  explicit capsule bridge.

If any target already exists, any identity/capsule relationship is inconsistent,
validation fails, the Git commit fails, the final receipt fails schema validation,
or the final ledger append fails, the target repository is restored to its exact
entry baseline and no materialized sidecar survives.
"""

from __future__ import annotations

import copy
import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any, Mapping

from .core import (
    ACEError,
    ROOT,
    file_sha256,
    load_json,
    normalize_name,
    semantic_sha256,
    utc_now,
    validate_json_schema,
)
from .character_retrieval import _record_from_flat_entity
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
    materialize_facility_packet,
)

CHARACTER_MATERIALIZER_VERSION = "0.5.0"
CHARACTER_TARGET_ROOT = Path("canon/L2/entities")
CHARACTER_INDEX_ROOT = CHARACTER_TARGET_ROOT / "characters"
CAPSULE_FILES = (
    "identity.json",
    "traits.json",
    "knowledge.jsonl",
    "cns.yaml",
    "state.bin",
    "runtime.py",
    "manifest.json",
)
CAPSULE_HASHED_FILES = tuple(name for name in CAPSULE_FILES if name != "manifest.json")
OUTER_BUNDLE_FILES = ("bundle.manifest.json", "BUILD_RECEIPT.json")


def _assert_authority(authority_mode: str, authority_ref: str) -> None:
    if authority_mode not in AUTHORITY_MODES:
        raise ACEError(
            f"authority_mode must be one of {sorted(AUTHORITY_MODES)}",
            code="materialization_authority_missing",
        )
    if not isinstance(authority_ref, str) or not authority_ref.strip():
        raise ACEError(
            "materialization requires a non-empty authority_ref",
            code="materialization_authority_missing",
        )


def _character_target(receipt: Mapping[str, Any], repo: Path) -> tuple[str, str, Path, str, Path]:
    materialization = receipt.get("materialization", {})
    if materialization.get("target_repository") != SUPPORTED_TARGET_REPOSITORY:
        raise ACEError("character materializer supports CanonRec only", code="target_unavailable")
    paths = materialization.get("target_paths", [])
    if not isinstance(paths, list) or len(paths) != 1 or not isinstance(paths[0], str):
        raise ACEError(
            "character materialization requires one canonical entity-directory target",
            code="input_validation_failed",
        )
    rel = Path(paths[0])
    if rel.is_absolute() or ".." in rel.parts:
        raise ACEError("character target path is unsafe", code="target_unavailable")
    if rel.parent != CHARACTER_TARGET_ROOT:
        raise ACEError(
            f"character target must be directly under {CHARACTER_TARGET_ROOT.as_posix()}",
            code="target_unavailable",
        )
    entity_id = rel.name
    if not entity_id.startswith("char_"):
        raise ACEError("character target must use a char_ canonical ID", code="input_validation_failed")

    target = (repo / rel).resolve()
    flat_rel = (CHARACTER_INDEX_ROOT / f"{entity_id}.json").as_posix()
    flat = (repo / flat_rel).resolve()
    repo_resolved = repo.resolve()
    for path in (target, flat):
        if path == repo_resolved or repo_resolved not in path.parents:
            raise ACEError("character target escapes CanonRec", code="target_unavailable")
    return entity_id, rel.as_posix(), target, flat_rel, flat


def _packet_sources(packet: Path, entity_id: str) -> tuple[Path, Path, Path, Path]:
    candidate = packet / "candidate" / f"{entity_id}.json"
    bundle = packet / "artifacts" / "charforge" / entity_id
    query = packet / "query_envelope.json"
    naming = packet / "receipts" / "naming_receipt.json"
    required = [candidate, query, naming, *(bundle / "capsule" / name for name in CAPSULE_FILES)]
    required.extend(bundle / name for name in OUTER_BUNDLE_FILES)
    missing = [path.relative_to(packet).as_posix() for path in required if not path.is_file()]
    if missing:
        raise ACEError(
            "character packet is incomplete: " + ", ".join(sorted(missing)),
            code="target_unavailable",
        )
    return candidate, bundle, query, naming


def _assert_new_targets(target: Path, flat: Path) -> None:
    existing = [path for path in (target, flat) if path.exists()]
    if existing:
        raise ACEError(
            "native character materialization is new-character-only; existing canonical targets require retrieval/reconciliation: "
            + ", ".join(str(path) for path in existing),
            code="transaction_conflict",
        )


def _assert_name_available(repo: Path, candidate: Mapping[str, Any]) -> None:
    requested = {
        normalize_name(str(name))
        for name in [candidate.get("canonical_name", ""), *candidate.get("aliases", [])]
        if normalize_name(str(name))
    }
    for path in sorted((repo / CHARACTER_INDEX_ROOT).glob("*.json")):
        try:
            row = load_json(path)
        except Exception as exc:
            raise ACEError(f"cannot inspect CanonRec character registry entry {path}", code="runtime_failure") from exc
        if not isinstance(row, dict):
            continue
        existing = {
            normalize_name(str(name))
            for name in [row.get("name", ""), *row.get("aliases", [])]
            if normalize_name(str(name))
        }
        collision = requested & existing
        if collision:
            raise ACEError(
                f"character name/alias collides with existing canonical registry entry {path.relative_to(repo).as_posix()}",
                code="transaction_conflict",
            )


def _atomic_copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".ace-character-", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(source.read_bytes())
        os.replace(temp_name, target)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def _canonicalize_capsule(
    bundle: Path,
    target: Path,
    *,
    entity_id: str,
    candidate: Mapping[str, Any],
    receipt: Mapping[str, Any],
    authority_ref: str,
) -> None:
    source_capsule = bundle / "capsule"
    target_capsule = target / "capsule"
    for name in CAPSULE_FILES:
        _atomic_copy(source_capsule / name, target_capsule / name)
    for name in OUTER_BUNDLE_FILES:
        _atomic_copy(bundle / name, target / name)

    identity = load_json(target_capsule / "identity.json")
    if not isinstance(identity, dict):
        raise ACEError("CharForge identity must be a JSON object", code="output_validation_failed")
    expected_name = str(candidate.get("canonical_name") or "")
    checks = {
        "capsule_id": entity_id,
        "character_name": expected_name,
        "faction_id": str(candidate.get("faction") or ""),
    }
    for field, expected in checks.items():
        if str(identity.get(field) or "") != expected:
            raise ACEError(
                f"CharForge identity {field} does not match the canonical candidate",
                code="output_validation_failed",
            )
    if str(identity.get("declared_layer") or "") != "L2":
        raise ACEError("character capsule must declare L2", code="output_validation_failed")

    identity["certainty"] = "CANON"
    identity["governance_verdict"] = "PROMOTE"
    identity["ace_materialization"] = {
        "query_id": receipt["query_id"],
        "source_determination_id": receipt["determination_id"],
        "materializer_version": CHARACTER_MATERIALIZER_VERSION,
        "materialization_authority_ref": authority_ref,
    }
    _write_json_atomic(target_capsule / "identity.json", identity)

    manifest = load_json(target_capsule / "manifest.json")
    if not isinstance(manifest, dict):
        raise ACEError("CharForge capsule manifest must be a JSON object", code="output_validation_failed")
    manifest["records"] = [
        {"path": name, "sha256": file_sha256(target_capsule / name)}
        for name in CAPSULE_HASHED_FILES
    ]
    _write_json_atomic(target_capsule / "manifest.json", manifest)


def _verify_capsule(target: Path) -> None:
    capsule = target / "capsule"
    missing = [name for name in CAPSULE_FILES if not (capsule / name).is_file()]
    if missing:
        raise ACEError("materialized capsule is incomplete: " + ", ".join(missing), code="output_validation_failed")
    manifest = load_json(capsule / "manifest.json")
    records = {str(row.get("path")): str(row.get("sha256")) for row in manifest.get("records", [])}
    for name in CAPSULE_HASHED_FILES:
        if records.get(name) != file_sha256(capsule / name):
            raise ACEError(f"materialized capsule hash mismatch for {name}", code="output_validation_failed")


def _flat_record(
    candidate: Mapping[str, Any],
    query: Mapping[str, Any],
    receipt: Mapping[str, Any],
    *,
    entity_id: str,
    target_rel: str,
    naming_receipt: Mapping[str, Any],
    authority_ref: str,
) -> dict[str, Any]:
    context = query.get("subject", {}).get("context", {})
    now = utc_now()
    faction = str(candidate.get("faction") or "")
    return {
        "entity_kind": "character",
        "entity_id": entity_id,
        "name": str(candidate.get("canonical_name") or ""),
        "aliases": list(candidate.get("aliases", [])),
        "certainty": "CANON",
        "status": "active",
        "faction_bindings": [faction] if faction else [],
        "organization_ids": list(context.get("organization_ids", [])),
        "conflict_flags": [],
        "role": str(candidate.get("role") or ""),
        "org_type": None,
        "parent_org_id": context.get("parent_org_id"),
        "location_type": context.get("location_type"),
        "region_id": context.get("region_id") or context.get("location_ref"),
        "canonical_position_status": None,
        "capsule_ref": f"{target_rel}/capsule/",
        "capsule_id": entity_id,
        "capsule_binding_note": "ACE v0.5 explicit bridge between the flat character discovery record and the native CharForge capsule.",
        "naming_receipt": dict(naming_receipt),
        "naming_receipt_ref": f"{target_rel}/naming_receipt.json",
        "doc_sources": [
            f"{target_rel}/capsule/identity.json (ACE materialized canonical capsule)",
            f"ACE determination {receipt['determination_id']}",
        ],
        "promotion_pass": "ACE Native Character Materialization v0.5",
        "locked_at": now,
        "updated_at": now[:10],
        "notes": "Generated only after ACE retrieval-first preflight established no plausible existing canonical referent; published atomically with the complete capsule and naming receipt.",
        "ace_provenance": {
            "query_id": receipt["query_id"],
            "source_determination_id": receipt["determination_id"],
            "materializer_version": CHARACTER_MATERIALIZER_VERSION,
            "materialization_authority_ref": authority_ref,
        },
    }


def _validate_flat_entity(
    flat: Path,
    repo: Path,
    *,
    entity_id: str,
    candidate: Mapping[str, Any],
    target_rel: str,
) -> None:
    """Validate the native flat registry record with ACE v0.4 retrieval semantics."""

    record, capsule_ref = _record_from_flat_entity(flat, repo)
    if record is None:
        raise ACEError(
            "native flat character record is not readable by the ACE character registry",
            code="output_validation_failed",
        )
    expected_capsule_ref = f"{target_rel}/capsule/identity.json"
    expected_name = str(candidate.get("canonical_name") or "")
    expected_faction = str(candidate.get("faction") or "")
    if record.canonical_id != entity_id:
        raise ACEError("flat character canonical ID does not match the packet", code="output_validation_failed")
    if normalize_name(record.name) != normalize_name(expected_name):
        raise ACEError("flat character name does not match the packet", code="output_validation_failed")
    if record.certainty != "CANON":
        raise ACEError("flat character must be readable as CANON", code="output_validation_failed")
    if expected_faction and record.faction_id != expected_faction:
        raise ACEError("flat character faction does not match the packet", code="output_validation_failed")
    if capsule_ref != expected_capsule_ref:
        raise ACEError(
            "flat character capsule bridge does not resolve to the materialized capsule",
            code="output_validation_failed",
        )
    if record.identity_sha256 != file_sha256(flat):
        raise ACEError("flat character registry digest is unstable", code="output_validation_failed")


def _target_hashes(repo: Path, target_rel: str, flat_rel: str) -> dict[str, str]:
    paths = [
        *(f"{target_rel}/capsule/{name}" for name in CAPSULE_FILES),
        *(f"{target_rel}/{name}" for name in OUTER_BUNDLE_FILES),
        f"{target_rel}/naming_receipt.json",
        flat_rel,
    ]
    return {path: file_sha256(repo / path) for path in sorted(paths)}


def _final_receipt(
    original: Mapping[str, Any],
    *,
    commit_sha: str,
    target_hashes: Mapping[str, str],
    entity_id: str,
    authority_mode: str,
    authority_ref: str,
    elapsed_ms: float,
) -> dict[str, Any]:
    final = copy.deepcopy(dict(original))
    prior_id = str(original["determination_id"])
    final["determination_id"] = f"{prior_id}.materialized.{commit_sha[:12]}"
    final["created_at"] = utc_now()
    final["engine"]["execution_mode"] = authority_mode
    final["status"] = "GENERATED_CANON"
    supersedes = list(final["answer"].get("supersedes_determination_refs", []))
    if prior_id not in supersedes:
        supersedes.append(prior_id)
    final["answer"]["supersedes_determination_refs"] = supersedes
    final["blockers"] = []
    final["materialization"]["status"] = "committed"
    final["materialization"]["commit_sha"] = commit_sha
    final["materialization"]["target_paths"] = sorted(target_hashes)

    result_digest = semantic_sha256(dict(sorted(target_hashes.items())))
    absence_digest = semantic_sha256({"entity_id": entity_id, "state": "all_targets_absent"})
    transaction = {
        "transaction_id": f"ace.transaction.materialization.{commit_sha[:16]}",
        "kind": "materialization",
        "scope": f"CanonRec:character:{entity_id}",
        "baseline_sha256": absence_digest,
        "result_sha256": result_digest,
        "concurrency_policy": "optimistic_compare_and_swap",
        "revalidation_status": "pass",
        "side_effects": ["wrote_canonical_character_artifact_set", "created_git_commit"],
        "receipt_ref": f"CanonRec:character:{entity_id}@{commit_sha}",
    }
    final["transactions"] = [*final.get("transactions", []), transaction]

    materialize_step = next(
        (
            step
            for step in final.get("plan", {}).get("steps", [])
            if step.get("capability_id") == "ace.capability.canonrec.materialize.entity"
        ),
        None,
    )
    if materialize_step is None:
        raise ACEError("determination plan has no CanonRec materializer step", code="invalid_manifest")
    materialize_step["status"] = "succeeded"
    materialize_step["tool_run_id"] = f"ace-run-character-materialization-{commit_sha[:12]}"
    materialize_step["run_receipt_ref"] = f"CanonRec:character:{entity_id}@{commit_sha}"
    materialize_step["duration_ms"] = elapsed_ms
    materialize_step["output_sha256"] = result_digest
    materialize_step["semantic_output_sha256"] = result_digest
    materialize_step["artifact_output_sha256"] = result_digest
    materialize_step["side_effects_observed"] = [
        "wrote_canonical_character_artifact_set",
        "created_git_commit",
    ]
    materialize_step["produces"] = sorted(target_hashes)

    final["integrity"]["prior_determination_digest"] = semantic_sha256(original)
    final["integrity"]["artifact_sha256s"] = sorted(
        set([*final["integrity"].get("artifact_sha256s", []), *target_hashes.values()])
    )
    final["replay"] = {
        "replayable": False,
        "deterministic": True,
        "replay_command": None,
        "required_artifact_refs": [
            "determination_receipt.json",
            f"candidate/{entity_id}.json",
            f"artifacts/charforge/{entity_id}/BUILD_RECEIPT.json",
            f"artifacts/charforge/{entity_id}/bundle.manifest.json",
            f"artifacts/charforge/{entity_id}/capsule/manifest.json",
            "receipts/naming_receipt.json",
        ],
        "non_replayable_reasons": [
            "Git commit identity and publication timestamp are materialization metadata; replay the semantic source packet instead."
        ],
    }
    final["materialization"]["gate_policy_ref"] = (
        str(final["materialization"].get("gate_policy_ref") or "")
        + f"; authority_ref={authority_ref}"
    ).strip("; ")
    return final


def materialize_character_packet(
    packet_dir: Path,
    target_repo: Path,
    *,
    authority_mode: str,
    authority_ref: str,
    ledger_dir: Path | None = None,
    root: Path = ROOT,
    commit_message: str | None = None,
) -> dict[str, Any]:
    """Commit a complete new character artifact set as one CanonRec transaction."""

    _assert_authority(authority_mode, authority_ref)
    packet = packet_dir.expanduser().resolve()
    repo = target_repo.expanduser().resolve()
    receipt_path = packet / "determination_receipt.json"
    if not receipt_path.is_file():
        raise ACEError("character packet is missing determination_receipt.json", code="target_unavailable")
    receipt = _validate_receipt(receipt_path, root=root)
    _assert_commit_ready(receipt)
    if receipt.get("simulation_mode") != "constitutive_generation" or not receipt.get("answer", {}).get("no_prior_record"):
        raise ACEError(
            "native character materialization requires a constitutive new-character determination",
            code="input_validation_failed",
        )

    _, baseline_head = _assert_clean_feature_branch(repo)
    expected_head = _canonrec_baseline(receipt)
    if baseline_head != expected_head:
        raise ACEError(
            f"CanonRec baseline advanced ({expected_head} -> {baseline_head}); recompile before materialization",
            code="registry_baseline_advanced",
        )

    entity_id, target_rel, target, flat_rel, flat = _character_target(receipt, repo)
    _assert_new_targets(target, flat)
    candidate_path, bundle, query_path, naming_path = _packet_sources(packet, entity_id)
    candidate = load_json(candidate_path)
    query = load_json(query_path)
    naming = load_json(naming_path)
    if not isinstance(candidate, dict) or candidate.get("entity_kind") != "character":
        raise ACEError("character candidate must be a character JSON object", code="input_validation_failed")
    if candidate.get("canonical_id") != entity_id or candidate.get("certainty") != "CANON_PROMOTE":
        raise ACEError("character candidate identity/certainty does not match the commit target", code="output_validation_failed")
    if not isinstance(query, dict) or query.get("subject", {}).get("entity_type") != "character":
        raise ACEError("character packet query envelope is invalid", code="input_validation_failed")
    if not isinstance(naming, dict):
        raise ACEError("character naming receipt must be a JSON object", code="input_validation_failed")
    _assert_name_available(repo, candidate)

    append_determination(receipt, ledger_dir, root=root)
    materialized_receipt_path: Path | None = None
    started = time.perf_counter()
    try:
        _canonicalize_capsule(
            bundle,
            target,
            entity_id=entity_id,
            candidate=candidate,
            receipt=receipt,
            authority_ref=authority_ref.strip(),
        )
        _verify_capsule(target)
        _atomic_copy(naming_path, target / "naming_receipt.json")
        _write_json_atomic(
            flat,
            _flat_record(
                candidate,
                query,
                receipt,
                entity_id=entity_id,
                target_rel=target_rel,
                naming_receipt=naming,
                authority_ref=authority_ref.strip(),
            ),
        )
        _validate_flat_entity(
            flat,
            repo,
            entity_id=entity_id,
            candidate=candidate,
            target_rel=target_rel,
        )

        hashes = _target_hashes(repo, target_rel, flat_rel)
        _git(repo, "add", "--", target_rel, flat_rel)
        staged = set(_git(repo, "diff", "--cached", "--name-only").splitlines())
        expected = set(hashes)
        if staged != expected:
            raise ACEError(
                "character materialization staged an unexpected artifact set",
                code="runtime_failure",
            )
        message = commit_message or f"feat(canon): materialize ACE character {entity_id}"
        _git(
            repo,
            "-c",
            "user.name=Aurora ACE Materializer",
            "-c",
            "user.email=ace@aurora.local",
            "commit",
            "-m",
            message,
        )
        commit_sha = _git(repo, "rev-parse", "HEAD")
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        final = _final_receipt(
            receipt,
            commit_sha=commit_sha,
            target_hashes=hashes,
            entity_id=entity_id,
            authority_mode=authority_mode,
            authority_ref=authority_ref.strip(),
            elapsed_ms=elapsed_ms,
        )
        with tempfile.TemporaryDirectory(prefix="ace-character-materialized-schema-") as temp:
            final_path = Path(temp) / "receipt.json"
            final_path.write_text(json.dumps(final, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            report = validate_json_schema(
                final_path,
                root / "catalog/schemas/aurora_ace_determination_receipt.schema.json",
                root,
            )
        if not report["ok"]:
            raise ACEError(
                "materialized character determination failed schema validation: "
                + json.dumps(report["errors"][:3]),
                code="output_validation_failed",
            )
        materialized_receipt_path = packet / "materialized_determination_receipt.json"
        _write_json_atomic(materialized_receipt_path, final)
        append_determination(final, ledger_dir, root=root)
        return final
    except Exception:
        if materialized_receipt_path is not None and materialized_receipt_path.exists():
            try:
                materialized_receipt_path.unlink()
            except OSError:
                pass
        try:
            _git(repo, "reset", "--hard", baseline_head, check=False)
            _git(repo, "clean", "-fd", "--", target_rel, flat_rel, check=False)
            if target.exists():
                shutil.rmtree(target, ignore_errors=True)
            if flat.exists():
                flat.unlink()
        except Exception:
            pass
        raise


def materialize_packet(
    packet_dir: Path,
    target_repo: Path,
    *,
    authority_mode: str,
    authority_ref: str,
    ledger_dir: Path | None = None,
    root: Path = ROOT,
    commit_message: str | None = None,
) -> dict[str, Any]:
    """Dispatch an ACE commit-ready packet to its native materializer."""

    packet = packet_dir.expanduser().resolve()
    if (packet / "candidate_facility_binding.json").is_file():
        return materialize_facility_packet(
            packet,
            target_repo,
            authority_mode=authority_mode,
            authority_ref=authority_ref,
            ledger_dir=ledger_dir,
            root=root,
            commit_message=commit_message,
        )
    if (packet / "candidate").is_dir() and (packet / "artifacts" / "charforge").is_dir():
        return materialize_character_packet(
            packet,
            target_repo,
            authority_mode=authority_mode,
            authority_ref=authority_ref,
            ledger_dir=ledger_dir,
            root=root,
            commit_message=commit_message,
        )
    raise ACEError("ACE packet type is not materializable by the registered native materializers", code="target_unavailable")

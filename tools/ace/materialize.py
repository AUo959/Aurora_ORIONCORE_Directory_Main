"""Authorized ACE materialization for validated L1 facility-binding packets.

This is intentionally narrow. The v0.2 slice materializes only the facility
binding produced by ``tools.ace.facility``. Character packets remain commit-ready
until their multi-artifact CanonRec serializer is implemented.

Materialization is a repository transaction, not a truth-generation step:
- the determination must already be complete and validation-clean;
- the target CanonRec checkout must still be at the receipt baseline;
- an explicit delegated/owner-gated authority reference is required;
- the target checkout must be on a non-protected feature branch and clean;
- only the declared canonical target path may be written;
- no runtime, activation, experiment, or exact-geometry authority is widened;
- the pre-materialization and post-materialization determinations are both
  retained in the append-only ledger.
"""

from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Mapping

from .core import (
    ACEError,
    ROOT,
    file_sha256,
    load_json,
    semantic_sha256,
    utc_now,
    validate_json_schema,
)
from .ledger import append_determination

MATERIALIZER_VERSION = "0.2.0"
SUPPORTED_TARGET_REPOSITORY = "CanonRec"
SUPPORTED_PACKET_RECORD = "ace_l1_facility_binding_candidate"
CANONICAL_RECORD_TYPE = "l1_facility_binding"
CANONICAL_SCHEMA_VERSION = "1.0.0"
PROTECTED_BRANCHES = {"main", "master"}
FACILITY_TARGET_PREFIX = Path("canon/L1/station/facility_bindings")
AUTHORITY_MODES = {"delegated_materialize", "owner_gated_materialize"}


def _git(repo: Path, *args: str, check: bool = True) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and completed.returncode != 0:
        raise ACEError(
            f"git {' '.join(args)} failed in {repo}: {completed.stderr.strip()}",
            code="runtime_failure",
        )
    return completed.stdout.strip()


def _assert_clean_feature_branch(repo: Path) -> tuple[str, str]:
    if not (repo / ".git").exists():
        raise ACEError(f"target is not a Git repository: {repo}", code="target_unavailable")
    status = _git(repo, "status", "--porcelain")
    if status:
        raise ACEError("CanonRec materialization requires a clean target worktree", code="transaction_conflict")
    branch = _git(repo, "branch", "--show-current")
    if not branch:
        raise ACEError("CanonRec materialization refuses detached HEAD", code="transaction_conflict")
    if branch in PROTECTED_BRANCHES:
        raise ACEError(
            f"CanonRec materialization refuses protected branch {branch!r}; use a feature branch and PR",
            code="materialization_authority_missing",
        )
    return branch, _git(repo, "rev-parse", "HEAD")


def _validate_receipt(receipt_path: Path, *, root: Path) -> dict[str, Any]:
    receipt = load_json(receipt_path)
    if not isinstance(receipt, dict):
        raise ACEError("determination receipt must be a JSON object", code="input_validation_failed")
    report = validate_json_schema(
        receipt_path,
        root / "catalog/schemas/aurora_ace_determination_receipt.schema.json",
        root,
    )
    if not report["ok"]:
        raise ACEError(
            "commit-ready determination failed schema validation: "
            + json.dumps(report["errors"][:3]),
            code="output_validation_failed",
        )
    return receipt


def _canonrec_baseline(receipt: Mapping[str, Any]) -> str:
    for item in receipt.get("baselines", []):
        if item.get("repository") == SUPPORTED_TARGET_REPOSITORY:
            value = item.get("commit_sha")
            if isinstance(value, str) and re.fullmatch(r"[a-f0-9]{40}", value):
                return value
    raise ACEError("determination does not contain a CanonRec baseline", code="input_validation_failed")


def _safe_target_path(receipt: Mapping[str, Any], repo: Path) -> tuple[str, Path]:
    materialization = receipt.get("materialization", {})
    if materialization.get("target_repository") != SUPPORTED_TARGET_REPOSITORY:
        raise ACEError("v0.2 materializer supports CanonRec only", code="target_unavailable")
    paths = materialization.get("target_paths", [])
    if not isinstance(paths, list) or len(paths) != 1 or not isinstance(paths[0], str):
        raise ACEError("v0.2 facility materialization requires exactly one target path", code="input_validation_failed")
    rel = Path(paths[0])
    if rel.is_absolute() or ".." in rel.parts:
        raise ACEError("materialization target path is unsafe", code="target_unavailable")
    try:
        rel.relative_to(FACILITY_TARGET_PREFIX)
    except ValueError as exc:
        raise ACEError(
            f"v0.2 facility materializer refuses non-facility target {rel.as_posix()}",
            code="target_unavailable",
        ) from exc
    target = (repo / rel).resolve()
    repo_resolved = repo.resolve()
    if target == repo_resolved or repo_resolved not in target.parents:
        raise ACEError("materialization target escapes CanonRec", code="target_unavailable")
    return rel.as_posix(), target


def _assert_commit_ready(receipt: Mapping[str, Any]) -> None:
    if receipt.get("status") != "EXECUTION_BLOCKED":
        raise ACEError("materializer expects an EXECUTION_BLOCKED commit-ready determination", code="input_validation_failed")
    if receipt.get("answer_contract", {}).get("overall_status") != "complete":
        raise ACEError("materializer refuses incomplete answer contract", code="semantic_coverage_incomplete")
    if receipt.get("validation", {}).get("overall_status") != "pass":
        raise ACEError("materializer refuses a determination that did not pass validation", code="output_validation_failed")
    if receipt.get("materialization", {}).get("status") != "commit_ready":
        raise ACEError("determination is not commit-ready", code="input_validation_failed")
    blockers = receipt.get("blockers", [])
    unsupported = [item for item in blockers if item.get("kind") != "materialization_authority_missing"]
    if unsupported:
        raise ACEError(
            "materializer cannot bypass non-authority blockers: "
            + ", ".join(str(item.get("kind")) for item in unsupported),
            code="output_validation_failed",
        )


def _canonical_facility_record(
    candidate: Mapping[str, Any],
    receipt: Mapping[str, Any],
    *,
    authority_ref: str,
) -> dict[str, Any]:
    if candidate.get("record_type") != SUPPORTED_PACKET_RECORD:
        raise ACEError("v0.2 materializer supports ACE facility-binding candidates only", code="input_validation_failed")
    for flag in ("causal_use_permitted", "activation_authority", "exact_geometry_authorized"):
        if candidate.get(flag) is not False:
            raise ACEError(f"facility candidate attempts to widen {flag}", code="output_validation_failed")
    required_strings = (
        "subject_ref",
        "component",
        "l1_kind",
        "canonical_location",
        "location_scope",
        "generation_policy_ref",
    )
    for field in required_strings:
        if not isinstance(candidate.get(field), str) or not str(candidate[field]).strip():
            raise ACEError(f"facility candidate requires non-empty {field}", code="output_validation_failed")

    return {
        "schema_version": CANONICAL_SCHEMA_VERSION,
        "record_type": CANONICAL_RECORD_TYPE,
        "subject_ref": candidate["subject_ref"],
        "component": candidate["component"],
        "l1_kind": candidate["l1_kind"],
        "canonical_location": candidate["canonical_location"],
        "location_scope": candidate["location_scope"],
        "certainty": "CANON",
        "causal_use_permitted": False,
        "activation_authority": False,
        "exact_geometry_authorized": False,
        "source_refs": list(candidate.get("source_refs", [])),
        "ace_provenance": {
            "query_id": receipt["query_id"],
            "source_determination_id": receipt["determination_id"],
            "generation_policy_ref": candidate["generation_policy_ref"],
            "materializer_version": MATERIALIZER_VERSION,
            "materialization_authority_ref": authority_ref,
        },
    }


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".ace-materialize-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def _final_receipt(
    original: Mapping[str, Any],
    *,
    commit_sha: str,
    target_path: str,
    target_existed: bool,
    target_hash: str,
    baseline_target_hash: str,
    authority_mode: str,
    authority_ref: str,
    elapsed_ms: float,
) -> dict[str, Any]:
    final = copy.deepcopy(dict(original))
    prior_id = str(original["determination_id"])
    final["determination_id"] = f"{prior_id}.materialized.{commit_sha[:12]}"
    final["created_at"] = utc_now()
    final["engine"]["execution_mode"] = authority_mode
    final["status"] = "CANON_REVISION" if target_existed else "GENERATED_CANON"
    supersedes = list(final["answer"].get("supersedes_determination_refs", []))
    if prior_id not in supersedes:
        supersedes.append(prior_id)
    final["answer"]["supersedes_determination_refs"] = supersedes
    final["blockers"] = []
    final["materialization"]["status"] = "committed"
    final["materialization"]["commit_sha"] = commit_sha

    transaction = {
        "transaction_id": f"ace.transaction.materialization.{commit_sha[:16]}",
        "kind": "materialization",
        "scope": f"CanonRec:{target_path}",
        "baseline_sha256": baseline_target_hash,
        "result_sha256": target_hash,
        "concurrency_policy": "optimistic_compare_and_swap",
        "revalidation_status": "pass",
        "side_effects": ["wrote_canonical_target", "created_git_commit"],
        "receipt_ref": f"CanonRec:{target_path}@{commit_sha}",
    }
    final["transactions"] = [*final.get("transactions", []), transaction]

    materialize_step = None
    for step in final.get("plan", {}).get("steps", []):
        if step.get("capability_id") == "ace.capability.canonrec.materialize.entity":
            materialize_step = step
            break
    if materialize_step is None:
        raise ACEError("determination plan has no CanonRec materializer step", code="invalid_manifest")
    materialize_step["status"] = "succeeded"
    materialize_step["tool_run_id"] = f"ace-run-materialization-{commit_sha[:12]}"
    materialize_step["run_receipt_ref"] = f"CanonRec:{target_path}@{commit_sha}"
    materialize_step["duration_ms"] = elapsed_ms
    materialize_step["output_sha256"] = target_hash
    materialize_step["semantic_output_sha256"] = target_hash
    materialize_step["artifact_output_sha256"] = target_hash
    materialize_step["side_effects_observed"] = ["wrote_canonical_target", "created_git_commit"]
    if target_path not in materialize_step.get("produces", []):
        materialize_step["produces"] = [*materialize_step.get("produces", []), target_path]

    final["integrity"]["prior_determination_digest"] = semantic_sha256(original)
    hashes = list(final["integrity"].get("artifact_sha256s", []))
    if target_hash not in hashes:
        hashes.append(target_hash)
    final["integrity"]["artifact_sha256s"] = sorted(set(hashes))
    final["replay"] = {
        "replayable": False,
        "deterministic": True,
        "replay_command": None,
        "required_artifact_refs": ["determination_receipt.json", "candidate_facility_binding.json"],
        "non_replayable_reasons": [
            "Git commit identity and timestamp are publication metadata; replay the semantic candidate from the prior determination instead."
        ],
    }
    final["materialization"]["gate_policy_ref"] = (
        str(final["materialization"].get("gate_policy_ref") or "")
        + f"; authority_ref={authority_ref}"
    ).strip("; ")
    return final


def materialize_facility_packet(
    packet_dir: Path,
    target_repo: Path,
    *,
    authority_mode: str,
    authority_ref: str,
    ledger_dir: Path | None = None,
    root: Path = ROOT,
    commit_message: str | None = None,
) -> dict[str, Any]:
    """Commit one validated facility binding and emit a new canonical determination.

    The original blocked receipt is preserved. The returned receipt has a new
    determination ID and supersedes the blocked receipt after the actual target
    commit exists.
    """

    if authority_mode not in AUTHORITY_MODES:
        raise ACEError(
            f"authority_mode must be one of {sorted(AUTHORITY_MODES)}",
            code="materialization_authority_missing",
        )
    if not isinstance(authority_ref, str) or not authority_ref.strip():
        raise ACEError("materialization requires a non-empty authority_ref", code="materialization_authority_missing")

    packet = packet_dir.expanduser().resolve()
    repo = target_repo.expanduser().resolve()
    receipt_path = packet / "determination_receipt.json"
    candidate_path = packet / "candidate_facility_binding.json"
    if not receipt_path.is_file() or not candidate_path.is_file():
        raise ACEError("facility packet is missing its determination or candidate artifact", code="target_unavailable")

    receipt = _validate_receipt(receipt_path, root=root)
    _assert_commit_ready(receipt)
    _, baseline_head = _assert_clean_feature_branch(repo)
    expected_head = _canonrec_baseline(receipt)
    if baseline_head != expected_head:
        raise ACEError(
            f"CanonRec baseline advanced ({expected_head} -> {baseline_head}); recompile before materialization",
            code="registry_baseline_advanced",
        )

    target_rel, target = _safe_target_path(receipt, repo)
    candidate = load_json(candidate_path)
    if not isinstance(candidate, dict):
        raise ACEError("facility candidate must be a JSON object", code="input_validation_failed")
    canonical = _canonical_facility_record(candidate, receipt, authority_ref=authority_ref)

    target_existed = target.exists()
    old_bytes = target.read_bytes() if target_existed else None
    baseline_target_hash = (
        file_sha256(target) if target_existed else semantic_sha256({"target": target_rel, "state": "absent"})
    )
    append_determination(receipt, ledger_dir, root=root)

    started = time.perf_counter()
    commit_sha: str | None = None
    try:
        _write_json_atomic(target, canonical)
        target_hash = file_sha256(target)
        _git(repo, "add", "--", target_rel)
        staged = _git(repo, "diff", "--cached", "--name-only")
        if target_rel not in staged.splitlines():
            raise ACEError("declared canonical target was not staged", code="runtime_failure")
        _git(repo, "config", "user.name", "Aurora ACE Materializer")
        _git(repo, "config", "user.email", "ace@aurora.local")
        message = commit_message or f"feat(canon): materialize ACE facility binding {candidate['subject_ref']}"
        _git(repo, "commit", "-m", message)
        commit_sha = _git(repo, "rev-parse", "HEAD")
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        final = _final_receipt(
            receipt,
            commit_sha=commit_sha,
            target_path=target_rel,
            target_existed=target_existed,
            target_hash=target_hash,
            baseline_target_hash=baseline_target_hash,
            authority_mode=authority_mode,
            authority_ref=authority_ref.strip(),
            elapsed_ms=elapsed_ms,
        )
        with tempfile.TemporaryDirectory(prefix="ace-materialized-schema-") as temp:
            final_path = Path(temp) / "receipt.json"
            final_path.write_text(json.dumps(final, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            report = validate_json_schema(
                final_path,
                root / "catalog/schemas/aurora_ace_determination_receipt.schema.json",
                root,
            )
        if not report["ok"]:
            raise ACEError(
                "materialized determination failed schema validation: "
                + json.dumps(report["errors"][:3]),
                code="output_validation_failed",
            )
        final_path = packet / "materialized_determination_receipt.json"
        _write_json_atomic(final_path, final)
        append_determination(final, ledger_dir, root=root)
        return final
    except Exception:
        # A clean, baseline-matched worktree was required at entry, so restoring
        # that exact baseline is safe and keeps failed materialization atomic.
        try:
            _git(repo, "reset", "--hard", baseline_head, check=False)
            if not target_existed and target.exists():
                target.unlink()
            elif target_existed and old_bytes is not None and not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(old_bytes)
        except Exception:
            pass
        raise

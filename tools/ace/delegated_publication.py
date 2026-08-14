"""
Policy-gated delegated CanonRec branch publication for ACE v0.12.

This module does not create canon authority. It takes an already commit-ready ACE
packet, invokes the packet's existing native materializer on an isolated CanonRec
feature branch, pushes that branch, and opens a draft pull request for review.
It never merges the pull request or advances CanonRec main.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

import yaml

from . import generic_entity as generic_engine
from .character_materialize import materialize_packet
from .core import ACEError, ROOT, load_json, semantic_sha256, utc_now, write_json
from .delegated_github import PublicationStateUncertain, open_pull_request
from .generic_entity_validation import (
    assert_native_entity_tree_readable,
    payload_validator_binding,
)
from .generic_naming import validate_generic_naming_receipt
from .materialize import _git as _native_git
from .mcp_adapter import (
    MCP_CANONREC_NAME,
    MCP_REGISTRY_REL,
    _canonrec_baseline,
    _registered_canonrec_repo,
    _safe_output_dir,
)
from .runtime_binding import _git_blob_sha

PUBLICATION_VERSION = "0.12.0"
PUBLICATION_CAPABILITY_ID = "ace.capability.canonrec.publish.delegated_pr"
PUBLICATION_POLICY_REL = Path("catalog/ace/policies/delegated_publication_v0_12.json")
PUBLICATION_AUTHORITY_MODE = "delegated_materialize"
_EXPECTED_POLICY_ID = "ace.policy.publication.delegated-pr.v1"
_EXPECTED_GITHUB_REPOSITORY = "AUo959/CanonRec"
_REQUIRED_SCOPES = frozenset({"ace:materialize", "ace:autonomic", "ace:publish"})
_ALLOWED_PACKET_KINDS = frozenset({"character", "facility", "generic_entity"})
_BRANCH_SAFE = re.compile(r"[^a-z0-9._-]+")
_AUTHORITY_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:@/-]{0,255}$")
_GENERIC_NAMING_REL = Path("tools/ace/generic_naming.py")
_GENERIC_NAMING_BLOB = "3059542cfd051427464f3ef88c127c8bb463e8e9"
_GITHUB_HELPER_REL = Path("tools/ace/delegated_github.py")
_GITHUB_HELPER_BLOB = "a82ca27d0bf0120f32755fecdb60fa9fdf5a59a2"


def _git(repo: Path, *args: str, check: bool = True) -> str:
    """Reuse the established ACE Git executor."""
    return _native_git(repo, *args, check=check)


def _assert_helper_dependencies(root: Path) -> None:
    expected = {
        _GENERIC_NAMING_REL: _GENERIC_NAMING_BLOB,
        _GITHUB_HELPER_REL: _GITHUB_HELPER_BLOB,
    }
    for rel, blob in expected.items():
        source = (root / rel).resolve()
        if not source.is_file() or _git_blob_sha(source) != blob:
            raise ACEError(
                f"delegated publication dependency changed without an updated binding: {rel}",
                code="stale_manifest",
            )


def _expect_policy(payload: Mapping[str, Any], expected: Mapping[str, Any]) -> None:
    for key, value in expected.items():
        if payload.get(key) != value:
            raise ACEError(f"delegated publication policy has invalid {key}", code="invalid_manifest")


def _validate_policy_collections(payload: Mapping[str, Any]) -> None:
    scopes = payload.get("required_remote_scopes")
    packet_kinds = payload.get("allowed_packet_kinds")
    prefix = payload.get("branch_prefix")
    if not isinstance(scopes, list) or set(scopes) != _REQUIRED_SCOPES:
        raise ACEError("delegated publication policy has invalid required scopes", code="invalid_manifest")
    if not isinstance(packet_kinds, list) or set(packet_kinds) != _ALLOWED_PACKET_KINDS:
        raise ACEError("delegated publication policy has invalid packet kinds", code="invalid_manifest")
    if not isinstance(prefix, str) or not prefix.startswith("ace/") or not prefix.endswith("/"):
        raise ACEError("delegated publication branch prefix is unsafe", code="invalid_manifest")


def _load_policy(root: Path) -> dict[str, Any]:
    path = (root / PUBLICATION_POLICY_REL).resolve()
    root_resolved = root.resolve()
    if path == root_resolved or root_resolved not in path.parents:
        raise ACEError("delegated publication policy escaped OrionCore", code="invalid_manifest")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ACEError("delegated publication policy cannot be loaded", code="invalid_manifest") from exc
    if not isinstance(payload, Mapping):
        raise ACEError("delegated publication policy must be an object", code="invalid_manifest")
    _expect_policy(
        payload,
        {
            "policy_id": _EXPECTED_POLICY_ID,
            "target_repository": MCP_CANONREC_NAME,
            "github_repository": _EXPECTED_GITHUB_REPOSITORY,
            "base_branch": "main",
            "authority_mode": PUBLICATION_AUTHORITY_MODE,
            "auto_merge_allowed": False,
            "pull_request_draft": True,
            "registered_baseline_required": True,
            "max_naming_warnings": 0,
        },
    )
    _validate_policy_collections(payload)
    return dict(payload)


def _registry_rows(root: Path) -> list[Mapping[str, Any]]:
    registry_path = root / MCP_REGISTRY_REL
    try:
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ACEError("repository registry cannot be loaded for publication", code="invalid_manifest") from exc
    rows = registry.get("repos") if isinstance(registry, Mapping) else None
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise ACEError("repository registry has no valid repos list", code="invalid_manifest")
    return rows


def _registered_canonrec_baseline(root: Path) -> str:
    matches = [row for row in _registry_rows(root) if row.get("name") == MCP_CANONREC_NAME]
    if len(matches) != 1:
        raise ACEError("delegated publication requires one registered CanonRec", code="invalid_manifest")
    row = matches[0]
    baseline = row.get("head_sha")
    if row.get("branch") != "main":
        raise ACEError("registered CanonRec branch must be main", code="invalid_manifest")
    if not isinstance(baseline, str) or re.fullmatch(r"[a-f0-9]{40}", baseline) is None:
        raise ACEError("registered CanonRec baseline is invalid", code="invalid_manifest")
    return baseline


def _packet_kind(packet: Path) -> str:
    if (packet / "candidate_entity.json").is_file():
        return "generic_entity"
    if (packet / "candidate_facility_binding.json").is_file():
        return "facility"
    if (packet / "candidate").is_dir() and (packet / "artifacts" / "charforge").is_dir():
        return "character"
    raise ACEError("delegated publication does not recognize this ACE packet type", code="target_unavailable")


def _principal_gate(principal: Mapping[str, Any], authority_ref: str, policy: Mapping[str, Any]) -> str:
    principal_id = principal.get("principal")
    scopes = principal.get("scopes")
    refs = principal.get("authority_refs")
    if not isinstance(principal_id, str) or not principal_id.strip():
        raise ACEError("delegated publication requires an authenticated principal", code="materialization_authority_missing")
    if _AUTHORITY_REF.fullmatch(authority_ref) is None:
        raise ACEError("delegated publication authority_ref is malformed", code="materialization_authority_missing")
    if not isinstance(scopes, list) or not set(policy["required_remote_scopes"]).issubset(set(scopes)):
        raise ACEError("delegated publication principal lacks required scopes", code="materialization_authority_missing")
    if not isinstance(refs, list) or authority_ref not in refs:
        raise ACEError("delegated publication principal is not bound to authority_ref", code="materialization_authority_missing")
    return principal_id.strip()


def _normalize_remote_url(value: str) -> str:
    url = value.strip()
    if url.startswith("git@github.com:"):
        url = "https://github.com/" + url[len("git@github.com:") :]
    if url.startswith("ssh://git@github.com/"):
        url = "https://github.com/" + url[len("ssh://git@github.com/") :]
    if url.endswith(".git"):
        url = url[:-4]
    return url.rstrip("/")


def _assert_remote_identity(repo: Path, policy: Mapping[str, Any]) -> None:
    expected = f"https://github.com/{policy['github_repository']}"
    observed = _normalize_remote_url(_git(repo, "remote", "get-url", "origin"))
    if observed != expected:
        raise ACEError(
            f"registered CanonRec origin does not match delegated publication policy: {observed}",
            code="materialization_authority_missing",
        )


def _remote_main_sha(repo: Path) -> str:
    line = _git(repo, "ls-remote", "origin", "refs/heads/main")
    sha = line.split("\t", 1)[0].strip() if line else ""
    if re.fullmatch(r"[a-f0-9]{40}", sha) is None:
        raise ACEError("could not resolve CanonRec remote main", code="target_unavailable")
    return sha


def _branch_component(value: str) -> str:
    normalized = _BRANCH_SAFE.sub("-", value.casefold()).strip("-._")
    return normalized[:64] or "entity"


def _branch_name(packet_kind: str, receipt: Mapping[str, Any], policy: Mapping[str, Any]) -> str:
    subject_refs = receipt.get("subject_refs")
    subject = subject_refs[0] if isinstance(subject_refs, list) and subject_refs else receipt.get("determination_id", "entity")
    digest = semantic_sha256(
        {
            "determination_id": receipt.get("determination_id"),
            "query_id": receipt.get("query_id"),
            "subject_refs": subject_refs,
            "packet_kind": packet_kind,
        }
    )[:12]
    return f"{policy['branch_prefix']}{packet_kind}/{_branch_component(str(subject))}-{digest}"


def _remote_branch_exists(repo: Path, branch: str) -> bool:
    return bool(_git(repo, "ls-remote", "--heads", "origin", f"refs/heads/{branch}"))


def _local_branch_exists(repo: Path, branch: str) -> bool:
    return bool(_git(repo, "show-ref", "--verify", f"refs/heads/{branch}", check=False))


def _assert_local_baseline(repo: Path, baseline: str, base_branch: str) -> None:
    if _git(repo, "rev-parse", "--is-inside-work-tree") != "true":
        raise ACEError("registered CanonRec is not a Git worktree", code="target_unavailable")
    if _git(repo, "status", "--porcelain"):
        raise ACEError("delegated publication requires a clean CanonRec worktree", code="transaction_conflict")
    branch = _git(repo, "branch", "--show-current")
    if branch != base_branch:
        raise ACEError(
            f"delegated publication requires CanonRec on {base_branch!r}, observed {branch!r}",
            code="transaction_conflict",
        )
    if _git(repo, "rev-parse", "HEAD") != baseline:
        raise ACEError("local CanonRec is not at the registered baseline", code="registry_baseline_advanced")


def _validate_generic_packet(packet: Path, policy: Mapping[str, Any], *, root: Path) -> dict[str, Any]:
    candidate = load_json(packet / "candidate_entity.json")
    if not isinstance(candidate, Mapping):
        raise ACEError("generic publication candidate must be an object", code="input_validation_failed")
    assert_native_entity_tree_readable(root / generic_engine.CANONREC_REL)
    naming = validate_generic_naming_receipt(candidate, root=root)
    if len(naming["warnings"]) > int(policy["max_naming_warnings"]):
        raise ACEError(
            "delegated publication refuses generic naming warnings; human review is required before publication",
            code="output_validation_failed",
        )
    return naming


def _materialize(packet: Path, repo: Path, packet_kind: str, authority_ref: str, *, root: Path) -> dict[str, Any]:
    message = f"feat(canon): ACE delegated {packet_kind} proposal"
    if packet_kind == "generic_entity":
        with payload_validator_binding(generic_engine):
            return generic_engine.materialize_generic_entity_packet(
                packet,
                repo,
                authority_mode=PUBLICATION_AUTHORITY_MODE,
                authority_ref=authority_ref,
                root=root,
                commit_message=message,
            )
    return materialize_packet(
        packet,
        repo,
        authority_mode=PUBLICATION_AUTHORITY_MODE,
        authority_ref=authority_ref,
        root=root,
        commit_message=message,
    )


def _push_branch(repo: Path, branch: str) -> None:
    _git(repo, "push", "--set-upstream", "origin", f"HEAD:refs/heads/{branch}")


def _delete_remote_branch(repo: Path, branch: str) -> None:
    _git(repo, "push", "origin", "--delete", branch)


def _restore_local(repo: Path, baseline: str, base_branch: str, proposal_branch: str | None = None) -> None:
    try:
        _git(repo, "reset", "--hard", baseline)
        _git(repo, "clean", "-fd")
        _git(repo, "checkout", "-B", base_branch, baseline)
        if proposal_branch and proposal_branch != base_branch and _local_branch_exists(repo, proposal_branch):
            _git(repo, "branch", "-D", proposal_branch)
        if _git(repo, "status", "--porcelain"):
            raise ACEError("restored CanonRec checkout is not clean", code="runtime_failure")
    except ACEError as exc:
        raise PublicationStateUncertain(
            "registered CanonRec checkout could not be restored deterministically",
            code="runtime_failure",
        ) from exc


def _publication_receipt(
    context: Mapping[str, Any],
    pr_number: int,
    pr_url: str,
    naming: Mapping[str, Any] | None,
) -> dict[str, Any]:
    branch = str(context["branch"])
    proposal_commit = str(context["proposal_commit"])
    return {
        "schema_version": PUBLICATION_VERSION,
        "record_type": "ace_delegated_publication_receipt",
        "publication_id": f"ace.publication.{semantic_sha256({'branch': branch, 'commit': proposal_commit})[:20]}",
        "created_at": utc_now(),
        "status": "review_pending",
        "capability_id": PUBLICATION_CAPABILITY_ID,
        "policy_ref": context["policy_id"],
        "authenticated_principal": context["principal_id"],
        "authority_ref": context["authority_ref"],
        "packet_kind": context["packet_kind"],
        "packet_ref": context["packet_ref"],
        "source_determination_id": context["source_determination_id"],
        "proposal_determination_id": context["proposal_determination_id"],
        "proposal_determination_status": context["proposal_determination_status"],
        "target_repository": MCP_CANONREC_NAME,
        "registered_baseline": context["baseline"],
        "proposal_branch": branch,
        "proposal_commit": proposal_commit,
        "pull_request": {
            "number": pr_number,
            "url": pr_url,
            "base_branch": context["base_branch"],
            "draft": True,
            "auto_merge_allowed": False,
        },
        "naming_admission": naming,
        "mainline_canon_advanced": False,
        "replayable": False,
    }


def _progress_receipt(context: Mapping[str, Any], status: str) -> dict[str, Any]:
    return {
        "schema_version": PUBLICATION_VERSION,
        "record_type": "ace_delegated_publication_receipt",
        "created_at": utc_now(),
        "status": status,
        "capability_id": PUBLICATION_CAPABILITY_ID,
        "policy_ref": context["policy_id"],
        "authenticated_principal": context["principal_id"],
        "authority_ref": context["authority_ref"],
        "packet_kind": context["packet_kind"],
        "packet_ref": context["packet_ref"],
        "source_determination_id": context["source_determination_id"],
        "registered_baseline": context["baseline"],
        "proposal_branch": context["branch"],
        "proposal_commit": context["proposal_commit"],
        "mainline_canon_advanced": False,
        "replayable": False,
    }


def _validate_publication_input(
    output_name: str,
    authority_ref: str,
    principal: Mapping[str, Any],
    *,
    root: Path,
    runtime_root: Path | None,
) -> tuple[dict[str, Any], str, Path, dict[str, Any], str]:
    _assert_helper_dependencies(root)
    policy = _load_policy(root)
    principal_id = _principal_gate(principal, authority_ref, policy)
    packet = _safe_output_dir(output_name, root=root, runtime_root=runtime_root)
    receipt_path = packet / "determination_receipt.json"
    if not receipt_path.is_file():
        raise ACEError("delegated publication packet has no determination_receipt.json", code="target_unavailable")
    receipt = load_json(receipt_path)
    materialization = receipt.get("materialization", {}) if isinstance(receipt, Mapping) else {}
    if not isinstance(receipt, Mapping) or materialization.get("status") != "commit_ready":
        raise ACEError("delegated publication requires a commit-ready determination", code="input_validation_failed")
    packet_kind = _packet_kind(packet)
    if packet_kind not in policy["allowed_packet_kinds"]:
        raise ACEError("delegated publication policy refuses this packet kind", code="materialization_authority_missing")
    return policy, principal_id, packet, dict(receipt), packet_kind


def _validate_repository_state(repo: Path, receipt: Mapping[str, Any], policy: Mapping[str, Any], *, root: Path) -> str:
    registered_baseline = _registered_canonrec_baseline(root)
    if _canonrec_baseline(receipt) != registered_baseline:
        raise ACEError("packet CanonRec baseline does not match the registered baseline", code="registry_baseline_advanced")
    _assert_local_baseline(repo, registered_baseline, str(policy["base_branch"]))
    _assert_remote_identity(repo, policy)
    if _remote_main_sha(repo) != registered_baseline:
        raise ACEError("CanonRec remote main advanced beyond the registered baseline", code="registry_baseline_advanced")
    return registered_baseline


def _prepare_state(
    output_name: str,
    authority_ref: str,
    principal: Mapping[str, Any],
    *,
    root: Path,
    runtime_root: Path | None,
) -> dict[str, Any]:
    policy, principal_id, packet, receipt, packet_kind = _validate_publication_input(
        output_name, authority_ref, principal, root=root, runtime_root=runtime_root
    )
    repo = _registered_canonrec_repo(root)
    baseline = _validate_repository_state(repo, receipt, policy, root=root)
    naming = _validate_generic_packet(packet, policy, root=root) if packet_kind == "generic_entity" else None
    branch = _branch_name(packet_kind, receipt, policy)
    if _remote_branch_exists(repo, branch) or _local_branch_exists(repo, branch):
        raise ACEError("delegated publication branch already exists; replay is refused", code="transaction_conflict")
    return {
        "policy": policy,
        "principal_id": principal_id,
        "packet": packet,
        "receipt": receipt,
        "packet_kind": packet_kind,
        "repo": repo,
        "baseline": baseline,
        "naming": naming,
        "branch": branch,
        "authority_ref": authority_ref,
    }


def _materialize_proposal(state: Mapping[str, Any], *, root: Path) -> tuple[dict[str, Any], str]:
    repo = state["repo"]
    baseline = str(state["baseline"])
    branch = str(state["branch"])
    _git(repo, "checkout", "-B", branch, baseline)
    determination = _materialize(
        state["packet"], repo, str(state["packet_kind"]), str(state["authority_ref"]), root=root
    )
    proposal_commit = _git(repo, "rev-parse", "HEAD")
    if int(_git(repo, "rev-list", "--count", f"{baseline}..HEAD")) != 1:
        raise ACEError("delegated publication requires exactly one proposal commit", code="runtime_failure")
    if _git(repo, "status", "--porcelain"):
        raise ACEError("delegated publication materializer left a dirty CanonRec worktree", code="runtime_failure")
    return determination, proposal_commit


def _proposal_context(
    state: Mapping[str, Any],
    determination: Mapping[str, Any],
    proposal_commit: str,
) -> dict[str, Any]:
    receipt = state["receipt"]
    policy = state["policy"]
    return {
        "packet_ref": str(state["packet"]),
        "packet_kind": state["packet_kind"],
        "source_determination_id": receipt.get("determination_id"),
        "proposal_determination_id": determination.get("determination_id"),
        "proposal_determination_status": determination.get("status"),
        "authority_ref": state["authority_ref"],
        "principal_id": state["principal_id"],
        "policy_id": policy["policy_id"],
        "base_branch": policy["base_branch"],
        "baseline": state["baseline"],
        "branch": state["branch"],
        "proposal_commit": proposal_commit,
    }


def _write_final_receipt(
    packet: Path,
    context: Mapping[str, Any],
    pr_number: int,
    pr_url: str,
    naming: Mapping[str, Any] | None,
) -> dict[str, Any]:
    publication = _publication_receipt(context, pr_number, pr_url, naming)
    try:
        write_json(packet / "delegated_publication_receipt.json", publication)
    except OSError as exc:
        raise PublicationStateUncertain(
            "CanonRec draft PR exists but ACE could not persist the final publication receipt",
            code="runtime_failure",
        ) from exc
    return publication


def _refuse_after_pr_failure(
    packet: Path,
    repo: Path,
    branch: str,
    context: Mapping[str, Any],
    exc: Exception,
) -> None:
    try:
        _delete_remote_branch(repo, branch)
    except ACEError as cleanup_exc:
        raise PublicationStateUncertain(
            "CanonRec draft PR failed and the orphan proposal branch could not be deleted",
            code="runtime_failure",
        ) from cleanup_exc
    refusal = {
        **_progress_receipt(context, "refused"),
        "failure": {"code": getattr(exc, "code", "runtime_failure"), "message": str(exc)},
    }
    write_json(packet / "delegated_publication_receipt.json", refusal)


def _publish_proposal(
    state: Mapping[str, Any],
    determination: Mapping[str, Any],
    proposal_commit: str,
) -> dict[str, Any]:
    packet = state["packet"]
    repo = state["repo"]
    branch = str(state["branch"])
    policy = state["policy"]
    context = _proposal_context(state, determination, proposal_commit)
    write_json(packet / "delegated_publication_receipt.json", _progress_receipt(context, "publication_in_progress"))
    try:
        _push_branch(repo, branch)
    except ACEError as exc:
        raise PublicationStateUncertain(
            "CanonRec proposal push failed with remote branch state uncertain",
            code="runtime_failure",
        ) from exc
    try:
        pr_number, pr_url = open_pull_request(
            branch,
            str(state["packet_kind"]),
            determination,
            str(state["authority_ref"]),
            str(state["principal_id"]),
            policy,
        )
    except PublicationStateUncertain:
        raise
    except Exception as exc:
        _refuse_after_pr_failure(packet, repo, branch, context, exc)
        raise
    return _write_final_receipt(packet, context, pr_number, pr_url, state["naming"])


def publish_delegated_packet(
    output_name: str,
    authority_ref: str,
    principal: Mapping[str, Any],
    *,
    root: Path = ROOT,
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    """Publish one validated ACE packet as a draft CanonRec pull request."""
    state = _prepare_state(output_name, authority_ref, principal, root=root, runtime_root=runtime_root)
    repo = state["repo"]
    try:
        determination, proposal_commit = _materialize_proposal(state, root=root)
        return _publish_proposal(state, determination, proposal_commit)
    finally:
        policy = state["policy"]
        _restore_local(repo, str(state["baseline"]), str(policy["base_branch"]), str(state["branch"]))

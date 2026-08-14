"""Exact-owner binding for ACE governed Orion L1 progression."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Tuple

import yaml

from .core import ACEError, CLOUDBANK_REL, ROOT
from .runtime_binding import _git_blob_sha

ORION_PROGRESSION_VERSION = "0.13.0"
ORION_PROGRESSION_CAPABILITY_ID = "ace.runtime.orion.l1.advance.governed"
ORION_PROGRESSION_POLICY_REL = Path("catalog/ace/policies/orion_progression_v0_13.json")
_SHA1 = re.compile(r"^[a-f0-9]{40}$")

_POLICY_FIELDS = {
    "policy_id": "ace.policy.orion.l1.governed-single-tick.v1",
    "version": ORION_PROGRESSION_VERSION,
    "capability_id": ORION_PROGRESSION_CAPABILITY_ID,
    "cloudbank_repository": "aurora-cloudbank-symbolic-main",
    "require_existing_run": True,
    "require_preflight_ready": True,
    "require_resume_ready": True,
    "elapsed_minutes": 15,
    "ticks_per_authorization": 1,
    "init_allowed": False,
    "provider_activation_allowed": False,
    "remote_exposure_allowed": False,
    "mcp_exposure_allowed": False,
    "automatic_retry_allowed": False,
    "state_uncertain_requires_operator_reconciliation": True,
    "required_principal": "ORION.ROLE.PILOT",
}
_OWNER_FIELDS = {
    "path": "simulation/l1_runtime.py",
    "git_blob_sha": "dd3ae6f73bb2d2130981011a7c2443c0e39b8210",
    "class": "OrionL1Runtime",
    "preflight_method": "preflight",
    "load_method": "load_run",
    "advance_method": "advance",
    "export_method": "export_state",
}


def _expect_fields(
    payload: Mapping[str, Any],
    expected: Mapping[str, Any],
    label: str,
) -> None:
    mismatches = [key for key, value in expected.items() if payload.get(key) != value]
    if mismatches:
        raise ACEError(
            f"{label} has invalid field(s): {', '.join(sorted(mismatches))}",
            code="invalid_manifest",
        )


def _read_policy(root: Path) -> Dict[str, Any]:
    path = (root / ORION_PROGRESSION_POLICY_REL).resolve()
    root_resolved = root.resolve()
    if path == root_resolved or root_resolved not in path.parents:
        raise ACEError(
            "Orion progression policy escaped OrionCore",
            code="invalid_manifest",
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ACEError(
            "Orion progression policy cannot be loaded",
            code="invalid_manifest",
        ) from exc
    if not isinstance(payload, dict):
        raise ACEError(
            "Orion progression policy must be an object",
            code="invalid_manifest",
        )
    return payload


def load_orion_policy(root: Path = ROOT) -> Dict[str, Any]:
    """Load and strictly validate the committed v0.13 progression policy."""
    payload = _read_policy(root)
    _expect_fields(payload, _POLICY_FIELDS, "Orion progression policy")
    owner = payload.get("owner")
    if not isinstance(owner, dict):
        raise ACEError(
            "Orion progression policy owner binding is missing",
            code="invalid_manifest",
        )
    _expect_fields(owner, _OWNER_FIELDS, "Orion progression owner binding")
    cloudbank_sha = payload.get("cloudbank_repository_sha")
    if not isinstance(cloudbank_sha, str) or _SHA1.fullmatch(cloudbank_sha) is None:
        raise ACEError(
            "Orion progression policy CloudBank SHA is invalid",
            code="invalid_manifest",
        )
    return payload


def _registry_rows(root: Path) -> list[Mapping[str, Any]]:
    try:
        registry = yaml.safe_load(
            (root / "catalog/repo_registry.yaml").read_text(encoding="utf-8")
        )
    except (OSError, yaml.YAMLError) as exc:
        raise ACEError(
            "repository registry cannot be loaded for Orion progression",
            code="invalid_manifest",
        ) from exc
    rows = registry.get("repos") if isinstance(registry, Mapping) else None
    if not isinstance(rows, list) or any(
        not isinstance(row, Mapping) for row in rows
    ):
        raise ACEError(
            "repository registry has no valid repos list",
            code="invalid_manifest",
        )
    return rows


def registered_cloudbank(
    root: Path,
    policy: Mapping[str, Any],
) -> Tuple[Path, str]:
    """Resolve the one registered CloudBank checkout and exact expected SHA."""
    matches = [
        row
        for row in _registry_rows(root)
        if row.get("name") == policy["cloudbank_repository"]
    ]
    if len(matches) != 1:
        raise ACEError(
            "Orion progression requires one registered CloudBank",
            code="invalid_manifest",
        )
    row = matches[0]
    expected = {
        "path": CLOUDBANK_REL.as_posix(),
        "branch": "main",
        "head_sha": policy["cloudbank_repository_sha"],
    }
    _expect_fields(row, expected, "registered CloudBank")
    repo = (root / CLOUDBANK_REL).resolve()
    if not repo.is_dir():
        raise ACEError(
            "registered CloudBank checkout is unavailable",
            code="target_unavailable",
        )
    return repo, str(row["head_sha"])


def _read_text(path: Path, message: str) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ACEError(message, code="target_unavailable") from exc


def _safe_ref_parts(ref: str) -> bool:
    parts = ref.split("/")
    return (
        ref.startswith("refs/")
        and ".." not in ref
        and "\\" not in ref
        and all(part not in {"", ".", ".."} for part in parts)
    )


def _safe_ref(head: str) -> str:
    if not head.startswith("ref: "):
        raise ACEError(
            "CloudBank Git HEAD has unsupported format",
            code="target_unavailable",
        )
    ref = head.removeprefix("ref: ").strip()
    if not _safe_ref_parts(ref):
        raise ACEError("CloudBank Git ref is unsafe", code="target_unavailable")
    return ref


def _packed_ref_candidates(lines: list[str], ref: str) -> list[str]:
    candidates = []
    for line in lines:
        sha, separator, name = line.partition(" ")
        if line and not line.startswith(("#", "^")) and separator and name == ref:
            candidates.append(sha)
    return candidates


def _packed_ref(git_dir: Path, ref: str) -> str:
    packed = git_dir / "packed-refs"
    if not packed.is_file():
        raise ACEError(
            "CloudBank Git ref cannot be resolved",
            code="target_unavailable",
        )
    lines = packed.read_text(encoding="utf-8").splitlines()
    matches = _packed_ref_candidates(lines, ref)
    valid = len(matches) == 1 and _SHA1.fullmatch(matches[0]) is not None
    if not valid:
        raise ACEError(
            "CloudBank Git ref cannot be resolved",
            code="target_unavailable",
        )
    return matches[0]


def resolve_cloudbank_head(repo: Path) -> str:
    """Resolve the checked-out CloudBank SHA without executing Git."""
    git_dir = repo / ".git"
    if not git_dir.is_dir():
        raise ACEError(
            "CloudBank checkout has no Git metadata",
            code="target_unavailable",
        )
    head = _read_text(git_dir / "HEAD", "CloudBank Git HEAD cannot be read")
    if _SHA1.fullmatch(head):
        return head
    ref = _safe_ref(head)
    loose = git_dir / ref
    if loose.is_file():
        value = _read_text(loose, "CloudBank Git ref cannot be read")
    else:
        value = _packed_ref(git_dir, ref)
    if _SHA1.fullmatch(value) is None:
        raise ACEError("CloudBank Git ref is invalid", code="target_unavailable")
    return value


def _owner_source(
    repo: Path,
    policy: Mapping[str, Any],
) -> Tuple[Path, str]:
    source = (repo / str(policy["owner"]["path"])).resolve()
    if repo not in source.parents or not source.is_file():
        raise ACEError(
            "registered Orion runtime owner source is unavailable",
            code="missing_tool",
        )
    observed_blob = _git_blob_sha(source)
    if observed_blob != policy["owner"]["git_blob_sha"]:
        raise ACEError(
            "Orion runtime owner source changed without policy review",
            code="stale_manifest",
        )
    return source, observed_blob


def _owner_spec(module_name: str, source: Path) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, source)
    if spec is None or spec.loader is None:
        raise ACEError(
            "Orion runtime owner cannot be imported",
            code="tool_unavailable",
        )
    return spec


def _execute_owner_module(module: Any, spec: Any, repo: Path, module_name: str) -> None:
    original_path = list(sys.path)
    sys.path[:0] = [str(repo / "simulation"), str(repo)]
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    finally:
        sys.path[:] = original_path


def _import_owner(source: Path, repo: Path, owner_blob: str) -> Any:
    module_name = f"ace_orion_l1_owner_{owner_blob[:12]}"
    existing = sys.modules.get(module_name)
    if existing is not None:
        return existing
    spec = _owner_spec(module_name, source)
    module = importlib.util.module_from_spec(spec)
    _execute_owner_module(module, spec, repo, module_name)
    return module


def _required_runtime_methods(policy: Mapping[str, Any]) -> list[str]:
    owner = policy["owner"]
    return [
        str(owner["preflight_method"]),
        str(owner["load_method"]),
        str(owner["advance_method"]),
        str(owner["export_method"]),
    ]


def _has_runtime_contract(runtime_class: type[Any], methods: list[str]) -> bool:
    return all(callable(getattr(runtime_class, name, None)) for name in methods)


def _runtime_class(
    module: Any,
    source: Path,
    policy: Mapping[str, Any],
) -> type[Any]:
    module_file = getattr(module, "__file__", None)
    source_matches = (
        isinstance(module_file, str) and Path(module_file).resolve() == source
    )
    if not source_matches:
        raise ACEError(
            "Orion runtime module provenance mismatch",
            code="tool_unavailable",
        )
    runtime_class = getattr(module, str(policy["owner"]["class"]), None)
    if not isinstance(runtime_class, type):
        raise ACEError(
            "Orion runtime owner class is unavailable",
            code="tool_unavailable",
        )
    if not _has_runtime_contract(runtime_class, _required_runtime_methods(policy)):
        raise ACEError(
            "Orion runtime owner callable contract is incomplete",
            code="tool_unavailable",
        )
    return runtime_class


def load_owner_runtime(root: Path = ROOT) -> Dict[str, Any]:
    """Return the exact verified CloudBank runtime owner binding."""
    policy = load_orion_policy(root)
    repo, registered_sha = registered_cloudbank(root, policy)
    observed_sha = resolve_cloudbank_head(repo)
    if observed_sha != registered_sha:
        raise ACEError(
            "registered CloudBank baseline advanced: "
            f"registry={registered_sha}, observed={observed_sha}",
            code="stale_manifest",
        )
    source, owner_blob = _owner_source(repo, policy)
    module = _import_owner(source, repo, owner_blob)
    return {
        "policy": policy,
        "runtime_class": _runtime_class(module, source, policy),
        "cloudbank_repo": repo,
        "cloudbank_sha": registered_sha,
        "owner_blob_sha": owner_blob,
    }

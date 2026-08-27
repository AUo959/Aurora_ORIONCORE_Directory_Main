"""The Orion policy pins CloudBank twice; the two pins must agree.

The failure this prevents
------------------------
`orion_progression_v0_13.json` carries both a `cloudbank_repository_sha` and the
`owner.git_blob_sha` of `simulation/l1_runtime.py`. They are independent fields
describing one fact, so a bump can update one and miss the other.

That mistake fails in a genuinely confusing place. `registered_cloudbank()`
compares the registry row against `cloudbank_repository_sha` and reports
"registered CloudBank has invalid field(s)", while `_owner_source()` compares
the file against `git_blob_sha` — so a half-done bump surfaces as a complaint
about the *registry*, sending the reader to `catalog/repo_registry.yaml`, which
is correct. On 2026-08-20 that misdirection cost real time: the error named
`branch, head_sha` and the branch half was a separate defect entirely.

Checking coherence directly turns a misleading runtime error into a named test.

Scope
-----
This asserts the policy is internally consistent — that `git_blob_sha` is what
`path` actually hashes to at `cloudbank_repository_sha`. It deliberately does
NOT assert the pin is current, because being behind live `main` is a legitimate
state: the pin is a reviewed attestation, not a mirror. Deciding whether a newer
baseline is acceptable is what `tools/ace_owner_contract_diff.py` is for.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY = REPO_ROOT / "catalog" / "ace" / "policies" / "orion_progression_v0_13.json"
CLOUDBANK = (
    REPO_ROOT / "GUMAS_SIM_2.5" / "Aurora_Sim_Architecture"
    / "aurora-cloudbank-symbolic-main"
)

pytestmark = pytest.mark.skipif(
    not (CLOUDBANK / ".git").exists() or not POLICY.is_file(),
    reason="CloudBank checkout or Orion policy not present",
)


@pytest.fixture(scope="module")
def policy() -> dict:
    return json.loads(POLICY.read_text(encoding="utf-8"))


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(CLOUDBANK), *args],
        capture_output=True, text=True, check=False, timeout=30,
    )


def test_pinned_commit_is_present_in_the_checkout(policy):
    """A pin nobody can resolve cannot be verified by anything downstream."""
    sha = policy["cloudbank_repository_sha"]
    result = _git("cat-file", "-t", sha)
    assert result.returncode == 0 and result.stdout.strip() == "commit", (
        f"policy pins CloudBank {sha[:12]}, which is not a commit in the local "
        f"checkout. Fetch it before trusting any downstream ACE verification."
    )


def test_owner_blob_matches_the_pinned_commit(policy):
    """The two pins describe one fact and must not drift apart."""
    sha = policy["cloudbank_repository_sha"]
    path = policy["owner"]["path"]
    declared = policy["owner"]["git_blob_sha"]

    result = _git("rev-parse", f"{sha}:{path}")
    assert result.returncode == 0, (
        f"{path} does not exist at pinned commit {sha[:12]}"
    )
    actual = result.stdout.strip()
    assert actual == declared, (
        f"policy pin incoherence: owner.git_blob_sha is {declared[:12]} but "
        f"{path} hashes to {actual[:12]} at cloudbank_repository_sha "
        f"{sha[:12]}.\n\n"
        f"Both fields describe the same fact, so a bump must move both. "
        f"Left half-done, this surfaces at runtime as a complaint about the "
        f"repo registry rather than about this file."
    )


def test_module_constant_matches_the_policy_file(policy):
    """The attestation is stored twice — in Python and in JSON.

    `orion_runtime_owner._OWNER_FIELDS` duplicates the policy's `owner` block,
    and `load_owner_runtime()` checks the policy against the constant. So a bump
    must move both, and missing one produces "Orion progression owner binding
    has invalid field(s): git_blob_sha" — which points at the binding rather
    than at whichever of the two copies was actually left behind.

    Found the hard way on 2026-08-20: updating only the JSON traded one red test
    for a different one.
    """
    import sys

    tools = REPO_ROOT / "tools"
    if str(tools) not in sys.path:
        sys.path.insert(0, str(tools))
    from ace.orion_runtime_owner import _OWNER_FIELDS  # noqa: PLC0415

    mismatched = {
        key: (value, policy["owner"].get(key))
        for key, value in _OWNER_FIELDS.items()
        if policy["owner"].get(key) != value
    }
    assert not mismatched, (
        "owner attestation disagrees between the module constant and the policy "
        "file:\n  " + "\n  ".join(
            f"{k}: module={m!r} policy={p!r}" for k, (m, p) in mismatched.items()
        )
    )


def test_named_contract_methods_exist_at_the_pin(policy):
    """The methods the policy names must be present on the class it names.

    Cheap, but it is the assumption every other Orion check rests on: if the
    owner file were re-pinned to a commit where `advance` had been renamed, the
    blob check above would still pass.
    """
    import ast

    sha = policy["cloudbank_repository_sha"]
    path = policy["owner"]["path"]
    class_name = policy["owner"]["class"]
    wanted = {
        policy["owner"][key]
        for key in ("preflight_method", "load_method", "advance_method",
                    "export_method")
    }

    result = _git("show", f"{sha}:{path}")
    assert result.returncode == 0, f"cannot read {path} at {sha[:12]}"

    tree = ast.parse(result.stdout)
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            found |= {
                item.name for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
    assert found, f"class {class_name} not found in {path} at {sha[:12]}"

    missing = sorted(wanted - found)
    assert not missing, (
        f"policy names methods absent from {class_name} at the pinned commit: "
        f"{missing}"
    )

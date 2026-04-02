from __future__ import annotations

import argparse
import builtins
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import _workspace_common as workspace_common  # noqa: E402
import aurora_qem_patch_release as aurora_qem_patch_release  # noqa: E402
import threadcore_deploy_accesskey as threadcore_deploy_accesskey  # noqa: E402
import threadcore_deploy_seal as threadcore_deploy_seal  # noqa: E402
import threadcore_echochain_link as threadcore_echochain_link  # noqa: E402
import threadcore_visible_node as threadcore_visible_node  # noqa: E402


@pytest.mark.parametrize(
    ("module", "family"),
    [
        (threadcore_visible_node, "threadcore_visible_node"),
        (threadcore_echochain_link, "threadcore_echochain_link"),
        (threadcore_deploy_accesskey, "threadcore_deploy_accesskey"),
        (aurora_qem_patch_release, "aurora_qem_patch_release"),
    ],
)
def test_run_validate_returns_structured_report_for_missing_required_fields(
    module: object,
    family: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    artifact = tmp_path / "invalid.json"
    artifact.write_text("{}\n", encoding="utf-8")

    result = module.run_validate(argparse.Namespace(artifact=str(artifact), report_out=None))
    report = json.loads(capsys.readouterr().out)

    assert result == 1
    assert report["family"] == family
    assert report["ok"] is False
    assert report["normalized_payload"] is None
    assert any(error.startswith("missing required field:") for error in report["errors"])


def test_load_yaml_like_preserves_quoted_list_scalars_with_colons_without_pyyaml(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    yaml_path = tmp_path / "quoted_list.yaml"
    yaml_path.write_text('items:\n  - "A:B"\n  - key: "value"\n', encoding="utf-8")

    original_import = builtins.__import__

    def blocked_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "yaml":
            raise ImportError("yaml disabled for test")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)

    payload = workspace_common.load_yaml_like(yaml_path)

    assert payload == {"items": ["A:B", {"key": "value"}]}


def test_deploy_accesskey_validator_accepts_schema_valid_underscores() -> None:
    payload = {
        "symbolic_key": "THREADCORE_DEPLOY::ALPHA_CORE",
        "associated_bundle": "bundle.zip",
        "vector": "VECTOR_ALPHA_CORE",
        "registered_node": "THREADCORE::VISIBLE_NODE.ALPHA_CORE",
        "linked_echochain": "ECHOCHAIN_ALPHA_CORE",
        "threadcore_manifest": "THREADCORE.md",
        "ethics_protocol": "Picard_Delta_3",
        "timestamp": "2026-04-02T00:00:00Z",
    }

    errors, warnings = threadcore_deploy_accesskey.validate_payload(payload)

    assert errors == []
    assert warnings == []


def test_patterns_reject_backslashes_in_validated_codes() -> None:
    assert not threadcore_visible_node.CODE_PATTERN.match("VISIBLE\\NODE")
    assert not threadcore_echochain_link.CODE_PATTERN.match("ECHO\\CHAIN")
    assert not aurora_qem_patch_release.CODE_PATTERN.match("VECTOR\\ORIGIN")
    assert not aurora_qem_patch_release.PATCH_PATTERN.match("PATCH\\CODE")
    assert not threadcore_deploy_seal.CODE_PATTERN.match("NODE\\CODE")
    match = threadcore_deploy_seal.VECTOR_PATTERN.search("QEM-ALPHA\\CORE")
    assert match is not None
    assert match.group(0) == "QEM-ALPHA"


def test_deploy_seal_ethics_validation_rejects_prefix_only_matches() -> None:
    payload = {
        "node_id": "THREADCORE::VISIBLE_NODE.ALPHA_CORE",
        "vector": "VECTOR_ALPHA_CORE",
        "type": "mobile-gui",
        "linked_manifest": "manifest.json",
        "patch_id": "patch.json",
        "bundle": "bundle.zip",
        "registered": "2026-04-02T00:00:00Z",
        "alias": "Alpha Core",
        "ethics": "Picard_Delta_3!!!",
    }

    errors, _warnings = threadcore_deploy_seal.validate_visible_node_payload(payload)

    assert "field does not match expected format: ethics" in errors

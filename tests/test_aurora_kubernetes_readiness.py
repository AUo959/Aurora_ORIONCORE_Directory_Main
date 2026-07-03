from __future__ import annotations

import json
import stat
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_ROOT))

import aurora_kubernetes_readiness as k8s_readiness  # noqa: E402


def write_file(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_executable(path: Path) -> None:
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def command_result(args: list[str], returncode: int = 0, stdout: str = "", stderr: str = "") -> k8s_readiness.CommandResult:
    return k8s_readiness.CommandResult(args=args, returncode=returncode, stdout=stdout, stderr=stderr)


def fake_runner(args: list[str], timeout: int) -> k8s_readiness.CommandResult:
    if args[:2] == ["kubectl", "version"]:
        return command_result(
            args,
            stdout=json.dumps(
                {
                    "clientVersion": {"gitVersion": "v1.34.1", "platform": "darwin/arm64"},
                    "kustomizeVersion": "v5.7.1",
                }
            ),
        )
    if args[:2] == ["helm", "version"]:
        return command_result(args, returncode=127, stderr="helm missing")
    return command_result(args, returncode=127, stderr="unexpected command")


def seed_devcontainer(root: Path) -> None:
    write_file(
        root / ".devcontainer/devcontainer.json",
        json.dumps(
            {
                "features": {
                    "ghcr.io/devcontainers/features/kubectl-helm-minikube:1": {
                        "kubectl": "latest",
                        "helm": "latest",
                        "minikube": "none",
                    }
                }
            }
        ),
    )


def seed_k8s_surface(root: Path, *, with_placeholders: bool = False) -> None:
    base = root / k8s_readiness.K8S_PATH
    write_file(
        base / "aurora-namespace-rbac.yaml",
        """
apiVersion: v1
kind: Namespace
metadata:
  name: aurora-cloudbank
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: aurora-gui-cloudhub
  namespace: aurora-cloudbank
""",
    )
    secret_value = "placeholder-openai-key" if with_placeholders else "sealed-reference-only"
    write_file(
        base / "aurora-configmap-secrets.yaml",
        f"""
apiVersion: v1
kind: ConfigMap
metadata:
  name: mcp-bridge-config
  namespace: aurora-cloudbank
data:
  mode: readonly
---
apiVersion: v1
kind: Secret
metadata:
  name: aurora-api-keys
  namespace: aurora-cloudbank
stringData:
  openai-api-key: {secret_value}
""",
    )
    image = "aurora-cloudbank-symbolic:latest" if with_placeholders else "ghcr.io/auo959/aurora-cloudbank-symbolic@sha256:abc123"
    write_file(
        base / "aurora-gui-cloudhub-deployment.yaml",
        f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aurora-gui-cloudhub
  namespace: aurora-cloudbank
spec:
  selector:
    matchLabels:
      app: aurora-gui-cloudhub
  template:
    metadata:
      labels:
        app: aurora-gui-cloudhub
    spec:
      containers:
        - name: api
          image: {image}
""",
    )
    write_file(
        base / "aurora-gui-cloudhub-service.yaml",
        """
apiVersion: v1
kind: Service
metadata:
  name: aurora-gui-cloudhub
  namespace: aurora-cloudbank
spec:
  selector:
    app: aurora-gui-cloudhub
  ports:
    - port: 80
      targetPort: 8000
""",
    )
    write_file(
        base / "aurora-nemo-deployment.yaml",
        """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aurora-nemo-service
  namespace: aurora-cloudbank
""",
    )
    write_file(
        base / "aurora-nemo-service.yaml",
        """
apiVersion: v1
kind: Service
metadata:
  name: aurora-nemo-service
  namespace: aurora-cloudbank
""",
    )
    write_file(
        root / k8s_readiness.WORKFLOW_PATH,
        """
name: Kubernetes CI/CD Pipeline
on:
  push:
    branches: [main]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo ghcr.io
  deploy:
    runs-on: ubuntu-latest
    steps:
      - run: echo deploy
""",
    )
    for script_path in k8s_readiness.DEPLOYMENT_SCRIPTS:
        path = root / script_path
        write_file(path, "#!/bin/bash\n# --help\n# --dry-run\nDRY_RUN=false\n")
        make_executable(path)


def gate_by_id(payload: dict[str, Any], gate_id: str) -> dict[str, Any]:
    return next(gate for gate in payload["gates"] if gate["gate_id"] == gate_id)


def test_ready_kubernetes_surface_without_apply_blockers(tmp_path: Path) -> None:
    seed_devcontainer(tmp_path)
    seed_k8s_surface(tmp_path)

    payload = k8s_readiness.build_report(tmp_path, runner=fake_runner, generated_at="2026-06-26T00:00:00Z")

    assert payload["status"] == "ready"
    assert payload["mutation_posture"] == "advisory_only"
    assert payload["nested_repo_mutation"] is False
    assert payload["live_runtime_execution"] is False
    assert payload["cluster_probe"]["status"] == "skipped"
    assert gate_by_id(payload, "kubectl_client_available")["status"] == "ready"
    assert gate_by_id(payload, "k8s_core_resources_present")["status"] == "ready"
    assert gate_by_id(payload, "k8s_apply_blockers_cleared")["status"] == "ready"
    assert payload["summary"]["manifest_file_count"] >= 6
    assert payload["summary"]["apply_blocker_count"] == 0
    assert payload["apply_blockers"] == []
    assert payload["remediation_plan"] == []


def test_placeholders_mark_report_attention(tmp_path: Path) -> None:
    seed_devcontainer(tmp_path)
    seed_k8s_surface(tmp_path, with_placeholders=True)

    payload = k8s_readiness.build_report(tmp_path, runner=fake_runner, generated_at="2026-06-26T00:00:00Z")

    assert payload["status"] == "attention"
    blocker_gate = gate_by_id(payload, "k8s_apply_blockers_cleared")
    assert blocker_gate["status"] == "attention"
    assert blocker_gate["evidence"]["apply_blocker_count"] > 0
    assert payload["summary"]["apply_blocker_count"] == len(payload["apply_blockers"])
    categories = payload["summary"]["apply_blocker_category_counts"]
    assert categories["mutable_or_local_image"] == 1
    assert categories["secret_placeholder"] == 1
    assert payload["apply_blockers"]
    assert all("placeholder-openai-key" not in finding["snippet"] for finding in payload["apply_blockers"])
    assert {item["category"] for item in payload["remediation_plan"]} == {"mutable_or_local_image", "secret_placeholder"}


def test_comment_only_examples_are_informational_not_apply_blockers(tmp_path: Path) -> None:
    seed_devcontainer(tmp_path)
    seed_k8s_surface(tmp_path)
    write_file(
        tmp_path / k8s_readiness.K8S_PATH / "aurora-ingress.yaml",
        """
# host: aurora.example.com
# image: your-registry.io/aurora-cloudbank-symbolic:v1.0.0
apiVersion: v1
kind: ConfigMap
metadata:
  name: example-comments-only
  namespace: aurora-cloudbank
data:
  mode: documentation-only
""",
    )

    payload = k8s_readiness.build_report(tmp_path, runner=fake_runner, generated_at="2026-06-26T00:00:00Z")

    assert payload["status"] == "ready"
    assert payload["summary"]["apply_blocker_count"] == 0
    assert payload["summary"]["informational_finding_count"] == 2
    assert payload["apply_blockers"] == []


def test_missing_required_manifest_blocks_report(tmp_path: Path) -> None:
    seed_devcontainer(tmp_path)
    seed_k8s_surface(tmp_path)
    (tmp_path / k8s_readiness.K8S_PATH / "aurora-gui-cloudhub-service.yaml").unlink()

    payload = k8s_readiness.build_report(tmp_path, runner=fake_runner, generated_at="2026-06-26T00:00:00Z")

    assert payload["status"] == "blocked"
    assert gate_by_id(payload, "k8s_manifest_surface_present")["status"] == "blocked"


def test_yaml_parse_error_blocks_report(tmp_path: Path) -> None:
    seed_devcontainer(tmp_path)
    seed_k8s_surface(tmp_path)
    write_file(tmp_path / k8s_readiness.K8S_PATH / "aurora-gui-cloudhub-service.yaml", "apiVersion: [broken\n")

    payload = k8s_readiness.build_report(tmp_path, runner=fake_runner, generated_at="2026-06-26T00:00:00Z")

    assert payload["status"] == "blocked"
    assert gate_by_id(payload, "k8s_yaml_parse_valid")["status"] == "blocked"


def test_kubectl_missing_blocks_report(tmp_path: Path) -> None:
    seed_devcontainer(tmp_path)
    seed_k8s_surface(tmp_path)

    def missing_kubectl(args: list[str], timeout: int) -> k8s_readiness.CommandResult:
        if args[:2] == ["kubectl", "version"]:
            return command_result(args, returncode=127, stderr="missing")
        return fake_runner(args, timeout)

    payload = k8s_readiness.build_report(tmp_path, runner=missing_kubectl, generated_at="2026-06-26T00:00:00Z")

    assert payload["status"] == "blocked"
    assert gate_by_id(payload, "kubectl_client_available")["status"] == "blocked"


def test_write_report_creates_parent_dirs(tmp_path: Path) -> None:
    seed_devcontainer(tmp_path)
    seed_k8s_surface(tmp_path)
    payload = k8s_readiness.build_report(tmp_path, runner=fake_runner, generated_at="2026-06-26T00:00:00Z")
    out = tmp_path / "reports/analysis/aurora_kubernetes_readiness_latest.json"

    k8s_readiness.write_report(out, payload)

    saved = json.loads(out.read_text(encoding="utf-8"))
    assert saved["tool"] == "aurora_kubernetes_readiness"

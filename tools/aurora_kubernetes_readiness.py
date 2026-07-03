#!/usr/bin/env python3
"""Build a read-only Kubernetes readiness receipt for Aurora.

This tool inventories the existing CloudBank Kubernetes deployment surface and
local Kubernetes client tooling. It validates manifest shape and highlights
apply blockers, but it does not connect to a cluster by default, run
``kubectl apply``, mutate manifests, create secrets, or deploy workloads.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

import yaml


DEFAULT_REPORT_PATH = Path("reports/analysis/aurora_kubernetes_readiness_latest.json")
CLOUDBANK_PATH = Path("GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main")
K8S_PATH = CLOUDBANK_PATH / "k8s"
DEVCONTAINER_PATH = Path(".devcontainer/devcontainer.json")

REQUIRED_MANIFESTS = [
    "aurora-namespace-rbac.yaml",
    "aurora-configmap-secrets.yaml",
    "aurora-gui-cloudhub-deployment.yaml",
    "aurora-gui-cloudhub-service.yaml",
]
OPTIONAL_MANIFESTS = [
    "aurora-hpa-monitoring.yaml",
    "aurora-ingress.yaml",
    "aurora-nemo-deployment.yaml",
    "aurora-nemo-service.yaml",
    "aurora-sealed-secrets-template.yaml",
    "deployment/aurora-cloudbank.yml",
]
DEPLOYMENT_SCRIPTS = [
    CLOUDBANK_PATH / "scripts/k8s_deploy_relays.sh",
    CLOUDBANK_PATH / "scripts/k8s_deploy_mcp.sh",
    CLOUDBANK_PATH / "scripts/k8s_deploy_firewall.sh",
]
WORKFLOW_PATH = CLOUDBANK_PATH / ".github/workflows/k8s-deploy.yml"

PLACEHOLDER_PATTERNS = [
    re.compile(r"placeholder", re.IGNORECASE),
    re.compile(r"REPLACE_WITH_", re.IGNORECASE),
    re.compile(r"your-registry\.io", re.IGNORECASE),
    re.compile(r"aurora\.example\.com", re.IGNORECASE),
]
LOCAL_OR_MUTABLE_IMAGE_RE = re.compile(r"image:\s*(?:aurora-cloudbank-symbolic|aurora-gui-cloudhub|.*:latest)\b")
SECRET_VALUE_RE = re.compile(
    r"(?P<prefix>\b(?:anthropic-api-key|openai-api-key|csrf-secret-key|jwt-secret-key)\s*:\s*)"
    r"(?P<quote>[\"']?)(?P<value>[^#\s\"']+)(?P=quote)"
)
MAX_SNIPPET_LENGTH = 180

REMEDIATION_BY_CATEGORY = {
    "example_domain": "Replace example ingress hosts/email with an owned local or staging domain, or exclude ingress from the apply set.",
    "example_registry": "Replace example registry references with the real registry path before deployment.",
    "mutable_or_local_image": "Publish the image to a registry and pin it to an immutable digest or release tag before applying deployments.",
    "placeholder_value": "Replace placeholder manifest values with environment-specific configuration before cluster dry-run.",
    "sealed_secret_template_placeholder": "Generate sealed values with kubeseal, or exclude the sealed-secret template from the apply set.",
    "secret_placeholder": "Replace placeholder Secret entries through sealed-secrets or external secret management; do not commit live plaintext secrets.",
}


@dataclass
class CommandResult:
    args: list[str]
    returncode: int
    stdout: str
    stderr: str


Runner = Callable[[list[str], int], CommandResult]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_command(args: list[str], timeout: int) -> CommandResult:
    try:
        completed = subprocess.run(args, text=True, capture_output=True, timeout=timeout, check=False)
        return CommandResult(args, completed.returncode, completed.stdout, completed.stderr)
    except subprocess.TimeoutExpired as exc:
        return CommandResult(args, 124, exc.stdout or "", exc.stderr or "command timed out")
    except OSError as exc:
        return CommandResult(args, 127, "", str(exc))


def normalize_status(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"ready", "ok", "pass", "passed", "clean"}:
        return "ready"
    if text in {"blocked", "fail", "failed", "error"}:
        return "blocked"
    if text in {"attention", "missing", "unknown", "warn", "warning", "skipped"}:
        return "attention"
    return text or "unknown"


def relpath(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def category_counts(findings: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        category = str(finding.get("category") or "unknown")
        counts[category] = counts.get(category, 0) + 1
    return dict(sorted(counts.items()))


def redact_snippet(line: str) -> str:
    snippet = line.strip()
    if SECRET_VALUE_RE.search(snippet):
        snippet = snippet.split("#", 1)[0].rstrip()
        snippet = SECRET_VALUE_RE.sub(
            lambda match: f"{match.group('prefix')}{match.group('quote')}<redacted>{match.group('quote')}",
            snippet,
        )
    if len(snippet) > MAX_SNIPPET_LENGTH:
        return f"{snippet[: MAX_SNIPPET_LENGTH - 3]}..."
    return snippet


def manifest_finding(
    path: Path,
    root: Path,
    line_number: int,
    category: str,
    detail: str,
    *,
    blocks_apply: bool,
    line: str,
) -> dict[str, Any]:
    return {
        "path": relpath(path, root),
        "line": line_number,
        "category": category,
        "severity": "attention" if blocks_apply else "info",
        "blocks_apply": blocks_apply,
        "detail": detail,
        "snippet": redact_snippet(line),
    }


def classify_manifest_line(path: Path, root: Path, line_number: int, line: str) -> list[dict[str, Any]]:
    stripped = line.strip()
    if not stripped:
        return []

    lowered = stripped.lower()
    comment_only = stripped.startswith("#")
    findings: list[dict[str, Any]] = []

    def add(category: str, detail: str, *, blocks_apply: bool) -> None:
        findings.append(
            manifest_finding(
                path,
                root,
                line_number,
                category,
                detail,
                blocks_apply=blocks_apply,
                line=line,
            )
        )

    if LOCAL_OR_MUTABLE_IMAGE_RE.search(stripped) and not comment_only:
        add(
            "mutable_or_local_image",
            "Image reference is local or mutable; a repeatable apply needs a registry reference pinned to a digest or release tag.",
            blocks_apply=True,
        )
        return findings

    if "replace_with_" in lowered:
        add(
            "sealed_secret_template_placeholder",
            "SealedSecret template still contains kube-seal replacement placeholders.",
            blocks_apply=not comment_only,
        )
        return findings

    if "aurora.example.com" in lowered or "admin@aurora.example.com" in lowered:
        add(
            "example_domain",
            "Ingress or certificate configuration still references example Aurora domains.",
            blocks_apply=not comment_only,
        )

    if "your-registry.io" in lowered:
        add(
            "example_registry",
            "Manifest still references an example image registry.",
            blocks_apply=not comment_only,
        )

    placeholder_like = "placeholder" in lowered or "your-actual-key" in lowered or "your_actual_key" in lowered
    if placeholder_like:
        if comment_only:
            add(
                "comment_only_example",
                "Comment-only placeholder/example text is documentation context, not an apply blocker.",
                blocks_apply=False,
            )
        elif SECRET_VALUE_RE.search(stripped):
            add(
                "secret_placeholder",
                "Secret manifest still contains placeholder API key material.",
                blocks_apply=True,
            )
        else:
            add(
                "placeholder_value",
                "Manifest still contains an active placeholder value.",
                blocks_apply=True,
            )

    return findings


def scan_manifest_findings(path: Path, root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        findings.extend(classify_manifest_line(path, root, line_number, line))
    return findings


def tool_record(tool_id: str, args: list[str], runner: Runner, timeout: int) -> dict[str, Any]:
    result = runner(args, timeout)
    record = {
        "id": tool_id,
        "command": args,
        "status": "ready" if result.returncode == 0 else "attention",
        "returncode": result.returncode,
        "stdout_preview": result.stdout[:400],
        "stderr_preview": result.stderr[:400],
    }
    if tool_id == "kubectl" and result.returncode == 0:
        try:
            payload = json.loads(result.stdout)
            client = payload.get("clientVersion", {})
            record["version"] = client.get("gitVersion")
            record["platform"] = client.get("platform")
            record["kustomize_version"] = payload.get("kustomizeVersion")
        except json.JSONDecodeError:
            record["status"] = "attention"
            record["parse_error"] = "kubectl client version output was not JSON"
    elif tool_id == "helm" and result.returncode == 0:
        record["version"] = result.stdout.strip()
    return record


def read_devcontainer(root: Path) -> dict[str, Any]:
    path = root / DEVCONTAINER_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"available": False, "path": DEVCONTAINER_PATH.as_posix(), "status": "missing"}
    except json.JSONDecodeError as exc:
        return {
            "available": False,
            "path": DEVCONTAINER_PATH.as_posix(),
            "status": "attention",
            "error": f"invalid_json: {exc.msg}",
        }

    features = payload.get("features") if isinstance(payload.get("features"), dict) else {}
    kube_feature = next((key for key in features if "kubectl-helm-minikube" in key), None)
    return {
        "available": True,
        "path": DEVCONTAINER_PATH.as_posix(),
        "status": "ready" if kube_feature else "attention",
        "kubectl_helm_minikube_feature": kube_feature,
        "feature_config": features.get(kube_feature) if kube_feature else None,
    }


def manifest_paths(root: Path) -> list[Path]:
    base = root / K8S_PATH
    paths: list[Path] = []
    if base.exists():
        paths.extend(sorted(base.glob("*.yaml")))
        deployment_dir = base / "deployment"
        if deployment_dir.exists():
            paths.extend(sorted(deployment_dir.glob("*.yaml")))
            paths.extend(sorted(deployment_dir.glob("*.yml")))
    return paths


def load_manifest_documents(path: Path) -> tuple[list[dict[str, Any]], Optional[str]]:
    try:
        documents = list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
    except Exception as exc:  # noqa: BLE001 - report parser failure as data
        return [], str(exc)

    resources: list[dict[str, Any]] = []
    for index, document in enumerate(documents, start=1):
        if document is None:
            continue
        if not isinstance(document, dict):
            resources.append({"document_index": index, "valid": False, "error": "document is not an object"})
            continue
        resources.append(
            {
                "document_index": index,
                "valid": bool(document.get("apiVersion") and document.get("kind")),
                "api_version": document.get("apiVersion"),
                "kind": document.get("kind"),
                "name": (document.get("metadata") or {}).get("name") if isinstance(document.get("metadata"), dict) else None,
                "namespace": (document.get("metadata") or {}).get("namespace")
                if isinstance(document.get("metadata"), dict)
                else None,
            }
        )
    return resources, None


def scan_manifest_file(path: Path, root: Path) -> dict[str, Any]:
    resources, parse_error = load_manifest_documents(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    findings = scan_manifest_findings(path, root)
    apply_blockers = [finding for finding in findings if finding["blocks_apply"]]
    placeholder_hits = [
        pattern.pattern
        for pattern in PLACEHOLDER_PATTERNS
        if pattern.search(text)
    ]
    mutable_image_count = len(LOCAL_OR_MUTABLE_IMAGE_RE.findall(text))
    return {
        "path": relpath(path, root),
        "status": "blocked" if parse_error else "ready",
        "parse_error": parse_error,
        "resource_count": len(resources),
        "resources": resources,
        "placeholder_hit_count": len(placeholder_hits),
        "placeholder_patterns": placeholder_hits,
        "mutable_or_local_image_reference_count": mutable_image_count,
        "finding_count": len(findings),
        "apply_blocker_count": len(apply_blockers),
        "finding_category_counts": category_counts(findings),
        "apply_blocker_category_counts": category_counts(apply_blockers),
        "findings": findings,
    }


def collect_manifests(root: Path) -> dict[str, Any]:
    base = root / K8S_PATH
    paths = manifest_paths(root)
    files = [scan_manifest_file(path, root) for path in paths]
    resources = [resource for file in files for resource in file["resources"] if resource.get("valid")]
    findings = [finding for file in files for finding in file.get("findings", [])]
    apply_blockers = [finding for finding in findings if finding["blocks_apply"]]
    informational_findings = [finding for finding in findings if not finding["blocks_apply"]]
    kinds: dict[str, int] = {}
    for resource in resources:
        kind = str(resource.get("kind") or "unknown")
        kinds[kind] = kinds.get(kind, 0) + 1

    required = []
    for filename in REQUIRED_MANIFESTS:
        path = root / K8S_PATH / filename
        required.append({"path": relpath(path, root), "exists": path.exists()})
    optional = []
    for filename in OPTIONAL_MANIFESTS:
        path = root / K8S_PATH / filename
        optional.append({"path": relpath(path, root), "exists": path.exists()})

    return {
        "path": K8S_PATH.as_posix(),
        "exists": base.exists(),
        "manifest_file_count": len(files),
        "resource_count": len(resources),
        "kind_counts": kinds,
        "required_manifests": required,
        "optional_manifests": optional,
        "files": files,
        "finding_count": len(findings),
        "apply_blocker_count": len(apply_blockers),
        "informational_finding_count": len(informational_findings),
        "finding_category_counts": category_counts(findings),
        "apply_blocker_category_counts": category_counts(apply_blockers),
        "apply_blockers": apply_blockers,
        "informational_findings": informational_findings,
    }


def build_remediation_plan(apply_blockers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = category_counts(apply_blockers)
    plan = []
    for category, count in counts.items():
        plan.append(
            {
                "category": category,
                "blocker_count": count,
                "recommended_next_action": REMEDIATION_BY_CATEGORY.get(
                    category,
                    "Review and resolve this apply blocker before cluster dry-run.",
                ),
            }
        )
    return plan


def resource_present(manifests: dict[str, Any], kind: str, name: str) -> bool:
    for file in manifests["files"]:
        for resource in file.get("resources", []):
            if resource.get("valid") and resource.get("kind") == kind and resource.get("name") == name:
                return True
    return False


def script_record(path: Path, root: Path) -> dict[str, Any]:
    exists = path.exists()
    content = path.read_text(encoding="utf-8", errors="replace") if exists else ""
    return {
        "path": relpath(path, root),
        "exists": exists,
        "executable": path.exists() and path.stat().st_mode & 0o111 != 0,
        "has_dry_run": "--dry-run" in content or "DRY_RUN" in content,
        "has_help": "--help" in content or "-h" in content,
    }


def workflow_record(root: Path) -> dict[str, Any]:
    path = root / WORKFLOW_PATH
    if not path.exists():
        return {"path": WORKFLOW_PATH.as_posix(), "exists": False, "status": "missing"}
    resources, parse_error = load_manifest_documents(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        "path": WORKFLOW_PATH.as_posix(),
        "exists": True,
        "status": "blocked" if parse_error else "ready",
        "parse_error": parse_error,
        "has_build_job": "build:" in text.lower(),
        "has_deploy_job": "deploy" in text.lower(),
        "uses_ghcr": "ghcr.io" in text,
        "document_count": len(resources),
    }


def gate(
    gate_id: str,
    title: str,
    status: str,
    *,
    required: bool,
    evidence: Optional[dict[str, Any]] = None,
    recommended_next_action: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "title": title,
        "status": normalize_status(status),
        "required": required,
        "evidence": evidence or {},
        "recommended_next_action": recommended_next_action,
    }


def build_gates(
    toolchain: dict[str, Any],
    manifests: dict[str, Any],
    scripts: list[dict[str, Any]],
    workflow: dict[str, Any],
) -> list[dict[str, Any]]:
    required_missing = [item["path"] for item in manifests["required_manifests"] if not item["exists"]]
    parse_errors = [file["path"] for file in manifests["files"] if file["parse_error"]]
    apply_blockers = manifests.get("apply_blockers", [])
    blocker_files = sorted({finding["path"] for finding in apply_blockers})
    scripts_ready = all(script["exists"] and script["executable"] and script["has_dry_run"] for script in scripts)
    core_resources_ready = all(
        [
            resource_present(manifests, "Namespace", "aurora-cloudbank"),
            resource_present(manifests, "Deployment", "aurora-gui-cloudhub"),
            resource_present(manifests, "Service", "aurora-gui-cloudhub"),
        ]
    )
    nemo_surface_ready = resource_present(manifests, "Deployment", "aurora-nemo-service") and resource_present(
        manifests, "Service", "aurora-nemo-service"
    )
    return [
        gate(
            "kubectl_client_available",
            "kubectl client is available locally",
            "ready" if toolchain["kubectl"]["status"] == "ready" else "blocked",
            required=True,
            evidence={
                "version": toolchain["kubectl"].get("version"),
                "platform": toolchain["kubectl"].get("platform"),
                "kustomize_version": toolchain["kubectl"].get("kustomize_version"),
            },
            recommended_next_action=None
            if toolchain["kubectl"]["status"] == "ready"
            else "Install or repair kubectl before Kubernetes validation.",
        ),
        gate(
            "k8s_manifest_surface_present",
            "CloudBank Kubernetes manifest surface is present",
            "ready" if manifests["exists"] and not required_missing else "blocked",
            required=True,
            evidence={"path": manifests["path"], "missing_required": required_missing},
            recommended_next_action=None if not required_missing else "Restore required CloudBank k8s manifests.",
        ),
        gate(
            "k8s_yaml_parse_valid",
            "Kubernetes YAML parses cleanly",
            "ready" if not parse_errors else "blocked",
            required=True,
            evidence={"parse_error_files": parse_errors, "manifest_file_count": manifests["manifest_file_count"]},
            recommended_next_action=None if not parse_errors else "Fix YAML parse errors before any cluster dry-run.",
        ),
        gate(
            "k8s_core_resources_present",
            "Core namespace, GUI deployment, and service resources are present",
            "ready" if core_resources_ready else "blocked",
            required=True,
            evidence={
                "namespace": resource_present(manifests, "Namespace", "aurora-cloudbank"),
                "gui_deployment": resource_present(manifests, "Deployment", "aurora-gui-cloudhub"),
                "gui_service": resource_present(manifests, "Service", "aurora-gui-cloudhub"),
            },
            recommended_next_action=None
            if core_resources_ready
            else "Restore namespace, deployment, and service before deployment planning.",
        ),
        gate(
            "k8s_apply_blockers_cleared",
            "Known apply blockers are cleared",
            "attention" if apply_blockers else "ready",
            required=True,
            evidence={
                "apply_blocker_count": len(apply_blockers),
                "apply_blocker_category_counts": manifests.get("apply_blocker_category_counts", {}),
                "blocker_files": blocker_files,
            },
            recommended_next_action=None
            if not apply_blockers
            else "Resolve the listed apply_blockers entries before kubectl apply or cluster dry-run.",
        ),
        gate(
            "k8s_gpu_nemo_surface_present",
            "Optional NeMo GPU Kubernetes surface is present",
            "ready" if nemo_surface_ready else "attention",
            required=False,
            evidence={
                "nemo_deployment": resource_present(manifests, "Deployment", "aurora-nemo-service"),
                "nemo_service": resource_present(manifests, "Service", "aurora-nemo-service"),
            },
            recommended_next_action=None
            if nemo_surface_ready
            else "Keep GPU lane gated unless local cluster GPU support is explicitly verified.",
        ),
        gate(
            "k8s_deployment_scripts_dry_run_capable",
            "Kubernetes deployment scripts are present and dry-run capable",
            "ready" if scripts_ready else "attention",
            required=False,
            evidence={"scripts": scripts},
            recommended_next_action=None if scripts_ready else "Repair deploy scripts before relying on scripted rollout.",
        ),
        gate(
            "k8s_workflow_present",
            "Kubernetes CI workflow is present",
            workflow["status"] if workflow["exists"] else "attention",
            required=False,
            evidence={
                "path": workflow["path"],
                "has_build_job": workflow.get("has_build_job"),
                "has_deploy_job": workflow.get("has_deploy_job"),
                "uses_ghcr": workflow.get("uses_ghcr"),
            },
            recommended_next_action=None if workflow.get("uses_ghcr") else "Review Kubernetes workflow before CI deployment use.",
        ),
    ]


def summarize(gates: list[dict[str, Any]], manifests: dict[str, Any]) -> dict[str, Any]:
    required = [item for item in gates if item["required"]]
    optional = [item for item in gates if not item["required"]]
    return {
        "gate_count": len(gates),
        "required_gate_count": len(required),
        "optional_gate_count": len(optional),
        "ready_gate_count": sum(1 for item in gates if item["status"] == "ready"),
        "attention_gate_count": sum(1 for item in gates if item["status"] == "attention"),
        "blocked_gate_count": sum(1 for item in gates if item["status"] == "blocked"),
        "required_ready": sum(1 for item in required if item["status"] == "ready"),
        "required_total": len(required),
        "optional_ready": sum(1 for item in optional if item["status"] == "ready"),
        "optional_total": len(optional),
        "manifest_file_count": manifests["manifest_file_count"],
        "resource_count": manifests["resource_count"],
        "kind_counts": manifests["kind_counts"],
        "finding_count": manifests.get("finding_count", 0),
        "apply_blocker_count": manifests.get("apply_blocker_count", 0),
        "informational_finding_count": manifests.get("informational_finding_count", 0),
        "apply_blocker_category_counts": manifests.get("apply_blocker_category_counts", {}),
    }


def report_status(gates: list[dict[str, Any]]) -> str:
    required = [item for item in gates if item["required"]]
    if any(item["status"] == "blocked" for item in required):
        return "blocked"
    if any(item["status"] != "ready" for item in required):
        return "attention"
    return "ready"


def build_report(root: Path, *, runner: Runner = run_command, generated_at: Optional[str] = None, timeout: int = 10) -> dict[str, Any]:
    toolchain = {
        "kubectl": tool_record("kubectl", ["kubectl", "version", "--client=true", "--output=json"], runner, timeout),
        "helm": tool_record("helm", ["helm", "version", "--template", "{{.Version}}\\n"], runner, timeout),
    }
    manifests = collect_manifests(root)
    scripts = [script_record(root / path, root) for path in DEPLOYMENT_SCRIPTS]
    workflow = workflow_record(root)
    gates = build_gates(toolchain, manifests, scripts, workflow)
    summary = summarize(gates, manifests)
    apply_blockers = manifests.get("apply_blockers", [])
    return {
        "schema_version": 1,
        "tool": "aurora_kubernetes_readiness",
        "generated_at": generated_at or utc_now(),
        "root": str(root),
        "status": report_status(gates),
        "run_mode": "read_only",
        "mutation_posture": "advisory_only",
        "nested_repo_mutation": False,
        "cluster_probe": {
            "status": "skipped",
            "reason": "Cluster probing is intentionally omitted; this receipt is manifest/client readiness only.",
        },
        "live_runtime_execution": False,
        "summary": summary,
        "toolchain": toolchain,
        "devcontainer": read_devcontainer(root),
        "manifests": manifests,
        "apply_blockers": apply_blockers,
        "remediation_plan": build_remediation_plan(apply_blockers),
        "deployment_scripts": scripts,
        "workflow": workflow,
        "gates": gates,
        "validation_commands": [
            "python3 tools/aurora_kubernetes_readiness.py --persist-report --summary",
            "python3 tools/aurora_operator_snapshot.py --persist-report --summary",
            "python3 -m pytest -q tests/test_aurora_kubernetes_readiness.py tests/test_aurora_operator_snapshot.py",
        ],
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def print_summary(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    print(f"status: {payload['status']}")
    print(f"required_gates: {summary['required_ready']}/{summary['required_total']}")
    print(f"optional_gates: {summary['optional_ready']}/{summary['optional_total']}")
    print(f"manifests: {summary['manifest_file_count']}")
    print(f"resources: {summary['resource_count']}")
    print(f"apply_blockers: {summary['apply_blocker_count']}")
    print(f"cluster_probe: {payload['cluster_probe']['status']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the read-only Aurora Kubernetes readiness receipt.")
    parser.add_argument("--root", default=".", help="Workspace root. Defaults to current directory.")
    parser.add_argument("--report-out", help="Write the report to this path.")
    parser.add_argument("--persist-report", action="store_true", help=f"Write {DEFAULT_REPORT_PATH}.")
    parser.add_argument("--timeout", type=int, default=10, help="Client tool timeout in seconds.")
    parser.add_argument("--summary", action="store_true", help="Print a concise summary instead of JSON.")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    payload = build_report(root, timeout=args.timeout)

    if args.persist_report:
        write_report(root / DEFAULT_REPORT_PATH, payload)
    if args.report_out:
        write_report(Path(args.report_out), payload)

    if args.summary:
        print_summary(payload)
    elif args.json or not (args.persist_report or args.report_out):
        print(json.dumps(payload, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

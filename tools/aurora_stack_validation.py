#!/usr/bin/env python3
"""Validate the local Aurora Docker Desktop stack and write a durable receipt.

This is read-only runtime evidence for the operator console. It inspects the
registered CloudBank compose stack and optional localhost endpoints; it does not
build images, start services, mutate nested repos, or execute Aurora commands.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Optional


DEFAULT_REPORT_PATH = Path("reports/analysis/aurora_stack_validation_latest.json")
CLOUDBANK_PATH = Path("GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main")

DEFAULT_SERVICES = {
    "aurora_gui": {
        "required": True,
        "profile": "default",
        "port": 8080,
        "endpoint": "http://127.0.0.1:8080/api/operator/snapshot",
    },
    "command_node": {
        "required": True,
        "profile": "default",
        "port": 3001,
        "endpoint": "http://127.0.0.1:3001/",
    },
    "nemo_service": {
        "required": False,
        "profile": "gpu",
        "port": 8090,
        "endpoint": "http://127.0.0.1:8090/nemo/health",
    },
}


@dataclass
class CommandResult:
    args: list[str]
    cwd: str
    returncode: int
    stdout: str
    stderr: str


Runner = Callable[[list[str], Path, int], CommandResult]
HttpGetter = Callable[[str, int], dict[str, Any]]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_command(args: list[str], cwd: Path, timeout: int) -> CommandResult:
    try:
        completed = subprocess.run(
            args,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return CommandResult(args, str(cwd), completed.returncode, completed.stdout, completed.stderr)
    except subprocess.TimeoutExpired as exc:
        return CommandResult(args, str(cwd), 124, exc.stdout or "", exc.stderr or "command timed out")
    except OSError as exc:
        return CommandResult(args, str(cwd), 127, "", str(exc))


def http_get(url: str, timeout: int) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read(2048)
            content_type = response.headers.get("content-type", "")
            return {
                "url": url,
                "status": "ready" if 200 <= response.status < 400 else "blocked",
                "http_status": response.status,
                "content_type": content_type,
                "body_preview": body.decode("utf-8", errors="replace")[:240],
            }
    except urllib.error.HTTPError as exc:
        return {
            "url": url,
            "status": "blocked",
            "http_status": exc.code,
            "error": str(exc),
        }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {
            "url": url,
            "status": "blocked",
            "http_status": None,
            "error": str(exc),
        }


def parse_compose_ps(output: str) -> tuple[list[dict[str, Any]], Optional[str]]:
    text = output.strip()
    if not text:
        return [], None
    try:
        payload = json.loads(text)
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)], None
        if isinstance(payload, dict):
            return [payload], None
        return [], "compose ps JSON was not an object or array"
    except json.JSONDecodeError:
        records: list[dict[str, Any]] = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as exc:
                return records, f"invalid compose ps JSON line: {exc.msg}"
            if isinstance(payload, dict):
                records.append(payload)
        return records, None


def normalize_status(value: Any) -> str:
    if value is None:
        return "unknown"
    text = str(value).strip().lower()
    if text in {"ready", "ok", "healthy", "running", "up"}:
        return "ready"
    if text in {"blocked", "error", "fail", "failed", "unhealthy", "exited", "dead"}:
        return "blocked"
    if text in {"gated", "profile_gated"}:
        return "gated"
    if text in {"attention", "missing", "unknown", "created", "restarting"}:
        return "attention"
    return text or "unknown"


def worst_status(statuses: Iterable[str]) -> str:
    ordered = [normalize_status(status) for status in statuses]
    if any(status == "blocked" for status in ordered):
        return "blocked"
    if any(status in {"attention", "missing", "unknown"} for status in ordered):
        return "attention"
    return "ready"


def service_name(record: dict[str, Any]) -> str:
    return str(record.get("Service") or record.get("service") or record.get("Name") or record.get("name") or "")


def classify_service(expected: dict[str, Any], record: Optional[dict[str, Any]]) -> dict[str, Any]:
    if record is None:
        status = "blocked" if expected["required"] else "gated"
        return {
            "status": status,
            "running": False,
            "health": "missing" if expected["required"] else "profile_gated",
            "state": "missing",
            "required": expected["required"],
            "profile": expected["profile"],
        }

    state = str(record.get("State") or record.get("state") or "").lower()
    health = str(record.get("Health") or record.get("health") or "").lower()
    running = state == "running"
    if running and (not health or health == "healthy"):
        status = "ready"
    elif running:
        status = "attention"
    else:
        status = "blocked" if expected["required"] else "gated"

    return {
        "status": status,
        "running": running,
        "health": health or "none",
        "state": state or "unknown",
        "required": expected["required"],
        "profile": expected["profile"],
        "container": record.get("Name") or record.get("Names"),
        "image": record.get("Image"),
        "ports": record.get("Ports"),
        "status_text": record.get("Status"),
    }


def build_service_records(compose_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_service = {service_name(record): record for record in compose_records if service_name(record)}
    services: list[dict[str, Any]] = []
    for name, expected in DEFAULT_SERVICES.items():
        service = {
            "service": name,
            "port": expected["port"],
            "endpoint": expected["endpoint"],
            **classify_service(expected, by_service.get(name)),
        }
        services.append(service)
    return services


def collect_http_endpoints(
    services: list[dict[str, Any]],
    *,
    getter: HttpGetter,
    timeout: int,
    skip_http: bool,
) -> list[dict[str, Any]]:
    endpoints: list[dict[str, Any]] = []
    for service in services:
        endpoint = service["endpoint"]
        if skip_http or service["status"] in {"gated", "blocked"}:
            endpoints.append(
                {
                    "service": service["service"],
                    "url": endpoint,
                    "status": "skipped" if skip_http else service["status"],
                    "reason": "http_probe_disabled" if skip_http else "service_not_ready",
                }
            )
            continue
        result = getter(endpoint, timeout)
        result["service"] = service["service"]
        endpoints.append(result)
    return endpoints


def command_record(result: CommandResult) -> dict[str, Any]:
    return {
        "command": result.args,
        "cwd": result.cwd,
        "returncode": result.returncode,
        "stdout_preview": result.stdout[:400],
        "stderr_preview": result.stderr[:400],
    }


def build_report(
    root: Path,
    *,
    runner: Runner = run_command,
    getter: HttpGetter = http_get,
    generated_at: Optional[str] = None,
    timeout: int = 20,
    http_timeout: int = 10,
    skip_http: bool = False,
) -> dict[str, Any]:
    compose_dir = root / CLOUDBANK_PATH
    compose_file = compose_dir / "docker-compose.yml"
    commands: list[dict[str, Any]] = []

    if not compose_file.exists():
        return {
            "schema_version": 1,
            "tool": "aurora_stack_validation",
            "generated_at": generated_at or utc_now(),
            "root": str(root),
            "status": "blocked",
            "run_mode": "read_only",
            "mutation_posture": "advisory_only",
            "nested_repo_mutation": False,
            "live_runtime_execution": False,
            "compose": {
                "repo": "aurora-cloudbank-symbolic-main",
                "path": CLOUDBANK_PATH.as_posix(),
                "compose_file": compose_file.as_posix(),
                "exists": False,
            },
            "services": [],
            "endpoints": [],
            "commands": [],
            "summary": {"required_ready": 0, "required_total": 2, "endpoint_ready": 0, "endpoint_total": 0},
            "validation_commands": [
                "python3 tools/aurora_stack_validation.py --summary",
                "python3 tools/aurora_stack_validation.py --persist-report",
                "python3 -m pytest -q tests/test_aurora_stack_validation.py",
            ],
        }

    config_result = runner(["docker", "compose", "config", "--quiet"], compose_dir, timeout)
    commands.append(command_record(config_result))
    ps_result = runner(["docker", "compose", "ps", "--format", "json"], compose_dir, timeout)
    commands.append(command_record(ps_result))

    compose_records, parse_error = parse_compose_ps(ps_result.stdout if ps_result.returncode == 0 else "")
    services = build_service_records(compose_records)
    endpoints = collect_http_endpoints(services, getter=getter, timeout=http_timeout, skip_http=skip_http)

    required = [service for service in services if service["required"]]
    required_ready = sum(1 for service in required if service["status"] == "ready")
    endpoint_candidates = [endpoint for endpoint in endpoints if endpoint["status"] != "skipped"]
    endpoint_ready = sum(1 for endpoint in endpoint_candidates if endpoint["status"] == "ready")
    command_status = "ready" if config_result.returncode == 0 and ps_result.returncode == 0 and not parse_error else "blocked"
    service_status = worst_status(service["status"] for service in required)
    endpoint_status = worst_status(endpoint["status"] for endpoint in endpoint_candidates) if endpoint_candidates else "ready"
    status = worst_status([command_status, service_status, endpoint_status])

    return {
        "schema_version": 1,
        "tool": "aurora_stack_validation",
        "generated_at": generated_at or utc_now(),
        "root": str(root),
        "status": status,
        "run_mode": "read_only",
        "mutation_posture": "advisory_only",
        "nested_repo_mutation": False,
        "live_runtime_execution": False,
        "compose": {
            "repo": "aurora-cloudbank-symbolic-main",
            "path": CLOUDBANK_PATH.as_posix(),
            "compose_file": compose_file.as_posix(),
            "exists": True,
            "config_status": "ready" if config_result.returncode == 0 else "blocked",
            "ps_status": "ready" if ps_result.returncode == 0 and not parse_error else "blocked",
            "parse_error": parse_error,
        },
        "services": services,
        "endpoints": endpoints,
        "commands": commands,
        "summary": {
            "required_ready": required_ready,
            "required_total": len(required),
            "endpoint_ready": endpoint_ready,
            "endpoint_total": len(endpoint_candidates),
            "gpu_profile_status": next(
                (service["status"] for service in services if service["service"] == "nemo_service"),
                "unknown",
            ),
        },
        "validation_commands": [
            "python3 tools/aurora_stack_validation.py --summary",
            "python3 tools/aurora_stack_validation.py --persist-report",
            "python3 -m pytest -q tests/test_aurora_stack_validation.py",
        ],
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def print_summary(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    print(f"status: {payload['status']}")
    print(f"required_services: {summary['required_ready']}/{summary['required_total']}")
    print(f"endpoints: {summary['endpoint_ready']}/{summary['endpoint_total']}")
    print(f"gpu_profile: {summary['gpu_profile_status']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an Aurora Docker stack validation receipt.")
    parser.add_argument("--root", default=".", help="Workspace root. Defaults to current directory.")
    parser.add_argument("--report-out", help="Write the stack validation report to this path.")
    parser.add_argument("--persist-report", action="store_true", help=f"Write {DEFAULT_REPORT_PATH}.")
    parser.add_argument("--summary", action="store_true", help="Print a concise summary instead of JSON.")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout.")
    parser.add_argument("--skip-http", action="store_true", help="Skip localhost HTTP endpoint probes.")
    parser.add_argument("--timeout", type=int, default=20, help="Docker command timeout in seconds.")
    parser.add_argument("--http-timeout", type=int, default=10, help="HTTP probe timeout in seconds.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()
    payload = build_report(
        root,
        timeout=args.timeout,
        http_timeout=args.http_timeout,
        skip_http=args.skip_http,
    )

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

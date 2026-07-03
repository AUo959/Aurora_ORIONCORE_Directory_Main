from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_ROOT))

import aurora_stack_validation as stack_validation  # noqa: E402


def write_file(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def compose_record(service: str, *, state: str = "running", health: str = "healthy") -> dict[str, Any]:
    return {
        "Service": service,
        "Name": f"aurora-cloudbank-symbolic-main-{service}-1",
        "Image": f"aurora-cloudbank-symbolic-main-{service}",
        "State": state,
        "Health": health,
        "Status": "Up 2 minutes (healthy)" if health == "healthy" else f"Up 2 minutes ({health})",
        "Ports": "127.0.0.1:8080->8080/tcp" if service == "aurora_gui" else "127.0.0.1:3001->3001/tcp",
    }


def fake_runner(records: list[dict[str, Any]], *, config_returncode: int = 0) -> stack_validation.Runner:
    def run(args: list[str], cwd: Path, timeout: int) -> stack_validation.CommandResult:
        if args == ["docker", "compose", "config", "--quiet"]:
            return stack_validation.CommandResult(args, str(cwd), config_returncode, "", "bad config" if config_returncode else "")
        if args == ["docker", "compose", "ps", "--format", "json"]:
            stdout = "\n".join(json.dumps(record) for record in records) + "\n"
            return stack_validation.CommandResult(args, str(cwd), 0, stdout, "")
        raise AssertionError(args)

    return run


def ready_getter(url: str, timeout: int) -> dict[str, Any]:
    return {"url": url, "status": "ready", "http_status": 200, "body_preview": "ok"}


def blocked_getter(url: str, timeout: int) -> dict[str, Any]:
    return {"url": url, "status": "blocked", "http_status": None, "error": "connection refused"}


def seed_compose(root: Path) -> None:
    write_file(root / stack_validation.CLOUDBANK_PATH / "docker-compose.yml", "services: {}\n")


def test_parse_compose_ps_accepts_json_lines() -> None:
    output = json.dumps(compose_record("aurora_gui")) + "\n" + json.dumps(compose_record("command_node")) + "\n"

    records, error = stack_validation.parse_compose_ps(output)

    assert error is None
    assert [record["Service"] for record in records] == ["aurora_gui", "command_node"]


def test_build_report_ready_for_default_services_with_gpu_gated(tmp_path: Path) -> None:
    seed_compose(tmp_path)
    records = [compose_record("aurora_gui"), compose_record("command_node")]

    payload = stack_validation.build_report(
        tmp_path,
        runner=fake_runner(records),
        getter=ready_getter,
        generated_at="2026-06-26T00:00:00Z",
    )

    assert payload["status"] == "ready"
    assert payload["summary"]["required_ready"] == 2
    assert payload["summary"]["endpoint_ready"] == 2
    assert payload["summary"]["gpu_profile_status"] == "gated"
    assert next(service for service in payload["services"] if service["service"] == "nemo_service")["status"] == "gated"


def test_build_report_blocks_when_required_service_missing(tmp_path: Path) -> None:
    seed_compose(tmp_path)
    records = [compose_record("aurora_gui")]

    payload = stack_validation.build_report(
        tmp_path,
        runner=fake_runner(records),
        getter=ready_getter,
        generated_at="2026-06-26T00:00:00Z",
    )

    assert payload["status"] == "blocked"
    assert payload["summary"]["required_ready"] == 1
    missing = next(service for service in payload["services"] if service["service"] == "command_node")
    assert missing["status"] == "blocked"
    assert missing["state"] == "missing"


def test_build_report_blocks_on_endpoint_failure(tmp_path: Path) -> None:
    seed_compose(tmp_path)
    records = [compose_record("aurora_gui"), compose_record("command_node")]

    payload = stack_validation.build_report(
        tmp_path,
        runner=fake_runner(records),
        getter=blocked_getter,
        generated_at="2026-06-26T00:00:00Z",
    )

    assert payload["status"] == "blocked"
    assert payload["summary"]["endpoint_ready"] == 0


def test_missing_compose_file_blocks_without_running_docker(tmp_path: Path) -> None:
    payload = stack_validation.build_report(tmp_path, runner=fake_runner([]), getter=ready_getter)

    assert payload["status"] == "blocked"
    assert payload["compose"]["exists"] is False
    assert payload["commands"] == []


def test_write_report_creates_parent_dirs(tmp_path: Path) -> None:
    payload = stack_validation.build_report(tmp_path, runner=fake_runner([]), getter=ready_getter)
    out = tmp_path / "reports/analysis/aurora_stack_validation_latest.json"

    stack_validation.write_report(out, payload)

    saved = json.loads(out.read_text(encoding="utf-8"))
    assert saved["tool"] == "aurora_stack_validation"

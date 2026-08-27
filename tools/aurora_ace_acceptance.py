#!/usr/bin/env python3
"""Evaluate the repository-grounded Aurora Canon Engine v1 acceptance matrix.

The evaluator is verification-only. Local-safe rows run against temporary test
artifacts. Rows that exercise CanonRec commits run only inside temporary clones
of the registered repositories, never in the canonical nested checkouts.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MATRIX = Path("catalog/contracts/aurora_ace_v1_acceptance_matrix.json")
DEFAULT_REPORT = Path("reports/analysis/aurora_ace_v1_acceptance_latest.json")
SCHEMA_VERSION = "1.0.0"
RECORD_TYPE = "aurora_ace_v1_acceptance_matrix"
ROW_ID = re.compile(r"^ACE-V1-[0-9]{3}$")
TEST_REF = re.compile(r"^(tests/[^:]+\.py)::(test_[A-Za-z0-9_]+)$")
EXECUTION_CLASSES = {"local_safe", "isolated_ci"}
ALLOWED_TEST_ENV = {"AURORA_ACE_LIVE_TESTS", "ACE_MCP_E2E", "ACE_GENERIC_E2E"}
OVERLAY_PREFIXES = ("tools/", "tests/", "catalog/", "docs/", "skills/")
OVERLAY_FILES = {
    "AGENTS.md",
    "README.md",
    "Makefile",
    "requirements-ace-mcp.txt",
    "setup.cfg",
}
ISOLATED_REPOSITORIES = ("CanonRec", "aurora-cloudbank-symbolic-main")


class AcceptanceError(RuntimeError):
    """Raised when the acceptance contract or execution environment is invalid."""


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(
    command: Sequence[str], *, cwd: Path, env: Mapping[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    # Callers construct argv from fixed executables and validated matrix node IDs.
    return subprocess.run(  # noqa: S603
        list(command),
        cwd=cwd,
        env=dict(env) if env is not None else None,
        capture_output=True,
        text=True,
        check=False,
    )


def _git(root: Path, *args: str) -> str:
    completed = _run(("git", *args), cwd=root)
    if completed.returncode != 0:
        raise AcceptanceError(
            f"git {' '.join(args)} failed: {completed.stderr.strip()}"
        )
    return completed.stdout.strip()


def _safe_relative(root: Path, value: Any, *, label: str) -> tuple[str, Path]:
    if not isinstance(value, str) or not value.strip():
        raise AcceptanceError(f"{label} must be a non-empty relative path")
    rel = Path(value)
    if rel.is_absolute() or ".." in rel.parts:
        raise AcceptanceError(f"{label} escaped the repository root: {value}")
    resolved_root = root.resolve()
    resolved = (resolved_root / rel).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise AcceptanceError(f"{label} escaped the repository root: {value}") from exc
    return rel.as_posix(), resolved


def load_matrix(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AcceptanceError(f"ACE acceptance matrix is missing: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise AcceptanceError(
            f"ACE acceptance matrix is unreadable: {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise AcceptanceError("ACE acceptance matrix must be a JSON object")
    return payload


def _top_level_symbols(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        raise AcceptanceError(f"cannot inspect Python evidence {path}: {exc}") from exc
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add(alias.asname or alias.name.rsplit(".", 1)[-1])
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def _test_symbol(root: Path, reference: str) -> tuple[str, Path, str]:
    match = TEST_REF.fullmatch(reference)
    if match is None:
        raise AcceptanceError(f"invalid pytest node reference: {reference}")
    rel, path = _safe_relative(root, match.group(1), label="test reference")
    return rel, path, match.group(2)


def _string_list(value: Any, *, label: str, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        qualifier = "an array" if allow_empty else "a non-empty array"
        raise AcceptanceError(f"{label} must be {qualifier}")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise AcceptanceError(f"{label} must contain non-empty strings")
    if len(value) != len(set(value)):
        raise AcceptanceError(f"{label} must not contain duplicates")
    return list(value)


def _validate_header(matrix: Mapping[str, Any]) -> None:
    if matrix.get("schema_version") != SCHEMA_VERSION:
        raise AcceptanceError(
            f"unsupported ACE acceptance schema: {matrix.get('schema_version')}"
        )
    if matrix.get("record_type") != RECORD_TYPE:
        raise AcceptanceError(
            f"unsupported ACE acceptance record type: {matrix.get('record_type')}"
        )
    engine = matrix.get("engine")
    if (
        not isinstance(engine, Mapping)
        or engine.get("canonical_name") != "Aurora Canon Engine"
    ):
        raise AcceptanceError("ACE matrix must identify the Aurora Canon Engine")
    authority = matrix.get("authority")
    if (
        not isinstance(authority, Mapping)
        or authority.get("mutation_posture") != "verification_only"
    ):
        raise AcceptanceError(
            "ACE matrix mutation posture must remain verification_only"
        )
    policy = matrix.get("seal_policy")
    if not isinstance(policy, Mapping) or policy.get("required_row_status") != "ready":
        raise AcceptanceError("ACE matrix seal policy must require ready rows")
    if policy.get("isolated_execution_uses_temporary_clones") is not True:
        raise AcceptanceError("ACE isolated acceptance must use temporary clones")


def validate_matrix(  # noqa: C901
    matrix: Mapping[str, Any], *, root: Path = ROOT
) -> list[dict[str, Any]]:
    """Validate matrix structure and return repository evidence for each row."""

    _validate_header(matrix)
    rows = matrix.get("rows")
    if not isinstance(rows, list) or not rows:
        raise AcceptanceError("ACE acceptance matrix rows must be a non-empty array")
    seen: set[str] = set()
    validated: list[dict[str, Any]] = []
    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping):
            raise AcceptanceError(f"ACE acceptance row {index} must be an object")
        row = dict(raw)
        row_id = row.get("id")
        if not isinstance(row_id, str) or ROW_ID.fullmatch(row_id) is None:
            raise AcceptanceError(f"ACE acceptance row has invalid id: {row_id}")
        if row_id in seen:
            raise AcceptanceError(f"ACE acceptance row id is duplicated: {row_id}")
        seen.add(row_id)
        for field in ("title", "requirement", "acceptance"):
            if not isinstance(row.get(field), str) or not str(row[field]).strip():
                raise AcceptanceError(f"{row_id} {field} must be a non-empty string")
        if not isinstance(row.get("required"), bool):
            raise AcceptanceError(f"{row_id} required must be boolean")
        boundaries = _string_list(row.get("boundaries"), label=f"{row_id} boundaries")
        if len(boundaries) < 2:
            raise AcceptanceError(f"{row_id} must cross at least two boundaries")
        execution_class = row.get("execution_class")
        if execution_class not in EXECUTION_CLASSES:
            raise AcceptanceError(
                f"{row_id} has unsupported execution_class {execution_class}"
            )

        implementation = row.get("implementation_evidence")
        if not isinstance(implementation, list) or not implementation:
            raise AcceptanceError(f"{row_id} implementation_evidence must be non-empty")
        evidence_receipts: list[dict[str, Any]] = []
        for item in implementation:
            if not isinstance(item, Mapping):
                raise AcceptanceError(
                    f"{row_id} implementation evidence must be objects"
                )
            rel, path = _safe_relative(
                root, item.get("path"), label=f"{row_id} implementation path"
            )
            if not path.is_file():
                raise AcceptanceError(f"{row_id} implementation path is missing: {rel}")
            symbols = _string_list(
                item.get("symbols", []), label=f"{row_id} symbols", allow_empty=True
            )
            if symbols:
                defined = _top_level_symbols(path)
                missing = sorted(set(symbols) - defined)
                if missing:
                    raise AcceptanceError(
                        f"{row_id} symbols missing from {rel}: {missing}"
                    )
            evidence_receipts.append(
                {"path": rel, "sha256": file_sha256(path), "symbols": symbols}
            )

        contract_receipts: list[dict[str, str]] = []
        for value in _string_list(
            row.get("contract_refs"), label=f"{row_id} contract_refs"
        ):
            rel, path = _safe_relative(root, value, label=f"{row_id} contract ref")
            if not path.is_file():
                raise AcceptanceError(f"{row_id} contract ref is missing: {rel}")
            contract_receipts.append({"path": rel, "sha256": file_sha256(path)})

        practical = row.get("practical")
        if not isinstance(practical, Mapping):
            raise AcceptanceError(f"{row_id} practical must be an object")
        test_receipts: list[dict[str, str]] = []
        for reference in _string_list(
            practical.get("test_refs"), label=f"{row_id} practical.test_refs"
        ):
            rel, path, symbol = _test_symbol(root, reference)
            if not path.is_file():
                raise AcceptanceError(f"{row_id} test file is missing: {rel}")
            if symbol not in _top_level_symbols(path):
                raise AcceptanceError(f"{row_id} test symbol is missing: {reference}")
            test_receipts.append(
                {"node_id": reference, "file_sha256": file_sha256(path)}
            )
        dependencies = _string_list(
            practical.get("dependencies"),
            label=f"{row_id} practical.dependencies",
            allow_empty=True,
        )
        environment = practical.get("environment")
        if not isinstance(environment, Mapping):
            raise AcceptanceError(f"{row_id} practical.environment must be an object")
        invalid_env = sorted(set(environment) - ALLOWED_TEST_ENV)
        if invalid_env or any(value != "1" for value in environment.values()):
            raise AcceptanceError(
                f"{row_id} practical.environment is not allowlisted: {invalid_env}"
            )

        validated.append(
            {
                "id": row_id,
                "title": row["title"],
                "required": row["required"],
                "execution_class": execution_class,
                "boundaries": boundaries,
                "implementation_evidence": evidence_receipts,
                "contract_evidence": contract_receipts,
                "test_evidence": test_receipts,
                "dependencies": dependencies,
                "environment": dict(environment),
                "static_status": "ready",
            }
        )
    return validated


def _missing_dependencies(dependencies: Sequence[str]) -> list[str]:
    missing: list[str] = []
    for name in dependencies:
        try:
            available = importlib.util.find_spec(name) is not None
        except (ImportError, AttributeError, ValueError):
            available = False
        if not available:
            missing.append(name)
    return missing


def _junit_counts(path: Path) -> dict[str, int]:
    try:
        # The XML is emitted by the local pytest subprocess into a private temp directory.
        root = ET.parse(path).getroot()  # noqa: S314
    except (OSError, ET.ParseError) as exc:
        raise AcceptanceError(
            f"pytest did not produce readable JUnit evidence: {exc}"
        ) from exc
    cases = list(root.iter("testcase"))
    failures = sum(1 for case in cases if case.find("failure") is not None)
    errors = sum(1 for case in cases if case.find("error") is not None)
    skipped = sum(1 for case in cases if case.find("skipped") is not None)
    total = len(cases)
    return {
        "tests": total,
        "passed": total - failures - errors - skipped,
        "failed": failures,
        "errors": errors,
        "skipped": skipped,
    }


def _practical_status(returncode: int, counts: Mapping[str, int]) -> str:
    if returncode != 0 or counts.get("failed", 0) or counts.get("errors", 0):
        return "blocked"
    if counts.get("skipped", 0) or counts.get("tests", 0) == 0:
        return "attention"
    return "ready"


def _run_pytest_row(row: Mapping[str, Any], *, cwd: Path) -> dict[str, Any]:
    test_refs = [item["node_id"] for item in row["test_evidence"]]
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="ace-v1-junit-") as temp_dir:
        junit = Path(temp_dir) / "pytest.xml"
        command = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            *test_refs,
            f"--junitxml={junit}",
        ]
        environment = os.environ.copy()
        environment.update(row["environment"])
        completed = _run(command, cwd=cwd, env=environment)
        elapsed_ms = round((time.monotonic() - started) * 1000, 3)
        counts = (
            _junit_counts(junit)
            if junit.is_file()
            else {
                "tests": 0,
                "passed": 0,
                "failed": 0,
                "errors": 1,
                "skipped": 0,
            }
        )
    combined = "\n".join(
        part for part in (completed.stdout.strip(), completed.stderr.strip()) if part
    )
    return {
        "status": _practical_status(completed.returncode, counts),
        "returncode": completed.returncode,
        "counts": counts,
        "elapsed_ms": elapsed_ms,
        "command": command,
        "output_tail": combined[-4000:],
        "working_tree": "temporary_clone"
        if cwd.resolve() != ROOT.resolve()
        else "canonical_root_read_only",
    }


def _overlay_current_files(source: Path, target: Path) -> None:
    completed = _run(("git", "ls-files", "-co", "--exclude-standard", "-z"), cwd=source)
    if completed.returncode != 0:
        raise AcceptanceError(
            f"cannot enumerate working files for isolated acceptance: {completed.stderr.strip()}"
        )
    for value in completed.stdout.split("\0"):
        if not value:
            continue
        if value not in OVERLAY_FILES and not value.startswith(OVERLAY_PREFIXES):
            continue
        source_path = source / value
        if not source_path.is_file():
            continue
        target_path = target / value
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)


def _registered_repositories(root: Path) -> dict[str, dict[str, str]]:
    try:
        import yaml
    except ImportError as exc:
        raise AcceptanceError(
            "PyYAML is required to prepare isolated ACE acceptance clones"
        ) from exc
    registry_path = root / "catalog/repo_registry.yaml"
    try:
        payload = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise AcceptanceError(f"cannot load repository registry: {exc}") from exc
    rows = payload.get("repos") if isinstance(payload, Mapping) else None
    if not isinstance(rows, list):
        raise AcceptanceError("repository registry has no repos array")
    selected: dict[str, dict[str, str]] = {}
    for item in rows:
        if (
            not isinstance(item, Mapping)
            or item.get("name") not in ISOLATED_REPOSITORIES
        ):
            continue
        name = str(item["name"])
        values = {key: item.get(key) for key in ("path", "branch", "head_sha")}
        if any(not isinstance(value, str) or not value for value in values.values()):
            raise AcceptanceError(
                f"registered repository {name} lacks path, branch, or head_sha"
            )
        selected[name] = {key: str(value) for key, value in values.items()}
    missing = sorted(set(ISOLATED_REPOSITORIES) - set(selected))
    if missing:
        raise AcceptanceError(
            f"repository registry lacks isolated ACE owners: {missing}"
        )
    return selected


def _canonical_nested_snapshot(root: Path) -> dict[str, dict[str, str]]:
    snapshot: dict[str, dict[str, str]] = {}
    for name, record in _registered_repositories(root).items():
        rel, repo = _safe_relative(
            root, record["path"], label=f"registered {name} path"
        )
        if not (repo / ".git").exists():
            raise AcceptanceError(f"registered {name} checkout is unavailable: {rel}")
        snapshot[name] = {
            "path": rel,
            "head": _git(repo, "rev-parse", "HEAD"),
            "branch": _git(repo, "branch", "--show-current"),
            "status_porcelain": _git(repo, "status", "--porcelain"),
        }
    return snapshot


def _prepare_isolated_workspace(source: Path, target: Path) -> None:
    clone_environment = os.environ.copy()
    clone_environment["GIT_LFS_SKIP_SMUDGE"] = "1"
    clone = _run(
        ("git", "clone", "--no-hardlinks", "--quiet", str(source), str(target)),
        cwd=source.parent,
        env=clone_environment,
    )
    if clone.returncode != 0:
        raise AcceptanceError(
            f"cannot clone root for isolated ACE acceptance: {clone.stderr.strip()}"
        )
    _overlay_current_files(source, target)
    for name, record in _registered_repositories(source).items():
        rel, source_repo = _safe_relative(
            source, record["path"], label=f"registered {name} path"
        )
        if not (source_repo / ".git").exists():
            raise AcceptanceError(f"registered {name} checkout is unavailable: {rel}")
        _, target_repo = _safe_relative(
            target, record["path"], label=f"isolated {name} path"
        )
        if target_repo.exists():
            shutil.rmtree(target_repo)
        target_repo.parent.mkdir(parents=True, exist_ok=True)
        nested = _run(
            (
                "git",
                "clone",
                "--no-hardlinks",
                "--quiet",
                str(source_repo),
                str(target_repo),
            ),
            cwd=target_repo.parent,
            env=clone_environment,
        )
        if nested.returncode != 0:
            raise AcceptanceError(
                f"cannot clone registered {name} for isolated acceptance: {nested.stderr.strip()}"
            )
        checkout = _run(
            ("git", "checkout", "-B", record["branch"], record["head_sha"]),
            cwd=target_repo,
            env=clone_environment,
        )
        if checkout.returncode != 0:
            raise AcceptanceError(
                f"cannot pin isolated {name} to {record['head_sha']}: {checkout.stderr.strip()}"
            )


@contextmanager
def isolated_workspace(root: Path = ROOT) -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix="aurora-ace-v1-") as temp_dir:
        target = Path(temp_dir) / "Aurora_ORIONCORE_Directory_Main"
        _prepare_isolated_workspace(root, target)
        yield target


def build_report(
    matrix: Mapping[str, Any],
    *,
    matrix_path: Path,
    root: Path = ROOT,
    run_practical: bool = False,
    include_isolated: bool = False,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build an acceptance report without mutating canonical repositories."""

    validated_rows = validate_matrix(matrix, root=root)
    root_commit = _git(root, "rev-parse", "HEAD")
    matrix_digest = file_sha256(matrix_path)
    results: list[dict[str, Any]] = []
    nested_before = (
        _canonical_nested_snapshot(root) if run_practical and include_isolated else None
    )

    isolated_context = (
        isolated_workspace(root) if run_practical and include_isolated else None
    )
    if isolated_context is None:
        _evaluate_rows(
            validated_rows,
            results,
            root=root,
            isolated_root=None,
            run_practical=run_practical,
        )
    else:
        with isolated_context as isolated_root:
            _evaluate_rows(
                validated_rows,
                results,
                root=root,
                isolated_root=isolated_root,
                run_practical=run_practical,
            )
    nested_after = (
        _canonical_nested_snapshot(root) if nested_before is not None else None
    )
    if nested_before != nested_after:
        raise AcceptanceError(
            "canonical nested repository state changed during isolated ACE acceptance"
        )

    required = [row for row in results if row["required"]]
    if any(row["status"] == "blocked" for row in required):
        status = "blocked"
    elif any(row["status"] != "ready" for row in required):
        status = "attention"
    else:
        status = "ready"
    counts = {
        state: sum(1 for row in results if row["status"] == state)
        for state in ("ready", "attention", "blocked")
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "aurora_ace_v1_acceptance_report",
        "generated_at": generated_at or utc_now(),
        "tool": "aurora_ace_acceptance",
        "engine": dict(matrix["engine"]),
        "matrix": {
            "path": matrix_path.resolve().relative_to(root.resolve()).as_posix(),
            "sha256": matrix_digest,
        },
        "root_commit": root_commit,
        "execution_environment": {
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
        },
        "mutation_posture": "verification_only",
        "canonical_nested_repositories_mutated": False,
        "canonical_nested_repository_snapshot": {
            "captured": nested_before is not None,
            "unchanged": nested_before == nested_after
            if nested_before is not None
            else None,
            "before": nested_before,
            "after": nested_after,
        },
        "isolated_execution_used": bool(run_practical and include_isolated),
        "status": status,
        "seal_eligible": status == "ready",
        "summary": {"total": len(results), "required": len(required), **counts},
        "rows": results,
        "interpretation": {
            "attention": "verification incomplete or unavailable in this execution environment; existing component contracts are not downgraded",
            "blocked": "repository evidence or an executed required check failed",
            "ready": "repository evidence exists and the row's practical checks passed",
        },
    }


def _evaluate_rows(
    rows: Sequence[Mapping[str, Any]],
    results: list[dict[str, Any]],
    *,
    root: Path,
    isolated_root: Path | None,
    run_practical: bool,
) -> None:
    for row in rows:
        result = dict(row)
        missing = _missing_dependencies(row["dependencies"])
        result["missing_dependencies"] = missing
        if missing:
            result["status"] = "attention"
            result["practical"] = {
                "status": "not_run",
                "reason": "missing_dependencies",
                "missing_dependencies": missing,
            }
        elif not run_practical:
            result["status"] = "attention"
            result["practical"] = {
                "status": "not_run",
                "reason": "practical_execution_not_requested",
            }
        elif row["execution_class"] == "isolated_ci" and isolated_root is None:
            result["status"] = "attention"
            result["practical"] = {
                "status": "not_run",
                "reason": "isolated_execution_not_requested",
            }
        else:
            cwd = isolated_root if row["execution_class"] == "isolated_ci" else root
            if cwd is None:
                raise AcceptanceError(f"{row['id']} has no valid execution root")
            practical = _run_pytest_row(row, cwd=cwd)
            result["status"] = practical["status"]
            result["practical"] = practical
        results.append(result)


def write_report(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--matrix",
        type=Path,
        default=DEFAULT_MATRIX,
        help="Acceptance matrix relative to the root.",
    )
    parser.add_argument(
        "--run-practical", action="store_true", help="Run local-safe practical rows."
    )
    parser.add_argument(
        "--include-isolated",
        action="store_true",
        help="Also run isolated rows against temporary root and nested-repository clones.",
    )
    parser.add_argument(
        "--report-out", type=Path, help="Write the JSON acceptance report."
    )
    parser.add_argument(
        "--persist-report", action="store_true", help=f"Write {DEFAULT_REPORT}."
    )
    parser.add_argument(
        "--summary", action="store_true", help="Print a compact human-readable summary."
    )
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit nonzero unless every required row is ready.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.include_isolated and not args.run_practical:
        raise SystemExit("--include-isolated requires --run-practical")
    matrix_path = args.matrix if args.matrix.is_absolute() else ROOT / args.matrix
    try:
        matrix = load_matrix(matrix_path)
        report = build_report(
            matrix,
            matrix_path=matrix_path,
            root=ROOT,
            run_practical=args.run_practical,
            include_isolated=args.include_isolated,
        )
    except AcceptanceError as exc:
        print(f"ACE v1 acceptance error: {exc}", file=sys.stderr)
        return 2

    output = args.report_out
    if args.persist_report:
        if output is not None and output != DEFAULT_REPORT:
            print(
                "--persist-report cannot be combined with a different --report-out",
                file=sys.stderr,
            )
            return 2
        output = DEFAULT_REPORT
    if output is not None:
        report_path = output if output.is_absolute() else ROOT / output
        write_report(report_path, report)

    if args.summary or output is None:
        summary = report["summary"]
        print(
            "ACE v1 acceptance: "
            f"status={report['status']} seal_eligible={str(report['seal_eligible']).lower()} "
            f"ready={summary['ready']} attention={summary['attention']} blocked={summary['blocked']}"
        )
        for row in report["rows"]:
            if row["status"] != "ready":
                reason = (
                    row["practical"].get("reason")
                    or row["practical"].get("output_tail", "")[-240:]
                )
                print(f"  {row['id']} {row['status']}: {reason}")
    if args.require_ready and not report["seal_eligible"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

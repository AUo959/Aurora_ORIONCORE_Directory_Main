#!/usr/bin/env python3
"""Auto-ingest Python package modules and validate adapter/fallback contracts."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence


@dataclass
class ModuleScan:
    module: str
    path: str
    public_classes: List[str]
    public_functions: List[str]
    adapter_classes: List[str]
    methods: Dict[str, List[str]]
    async_methods: Dict[str, List[str]]
    has_fallback_class: bool
    has_guarded_optional_import: bool
    has_mode_assignment: bool
    parse_error: Optional[str] = None


class _GuardedImportVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.found = False

    def visit_Try(self, node: ast.Try) -> None:  # noqa: N802
        has_import = any(isinstance(stmt, (ast.Import, ast.ImportFrom)) for stmt in node.body)
        if has_import and node.handlers:
            self.found = True
        self.generic_visit(node)


class _ModeAssignmentVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.found = False

    def visit_Assign(self, node: ast.Assign) -> None:  # noqa: N802
        for target in node.targets:
            if isinstance(target, ast.Attribute) and target.attr == "mode":
                self.found = True
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:  # noqa: N802
        if isinstance(node.target, ast.Attribute) and node.target.attr == "mode":
            self.found = True
        self.generic_visit(node)


def _extract_public_symbols(tree: ast.AST) -> ModuleScan:
    public_classes: List[str] = []
    public_functions: List[str] = []
    adapter_classes: List[str] = []
    methods: Dict[str, List[str]] = {}
    async_methods: Dict[str, List[str]] = {}
    has_fallback_class = False

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            if node.name.startswith("_Fallback"):
                has_fallback_class = True
            if not node.name.startswith("_"):
                public_classes.append(node.name)
                if node.name.endswith("Adapter"):
                    adapter_classes.append(node.name)

            class_methods: List[str] = []
            class_async_methods: List[str] = []
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    class_methods.append(child.name)
                elif isinstance(child, ast.AsyncFunctionDef):
                    class_methods.append(child.name)
                    class_async_methods.append(child.name)
            methods[node.name] = sorted(class_methods)
            async_methods[node.name] = sorted(class_async_methods)

        elif isinstance(node, ast.FunctionDef):
            if not node.name.startswith("_"):
                public_functions.append(node.name)

    return ModuleScan(
        module="",
        path="",
        public_classes=sorted(public_classes),
        public_functions=sorted(public_functions),
        adapter_classes=sorted(adapter_classes),
        methods=methods,
        async_methods=async_methods,
        has_fallback_class=has_fallback_class,
        has_guarded_optional_import=False,
        has_mode_assignment=False,
    )


def scan_module(path: Path) -> ModuleScan:
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except Exception as exc:
        return ModuleScan(
            module=path.stem,
            path=str(path),
            public_classes=[],
            public_functions=[],
            adapter_classes=[],
            methods={},
            async_methods={},
            has_fallback_class=False,
            has_guarded_optional_import=False,
            has_mode_assignment=False,
            parse_error=str(exc),
        )

    scan = _extract_public_symbols(tree)
    scan.module = path.stem
    scan.path = str(path)

    import_visitor = _GuardedImportVisitor()
    import_visitor.visit(tree)
    scan.has_guarded_optional_import = import_visitor.found

    mode_visitor = _ModeAssignmentVisitor()
    mode_visitor.visit(tree)
    scan.has_mode_assignment = mode_visitor.found

    return scan


def list_modules(package_dir: Path) -> List[Path]:
    return sorted(
        p
        for p in package_dir.glob("*.py")
        if p.name != "__init__.py" and not p.name.startswith(".")
    )


def choose_exports(scan: ModuleScan) -> List[str]:
    if scan.public_classes:
        return scan.public_classes
    return scan.public_functions


def parse_existing_all(init_path: Path) -> List[str]:
    if not init_path.exists():
        return []

    try:
        tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))
    except Exception:
        return []

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        values: List[str] = []
                        for element in node.value.elts:
                            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                                values.append(element.value)
                        return values
    return []


def parse_existing_docstring(init_path: Path, package_name: str) -> str:
    if not init_path.exists():
        return f'"""Public exports for {package_name}."""'

    try:
        tree = ast.parse(init_path.read_text(encoding="utf-8"), filename=str(init_path))
        value = ast.get_docstring(tree)
        if value:
            return f'"""{value}"""'
    except Exception:
        pass

    return f'"""Public exports for {package_name}."""'


def build_init_content(package_dir: Path, scans: Sequence[ModuleScan]) -> str:
    exports_by_module: Dict[str, List[str]] = {}
    for scan in scans:
        if scan.parse_error:
            continue
        symbols = choose_exports(scan)
        if symbols:
            exports_by_module[scan.module] = symbols

    package_name = package_dir.name
    init_path = package_dir / "__init__.py"
    docstring = parse_existing_docstring(init_path, package_name)

    lines: List[str] = [docstring, ""]
    all_symbols: List[str] = []

    for module_name in sorted(exports_by_module):
        symbols = sorted(exports_by_module[module_name])
        all_symbols.extend(symbols)
        lines.append(f"from .{module_name} import {', '.join(symbols)}")

    if exports_by_module:
        lines.append("")

    lines.append("__all__ = [")
    for symbol in sorted(set(all_symbols)):
        lines.append(f'    "{symbol}",')
    lines.append("]")
    lines.append("")

    return "\n".join(lines)


def build_findings(scans: Sequence[ModuleScan]) -> List[Dict[str, str]]:
    findings: List[Dict[str, str]] = []

    for scan in scans:
        if scan.parse_error:
            findings.append(
                {
                    "severity": "error",
                    "code": "parse_error",
                    "module": scan.module,
                    "message": scan.parse_error,
                }
            )
            continue

        for adapter in scan.adapter_classes:
            async_methods = set(scan.async_methods.get(adapter, []))
            methods = set(scan.methods.get(adapter, []))

            if "process_turn" not in async_methods:
                findings.append(
                    {
                        "severity": "error",
                        "code": "adapter_missing_async_process_turn",
                        "module": scan.module,
                        "message": (
                            f"{adapter} should define async process_turn for runtime compatibility."
                        ),
                    }
                )

            if "get_performance_summary" not in methods:
                findings.append(
                    {
                        "severity": "warning",
                        "code": "adapter_missing_summary",
                        "module": scan.module,
                        "message": (
                            f"{adapter} should expose get_performance_summary for telemetry parity."
                        ),
                    }
                )

        if scan.adapter_classes and not scan.has_fallback_class:
            findings.append(
                {
                    "severity": "warning",
                    "code": "missing_fallback_class",
                    "module": scan.module,
                    "message": "No _Fallback* class detected alongside adapter class.",
                }
            )

        if scan.adapter_classes and not scan.has_guarded_optional_import:
            findings.append(
                {
                    "severity": "warning",
                    "code": "missing_guarded_optional_import",
                    "module": scan.module,
                    "message": "No try/except guarded optional import detected in adapter module.",
                }
            )

        if scan.adapter_classes and not scan.has_mode_assignment:
            findings.append(
                {
                    "severity": "warning",
                    "code": "missing_mode_assignment",
                    "module": scan.module,
                    "message": "No self.mode assignment detected for adapter mode introspection.",
                }
            )

    return findings


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Auto-ingest Python package modules and validate adapter/fallback contracts."
    )
    parser.add_argument("--package-dir", required=True, help="Package directory to ingest")
    parser.add_argument(
        "--report-json",
        help="Output path for JSON report (default: <package-dir>/ingest_report.json)",
    )
    parser.add_argument(
        "--apply-init",
        action="store_true",
        help="Rewrite package __init__.py with deterministic exports",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on error-severity findings",
    )
    parser.add_argument(
        "--print-init-preview",
        action="store_true",
        help="Print generated __init__.py preview",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    package_dir = Path(args.package_dir).expanduser().resolve()

    if not package_dir.exists() or not package_dir.is_dir():
        print(f"[ingest] package directory not found: {package_dir}", file=sys.stderr)
        return 2

    init_path = package_dir / "__init__.py"
    module_paths = list_modules(package_dir)
    scans = [scan_module(path) for path in module_paths]

    generated_init = build_init_content(package_dir, scans)

    exports: List[str] = []
    for scan in scans:
        if scan.parse_error:
            continue
        exports.extend(choose_exports(scan))
    proposed_exports = sorted(set(exports))

    existing_exports = sorted(set(parse_existing_all(init_path)))
    missing_exports = sorted(set(proposed_exports) - set(existing_exports))
    extra_exports = sorted(set(existing_exports) - set(proposed_exports))

    findings = build_findings(scans)
    severity_counts = {
        "error": sum(1 for finding in findings if finding["severity"] == "error"),
        "warning": sum(1 for finding in findings if finding["severity"] == "warning"),
    }

    applied_init_update = False
    if args.apply_init:
        init_path.write_text(generated_init, encoding="utf-8")
        applied_init_update = True

    report_path = (
        Path(args.report_json).expanduser().resolve()
        if args.report_json
        else package_dir / "ingest_report.json"
    )

    report = {
        "package_dir": str(package_dir),
        "module_count": len(scans),
        "init_path": str(init_path),
        "modules": [asdict(scan) for scan in scans],
        "existing_exports": existing_exports,
        "proposed_exports": proposed_exports,
        "missing_exports": missing_exports,
        "extra_exports": extra_exports,
        "findings": findings,
        "severity_counts": severity_counts,
        "applied_init_update": applied_init_update,
    }

    report_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    print(f"[ingest] package: {package_dir}")
    print(f"[ingest] modules scanned: {len(scans)}")
    print(f"[ingest] proposed exports: {len(proposed_exports)}")
    print(f"[ingest] missing exports: {len(missing_exports)}")
    print(f"[ingest] extra exports: {len(extra_exports)}")
    print(f"[ingest] findings: {severity_counts['error']} error(s), {severity_counts['warning']} warning(s)")
    print(f"[ingest] report: {report_path}")
    if applied_init_update:
        print(f"[ingest] updated: {init_path}")

    if args.print_init_preview:
        print("\n--- __init__.py preview ---")
        print(generated_init)

    if args.strict and severity_counts["error"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

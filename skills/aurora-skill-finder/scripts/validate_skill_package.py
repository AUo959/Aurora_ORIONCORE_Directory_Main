#!/usr/bin/env python3
"""Validate the installed Aurora skill package for drift and broken references."""

from __future__ import annotations

import argparse
import json
import py_compile
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

SKILLS_ROOT_DEFAULT = Path("/Users/travisstreets/.codex/skills")
CATALOG_FILES = {
    "session": "aurora-skill-finder/references/session_skill_catalog.json",
    "aurora-core": "aurora-skill-finder/references/aurora_core_skill_catalog.json",
    "general-utility": "aurora-skill-finder/references/general_utility_skill_catalog.json",
}
GOVERNOR_SKILLS = {
    "aurora-governance-orchestrator",
    "threadcore-governor",
    "zipwiz-governor",
    "aurora-script-governor",
    "aurora-narrative-tone-governor",
    "aurora-repo-stabilizer",
}
REF_PATTERNS = (
    re.compile(r"`((?:scripts|references|assets|agents)/[^`\n]+)`"),
    re.compile(r"\((?P<ref>(?:scripts|references|assets|agents)/[^)\n]+)\)"),
)
YAML_MARKERS = ("interface:", "display_name:", "short_description:", "default_prompt:")
if hasattr(sys, "pycache_prefix"):
    sys.pycache_prefix = str(Path(tempfile.gettempdir()) / "aurora_skill_package_pycache")


def iter_skill_dirs(skills_root: Path) -> list[Path]:
    out: list[Path] = []
    for child in sorted(skills_root.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("."):
            continue
        if not (child / "SKILL.md").exists():
            continue
        out.append(child)
    return out


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_relative_refs(text: str) -> list[str]:
    refs: list[str] = []
    for pattern in REF_PATTERNS:
        for match in pattern.finditer(text):
            ref = match.group("ref") if "ref" in pattern.groupindex else match.group(1)
            if ref not in refs:
                refs.append(ref)
    return refs


def validate_skill_dir(skill_dir: Path) -> tuple[list[dict[str, str]], list[dict[str, str]], int]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    python_count = 0

    skill_md = skill_dir / "SKILL.md"
    agent_yaml = skill_dir / "agents" / "openai.yaml"

    if not skill_md.exists():
        errors.append({"skill": skill_dir.name, "check": "required_file", "detail": "Missing SKILL.md"})
    if not agent_yaml.exists():
        errors.append({"skill": skill_dir.name, "check": "required_file", "detail": "Missing agents/openai.yaml"})

    if agent_yaml.exists():
        yaml_text = agent_yaml.read_text(encoding="utf-8")
        for marker in YAML_MARKERS:
            if marker not in yaml_text:
                errors.append(
                    {
                        "skill": skill_dir.name,
                        "check": "yaml_marker",
                        "detail": f"agents/openai.yaml missing marker: {marker}",
                    }
                )

    if skill_md.exists():
        skill_text = skill_md.read_text(encoding="utf-8")
        for ref in collect_relative_refs(skill_text):
            candidate = skill_dir / ref
            if not candidate.exists():
                errors.append(
                    {
                        "skill": skill_dir.name,
                        "check": "relative_reference",
                        "detail": f"Missing referenced path: {ref}",
                    }
                )

        if skill_dir.name in GOVERNOR_SKILLS and "finding_schema.md" not in skill_text:
            warnings.append(
                {
                    "skill": skill_dir.name,
                    "check": "shared_schema_reference",
                    "detail": "Governor SKILL.md does not mention finding_schema.md",
                }
            )

    for script in sorted(skill_dir.glob("scripts/*.py")):
        python_count += 1
        try:
            py_compile.compile(str(script), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(
                {
                    "skill": skill_dir.name,
                    "check": "py_compile",
                    "detail": f"{script.name}: {exc.msg}",
                }
            )

    return errors, warnings, python_count


def validate_catalogs(skills_root: Path) -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, Any]]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    catalog_stats: dict[str, Any] = {}

    installed = {path.name for path in iter_skill_dirs(skills_root)}
    loaded: dict[str, dict[str, Any]] = {}

    for profile, rel in CATALOG_FILES.items():
        path = skills_root / rel
        if not path.exists():
            errors.append({"skill": "package", "check": "catalog_file", "detail": f"Missing catalog: {path}"})
            continue
        payload = load_json(path)
        names = [row.get("name") for row in payload.get("skills", []) if isinstance(row, dict)]
        loaded[profile] = {"path": str(path), "names": names}
        catalog_stats[profile] = {"path": str(path), "skill_count": len(names)}
        for name in names:
            if name not in installed:
                errors.append(
                    {
                        "skill": "package",
                        "check": "catalog_membership",
                        "detail": f"{profile} catalog references missing installed skill: {name}",
                    }
                )

    session_names = set(loaded.get("session", {}).get("names", []))
    core_names = set(loaded.get("aurora-core", {}).get("names", []))
    utility_names = set(loaded.get("general-utility", {}).get("names", []))

    missing_in_session = sorted(installed - session_names)
    extra_in_session = sorted(session_names - installed)
    if missing_in_session:
        errors.append(
            {
                "skill": "package",
                "check": "session_catalog_sync",
                "detail": f"Installed skills missing from session catalog: {missing_in_session}",
            }
        )
    if extra_in_session:
        errors.append(
            {
                "skill": "package",
                "check": "session_catalog_sync",
                "detail": f"Session catalog contains non-installed skills: {extra_in_session}",
            }
        )

    overlap = sorted(core_names & utility_names)
    if overlap:
        errors.append(
            {
                "skill": "package",
                "check": "catalog_profile_overlap",
                "detail": f"aurora-core and general-utility overlap: {overlap}",
            }
        )

    if session_names and session_names != core_names | utility_names:
        errors.append(
            {
                "skill": "package",
                "check": "catalog_profile_coverage",
                "detail": "aurora-core + general-utility does not reconstruct the session catalog",
            }
        )

    return errors, warnings, catalog_stats


def build_report(skills_root: Path) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    python_files = 0

    skills = iter_skill_dirs(skills_root)
    for skill_dir in skills:
        skill_errors, skill_warnings, skill_python = validate_skill_dir(skill_dir)
        errors.extend(skill_errors)
        warnings.extend(skill_warnings)
        python_files += skill_python

    catalog_errors, catalog_warnings, catalog_stats = validate_catalogs(skills_root)
    errors.extend(catalog_errors)
    warnings.extend(catalog_warnings)

    status = "ok" if not errors else "issues"
    return {
        "status": status,
        "skills_root": str(skills_root),
        "summary": {
            "skill_count": len(skills),
            "python_script_count": python_files,
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "catalogs": catalog_stats,
        "errors": errors,
        "warnings": warnings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate the installed Aurora skill package.")
    parser.add_argument("--skills-root", default=str(SKILLS_ROOT_DEFAULT), help="Path to installed skills root")
    parser.add_argument("--out", help="Optional output JSON path")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument("--fail-on-issues", action="store_true", help="Return non-zero when errors are found")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    skills_root = Path(args.skills_root).expanduser().resolve()
    report = build_report(skills_root)

    indent = 2 if args.pretty else None
    payload = json.dumps(report, indent=indent, ensure_ascii=False, sort_keys=bool(indent))
    if args.out:
        out_path = Path(args.out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload + "\n", encoding="utf-8")

    print(payload)
    if args.fail_on_issues and report["errors"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

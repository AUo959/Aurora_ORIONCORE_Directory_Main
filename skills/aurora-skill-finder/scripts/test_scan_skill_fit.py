#!/usr/bin/env python3
"""Focused tests for aurora-skill-finder scanner behavior."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parent / "scan_skill_fit.py"
spec = importlib.util.spec_from_file_location("scan_skill_fit", MODULE_PATH)
assert spec is not None and spec.loader is not None
scan = importlib.util.module_from_spec(spec)
sys.modules["scan_skill_fit"] = scan
spec.loader.exec_module(scan)


def make_entry(**kwargs):
    return scan.SkillEntry(
        name=kwargs.get("name", "test-skill"),
        description=kwargs.get("description", "test"),
        include_keywords=tuple(kwargs.get("include_keywords", [])),
        exclude_keywords=tuple(kwargs.get("exclude_keywords", [])),
        path_hints=tuple(kwargs.get("path_hints", [])),
        filetype_bias=dict(kwargs.get("filetype_bias", {})),
        min_confidence_override=kwargs.get("min_confidence_override"),
    )


def test_resolve_scan_roots_focused_includes_git_and_optional(tmp_path):
    root = tmp_path

    (root / "repo_a" / ".git").mkdir(parents=True)
    (root / "nested" / "repo_b" / ".git").mkdir(parents=True)
    (root / "Aurora_New_11_9").mkdir()
    (root / "GUMAS_SIM_2.0").mkdir()

    roots = scan.resolve_scan_roots(root, "focused", include_archives=False)
    root_strings = {str(item) for item in roots}

    assert str((root / "repo_a").resolve()) in root_strings
    assert str((root / "nested" / "repo_b").resolve()) in root_strings
    assert str((root / "Aurora_New_11_9").resolve()) in root_strings
    assert str((root / "GUMAS_SIM_2.0").resolve()) in root_strings


def test_structural_boost_for_selective_integration_hotspot():
    entry = make_entry(
        name="aurora-selective-integration",
        include_keywords=["selective integration", "capsule"],
        path_hints=["selective_integration", "auto_selective_ingest_gate.py"],
        filetype_bias={".py": 0.07},
    )

    row = scan.score_skill_match(
        entry=entry,
        relative_path="scripts/auto_selective_ingest_gate.py",
        project_relative_path="repo/scripts/auto_selective_ingest_gate.py",
        content_text="run selective integration capsule generation",
        extension=".py",
        scope="focused",
    )

    assert row["score"] >= 0.65
    assert any("structural boost" in note for note in row["evidence"])


def test_boundary_penalty_reduces_cross_domain_bleed():
    entry = make_entry(
        name="threadcore-governor",
        include_keywords=["threadcore", "beacon", "anchor"],
        exclude_keywords=["zipwiz", "packaging protocol"],
        path_hints=["threadcore"],
        filetype_bias={".md": 0.08},
    )

    row = scan.score_skill_match(
        entry=entry,
        relative_path="ZipWiz_Chamber_6_28/ZIPWIZ_Documents/L3_GOV__ZIPWIZ_PACKAGING_PROTOCOL.md",
        project_relative_path="ZipWiz_Chamber_6_28/ZIPWIZ_Documents/L3_GOV__ZIPWIZ_PACKAGING_PROTOCOL.md",
        content_text="zipwiz packaging protocol and bundle manifest",
        extension=".md",
        scope="focused",
    )

    assert row["score"] < 0.45


def test_archive_penalty_is_applied():
    entry = make_entry(
        name="aurora-canon-reconciler",
        include_keywords=["canon", "promotion_queue"],
        path_hints=["promotion_queue"],
        filetype_bias={".md": 0.06},
    )

    non_archive = scan.score_skill_match(
        entry=entry,
        relative_path="GUMAS_SIM_2.5/CanonRec/promotion_queue.md",
        project_relative_path="GUMAS_SIM_2.5/CanonRec/promotion_queue.md",
        content_text="canon promotion_queue",
        extension=".md",
        scope="focused",
    )
    archive = scan.score_skill_match(
        entry=entry,
        relative_path="GUMAS_SIM_2.0/06_ARCHIVES/legacy/promotion_queue.md",
        project_relative_path="GUMAS_SIM_2.0/06_ARCHIVES/legacy/promotion_queue.md",
        content_text="canon promotion_queue",
        extension=".md",
        scope="focused",
    )

    assert archive["score"] < non_archive["score"]


def test_multi_domain_governance_overlap_prefers_orchestrator():
    orchestrator = make_entry(
        name="aurora-governance-orchestrator",
        include_keywords=["governance preflight", "merged findings", "orchestrator"],
        path_hints=["governance", "preflight"],
        filetype_bias={".md": 0.04},
    )
    threadcore = make_entry(
        name="threadcore-governor",
        include_keywords=["threadcore", "beacon", "continuity"],
        path_hints=["threadcore", "beacon"],
        filetype_bias={".md": 0.05},
    )

    shared_path = "governance/threadcore_zipwiz_preflight.md"
    shared_content = "cross-domain drift report covering threadcore beacon continuity and zipwiz staging manifest governance"

    orchestrator_row = scan.score_skill_match(
        entry=orchestrator,
        relative_path=shared_path,
        project_relative_path=shared_path,
        content_text=shared_content,
        extension=".md",
        scope="focused",
    )
    threadcore_row = scan.score_skill_match(
        entry=threadcore,
        relative_path=shared_path,
        project_relative_path=shared_path,
        content_text=shared_content,
        extension=".md",
        scope="focused",
    )

    assert orchestrator_row["score"] > threadcore_row["score"]
    assert any("multi-domain governance context" in note for note in orchestrator_row["evidence"])


def test_catalog_profile_path_resolution_uses_builtin_profile():
    script_dir = Path("/tmp/aurora-skill-finder/scripts")

    resolved = scan.resolve_catalog_path(script_dir, None, "aurora-core")

    assert resolved.as_posix().endswith("/aurora-skill-finder/references/aurora_core_skill_catalog.json")

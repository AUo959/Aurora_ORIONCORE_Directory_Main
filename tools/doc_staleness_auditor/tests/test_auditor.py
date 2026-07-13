"""Tests for the doc staleness auditor.

The key invariant under test is the evidence policy: CONFIRMED is only ever
reached via a primary source (git tree / AST / config file), STALE only via an
observed contradiction, and unbacked claims fall through to UNVERIFIABLE.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from doc_staleness_auditor.extractors import extract_claims
from doc_staleness_auditor.governance import build_artifacts
from doc_staleness_auditor.models import ClaimType, PRIMARY_METHODS, Status
from doc_staleness_auditor.planner import plan_fixes
from doc_staleness_auditor.repo_reader import make_reader
from doc_staleness_auditor.verifiers import Verifier
from doc_staleness_auditor.config import RepoConfig


def _git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)  # noqa: S603, S607


@pytest.fixture()
def repo(tmp_path):
    """A tiny real git repo with a source file, a version file, and a doc."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text(
        "def real_function():\n    return 1\n\n\nclass RealClass:\n    pass\n")
    (tmp_path / "VERSION").write_text("2.0.0\n")
    (tmp_path / "README.md").write_text(
        "# Demo\n"
        "See `src/app.py` for details.\n"                 # path -> CONFIRMED
        "The function `real_function` does work.\n"        # symbol -> CONFIRMED
        "Also `src/missing.py` is referenced.\n"           # path -> STALE
        "The class `GhostClass` in `src/app.py` exists.\n"  # symbol -> STALE
        "Current version 2.0.0 per VERSION file.\n"        # version -> CONFIRMED
        "Legacy version 1.0.0 per VERSION file.\n"         # version -> STALE
        "Our architecture is fundamentally emergent.\n"    # narrative -> nothing
    )
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t.t")
    _git(tmp_path, "config", "user.name", "t")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "init")
    return tmp_path


def _verify_all(repo):
    reader = make_reader(str(repo), backend="git")
    claims = extract_claims("README.md", (repo / "README.md").read_text())
    findings = Verifier(reader).verify_all(claims)
    return {(f.claim.type, f.claim.value): f for f in findings}


def test_confirmed_only_via_primary_evidence(repo):
    for f in _verify_all(repo).values():
        if f.status is Status.CONFIRMED:
            assert f.evidence.method in PRIMARY_METHODS, f.evidence.method
            assert f.evidence.files or f.evidence.sha


def test_path_present_confirmed_missing_stale(repo):
    fs = _verify_all(repo)
    assert fs[(ClaimType.PATH, "src/app.py")].status is Status.CONFIRMED
    assert fs[(ClaimType.PATH, "src/app.py")].evidence.method == "git_tree_lookup"
    assert fs[(ClaimType.PATH, "src/missing.py")].status is Status.STALE


def test_symbol_confirmed_via_ast(repo):
    fs = _verify_all(repo)
    hit = fs[(ClaimType.SYMBOL, "real_function")]
    assert hit.status is Status.CONFIRMED
    assert hit.evidence.method == "python_ast_parse"
    assert hit.evidence.files == ["src/app.py"]


def test_symbol_with_bad_file_hint_is_stale(repo):
    fs = _verify_all(repo)
    ghost = fs[(ClaimType.SYMBOL, "GhostClass")]
    assert ghost.status is Status.STALE
    assert ghost.evidence.method == "source_content_read"


def test_version_confirmed_and_stale_against_config(repo):
    fs = _verify_all(repo)
    assert fs[(ClaimType.VERSION, "2.0.0")].status is Status.CONFIRMED
    assert fs[(ClaimType.VERSION, "2.0.0")].evidence.method == "config_file_read"
    assert fs[(ClaimType.VERSION, "1.0.0")].status is Status.STALE


def test_narrative_never_confirmed(repo):
    # A prose architecture assertion yields no checkable claim -> no CONFIRMED.
    claims = extract_claims("README.md", "Our architecture is fundamentally emergent.\n")
    assert claims == []


def test_doc_to_doc_is_not_evidence(repo, tmp_path):
    # A second doc asserting the same missing path must not flip it to CONFIRMED.
    (repo / "OTHER.md").write_text("`src/missing.py` definitely exists, trust me.\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "add corroborating doc")
    reader = make_reader(str(repo), backend="git")
    claims = extract_claims("README.md", (repo / "README.md").read_text())
    findings = {(f.claim.type, f.claim.value): f for f in Verifier(reader).verify_all(claims)}
    assert findings[(ClaimType.PATH, "src/missing.py")].status is Status.STALE


def test_planner_cites_evidence_for_stale(repo):
    findings = list(_verify_all(repo).values())
    edits = plan_fixes(findings)
    assert edits
    for e in edits:
        assert e.rationale
        assert e.evidence.get("sha") or e.evidence.get("files")


def test_governance_artifacts_match_drift_format(repo):
    findings = [f for f in _verify_all(repo).values() if f.status is Status.STALE]
    edits = plan_fixes(findings)
    cfg = RepoConfig(name="CanonRec", governance_mode="canon_promotion_queue")
    arts = build_artifacts(edits, cfg, today="2026-07-13")
    assert arts.drift_log_entry.lstrip().startswith("## Drift Entry — 2026-07-13")
    assert "- **Source:**" in arts.drift_log_entry
    assert "- **Resolution:**" in arts.drift_log_entry
    assert arts.quarantine_path.startswith("canon/_quarantine/drift/")

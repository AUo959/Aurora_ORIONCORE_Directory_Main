from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import workspace_recovery_index  # noqa: E402


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_manifest(path: Path) -> None:
    payload = {
        "schema_version": 1,
        "id": "test-recovery-index",
        "default_report_path": "reports/analysis/workspace_recovery_index_latest.json",
        "max_candidates": 20,
        "min_value_score": 2,
        "max_file_bytes": 100000,
        "max_hash_bytes": 100000,
        "max_probe_bytes": 4096,
        "max_files_per_root": 100,
        "include_extensions": [".md", ".py", ".txt", ".json"],
        "include_filenames": [],
        "exclude_directory_names": [".git", "__pycache__", "node_modules"],
        "exclude_subpaths": [],
        "scan_roots": [
            {
                "path": ".",
                "mode": "top_level_files",
                "source_status": "loose_root_intake",
                "priority": "high",
                "reason": "test loose files",
            },
            {
                "path": "legacy",
                "mode": "tree",
                "source_status": "legacy_archive_intake",
                "priority": "high",
                "reason": "test legacy tree",
            },
        ],
        "value_signals": [
            {
                "id": "code_logic",
                "weight": 5,
                "extensions": [".py"],
                "content_terms": ["def ", "class ", "import "],
            },
            {
                "id": "cloudbank_runtime",
                "weight": 4,
                "path_terms": ["cloudbank", "symbolic"],
                "content_terms": ["cloudbank", "symbolicengine"],
            },
            {
                "id": "governance_or_control_plane",
                "weight": 3,
                "path_terms": ["receipt", "recovery"],
                "content_terms": ["control plane", "receipt", "recovery"],
            },
        ],
        "route_hints": [
            {
                "target": "aurora-cloudbank-symbolic-main",
                "owner_surface": "canonical nested repo",
                "path_terms": ["cloudbank", "symbolic"],
                "content_terms": ["cloudbank", "symbolicengine"],
            },
            {
                "target": "root",
                "owner_surface": "root control-plane repo",
                "path_terms": ["receipt", "recovery"],
                "content_terms": ["control plane", "receipt", "recovery"],
            },
        ],
        "validation_commands": ["python3 tools/workspace_recovery_index.py"],
    }
    write_file(path, json.dumps(payload, indent=2) + "\n")


def test_build_report_indexes_recoverable_logic_and_routes_it(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    manifest_path = root / "catalog" / "recovery_index_manifest.json"
    write_manifest(manifest_path)
    write_file(
        root / "legacy" / "cloudbank_symbolic_engine.py",
        "class SymbolicEngine:\n    def execute_chain(self):\n        return 'CloudBank'\n",
    )
    write_file(
        root / "recovery_receipt.md",
        "# Recovery Receipt\n\nThis control plane receipt records recovery routing.\n",
    )

    report = workspace_recovery_index.build_report(
        root,
        manifest_path,
        generated_at="2026-05-20T00:00:00Z",
    )

    paths = {candidate["path"]: candidate for candidate in report["candidates"]}
    assert report["status"] == "READY"
    assert paths["legacy/cloudbank_symbolic_engine.py"]["target_repo_hint"] == "aurora-cloudbank-symbolic-main"
    assert "code_logic" in paths["legacy/cloudbank_symbolic_engine.py"]["signals"]
    assert paths["recovery_receipt.md"]["target_repo_hint"] == "root"
    assert paths["legacy/cloudbank_symbolic_engine.py"]["promotion_status"] == "pending_review"
    assert paths["legacy/cloudbank_symbolic_engine.py"]["canonical_status"] == "not_promoted"


def test_build_report_skips_private_and_nested_git_content(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    manifest_path = root / "catalog" / "recovery_index_manifest.json"
    write_manifest(manifest_path)
    write_file(root / "legacy" / "clinical_notes.txt", "Patient Name: Jane Example\nDate of Birth: 1990-01-01\n")
    write_file(root / "legacy" / "nested_repo" / ".git" / "HEAD", "ref: refs/heads/main\n")
    write_file(root / "legacy" / "nested_repo" / "cloudbank_hidden.py", "def hidden():\n    return 'CloudBank'\n")

    report = workspace_recovery_index.build_report(
        root,
        manifest_path,
        generated_at="2026-05-20T00:00:00Z",
    )

    paths = {candidate["path"] for candidate in report["candidates"]}
    assert "legacy/clinical_notes.txt" not in paths
    assert "legacy/nested_repo/cloudbank_hidden.py" not in paths
    assert report["summary"]["skip_counts"]["auto_private_content"] == 1


def test_build_report_skips_configured_vendor_directories(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    manifest_path = root / "catalog" / "recovery_index_manifest.json"
    write_manifest(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["exclude_directory_names"].extend(["GitHub Desktop.app", "site-packages"])
    write_file(manifest_path, json.dumps(manifest, indent=2) + "\n")
    write_file(
        root / "legacy" / "GitHub Desktop.app" / "Contents" / "Resources" / "app" / "main.js",
        "function boot() { return 'not Aurora recovery material'; }\n",
    )
    write_file(
        root / "legacy" / "site-packages" / "yfinance" / "const.py",
        "def constants():\n    return 'not local Aurora logic'\n",
    )
    write_file(root / "legacy" / "cloudbank_logic.py", "def route():\n    return 'CloudBank'\n")

    report = workspace_recovery_index.build_report(
        root,
        manifest_path,
        generated_at="2026-05-20T00:00:00Z",
    )

    paths = {candidate["path"] for candidate in report["candidates"]}
    assert "legacy/cloudbank_logic.py" in paths
    assert not any("GitHub Desktop.app" in path for path in paths)
    assert not any("site-packages" in path for path in paths)


def test_main_persist_report_writes_configured_report_path(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    manifest_path = root / "catalog" / "recovery_index_manifest.json"
    write_manifest(manifest_path)
    write_file(root / "legacy" / "cloudbank_logic.py", "def route():\n    return 'CloudBank'\n")

    exit_code = workspace_recovery_index.main(
        [
            "--root",
            str(root),
            "--manifest",
            str(manifest_path),
            "--persist-report",
        ]
    )

    report_path = root / "reports" / "analysis" / "workspace_recovery_index_latest.json"
    assert exit_code == 0
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["summary"]["candidate_count"] == 1
    assert report["candidates"][0]["path"] == "legacy/cloudbank_logic.py"

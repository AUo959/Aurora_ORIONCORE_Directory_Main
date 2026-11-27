"""Pre-commit must preserve deliberate nested-repository pins."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import workspace_verify_precommit as gate  # noqa: E402

CHECK = TestCase()


@pytest.mark.parametrize('checks', [
    ['repo_head_match'], ['repo_branch_match'],
    ['repo_head_match', 'manifest_top_level_coverage'],
])
def test_pin_drift_blocks_without_running_a_generator(monkeypatch, checks):
    report = json.dumps({'findings': [{'check': c, 'blocking': True} for c in checks]})
    monkeypatch.setattr(gate, '_run_verify', lambda: (1, report))
    monkeypatch.setattr(gate.subprocess, 'run', lambda *a, **k: pytest.fail('must not regenerate pins'))
    CHECK.assertEqual(gate.main(), 1)


def test_manifest_healing_preserves_registry_file_and_staging_scope(tmp_path, monkeypatch):
    registry = tmp_path / 'catalog/repo_registry.yaml'
    registry.parent.mkdir()
    registry.write_text('intentional-pinned-revision\n')
    monkeypatch.setattr(gate, 'REPO_ROOT', tmp_path)
    reports = iter([(1, json.dumps({'findings': [
        {'check': 'manifest_top_level_coverage', 'blocking': True}]})),
        (0, '{"findings": []}')])
    monkeypatch.setattr(gate, '_run_verify', lambda: next(reports))
    commands = []

    def run(argv, **kwargs):
        commands.append(argv)
        if '--repo-registry-out' in argv:
            shadow = Path(argv[argv.index('--repo-registry-out') + 1])
            CHECK.assertNotEqual(shadow, registry)
            shadow.write_text('scanner-observed-revision\n')
        return SimpleNamespace(returncode=0, stdout='', stderr='')

    monkeypatch.setattr(gate.subprocess, 'run', run)
    CHECK.assertEqual(gate.main(), 0)
    CHECK.assertEqual(registry.read_text(), 'intentional-pinned-revision\n')
    CHECK.assertEqual(len(commands), 2)
    CHECK.assertEqual(commands[1][:2], ['git', 'add'])
    CHECK.assertNotIn('catalog/repo_registry.yaml', commands[1])

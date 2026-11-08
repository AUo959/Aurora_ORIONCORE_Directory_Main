"""Exercise real linked worktrees and the pre-commit healer entry point."""
import json
from pathlib import Path
import shutil
import subprocess  # nosec B404 - fixed Git/Python CLI integration tests.
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import session_claim as claims  # noqa: E402
import session_stop_hook as hook  # noqa: E402
import workspace_verify_precommit as gate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GIT_BINARY = shutil.which('git') or '/usr/bin/git'


def git(root, *args):
    # Controlled fixture paths and argv; no shell or external command text.
    return subprocess.run(  # noqa: S603,S607  # nosec B603 B607
        [GIT_BINARY, '-C', str(root), *args], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def linked(tmp_path, monkeypatch):
    root = tmp_path / 'main'
    root.mkdir()
    git(root, 'init')
    (root / 'tools').mkdir()
    for name in ('session_state_io.py', 'session_state_check.py', 'session_claim.py', '_workspace_common.py',
                 'session_stop_hook.py', 'workspace_verify_precommit.py'):
        shutil.copyfile(ROOT / 'tools' / name, root / 'tools' / name)
    (root / 'catalog').mkdir()
    shutil.copyfile(ROOT / 'catalog/session_state.json', root / 'catalog/session_state.json')
    git(root, 'add', '.')
    git(root, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-m', 'fixture')
    worktree = tmp_path / 'linked'
    git(root, 'worktree', 'add', '-b', 'test-linked', str(worktree))
    monkeypatch.setattr(claims, 'MACHINE_ID_PATH', tmp_path / 'machine-id')
    return root, worktree


def create(root, claim_id='other', posture='editing', repo='root'):
    code, result = claims.create_claim(root=root, platform='claude-code', task_id='test', repo=repo,
                                      paths=['catalog/session_state.json'], mutation_posture=posture,
                                      ttl_minutes=30, claim_id=claim_id)
    assert code == 0
    return result


def test_worktrees_share_claim_create_check_refresh_and_release(linked):
    root, worktree = linked
    create(root)
    assert claims.claims_dir(root) == claims.claims_dir(worktree)
    assert claims.check_claims(root=worktree, repo='root', paths=['catalog'])['status'] == 'conflict'
    code, _ = claims.refresh_claim(worktree, 'other', 60)
    assert code == 0
    assert claims.find_claim(root, 'other')[1]['ttl_minutes'] == 60
    assert claims.release_claim(worktree, 'other')[0] == 0
    assert claims.check_claims(root=root, repo='root', paths=['catalog'])['status'] == 'clear'
    create(worktree, 'from-linked')
    assert claims.find_claim(root, 'from-linked')[1]['worktree'] == str(worktree)


@pytest.mark.parametrize('posture,repo,expected', [
    ('editing', 'root', 3), ('read_only', 'root', 0), ('editing', 'other-repo', 0)])
def test_worktree_state_cli_honors_canonical_claim_without_clobber(linked, posture, repo, expected):
    root, worktree = linked
    create(root, posture=posture, repo=repo)
    state = worktree / 'catalog/session_state.json'
    before = state.read_bytes()
    result = subprocess.run(  # noqa: S603  # nosec B603
        [sys.executable, str(worktree / 'tools/session_state_io.py'),
                             '--platform', 'codex', 'set-summary', 'worktree regression'],
                            cwd=worktree, capture_output=True, text=True)
    assert result.returncode == expected, result.stderr + result.stdout
    if expected == 3:
        assert state.read_bytes() == before
    else:
        assert json.loads(state.read_text())['last_session_summary'] == 'worktree regression'


def test_independent_clones_have_independent_claim_stores(linked, tmp_path):
    root, _ = linked
    clone = tmp_path / 'clone'
    subprocess.run(  # noqa: S603,S607  # nosec B603 B607
        [GIT_BINARY, 'clone', str(root), str(clone)], check=True, capture_output=True)
    create(root)
    assert claims.claims_dir(clone) != claims.claims_dir(root)
    assert claims.check_claims(root=clone, repo='root', paths=['catalog'])['status'] == 'clear'


@pytest.fixture
def platform_env(monkeypatch):
    for key in ('AURORA_SESSION_PLATFORM', 'CLAUDECODE', 'CODEX_HOME', 'CODEX_CLI_PATH'):
        monkeypatch.delenv(key, raising=False)
    return monkeypatch


@pytest.mark.parametrize('signals,expected', [
    ({}, None), ({'CLAUDECODE': '1'}, 'claude-code'), ({'CODEX_HOME': '/example/codex'}, 'codex'),
    ({'CLAUDECODE': '1', 'CODEX_HOME': '/example/codex'}, None),
    ({'AURORA_SESSION_PLATFORM': 'invalid', 'CLAUDECODE': '1'}, None),
    ({'AURORA_SESSION_PLATFORM': 'codex', 'CLAUDECODE': '1'}, 'codex'),
])
def test_platform_requires_explicit_or_unambiguous_evidence(platform_env, signals, expected):
    for key, value in signals.items():
        platform_env.setenv(key, value)
    assert hook.session_platform() == expected


@pytest.mark.parametrize('platform', ['codex', 'claude-code', None])
def test_refresh_and_orphans_preserve_platform_truth(tmp_path, monkeypatch, platform_env, platform):
    if platform:
        platform_env.setenv('AURORA_SESSION_PLATFORM', platform)
    monkeypatch.setattr(hook, 'CLAIMS_DIR', tmp_path / 'claims')
    monkeypatch.setattr(hook, '_git_log_since', lambda _: [])
    state = {'last_platform': 'previous', 'recent_commits': [], 'known_state': {}}
    updated, _ = hook._update_state(state, 'abc1234')
    assert updated['last_platform'] == (platform or 'previous')
    marker = hook._write_orphan_marker(['tools/example.py'], 'abc1234')
    if platform:
        assert marker.name.startswith(f'.orphan_{platform}_')
        assert json.loads(marker.read_text())['platform'] == platform
    else:
        assert marker is None
        assert not (tmp_path / 'claims').exists()


@pytest.mark.parametrize('platform', ['codex', 'claude-code', None])
def test_precommit_healer_uses_refresh_only_without_session_side_effects(
        tmp_path, monkeypatch, platform_env, platform):
    if platform:
        platform_env.setenv('AURORA_SESSION_PLATFORM', platform)
    state = tmp_path / 'catalog/session_state.json'
    state.parent.mkdir()
    shutil.copyfile(ROOT / 'catalog/session_state.json', state)
    monkeypatch.setattr(hook, 'REPO_ROOT', tmp_path)
    monkeypatch.setattr(hook, 'STATE_PATH', state)
    monkeypatch.setattr(hook, '_git_short_sha', lambda: 'abc1234')
    monkeypatch.setattr(hook, '_git_log_since', lambda _: [])
    monkeypatch.setattr(hook, '_git', lambda *a, **k: '')
    monkeypatch.setattr(hook, '_git_uncommitted_tracked', lambda: ['tools/dirty.py'])
    monkeypatch.setattr(hook, '_stale_registry_pins', lambda: [])
    monkeypatch.setattr(hook, 'surface_queue_health', lambda **k: None)
    import session_state_io as sio
    monkeypatch.setattr(sio, 'blocking_claims', lambda *a: [])
    monkeypatch.setattr(sio, 'commit_records', lambda *a: [])
    monkeypatch.setattr(sio, 'save', lambda value: (state.write_text(json.dumps(value)), [])[1])
    for name in ('release_auto_claim', 'record_landing_ledger', '_write_orphan_marker'):
        monkeypatch.setattr(hook, name, lambda *a: pytest.fail('healer must not end a live session'))
    monkeypatch.setattr(hook.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=0, stdout='1'))
    argv = gate.HEAL_COMMANDS['session_state_freshness'][0]
    monkeypatch.setattr(sys, 'argv', argv[1:])
    assert hook.main() == 0
    assert json.loads(state.read_text())['last_platform'] == (platform or 'codex')


def test_foreign_git_environment_does_not_redirect_claims(linked, tmp_path, monkeypatch):
    root, worktree = linked
    unrelated = tmp_path / 'other'
    unrelated.mkdir()
    git(unrelated, 'init')
    monkeypatch.setenv('GIT_DIR', str(unrelated / '.git'))
    monkeypatch.setenv('GIT_WORK_TREE', str(unrelated))
    assert claims.claims_dir(worktree) == root / 'catalog/session_claims'


@pytest.mark.parametrize('refresh,expected', [(True, 1), (False, 0)])
def test_conflicting_claim_stops_refresh_before_ledger_or_state_writes(monkeypatch, platform_env, refresh, expected):
    import session_state_io as sio
    platform_env.setenv('AURORA_SESSION_PLATFORM', 'claude-code')
    monkeypatch.setattr(sys, 'argv', ['session_stop_hook.py'] + (['--refresh-only'] if refresh else []))
    monkeypatch.setattr(sio, 'blocking_claims', lambda *a: [{'platform': 'codex'}])
    released = []
    monkeypatch.setattr(hook, 'release_auto_claim', lambda: released.append(True))
    monkeypatch.setattr(hook, 'record_landing_ledger', lambda: pytest.fail('must preserve protected state'))
    monkeypatch.setattr(hook, '_update_state', lambda *a: pytest.fail('must preserve protected state'))
    assert hook.main() == expected
    assert released == ([] if refresh else [True])


@pytest.mark.parametrize('platform', ['codex', None])
def test_actual_precommit_process_refreshes_and_stages_without_ending_session(
        linked, monkeypatch, platform_env, platform):
    root, worktree = linked
    if platform:
        platform_env.setenv('AURORA_SESSION_PLATFORM', platform)
    state_path = worktree / 'catalog/session_state.json'
    state = json.loads(state_path.read_text())
    state['known_state']['main_sha'] = git(worktree, 'rev-parse', '--short', 'HEAD')
    state['last_platform'] = 'claude-code'
    state_path.write_text(json.dumps(state))
    git(worktree, 'add', '.')
    git(worktree, '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '-m', 'advance')
    platform_env.setenv('EXPECTED_TEST_HEAD', git(worktree, 'rev-parse', '--short', 'HEAD'))
    verifier = worktree / 'tools/workspace_verify.py'
    verifier.write_text("""import json, os, pathlib, sys
state=json.loads(pathlib.Path('catalog/session_state.json').read_text())
stale=state['known_state']['main_sha'] != os.environ['EXPECTED_TEST_HEAD']
print(json.dumps({'findings': [{'check':'session_state_freshness','blocking':True}] if stale else []}))
sys.exit(1 if stale else 0)
""")
    marker = worktree / 'catalog/session_claims/.claude_auto_claim'
    marker.parent.mkdir(parents=True)
    marker.write_text('keep-live-session')
    dirty = worktree / 'tools/session_state_check.py'
    dirty.write_text(dirty.read_text() + '\n# unrelated tracked work\n')
    # Fixed checked-in healer, scoped to an isolated linked-worktree fixture.
    result = subprocess.run(  # noqa: S603  # nosec B603
        [sys.executable, str(worktree / 'tools/workspace_verify_precommit.py')],
        cwd=worktree, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(state_path.read_text())['last_platform'] == (platform or 'claude-code')
    assert marker.read_text() == 'keep-live-session'
    assert not list(marker.parent.glob('.orphan_*'))
    assert git(worktree, 'diff', '--cached', '--name-only') == 'catalog/session_state.json'
    assert git(worktree, 'diff', '--name-only') == 'tools/session_state_check.py'

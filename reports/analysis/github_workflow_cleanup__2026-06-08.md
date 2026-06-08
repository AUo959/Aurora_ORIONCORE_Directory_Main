# GitHub Workflow Cleanup Receipt - 2026-06-08

Status: completed
Scope: root repo only

## Live GitHub State

- Root repo: `AUo959/Aurora_ORIONCORE_Directory_Main`
- Latest `main` commit checked: `27acff569944bea02281ba61de31bafbe4ea42b1`
- Latest `main` Aurora CI run: `27158782656` - success
- Latest `main` Secret Scan run: `27158782702` - success
- Open root PRs after cleanup: none verified through the GitHub connector after closing PR `#16`.

## Stale Failure Closed

- Closed PR: `#16` (`chore(review-debt): clear rd-20260531 x 2 - adopt Peer Review Protocol v1`)
- Disposition: closed unmerged as superseded.
- Evidence comment: `4654303203`
- Failed run addressed: Aurora CI `26765578063`, which failed on June 1 while collecting tests with `ModuleNotFoundError: No module named 'tools'`.
- Supersession evidence: current `main` exposes the repo root on `PYTHONPATH` in `.github/workflows/ci.yml`, and `04ffa60` records the accepted combined peer-review receipt.

## Salvaged Local Change

Ported only the non-conflicting test-hardening delta from PR `#16`:

- `tests/test_aurora_nested_repo_normalizer.py`
- `tests/test_workspace_verify.py`

Both temporary Git fixture repositories now set `commit.gpgsign=false` so user-level commit signing config cannot leak into fixture commits.

## Validation

- `python3 -m pytest tests/test_workspace_verify.py tests/test_aurora_nested_repo_normalizer.py -q` - 31 passed
- `python3 -m pytest tests/ -q` - 161 passed, 25 skipped
- `uv run --python /Users/travisstreets/.local/bin/python3.12 --with pytest --with pyyaml python -m pytest tests/ -q` - 161 passed, 25 skipped
- `/Users/travisstreets/.local/bin/python3.12 tools/workspace_verify.py` - warn only, 0 blocking findings
- YAML manifest validation - passed
- JSON catalog validation - passed
- Codex plugin JSON validation - passed
- Tracked size limit check - passed

## Notes

- Local `gh auth status` still reports the default token for `AUo959` as invalid, so Actions inspection used the GitHub connector plus read-only public GitHub REST calls.
- No nested repos were edited or pushed.

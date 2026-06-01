# CloudBank Issue Broker Receipt - 2026-06-01

## Scope

Built a root-control-plane CloudBank issue broker so Codex and Claude Code can
safely turn "resolve CloudBank issues" into a local claim, clean worktree, PR,
and release workflow.

## Changed Surfaces

- `tools/cloudbank_issue_broker.py`: new broker CLI with `status`, `plan`,
  `check`, `claim`, and `release`.
- `tests/test_cloudbank_issue_broker.py`: regression tests for path
  normalization, duplicate issue claims, and CLI JSON output.
- `docs/CLOUDBANK_ISSUE_BROKER_WORKFLOW_v1.md`: operator workflow.
- `README.md`, `AGENTS.md`, `Makefile`: discoverability and command wiring.
- Generated root metadata timestamps were refreshed by `python3 tools/workspace_scan.py`.

## Behavior

- Resolves the canonical CloudBank nested repo through `catalog/repo_registry.yaml`.
- Uses `catalog/session_claims/*.json` via `tools/session_claim.py`; it does not
  introduce a second tracked lock store.
- Blocks duplicate active claims for the same CloudBank issue.
- Blocks overlapping active path claims in `aurora-cloudbank-symbolic-main`.
- Reports local CloudBank worktrees whose branch or path names mention an issue.
- Emits the branch/worktree command after a successful claim, but does not run it.
- Does not mutate CloudBank, GitHub, issues, PRs, labels, or comments.

## Validation

- `python3 -m pytest -q tests/test_cloudbank_issue_broker.py`: 6 passed.
- `python3 -m pytest -q tests/test_session_claim.py tests/test_cloudbank_issue_broker.py`: 12 passed.
- `env PYTHONPYCACHEPREFIX=/private/tmp/aurora_pycache python3 -m py_compile tools/cloudbank_issue_broker.py`: passed.
- `python3 tools/cloudbank_issue_broker.py plan --issue 842 --issue 843 --json`: passed; both issues were locally claim-ready, with `canonical_cloudbank_checkout_dirty` warning.
- `python3 tools/cloudbank_issue_broker.py check --issue 842 --paths src/middleware/fastapi_security.py tests/test_security_middleware.py --json`: passed with normalized CloudBank paths.
- `python3 tools/workspace_verify.py`: pass, 0 findings.
- `python3 tools/workspace_scan.py`: completed.
- `make devkit-check`: READY, 21/21 tools.
- `make mission-control`: attention, 0 blocking items.
- `make skills-check`: command succeeded; existing installed-runtime drift remains for `aurora-skill-finder`.

## Current Local Evidence

The canonical CloudBank checkout is dirty and should not be used as the work
surface for issue resolution:

- `.env_status.json`
- `.github/dependabot.yml`
- `src/middleware/fastapi_security.py`
- `tests/test_security_middleware.py`

Use broker claim output to create clean issue worktrees from `origin/main`.

# CloudBank Workflow Fix Receipt - 2026-06-09

## Scope

- Target repo: `aurora-cloudbank-symbolic-main`
- Registered path: `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`
- Worktree used: `/private/tmp/cloudbank-fix-knowledge-aggregator-2026-06-08`
- Branch pushed: `codex/cloudbank-fix-knowledge-aggregator-2026-06-08`
- Commit pushed: `36f2ba71 fix(actions): stabilize knowledge aggregator pushes`

## Failure Evidence

The active failing workflow class was `Constellation Knowledge Aggregator`.
Run log evidence from the prior live inspection showed aggregation succeeding,
then the commit step writing generated knowledge-index changes and failing to
push with `fetch first` while other dispatch runs moved `main`.

The root cause was two-part:

- concurrent `repository_dispatch` aggregator jobs raced to commit and push to
  `main`
- the aggregator rewrote generated timestamps even when document content did
  not materially change

## Fix

- Added workflow-level concurrency for the aggregator.
- Changed checkout to fetch full history and sync to latest `origin/main`
  before aggregation.
- Changed the commit step to skip push when `knowledge-indexes/` is unchanged.
- Added `git pull --rebase origin main` before push as a final fast-forward
  guard.
- Updated `scripts/aggregate-knowledge-indexes.py` to preserve existing
  aggregate and spoke-cache files when only volatile generated timestamps
  changed.
- Added focused regression coverage in
  `tests/test_aggregate_knowledge_indexes.py`.

## Verification

- `UV_CACHE_DIR=/private/tmp/uv-cache /Users/travisstreets/.local/bin/uv run --python /Users/travisstreets/.local/bin/python3.12 --with pytest python -m pytest --confcutdir=tests tests/test_aggregate_knowledge_indexes.py -q`
  - Result: `2 passed`
- `/Users/travisstreets/.local/bin/python3.12 -m py_compile scripts/aggregate-knowledge-indexes.py tests/test_aggregate_knowledge_indexes.py`
  - Result: passed
- `ruby -e 'require "yaml"; YAML.load_file(".github/workflows/constellation-knowledge-aggregator.yml"); puts "yaml ok"'`
  - Result: `yaml ok`
- `/Users/travisstreets/.local/bin/python3.12 scripts/aggregate-knowledge-indexes.py --local`
  - Result: no material changes; generated timestamp churn suppressed
- `git diff -- knowledge-indexes`
  - Result: no diff

## Publication State

The branch was pushed to GitHub over SSH. PR creation was attempted with
`gh pr create`, but GitHub returned:

`GraphQL: API rate limit already exceeded for user ID 206913296.`

No direct push to CloudBank `main` was performed. Next safe step is to create a
PR from the pushed branch once the API rate limit resets, or explicitly approve
a direct fast-forward push to `main` if stopping the workflow storm immediately
is higher priority than preserving the PR path.

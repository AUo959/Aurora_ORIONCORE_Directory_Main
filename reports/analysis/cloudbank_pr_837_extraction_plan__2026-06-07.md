# CloudBank PR 837 Extraction Plan - 2026-06-07

## Scope

- Target repo: `AUo959/aurora-cloudbank-symbolic`
- Source PR: `#837`
- Root coordination repo: Aurora / ORIONCORE control plane
- Nested checkout mutation: none
- GitHub mutation: posted follow-up extraction plan on closed PR `#837`
- Local edit surface: root plan receipt only

## Why This Exists

Closing `#837` removed an unsafe merge candidate, but it did not by itself
preserve the useful scorecard work from the PR. This plan defines the follow-up
path: treat `#837` as an archival source for a small scorecard extraction, not
as abandoned work and not as a branch to merge or replay.

## Live Sources

- PR `#837`: `https://api.github.com/repos/AUo959/aurora-cloudbank-symbolic/pulls/837`
- PR `#837` files: `https://api.github.com/repos/AUo959/aurora-cloudbank-symbolic/pulls/837/files?per_page=100`
- Open issues: `https://api.github.com/repos/AUo959/aurora-cloudbank-symbolic/issues?state=open&per_page=100`
- Open PRs: `https://api.github.com/repos/AUo959/aurora-cloudbank-symbolic/pulls?state=open&per_page=100`
- Current CloudBank `main`: `https://api.github.com/repos/AUo959/aurora-cloudbank-symbolic/git/ref/heads/main`
- GitHub plan comment: `https://github.com/AUo959/aurora-cloudbank-symbolic/pull/837#issuecomment-4644456473`

## Current PR 837 State

- State: `closed`
- Draft: `true`
- Merged: `false`
- Base SHA: `52563a4abc261d52a0ca1885da11e697404a18a7`
- Head SHA: `60f17834aa92af466a9607fb180662677ef3467d`
- Current CloudBank `main`: `7fba7fc39e03606cb34930a8e190d122ceb1e92a`
- Scope: umbrella over `#767-#836`
- Diff size: `64` files, `2900` additions, `602` deletions
- Useful salvage target: `scripts/benchmark_scorecard.py`
- Unsafe replay surface: the other `63` changed files, spanning workflows,
  API/runtime modules, monitoring/state files, dependency manifests, docs, and
  tests.

## Scorecard Inventory

`#837` added `scripts/benchmark_scorecard.py` with `24` checks across these
domains:

- Security:
  - `HTTPException str(e) leak sites` (`#783`, required)
  - `datetime.utcnow() call sites` (`#768`)
  - `Files using Depends(verify_csrf_token)` (`#784`, required)
  - `Third-party GitHub Actions SHA-pinned` (`#832`)
  - `Docker base images digest-pinned` (`#833`)
- Testing:
  - `Test function count (info only)` (`#789`)
  - `Test file count (info only)` (`#789`)
  - `Coverage threshold configured` (`#790`, required)
  - `continue-on-error count in CI` (`#758`, required)
  - `CodeQL workflow status` (`#786`)
  - `Hollow assertion count` (`#791`)
  - `App-assembly test scaffold` (`#793`)
- Wiring:
  - `Telemetry middleware wired` (`#769`, required)
  - `EthicsEngine on production paths` (`#770`, required)
  - `Ledger verify_integrity at startup` (`#806`)
  - `Atomic-write coverage on state files` (`#807`)
  - `Request-ID middleware mounted` (`#818`)
- Ops:
  - `Health endpoints split` (`#814`)
- Supply:
  - `Python floor consistency` (`#834`)
  - `Lockfile present + hashed` (`#787`, `#835`)
  - `.env.example completeness` (`#821`)
- Connector:
  - `Connector tests exist` (`#827`, required)
  - `Bridge retries + identifying headers` (`#824`, `#826`)

## Current Coverage Map

Live open PR count when this plan was prepared: `43`.

Already covered by active draft PRs:

- `#784` -> `#901`
- `#832` / `#833` -> `#910`
- `#769` -> `#914`
- `#770` -> `#915`
- `#807` / `#808` -> `#886` / `#908`
- `#793` -> `#885`
- `#787` -> `#902`
- `#827` -> `#903`
- `#824` / `#826` -> `#890` / `#899`
- `#778` -> `#912`
- `#805` -> `#911`
- `#773` -> `#913`

Open scorecard-related issues without an active PR in this snapshot:

- `#791` hollow assertions
- `#835` pip `--require-hashes`

Historical or not open in the current open-issue snapshot; verify before making
them required scorecard gates:

- `#758`
- `#768`
- `#783`
- `#786`
- `#789`
- `#790`
- `#806`
- `#814`
- `#818`
- `#821`
- `#834`

## Execution Plan

1. Create a tracking issue for `Extract hardening benchmark scorecard from #837`.
   - If a separate issue is not desired, reopen or rename `#837` as
     tracking-only, not merge-ready.
   - Do not let `#837` close any backlog issues directly.

2. Use the CloudBank issue broker before code edits.
   - Start from current `main`.
   - Use a clean CloudBank worktree from `origin/main`.
   - Do not use the dirty canonical checkout or the closed `#837` branch as the
     edit surface.
   - First extraction claim should include only:
     - `scripts/benchmark_scorecard.py`
     - `tests/test_benchmark_scorecard.py`
     - optionally `docs/` or `README.md` for a short usage note.

3. PR A: recover the scorecard only.
   - Manually port `scripts/benchmark_scorecard.py` from `#837` head
     `60f17834aa92af466a9607fb180662677ef3467d`.
   - Discard all other `#837` file changes.
   - Update the scorecard against current `main` and current issue state.
   - Convert historical or closed issue checks to non-blocking `info` or remove
     them until verified.
   - Add tests around check registration, domain grouping, strict/strict-all
     behavior, and safe handling of missing files.
   - Validation:
     - `python3 scripts/benchmark_scorecard.py`
     - `python3 scripts/benchmark_scorecard.py --strict`
       - expected to return non-zero while required backlog rows still fail
     - `pytest tests/test_benchmark_scorecard.py`

4. PR B: add non-blocking CI publication after PR A lands.
   - Publish scorecard output as an artifact or PR comment.
   - Keep it advisory only.
   - Do not enable `--strict` as a merge gate during the active issue-PR wave.

5. PR C: enable strict gating only after the scorecard is stable.
   - Gate on required rows first.
   - Use `--strict-all` only as a later all-green burn-down target.

## Explicit Non-Replay Rule

Do not cherry-pick the other `63` files from `#837`. They overlap the current
issue-specific PR wave and touch hot merge-conflict surfaces. Any still-needed
logic outside `scripts/benchmark_scorecard.py` must get its own issue-specific
broker claim and current-`main` branch.

## Immediate Next Action

The next implementer should create or designate the scorecard tracking issue,
then run:

```bash
python3 tools/cloudbank_issue_broker.py plan --issue <tracking-issue>
python3 tools/cloudbank_issue_broker.py claim --platform codex --issue <tracking-issue> --paths scripts/benchmark_scorecard.py tests/test_benchmark_scorecard.py
```

Only after the broker claim succeeds should a clean CloudBank worktree be used
to recover the scorecard script.

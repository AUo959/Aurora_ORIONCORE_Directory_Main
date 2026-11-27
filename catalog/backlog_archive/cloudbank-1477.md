# aurora-cloudbank-symbolic#1477: ci: SONAR_TOKEN is unauthorized — every SonarCloud API query returns 401

- URL: https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1477
- State at archive: open
- Author: AUo959
- Created: 2026-08-08T14:41:48Z
- Updated: 2026-09-01T21:37:18Z
- Labels: ci, needs info, high-priority, owner-decision
- Milestone: none

## Linked pull requests (head SHA at archive time)

- aurora-cloudbank-symbolic#1381 — feat(continuity): add neutral Universal Thread Beacon schema and offline validator — merged — `feat/1377-utb-neutral-schema` @ `83dcf25f8e092e8295b76f1302a30fd955e54710`
- aurora-cloudbank-symbolic#1442 — fix(security): repair secure_storage key derivation and unskip its tests — merged — `claude/cloudbank-issues-prs-0dvl1n` @ `4047ce67773b837372ec51c105acc4b16dd9581e`
- aurora-cloudbank-symbolic#1476 — fix(ci): make the SonarCloud reporter answer why the gate failed — merged — `claude/cloudbank-issues-prs-0dvl1n-sonar-reporter` @ `5a21152ee5e38ff039c39ddb8c9e7c97d515a13b`
- aurora-cloudbank-symbolic#1506 — sim: restore recovered complete GUMAS v2 tactical lineage for deterministic control run — open (draft) — `agent/gumas-flash-rebellion-battle-baseline` @ `40b5866dba2d8ac3a0636736dcf069adaa451c8a`
- aurora-cloudbank-symbolic#1513 — docs: record AI-assisted authorship provenance — merged — `codex/cloudbank-issue-1504-ai-authorship` @ `42d7bf7234801c4aff4c92bb9aaaaf0a8eedb9d0`
- aurora-cloudbank-symbolic#1533 — feat(salvage): add deterministic corpus archaeology Phase 1 — merged — `feat/1526-corpus-archaeology-phase1` @ `6b7dffdd94dedce920223addc37497380dc5ad62`
- aurora-cloudbank-symbolic#1546 — fix(constellation): make the hub able to accept and route a real event — merged — `integration/connectivity-pass-2026-08-19` @ `7108d574d0f6f067c6e69c59d7ea90ee18d6f7db`
- aurora-cloudbank-symbolic#1729 — ci(sonar): fall back to anonymous SonarCloud API when SONAR_TOKEN is refused — merged — `claude/project-thread-68fxeb` @ `c6e9d768b61220eb62af5564b2fc2a707650a2b8`

## Branches named in the issue

- none

## Original body

## Summary

`SONAR_TOKEN` does not authenticate. Every SonarCloud Web API request made from CI returns **401**. This needs a new token in repository secrets — it cannot be fixed from a pull request.

This is almost certainly the real reason the SonarCloud reporter has never produced a useful comment, and it went unnoticed for as long as it did because the old workflow was written to swallow exactly this failure.

## Observed

First live run of the repaired reporter (#1476), firing on #1381's failed gate — run [31261077478](https://github.com/AUo959/aurora-cloudbank-symbolic/actions/runs/31261077478), job succeeded:

```text
### Could not read the quality gate

`api/qualitygates/project_status` unauthorized - SONAR_TOKEN missing, expired, or wrong scope.

**This is not an all-clear.** The gate is red; this workflow could not determine why.

> Hotspot query failed: unauthorized - SONAR_TOKEN missing, expired, or wrong scope
> Issue query failed: unauthorized - SONAR_TOKEN missing, expired, or wrong scope
```

All three endpoints — `qualitygates/project_status`, `hotspots/search`, `issues/search` — returned 401 on the same run.

## Why this went unseen

The previous reporter wrapped its single query in:

```bash
RESPONSE=$(curl -sf -u "${SONAR_TOKEN}:" "..." || echo '{"issues":[]}')  # gitleaks:allow (archive note: env-var reference, not a secret)
```

`curl -sf` exits non-zero on 401, so the fallback fired and the workflow posted:

> ### SonarCloud: No open BUG/VULNERABILITY issues returned

That is what a **401 on every request** looked like from the outside. Not "the query found nothing" — "the query was never authorized." The reporter has likely been reporting an authentication failure as a clean result on every gate failure it has ever handled, including #1442, where a hardcoded PBKDF2 salt was driving Security Rating D.

Filed as #1444 and fixed in #1476, which is why this is now visible.

## What still works

Analysis itself is fine — SonarCloud runs in Automatic Analysis mode and does not use `SONAR_TOKEN` to analyse. Gates still evaluate, check runs are still published, and the pass/fail signal is accurate. What is broken is only CI's ability to *ask why*.

The repaired reporter degrades correctly: it records the check run's own summary before any API call, so the comment still leads with the real answer —

```text
### Reported by the SonarCloud check run

Failed conditions
[C Security Rating on New Code](...) (required ≥ A)
```

— which is how #1381 was finally diagnosed at all. But the summary names only the failing *condition*. The rule, file and line live behind the API, and that is what 401 is costing.

## Impact

**#1381 is blocked on this.** Its gate has been red since 2026-07-28 with `C Security Rating on New Code`. Identifying the responsible rule requires `api/issues/search` or `api/hotspots/search`, both of which are unauthorized. Without a working token the only remaining route is bisecting by pushing candidate changes and watching the gate flip — the same expensive loop that #1442 required, and the exact thing #1444 set out to eliminate.

## Remediation

1. Generate a new SonarCloud user token (Account → Security) with access to the `AUo959_aurora-cloudbank-symbolic` project.
2. Replace the `SONAR_TOKEN` repository secret.
3. Re-run SonarCloud on #1381, or trigger the reporter's dry run:
   `Actions → SonarCloud Issue Reporter → Run workflow → pull_request_number: 1381`
   The dry run prints the report without posting, which makes this cheap to verify.

## Acceptance criteria

- The reporter's comment shows a `Quality gate: ERROR` section with a metric/threshold table, not "Could not read the quality gate".
- Hotspot and issue sections render rules, files and lines.
- #1381's failing rule is identifiable without bisecting.

Note: whether `api/hotspots/search` accepts the `pullRequest` parameter is still untested — it 401'd before that could be exercised. Raised by Copilot on #1476 and worth re-checking once the token works.

## Boundary impact

- Repository secret only. No code, no CI logic.
- No L1/L2/L3 authority change.
- No GUMAS deterministic behavior change.

Refs #1444
Refs #1476
Blocks #1381

## Comments (2)

### AUo959 — 2026-08-15T07:13:36Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1477#issuecomment-5301101992>

## Backlog execution update — 2026-08-15

The stale dependency in this issue has changed:

- PR #1381 is now merged (`7902a044`), so #1477 no longer blocks that PR.
- SonarCloud Automatic Analysis and pass/fail quality gates are working; recent PRs, including #1513, received successful SonarCloud analysis.
- The repository's Actions-secret inventory still contains **no `SONAR_TOKEN`**, so the reporter still cannot query the Web API for rule/file/line detail. The current state is therefore missing-secret, not a confirmed-current 401 from a configured token.

The acceptance criteria remain unmet and the issue stays open. Owner action is still required:

1. create a SonarQube Cloud token authorized for `AUo959/aurora-cloudbank-symbolic`;
2. store it as the repository Actions secret `SONAR_TOKEN`;
3. run the **SonarCloud Issue Reporter** dry-run against a PR with a known gate result;
4. verify the report includes the quality-gate metric table plus issue/hotspot rule, file, and line details.

Do not post the token in this issue. The item is now surfaced as `owner-decision`, `needs info`, `ci`, and `high-priority` until that secret-side validation is complete.


### AUo959 — 2026-09-01T21:37:18Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1477#issuecomment-5500774233>

## Scope correction — this does not block diagnosis, only reporting

Found while clearing #1546's red gate on 2026-09-01.

This issue is filed as though a dead `SONAR_TOKEN` makes gate failures undiagnosable. In practice it does not, because **the SonarCloud project is readable anonymously**:

```bash
curl -s "https://sonarcloud.io/api/issues/search?componentKeys=AUo959_aurora-cloudbank-symbolic&pullRequest=<PR>&types=VULNERABILITY"
curl -s "https://sonarcloud.io/api/qualitygates/project_status?projectKey=AUo959_aurora-cloudbank-symbolic&pullRequest=<PR>"
```

Both return full rule / severity / file / line detail and the per-condition gate breakdown with no credentials at all.

### Why this matters

#1546 sat red for a week. The in-PR reporter said only *"This is not an all-clear… could not determine why"*, so the cause was guessed from the diff — and **the guess was wrong**. Two unauthenticated API calls named it exactly: `githubactions:S8544` (unpinned `pip install`) and `githubactions:S8541` (missing `--only-binary=:all:`), neither of which resembled the guess.

### Suggested re-scope

The token still needs fixing, but the valuable half of the fix is different from what's written here:

1. **Fall back to the anonymous API in the reporter** when the authenticated query returns 401. It currently reports the failed query and stops; for a public project it can still name the findings. This is the change that would have saved the week.
2. Rotate `SONAR_TOKEN` for the authenticated path and for any future private-project state.
3. Keep the existing "a failed query is reported as a failed query" honesty — that behaviour is correct and should not be traded away for a fallback that could silently claim "clean".

Item 1 is a repo-side change and needs no owner decision or secret. Items 2–3 keep the `owner-decision` label.


# Independent review: CloudBank CI consolidation (#1693)

- Reviewer: claude-code (author: codex)
- Reviewed: 2026-11-10T03:50:29Z
- Verdict: **approve-with-notes**
- Debt: `rd-20261109-ci-consolidation` (cleared)
- Range: `f289f69c` to `fe99f3e5` ([CloudBank #1693](https://github.com/AUo959/aurora-cloudbank-symbolic/pull/1693)); root sync [#112](https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/pull/112)

## Summary

The cleanup is what it claims. Main's required check is exactly CI Check from the Actions app (15368), and the one job with that name lives in aurora-ci-minimal.yml, which the range does not touch. The four retired workflows were echo-only, disabled or receipt-only duplicates; no workflow, test or required check consumes their names (the two `workflow_run` consumers use a wildcard). k8s-deploy.yml and the canonical receipt gate are unchanged, and hosted logs show Run Tests verifying the exact checkout on both the PR merge commit and fe99f3e5. Constellation keeps its blocking type check and advisory audit, lint and build with all four artifacts, now from one install, and my mutation checks show the new tests catch a re-added install and a blocking audit. The workflow map matches the 37 files exactly, the simulation tree is unchanged, and the root pins agree. Notes only: several maintained AI/developer docs still describe the retired workflows (f1), an unwired generator can re-emit branch-protection.yml (f2), and the simulation freshness guard stays red on main with its tracking issue closed (f3).

## Reverified gates

| Gate | Result | Command | Evidence |
|---|---|---|---|
| environment | pass | `Detached worktree of the CloudBank clone at fe99f3e5 and the base f289f69c; env-ci Python 3.12; node v26.5.0; gh API read-only` | No live Aurora, model-provider credentials or production services. GitHub API reads only; no protection or workflow setting was changed. |
| range | pass | `git log f289f69c..fe99f3e5; git diff --stat` | One squash commit (#1693): 14 files, +102/-260. Four workflow files deleted, constellation-ci.yml edited, docs/instructions repointed, two tests updated. simulation/, package*.json, .codacy.yml and sonar-project.properties untouched. |
| required check mapping | pass | `gh api repos/AUo959/aurora-cloudbank-symbolic/branches/main/protection/required_status_checks; .../rules/branches/main; .../rulesets` | contexts ['CI Check'], checks [{context:'CI Check', `app_id:15368`}]. Rules on main: `copilot_code_review`, deletion, `non_fast_forward`; rulesets Au01, Copilot Code Review, Main Branch Protection - Require Reviews, all active; none requires a retired check. My token could read the required-checks endpoint directly, so this is first-hand, not the author's 403-limited view. |
| CI Check owner unchanged | pass | `git diff --stat f289f69c fe99f3e5 -- aurora-ci-minimal.yml k8s-deploy.yml scripts; grep job names` | No change to aurora-ci-minimal.yml, k8s-deploy.yml or scripts/. 'CI Check' is jobs.ci.name in aurora-ci-minimal.yml; 'Run Tests' is the k8s test job. |
| retired workflows were inert | pass | `git show f289f69c:<each retired file>` | branch-protection.yml: three jobs that print success. codacy.yml and codacy-analysis.yml: 'if: false'. code-quality.yml: only 'python `scripts/ci_verification.py` wait', a receipt-only wait duplicating the Kubernetes gate; its paths-ignore test was removed with it. |
| consumer audit | pass | `git grep for each workflow name, filename and job id across the tree, excluding archive; inspect workflow_run consumers` | Only wildcard `workflow_run` consumers (project-board-ci-sync, ci-status-project-automation, which reads check runs generically and excludes only its own names). No `workflow_call`, dispatch or required-check dependency. Remaining textual references are documentation (see f1) and an unwired generator (f2). |
| Kubernetes exact-checkout proof | pass | `gh api actions runs 42565913376 (PR) and 42566972090 (main); job logs for 'Run Tests'` | PR: 'Canonical CI verified checkout a3fafd335ee7dc953dbee4589f00c70708924d58 (run 42565913519)'. Main: fetch of fe99f3e5 then 'Canonical CI verified checkout fe99f3e5a300ecdc21c9fdf86563834d9e782568 (run 42566971942)'. Kubernetes jobs (manifests, Run Tests, build, staging, log validation, notification) all success. |
| hosted main run | pass | `gh api runs 42566971942 (Aurora CI Minimal), 42566971927 (Constellation CI)` | Both success at fe99f3e5; 'CI Check' job success; Constellation 'test' job success. |
| Constellation retained validation | pass | `read the workflow diff; gh api run 42566971927 jobs/steps/artifacts` | One 'npm ci --ignore-scripts'; steps in order: audit (advisory, continue-on-error) -> upload security-audit -> type check (blocking) -> upload typescript-check -> lint (advisory) -> upload lint-check -> build (advisory) -> upload build-log. All steps success; four artifacts present and unexpired: lint-check, typescript-check, security-audit, build-log. Audit now runs before the blocking check. |
| removed Constellation jobs | pass | `git show f289f69c:.github/workflows/constellation-ci.yml` | 'integration' only echoed a placeholder after an install and ran on main push only; 'security' (audit + artifact) was folded into 'test' unchanged. constellation-integration.yml, which owns contract/OpenAPI/schema/type/manifest checks, is untouched. |
| contract tests | pass | `env-ci python -m pytest tests/test_ci_verification.py tests/test_public_readiness_ci_security.py tests/test_collab_workflow_trigger.py -q` | 54 passed (the author's 52 count was for the first two files; plus the collab trigger tests). |
| mutation: extra install | pass | `insert a second 'npm ci --ignore-scripts' in constellation-ci.yml, rerun the two test files, restore` | 2 failed (`test_constellation_preserves_unique_validation_with_one_install`, `test_constellation_ci_executes_only_installed_node_tools`); file restored, worktree clean. |
| mutation: blocking audit | pass | `remove continue-on-error from the audit step, rerun test_ci_verification.py, restore` | 1 failed (`test_constellation_preserves_unique_validation_with_one_install`); restored. |
| workflow YAML and map | pass | `yaml.safe_load all .github/workflows/*.yml; compare CI_WORKFLOW_MAP.md inventory to files` | 37 files, all parse as mappings. Inventory lists exactly the 37 files: none missing, none extra. 41 workflow files at f289f69c. actionlint was not installed here, so the author's actionlint pass is not independently reproduced. |
| Constellation local check | pass | `npm ci --ignore-scripts --no-audit; ./node_modules/.bin/tsc -p tsconfig.constellation.json --noEmit --skipLibCheck; npm audit --audit-level=moderate --json` | npm ci exit 0; tsc exit 0 (node v26.5.0 locally, hosted job stays Node 20). Audit reports 35 findings (6 low, 21 moderate, 5 high, 3 critical) vs the author's 39; advisory only and moves with the advisory database; no dependency or policy change in the range. |
| simulation owner unchanged | pass | `git diff --quiet f289f69c fe99f3e5 -- simulation; git rev-parse fe99f3e5:simulation/l1_runtime.py` | Diff empty; blob 5b6d93515fb219cb26d267db6c6df6c052413ae1, equal to the policy owner blob. |
| root pins in #112 | pass | `git show 0e8fc755 for registry, policy and progression test` | `repo_registry` `head_sha`, policy `cloudbank_repository_sha` and `CLOUDBANK_SHA` all moved f289f69c -> fe99f3e5; nothing else pin-related changed. Later root #114 moved them forward to b68c4717 (SSE guard) as intended; the cleanup is preserved in current CloudBank main (0 retired workflow files, 37 workflows). |
| CloudBank full suite | not-run | `not re-run` | Hosted evidence only: PR and main runs report 3,818 passed, 92 skipped, nine expected failures, two expected-test passes. I ran the subset that touches this change (54 tests) and the later SSE review's full make check on the descendant b68c4717 line, not this historical commit. |
| simulation freshness guard | pass | `gh run list --workflow simulation-state-freshness.yml; gh issue view 1083` | Red on f289f69c, fe99f3e5 and b68c4717, as the author documented, so it predates and is independent of this change. Not suppressed and no timestamp was refreshed. #1083 (GAP-010) is CLOSED while the guard still fails (f3). |
| root gates for this receipt | pass | `make session-state-check; make registry-sync-check; python tools/aurora_integration_gate.py; focused receipt/session tests` | session-state-check OK; registry-sync-check exit 0 (0 drifted, 9 skipped because nested repos are absent in a fresh worktree); integration gate exit 0, verdict warn (existing advisories); 139 passed, 1 skipped in the session/peer/receipt/debt/queue test subset. |

## Findings

### f1 (note, accepted-with-note)

Maintained developer and AI-assistant documents still describe retired workflows as live: CLAUDE.md (lines 361, 367, 1288), `docs/CODE_QUALITY_SYSTEM.md` (114, 188) and `.github/BOT_IMPROVEMENTS.md`, `BOT_REFINEMENT_GUIDE.md` and `AGENT_WORKFLOW_INVESTIGATION.md.` The author repointed the auditor/Copilot instructions and Codacy setup docs, which is accurate for the files it names, but CLAUDE.md in particular is read by assistants as current guidance. Documentation only; no behavior depends on it.

Evidence: git grep -nE 'code-quality\.yml|codacy(-analysis)?\.yml|branch-protection\.yml' origin/main -- CLAUDE.md `docs/CODE_QUALITY_SYSTEM.md` .github (excluding workflows and archive) lists the references above on current main.

Correction: Fold into the roadmap-1.1 consumer audit: repoint or mark historical in one docs pass. Not queued as a separate task.

### f2 (note, accepted-with-note)

`automation/health/phase2_health_optimizer.py` contains a generator that writes .github/workflows/branch-protection.yml (the retired echo-only workflow). Nothing in CI or the Makefile invokes it, so this is a latent re-creation path rather than an active one.

Evidence: Source lines near 205-215 write the workflow content; repo-wide grep finds the script referenced only by archived reports and scan manifests.

Correction: Retire or neutralise the generator when the legacy-consumer audit reaches automation/; no action needed for this change.

### f3 (note, accepted-with-note)

The simulation-state-freshness guard fails on every recent main commit while its tracking issue, #1083 (GAP-010), is CLOSED. The author's statement that the failure is pre-existing and unrelated is correct, but the closed issue no longer points at open work. Per instructions the guard was not suppressed and no state was refreshed.

Evidence: Runs: failure at f289f69c (2026-11-09T01:36Z), fe99f3e5 (2026-11-09T05:22Z), b68c4717 (2026-11-10T02:42Z); gh issue view 1083 state CLOSED.

Correction: Owner/process decision outside this review: reopen or replace the tracking issue so the red guard has an open owner.

## Not verified

- actionlint pass on the changed workflow (tool not installed here); YAML parse and the contract tests were run instead.
- CloudBank full make check on fe99f3e5 itself; relied on the hosted PR/main runs for that commit.
- Contents of the external Codacy app configuration (not in the repository).

# Session-status mod Codacy remediation

PR: <https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/pull/94>

Initial Codacy gate reported 64 issues; GitHub exposed the first 50 annotations. Those included duplicate Bandit security diagnostics on test assertions and subprocess calls, control-character regex warnings, bare documentation URLs, and source complexity. The critical classification was a complexity finding, not an established exploit.

Remediation retains the adapter/host tests. Test conditions now use unittest assertions. Git and Node executable paths are resolved before process launch. Narrow B404/B603 and S603 annotations document the reviewed shell-free, fixed-verb process boundaries; no source or test directories were excluded from analysis. Status assembly was split into source, active-task, and checkout helpers. Character filtering now uses numeric code points. Documentation URLs use Markdown autolinks.

Validation: 34 focused pytest tests passed, including the Node host harness; Bandit returned no findings; Ruff security and McCabe checks passed at complexity ceiling 15; session-state validation and diff whitespace checks passed. Remote Codacy reassessment remains pending at publication.

Visual testing in an actual Claude Code host remains pending because Claude Code is unavailable in this execution environment. Keep the PR draft until that acceptance check is complete. CloudBank model migration remains separate.

Second pass: remote gate fell from 64 to 11 issues. Remaining subprocess audit findings were reviewed against the upstream Semgrep rules; the reader now explicitly allowlists only three read-only Git queries and tests rejection of mutating verbs. Per-call Semgrep annotations cover only the reviewed subprocess rule IDs. Checkout resolution, registry loading, queue selection and continuation selection were split into small helpers to meet Codacy's stricter per-function complexity limits. The receipt URL was corrected to an autolink.

Third pass: remote gate reached eight issues: seven subprocess findings and one helper complexity finding (stricter limit eight). Pin comparison was extracted. Codacy did not honor the upstream-qualified Semgrep IDs, so reviewed process calls use call-local nosemgrep comments alongside the documented fixed-argv boundary; no file exclusions or global rule changes were made.

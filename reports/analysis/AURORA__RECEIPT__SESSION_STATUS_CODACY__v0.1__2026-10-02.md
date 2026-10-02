# Session-status mod Codacy remediation

PR: https://github.com/AUo959/Aurora_ORIONCORE_Directory_Main/pull/94

Initial Codacy gate reported 64 issues; GitHub exposed the first 50 annotations. Those included duplicate Bandit security diagnostics on test assertions and subprocess calls, control-character regex warnings, bare documentation URLs, and source complexity. The critical classification was a complexity finding, not an established exploit.

Remediation retains the seven adapter/host tests. Test conditions now use unittest assertions. Git and Node executable paths are resolved before process launch. Narrow B404/B603 and S603 annotations document the reviewed shell-free, fixed-verb process boundaries; no source or test directories were excluded from analysis. Status assembly was split into source, active-task, and checkout helpers. Character filtering now uses numeric code points. Documentation URLs use Markdown autolinks.

Validation: 33 focused pytest tests passed, including the Node host harness; Bandit returned no findings; Ruff security and McCabe checks passed at complexity ceiling 15; session-state validation and diff whitespace checks passed. Remote Codacy reassessment remains pending at publication.

Visual testing in an actual Claude Code host remains pending because Claude Code is unavailable in this execution environment. Keep the PR draft until that acceptance check is complete. CloudBank model migration remains separate.

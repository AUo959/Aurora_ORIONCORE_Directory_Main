# aurora-cloudbank-symbolic#1534: ci: align SonarQube Automatic Analysis scope with repository intent

- URL: https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1534
- State at archive: open
- Author: AUo959
- Created: 2026-08-18T04:00:02Z
- Updated: 2026-08-18T04:00:02Z
- Labels: ci, high-priority, repo-hygiene
- Milestone: none

## Linked pull requests (head SHA at archive time)

- aurora-cloudbank-symbolic#1533 — feat(salvage): add deterministic corpus archaeology Phase 1 — merged — `feat/1526-corpus-archaeology-phase1` @ `6b7dffdd94dedce920223addc37497380dc5ad62`
- aurora-cloudbank-symbolic#1561 — fix(ai_core): stop sending parameters the Claude models reject — merged — `fix/1560-anthropic-sampling-params` @ `46a3916e7ba6989fe56ce113bd0f19261d88cf20`

## Branches named in the issue

- none

## Original body

## Summary

Aurora CloudBank currently uses **SonarQube Cloud Automatic Analysis**, but the repository's intended analysis scope and exclusions are defined in `sonar-project.properties`.

According to current SonarQube Cloud documentation, Automatic Analysis ignores `sonar-project.properties`; Automatic Analysis configuration belongs in `.sonarcloud.properties` and/or the SonarQube Cloud project UI.

The repository currently has **no `.sonarcloud.properties` file**.

This creates a provenance problem for quality-gate results: the repository appears to declare one scope, while Sonar's actual automatic-analysis scope may be broader.

## Evidence

### Repository state

`sonar-project.properties` currently declares:

```properties
sonar.sources=src,modules,aurora_api.py,aurora_cli.py
sonar.tests=tests
sonar.exclusions=...
```

But the project is documented in #1477 as using SonarCloud **Automatic Analysis**.

No `.sonarcloud.properties` file is present on `main`.

### External documentation

SonarQube Cloud's Automatic Analysis documentation states that when a repository contains `sonar-project.properties`, Automatic Analysis ignores those parameters. It documents `.sonarcloud.properties` as the repository-side configuration surface for Automatic Analysis.

### Triggering observation

Draft PR #1533 changes only:

- `tools/salvage/...`
- `schemas/salvage/...`
- `tests/...`

Native CI, CodeQL, Code Quality, PR Evaluation, Constellation CI, branch-protection, and Codacy are green on the current head, but SonarQube Cloud reports a failed analysis. Because the intended `sonar-project.properties` scope is not authoritative in Automatic Analysis, it is not currently possible to infer from repository configuration alone whether `tools/salvage` is inside or outside Sonar's actual analyzed new-code scope.

This does **not** establish that Sonar's red result is false. It establishes that the repository's checked-in scope declaration is not the configuration actually governing Automatic Analysis.

## Related diagnostic blocker

#1477 remains open because `SONAR_TOKEN` is unauthorized. Sonar's pass/fail signal still works, but the repository reporter cannot retrieve the rule/file/line details needed to attribute a failure efficiently.

Together these create two distinct problems:

1. **scope ambiguity** — this issue;
2. **diagnostic API authentication failure** — #1477.

## Proposed remediation

Choose one analysis mode explicitly and make repository configuration match it.

### Option A — retain Automatic Analysis

- Add a minimal `.sonarcloud.properties` that encodes the intended supported Automatic Analysis scope/exclusions.
- Reconcile supported properties against `sonar-project.properties`.
- Document any settings that must remain UI-owned.
- Treat `sonar-project.properties` as CI-scanner-only or retire it if no CI-based analysis uses it.

### Option B — move to CI-based analysis

- Disable Automatic Analysis in SonarQube Cloud.
- Run a supported scanner in CI using `sonar-project.properties`.
- Ensure only one analysis method is active.

Do **not** enable both methods simultaneously; Sonar documents Automatic Analysis and CI-based analysis as mutually exclusive analysis modes.

## Acceptance criteria

- The active Sonar analysis method is explicitly documented.
- Repository-side scope configuration is authoritative for that method.
- A changed file can be deterministically classified as analyzed or excluded from repository-visible configuration.
- The intended source/test distinction is preserved.
- #1477 is linked but remains independently fixable; solving scope does not require weakening diagnostic honesty.
- No Sonar finding is suppressed merely to turn a gate green.

## Boundary impact

- CI/analysis configuration only.
- No L1/L2/L3 authority change.
- No runtime or canon change.
- No GUMAS deterministic behavior change.

Refs #1477
Refs #1533

## Comments (0)

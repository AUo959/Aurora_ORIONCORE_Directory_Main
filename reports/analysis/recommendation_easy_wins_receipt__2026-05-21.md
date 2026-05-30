# Recommendation Easy Wins Receipt - 2026-05-21

## Scope

Evaluated the current recommendation engine output and applied the low-risk
root-control-plane cleanup that did not require system installs, nested repo
mutation, canon promotion, or recovery extraction.

## Evaluation

- Developer-tooling recommendations are not easy wins in this repo turn.
  Homebrew is absent, so Docker, Go, and Rust remain blocked behind
  system-level package-manager work. `xcodebuild` exists at `/usr/bin/xcodebuild`
  but `xcodebuild -version` reports that the active developer directory is
  `/Library/Developer/CommandLineTools`, not full Xcode.
- Recovery recommendations are actionable only as routing evidence. No
  candidate was promoted or copied into a canon surface.

## Easy Win Applied

Added recovery-index exclusions for obvious vendored archive noise:

- `GitHub Desktop.app`
- `site-packages`

This keeps third-party application resources and Python package snapshots from
being ranked as recoverable Aurora work while leaving the original archive
material untouched.

## Impact

Before:

- scanned files: `3491`
- discovered candidates: `1168`
- retained candidates: `100`
- archive retained candidates: `44`
- review-required retained candidates: `9`
- root routed retained candidates: `36`

After:

- scanned files: `2371`
- discovered candidates: `1011`
- retained candidates: `100`
- archive retained candidates: `39`
- review-required retained candidates: `8`
- root routed retained candidates: `32`

The retained candidate cap still applies, so this pass reduced noise and let
other recovery candidates surface into the top `100`; it did not resolve the
remaining recovery-review recommendations.

Clean post-commit recommendation refresh:

- recommendation count: `11`
- blocking recommendations: `0`
- approval-required recommendations: `11`
- P1 recovery review: `36` restricted candidates
- routed recovery groups: CloudBank `47`, QGIA library `1`, QGIA spine `12`,
  root `32`, manual review `8`

## Validation

```bash
python3 -m json.tool catalog/recovery_index_manifest.json
python3 -m pytest -q tests/test_workspace_recovery_index.py
python3 tools/workspace_recovery_index.py --persist-report
python3 tools/workspace_recovery_index.py --summary
python3 tools/aurora_recommendation_engine.py --persist-report --summary
```

Results:

- recovery-index manifest JSON: valid
- recovery-index focused tests: `4 passed`
- recovery-index summary: `READY`, `2371` scanned files, `100` retained of
  `1011` discovered, no findings
- recommendation-engine summary: `11` recommendations, `0` blocking,
  `11` approval-required

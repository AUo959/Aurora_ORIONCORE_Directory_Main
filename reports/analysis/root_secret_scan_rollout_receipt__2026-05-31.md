# Root Secret Scan Rollout Receipt - 2026-05-31

Timestamp: 2026-05-31T14:14:20Z

Scope: root control-plane repo plus read-only inspection of registered nested
repos from `catalog/repo_registry.yaml`. No nested repo files were edited. No
push was performed.

## Root Changes

- `.github/workflows/secret-scan.yml`
  - Added `workflow_dispatch` for manual verification reruns.
  - Updated `actions/checkout` from `v4` to `v6`.
  - Updated `gitleaks/gitleaks-action` from `v2` to `v3`.
  - Set `GITLEAKS_CONFIG=.gitleaks.toml`.
  - Set `GITLEAKS_ENABLE_COMMENTS=false` so `contents: read` remains sufficient.
  - Set `GITLEAKS_VERSION=8.30.1` to match the root devkit tool version.
- `.gitleaksignore`
  - Added 5 fingerprint-only baselines for historical
    `catalog/session_state.json` AWS access-key ID findings.
  - These baselines do not declare the credential safe and do not satisfy the
    owner deactivation check.
- `.gitignore`
  - Allowed root Git tracking of `.gitleaksignore`.
- `catalog/session_state.json`
  - Redacted the AWS access-key ID from current handoff text.
  - Updated the pending owner action wording to reflect historical
    `catalog/session_state.json` exposure and owner-required remediation.
- `catalog/classification_overrides.yaml`
  - Registered `.gitleaksignore` as a managed root policy file.
- Generated root control-plane surfaces refreshed by
  `python3 tools/workspace_scan.py`
  - `catalog/workspace_manifest.yaml`
  - `catalog/repo_registry.yaml`
  - `docs/workspace-map.md`
  - `reports/analysis/workspace_scan_summary.json`

## Validation

Initial `gitleaks detect --config .gitleaks.toml --source . --redact --no-banner`
found 5 redacted `aws-access-token` findings, all historical
`catalog/session_state.json` references. After current-file redaction and the
fingerprint-only baseline, the root gate passed.

Final command results:

| Command | Result |
| --- | --- |
| YAML contract check for `secret-scan.yml`, `ci.yml`, pre-commit config, manifest, registry | pass |
| `pre-commit run --config .pre-commit-config.yaml --files ...` | pass |
| `gitleaks detect --config .gitleaks.toml --source . --redact --no-banner` | pass; 144 commits scanned, no leaks found |
| `python3 tools/workspace_verify.py` | pass; 0 findings |
| `python3 -m pytest tests/ -q --tb=short` | pass; 154 passed, 25 skipped |
| `make devkit-check` | pass; READY, 21/21 tools ok |
| `make mission-control` | attention only; 0 blocking, 7 inbox items |
| `make integration-gate` | pass after releasing the editing session claim |

Reference checked for the action update:

- https://github.com/gitleaks/gitleaks-action
  - Current example uses `actions/checkout@v6` and
    `gitleaks/gitleaks-action@v3`.
  - The upstream migration note says `v3` moves to the Node 24 runtime with no
    behavior/input change from `v2`.
  - The upstream README states `GITLEAKS_LICENSE` is required for organization
    repositories, not personal accounts.

## Registered Repo Readiness

Read-only inspection only. Each repo remains a separate Git boundary and needs
its own branch, commit, PR, and push decision.

| Repo | Path | Branch/state | Existing secret scan | Existing gitleaks config | Boundary note |
| --- | --- | --- | --- | --- | --- |
| `aurora-cloudbank-symbolic-main` | `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main` | `codex/cloudbank-gumas-mutation-auth-2026-05-25`; dirty files present | no | no | Do not add rollout changes onto the current dirty auth-middleware branch. Use a clean branch/worktree. |
| `CanonRec` | `GUMAS_SIM_2.5/CanonRec` | `main`, clean | no | no | Separate repo; root push will not publish it. |
| `DuelSim_v2.0` | `GUMAS_SIM_2.5/DuelSim/DuelSim_v2.0` | `main`, clean | no | no | Separate repo; root push will not publish it. |
| `qgia-knowledge-library-main` | `qgia-knowledge-library-main` | `main`, clean | no | no | Separate repo; root push will not publish it. |
| `qgia-knowledge-spine-main` | `qgia-knowledge-spine-main` | `main`, clean | no | no | Separate repo; root push will not publish it. |

## Smallest Safe Rollout Package

Do not copy the root `.gitleaks.toml` or `.gitleaksignore` into other repos by
default. The root allowlist and baseline are root-specific. The smallest safe
first rollout for each registered repo is only this workflow file:

```yaml
name: Secret Scan (gitleaks)

on:
  push:
    branches: ["**"]
  pull_request:
    branches: ["**"]
  workflow_dispatch:

permissions:
  contents: read

jobs:
  gitleaks:
    name: Detect secrets
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v6
        with:
          fetch-depth: 0

      - name: Run gitleaks
        uses: gitleaks/gitleaks-action@v3
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITLEAKS_ENABLE_COMMENTS: "false"
          GITLEAKS_VERSION: "8.30.1"
```

If a repo needs a local allowlist after its first redacted scan, add a
repo-local `.gitleaks.toml` and, only for already reviewed historical findings,
a fingerprint-only `.gitleaksignore` in that same repo. Do not use the root
baseline outside the root repo.

## Still Needs Approval

- Owner must verify/deactivate the redacted AWS IAM access-key ID in AWS before
  accepting the historical baseline as final.
- Owner must approve whether to keep the fingerprint-only baseline or instead
  perform destructive history remediation. No history rewrite was attempted.
- Owner must approve pushing the root branch. This session intentionally did not
  push.
- Owner must approve per-repo rollout branches/PRs for each registered nested
  repo. No nested repo was mutated.
- If any registered repo is owned by a GitHub organization account, add
  `GITLEAKS_LICENSE` as a repo or org secret before enabling the workflow there.

## Repo-Boundary Constraints

- Root controls only root CI and control-plane metadata.
- Nested repo rollout must occur inside each registered repo boundary.
- Root `.gitleaksignore` is not a canon promotion and is not evidence that the
  underlying credential is inactive.
- CloudBank rollout should wait for a clean worktree or a dedicated worktree
  because the registered CloudBank path currently has unrelated dirty auth work.

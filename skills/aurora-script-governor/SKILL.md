---
name: aurora-script-governor
description: Govern Aurora repository script surfaces with deterministic checks and safe remediation guidance. Use when users need to convert empty/setup stubs into diagnostic no-op scripts, consolidate duplicate branch-cleanup scripts into one canonical entrypoint plus compatibility wrappers, and triage hazardous script patterns before commit. Trigger on requests like script governance, script canonization, setup script hardening, branch cleanup consolidation, hazard sweep, trust matrix for scripts, or pre-commit script safety. Not for Aurora narrative canon reconciliation; use aurora-canon-reconciler for worldbuilding continuity.
author: Aurora ORIONCORE
---

# Aurora Script Governor

## Overview
Harden Aurora script surfaces with a policy-first workflow: scan first, classify risk, then apply minimal safe fixes. Keep behavior stable while reducing script drift and maintenance ambiguity.

Use this skill for focused script-governance batches. For broader repo operations hardening, pair with `aurora-repo-stabilizer`.

## Workflow

### Step 1: Collect Governance Evidence
Run the scanner first and treat its output as the baseline:

```bash
python /path/to/skill/scripts/script_governance_scan.py --repo <repo_root> --out /tmp/script_governance_scan.json --pretty
```

Prioritize these categories:
- setup script stubs and unsafe setup behavior
- branch-cleanup duplication and canonical entrypoint drift
- script hazard patterns (string interpolation mistakes, malformed git commands, unsafe shell patterns)

### Step 2: Classify Findings by Impact
Use the following severity order:
1. `high`: destructive or misleading execution risk (zero-byte setup entrypoints, dangerous shell patterns, no canonical branch cleanup entrypoint)
2. `medium`: maintainability or correctness risk likely to regress behavior (duplicate non-wrapper cleanup implementations, shell=True usage, malformed git subcommands)
3. `low`: style or dormant-risk items that should be batched when touching nearby scripts (disabled-script hazards, minor guidance gaps)

### Step 3: Apply Minimal Safe Remediation

#### A) Setup Script Governance
For zero-byte or ambiguous setup scripts, convert to explicit diagnostic no-ops:
- print current repo context
- report key dependency/environment presence
- provide next-step guidance without mutating state

Do not auto-install dependencies or write environment files unless explicitly requested.

#### B) Branch Cleanup Canonicalization
Standardize on one canonical entrypoint (prefer `branch_manager.py` when present under the repo's `scripts/` directory).
For alternate entrypoints:
- keep user-facing filenames as thin wrappers
- delegate directly to canonical entrypoint
- preserve CLI pass-through (`"$@"` for shell wrappers)

Avoid deleting wrappers that external automation may still call.

#### C) Hazard Triage Batch
Fix hazards in one focused pass for touched script families:
- convert brace-literal log lines to real interpolation (`f"...{var}..."`)
- repair malformed git subcommands
- replace unsafe shell execution patterns with argument-list subprocess calls where practical

### Step 4: Validate and Report
After edits:
1. run modified scripts in dry-run/diagnostic mode
2. rerun scanner to confirm finding reduction
3. report: high-risk findings, applied fixes, residual risks

For cross-skill package workflows, align findings to the shared schema at `/Users/travisstreets/.codex/skills/aurora-governance-orchestrator/references/finding_schema.md`.

## Workflow Position

- Upstream: `aurora-skill-finder` for routing, or `aurora-repo-stabilizer` when repo hardening narrows into script-surface work.
- Downstream: hand merged governance requests to `aurora-governance-orchestrator`.
- Preset reference: `/Users/travisstreets/.codex/skills/aurora-governance-orchestrator/references/workflow_presets.md`.

## Command Patterns

Quick scan:
```bash
python /path/to/skill/scripts/script_governance_scan.py --repo .
```

Write JSON report:
```bash
python /path/to/skill/scripts/script_governance_scan.py --repo . --out /tmp/script_governance_scan.json --pretty
```

Filter out disabled scripts from hazard totals:
```bash
python /path/to/skill/scripts/script_governance_scan.py --repo . --exclude-disabled --pretty
```

## Resources
- `scripts/script_governance_scan.py`: deterministic scanner for setup/branch/hazard governance findings
- `references/governance-playbook.md`: remediation rules and wrapper/no-op templates

---
name: aurora-repo-stabilizer
description: Stabilize Aurora repositories that have overlapping scripts, fragile hooks, placeholder automation, or unclear validation paths. Use when users ask to harden pre-commit/pre-push/CI behavior, build a trusted script matrix, reduce script sprawl, repair maintenance pipelines, or produce a prioritized safe-fix plan for scripts and repo ops tooling. Trigger on requests like stabilize repo, script audit, trust matrix, fix broken hooks, validation loop, cleanup automation, or maintenance hardening. Not for canonizing narrative entities; use aurora-canon-reconciler for worldbuilding canon reconciliation.
author: Aurora ORIONCORE
---

# Aurora Repo Stabilizer

## Overview
Audit and stabilize Aurora repository operations with a deterministic workflow: map scripts, classify trust, detect blockers, and apply minimal safe fixes. Prioritize operational reliability over broad refactors.

## Workflow

### Step 0: Confirm Scope
Treat this as an engineering-ops task when the request is about scripts, hooks, CI behavior, validation reliability, or maintenance automation.

If the request is about L1/L2/L3 entity canon promotion or continuity reconciliation, hand off to `aurora-canon-reconciler`.

### Step 1: Build Baseline Evidence
Run the scanner first:

```bash
python /path/to/skill/scripts/repo_stabilizer_scan.py --repo <repo_root> --out /tmp/repo_stabilizer_scan.json
```

Use the scan output as the source of truth for:
- zero-byte scripts
- disabled scripts
- placeholder/mock markers
- obvious execution hazards
- potential duplicate script families

### Step 2: Classify Script Trust
Use four classes:
- `trusted`: validated in current repo context; no placeholder/hazard flags
- `candidate`: appears healthy but not yet execution-verified
- `risky`: executable but has placeholders, hazardous command patterns, or inconsistent behavior
- `stub/disabled`: zero-byte or `.disabled`; never treat as active implementation

Do not guess trust levels from filenames only.

### Step 3: Identify Stabilization Targets
Prioritize in this order:
1. Broken execution paths (hook scripts, validator entrypoints, malformed git commands)
2. Misleading automation (scripts that claim functionality but return placeholder text)
3. Duplicate/overlapping scripts with no clear owner
4. Noise reduction (archive or mark deprecated variants after validation)

For each target, capture:
- impact
- evidence file/line
- proposed minimal change
- regression risk

### Step 4: Apply Minimal Safe Fixes
Fix only what is needed for reliability:
- preserve behavior unless it is clearly broken
- avoid speculative rewrites
- keep changes local and reversible
- run targeted validation after edits

Validation preference:
1. direct script invocation for modified scripts
2. targeted tests
3. broader suite only when necessary

### Step 5: Produce Deliverables
Return:
1. `Trust Matrix` summary (counts + notable scripts)
2. `Critical Findings` ordered by severity
3. `Applied Fixes` with file references
4. `Residual Risks` and what is intentionally deferred

## Command Patterns

Quick scan:
```bash
python /path/to/skill/scripts/repo_stabilizer_scan.py --repo .
```

Write pretty JSON:
```bash
python /path/to/skill/scripts/repo_stabilizer_scan.py --repo . --out /tmp/scan.json --pretty
```

## Resources
- `scripts/repo_stabilizer_scan.py`: deterministic scanner for script-surface risk profiling
- `references/stabilization-playbook.md`: fix-order rules and decision guide
- For cross-skill governance workflows, align findings to the shared schema at `/Users/travisstreets/.codex/skills/aurora-governance-orchestrator/references/finding_schema.md`.

## Workflow Position

- Upstream: `aurora-skill-finder` when repo-surface routing is unclear.
- Downstream: hand targeted setup/wrapper/hazard work to `aurora-script-governor`; hand merged governance to `aurora-governance-orchestrator`.
- Preset reference: `/Users/travisstreets/.codex/skills/aurora-governance-orchestrator/references/workflow_presets.md`.

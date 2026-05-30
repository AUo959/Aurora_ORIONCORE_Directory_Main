---
name: aurora-governance-orchestrator
description: Orchestrate Aurora governance scanners into one deterministic promotion verdict with merged findings and remediation. Use when users ask for full governance preflight, one report for readiness, unified go/no-go gating, cross-domain drift checks, or orchestration across threadcore-governor, zipwiz-governor, aurora-script-governor, aurora-narrative-tone-governor, aurora-repo-stabilizer, and optional aurora-canon-reconciler draft validation.
author: Aurora ORIONCORE
---

# Aurora Governance Orchestrator

## Overview
Run a single governance preflight that executes selected Aurora specialist scanners, normalizes severity and scope, and emits one merged verdict (`BLOCKED`, `PROMOTE_WITH_REMEDIATION`, or `PROMOTE`).

## Workflow

### 1) Run the orchestrator CLI
Use the script in this skill:

```bash
python3 /Users/travisstreets/.codex/skills/aurora-governance-orchestrator/scripts/orchestrate_governance.py \
  --repo /path/to/repo \
  --out-json /tmp/aurora_governance_orchestrator.json \
  --out-md /tmp/aurora_governance_orchestrator.md
```

Optional routing controls:

```bash
python3 /Users/travisstreets/.codex/skills/aurora-governance-orchestrator/scripts/orchestrate_governance.py \
  --repo /path/to/repo \
  --mode changed-paths \
  --changed-paths "path/a.json,scripts/tool.sh" \
  --strictness balanced
```

Optional canon validation path:

```bash
python3 /Users/travisstreets/.codex/skills/aurora-governance-orchestrator/scripts/orchestrate_governance.py \
  --repo /path/to/repo \
  --draft-input /path/to/draft.json \
  --draft-auto-detect
```

### 2) Interpret outputs
Read both outputs:
- JSON: machine-readable merged report for downstream automation.
- Markdown: human-readable governance summary and remediation queue.

Review these sections first:
1. Root resolution diagnostics.
2. Domain execution summary.
3. Blocking findings.
4. Final verdict and confidence.

### 3) Apply routing and severity policy
Use the orchestrator defaults:
1. `BLOCK` in `threadcore`, `canon`, `script_governor`, or `narrative_tone` blocks promotion.
2. `BLOCK` in `zipwiz` blocks promotion unless it is `evolution_evidence` (reference-only scope).
3. Execution-health failures in selected authoritative domains block promotion.
4. `repo_stabilizer` outputs are advisory in v1.

### 4) Follow remediation queue
Apply the deduplicated remediation queue in priority order:
1. `BLOCK` actions first.
2. Then `WARN` actions.
3. Rerun orchestrator after remediations and compare verdict delta.

## Resources

### scripts/
- `orchestrate_governance.py`: CLI entrypoint for unified governance orchestration.
- `test_orchestrate_governance.py`: unit tests for routing, normalization, verdict, and schema behavior.

### references/
- `finding_schema.md`: shared cross-skill finding payload fields for governor workflows.
- `routing_and_severity.md`: domain routing heuristics, severity normalization, and verdict policy.
- `workflow_presets.md`: canonical cross-skill workflow chains for promotion, repo hardening, simulation-to-brief, and selective integration gating.

### assets/
- `assets/templates/unified_report.md`: report template shape for stable section ordering.

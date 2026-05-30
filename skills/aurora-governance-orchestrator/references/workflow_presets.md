# Workflow Presets

Use these presets to chain Aurora skills without rebuilding the routing decision each time.

## `promotion_preflight`
1. `aurora-skill-finder` when scope is unclear
2. `aurora-governance-orchestrator`
3. `aurora-canon-reconciler` only when a draft canon payload is part of the batch

Use when the goal is one promotion verdict with merged remediation.

## `repo_hardening`
1. `aurora-skill-finder`
2. `aurora-repo-stabilizer`
3. `aurora-script-governor`
4. `gh-fix-ci` or security skills when the repo work expands into CI/AppSec

Use when the request starts as repo reliability and script-surface reduction.

## `sim_to_brief`
1. `gumas-simulation-engine` or `aurora-quantum-forge-ops`
2. `aurora-narrative-tone-governor` when prose output needs governance
3. `aurora-exec-brief-pipeline`

Use when engine outputs must become leadership-readable narrative and summary artifacts.

## `selective_integration_gate`
1. `aurora-skill-finder`
2. `aurora-selective-integration`
3. specialist governors only for affected domains
4. `aurora-governance-orchestrator`
5. `aurora-canon-reconciler` only if the batch promotes into canon

Use when ingesting an external kit/archive into Aurora with rollback-ready decisions.

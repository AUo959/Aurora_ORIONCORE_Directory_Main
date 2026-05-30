# Stabilization Playbook

## Objective
Increase operational reliability of Aurora repositories by reducing script ambiguity and repairing critical execution paths first.

## Fix Order
1. Hook and commit-path blockers (`scripts/git_pre_commit_hook.py`, hook installers, validator entrypoints)
2. Validation integrity (`canonical_validator`, validation manager wiring, report path behavior)
3. Placeholder and mock behavior in "active" maintenance scripts
4. Duplicate script consolidation and deprecation markers

## Trust Matrix Rules
- `trusted`: validated by execution in current repo and no placeholder/hazard signals
- `candidate`: no immediate red flags, but not yet execution-verified
- `risky`: executes but has placeholder/mock/hazard patterns or contradictory behavior
- `stub/disabled`: empty or explicitly disabled

## Safe-Fix Rules
- Prefer minimal diffs over broad rewrites.
- Do not delete alternatives until one path is verified working.
- Keep one canonical script per job; mark others as deprecated clearly.
- Re-run local validations after each critical fix.

## Evidence Requirements
For each proposed fix include:
- file path
- concrete failing or risky pattern
- user impact
- minimal patch plan
- post-fix validation command

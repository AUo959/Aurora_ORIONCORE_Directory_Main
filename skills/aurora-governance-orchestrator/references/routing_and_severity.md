# Routing and Severity Model

## Domain execution order
1. `threadcore`
2. `zipwiz`
3. `script_governor`
4. `narrative_tone`
5. `repo_stabilizer`
6. `canon` (only when draft input is provided)

## Routing modes

### Full mode
- Run all enabled domains except `canon` and `narrative_tone`.
- Keep `narrative_tone` path-driven for now to avoid broad false blocks on legacy narrative corpus scans.

### Changed-paths mode
- Route by path heuristics:
  - Threadcore-like paths: `threadcore`, `checkpoint`, `continuity`, `beacon`, `delta`.
  - ZipWiz-like paths: `zipwiz`, `zipwizard`, `bundle.manifest`, `staging_manifest`, `zipcomm`.
  - Script/ops paths: `scripts/`, hooks, workflow paths -> `script_governor` + `repo_stabilizer`.
  - Narrative/tone paths: `narr`, `story`, `scene`, `recap`, `thread`, `tone`, `cadence`, `anti-flourish` -> `narrative_tone`.
  - Canon-like paths: `canon`, `entity`, `entities`, `worldbuilding`, `l1`, `l2`, `l3`.
- If no domains match, fall back to full mode and record fallback in routing metadata.

## Overlap policy
- If two or more governance families are implicated in the same routing decision, prefer `aurora-governance-orchestrator` over a specialist-only route.
- Prefer `aurora-script-governor` over `aurora-repo-stabilizer` when the evidence is about setup stubs, wrappers, branch cleanup, or script hazards.
- Prefer `aurora-repo-stabilizer` over `aurora-script-governor` when the evidence is about hooks, CI, workflows, or repo validation topology.
- Prefer `aurora-selective-integration` over `aurora-exec-brief-pipeline` for include/backup/reject triage or rollback capsule work.
- Prefer `aurora-exec-brief-pipeline` over `aurora-selective-integration` for leadership briefs, decision snapshots, or mixed-export reporting.

## Root rebasing policy
For hardcoded roots from specialist scanners:
1. Use configured absolute path when it exists.
2. Otherwise, if root includes `/Aurora_ORIONCORE_Directory_Main/`, extract suffix.
3. Rebuild as `<repo_root>/<suffix>`.
4. Mark `rebased=true` when rebuilt root resolves.
5. Emit `B_SCAN_ROOTS_UNRESOLVED` when all authoritative roots for a selected domain remain unresolved.

## Severity normalization

### Native domains
- `threadcore`, `zipwiz`, `narrative_tone`, and `canon` keep scanner-native severities.

### Script governor mapping
- `high -> BLOCK`
- `medium -> WARN`
- `low -> INFO`

### Repo stabilizer mapping
- zero-byte and risky surfaces -> `WARN`
- duplicate-family signals -> `INFO`
- never emit `BLOCK` in v1

## Blocking scope policy
- `authoritative`: can block promotion.
- `reference_only`: never blocks promotion in v1.
- `advisory`: informational or warning-only policy scope.
- `execution_health`: orchestration/runtime health findings.

## Verdict policy
1. Any blocking finding -> `BLOCKED`.
2. Else any warning -> `PROMOTE_WITH_REMEDIATION`.
3. Else -> `PROMOTE`.

## Shared findings schema
All governor domains should emit or normalize to the shared schema in `finding_schema.md`:
- `severity`
- `domain`
- `rule_id`
- `file`
- `source_path`
- `message`
- `rationale`
- `evidence`
- `remediation`

### Confidence policy
- `low`: execution-health block or authoritative domain execution failure.
- `medium`: rebased roots or unexpected zero-artifact scans.
- `high`: all selected domains execute cleanly without execution-health findings.

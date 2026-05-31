# Workspace Coherence Checklist

This checklist is for root-control-plane coherence checks while Codex and
Claude Code may both be active. It is advisory unless a workflow explicitly
marks one of these checks as a gate.

## Scope Rules

- Treat this repo as the root control plane.
- Do not mutate nested repos unless the user names the nested repo in the
  current request.
- Prefer path-scoped checks when another platform has an active claim.
- Treat generated control surfaces as generated. Regenerate them instead of
  hand-editing them unless the task is explicitly about the generator.
- Keep draft, staged, generated, canonical, and superseded states explicit.

## Start Checks

| Surface | Command | Healthy signal | Conflict signal |
| --- | --- | --- | --- |
| Shared handoff state | `python3 -m json.tool catalog/session_state.json` | Valid JSON and current task is understood | Suspended task or stale active task with no next step |
| Active claims | `python3 tools/session_claim.py list --json` | Active claims explain current work | Unknown active claim on the same path |
| Path claim check | `python3 tools/session_claim.py check --repo root --paths <paths> --mutation-posture editing --json` | `status: clear` for intended paths | `status: blocked` with overlapping active claim |
| Worktree status | `git status --short --branch --untracked-files=all` | Dirty paths are expected and claimed | Dirty paths outside the active task scope |
| Recent commits | `git log --oneline -5` | New commits match expected handoff state | Unexpected commits since `session_state.json` |
| Worktrees | `git worktree list` | No branch/path collision | Another worktree owns the intended branch |

## Root Health Checks

| Surface | Command | Healthy signal | Notes |
| --- | --- | --- | --- |
| Workspace verification | `python3 tools/workspace_verify.py` | Passes with zero blocking findings | Use `--persist-report` only when updating generated reports intentionally |
| Dev toolkit | `make devkit-check` | Reports ready with no required installs | System installs require explicit approval |
| Mission Control | `make mission-control` | No source errors and actionable inbox items only | Source errors usually indicate an upstream scanner failure |
| Recommendations | `make recommendations` | Ranked advisory actions with no failed sources | Recommendations are read-only and do not promote canon |
| Integration gate | `make integration-gate` | Passes or reports only expected active-claim blocks | Gate should distinguish read-only checks from mutating checks |
| Skills sync | `make skills-check` | No project-owned skill drift | Use `make skills-install` only after reviewing the drift |
| Recovery index | `python3 tools/workspace_recovery_index.py --summary` | Completes without traceback | Candidates remain pending until a promotion gate |

## Parallel-Work Rules

- Codex may continue on unclaimed docs, reports, and catalog handoff artifacts
  while Claude Code edits source, tests, skills, or lint surfaces.
- Do not stage or commit another platform's dirty files by implication.
- If a root-wide check fails only because another platform has an active
  editing claim, record it as a coordination constraint rather than a content
  defect.
- If a scanner fails inside the other platform's claimed path, report the
  exact command and error, then leave the fix to that platform unless the user
  redirects the task.

## Exit Checks

- Re-run the path-scoped claim check for the files changed in the session.
- Re-run the cheapest relevant validation command.
- If work remains in progress, update the handoff state with a concrete next
  step before ending the session.
- Push only the repo explicitly targeted by the user, and only after verifying
  staged files exclude unrelated platform work.

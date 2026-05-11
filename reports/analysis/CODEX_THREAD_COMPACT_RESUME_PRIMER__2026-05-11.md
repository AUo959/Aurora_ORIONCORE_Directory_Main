# Codex Thread Compact Resume Primer

Generated: 2026-05-11T01:10:58Z

Purpose: reduce loss of working state when Codex automatic thread compacting or
remote compact calls disconnect. This does not disable compaction. It gives the
next agent a bounded, durable restart packet inside the Aurora root control
plane.

## First Read After Reconnect

Read these files before resuming work:

1. `AGENTS.md`
2. `README.md`
3. `catalog/workspace_manifest.yaml`
4. `catalog/repo_registry.yaml`
5. `reports/analysis/CODEX_THREAD_COMPACT_RESUME_PRIMER__2026-05-11.md`

Then run:

```bash
git status --short --branch
python3 tools/workspace_verify.py
```

Use `catalog/repo_registry.yaml` before operating on nested repos. Do not infer
that a root task applies to nested repos.

## Current Root Baseline

- Workspace: `/Users/travisstreets/Library/Mobile Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main`
- Scope: root control-plane repo only unless the user names a nested repo.
- Branch at primer time: `main`
- Upstream at primer time: `origin/main`
- Root sync state at primer time: dirty, with generated control-surface updates
  and untracked receipts/tooling already present.
- Last verifier baseline: `python3 tools/workspace_verify.py` passed with zero
  findings on 2026-05-10T14:48:19Z.
- Strong verifier baseline:
  `python3 tools/workspace_verify.py --check-determinism --exercise-relocation`
  passed with zero findings on 2026-05-10T14:49:55Z.
- Health-check caveat: `workspace_health_check.py --json` reported
  `DEGRADED (1 issue)` only because optional `jsonschema` was missing; tests,
  YAML, JSON, verifier, and sync audit were otherwise green.

## Resume Prompt

If a thread disconnects, start the next thread with:

```text
Please resume from the Aurora root compact primer:
reports/analysis/CODEX_THREAD_COMPACT_RESUME_PRIMER__2026-05-11.md
Read AGENTS.md, README.md, catalog/workspace_manifest.yaml, and
catalog/repo_registry.yaml first. Then inspect git status and continue from the
latest durable receipt without redoing unrelated work.
```

## Local Recovery Evidence

If the UI appears to lose the thread, inspect local Codex state before asking
the user to restate context:

- `~/.codex/sessions/...`
- `~/.codex/.codex-global-state.json`
- `~/Library/Logs/com.openai.codex/...`

Prior local evidence showed that a thread can remain recoverable even when the
remote compact request fails. Successful `thread/read`, `thread/resume`, or
`maybe_resume_success` log entries are stronger evidence than a stale failed
turn.

## Working Rules For Long Runs

- Keep updates concise and write a receipt after each meaningful milestone.
- Before a high-risk or long-running step, write the intended next command and
  expected output artifact into a root receipt.
- Do not leave required shell sessions running at turn end.
- Prefer generated control-surface refreshes over hand edits for:
  `catalog/workspace_manifest.yaml`, `catalog/repo_registry.yaml`,
  `docs/workspace-map.md`, `catalog/relocation_plan.json`, and
  `reports/analysis/workspace_verify_latest.json`.
- Treat this primer as a restart aid, not canonical project state.

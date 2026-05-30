# Aurora Automation Matrix Receipt - 2026-05-02

## Scope

This receipt records the machine-local Codex automation matrix configured from
the Aurora root control plane on 2026-05-02.

The root repo remains the control plane only. Nested repos remain separate Git
boundaries and are validated through `catalog/repo_registry.yaml`.

## Active Automations

| Automation ID | Cadence | Model | Purpose |
| --- | --- | --- | --- |
| `weekly-skill-audit` | Monday 09:00 | `gpt-5.5`, high reasoning | Audit installed Aurora skills, routing catalogs, metadata, scripts, and governance overlap. |
| `aurora-multi-repo-git-health` | Tuesday and Friday 09:30 | `gpt-5.5`, medium reasoning | Use the root repo registry to scan configured repos for status, divergence, stale branches, and maintenance-entrypoint failures. |
| `aurora-root-workspace-health` | Wednesday 09:00 | `gpt-5.5`, medium reasoning | Run root control-plane scan, move-plan, and verifier checks with generated-surface boundaries explicit. |
| `qgia-closed-loop-validation` | Thursday 09:00 | `gpt-5.5`, medium reasoning | Validate QGIA corpus/spine closed-loop contracts, tests, and repo-boundary status. |
| `archive-entropy-guard` | Saturday 12:00 | `gpt-5.5`, medium reasoning | Scan the canonical workspace archive zones for duplicate and oversized artifacts and return safe quarantine guidance. |

## Guardrails

- The matrix does not promote draft, recovered, staged, generated, or intake
  material into canon.
- The multi-repo health automation reads repo scope from
  `catalog/repo_registry.yaml`; it does not infer nested repo targets from root
  prose.
- Archive entropy scans must check the canonical workspace path, not only a
  Codex worktree mirror.
- QGIA validation keeps `qgia-knowledge-library-main` as corpus and
  `qgia-knowledge-spine-main` as methodology/backbone.
- Automations should report environment limitations, such as denied fetches or
  sandbox write boundaries, separately from verified repo defects.

## Local Automation State

The automation definitions live under:

`/Users/travisstreets/.codex/automations/`

That directory is machine-local Codex state and is not synced by publishing the
root repo. This receipt is the root-control record of the configured matrix.

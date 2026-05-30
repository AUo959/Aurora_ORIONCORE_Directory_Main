# Root Unfinished Work Routing Receipt

- Generated: `2026-04-24`
- Scope: unresolved recoverable items remaining after the April 23 scoped finish pass
- Basis:
  - `docs/workspace-map.md` planned move candidates
  - `catalog/workspace_manifest.yaml` `planned_move` entries
  - `git status --short --branch` in the root repo and the scoped CloudBank repo
- Resolved and omitted:
  - root QGIA closed-loop metadata refresh
  - `qgia-knowledge-spine-main` bootstrap adoption
  - CloudBank narrative-validation engine implementation

## Routing Labels

- `routed_only`: recoverable material that should be routed into intake or review, not promoted.
- `staged`: recoverable repo-local work bundle awaiting its own scoped review before any commit or install.
- `generated`: recoverable generated output that should remain evidence-only unless a future thread explicitly requests a durable receipt.

| Recoverable item | Current location | Routing label | Next concrete action | Promotion gate |
| --- | --- | --- | --- | --- |
| Aurora Sim Architecture intake collection | `Aurora_Sim_Architecture` | `routed_only` | Keep as the existing `wave4_root_intake_cleanup_initial` planned move candidate and review contents before any move; if still wanted, route to `intake/Aurora_Sim_Architecture`. | Do not promote without separate canonical approval. |
| QGIA space navigation guide duplicate | `QGIA_SPACE_NAVAGATION_GUIDE.md` | `routed_only` | Treat as intake-only duplicate material and either route to `intake/QGIA_SPACE_NAVAGATION_GUIDE.md` under the existing batch or delete only after duplicate review against `docs/QGIA_SPACE_NAVIGATION_GUIDE.md`. | Do not promote without separate canonical approval. |
| Root agent-dispatcher skill bundle | `skills/agent-dispatcher/` plus `tests/test_agent_dispatcher_skill.py` | `staged` | Open a separate scoped root-tooling review, decide whether this skill belongs in the root control plane, and only then stage and commit it or discard it locally. | Do not promote in this thread. Canonical approval is not yet applicable; separate scoped review is required first. |
| CloudBank skill-finder exploratory output | `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/workflow_output/skill_finder/` | `generated` | Leave untracked by default; only copy into a receipt or report path if a future thread explicitly needs this output as evidence. | Do not promote. Generated exploratory output is not a canonical surface. |

## Notes

- `QGIA_SPACE_NAVAGATION_GUIDE.md` and `docs/QGIA_SPACE_NAVIGATION_GUIDE.md` currently compare equal by content, so the top-level file should stay intake-routed rather than being treated as a second canonical document.
- This receipt is intentionally root-control-plane oriented. Nested repo source files completed and pushed in the April 23 thread are not listed as unfinished work.

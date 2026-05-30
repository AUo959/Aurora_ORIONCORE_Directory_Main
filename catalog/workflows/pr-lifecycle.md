# Workflow: PR Lifecycle

**ID:** `pr-lifecycle`
**Platforms:** Claude Code · Codex (either can hold any step)
**Trigger:** Any time a feature branch needs to go from implementation to merged PR
**Handoff mechanism:** `catalog/session_state.json` → `active_task` + `task_queue`

---

## Steps

### 1 · Implement
- Create branch (follow naming convention in AGENTS.md: `codex/` or `feat/` prefix)
- Make changes, run tests locally (`make test` / `pytest`)
- Run linter: `ruff check .` and pre-commit if touching Python
- Commit with conventional message

**Suspend signal:** Set `active_task.status = "suspended"`, `next_step = "open-pr"`, include branch name and last commit SHA.

---

### 2 · Open PR
- `gh pr create --draft` initially
- Include summary of changes and test plan in PR body
- Record PR number in `active_task.pr_number`

**Codex:** Use `gitwiz-github-manager` skill for PR packet drafting.
**Claude Code:** Use `gh pr create` directly.

**Suspend signal:** `next_step = "await-review"`, `pr_url` set.

---

### 3 · Await + Address Review
- Poll `gh pr view <number> --json reviewDecision,comments`
- **If Codex:** Use `gh-address-comments` skill — reads open review comments and proposes fixes
- **If Claude Code:** Read comments via `gh pr view --comments`, implement fixes directly in files, commit

**Suspend signal:** `next_step = "merge-ready"` once all review threads resolved and CI green.

---

### 4 · Merge
- Verify CI: `gh pr checks <number>`
- Merge: `gh pr merge <number> --squash --delete-branch`
- Update `active_task.status = "complete"`, move to `completed_tasks` in session state

---

## Suspend Point Template

```json
{
  "id": "pr-lifecycle-<branch-slug>",
  "workflow": "pr-lifecycle",
  "status": "suspended",
  "created_by": "<platform>",
  "last_updated_by": "<platform>",
  "last_updated": "<iso-timestamp>",
  "branch": "<branch-name>",
  "pr_number": null,
  "pr_url": null,
  "last_commit": "<sha>",
  "completed_steps": [],
  "next_step": "implement | open-pr | await-review | merge-ready | complete",
  "next_step_detail": "<plain-English description of exactly what to do next>",
  "context_files": ["AGENTS.md", "catalog/session_state.json"],
  "skills_for_codex": ["gitwiz-github-manager", "gh-address-comments"],
  "notes": ""
}
```

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

**Interrupted-session signal:** Use `suspend-active --next-step "open the PR" --resume-by <timestamp>` only when the continuation is short and immediately executable. Local implementation and PR preparation are not owner-gated.

---

### 2 · Open PR
- `gh pr create --draft` initially
- Include summary of changes and test plan in PR body
- Record PR number in `active_task.pr_number`

**Codex:** Use `gitwiz-github-manager` skill for PR packet drafting.
**Claude Code:** Use `gh pr create` directly.

**Wait signal:** Move the task to `waiting_on=external` with the PR URL as evidence, a review trigger, and `review_at`; this clears the active slot while review is genuinely external.

---

### 3 · Await + Address Review
- Poll `gh pr view <number> --json reviewDecision,comments`
- **If Codex:** Use `gh-address-comments` skill — reads open review comments and proposes fixes
- **If Claude Code:** Read comments via `gh pr view --comments`, implement fixes directly in files, commit

**Ready signal:** When all review threads are resolved and CI is green, return the item to `ready`. Request owner authorization only when the remaining consequential action is merge/publication and that authorization has not already been given.

---

### 4 · Merge
- Verify CI: `gh pr checks <number>`
- Merge: `gh pr merge <number> --squash --delete-branch`
- Run `complete-active --detail "PR merged and post-merge state verified."` so completion and active-slot clearing are atomic.

---

## Lifecycle record

```bash
python3 tools/session_state_io.py add-item pr-lifecycle-<branch-slug> \
  --description "Deliver <scope> through a verified PR." \
  --next-action "Implement and run the targeted validation." \
  --definition-of-done "PR is merged and post-merge state is verified." \
  --review-at <iso-timestamp>
python3 tools/session_state_io.py start-item pr-lifecycle-<branch-slug>
```

Branch, PR URL, last commit, findings, and validation evidence are optional
record fields or referenced receipts. The lifecycle-required fields remain
governed by schema v3.

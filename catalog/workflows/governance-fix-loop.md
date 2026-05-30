# Workflow: Governance → Fix Loop

**ID:** `governance-fix-loop`
**Platforms:** Claude Code · Codex (either can hold any step)
**Trigger:** Any time Aurora governance scanning is needed and findings require code/file fixes
**Handoff mechanism:** `catalog/session_state.json` → `active_task` + `task_queue`

---

## Steps

### 1 · Run Governance Scan
- **Codex (preferred — has the skills):** Use `aurora-governance-orchestrator` skill
  ```
  python3 /path/to/skills/aurora-governance-orchestrator/scripts/orchestrate_governance.py \
    --repo <repo-path> \
    --out-json /tmp/aurora_governance.json \
    --out-md /tmp/aurora_governance.md
  ```
- **Claude Code (fallback):** Run individual scanners via `make` targets or Codacy CLI
  ```
  codacy-analysis analyze . --tool <tool> -f json -o /tmp/findings.json
  ```

Write output to `reports/analysis/` and reference the path in the suspend point.

**Suspend signal:** `next_step = "triage-findings"`, `findings_path` set.

---

### 2 · Triage Findings
- Read the governance report
- Classify each finding: `fix-now` | `accept` | `defer`
- Record classifications in the suspend point `findings` array
- **Verdict:** If all findings are `accept` or `defer` → skip to step 4. If any are `fix-now` → continue to step 3.

**Suspend signal:** `next_step = "apply-fixes"`, findings array populated.

---

### 3 · Apply Fixes
- **Claude Code (preferred — precise file editing, Codacy verification):**
  - Work through `fix-now` findings one at a time
  - For each: read file, apply fix, verify with linter/test, note in findings array
  - Commit: `fix(<scope>): resolve <N> governance findings — <pattern-ids>`
- **Codex (fallback):** Apply fixes in the governance skill's remediation queue, then commit

**Suspend signal:** `next_step = "verify"`, each `fix-now` item updated with `fixed_in_commit`.

---

### 4 · Verify Clean
- Re-run the scan: confirm finding count dropped
- **Claude Code:** `codacy-analysis analyze . --tool <tool>` or `make integration-gate`
- **Codex:** Re-run governance skill in verify mode

**Suspend signal:** `next_step = "complete"` if clean; `next_step = "apply-fixes"` if residual findings remain.

---

### 5 · Complete
- Push fixes to origin
- Update `active_task.status = "complete"`, move to `completed_tasks`
- Optionally open PR for the fix batch (use `pr-lifecycle` workflow)

---

## Suspend Point Template

```json
{
  "id": "governance-fix-<repo>-<date>",
  "workflow": "governance-fix-loop",
  "status": "suspended",
  "created_by": "<platform>",
  "last_updated_by": "<platform>",
  "last_updated": "<iso-timestamp>",
  "target_repo": "<repo-name>",
  "target_repo_path": "<relative-path>",
  "findings_path": "reports/analysis/<governance-report>.json",
  "verdict": null,
  "findings": [
    {
      "id": "<finding-id>",
      "pattern": "<pattern-id>",
      "file": "<file>",
      "line": 0,
      "severity": "High | Warning | Info",
      "disposition": "fix-now | accept | defer",
      "fixed_in_commit": null,
      "notes": ""
    }
  ],
  "completed_steps": [],
  "next_step": "run-scan | triage-findings | apply-fixes | verify | complete",
  "next_step_detail": "<plain-English description of exactly what to do next>",
  "context_files": ["AGENTS.md", "catalog/session_state.json"],
  "skills_for_codex": ["aurora-governance-orchestrator", "aurora-script-governor", "aurora-repo-stabilizer"],
  "notes": ""
}
```

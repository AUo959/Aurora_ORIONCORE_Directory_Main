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

**Interrupted-session signal:** Suspend only if the next scan or triage action is immediately executable and has a near-term `resume_by`. Otherwise keep the item `ready` with the findings path as evidence.

---

### 2 · Triage Findings
- Read the governance report
- Classify each finding: `fix-now` | `accept` | `defer`
- Record classifications in an evidence receipt referenced by the lifecycle item
- **Verdict:** If all findings are `accept` or `defer` → skip to step 4. If any are `fix-now` → continue to step 3.

Routine `fix-now` work remains `ready`; governance findings do not become owner-gated merely because they need review. Use an owner decision only for a concrete consequential disposition that remains after investigation.

---

### 3 · Apply Fixes
- **Claude Code (preferred — precise file editing, Codacy verification):**
  - Work through `fix-now` findings one at a time
  - For each: read file, apply fix, verify with linter/test, note in findings array
  - Commit: `fix(<scope>): resolve <N> governance findings — <pattern-ids>`
- **Codex (fallback):** Apply fixes in the governance skill's remediation queue, then commit

**Interrupted-session signal:** If interrupted, suspend with the exact remaining verification command and a near-term `resume_by`.

---

### 4 · Verify Clean
- Re-run the scan: confirm finding count dropped
- **Claude Code:** `codacy-analysis analyze . --tool <tool>` or `make integration-gate`
- **Codex:** Re-run governance skill in verify mode

If clean, complete atomically. If findings remain actionable, keep the item active or return it to `ready` with an updated next action and review date.

---

### 5 · Complete
- Push fixes to origin
- Run `complete-active --detail "Governance findings resolved and clean scan verified."`
- Optionally open PR for the fix batch (use `pr-lifecycle` workflow)

---

## Lifecycle record

```bash
python3 tools/session_state_io.py add-item governance-fix-<repo>-<date> \
  --repo <repo-name> \
  --description "Triage and resolve the bounded governance finding set." \
  --next-action "Run the scan and record the evidence path." \
  --definition-of-done "Fix-now findings are resolved and verification is clean." \
  --review-at <iso-timestamp>
python3 tools/session_state_io.py start-item governance-fix-<repo>-<date>
```

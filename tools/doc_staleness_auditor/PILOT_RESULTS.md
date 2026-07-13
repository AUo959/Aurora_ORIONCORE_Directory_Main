# Doc Staleness Auditor — Pilot Results

Real (non-mocked) `scan` + `verify` runs of `tools/doc_staleness_auditor` against
both pilot repos at their live HEADs. Every finding below was re-checked by hand
against the cited ground truth.

| repo | HEAD | docs | claims | CONFIRMED | STALE | UNVERIFIABLE |
|---|---|---|---|---|---|---|
| Aurora_ORIONCORE_Directory_Main | `b3244113ad77` | 300 | 3882 | 1322 | 437 | 2123 |
| aurora-cloudbank-symbolic | `5dd18d364070` | 703 | 7110 | 4320 | 516 | 2274 |

Verification is fast (Aurora ~1s, cloudbank ~3s incl. building the AST symbol
index). No network is used for verification — all ground truth is read from the
target repo at HEAD.

## Evidence policy in force

`CONFIRMED` was only ever reached via a primary source — `git ls-tree` state,
file content read + `ast`-parsed, or a config/version file value. Doc-to-doc
corroboration and bare filename existence are never sufficient. Claims with no
machine-checkable ground truth are `UNVERIFIABLE_BY_AUTOMATION` (the large bucket
above is mostly narrative prose and unscoped counts — correctly *not* confirmed).

---

## aurora-cloudbank-symbolic — headline real findings

### STALE — CHANGELOG headline vs VERSION file
- **Claim:** `CHANGELOG.md:14` — "Aurora **v2.2.5** formalizes …" (latest released heading `## [2.2.5]`)
- **Observed:** `VERSION` file first line = `2.1.0`
- **Evidence:** `[config_file_read]` CHANGELOG latest release `2.2.5` vs `VERSION` → `2.1.0` (files: `VERSION`, `CHANGELOG.md` @ `5dd18d364070`)
- **Hand-check:** `cat VERSION` → `2.1.0`; changelog top release is `2.2.5`. Genuine drift.

### STALE — documented Python floor vs pinned runtime
- **Claim:** `.github/copilot-instructions.md:270` — "Target **Python 3.11+** (configured in pyproject.toml)"
- **Observed:** `runtime.txt` = `python-3.12.0`
- **Evidence:** `[config_file_read]` python floor `3.11` vs `runtime.txt` → `3.12`
- **Hand-check:** `cat runtime.txt` → `python-3.12.0`. The stated floor lags the pinned runtime.

### CONFIRMED — version matches VERSION
- **Claim:** `tools/command_chain/COMPREHENSIVE_SYNC_321.md:284` — version `2.1.0` per VERSION file
- **Evidence:** `[config_file_read]` read first line of `VERSION` at HEAD → `2.1.0`

### CONFIRMED — symbols via AST
- `ImprovementPattern.detect` → `modules/data_guardian/detection_rules.py:158` `[python_ast_parse]`
  (hand-check: line 158 is `def detect(self, text: str, …)`)
- `export_status` → `src/aurora/continuity/halo_pas_controller.py:257` `[python_ast_parse]`
- `analyze_staffing_needs` → `modules/hr_system/api/hr_routes.py:77` `[python_ast_parse]`

### STALE — broken intra-repo path references (sample of 516)
- `.aurora/SESSION_COMPLETION_REPORT.md:67` → `docs/SUBROUTINE_SUITE_COMPLETE.md` — not in tree
- `.aurora/SUBROUTINE_INTEGRATION_STATUS.md:112` → `modules/opal2/api/routes.py` — not in tree
- `.aurora/HR_SYSTEM_VALIDATION.md:300` → `modules/hr_system/data/canonical_characters.py` — not in tree
  (each: `[git_tree_lookup]` first segment is a real top-level dir, target absent @ `5dd18d364070`)

---

## Aurora_ORIONCORE_Directory_Main — headline real findings

### CONFIRMED — session-state API via AST
- **Claim:** `CLAUDE.md:56` references the `load()` / `save()` session-state API
- **Evidence:** `[python_ast_parse]` `load` defined at `tools/session_state_io.py:76`; `save` at `:84`
- **Hand-check:** both `def load` / `def save` present in that file. Confirmed against real source, not file existence.

### CONFIRMED — path against git tree
- **Claim:** `CLAUDE.md:11` → `docs/WORKSPACE_MIGRATION_2026-07-01.md`
- **Evidence:** `[git_tree_lookup]` path present in git tree at HEAD @ `b3244113ad77`

### STALE — Charter links a philosophy set that does not exist
- **Claim:** `docs/AURORA__CHARTER__MORAL_ARCHITECTURE__v1.0__2026-06-11.md:470-476` link
  `docs/philosophy/PHILOSOPHY.md`, `…/01_EPISTEMIC_FOUNDATION.md`, `…/04_ETHICS_PROTOCOL.md`, etc.
- **Observed:** `<not found>` — no `docs/philosophy/` directory in the tree
- **Evidence:** `[git_tree_lookup]` no tracked path in git tree at HEAD; first segment `docs` is a real top-level dir → broken intra-repo reference @ `b3244113ad77`
- **Hand-check:** `git ls-tree -r HEAD | grep docs/philosophy` → empty. Genuine broken links.

### STALE — Peer-review protocol references unbuilt artifacts
- `docs/AURORA_PEER_REVIEW_PROTOCOL_v1.md` references `tools/peer_review.py`,
  `catalog/schemas/peer_review_receipt.schema.json`, `catalog/review_ledger.json`,
  `warrant-lens/pipeline.py` — none present at HEAD (`[git_tree_lookup]`).

---

## Governance-mode dry run (CanonRec, `canon_promotion_queue`)

`execute --repo CanonRec` (dry run) routes the 437 Aurora STALE findings into the
Drift Containment Protocol instead of a PR, producing artifacts that match the
real CanonRec formats (read from `AUo959/CanonRec` via `gh api`):

- **Quarantine draft:** `canon/_quarantine/drift/DRIFT_DRAFT__doc_audit__2026-07-13.md`
- **`DRIFT_LOG.md` append** (matches existing `## Drift Entry — <date>` block with
  `- **Source:** / - **Type:** / - **Entities affected:** / - **Description:** / - **Resolution:**`)
- **Promotion-queue append:** a proposal bullet pointing at the quarantine draft,
  for canon-owner decision — never a direct edit to canon content, never a PR.

## How to reproduce

```bash
cd tools
python3 -m doc_staleness_auditor scan   --repo <target> --out claims.json
python3 -m doc_staleness_auditor verify --claims claims.json --repo <target> \
        --out findings.json --md findings.md
python3 -m doc_staleness_auditor plan   --findings findings.json
python3 -m doc_staleness_auditor execute --findings findings.json \
        --repo <name-in-repos.yaml> --repo-root <target>   # dry run; add --apply to write
```

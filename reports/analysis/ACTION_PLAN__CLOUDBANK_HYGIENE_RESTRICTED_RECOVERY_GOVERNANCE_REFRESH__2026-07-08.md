# Action Plan — CloudBank Branch Hygiene, Restricted Recovery Triage, Governance Refresh

- **Created:** 2026-07-08
- **Source:** `reports/state_briefs/executive_brief__2026-07-08.md`, Top Risks #2, #3, #4
- **Intended picker-up:** any Codex or Claude Code session with root + CloudBank repo write access. Advisory only until executed — no commands in this doc have been run.
- **Handle:** `AP-20260708-cloudbank-restricted-governance`
- **Related open items this plan does NOT replace:** `roadmap-1.1` (CloudBank CI sprawl), `roadmap-0.5` (CanonRec purpose decision), `ga-ethics-hub-integration` — those stay in `catalog/session_state.json → pending_for_next_session` unchanged.

**How to claim this:** run `python3 tools/session_claim.py check --repo root --paths .` first (root-wide claim check), then follow `docs/SESSION_CLAIMS_WORKFLOW_v1.md` before touching CloudBank or the recovery candidates. Record progress in `catalog/session_state.json` as you go — partial completion should update `pending_for_next_session`, not silently disappear.

---

## Part 1 — CloudBank branch hygiene (Top Risk #2)

### Problem statement

`GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main` carries one dirty feature branch and five stranded/unpublished branches. Source: `catalog/session_state.json → publication_debt` (checked 2026-07-06T21:04Z) plus a live `git status` re-check on 2026-07-08. None of this is new work risk (nothing is uncommitted-and-untracked-only) — it's a **publication backlog**: work exists, is committed or stageable, but hasn't been pushed/PR'd/decided.

### 1.1 — Working branch: `codex/l2-scenario-seed-simulation-initializer`

Current state (live, 2026-07-08): 11 modified, 3 untracked, no upstream configured, last commit `1eedd38f` (2026-06-19, 19 days old).

| File | Change type |
|---|---|
| `.env_status.json` | modified |
| `Dockerfile_aurora_gui_cloudhub` | modified |
| `README.md` | modified |
| `api/aurora_gui_cloudhub_fastapi.py` | modified |
| `docker-compose.yml` | modified |
| `scripts/apply_security_fixes.sh` | modified |
| `scripts/deployment/launch-demo.sh` | modified |
| `static/js/aurora-security.js` | modified |
| `static/js/synergy-dashboard.js` | modified |
| `static/quantum-vsa-demo.html` | modified |
| `static/synergy-dashboard.html` | modified |
| `Dockerfile_aurora_gui_cloudhub.dockerignore` | untracked |
| `static/aurora-simulation-console.html` | untracked |
| `tests/test_cloudhub_console_routes.py` | untracked |
| `weekly_schedule.json.pre-icloud-sync-20260701.bak` | untracked — **migration artifact, almost certainly safe to delete rather than commit; confirm it's not a live file before removing** |

**Steps:**
1. `cd GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`
2. Confirm this repo's own devkit signal first: `.env_status.json` is flagged stale by `aurora_devkit`. Regenerate it per that repo's own setup script before validating anything else here (see Part 3 note on the same finding).
3. `git diff` each modified file to confirm the changes match the known scope (scenario-seed initializer adapter + security/demo console follow-on work — per `pending_for_next_session` item `ga-ethics-hub-integration`, this branch is explicitly called out as having "uncommitted auth-middleware work," so do not casually discard).
4. Delete the `.pre-icloud-sync-20260701.bak` file if `git log --all --full-history -- weekly_schedule.json` shows the live `weekly_schedule.json` is already tracked and current (it's a migration-era backup, not source).
5. Stage and commit in logical groups rather than one giant commit — suggested split: (a) `Dockerfile`/`docker-compose.yml`/`.dockerignore` as an infra commit, (b) `api/`, `static/`, `tests/` as a feature commit continuing the scenario-seed initializer work, (c) `scripts/apply_security_fixes.sh` + `scripts/deployment/launch-demo.sh` + `static/js/aurora-security.js` as a security-hardening commit.
6. `git push -u origin codex/l2-scenario-seed-simulation-initializer`
7. `gh pr create --fill` (or open manually) once pushed. Reference `pending_for_next_session` item `ga-ethics-hub-integration` in the PR description since it's gated on this branch going clean.
8. Update `catalog/session_state.json → publication_debt` to remove this entry once the PR is open (or re-run whatever tool generates `publication_debt` if one exists; otherwise hand-edit per the schema already in the file).

### 1.2 — Five stranded/unpublished branches

All five are **pushed to origin already** (per `publication_debt`) except where noted — this is a PR-or-retire decision, not a data-loss risk.

| Branch | State | Remediation command |
|---|---|---|
| `codex/cloudbank-issue-1015-salvage` | pushed, 3 commits ahead, no PR | `gh pr create --head codex/cloudbank-issue-1015-salvage` (or retire deliberately with `git push origin --delete codex/cloudbank-issue-1015-salvage` if superseded) |
| `codex/cloudbank-issue-1020-mesh-router-contract` | pushed, 1 commit ahead, no PR | `gh pr create --head codex/cloudbank-issue-1020-mesh-router-contract` |
| `codex/cloudbank-issue-1070-ethics-engine` | pushed, 1 commit ahead, no PR | `gh pr create --head codex/cloudbank-issue-1070-ethics-engine` — **check for overlap with `ga-ethics-hub-integration` before opening; may be the same work-in-progress under two names** |
| `codex/cloudbank-pat-terminal-compat-2026-06-16` | pushed, 1 commit ahead, no PR | `gh pr create --head codex/cloudbank-pat-terminal-compat-2026-06-16` |
| `codex/cloudbank-salvage-p3-forge-policy-2026-06-15` | pushed, 1 commit ahead, no PR | `gh pr create --head codex/cloudbank-salvage-p3-forge-policy-2026-06-15` |

**For each branch, before opening a PR:**
1. `git log main..<branch> --oneline` to see exactly what's ahead.
2. `git log main..<branch> -p | head -100` (or a diff review) to confirm it's still relevant and doesn't conflict with work already merged on `main` since the branch was cut.
3. If the branch is superseded or abandoned, retire it explicitly (`git push origin --delete <branch>` plus a one-line note in `catalog/session_state.json` recording the retirement decision and reason) rather than leaving it silently stranded for another cycle.
4. If it's still good, open the PR and link it from `pending_for_next_session` / `publication_debt` so the next brief sees it as `in_review` rather than `stranded`.

### 1.3 — Root's own unpublished branch (adjacent finding, same category)

`codex/charforge-capsule-implementation-2026-06-14` on the **root** repo — pushed, 1 commit ahead, no PR. Same treatment: `gh pr create --head codex/charforge-capsule-implementation-2026-06-14` or retire.

---

## Part 2 — Restricted recovery candidate triage (Top Risk #3)

### Problem statement

`reports/analysis/workspace_recovery_index_latest.json` (generated 2026-05-31, now 38 days stale) flags **36 files** with a `secret_or_key_material` signal. This signal is a **heuristic keyword/pattern match**, not a verified-secret scan — two of the 36 (`AGENTS.md`, `.gitleaks.toml`) are almost certainly false positives (a project doc and the gitleaks config itself naturally contain words like "key" and "secret" in a governance/config context). The other 34 are early recovered/archived work of unknown provenance and need an actual look, not just a re-run of the same heuristic.

This has been open, unchanged, since **2026-05-24** — at least six consecutive weekly briefs.

### 2.1 — Triage procedure

1. Run `python3 tools/workspace_recovery_index.py --summary` to confirm the count is still 36 and nothing has silently changed since 2026-05-31 (files can move during the ongoing archive/intake cleanup work referenced elsewhere in this session).
2. Work through the table in the Appendix below, file by file. For each: open it (`less`, not an editor that might auto-save), and classify as one of:
   - **`false_positive`** — heuristic matched on the word "key"/"secret"/etc. in a non-credential context. (Expected outcome for `AGENTS.md`, `.gitleaks.toml`, and likely several of the `.md`/`.json` narrative/index files given their `narrative_or_agent_logic` / `governance_or_control_plane` signal overlap.)
   - **`benign_test_fixture`** — a fake/example key used in tests or docs (e.g. `sk-test-...`, `AKIA` placeholder patterns). Confirm it's clearly non-functional before marking this.
   - **`live_credential_confirmed`** — an actual working credential. **Stop triage on this file immediately, do not paste the value anywhere else (including into `catalog/session_state.json` or this plan's completion notes), and escalate directly to Travis for rotation before doing anything else with the file.** This mirrors the handling already used for the 2026-05-30 OpenAI key and the still-open AWS IAM key item.
   - **`needs_owner_review`** — ambiguous; can't confirm live/dead without owner context (e.g. references to real infrastructure names, internal URLs, or account identifiers you can't independently verify).
3. Record every decision. There's no existing per-file triage log in the repo, so create one: `reports/analysis/restricted_recovery_triage__2026-07-08.json`, one entry per file with `{path, classification, reviewer, reviewed_at, notes}`. This becomes the evidence artifact for the next `workspace_recovery_index` run and for the audit trail.
4. For anything classified `false_positive` or `benign_test_fixture`: no further action needed beyond the log entry — these can stay where they are or be routed per their `target_repo_hint` during normal intake cleanup.
5. For anything `live_credential_confirmed`: escalate to Travis before any further git operations on that file. Do not commit, move, or delete it as a way of "handling" it — rotation happens first, in the actual credential provider, then the file can be cleaned.
6. For `needs_owner_review`: batch these into a short list for Travis rather than blocking the rest of the triage on them.

### 2.2 — Full candidate list (36), grouped by target-repo hint, ranked by value_score (recovery-index's own relevance ranking, not a risk ranking)

**Root-hinted (10 files) — most likely to be reviewed by the root/session-history maintainer:**

| Path | Source | Value score |
|---|---|---|
| `intake/text_conversation_PDK001.txt` | intake | 25 |
| `intake/TOBIAS_QIN_CHARACTER_PROFILE.md` | intake | 23 |
| `_staging/apple_notes_recovery__2026-03-16/L1/ord_drone_fleet_v1.0.py` | staged | 22 |
| `archives/unzipped/Unzipped Archives/Extra_Folders_Sort/GUMAS/080_Au_GUMAS_StAc/Please provide a comprehensive report outlining th 1.md` | archive | 20 |
| `archives/unzipped/Unzipped Archives/Extra_Folders_Sort/GUMAS/080_Au_GUMAS_StAc/Please provide a comprehensive report outlining th.md` | archive | 20 |
| `archives/unzipped/ZipWiz_Chamber_6_28/ZIPWIZ_Documents/ZIPWIZ Docs1/Please provide a comprehensive report outlining th.md` | archive | 20 |
| `intake/threadcore_symbiosis_delta_manifest.md` | intake | 20 |
| `archives/unzipped/ZipWiz_Chamber_6_28/aurora_bridge_output/relay_handshake.py` | archive | 19 — **filename suggests this is worth prioritizing; "handshake" scripts are a plausible home for real connection secrets** |
| `_staging/apple_notes_recovery__2026-03-16/L2/MULTILINGUAL_BEAMFORMING_ARRAY_SEED.md` | staged | 16 |
| `intake/text_CN_v4.txt`, `intake/text_CN_v5.txt`, `intake/text_CN_v6.txt` | intake | 16 each |
| `archives/unzipped/Unzipped Archives/Extra_Folders_Sort/GUMAS/Aurora_ORIONCORE_Directory_Main/Au_Archive_62_619/54726075.md` | archive | 15 |

**CloudBank-hinted (14 files) — review alongside Part 1 branch work, same repo:**

| Path | Source | Value score |
|---|---|---|
| `intake/Aurora_CloudBank_Review_R1_R10.md` | intake | 25 |
| `intake/aurora_scaffold_nexus_meta_narrative.md` | intake | 23 |
| `_staging/orion_ord_review_fix/package/tests/test_ord_policy_engine.py` | staged | 22 |
| `archives/unzipped/Unzipped Archives/Extra_Folders_Sort/GUMAS/080_Au_GUMAS_StAc/QuantumSymbolic_Index.txt` | archive | 22 |
| `archives/unzipped/ZipWiz_Chamber_6_28/ZIPWIZ_Documents/ZIPWIZ Docs1/QuantumSymbolic_Index.txt` | archive | 22 |
| `intake/text_25.txt` | intake | 22 |
| `AGENTS.md` | loose_root_intake | 20 — **expected false positive** |
| `_staging/orion_ord_review_fix/package/staging/legacy_pack/SOURCE__Recovered__ORD_DroneDispatch__v0.1__2026-03-10.py` | staged | 19 |
| `intake/text_16.txt` | intake | 19 |
| `intake/text_Opal2_Core.txt` | intake | 19 |
| `_staging/orion_ord_review_fix/zipwiz_fixed.md` | staged | 17 |
| `archives/unzipped/Complete Archive 4_19 copy/COMMANDCORE_FULL_INDEX_v1.json` | archive | 16 |
| `.gitleaks.toml` | loose_root_intake | 13 — **expected false positive (the secret-scanner's own config)** |

**qgia-knowledge-spine-hinted (9 files):**

| Path | Source | Value score |
|---|---|---|
| `SPEC__WARRANT_LENS__v1.md` | loose_root_intake | 21 |
| `archives/unzipped/Complete Archive 4_19 copy/formatted_galactic_union_memory_index.json` (+ 3 numbered duplicates) | archive | 13 each |
| `archives/unzipped/Complete Archive 4_19 copy/merged_galactic_union_memory_index.json` (+ 3 numbered duplicates) | archive | 13 each |

**qgia-knowledge-library-hinted (1 file):**

Not separately listed by name in the extracted output above — cross-check against the live `workspace_recovery_index.py --summary` re-run in step 2.1.1, since the routing counts (`candidates_by_target_repo_hint`) show 1 file routed here.

**review-required (1 file):**

| Path | Source | Value score |
|---|---|---|
| `intake/text_44.txt` | intake | 14 |

**Time-boxing note:** the last brief suggested a 30-minute review; given 36 files with several being multi-hundred-KB archive JSON dumps, budget closer to 90 minutes for a first honest pass, or split it — root+CloudBank hinted files (24 of 36) in one session, the remaining 12 (qgia + review-required) in a second.

---

## Part 3 — Governance artifact refresh (Top Risk #4)

### Problem statement

Four governance artifacts are 38 days stale (generated 2026-05-31): Mission Control, recovery index, recommendations, confidence audit. None reflect the migration, the CanonRec push, the QGIA catch-up, or the CloudBank branch drift documented in this brief. `aurora_devkit` also regressed from READY to WARN on 2026-07-04 (CloudBank's `.env_status.json` flagged stale relative to the check, likely just a timing artifact — see note below).

### 3.1 — Refresh order and commands

Run from repo root (`~/dev/Aurora_ORIONCORE_Directory_Main`). These are read-only/report-persisting only — none mutate source repos.

| Order | Command | Refreshes | Why this order |
|---|---|---|---|
| 1 | `make verify` | `workspace_verify_latest.json` | Cheapest, catches structural problems before the heavier reports run |
| 2 | `make devkit-report` | `aurora_devkit_latest.json` | Confirms toolchain is sane before trusting downstream reports; re-check the CloudBank `.env_status.json` WARN clears once Part 1 step 1.1.2 regenerates it |
| 3 | `make recovery-report` | `workspace_recovery_index_latest.json` | Run **after** Part 2 triage, not before — otherwise the refreshed report just reproduces the same 36-item finding with no new classification data attached |
| 4 | `make recommendations-report` | `aurora_recommendations_latest.json` | Depends on recovery index being current |
| 5 | `make mission-control-report` | `aurora_mission_control_latest.json` | Aggregates recovery + recommendations + git state; run last among the governance quartet |
| 6 | `make confidence-audit-report` | `aurora_confidence_audit_latest.json` | Independent scoring pass; can run anytime after step 1, included here to close out the full quartet in one session |
| 7 | `make kubernetes-readiness-report` | `aurora_kubernetes_readiness_latest.json` | Not part of the stale quartet but also worth refreshing since it's 12 days old and unchanged — confirms whether the 17 apply-blockers are still accurate before anyone spends time remediating them |
| 8 | `python3 skills/gitwiz-github-manager/scripts/gitwiz_sync_audit.py --repo all` (or equivalent all-repo flag — check script's `--help`; the 2026-07-03 run only covered `root`) | full gitwiz sync audit including nested repos | Last, since it should reflect the post-Part-1 branch state |

### 3.2 — Devkit WARN note

`aurora_devkit_latest.json` (2026-07-04T06:34:28Z) flags CloudBank's `.env_status.json` as stale. Live inspection shows `.env_status.json` was actually written at `2026-07-04T06:51:35Z` — **17 minutes after** the devkit check ran. This is very likely a same-day ordering artifact from the migration cleanup, not a real drift problem. Re-running `make devkit-report` (step 2 above) should clear it on its own; if it doesn't, that's a genuine finding worth a closer look rather than a re-run artifact.

### 3.3 — Post-refresh verification

After all eight steps: re-run `make mission-control` (summary, no persist) and confirm the operator-inbox item count and P1/P2 split reflect the resolved CanonRec/QGIA items from this week rather than the stale 2026-05-31 snapshot (7 items, 1 P1/6 P2). If the count doesn't change, the refresh didn't pick up new signal and needs investigation before being trusted for the next weekly brief.

---

## Completion checklist

- [ ] Part 1.1 — CloudBank working branch committed, pushed, PR opened
- [ ] Part 1.2 — 5 stranded branches each PR'd or explicitly retired
- [ ] Part 1.3 — root `codex/charforge-capsule-implementation-2026-06-14` PR'd or retired
- [ ] Part 2.1–2.2 — all 36 restricted candidates classified in `reports/analysis/restricted_recovery_triage__2026-07-08.json`
- [ ] Part 2 — any `live_credential_confirmed` escalated to Travis directly, not left in a report queue
- [ ] Part 3.1 — all 8 refresh commands run in order
- [ ] Part 3.3 — mission-control output spot-checked against expected week's changes
- [ ] `catalog/session_state.json → pending_for_next_session` updated to reflect what was closed vs. still open
- [ ] Next weekly brief (`executive_brief__2026-07-1x.md`) references this plan's completion status in its Week-over-Week Delta section

---

## Evidence sources

- `reports/state_briefs/executive_brief__2026-07-08.md` (this plan's parent brief)
- `catalog/session_state.json → publication_debt` (2026-07-06T21:04:27Z)
- `reports/analysis/workspace_recovery_index_latest.json` (2026-05-31T21:04:06Z)
- `Makefile` (governance report targets, lines 25–150)
- Live `git status`/`git log` against `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main` and root, 2026-07-08

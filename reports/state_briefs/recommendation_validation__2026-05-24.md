# Aurora / ORIONCORE — Recommendation Validation & Confidence Audit

- **Generated:** 2026-05-24
- **Subject:** All recommendations in [`development_roadmap__2026-05-24.md`](development_roadmap__2026-05-24.md) (18 workstreams) + [`executive_brief__2026-05-24.md`](executive_brief__2026-05-24.md) (recommended actions)
- **Framework:** Project confidence-audit rubric — `catalog/contracts/aurora_confidence_audit_contract_v1.json` / `catalog/schemas/aurora_confidence_record.schema.json`
- **Companion:** `recommendation_validation__2026-05-24.json` (machine-readable)

---

## Summary

Each recommendation was re-validated against live repo state, then scored on the project's confidence scale. **17 of 19 recommendations clear the 0.70 threshold; 2 fall below it and carry a user alert** — both because validation found the *stated premise* was overstated, not because the underlying action is wrong.

| Metric | Value |
|---|---|
| Recommendations validated | 19 |
| Confirmed as stated | 17 |
| Confirmed **with correction** | 2 (R3.3, R3.4) |
| Refuted | 0 |
| Mean confidence | 0.83 (`substantial`) |
| Range | 0.62 – 0.96 |
| Band: high (≥0.85) | 10 |
| Band: substantial (0.70–0.84) | 7 |
| Band: limited (0.50–0.69) | 2 |
| **`requires_user_alert` (score < 0.70)** | **2 — R3.3, R3.4** |

### Read first — the two flagged items

- **R3.4 (Dependency policy) — 0.62, alert.** The roadmap said to "add Dependabot/Renovate" and that "no unified dependency policy exists." **Correction:** `aurora-cloudbank-symbolic-main` *already has* `.github/dependabot.yml`. The accurate recommendation: **extend Dependabot to the 5 repos that lack it** (root, DuelSim, CanonRec, both QGIA repos) and lift CloudBank's config into a shared policy. The action survives; the premise was wrong.
- **R3.3 (Governance trend observability) — 0.66, alert.** The roadmap said the scanners emit "no history." **Correction:** partial history *does* exist — `reports/analysis/gitwiz/` keeps dated audits and `reports/automation/archive-entropy-guard/` keeps dated runs. The real gap is narrower: the **core scanners** (`workspace_verify`, `recovery_index`, `confidence_audit`, `mission_control`) overwrite single `*_latest.json` snapshots with no trend store. The recommendation should target *those four*, not "the scanners" broadly.

Neither correction changes the roadmap's phase ordering. Both are scoped down, not dropped.

---

## Scored recommendation register

Confidence bands (project rubric): `high` ≥0.85 · `substantial` ≥0.70 · `limited` ≥0.50 · `low` ≥0.30 · `unsupported` ≥0. Alert threshold 0.70.

| ID | Recommendation | Premise verdict | Evidence level | Confidence | Band | Alert |
|---|---|---|---|---|---|---|
| R0.1 | Triage 36 secret/key recovery candidates | Confirmed | verified_artifact | **0.96** | high | — |
| R0.2 | Add secret-scanning CI gate to all 6 repos | Confirmed | deterministic_check | **0.87** | high | — |
| R0.3 | Land root branch into `main` (open/refresh PR) | Confirmed | deterministic_check | **0.90** | high | — |
| R0.4 | Prune 8 fully-merged local branches | Confirmed | deterministic_check | **0.93** | high | — |
| R0.5 | Decide CanonRec's purpose | Confirmed | direct_observation | **0.82** | substantial | — |
| R1.1 | Collapse CloudBank CI (33 → ~8 workflows) | Confirmed | deterministic_check | **0.84** | substantial | — |
| R1.2 | Unify Python version across the fleet | Confirmed (strengthened) | deterministic_check | **0.89** | high | — |
| R1.3 | Cut repo bloat (20 tracked zips; dup archives) | Confirmed | deterministic_check | **0.88** | high | — |
| R1.4 | Govern the `GUMAS_SIM_2.5/` container | Confirmed | direct_observation | **0.87** | high | — |
| R2.1 | Recovery pipeline v2 — build promotion gate | Confirmed | deterministic_check | **0.86** | high | — |
| R2.2 | Establish a fleet-wide test floor | Confirmed | deterministic_check | **0.88** | high | — |
| R2.3 | Mission Control as a live dashboard | Confirmed | verified_artifact | **0.78** | substantial | — |
| R2.4 | Formalize CanonRec release flow | Confirmed (conditional) | direct_observation | **0.80** | substantial | — |
| R2.5 | Thicken QGIA automation | Confirmed | deterministic_check | **0.76** | substantial | — |
| R3.1 | Make the inter-repo contract explicit | Confirmed | corroborated_inference | **0.74** | substantial | — |
| R3.2 | Settle the monorepo-vs-polyrepo question | Confirmed | verified_artifact | **0.76** | substantial | — |
| R3.3 | Governance trend observability | **Confirmed with correction** | deterministic_check | **0.66** | limited | **⚠ yes** |
| R3.4 | Dependency & supply-chain policy | **Confirmed with correction** | deterministic_check | **0.62** | limited | **⚠ yes** |
| RB.1 | Refresh Mission Control report (brief action) | Confirmed | verified_artifact | **0.92** | high | — |

*The executive brief's six "Recommended Actions" are a subset of the above: secret triage → R0.1, PR to main → R0.3, branch prune → R0.4, recovery queue → R2.1, CanonRec decision → R0.5, refresh Mission Control → RB.1.*

---

## Validation detail

### Phase 0 — Stabilize

**R0.1 — Triage 36 secret/key candidates · 0.96.** Premise verified twice: `aurora_mission_control_latest.json` → `recovery_index.restricted_candidate_count = 36`, and `workspace_recovery_index_latest.json` → `signal_counts.secret_or_key_material = 36`. The action (review flagged secrets, rotate live keys) is non-discretionary. Highest-confidence item in the set.

**R0.2 — Secret-scanning gate · 0.87.** Verified: a grep of all six repos' `.github/workflows/` returns **zero** dedicated secret-scan workflows (`gitleaks`/`trufflehog`/`detect-secrets`). The 14 CloudBank workflows that match "secret" use the `${{ secrets.* }}` Actions context — i.e., they *consume* secrets, they do not *scan* for them. *Caveat (−0.09):* GitHub's native secret scanning / push protection is a repository **setting** not visible in tracked files, so "no scanning exists" is confirmed only for workflow-based scanning. The recommendation to add explicit, version-controlled scanning is sound regardless.

**R0.3 — Land root branch · 0.90.** Re-confirmed `git rev-list --left-right --count origin/main...HEAD` = `0 18` (0 behind, 18 ahead). Opening or refreshing a PR is always safe; the only judgment is *merge timing* relative to the in-flight CloudBank PR sweep, which is the owner's call.

**R0.4 — Prune 8 branches · 0.93.** Each named branch was verified via `git rev-list main...<branch>` to have **0 commits not already in `main`** — they are fully contained and deletion loses no history. The 7 branches with unmerged commits were correctly excluded from the delete list.

**R0.5 — Decide CanonRec's purpose · 0.82.** Premise verified: `CanonRec` holds `CanonRec_v1.3` … `v1.3.7` zip archives plus a `.skill` file — functionally a skill-release repo. Scored `substantial` rather than `high` because it is a meta-recommendation ("make a decision"); its value depends on the decision that follows.

### Phase 1 — Consolidate

**R1.1 — Collapse CloudBank CI · 0.84.** Verified: `ls .github/workflows | wc -l` = **33**, and `pr_evaluation.yml.backup` is git-tracked (confirmed delete candidate). Scored `substantial`: the *direction* (consolidation via reusable workflows) is well-evidenced, but the specific "~8" target is an estimate pending the workflow inventory.

**R1.2 — Unify Python version · 0.89.** Premise verified and **stronger than first stated** — CloudBank carries three different version signals internally: `setup.py` → `python_requires=">=3.8"`, `runtime.txt` → `python-3.12.0`, README badge → `3.11+`; the workspace machine's `python3` is `3.9.6`. A four-way skew. The "pick 3.12 as floor" choice is reasoned judgment.

**R1.3 — Cut repo bloat · 0.88.** Verified: `git ls-files` in CloudBank lists **20 tracked `.zip` files**; `docs/workspace-map.md` inventories multiple 845.1 MiB archives tagged `hash_duplicate`. History-rewrite coordination risk is acknowledged in the recommendation itself.

**R1.4 — Govern `GUMAS_SIM_2.5/` · 0.87.** Verified: the directory is **1.3 GB**, has **no `.git`**, and holds **46 loose top-level files** alongside 3 nested repos. Applying the root control-plane pattern is a proven approach within this same workspace.

### Phase 2 — Productionize

**R2.1 — Recovery pipeline v2 · 0.86.** Verified: `workspace_recovery_index_latest.json` → 1,011 discovered / 100 surfaced; and `tools/` contains **no promotion/extraction tool** (matches in `tools/*.py` for "promot" are all disclaimer text — "does not promote canon"). The README itself names a required "separate promotion gate" as not-yet-built. The recommendation is aligned with the project's own stated mission. XL effort means execution uncertainty, not premise uncertainty.

**R2.2 — Test floor · 0.88.** Verified by file count: DuelSim **0** `test_*.py` (Playwright e2e only), CanonRec **0**, QGIA library/spine **1** each, root **18**. CloudBank's ~109 figure is self-reported (README badge) → `corroborated_inference` for that one repo only; the zero-coverage findings are deterministic.

**R2.3 — Mission Control dashboard · 0.78.** Premise verified (`aurora_mission_control` aggregates 6 sources). Scored `substantial`: this is an enhancement, not a defect fix — discretionary value.

**R2.4 — Formalize CanonRec releases · 0.80.** Premise verified (committed version zips). Scored `substantial` and **conditional** — only applies if R0.5 decides CanonRec stays active.

**R2.5 — Thicken QGIA automation · 0.76.** Verified: 4 scripts / 1 test per repo; `constellation-knowledge-index.yml` present. Scored `substantial`: "where to invest" is somewhat open-ended judgment.

### Phase 3 — Architect

**R3.1 — Explicit inter-repo contract · 0.74.** The implied architecture (CloudBank = runtime authority, QGIA = knowledge, etc.) is drawn from reading `README.md`/`AGENTS.md` prose → `corroborated_inference`, not a hard artifact. Strategic and judgment-heavy; scored `substantial`.

**R3.2 — Monorepo vs polyrepo · 0.76.** Premise verified — `AGENTS.md` has an explicit "Commit / Hook Caveat" section documenting the worktree/pre-commit path mismatch that the nested-repo-in-control-plane shape causes. The recommendation is "decide deliberately"; sound but meta.

**R3.3 — Governance trend observability · 0.66 ⚠.** **Confirmed with correction.** Verified that the four core scanners overwrite single `*_latest.json` snapshots (9 such files, no trend store). **However**, the original "no history" framing was too broad: `reports/analysis/gitwiz/` and `reports/automation/archive-entropy-guard/` *do* retain dated history. Recommendation re-scoped to the four core scanners. Below threshold because the recommendation *as written in the roadmap* overstated its premise.

**R3.4 — Dependency & supply-chain policy · 0.62 ⚠.** **Confirmed with correction.** Verified across all 6 repos: only `aurora-cloudbank-symbolic-main` has `.github/dependabot.yml`; the other 5 (root, DuelSim, CanonRec, QGIA library, QGIA spine) have none, and no `renovate.json` exists anywhere. The roadmap's "add Dependabot/Renovate / no unified policy exists" was inaccurate — CloudBank already has Dependabot. Corrected recommendation: **extend Dependabot to the 5 uncovered repos and standardize on CloudBank's config.** Below threshold because the premise as written was partly false.

### Brief-specific action

**RB.1 — Refresh Mission Control · 0.92.** Verified: `aurora_mission_control_latest.json` `generated_at` 2026-05-23T19:59Z predates current HEAD `42faeba`; its "9 in-progress paths" item is already resolved. `make mission-control-report` is read-only and safe.

---

## Automation opportunities (grouped)

The roadmap's automation suggestions — reusable-workflow library, scheduled GITWIZ sync audit, recovery burn-down digest, PR→Gmail notification — were not individually scored. As a group they are **substantial confidence (~0.80)**: all are well-evidenced enabling actions, none is on a critical path, and each depends on a parent workstream landing first (e.g., the reusable-workflow library depends on R1.1).

---

## Method & limitations

- **Scoring scale** is the project's own — `aurora_confidence_audit_contract_v1` bands and 0.70 threshold. Scores are **analyst-assigned**, which the contract explicitly anticipates as a calibration input ("reviewer adjudication"). They were *not* produced by the mechanical `tools/aurora_confidence_audit.py`, whose rubric scores claim *metadata completeness* rather than per-recommendation judgment.
- **A confidence score is not a truth proof** (per the contract's non-goals). Each score blends premise certainty with action soundness; a high score means "well-evidenced and sound to act on," not "guaranteed outcome."
- **Self-review caveat:** this validates recommendations authored in the same session. The two corrections (R3.3, R3.4) were surfaced by independent re-checks against the repos; an outside reviewer is still the stronger check for strategic items R3.1–R3.2.
- **Calibration state** is `bootstrap_default_v1` / `rubric_seed_only` — the project has no resolved-outcome history yet, so absolute scores should be read as relative rankings, not calibrated probabilities.
- All premises were re-verified live at generation time (git state, file counts, workflow inventories, manifest contents). No nested repos were mutated.

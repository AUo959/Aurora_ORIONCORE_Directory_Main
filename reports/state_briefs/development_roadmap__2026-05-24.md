# Aurora / ORIONCORE — Holistic Development Roadmap

- **Generated:** 2026-05-24 (Opus-authored strategic recommendations)
- **Scope:** All 6 repos — root control-plane + `aurora-cloudbank-symbolic-main`, `DuelSim_v2.0`, `CanonRec`, `qgia-knowledge-library-main`, `qgia-knowledge-spine-main` — plus the `GUMAS_SIM_2.5/` container.
- **Companion:** [`executive_brief__2026-05-24.md`](executive_brief__2026-05-24.md) (current-state snapshot)
- **Nature:** Advisory. Nothing here has been executed. Sequencing assumes a single maintainer.

---

## How to read this

The state brief answers *"is anything broken?"* (no). This roadmap answers *"where should engineering effort go?"* It is organized as four phases — **Stabilize → Consolidate → Productionize → Architect** — with effort/impact scoring per workstream. Phase 0 is days of work; Phase 3 is a multi-month horizon. Phases overlap; the ordering is dependency-driven, not calendar-locked.

**Effort:** S (<1 day) · M (1–3 days) · L (1–2 weeks) · XL (>2 weeks)
**Impact:** ★ low · ★★ moderate · ★★★ high

---

## Fleet snapshot — what we are developing on

| Repo | Role | Size signal | Tests | CI workflows | Health flag |
|---|---|---|---|---|---|
| **root** (`Aurora_ORIONCORE_Directory_Main`) | Workspace control plane: 23 Python tools, governance scanners, manifests | `.git` 17 MB | 18 `test_*.py` | 1 (`ci.yml`) | Branch sprawl |
| **aurora-cloudbank-symbolic-main** | Quantum-symbolic runtime / parser authority | `.git` 44 MB, 2,465 tracked files, **20 tracked `.zip`** | ~109 (self-reported) | **33** | CI sprawl, repo bloat, version skew |
| **DuelSim_v2.0** | Standalone duel simulation app (UI contract frozen v2.4.1) | 10 `.py` | **0 pytest** (Playwright e2e only) | 1 (`release-gate.yml`) | No unit tests |
| **CanonRec** | Canon-reconciliation skill distribution (`v1.3`–`v1.3.7`) | mostly `.zip` archives | **0** | **0** | Undefined repo purpose |
| **qgia-knowledge-library-main** | Geopolitical knowledge corpus + closed-loop scripts | 4 `.py` | 1 | 1 | Thin automation |
| **qgia-knowledge-spine-main** | Forecasting/Bayesian knowledge spine | 4 `.py` | 1 | 1 | Thin automation |
| `GUMAS_SIM_2.5/` (container) | **Not a repo** — 1.3 GB folder holding 3 nested repos + 46 loose files | 1.3 GB | — | — | Ungoverned junk drawer |

**The structural story:** the *root* repo received disciplined control-plane treatment (manifests, scanners, intake routing, privacy screen). That discipline has **not** propagated to the rest of the fleet. CloudBank carries enterprise-grade ambition with maintenance debt; `GUMAS_SIM_2.5/` is an ungoverned 1.3 GB container; DuelSim and CanonRec have near-zero test/CI coverage. The roadmap is mostly about **propagating the root's discipline outward**.

---

## Phase 0 — Stabilize (this week)

Close exposure and clear the integration backlog before starting new work.

| # | Workstream | Effort | Impact | Notes |
|---|---|---|---|---|
| 0.1 | **Triage 36 secret/key recovery candidates** | M | ★★★ | Inspect for live credentials; rotate anything real; mark dispositioned. Do not promote to canon. This is the single P1. |
| 0.2 | **Add a secret-scanning CI gate to all 6 repos** | S | ★★★ | `gitleaks` or `trufflehog` as a GitHub Action on push + PR. Prevents recurrence of 0.1. One reusable workflow, referenced by each repo. |
| 0.3 | **Land the root branch into `main`** | S | ★★ | 18 commits ahead, 0 behind. `python3 skills/gitwiz-github-manager/scripts/gitwiz_pr_packet.py --repo-name root --base origin/main` drafts the PR. |
| 0.4 | **Prune 8 fully-merged local branches** | S | ★★ | `clean-diff-panel-2026-04-14`, `gitwiz-sync-audit-mainline-2026-04-08`, `gitwiz-sync-audit-overlap-2026-04-08`, `privacy-scope-hardening`, `privacy-scope-hardening-mergefix`, `root-control-plane-sync-2026-04-01`, `root-control-plane-sync-2026-04-01-split-prep`, `root-workspace-inventory-surfaces-2026-04-01`. |
| 0.5 | **Decide CanonRec's purpose** | S | ★★ | It is functionally a skill-release repo (`v1.3`–`v1.3.7` zips). Either formalize that (see 2.4) or mark it archived in `catalog/repo_registry.yaml`. The ~85-day "staleness" is then expected, not a risk. |

**Exit criteria:** zero unreviewed secret candidates, secret-scanning live fleet-wide, root branch merged, branch count down to ~9.

---

## Phase 1 — Consolidate the fleet (next 2–4 weeks)

Reduce maintenance surface and remove drift hazards.

### 1.1 — Collapse CloudBank CI sprawl · L · ★★★

33 workflow files in one repo is unmaintainable and slows every PR. Recommended:

- Inventory the 33; classify as **core** (lint, test, build, security, deploy), **event/automation** (constellation-*, auto-*, project-board sync), and **dead/duplicate** (note `pr_evaluation.yml.backup` is committed — delete).
- Extract shared steps into **reusable workflows** (`workflow_call`) kept in one place; have repos reference them.
- Target a core set of ~6–8 workflows per repo. Move bot/automation noise behind path filters and `concurrency` groups.
- This same reusable-workflow library becomes the delivery vehicle for 0.2 (secret scan) and 2.2 (test floor).

### 1.2 — Unify the Python version across the fleet · M · ★★★

Active version skew: CloudBank `runtime.txt` pins **3.12.0** and its README badges **3.11+**, while the workspace machine and root devkit run **3.9.6** (past upstream EOL). Recommended:

- Pick one supported floor — **3.12** aligns with CloudBank's declared runtime.
- Add `requires-python` to root tooling (`pyproject.toml` / packaging metadata) and a `python-version` matrix to each repo's CI.
- Install 3.12 on the workspace machine (the devkit's install-plan path can stage this) and re-run `make devkit-report`.
- Until then, treat root tools as 3.9-compatible and **do not** assume 3.10+ syntax in `tools/`.

### 1.3 — Cut repo bloat · M · ★★

- CloudBank tracks **20 `.zip` bundles** in Git history. Move them to GitHub Releases or Git LFS and remove from history (`git filter-repo` / BFG) — coordinate, it rewrites history.
- Root holds duplicated 845 MiB archive families under `archives/` (already inventoried, `hash_duplicate`-tagged). Execute the planned quarantine → hash-verify → delete flow; do not hard-delete directly (control-plane rule).
- `node_modules` is correctly untracked in CloudBank — keep it that way.

### 1.4 — Govern the `GUMAS_SIM_2.5/` container · L · ★★★

It is a **1.3 GB plain directory** with 46 loose top-level files (PDFs, `.docx`, dozens of `.zip` module packets, `SIM_ENGINE_OUTPUTS*`, `draft_logic/`, `draft_worldbuilding/`) interleaved with 3 live nested repos. Recommended:

- Apply the root's pattern: a manifest, an `intake/` lane, an `archives/` zone, and the recovery scanner pointed at it.
- The 3 nested repos already have their own remotes — leave them in place but register their boundaries explicitly (the root already does this in `catalog/repo_registry.yaml`; extend coverage).
- Loose `MODULE_PACKET__*.zip` / `ORION__*.zip` artifacts are prime recovery-index input — route, don't leave loose.

**Exit criteria:** CloudBank CI ≤ ~8 core workflows, single Python floor declared and tested in CI, no `.zip` in any repo's tracked tree, `GUMAS_SIM_2.5/` under a manifest.

---

## Phase 2 — Productionize the tooling (4–10 weeks)

Turn one-off scripts and review backlogs into durable systems.

### 2.1 — Recovery pipeline v2 · XL · ★★★

The recovery index is the project's defining mission (recover early local work predating GitHub). Today: **1,011 candidates discovered, 100 surfaced under a cap** — manual review does not scale. Recommended:

- Add the missing **promotion gate**: a tool that takes a reviewed candidate → validates → emits a receipt/PR into the correct owner repo. The scanners exist; the *disposition* half does not.
- Add **batch disposition** (accept/reject/defer with reason) and **dedup** so the 845 MiB of hash-duplicate archives collapse before review.
- Build a **live triage dashboard** (see 2.3) so the backlog is a worklist, not a JSON file.
- Track a burn-down metric in the weekly brief: candidates dispositioned per week.

### 2.2 — Establish a test floor · L · ★★

Coverage is uneven: root 18 tests (good model), CloudBank ~109, **DuelSim 0 pytest**, **CanonRec 0**, QGIA library/spine 1 each. Recommended:

- Minimum bar: every repo with executable code has a `tests/` dir, a smoke test, and CI that runs it.
- DuelSim has Playwright e2e but no unit tests — add `pytest` coverage for `duel_sim_v2_0.py` and `historical_presets_v2_0.py`; the v2.4.1 UI contract freeze is a good stabilization point to lock behavior with tests.
- QGIA repos are knowledge-heavy — their tests should validate the closed-loop contract and link integrity, not just code.

### 2.3 — Mission Control as a live dashboard · M · ★★★

`aurora_mission_control.py` already aggregates 6 signal sources into JSON. Promote it from a file to a **refreshable HTML view** — operator inbox, build lanes, recovery burn-down, and the 6-repo Git matrix on one page that re-pulls on open. Pairs naturally with the weekly scheduled brief (already configured).

### 2.4 — Formalize CanonRec's release flow · M · ★★

If CanonRec stays (decision from 0.5), make its versioning real: tagged releases instead of committed `v1.3.x.zip` files, a changelog, and a CI job that packages the `.skill` artifact. Otherwise the repo accumulates zip drift indefinitely.

### 2.5 — Thicken QGIA automation · M · ★★

The library/spine repos are strong on content, thin on code (4 scripts, 1 test each). Their `constellation-knowledge-index.yml` CI suggests an indexing ambition — invest there: automated index regeneration, broken-cross-reference detection, and the closed-loop contract validation already scaffolded in `QGIA_KNOWLEDGE_CLOSED_LOOP_CONTRACT_v1`.

**Exit criteria:** recovery backlog burning down weekly, every code repo has CI-run tests, Mission Control viewable as a live page.

### Automation opportunities (Phase 2)

- **GitHub:** one reusable-workflow repo/library consumed by all 6 repos — single source for lint/test/security/release. Cuts per-repo CI maintenance to near zero.
- **Scheduled jobs:** weekly state brief is live; add a scheduled all-repo GITWIZ sync audit and a recovery burn-down digest.
- **Browser/Gmail:** when a promotion gate (2.1) opens a PR, a lightweight notification to Gmail closes the loop without polling GitHub.

---

## Phase 3 — Architect the portfolio (10+ weeks)

Strategic decisions that need the lower phases done first.

### 3.1 — Make the inter-repo contract explicit · L · ★★★

The fleet has an implied architecture: **CloudBank** is the parser/runtime authority for command grammar; **QGIA** library/spine supply knowledge; **DuelSim** is a downstream sim app; **CanonRec** governs canon; **root** is the control plane. This is asserted in prose across `README.md` / `AGENTS.md` but not enforced. Recommended: a single `portfolio_architecture.md` plus machine-readable dependency edges in `catalog/`, so "who depends on whom" is queryable and CI-checkable.

### 3.2 — Settle the monorepo-vs-polyrepo question · M · ★★

Current shape is *polyrepo nested inside a control-plane repo* — unusual, and the source of the worktree/pre-commit caveat already documented in `AGENTS.md`. Either commit to it deliberately (document the boundary contract, tooling, and the path-mismatch workaround as intentional) or plan a migration to true sibling repos with the control plane as a thin orchestrator. Decide; don't drift.

### 3.3 — Governance trend observability · M · ★★

The governance scanners (`workspace_verify`, `recovery_index`, `confidence_audit`, `mission_control`) emit excellent point-in-time JSON but no history. Add a small append-only metrics store so trends — finding counts, recovery burn-down, confidence scores — are visible over time. The weekly brief's "Week-over-Week Delta" is the consumer.

### 3.4 — Dependency & supply-chain policy · M · ★★

CloudBank advertises AWS/Azure/IBM/Google quantum backends and ships `requirements*.txt` + `pyproject.toml` + npm. Add Dependabot/Renovate, pin lockfiles, and a license check across the fleet — currently no unified dependency policy exists.

---

## Per-repo priority summary

| Repo | Top action | Phase |
|---|---|---|
| root | Land branch, prune branches, declare Python floor | 0–1 |
| aurora-cloudbank-symbolic-main | CI consolidation (33→~8), de-bloat 20 zips, version pin | 1 |
| DuelSim_v2.0 | Add pytest unit coverage against frozen v2.4.1 contract | 2 |
| CanonRec | Decide purpose; formalize release flow or archive | 0 / 2 |
| qgia-knowledge-library-main | Thicken indexing automation + closed-loop validation | 2 |
| qgia-knowledge-spine-main | Same as library; broken-reference detection | 2 |
| `GUMAS_SIM_2.5/` | Bring under a control-plane manifest | 1 |

---

## Sequencing risks

- **History rewrites (1.3):** removing tracked `.zip` from CloudBank history rewrites SHAs — coordinate so no one is mid-branch, and do it before more branches fork.
- **CI consolidation regressions (1.1):** 33 workflows likely encode hard-won fixes. Migrate incrementally; keep old workflows disabled-not-deleted for one cycle.
- **Python bump (1.2):** 3.9→3.12 can surface dependency incompatibilities. Stage in CI matrix before flipping the machine default.
- **Recovery promotion (2.1):** the control-plane rule that recovery candidates are *not canonical by default* must hold — the promotion gate enforces review, it does not bypass it.

## Quick-win checklist (Phase 0, all S/M effort)

- [ ] Triage 36 secret/key candidates; rotate live keys
- [ ] Add `gitleaks` GitHub Action to all 6 repos
- [ ] Open + merge the root → `main` PR (18 commits)
- [ ] Delete 8 fully-merged local branches
- [ ] Decide + record CanonRec's status in `repo_registry.yaml`
- [ ] Delete committed `pr_evaluation.yml.backup` in CloudBank
- [ ] Refresh Mission Control (`make mission-control-report`)

---

*Method note: repo facts (test counts, CI workflow counts, tracked-file/`.zip` counts, `.git` sizes, Python version sources, `GUMAS_SIM_2.5/` size) were verified live at generation time. Effort/impact scores are judgment calls for a single-maintainer context and should be re-weighted if staffing changes.*

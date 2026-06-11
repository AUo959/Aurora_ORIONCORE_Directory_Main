# Remote-Branch & Closed-PR Sweep — 2026-06-11

Owner-directed pass targeting the recurring failure pattern: **work matured on
branches, no PR ever created, foundational pieces never wired in.** Scope:
remote branches across all six repos (the earlier unlanded-work audit covered
local branches only), all closed-unmerged PRs, and the full AUo959 GitHub
repo inventory.

## Recovered and LANDED this pass

| Work | Origin | Age when found | Disposition |
|---|---|---|---|
| **Central development roadmap** + review-note intake wiring + PR-template maintenance checks | `codex/central-dev-roadmap-review-intake(-v2)`, never PR'd | 14 days | CloudBank PR #984, merged (v1 wiring + v2 doc text) |
| **Autonomous drift responder** — agent, runbooks, metrics API + WS stream, 24 tests | `feature/drift-autonomous-response`, never PR'd | 65 days | CloudBank PR #985, merged (the response half of the drift story the outside review called "theatre") |
| **Ethical checkpoint vault** — versioned ethics-state checkpoints with rollback | `feature/ethical-checkpoint-vault`, never PR'd | 65 days | CloudBank PR #986, merged (tests adapted to CSRF middleware) |
| **QGIA forecast API** — QSFE engine REST surface | `feature/qgia-forecast-api`, never PR'd | 65 days | CloudBank PR #987, merged (wiring conflict with #986 resolved; 48 combined tests pass) |
| **Spine CRITICAL fix** — invert log pool robustness claim + truncation protocol | `critical-fixes-20260228`, never merged | 103 days | Spine PR #4, merged (knowledge index regenerated, contract validates) |
| **Peer Review Protocol status flip** DRAFT → ADOPTED | closed root PR #16 (closure note said "superseded" but the flip never landed; Codex's approve-with-notes receipt and cleared review-debts were already on main) | 10 days | Root commit (this sweep) |
| **GPT-5.5 upgrade package** — connected-repo audit + core upgrade plan | `codex/gpt-5-5-aurora-orion-upgrade-package-2026-04-29`, never PR'd | 43 days | Extracted to `reports/recovered_canon/` |

## Verified already landed (residue only — no action)

- `feature/reconstruct-pr-510-mrm` → merged as #511
- `codex/perplexity-agent-coordination-bridge-issue-20` → #21; doc byte-identical on main
- `codex/ci-pytest-artifacts-issue-18` → #19; `copilot/setup-repo-configuration` → #2
- Library `pr-3` Iran War 2026 package → content-identical to what landed 2026-06
- `codex/gitwiz-sync-audit-canonical` remote → superseded by the 2026-06-11 3-way merge
- Dependabot singles → bot-managed

## Documented decisions (deliberate, not lost)

- **PR #837** (39 commits, benchmark scorecard): closure note explicitly marks
  it "archival source for a smaller scorecard extraction, not abandoned work."
  Pending owner-paced extraction.
- **`copilot/fix-failing-workflows-actions`** (9 commits, May 6): project-board
  workflow logic guards; the #942 pin-fix era reshaped these files. Needs
  per-file evaluation against current workflows — deferred with this note.
- **`copilot/improve-aurora-agent` (#690) / `update-open-dependency-prs` (#691)**:
  closed during the May hardening; low-priority re-evaluation candidates.
- **`backup/prepopulate-main-2026-03-09`** + root March rescue remotes:
  archival pre-reset state; preserved (bundles + remote).

## NEW: unregistered repos found in the GitHub inventory

| Repo | Last push | Why it matters |
|---|---|---|
| `aurora-cloudbank-symbolic1` | 2025-09-23 | Name suggests an early CloudBank twin — possibly holds pre-dual-history work. **Registration + history comparison recommended** (next session). |
| `zip_wizard` | 2025-12-26 | The ZIPWIZ implementation repo; the zipwiz-governor skill exists but the repo is outside the registry/audit perimeter. **Register.** |
| `Un-Dia-en-la-Finca` | 2025-06-16 | Active but LaFinca-scope (non-Aurora); confirm out-of-scope classification. |
| AuroraOS / cloudbank-quantum-en | 2026-03-13 | Already registered remote-only; still unwired to constellation dispatch since March. |

## Pattern diagnosis

Every one of the seven recoveries follows the same shape: the work was
*finished* — tests written, docs polished — and then the session ended
without `gh pr create`. The June handoff strandings, the March porting
branches, and now the April/May feature branches are all the same failure.
Two defenses now exist (the unlanded-work audit method + the gitwiz sync
audit's new overlap detection); the third should be structural: a
**branches-without-PRs check** in the periodic audit cadence, which this
report's method now documents.

---

# Deep Pass Addendum — closed-PR refs and unregistered repos (same day)

The branch sweep could not see closed PRs whose branches were deleted;
GitHub's `refs/pull/N/head` can. All **103 closed-unmerged non-bot PRs**
were fetched and cherry-checked.

## Landed this pass

- **Benchmark scorecard** (`scripts/benchmark_scorecard.py`, 710 lines) —
  the extraction explicitly mandated by #837's closure note. Verified
  against current main (issue-linked health report: 12 fails / 5 required).
  Merged as **#988**.

## Verified landed-in-modified-form (June hardening wave)

#914 (R2 telemetry), #883 (rate limits) — 0 unlanded. #905/#904 (prompt
injection defense), #890 (MCP bridge hardening), #886 (atomic writes +
locks) — single cherry-orphans each, but the features verified present on
main by file/content inspection. #864/#843 — deliberate evidence-cited
closures (already documented).

## Long-tail dispositions (older eras, owner-paced)

| PR | Cherry | Disposition |
|---|---|---|
| #142/#97 Probabilistic Query Nexus (Sept era) | 18/13 | Module-era superseded by aumemmanager evolution; preserved in pull refs; evaluate only if PQN concepts return |
| #415 L1 relay agent nomenclature | 15 | Narrative-adjacent; candidate for canon reconciliation review next session |
| #124 async diagnostics refactor | 14 | Era-superseded; preserved |
| #251/#262/#96 lint/CI cleanups | 12/8/7 | Superseded by current CI |
| #405 OAuth2/RBAC route integration | 6 | Auth landed via other waves; verify-only candidate |
| #157/#158 insecure crypto removal | 6 | No legacy crypto module present on main; resolved by evolution |
| #107 validate command before ethics check | 6 | Ordering principle worth re-checking against current gate; small |
| #376 CLAUDE.md | 5 | CLAUDE.md exists on main; superseded |
| #348/#349/#350 DriftAwareAgent / EthicalCheckpoint / SymbolicForecastEngine | — | Original versions of the modules landed today as #985/#986/#987 — closed-the-loop confirmation |

## Unregistered repos — now registered

- **`zip_wizard`** — ZIPWIZ implementation (~97MB, 4 feature branches incl.
  vulnerability scanner, dormant since 2025-12). **SECURITY FLAG: `.env`
  committed at repo root on GitHub.** Owner must inspect/rotate/purge;
  agent access to credential contents is correctly classifier-blocked.
- **`aurora-cloudbank-symbolic1`** — single-commit Node.js skeleton
  (2025-09-23); NOT early CloudBank history (different stack);
  archive-or-delete candidate.

## Method note

`git fetch origin '+refs/pull/*/head:refs/remotes/pr/*'` + per-ref cherry
makes deleted-branch PRs auditable. This closes the last structural blind
spot in the recovery method: local branches, remote branches, stashes,
worktrees, runtime databases, and now pull refs are all swept surfaces.

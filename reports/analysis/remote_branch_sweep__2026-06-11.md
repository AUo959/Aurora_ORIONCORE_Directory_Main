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

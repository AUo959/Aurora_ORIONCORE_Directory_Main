# ORION — L3 Salvage Pass — Closing Record

**Version:** v1.2 · **Date:** 2026-09-08 · closes `…v1.0…` (inventory) and `…v1.1…` (execution log)
**Status: complete. Zero unpushed commits in any repository under `~/dev`.**

v1.1 recorded the salvage as done-but-unpushed, with pushing listed as blocked. That was wrong about the blocker: the bridge shell has no SSH egress, but `osascript` reaches the Mac's own shell, where the keys live. Everything is now on GitHub.

---

## 1. Final state

| Repo | Result |
|---|---|
| `Aurora_ORIONCORE_Directory_Main` | `main` +3 commits pushed · `integration/connectivity-pass-2026-08-19` pushed · **11 salvage branches** · **23 salvage tags** |
| `aurora-cloudbank-symbolic` | `integration/connectivity-pass-2026-08-19` and `codex/cloudbank-issue-1504-root-declaration-precommit` pushed · **25 salvage branches** |
| `qgia-knowledge-library` | `integration/connectivity-pass-2026-08-19` pushed |
| `qgia-knowledge-spine`, `CanonRec`, `DuelSim_v2.0` | already clean |

`git log --branches --not --remotes` returns **empty in all six repositories.**

## 2. Correction to v1.0 §1.2

v1.0 reported 7 unpushed commits across three repos, caveated as measured against a fetch cache from 2026-09-06. A live fetch revised that: the cloudbank and qgia-library commits sat on **branches** that had never been pushed, not on `main` — `main` in cloudbank was 31 *behind*, not ahead. The finding held; the shape of it did not. The caveat earned its place.

## 3. The GH007 decision, executed

Twelve commits — not three — carried `tlstreets@gmail.com` in both author and committer: the 3 connectivity commits plus a 9-commit Velar ruling chain behind the five 2026-07-21 tags (two parallel lineages of the same rulings, plus `63349bfe`). GitHub's email-privacy protection rejected every one.

Per the owner decision on queue item `connectivity-branch-email-privacy`, **option 2** was taken: rewrite author and committer email to `206913296+AUo959@users.noreply.github.com`.

| Guarantee | Evidence |
|---|---|
| Content byte-identical | branch tree `776f3430…` before **and** after |
| Nothing discarded | 12 refs preserved locally under `refs/backup/pre-email-rewrite/*` and `refs/original/*` |
| Working tree untouched | stashed and popped around the rewrite; `git status` identical before and after |
| No gmail left | all 12 rewritten commits report the noreply address |

SHAs changed, as the queue item anticipated: `7a50e0a → bd690f76`, `62dc466 → e8abece0`, `6349b1f → 80e3d40b`. **The registry pins that reference the old SHAs will need a refresh** — that is the known cost of option 2, not a new defect.

`connectivity-branch-email-privacy` now meets its definition of done (`integration/connectivity-pass-2026-08-19 exists on origin`). Worth confirming with `publication_debt` and closing the item in `catalog/session_state.json`.

## 4. Also done

`git worktree prune` removed two stale registrations (`aurora-root-publication-debt-20260826`, `aurora-root-connectivity-20260827`) whose paths no longer existed. The worktrees under `~/.codex/worktrees` and `~/dev/ecguard-wt` still exist on disk and were left alone.

## 5. Still open — unchanged from v1.1

- **The two withheld simulation runs** (§D.1 of v1.1). Decision still yours; `catalog/execution_context_exemption.yaml` now exists as the mechanism.
- **The catalog relocation plan** left uncommitted (§D.2 of v1.1) — it proposes moving `recovery/` into `intake/`.
- **The iCloud repo** at `~/Documents/GitHub/aurora-cloudbank-symbolic` (§E.2) — conflict duplicates inside `.git`. Untouched.
- **Step 5**: `aurora-ace-reviews/` (L3 promotion candidates), `~/Downloads/CharSim/`, `aurora_exhibit_site/`, `~/.aurora/l1-runs/` still have no version control anywhere.
- `gc.auto=0` and `pruneExpire=never` remain set on ORIONCORE and cloudbank. Now that the tags are on origin this is belt-and-braces; **unset it when you want maintenance running again.**

---

*Built for consistency, clarity, and care.*

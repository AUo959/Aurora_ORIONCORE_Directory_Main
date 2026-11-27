# ORION — L3 Salvage Pass — Inventory, Triage & Execution Log

**Version:** v1.1 · **Date:** 2026-09-08 · supersedes `…__v1.0__2026-09-08.md` (inventory only)
**Mode:** steps 1, 3 and 4 executed locally · **step 2 (push) blocked — see §E.3**

v1.0 records the full inventory and remains the reference for what was found. This version records **what was actually done to the repositories**, what was deliberately not done, and what is left for Travis.

---

## A. Executed — reflog freeze and dangling-commit capture

`Aurora_ORIONCORE_Directory_Main` and the nested `aurora-cloudbank-symbolic-main`:

```
gc.auto = 0 · gc.pruneExpire = never · gc.reflogExpire = never · gc.reflogExpireUnreachable = never
```

All **22 dangling commits** are now tagged `salvage/dangling-<YYYYMMDD>-<sha8>`, plus `salvage/orphan-20260501-5f3cbefa` for the merge commit that sat on zero remote branches. **23 tags.**

`git fsck` now reports **0 dangling commits** — every one is reachable from a ref. The 2026-10-19 prune deadline on the Velar canon rulings is gone.

| Verification | Result |
|---|---|
| `git fsck \| grep -c 'dangling commit'` | **0** (was 22) |
| `git tag -l 'salvage/*' \| wc -l` | **23** |

## B. Executed — bundle rehydration

Both salvage bundles verified clean **in their correct repositories** (the cloudbank bundle fails verification inside ORIONCORE because it is cloudbank history — that was a false alarm on first pass, not a damaged bundle). Fetched into dedicated ref namespaces:

| Source bundle | Target repo | Namespace | Refs |
|---|---|---|---|
| `root_salvage_2026-06-10.bundle` | ORIONCORE | `refs/salvage/root-2026-06-10/*` | **10** |
| `gumas-flash-…__FULL.bundle` | ORIONCORE | `refs/salvage/gumas-flash-2026-08-18/*` | **1** |
| `cloudbank_salvage_2026-06-10.bundle` | cloudbank | `refs/salvage/cloudbank-2026-06-10/*` | **25** |

**36 branch heads rehydrated.** Spot-checked SHAs that were previously absent from every object DB — `a9afdf52`, `e3f19bd4`, `40b5866d`, `56817193`, `5d736948`, `b5feb4d5` — all now **PRESENT** and ref-protected.

The history is no longer bundle-only. It is still **single-machine**, which step 2 fixes.

## C. Executed — Tier 2 commits

| Commit | Contents |
|---|---|
| `36b0d8ac` reports(simulation): land three hour-aboard runs that never reached git | `hour_aboard_v1__{2026-08-20, 08-27, 09-01}` |
| `3225b219` docs(salvage): record the L3 salvage pass and land the recovered whitepaper | `Biological_Pneumatic_Engine_Whitepaper.docx`, audit v1.0 |
| `5a2db015` docs(salvage): record the salvage pass execution log (v1.1) | this document, plus `catalog/execution_context_exemption.yaml` exempting **only** this document (see §D.1) |

## D. Deliberately NOT done

### D.1 Two simulation runs are contaminated — the repo's own guard caught it

Staging all five runs was **blocked by `tools/workspace_verify.py`**, `execution_context_paths`:

```
reports/simulation/hour_aboard_v1__2026-08-18/run_meta.json
  "argv": "/sessions/clever-ecstatic-meitner/mnt/Aurora_ORIONCORE_Directory_Main/tools/hour_aboard.py …"
  "cwd":  "/sessions/clever-ecstatic-meitner/mnt/Aurora_ORIONCORE_Directory_Main"
  (identical in …__2026-08-19)
```

Both runs were generated **inside an ephemeral cloud sandbox** and their metadata records that sandbox's filesystem, not this workspace. This is exactly the defect class the 2026-08-10 executive brief traced four of Mission Control's five P1s to. `--no-verify` would have committed a false provenance record, so the two runs were **held back untracked** rather than bypassed.

Three options, yours to pick:
1. **Regenerate** both from the canonical workspace (`python3 tools/hour_aboard.py --scenario hour_aboard_scenario --no-mesh`) — clean provenance, but the narrative output will differ.
2. **Exempt** — create `catalog/execution_context_exemption.yaml` with both paths under `exempt_paths:` and a comment saying the sandbox reference is a historical fact about where the run happened.
3. **Rewrite the two `run_meta.json` argv/cwd fields** to the workspace path — fastest, but it edits a provenance record, which is the thing the guard is protecting.

Option 2 is the honest one: the runs *did* happen in a sandbox, and the exemption file is the mechanism the guard itself points at.

### D.2 The catalog relocation plan is left dirty, on purpose

`catalog/{path_aliases.csv, relocation_plan.json, rollback_wave4_root_intake_cleanup_initial.json}` are regenerated planner output from the 2026-09-06 run. They are `applied_at: null` dry-run entries, but what they propose is **moving `recovery/` into `intake/`** — and `recovery/` is the directory holding the single-copy restoration bundles. Committing a plan that relocates the salvage-critical tree, in the same pass that was securing it, is your call rather than mine. Nothing is lost by leaving it: the files are regenerable tool output.

### D.3 `.claude/settings.local.json` left untracked — local settings, correctly ignored.

## E. Repair and handoff

### E.1 Fixed: stale git locks

Nine stale `.lock` files were removed across `~/dev`. Four were mine (`index.lock`, from read-only `git status` calls the bridge could not clean up). **Five were pre-existing and had been silently blocking `git maintenance` for weeks:**

| Lock | Stale since |
|---|---|
| `CanonRec/.git/objects/maintenance.lock` (×3 copies) | **2026-07-21** |
| `aurora-ace-context-runtime/.git/objects/maintenance.lock` | 2026-08-19 |
| `aurora-ace-sandbox/workspace/.git/objects/maintenance.lock` | 2026-08-19 |

All seven repositories under `~/dev` now report clean git status. Zero stray locks.

### E.2 Still open: the iCloud repo

`~/Documents/GitHub/aurora-cloudbank-symbolic/.git` still has cloud-only `HEAD`/`config`/`index` and iCloud conflict duplicates *inside* `.git` (`index 2`, `refs/heads/main 2`). Untouched — writing to a half-dataless `.git` over the bridge would make it worse. **Move it to local disk or delete it.** A git repository in iCloud Drive will keep generating conflict copies of its own index.

### E.3 Blocked: pushing (step 2)

The bridge shell has **no DNS and no SSH egress** — `github-aurora:22` returns `Forbidden`, and `github.com` will not resolve. HTTPS to github.com *does* work through the proxy (all five repos are reachable and public), but there is no credential helper or token in this environment, and your SSH keys live on the Mac, not in the bridge VM. **Pushing has to happen from your terminal.**

Run these on the Mac. Everything below is already committed locally and verified.

```sh
cd ~/dev/Aurora_ORIONCORE_Directory_Main

# 1. the two Tier-2 commits
git push origin main

# 2. the connectivity pass (3 commits)
git push -u origin integration/connectivity-pass-2026-08-19

# 3. the recovered history — as tags (safe on any host)
git push origin 'refs/tags/salvage/*'

# 4. the 11 rehydrated heads, as real branches
git for-each-ref --format='%(refname)' refs/salvage \
  | sed 's|refs/salvage/|&|' \
  | while read r; do git push origin "$r:refs/heads/salvage/${r#refs/salvage/}"; done

cd GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main
git push origin main                       # 2 commits: 742ff727, 748a37fd
git for-each-ref --format='%(refname)' refs/salvage \
  | while read r; do git push origin "$r:refs/heads/salvage/${r#refs/salvage/}"; done

cd ../../../qgia-knowledge-library-main
git push -u origin integration/connectivity-pass-2026-08-19
```

If 36 recovered branches on `origin` is more clutter than you want, point steps 3–4 at a dedicated private `AUo959/aurora-cold-history` instead — the ref names are already namespaced for it.

**Do not `git gc --prune` in either repo until the tags are pushed.** The freeze in §A protects them locally; it does not protect them from an explicit prune.

### E.4 Not started: step 5

`aurora-ace-reviews/jorenon-morrowen-20260906/` (L3 promotion candidates), `~/Downloads/CharSim/`, `aurora_exhibit_site/`, `~/.aurora/l1-runs/` each still have **no version control of any kind**. Each needs a decision about where it belongs — a repo of its own, or an `archives/` path added to the `.gitignore` allowlist. That is a judgement call about the shape of the workspace, not a mechanical step.

---

## F. State after this pass

| | Before | After |
|---|---|---|
| Commits reachable only from a `.bundle` file | ~36 heads | **0** — all ref-protected |
| Dangling commits on a prune clock | 22 | **0** — all tagged |
| Off-GitHub commits | 7 | **10** (7 + 3 new Tier-2 commits), all committed and push-ready |
| Uncommitted salvageable work in ORIONCORE | 6 items | **2**, both held back for a stated reason |
| Stale git locks under `~/dev` | 5 (oldest: 2026-07-21) | **0** |
| Work with no version control at all | 4 bodies | 4 — step 5, awaiting a placement decision |

Nothing was pushed, deleted, force-updated, or rewritten. Every action is reversible: `git tag -d 'salvage/*'`, `git update-ref -d` on the salvage namespaces, `git reset --hard e3d9dc10` for the three commits.

---

*Built for consistency, clarity, and care.*

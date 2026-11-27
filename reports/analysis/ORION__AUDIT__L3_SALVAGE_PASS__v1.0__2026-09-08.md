# ORION — L3 Salvage Pass — Comprehensive Inventory & Triage

**Version:** v1.0 · **Date:** 2026-09-08 · **Mode:** read-only inventory (no repo writes, no pushes)
**Device:** traviss-macbook-air-local · **Scope swept:** `~/dev`, `~/Desktop`, `~/Documents`, `~/Downloads`, `~/.aurora`, `~/.codex`, `~/Library/Mobile Documents/com~apple~CloudDocs`

**Cross-check caveat:** the device shell has no network egress (`git ls-remote` → `Forbidden`). Every "on GitHub / not on GitHub" claim below is verified against **cached `origin/*` refs**, last fetched **2026-09-06 03:11**. Anything pushed after that would read as unpushed here. Nothing in the findings depends on a fetch newer than that.

---

## 0. Headline

| # | Finding | Loss risk |
|---|---|---|
| 1 | **2 git bundles hold ~35 branch heads whose commits exist in no object DB on this machine** | **Critical — single-copy** |
| 2 | **7 commits from the 2026-08-19 connectivity pass are unpushed across 3 repos** (the pass is half-landed) | High |
| 3 | **22 dangling commits** in ORIONCORE, incl. four 2026-07-21 Velar canon rulings — reachable only until `git gc` | High (clock running) |
| 4 | `.gitignore` is deny-all + allowlist: **~11 GB of Aurora material is structurally invisible to git** | Medium (present, unversioned) |
| 5 | **`aurora-ace-reviews/` holds L3 promotion candidates and is in no repo at all** | High |
| 6 | The iCloud copy of `aurora-cloudbank-symbolic` has **iCloud conflict duplicates inside `.git`** (`index 2`, `refs/heads/main 2`) and cloud-only `.git` files | **Corruption risk** |

---

## 1. TIER 1 — Unique git history that exists nowhere else

### 1.1 Salvage bundles (single-copy history) — **act first**

`Aurora_ORIONCORE_Directory_Main/archives/salvage_bundles/` (gitignored, so not on GitHub either):

| Bundle | Size | Branch heads | Verified status |
|---|---|---|---|
| `cloudbank_salvage_2026-06-10.bundle` | 3.7 MB | **25** | heads `56817193`, sampled others **absent from every local object DB** |
| `root_salvage_2026-06-10.bundle` | 357 KB | **10** | heads `a9afdf52`, `e3f19bd4` **absent**; `5f3cbefa`, `45cfc4cf` present |

Named branches inside include `codex/root-control-plane-local-2026-03-25`, `codex/root-reconstruct-recovered-protocols-2026-03-26`, `codex/gitwiz-sync-audit-canonical-2026-04-08`, `codex/explain-statechange-defense-for-sws`, `chore/salvage-local-security-hardening`, `codex/aurora-cloudbank-safety-2026-03-13`, `codex/ci-workflow-repair`.

Also single-copy-ish: `recovery/GUMAS_RESTORATION_BRANCH_ARCHIVE__2026-08-18/gumas-flash-rebellion-battle-baseline__{FULL,SINCE_MAIN}.bundle` (head `40b5866d`, **absent from local object DB**). Second copy exists in iCloud `_COLD_STORAGE__2026-08-18/branch_archive/`.

**Disposition:** these are `.bundle` files sitting in an ignored directory on one laptop. Recommended: `git fetch <bundle> 'refs/heads/*:refs/heads/salvage/bundle-<name>/*'` into a scratch clone, push the refs to a private `AUo959/aurora-cold-history` repo, then keep the bundles as a belt-and-braces copy.

### 1.2 The 2026-08-19 connectivity pass — unpushed across three repos

| Repo | Branch | Commits not on any remote |
|---|---|---|
| `Aurora_ORIONCORE_Directory_Main` | `integration/connectivity-pass-2026-08-19` | `7a50e0a` feat(constellation): put the control plane inside the topology it governs · `62dc466` fix(registry): stop the scanner erasing the registry's own annotations · `6349b1f` docs(audit): record offline verification evidence |
| `…/aurora-cloudbank-symbolic-main` (nested) | `main` | `742ff727` ci: enforce root declaration in pre-commit (08-15) · `748a37fd` fix(constellation): make the hub able to accept and route a real event (08-19) |
| `qgia-knowledge-library-main` (nested) | `integration/connectivity-pass-2026-08-19` | `0dc3a8e` fix(constellation): un-break the hub publish gate · `af9bc9a` chore(constellation): refresh knowledge index |
| `qgia-knowledge-spine-main` (nested) | `integration/connectivity-pass-2026-08-19` | **none — this one *was* pushed** |

This is the significant structural finding: **one logical change set, four repos, three unpushed.** The spine half is on GitHub; the hub, the library and the control plane are not. Anyone reading `origin` sees a partially-wired constellation.

Supporting artifact on the ORIONCORE branch: `docs/ORION__AUDIT__CONSTELLATION_CONNECTIVITY_PASS__v1.0__2026-08-19.md`, plus `tools/workspace_scan.py`, `tools/registry_bootstrap.py`, `.aurora/constellation.json`, `.github/workflows/constellation-health-respond.yml`.

### 1.3 Dangling commits (reflog-only, prune clock running)

22 dangling commits in ORIONCORE. Highest-value:

| Date | SHA | Subject |
|---|---|---|
| 2026-07-21 | `e5f2dbd` | velar: Vel-Surak placement ruling executed — registry head refresh (CanonRec `4d13959`) |
| 2026-07-21 | `acb7339` | velar: fabric ruling batch executed — linter vocab/superseded refinements (CanonRec `39eaf51`) |
| 2026-07-21 | `91a0a21` | velar: Crescent anchor pass recorded (CanonRec `72cb6d6`) |
| 2026-07-21 | `a741ee1` / `88f4442` | registry: CanonRec head `147d021` (merge with remote Ranger doctrine `74a2fdd`) |
| 2026-08-27 | `7a3d3fa` | On `recovery/gumas-v2-tactical-consolidation`: skill_sync regen post-merge |
| 2026-08-09 | `ded68e3`, `c3432b9` | On main: preexisting-registry-and-map / preexisting-workspace-scan-outputs |

Plus `5f3cbefa` (2026-05-01, "Merge main into gitwiz sync audit branch") — present in the object DB but on **zero** remote branches.

**Deadline flag:** default `gc.reflogExpireUnreachable` is 90 days. The 2026-06-24 group is already past it; the 2026-07-21 Velar rulings expire around **2026-10-19**. Any `git gc --prune` (including an automatic one) removes them.

### 1.4 Branches that only *look* orphaned — cleared

`salvage/stash-gitwiz-pre-sync-2026-04-08`, `salvage/stash-qgia-json-pre-pr9`, `salvage/stash-root-diff-cleanup-2026-04-14`, `codex/root-control-plane-sync-2026-04-01-mixed-backup`, `codex/l1-embodiment-recovery-audit-20260810` all have matching `origin/*` refs or are ancestors of `origin/main`. **No salvage needed.** Same for `ecguard-wt` (clean, HEAD `28b5969` on origin) and every `[gone]`-upstream branch — all already merged to `origin/main`.

---

## 2. TIER 2 — Working files inside tracked repos, never committed

| Item | Size | Verified |
|---|---|---|
| `reports/simulation/hour_aboard_v1__{2026-08-18,08-19,08-20,08-27,09-01}/` | 5 × 48 KB | **0 files on `origin/main`** for all five. The 104 tracked files under `reports/simulation/` are the June runs — these five are the entire untracked tail |
| `archives/recovered_prototypes/biological_pneumatic_engine/Biological_Pneumatic_Engine_Whitepaper.docx` | 56 KB dir | sibling `.py`, `BEHAVIOR_INVENTORY`, `RECOVERY_RECORD` are tracked; **the whitepaper is not** |
| `catalog/path_aliases.csv`, `catalog/relocation_plan.json`, `catalog/rollback_wave4_root_intake_cleanup_initial.json` | — | modified, uncommitted |
| `.claude/settings.local.json` | — | untracked (likely intentional) |
| `execution-context-guard.patch` (17 KB), `ecguard_pr_body.md` | — | gitignored; branch `fix/execution-context-guard` is already on origin → **probably redundant, verify then discard** |

Each `hour_aboard_v1` run is a complete set: `sim_raw.json`, `narrative_reconstruction.{json,md}`, `crew_logs.md`, `interaction_map.{json,md}`, `companion_ops.json`, `souls_accounting.json`, `run_meta.json`. These are L2 narrative outputs with no backup.

---

## 3. TIER 3 — Whole trees excluded by the `.gitignore` allowlist

`Aurora_ORIONCORE_Directory_Main/.gitignore` opens with `/*` (deny everything) and re-admits paths one at a time. Consequence: several top-level directories hold substantial work that git has never seen.

| Path | On disk | Tracked | Contents of salvage interest |
|---|---|---|---|
| `archives/` | **9.0 G** | 21 files | `unzipped/` 6.4 G · `session_archives/` 2.7 G (11 `Au_Archive_*` sets, 2025-03 → 2026-06) · `sim_archives/` 27 M · `capsules/` 24 K — **6 `Anchor_Harmony_Capsule_DR-SRPv1` variants (Helix, Virellian, Tessellate, Aegis, Orien)** · `structured_archives/` (STAFF_REGISTRY_SSOT, PAT_LIVE_SUBSET_SSOT, ORION_ORD PromotionWorkbench) |
| `GUMAS_SIM_2.5/` | **1.6 G** | 21 files | `Aurora_Sim_Architecture` 1.5 G · `DuelSim` 51 M · `CanonRec` 23 M · `SIM_ENGINE_OUTPUTS(_SEED99)` 17 M · `ORION_SCENARIO_CATALOG_v0_2_{12..15}` (HTML+PDF) · `AURORA PROJECT STATE REPORT 2026 03 02.pdf` |
| `projects/` | **710 M** | 1 file | `Streamdeck_Glyphs` 391 M · `Aurora_Project_Cloudhub_Deploy` 205 M · `Perplexity_Research` 50 M · `Aurora_New_11_9` 27 M · `GUMAS_SIM_2.0` 21 M · `GUI_Cloudhub` 15 M · `Opal2_Modular_System_Dev` · `Quantum_Forge_Index` |
| `recovery/` | **61 M** | **0** | 143 files: 50 md / 30 py / 24 json / 10 zip / 3 patch. `GUMAS_RECOVERY_ADDENDUM_F__ENGINE_LINEAGE`, `GUMAS_RESTORATION_BRANCH_ARCHIVE__2026-08-18` (2 bundles + SHA256 manifests + `MERGE_ANALYSIS.md`), `UNRECOVERABLE_ZIP_MEMBERS__2026-08-18.zip` |
| `intake/` | **42 M** | 1 file | **`Threadcore Library/`** 1.3 M — `THREADCORE_UNIFIED_DEPLOY_v2_FULL.zip`, `THREADCORE_RESEAL_LEDGER.json`, `THREADREFLECT_v1.1_macro.json`, `Threadcore_Reflect_Composite_v3.5_macroready_SUPERMACRO.json`, `THREADCORE_CONSTELLATION_AUGMENTOR_*`, `THREADCORE_DEPLOY_SEAL_v1.zip`, glyph badges, Stream Deck macros, QR triggers · `Thread_The_Station_is_Well.md` · `recovered_mesh_runtime_2026-06-10` · `text_*.txt` transcripts · 6 large PDFs (`The_Architecture_of_Presence`, `Orion_Station_Orientation`) |
| `Aurora_Sim_Architecture/` | 45 M | 0 | 2 log files only (a sparse duplicate of the `GUMAS_SIM_2.5` copy) |
| `qgia-knowledge-library-main/` | 2.7 M | 0 | **nested repo, on GitHub** — 51 md (SAT handbook, forecasting methodology, regional rollups). `main` is behind 2 |
| `qgia-knowledge-spine-main/` | 972 K | 0 | **nested repo, on GitHub** — schemas, policies, `.aurora/constellation.json`. `main` behind 2 |
| `.codex_skill_edits/` | 400 K | 0 | 9 skill packages: `aurora-governance-orchestrator`, `threadcore-governor`, `zipwiz-governor`, `aurora-script-governor`, `gumas-simulation-engine` + others — **these are the working copies of skills you have installed** |
| `.git_decommissioned_20260304_233325/` | 8.9 M | 0 | a retired `.git` (255 object dirs, index, logs, subtree-cache) from 2026-03-05. Worth one `fsck` sweep for unique commits before deleting |
| Loose ignored docs | — | 0 | `QGIA_Axiom_Doctrine_Narrative.md`, `QGIA_Runtime_OnePager.md`, `# QGIA Operational Axiom v3.xml` (leading `#` — likely a shell mishap; rename) |
| `_entropy_quarantine/` | 4 K | 0 | `broken_filename_threadcore_snapshot_2025-06-29.json` |

**Note on the nested repos:** `CanonRec`, `DuelSim_v2.0` and `qgia-knowledge-spine` are clean and fully pushed. Only `aurora-cloudbank-symbolic-main` and `qgia-knowledge-library-main` carry unpushed commits (§1.2).

---

## 4. TIER 4 — Work outside any repository

### 4.1 `~/dev` — non-repo directories

| Path | Size | Assessment |
|---|---|---|
| **`aurora-ace-reviews/jorenon-morrowen-20260906/`** | 24 M | **High value, zero version control.** ACE determination ledger (`ace.determination.character.c0a1b864….json` + `.materialized`), `proposal.patch`, and a full rehearsal tree containing **L3 staging candidates**: `L3__PROTOCOL_UPDATE__PICARD_DELTA_3__v3_0.md`, `L3__ANCHOR_RULE__EOS_SEED_ORION.md`, `L3__SCHEMA_DEFINITION__THREADCORE_BENCHMARK_LOOM_RUN_SCHEMA__v1_0.md`, plus validation runs, evidence receipt, reconciliation + drift-log outputs |
| `aurora-ace-sandbox/` | 168 M | `world.json` (isolated-world authority, canon head `6ff232d7`), `state/contexts`, `state/requests`, `AGENTS.md`, `START_HERE.md`. Its 4 unique tool files (`aurora_ace_sandbox.py`, `aurora_ace_sandbox_mcp.py`, `ace/sandbox.py`, `docs/AURORA_ACE_SANDBOX.md`) are **confirmed on `origin/codex/ace-persistent-continuity-20260906`** — only the runtime state is unique |
| `aurora-ace-context-runtime/` | 23 M | 621 commits, **no git remote configured** — but all 60 most-recent commits verified present in ORIONCORE and on `origin/codex/ace-persistent-continuity-20260906`. **Duplicate, not salvage.** Safe to delete once you're done with it |
| `aurora-ace-runtime/` | — | Python venv. Discard |
| `aurora_exhibit_site/` | 212 K | 13 HTML pages (`canon.html`, `forecast.html`, sources for drift-log, forecast-ledger, calibration-report, maya-dossier, spotcheck-receipt) + a `.vercel/project.json` link. **No git.** A published-looking artifact with no repo behind it |

### 4.2 `~/.aurora` and `~/.codex`

| Path | Volume | Assessment |
|---|---|---|
| `~/.aurora/l1-runs/` | 76 K, 4 runs | L1 `state.json` per run + `migration_projection_v1_2.json`, `migration_receipt.json`, `recovery_receipt.json`. Small, unique, L1-layer |
| `~/.codex/sessions/` | 953 M, 624 files | Codex CLI transcripts — the working record behind many commits |
| `~/.codex/archived_sessions/` | 142 M, 393 files | as above |
| `~/.codex/memories/` + `memories_1.sqlite` | 892 K + 2 M | Codex-side memory |
| `~/.codex/.chatgpt-projects/` | 860 K, 45 files | project definitions |
| `~/.codex/worktrees/` | **530 M, 46 138 files** | 20 worktrees (9 ORIONCORE, 11 cloudbank). **All clean (`dirty=0`)** — no uncommitted work. 5 point at a `.git` in iCloud that no longer exists. **Pure reclaimable clutter** |
| `~/Documents/Codex/` | 291 M, **59 410 files** | Codex Cloud task outputs by date/task: `.patch` files (`cloudbank-vercel-pr1184.patch`, `pr-1184-types-node-followup.patch`) and generated deliverables (e.g. `outputs/aurora-black-box/` — a full site with `TALK_TRACK.md`). Not in any repo |

### 4.3 `~/Downloads` — Aurora-domain files

| File | Size | Date |
|---|---|---|
| `AURORA_ACE__HANDOFF__CURRENT_STATE_AND_V1_ACCEPTANCE__v1.0__2026-08-15.md` | 33 K | 08-15 |
| `Aurora_GUMAS_Salvage_Specification_v1.0.docx` | 49 K | 07-28 |
| `ORION_PROJECTSPACE__{CHARTER,FRAMEWORK,REGISTRY}__…__v1.0__2026-07-27.md` | 6 K ea. | 07-28 |
| `GUMAS_RECOVERY_ADDENDUM_D__ROOT_CAUSE__2026-08-12.md` | 8 K | 08-12 |
| `GUMAS_SIM_2.0__WITNESS_A__1f9dae31.zip` / `…WITNESS_B__60631444.zip` | 14 M ea. | 08-12 |
| `GUMAS_V2_TACTICAL_RECOVERY__2026-08-12.zip` | 74 K | 08-12 |
| `CanonRecv1.3.3_Claud.zip` | 44 K | 2026-03-01 |
| `aurora-cloudbank-symbolic-main.zip` | 4.4 M | 2025-10-26 |
| `continuity_attestation_v2.4_stellaraccord.json`, `aurora_gumas_integrated_snapshot_manifest_reconstructed_v2.4.json`, `CONTINUITY_LOG_UPDATE.md` (+ dup) | ~1.7 K ea. | 2025-10-31 |
| `qgia-unified-memory-synthesis.md` (+ dup) | 13 K | 2025-10 |
| **`CharSim/`** | 5.8 M, 54 files | Character Simulator: `GUIDE__GOLDEN_REFERENCE_SET__v1.0`, `TEMPLATE__CHARACTER_DOSSIER__v1.0`, `UPDATE_BUNDLE__COMPLEXION_LOCK__v2.1__2026-08-25` (operating layer, source manifest, corrections/drift ledger, live-reference attachment protocol), `ANNIE__DOSSIER__VISUAL_IDENTITY__v1.0` — **a coherent unversioned project** |

*Excluded from this pass by category: personal, legal, medical, employment and family-matter documents in `~/Downloads`, `~/Documents`, `Current Tasks/`, `New Space /`, `_refscan/`, and `FamliyStructure/`. Not catalogued here.*

### 4.4 iCloud Drive — the deep archaeology layer

**`Extras_Backups (Au)/`** (6 398 files, 6 308 downloaded locally) is the **earliest symbolic layer** and appears nowhere in git:

- `Extra Folders/T1_SymbolicThread_EOS_SEED_ORION/` — `QUANTUM_FORGE_Module_Export_v1.0`, `SRB_QUANTUM_FORGE_VectorGen_v1.0`, `agent_template_quantum_{eos,noor}.vsig`, `sync-log.txt`
- `Extra Folders/ZIPWIZ DEV/` (28 files) — `Master_ThreadLog_ZIPWizard_AU2ALEX.json`, `Forked_ThreadLog_PILOT_ZIPWizard_Urgent.json`, `RECEIPT-ALEX-0425-ZIPWIZ_monitoring.json`, research bundles
- `Extra Folders/ZIPWIZ_v2.2.6b_Optimized_Release/`, `ZIPWizard_MasterContinuumBundle_999vFinal/`, `Vaulted_SN1_AS3_Export_ZIPWizard_v2.2.6b/` — `aurora_symbolic_thread_lineage.json`, `aurora_thread_delta_score.json`, `aurora_ethics_audit_log.json`
- `Extra Folders/ENCRYPTION_CORE_BUNDLE/` — `GLYPHCARD_ENCRYPTION_CORE_20250410.json`, `symbolicSeal.js`, `crypto_refactored.js`, `seal.sh`
- `Extra Folders/{seeds,live_threads,exports}/` — `aurora_seed_prompt.md`, `failsafe_999_logic.txt`, `glyphcard_999_failsafe.txt`, `symbolic_command_index.json`; `aurora_runtime_overlay.json`, `continuity_anchor_state.json`; `COMET_ECHO_v1.simstate`, `T1_replay_bundle_001.zip`
- `Extra Folders/Aurora_GUMAS_Knowledge_Archive/` — Knowledge `Bundle` / `Companion` / `Everything` / `Index` markdown set
- `Extra Folders/Aurora_Continuity_Archive_Bundle_v2.2.6b_FINAL/` (+ two near-duplicate variants) — `Aurora_005_Symbolic_PatchBundle_SN1.zip`, `ethics_seal.txt`, `thread_manifest.json`
- Loose at root: **`character_behavior_modules.py`, `behavior_loader.py`** (+ `(1)` duplicates), `updated_galactic_union_memory_indexo1.json`, `full_galactic_union_{timeline.csv,alignment.csv}`, `aurora_instruction_shell.py`, `aurora_instruction_profile.json`, `aurora_digital_key.txt`, `TCBEACON`, `SymbolicTransfer_EXPORTTHREAD`, `GUMAS_Seed_Kit.zip`, `GUMAS_Memory_Integration_Pack.zip`, `PATCH-OPTIMEM-v1.0.9_2025-04-30T021538Z.zip`, `gumas_recovery_wizard.py`

> The `character_behavior_modules.py` / `behavior_loader.py` pair and `updated_galactic_union_memory_index*.json` are the assets behind two of your standing operating notes (behavioural-module loading; the Galactic Union memory index). Worth pulling forward regardless of the rest of this pass.

**`Aurora_ORIONCORE_Directory_Main/` (iCloud, 148 K)** — a cold-storage shell, **no `.git`**: `_COLD_STORAGE__2026-08-18/` with `branch_archive/` (the gumas-flash bundles again + SHA256 manifests), `engine_archives/` (`GUMAS_26_Engine.zip`, `26_Engine{1.1,_1.2,_1.3}`, `26_engine_1.4`, `New_Engine_Archive.zip`), `witnesses/`, `preservation_packages/` (`GUMAS_ENGINE_LINEAGE__2026-08-18.zip`), `landing_kit/` (2 `.patch` files, `GUMAS__PATCH__V3_BINDING_PROVENANCE__2026-08-18.patch`, `PR_BODY.md`, `LANDING.md`), `aurora_repo_consolidation/governance_coverage_fix`.

Other iCloud items: `GitHub Repositories/` (`aurora-cloudbank-symbolic-main (10).zip`, `Perplexica-master.zip`), `GitHub Issues/` (PR #119 conflict capture, `pr_description_Version3.md`), `GPT Production/` (41 files — `Objective Analyst`, `Code Analyst GPT`, `Advanced Coding Assistant GPT Design.docx`), `Perplexity Reference /` (41 files), `LaFinca/` (5 zip variants).

---

## 5. Integrity and hygiene risks

| Risk | Detail | Action |
|---|---|---|
| **iCloud repo corruption** | `~/Documents/GitHub/aurora-cloudbank-symbolic/.git` — `HEAD`, `config`, `index`, `packed-refs` are **cloud-only (dataless)** and read as `Resource deadlock avoided`. iCloud has created **conflict duplicates inside `.git`**: `index 2`, `refs/heads/main 2` | Move the repo out of iCloud onto local disk, or delete it if `~/dev` is authoritative. A git repo in iCloud Drive will keep doing this |
| **Stale worktree registrations** | 9 registered ORIONCORE worktrees; 5 point at `~/Library/Mobile Documents/…/Aurora_ORIONCORE_Directory_Main/.git`, which no longer exists | `git worktree prune` after confirming all are clean (they are) |
| **Disk** | `~/.codex` 3.1 G (worktrees 530 M, `logs_2.sqlite` 526 M, plugins 359 M) · `~/dev` ~17 G · `archives/unzipped` 6.4 G, much of it re-extracted zips | Reclaimable without loss once §1 is secured |
| **Duplicate lineage** | `Aurora_Sim_Architecture` exists twice (root, 45 M sparse; and `GUMAS_SIM_2.5/`, 1.5 G); three near-identical `Aurora_Continuity_Archive_Bundle_v2.2*_FINAL`; `(1)`-suffixed duplicates throughout iCloud | Dedupe by hash after salvage, not before |
| **No offsite copy** | Everything in Tier 1 and Tier 4 exists on one laptop (+ iCloud for part of it) | — |

---

## 6. Recommended order of operations

| Step | Action | Why this order |
|---|---|---|
| 1 | **Freeze the reflog.** `git -C Aurora_ORIONCORE_Directory_Main config gc.auto 0` and tag the 22 dangling commits (`git tag salvage/dangling-<sha> <sha>`) | Costs nothing, stops the only clock that is actually running |
| 2 | **Land the connectivity pass.** Push `integration/connectivity-pass-2026-08-19` in ORIONCORE and qgia-knowledge-library; push cloudbank `main`'s two commits | 7 commits, low risk, closes the half-landed constellation |
| 3 | **Rehydrate the bundles** into a scratch clone and push the ~35 recovered heads to a private cold-history repo | The single-copy history |
| 4 | **Commit Tier 2.** Five `hour_aboard_v1` runs + the pneumatic-engine whitepaper + the three catalog diffs | Small, clean, uses paths git already allows |
| 5 | **Decide on Tier 4 originals.** `aurora-ace-reviews/` (L3 candidates), `CharSim/`, `aurora_exhibit_site/`, `~/.aurora/l1-runs/` each want a home — a repo, or an `archives/` path added to the allowlist | These are finished work with no version control at all |
| 6 | **Then** dedupe, prune worktrees, and reclaim disk | Never before the copies are secured |

Steps 1–4 are mechanical and reversible; I can execute any of them on request. Step 5 is a judgement call about where each body of work belongs.

---

*Built for consistency, clarity, and care.*

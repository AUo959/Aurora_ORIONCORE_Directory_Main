# ZipWiz Salvage Inventory - 2026-06-15

Generated: 2026-06-15T22:08:03Z

Scope: root filesystem inventory plus live GitHub inspection for ZipWiz-related
material. This is a salvage and routing receipt only. It does not promote
archive, staging, recovered, or remote-only material into canon or runtime.

## Executive Status

- Root source change made: updated the versioned `zipwiz-governor` default scan
  roots so future default scans see the actual local ZipWiz packaging,
  CloudBank, harvest, chamber, and technical-reference surfaces.
- Root evidence artifacts created:
  - `reports/analysis/zipwiz_salvage_inventory__2026-06-15.md`
  - `reports/analysis/zipwiz_salvage_inventory__2026-06-15.json`
- GitHub owner surface confirmed live:
  - `AUo959/zip_wizard`
  - public repository
  - default branch `main`
  - `main` SHA `0d2a0e1d4a19833bc13abfbe5080ed35389ff3a8`
  - pushed at `2026-06-11T09:44:31Z`
  - 456 tracked blobs on main
- Current `zip_wizard` main tree contains `.env.example` and `.gitignore`, and
  does not contain a root `.env`.
- Historical `.env` exposure remains a restricted provenance note only. PR #11
  removed tracking of `.env`; I did not read, copy, or reproduce `.env`
  contents.
- ZipWiz governor validation after the default-root repair:
  - `REVIEW`
  - `CONDITIONAL`
  - 156 artifacts
  - 105 findings
  - 0 blocking findings
  - 1 warning: `W_EVOLUTION_VERSION_DATE_CONTRADICTION`

## Salvage Verdict

ZipWiz has three valid owner surfaces, each with a different promotion path:

1. `AUo959/zip_wizard`: active application/repository owner surface.
2. Root `skills/zipwiz-governor` plus `reports/analysis/non_can_reports`: root
   governance and evidence owner surface.
3. CloudBank ZipWiz runtime bridges/manifests: nested runtime owner surface,
   separate from root publication.

The dedicated `zip_wizard` repository should be treated as the primary product
surface for application code, docs, and archive-management UI/API work. The
root repo should retain governance receipts, scan tooling, and non-canonical
technical references. CloudBank should keep runtime bridge and constellation
contract material only when explicitly selected as the runtime integration
target.

## GitHub Inventory

### Dedicated Repo

`AUo959/zip_wizard`

- Visibility: public
- Default branch: `main`
- Main SHA: `0d2a0e1d4a19833bc13abfbe5080ed35389ff3a8`
- Repository size reported by GitHub: 97,656 KB
- Open standalone issues: none from the `issues?state=all` API after excluding
  pull requests.
- Current main root/tree highlights:
  - App and runtime: `client/`, `server/`, `shared/`
  - Documentation: `README.md`, `ARCHITECTURE.md`, `SECURITY.md`,
    `IMPLEMENTATION_SUMMARY.md`, `PR_INTEGRATION_SUMMARY.md`, `docs/`
  - Attached salvage assets: `attached_assets/`
  - Coverage artifacts: `coverage/`
  - Environment template only: `.env.example`

### Branches

| Branch | SHA | Status |
| --- | --- | --- |
| `main` | `0d2a0e1` | current default |
| `codex/conduct-full-code-review` | `c637acb` | open PR #10, include candidate |
| `dependabot/npm_and_yarn/npm_and_yarn-3c67cbb9cd` | `851867e` | open PR #9, dependency update |
| `copilot/build-advanced-archive-manager` | `073014c` | merged PR #7 history |
| `copilot/create-archive-manager-skeleton` | `f9f1234` | merged PR #6 history |
| `copilot/implement-vulnerability-scanner` | `d28e162` | merged PR #8 history |

### Pull Requests

| PR | State | Routing | Notes |
| --- | --- | --- | --- |
| #11 | merged | security provenance | Removed tracked `.env`; current main has `.env.example` only. PR body reports low risk and gitleaks-clean history, but I did not rerun gitleaks in this pass. |
| #10 | open | include candidate | Privacy/security hardening and modular home-view work. Diff stat: 15 files, 766 insertions, 354 deletions. Rebase onto current `main`, run tests, then merge or close intentionally. |
| #9 | open | dependency hygiene | js-yaml dependency bump. Diff stat: `package.json` and `package-lock.json` only. Rebase/test or close if superseded. |
| #8 | merged | included in repo history | Security/privacy system, vulnerability scanner, audit logging, RBAC, notifications. |
| #7 | merged | included in repo history | Advanced archive manager with streaming and virtualization. |
| #6 | merged | included in repo history | Extensible archive manager skeleton. |
| #1-#5 | closed | dependency history | Old dependency PRs, mostly closed/unmerged or superseded. |

### Attached Assets On GitHub Main

These are in `AUo959/zip_wizard/attached_assets` and should be routed as
backup/source evidence unless explicitly unpacked and promoted through a later
intake:

- `Aurora_Research_NoteCard_ZIPWizardCloud_1753943158314.txt`
- `Comprehensive_Chat_Archive_20250410_032233_1753967517177.zip`
- `Pasted--prompt-Build-an-advanced-ZipWiz-archive-management-application-with-the-following-comprehen-1754067213277_1754067213277.txt`
- `Pasted-git-pull-origin-main-no-edit-From-https-github-com-AUo959-zip-wizard-branch-main--1763655894553_1763655894553.txt`
- `RESEARCH_BUNDLE_ZIPWIZARD_CLOUD_V1_1753943158314.zip`
- `Snapshot_ZIPWizard_Continuity_Thread_Alex_v2.2.6b_1753943158314.zip`
- `T1_CHAIN__ZIPWizard__v2.2.6b__AU_TO_ALEX__LaunchAndExtend_1753943158314.zip`
- `ZIPWIZ DEV_1753943158314.zip`
- `ZIPWizard_MasterContinuumBundle_999vFinal_1753943158314.zip`
- `ZIPWizard_Status_Dashboard_AU2ALEX_ASCII_1753943158314.pdf`
- `ZipWiz Archive_1753943158314.zip`

### Cross-Repo GitHub Search

GitHub code search for `ZipWiz` / `zipwizard` under `user:AUo959` found
ZipWiz-related references in:

- `AUo959/zip_wizard`: primary app/product surface.
- `AUo959/Aurora_ORIONCORE_Directory_Main`: root ZipWiz governor and analysis
  receipts.
- `AUo959/aurora-cloudbank-symbolic`: CloudBank runtime bridge, scripts,
  constellation manifest, and staged optimizer core.
- `AUo959/CanonRec`: canon/private references. Do not mutate or promote from
  root by implication.
- `AUo959/AuroraOS`: historical constellation/Glyphnet references.
- `AUo959/cloudbank-quantum-en`: constellation reference.

The GitHub code-search output was capped at 100 results, so it should be
treated as a broad routing map, not a complete file manifest.

## Local Filesystem Inventory

The local path scan found 515 ZipWiz/ZipWizard path-match files. Categories:

| Category | Files | Bytes | Routing |
| --- | ---: | ---: | --- |
| `canonical_packaging_root` | 24 | 545,190 | include |
| `cloudbank_runtime_surface` | 7 | 45,315 | include candidate, nested repo only |
| `gumas25_bridge_or_harvest` | 2 | 22,140 | include as evolution evidence |
| `zipwiz_chamber_unzipped` | 130 | 2,149,238,160 | reference evidence, backup only unless later intake |
| `complete_archive_4_19` | 38 | 910,288 | backup only |
| `session_archives` | 27 | 3,570,263 | backup only |
| `gumas2_project_archive` | 75 | 1,325,265 | backup only except packaging-root subset |
| `archive_mirror_duplicates` | 69 | 3,818,232 | backup only |
| `reviewed_quarantine_duplicates` | 114 | 519,092,632 | quarantine/backup only |
| `staging_candidate` | 2 | 182,388 | include candidate, needs owner decision |
| `root_reports` | 1 | 27,059 | include as non-canonical reference |
| `zipwiz_governor_skill` | 18 | 156,937 | include |
| `other` | 8 | 4,908,206 | inspect before promotion |

## Local Include Candidates

### Root Governance And Packaging

Include in root control-plane scope:

- `skills/zipwiz-governor/`
- `reports/analysis/non_can_reports/ZIPWIZ_CHAMBER_TECHNICAL_REFERENCE.md`
- `projects/GUMAS_SIM_2.0/05_BUILD_TOOLS/ZipWiz_Packaging/New ZipWiz/L3_GOV__ZIPWIZ_PACKAGING_PROTOCOL__v0.1.0__2026-02-08__BAY02_0814.md`
- `projects/GUMAS_SIM_2.0/05_BUILD_TOOLS/ZipWiz_Packaging/New ZipWiz/L3_SCHEMA__ORION_BUNDLE_MANIFEST__v0.1.0__2026-02-08__BAY02_0814.schema.json`
- `projects/GUMAS_SIM_2.0/05_BUILD_TOOLS/ZipWiz_Packaging/New ZipWiz/L3_TEMPLATE__ORION_BUNDLE_MANIFEST__v0.1.0__2026-02-08__BAY02_0814.json`
- `projects/GUMAS_SIM_2.0/05_BUILD_TOOLS/ZipWiz_Packaging/New ZipWiz/ORION_PROPRIETARY_FORMAT_BUNDLE__v0.1.0__2026-02-08__BAY02_1012/STAGING_MANIFEST__ORION_PROPRIETARY_FORMAT_BUNDLE__v0.1.0__2026-02-08__BAY02_1012.json`

### CloudBank Runtime Surface

Include candidate only if the nested CloudBank repo is explicitly selected:

- `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/constellation-contracts/manifests/zipwiz-engine.manifest.json`
- `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/src/bridges/zip-wizard/bridge.ts`
- `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/services/command_node/modules/zipwiz.js`
- `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/scripts/zipwiz.py`
- `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/utilities/aurora_zipwiz_unified_launcher.py`
- `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/modules/opal2/staging/integration_ready/zipwiz_optimizer_core/`

### Bridge And Beacon Evidence

Include candidate only after choosing an owner surface:

- `archives/unzipped/ZipWiz_Chamber_6_28/aurora_bridge_output/zipwiz_bridge.py`
- `archives/unzipped/ZipWiz_Chamber_6_28/aurora_bridge_output/relay_handshake.py`
- `archives/unzipped/ZipWiz_Chamber_6_28/ZIPWIZ_Documents/ZIPWIZ Docs3/ZIPWizard_Universal_Beacon_Capsule.json`
- `archives/unzipped/ZipWiz_Chamber_6_28/ZIPWIZ_Documents/ZIPWIZ Docs3/ZIPWizard_Shuttlecraft_Beacon_Activated_FULL.beacon.json`
- `GUMAS_SIM_2.5/SIM_HARVEST_26/meta_narrative_summary_zipwizard_threadcore_functional_patch_thread.md`
- `_staging/orion_ord_review_fix/zipwiz_fixed.md`
- `_staging/orion_ord_review_fix/zipwiz_fixed.json`

## Checksums For High-Value Local Candidates

| Path | SHA-256 |
| --- | --- |
| `projects/GUMAS_SIM_2.0/05_BUILD_TOOLS/ZipWiz_Packaging/New ZipWiz/L3_GOV__ZIPWIZ_PACKAGING_PROTOCOL__v0.1.0__2026-02-08__BAY02_0814.md` | `456d60bf6c27712a4d38594a6c73aa2baf0bb97922130a9c3ff05891a8bc9d0c` |
| `projects/GUMAS_SIM_2.0/05_BUILD_TOOLS/ZipWiz_Packaging/New ZipWiz/L3_SCHEMA__ORION_BUNDLE_MANIFEST__v0.1.0__2026-02-08__BAY02_0814.schema.json` | `05512420df676cc8d05b63796f75378245aaf7032b813055473104faa5b75c97` |
| `projects/GUMAS_SIM_2.0/05_BUILD_TOOLS/ZipWiz_Packaging/New ZipWiz/L3_TEMPLATE__ORION_BUNDLE_MANIFEST__v0.1.0__2026-02-08__BAY02_0814.json` | `4579d108278ea9c76953a134ba077d6e17968a0d04cdee93efb1b43dcaf2d88e` |
| `projects/GUMAS_SIM_2.0/05_BUILD_TOOLS/ZipWiz_Packaging/New ZipWiz/ORION_PROPRIETARY_FORMAT_BUNDLE__v0.1.0__2026-02-08__BAY02_1012/STAGING_MANIFEST__ORION_PROPRIETARY_FORMAT_BUNDLE__v0.1.0__2026-02-08__BAY02_1012.json` | `708b2bff61dc1e1eb5cac8d72a80ec342625ddc260470c51d4a067ee553e2b9b` |
| `archives/unzipped/ZipWiz_Chamber_6_28/ZIPWIZ_Documents/ZIPWIZ Docs3/ZIPWIZ_OptimizerCore.py` | `9ce691506c9dccb519d8e06dea368a0971e3649bc5c81fce1e73a4396e5452be` |
| `archives/unzipped/ZipWiz_Chamber_6_28/aurora_bridge_output/zipwiz_bridge.py` | `51c65beb626fef83528637d7d00b5fe32ebeb24946c75119676c04c14eef69c0` |
| `archives/unzipped/ZipWiz_Chamber_6_28/aurora_bridge_output/relay_handshake.py` | `e55b81ede35efb8c770b67d2452b3c6d66b905addeffa8d98e4a9b7af858644a` |
| `archives/unzipped/ZipWiz_Chamber_6_28/ZIPWIZ_Documents/ZIPWIZ Docs3/ZIPWizard_Universal_Beacon_Capsule.json` | `9a4ef49603d67f36de318a48d8224233ff584195546755eb996779fdf0e5b368` |
| `archives/unzipped/ZipWiz_Chamber_6_28/ZIPWIZ_Documents/ZIPWIZ Docs3/ZIPWizard_Shuttlecraft_Beacon_Activated_FULL.beacon.json` | `7d49101a4e6c7f547d45c80b4aecaf2f3ebfab9e1dd11d67269ef6543bec6b91` |
| `GUMAS_SIM_2.5/SIM_HARVEST_26/meta_narrative_summary_zipwizard_threadcore_functional_patch_thread.md` | `c814b3fd527b1c53aaf98d2b0ad9f6f8c92c93e024729293d96833e4b00e37ad` |
| `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/src/bridges/zip-wizard/bridge.ts` | `9d808b3352f45dca5d70fa83784a1ce7b7afd8acc5789e1bb28f3038002f807d` |
| `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/services/command_node/modules/zipwiz.js` | `a9749d1059f90f024a1d59dea7387b29bde21f96fd5060bcf803c3c7efb9b2d6` |
| `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/scripts/zipwiz.py` | `d7c8fcc129c1e58ea77a0721e13286a13fe0c3fa3552df813933df919a1c2258` |
| `_staging/orion_ord_review_fix/zipwiz_fixed.md` | `4d969de0a9905be59b90f4b16cafa62257a4896f9043325512a22aad2b7b1279` |
| `_staging/orion_ord_review_fix/zipwiz_fixed.json` | `b33e21d5041c654530c8f4a7b6ec22ac02a71c6f8a765c03604b9891174c6fc9` |
| `reports/analysis/non_can_reports/ZIPWIZ_CHAMBER_TECHNICAL_REFERENCE.md` | `efb4644826440090c11396564811e8572296daf0ef0975d203be214707bf9e71` |

## Backup-Only Buckets

Keep these as provenance/archive evidence unless a later selective-integration
pass extracts specific files:

- Bulk ZIP archives under `archives/unzipped/ZipWiz_Chamber_6_28/`.
- Duplicates under archive mirrors.
- Reviewed quarantine duplicate material.
- Session archive copies.
- Complete Archive 4-19 copies.
- Current GitHub `zip_wizard/attached_assets/*.zip` bundles.
- Generated coverage HTML in `AUo959/zip_wizard/coverage/`.

## Restricted Material

- Historical tracked `.env` in `AUo959/zip_wizard` is restricted security
  provenance only.
- Current main no longer tracks `.env`, confirmed by GitHub tree and the
  no-checkout inspection mirror.
- Do not copy historical `.env` content into root reports, chat, docs, tests,
  or issue comments.
- Before any full promotion or history cleanup, run a redacted gitleaks scan in
  the selected owner repo. This pass did not rerun gitleaks.

## Completed Salvage Action

The versioned ZipWiz governor default roots were corrected:

- `skills/zipwiz-governor/scripts/zipwiz_rules.py`
- `skills/zipwiz-governor/references/canonical_roots.md`

Old defaults pointed at absent or stale locations:

- `GUMAS_SIM_2.0/05_BUILD_TOOLS/ZipWiz_Packaging`
- `Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`
- `ZipWiz_Chamber_6_28/ZIPWIZ_Documents`
- `Non_can_reports/ZIPWIZ_CHAMBER_TECHNICAL_REFERENCE.md`

New defaults are repo-relative and match this workspace:

- `projects/GUMAS_SIM_2.0/05_BUILD_TOOLS/ZipWiz_Packaging`
- `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`
- `GUMAS_SIM_2.5/SIM_HARVEST_26`
- `archives/unzipped/ZipWiz_Chamber_6_28/ZIPWIZ_Documents`
- `reports/analysis/non_can_reports/ZIPWIZ_CHAMBER_TECHNICAL_REFERENCE.md`

Validation:

- `python3 -m unittest skills/zipwiz-governor/scripts/test_zipwiz_governance.py`
  - Result: 20 tests passed.
- `python3 skills/zipwiz-governor/scripts/zipwiz_governance_scan.py --repo . --out-json /tmp/zipwiz_governance_default_after_patch_20260615.json --out-md /tmp/zipwiz_governance_default_after_patch_20260615.md`
  - Result: `REVIEW`, `CONDITIONAL`, 156 artifacts, 0 blocks.
- `make skills-check`
  - Result: expected two `zipwiz-governor` changes pending for installed
    runtime sync.
- `make skills-install`
  - First run failed under sandbox permissions while writing `~/.codex/skills`.
  - Escalated retry was rejected by the environment usage-limit gate, so
    installed-runtime sync remains a handoff item.

## Promotion Plan

1. Commit and push the root control-plane receipt and ZipWiz governor default
   root repair.
2. Sync installed skill runtime with `make skills-install` when approvals/usage
   allow.
3. In `AUo959/zip_wizard`, rebase and validate PR #10. Treat it as the next
   high-value live salvage candidate.
4. In `AUo959/zip_wizard`, rebase/test or close PR #9.
5. If the Python bridge is still desired, choose the owner surface first:
   `zip_wizard` app/package, CloudBank runtime bridge, or root governance tool.
6. Do not copy `archives/unzipped/ZipWiz_Chamber_6_28/aurora_bridge_output/*`
   into CloudBank until the `zipwiz` package/dependency surface is verified.
7. Do not unpack or promote GitHub attached ZIP assets without a separate
   selective-integration capsule.

## Handoff For Claude Code

Use this if Codex cannot complete publication:

1. From root, inspect:
   - `reports/analysis/zipwiz_salvage_inventory__2026-06-15.md`
   - `reports/analysis/zipwiz_salvage_inventory__2026-06-15.json`
   - `skills/zipwiz-governor/scripts/zipwiz_rules.py`
   - `skills/zipwiz-governor/references/canonical_roots.md`
2. Run:
   - `python3 -m unittest skills/zipwiz-governor/scripts/test_zipwiz_governance.py`
   - `python3 skills/zipwiz-governor/scripts/zipwiz_governance_scan.py --repo . --out-json /tmp/zipwiz_governance_default_after_patch_20260615.json --out-md /tmp/zipwiz_governance_default_after_patch_20260615.md`
   - `make skills-check`
3. If local runtime sync is desired, run `make skills-install` outside the
   Codex sandbox.
4. Commit root changes.
5. Push root `main`.
6. Handle `AUo959/zip_wizard` as a separate repo decision:
   - PR #10: rebase, test, merge or close.
   - PR #9: rebase/test or close if superseded.
   - Run redacted gitleaks before any history-sensitive work.

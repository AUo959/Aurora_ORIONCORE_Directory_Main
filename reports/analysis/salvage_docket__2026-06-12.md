# Aurora Salvage Docket - 2026-06-12

Status: control-plane salvage planning receipt. No candidate was promoted by this
report.

Scope:

- Root control plane: read reports, recovery indexes, and bounded iCloud scan
  outputs.
- Nested repos: inspected only as owner surfaces for fit and duplication.
- Excluded: active CloudBank/Hub edits that appear to belong to another
  platform or in-progress PR branch.

## Evidence Read

Primary root reports:

- `reports/analysis/aurora_salvage_report_latest.md`
- `reports/analysis/aurora_salvage_report_latest.json`
- `reports/analysis/ord_integration__2026-06-12.md`
- `reports/analysis/orion_station_spec_recovery__2026-06-12.md`
- `reports/analysis/unlanded_work_audit__2026-06-10.md`
- `reports/analysis/remote_branch_sweep__2026-06-11.md`
- `reports/analysis/integration_pass__2026-06-11.md`
- `reports/analysis/restricted_recovery_pretriage_packet__2026-06-07.md`
- `reports/state_briefs/executive_brief__2026-06-01.md`
- `reports/state_briefs/executive_brief__2026-06-01.json`
- `reports/automation/devkit_watch_2026-06-01.md`

Fresh commands run during docket construction:

```bash
python3 tools/workspace_recovery_index.py --summary
python3 tools/aurora_salvage_scan.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=_staging/orion_ord_review_fix/package \
  python3 -m pytest -q _staging/orion_ord_review_fix/package/tests -p no:cacheprovider
python3 tools/workspace_recovery_index.py \
  --root "/Users/travisstreets/Library/Mobile Documents/com~apple~CloudDocs" \
  --manifest /tmp/aurora_icloud_recovery_manifest_20260612.json \
  --report-out /tmp/aurora_icloud_salvage_candidates_20260612.json \
  --summary
```

Observed summaries:

- Root recovery index: `READY`; 2,436 files scanned; 100 retained from 1,070
  candidate records; target hints were CloudBank 56, root 32, spine 7,
  library 1, review-required 4.
- Root salvage scan: 100 contacts surveyed; 96 adrift; 13 high-value cargo;
  33 beacon signals; 35 derelicts; 15 debris; 4 registered; 1 uncommitted
  nested-repo surface; 0 unpushed surfaces.
- Bounded iCloud scan: 192 files scanned; 79 retained; target hints were
  CloudBank 24, root 20, spine 7, review-required 28. The broad CloudDocs
  filesystem is noisy, so this scan used a temporary bounded manifest and was
  not persisted as canonical metadata.
- ORD staging tests: `15 passed in 0.02s`.

## Promotion Rules For This Batch

- Survey never salvages. Promotion requires a later explicit gate in the owning
  repo.
- Staging, intake, archive, download, and backup material stays non-canonical
  until the owner surface accepts it through Git.
- Direct replay is disallowed for legacy packs, generated bundles, and broken
  historical code. Extract behavior or tests only after reconciliation.
- Restricted flags remain review labels unless a current secret or live
  credential indicator is confirmed.

## Priority Queue

### P1 - ORD Policy Family

Disposition: include, already staged for CloudBank integration.

Evidence:

- `_staging/orion_ord_review_fix/package/modules/ord/ord_policy_engine.py`
  hash `ac048ef9f2738875fc38450f47cee3bc4572ffb2f1582e40481b4c9aadb6db2a`
- `_staging/orion_ord_review_fix/package/modules/ord/ord_threshold_registry.py`
  hash `6bebb5d429ba3db4353cabcda2ff1fe69b2e1fd96f860b3e76c670460f058096`
- `_staging/orion_ord_review_fix/package/modules/ord/ord_inspection_policy.py`
  hash `b6bbaf7dfd7d7f561a83d3814f7d6a01263233a7a80f658f9a648a33079aed49`
- `_staging/orion_ord_review_fix/package/tests/test_ord_policy_engine.py`
  hash `668c0487f5e4a64746c0f74a8750de362a284140400ebe6622e267c9eb21ac57`

Current fit:

- `reports/analysis/ord_integration__2026-06-12.md` records this as pure
  uncommitted cargo now staged through CloudBank PR `#1016` on
  `feat/ord-policy-family`.
- Current CloudBank already has the `src/entities/fleet/` registry accessors
  for ORD-1/2/3 and Wisp.
- Local staged package tests pass: 15 passed.

Next gate:

- Watch or review CloudBank PR `#1016` when Claude Code is not actively editing
  that surface.
- After merge, decide whether an MCP dispatch adapter is still needed.
- Do not copy the legacy ORD source directly into runtime.

### P2 - ORD Legacy Fleet Source And Apple Notes Pack

Disposition: backup_only reference, behavior reconciliation.

Evidence:

- `_staging/apple_notes_recovery__2026-03-16/L1/ord_drone_fleet_v1.0.py`
  hash `affb09adea8838460bd28c9668e2d5dfc946399236f82849bfaf45298e428c88`
- The legacy recovered ORD dispatch pack is cited in
  `reports/analysis/ord_integration__2026-06-12.md` as a 1,349-line source
  family.

Current fit:

- This source contains earlier-generation behavior labels and object shapes
  such as `DeltaScout`, `Shadowfax`, `GammaSwarm`, `Wisp`, and
  `DroneDispatcher`.
- It overlaps with the cleaner policy-family staging package but is not itself
  the desired merge shape.

Next gate:

- Compare legacy behavior against the CloudBank PR `#1016` implementation.
- Extract missing tests, constants, or documentation only if they are not
  already represented.

### P3 - Quantum Agent Forge Protocol

Disposition: include as spec reconciliation, not direct runtime copy.

Evidence:

- `_staging/apple_notes_recovery__2026-03-16/L2/QUANTUM_AGENT_FORGE_PROTOCOL_v1.0.md`
  hash `52a571a9d5f1c0993897c51c12465d17c040b5d8241f61870aef5653e13bb39e`

Current fit:

- Current CloudBank already has a substantial `modules/quantum_forge/` owner
  surface and v3 tests.
- The recovered protocol is useful for lifecycle, retention, spawning,
  authorization, and governance comparison, not for blind copy.

Next gate:

- Reconcile protocol claims against current CloudBank forge tests and CanonRec
  doctrine.
- Route any normative changes through CloudBank implementation review and
  CanonRec only if they are canon-bearing.

### P4 - ZipWiz Python Bridge Candidate

Disposition: include candidate, blocked on owner-surface decision and security
review.

Evidence:

- `archives/unzipped/ZipWiz_Chamber_6_28/aurora_bridge_output/zipwiz_bridge.py`
  hash `51c65beb626fef83528637d7d00b5fe32ebeb24946c75119676c04c14eef69c0`

Current fit:

- Current CloudBank has a TypeScript stub at `src/bridges/zip-wizard/bridge.ts`
  plus multiple ZipWiz-adjacent scripts and launchers.
- The recovered Python bridge appears more functional, but it depends on a
  ZipWiz runtime/library surface that must be verified in its owning repo.
- Recent root reports already record a ZipWiz security cleanup pass and should
  remain the authority for credential disposition.

Next gate:

- Run `zipwiz-governor` or a focused security review before promotion.
- Decide whether the owner surface is CloudBank `src/bridges/`, the separate
  `zip_wizard` repo, or root control-plane tooling.
- Port behavior into typed tests first, then implementation.

### P5 - Canon Promotion Governance Pack

Disposition: include candidate for root workflow/docs reconciliation.

Evidence:

- `/Users/travisstreets/Library/Mobile Documents/com~apple~CloudDocs/Downloads/AURORA_GOVERNANCE__PACK__GITHUBOPS_GOVERNANCE_LAYER__v1.0__2026-06-12/AURORA_GOVERNANCE__WORKFLOW__CANON_PROMOTION_PIPELINE__v1.0__2026-06-12.md`
  hash `b481d63effd38d6559aa3bb8dfb07a0bfb4c7e78814d61e8ea57fb9a61a8b3b7`

Current fit:

- The pack's hard rules align with current root authority policy: no symbolic
  coherence override, no simulation-to-canon implication, no ethics claim
  without implementation evidence, and no generated artifact canon until
  promoted through Git.

Next gate:

- Diff against `AGENTS.md`, `README.md`, `docs/AURORA_INTERACTION_WARRANT_POLICY_v1.md`,
  and the existing workflow docs.
- Promote only non-duplicative rules or machine-checkable workflow hooks.

### P6 - GUI CloudHub And Recovery Utilities

Disposition: selective backup_only, possible extraction of tests or isolated
helpers after security review.

Evidence:

- `/Users/travisstreets/Library/Mobile Documents/com~apple~CloudDocs/Extras_Backups (Au)/aurora_instruction_shell.py`
  hash `4f868518172aff8d4072119c74c7c11a2366137a350290a236ecada55179be93`
- `/Users/travisstreets/Library/Mobile Documents/com~apple~CloudDocs/Extras_Backups (Au)/gumas_recovery_wizard.py`
  hash `f3c3de70fe93e792a8fa4b0273a260afbd8bb46b4f5922c96855e0ae81ff3bb0`
- `/Users/travisstreets/Library/Mobile Documents/com~apple~CloudDocs/Extras_Backups (Au)/Extra Folders/ZIPWIZ_v2.2.6b_Optimized_Release/Aurora_v2.2.6b_GUI_CLOUD_SNAPSHOT_20250407_FINAL/aurora_gui_cloudhub_fastapi.py`
  hash `7c394a8534180dbd63e33e02ea128967c756e939c2179804b54865082144d18d`

Current fit:

- Earlier root references classify GUI CloudHub material as non-canonical
  technical reference.
- `gumas_recovery_wizard.py` includes unsafe archive extraction behavior and
  must not be promoted directly.

Next gate:

- Treat these as design evidence and test-fixture candidates.
- Reimplement any useful behavior in the correct owner repo with path-safe
  archive handling and explicit tests.

### P7 - Biological Pneumatic Engine Prototype

Disposition: prototype review, owner/domain decision required before routing.

Evidence:

- `/Users/travisstreets/Library/Mobile Documents/com~apple~CloudDocs/Downloads/biological_pneumatic_engine.py`
  hash `20df62806321976e63b3c209750b51e67bb34413d4bfbf59b2dd72bab501fe33`

Current fit:

- The file appears to be a standalone engine prototype that may overlap with
  breathing, orchestration, or consciousness-model work.
- No owning repo or canon route was confirmed in this docket pass.

Next gate:

- Owner chooses target lane: CloudBank runtime experiment, CanonRec doctrine
  reference, or root recovered-prototype archive.
- If selected, build a small behavior inventory before code migration.

## Reject Or Defer

- `symbolicSeal.js`: reject direct promotion. Existing reports/catalog already
  identify the archived copy as broken on current Node.
- `crypto_refactored.js`: reject direct promotion. The iCloud candidate includes
  a hardcoded fallback cryptographic key and should only be used as a negative
  security fixture or reimplemented safely.
- Copied application internals and bundled third-party code: excluded from the
  bounded iCloud scan after false-positive discovery.
- Unrelated personal or non-Aurora CloudDocs material: excluded from this
  docket. Broad filesystem text search is too noisy for authoritative salvage.

## Integration Lanes

CloudBank/Hub:

- ORD policy family through PR `#1016`.
- ZipWiz bridge candidate after ZipWiz owner-surface and security review.
- Quantum Forge protocol reconciliation against current `modules/quantum_forge/`.
- PDP/biological engine only if the owner selects CloudBank as the runtime lane.

CanonRec:

- Canon-bearing station, Aurora Seed, and Quantum Forge doctrine only after
  canon reconciliation.
- Do not promote simulation or runtime behavior into canon by implication.

Root control plane:

- Canon promotion governance pack reconciliation.
- Salvage tooling improvements: whole-vessel detection, `mothballed`
  classification, better iCloud path scoping, and persistent exclusion rules
  for copied app internals.

## Immediate Next Commands

```bash
python3 tools/workspace_recovery_index.py --summary
python3 tools/aurora_salvage_scan.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=_staging/orion_ord_review_fix/package \
  python3 -m pytest -q _staging/orion_ord_review_fix/package/tests -p no:cacheprovider
```

When CloudBank is not actively occupied by Claude Code:

```bash
python3 tools/cloudbank_issue_broker.py status
```

Then inspect PR `#1016` and its CI before any Codex-side CloudBank mutation.

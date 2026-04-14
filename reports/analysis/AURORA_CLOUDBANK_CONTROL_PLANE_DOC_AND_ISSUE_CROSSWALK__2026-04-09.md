# Aurora CloudBank Control-Plane Doc and Issue Crosswalk

Generated: 2026-04-09
Updated: 2026-04-10
Scope: recent root control-plane documents related to `aurora-cloudbank-symbolic`, their supporting nested-repo evidence, and the GitHub issue/PR surfaces they appear to map to
Owner repo: `AUo959/Aurora_ORIONCORE_Directory_Main`
Method: root-first evidence review, then nested-repo corroboration, then GitHub issue/PR lookup

## Summary

The recent control-plane layer does contain relevant material, but most of it is governance, registry, and repo-state oriented rather than a new full structural audit.

The deepest root-level architecture mapping artifact remains:

- `docs/aurora_cloudbank_symbolic_architecture_discovery_report.md`

The most relevant recent root control-plane follow-ons are:

- `reports/analysis/UNFINISHED_WORK_TRIAGE__2026-04-09.md`
- `docs/workspace-map.md`
- `docs/ORION__REGISTRY__AURORA_PORTFOLIO_CANON__v1.0__2026-04-02.md`
- `docs/ORION__ADR_LITE__AURORA_PORTFOLIO_CANON_AND_ARCHIVE_DECISIONS__v1.0__2026-04-02.md`
- `reports/analysis/APRIL_8_PERPLEXITY_PACKET_RECONCILIATION__2026-04-09.md`

The strongest confirmed doc-to-GitHub conversions found in this pass are:

- Triplex Handshake mock-removal work
- CloudHub / MCP / HR integration work
- observability / Prometheus / telemetry work
- MCP bridge consolidation

After a follow-on de-duplication pass and live GitHub issue creation, the main control-plane structural gaps are now represented by:

- Issue `#634` for runtime topology and L3 communications authority
- Issue `#635` for stale docs / path drift ledger work
- Issue `#636` for multi-service API catalog governance

## Authority Notes

This report distinguishes between:

1. root control-plane truth
2. nested-repo supporting evidence
3. GitHub issue state
4. lower-authority imported analysis material

Do not treat lower-authority imported reports as canonical truth unless corroborated by code, current repo state, or a committed control-plane artifact.

## A. Recent Root Control-Plane Documents

### 1. `reports/analysis/UNFINISHED_WORK_TRIAGE__2026-04-09.md`

Role:
- most recent root analysis that directly flags `aurora-cloudbank-symbolic-main` as unfinished work

Relevant findings:
- nested repo is `main...origin/main [behind 18]`
- local modifications remain
- dedicated sync/triage pass is still needed

Use:
- current operational status receipt for the nested repo from the root control-plane perspective

### 2. `docs/workspace-map.md`

Role:
- current workspace registry snapshot

Relevant findings:
- `aurora-cloudbank-symbolic-main` is listed as an active nested repo
- remote is marked `configured`

Use:
- current root registry reference for nested repo presence and configured-remote status

### 3. `docs/ORION__REGISTRY__AURORA_PORTFOLIO_CANON__v1.0__2026-04-02.md`

Role:
- recent portfolio registry and canon-role declaration

Relevant findings:
- `Aurora_ORIONCORE_Directory_Main` is the portfolio root / control plane
- `aurora-cloudbank-symbolic` is the canonical platform hub
- portfolio truth lives in the control-plane repo
- platform truth lives in `aurora-cloudbank-symbolic`

Use:
- top-level role map for repo boundaries and canon classification

### 4. `docs/ORION__ADR_LITE__AURORA_PORTFOLIO_CANON_AND_ARCHIVE_DECISIONS__v1.0__2026-04-02.md`

Role:
- accepted decision record for portfolio structure

Relevant findings:
- core problem is role declaration drift, not lack of architecture
- reinforces control-plane truth vs platform truth separation

Use:
- compact governance decision record; not a structural gap ledger

### 5. `reports/analysis/APRIL_8_PERPLEXITY_PACKET_RECONCILIATION__2026-04-09.md`

Role:
- authority-drift reconciliation receipt for intake-side material

Relevant findings:
- canon-style overclaims were demoted to staging
- nested-repo path claims were treated as not fully verified in root

Use:
- evidence that the control-plane is actively correcting authority drift rather than silently promoting it

### 6. `reports/analysis/gitwiz/GITWIZ_SYNC_AUDIT__2026-04-09T225924Z.md`

Role:
- root Git publication receipt

Relevant findings:
- scanned `root` only
- root branch is ahead of upstream and clean

Use:
- publication-state receipt for the control-plane repo
- not a structural analysis of `aurora-cloudbank-symbolic`

## B. Older Root Document Still Carrying Structural Weight

### `docs/aurora_cloudbank_symbolic_architecture_discovery_report.md`

Role:
- still the deepest root-level structural mapping document

Core findings:
- repo is a multi-surface platform, not a thin symbolic archive
- docs and deployment scripts contain path drift and stale snapshots
- API catalog is monolith-scoped, not platform-scoped
- `mesh_api.js` is test-mounted but not proven production-mounted
- runtime topology for L3 communications remains unresolved

Recommended analytical follow-ons recorded there:
- runtime topology map
- stale docs / path drift ledger
- L3 communications surface map
- API catalog governance decision

Note:
- `reports/analysis/aurora_cloudbank_symbolic_architecture_discovery_report.md` is a duplicate copy of the same content

## C. Supporting Nested-Repo Documents

These are not control-plane documents, but they materially support or sharpen the control-plane view.

### 1. `docs/reports/SYSTEM_RETROSPECTIVE_REPORT.md`

Strong overlap with the control-plane discovery report:
- orphaned monitoring systems
- incomplete `hr_system` wiring
- OPAL2 as standalone API surface
- no unified API endpoint catalog
- recommendation to create architecture documentation

This is the strongest nested-repo counterpart to the control-plane discovery report.

### 2. `docs/aurora-phased-upgrade-roadmap.md`

Key value:
- explicitly states phases should be tracked in GitHub Projects or milestone issues
- includes observability, compliance, and bridge hardening as phased work

This is the clearest nested-repo planning document that appears intentionally GitHub-facing.

### 3. `docs/OPAL2_TREASURE_MAP.md`

Key value:
- explicit subsystem map for OPAL2
- points to `docs/operational/guides/OPAL2_EXPANSION_PLAN.md` as canonical OPAL2 planning material

## D. Lower-Authority Imported Analysis Material

### `reports/analysis/non_can_reports/AURORA_NEW_11_9_EXECUTIVE_SUMMARY.md`

This report is useful because it enumerates concrete enhancement gaps:

- L2 Meta-Agent Bridge not exposed
- HALO not runtime-active
- Drift to Prometheus gap
- fleet sync one-directional
- Triplex Handshake mock wiring

However:
- it is outside the control-plane canonical lane
- it makes stronger "production-ready" claims than I can verify from current root evidence alone

Use it as a lead sheet, not a canon declaration.

## E. GitHub Crosswalk

### Confirmed strong matches

| Theme | Root / repo evidence | GitHub state |
|---|---|---|
| Triplex Handshake mock replacement | lower-authority explicit gap sheet plus current repo work pattern | Issue `#527`, draft PR `#528`, follow-on issue `#529` |
| CloudHub / MCP / HR integration | control-plane discovery report and nested retrospective both point to fragmentation / incomplete wiring | Issue `#380` |
| Observability / Prometheus / telemetry | nested roadmap plus imported gap sheet | Issues `#384` and `#259` |
| MCP bridge consolidation | nested-repo bridge/config work | Issue `#382` resolved by merged PR `#411` |

### Confirmed related but not direct control-plane conversions

| Theme | GitHub state |
|---|---|
| drift / monitoring persistence and restart safety | Issue `#593` |

### Follow-on issue creation completed after de-duplication

| Theme | GitHub state |
|---|---|
| canonical runtime topology and L3 communications authority | Issue `#634` |
| stale docs / path drift ledger | Issue `#635` |
| multi-service API catalog governance | Issue `#636` |

Issue `#634` intentionally absorbs:

- `mesh_api.js` production mount question
- `EnhancedApiBridge` route/mount question
- authoritative L3 communications surface map

This keeps the unresolved L3 architecture surface in one ticket rather than splitting it into overlapping issues.

### Still not verified as direct GitHub issue conversions

I did not find direct issue matches for:

- fleet bidirectional sync as a standalone issue

## F. Current State Observed During This Pass

Current live nested-repo state observed from the workspace:

- repo path: `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`
- branch: `main`
- remote: `origin=git@github-aurora:AUo959/aurora-cloudbank-symbolic.git`
- status: `main...origin/main [behind 18]`

This matters because some older analysis artifacts in root were already stale on the day of capture regarding remote configuration. The control-plane discovery report's warning about historical snapshots proved accurate.

## G. Recommended Next Control-Plane Follow-On

If a new root report is needed, the highest-value control-plane successor to the March discovery report would be:

1. `RUNTIME_TOPOLOGY_MAP`
2. `PATH_DRIFT_LEDGER`
3. `DOC_TO_ISSUE_TRACE_MATRIX`

The third item is partially fulfilled by this report.

## H. Bottom Line

The recent control-plane documents do contain relevant `aurora-cloudbank-symbolic` material, but mostly as:

- portfolio governance
- repo boundary and canon-role declaration
- nested-repo status receipts
- authority-drift reconciliation

The March root discovery report remains the strongest structural mapping document.

The best confirmed doc-to-GitHub conversions found in this pass are:

- Issue `#380`
- Issue `#384`
- Issue `#259`
- Issue `#527`
- PR `#528`
- Issue `#529`
- Issue `#382` resolved by PR `#411`
- Issue `#634`
- Issue `#635`
- Issue `#636`

The remaining notable structural theme that is still not verified as issue-tracked from root control-plane evidence is:

- fleet bidirectional sync

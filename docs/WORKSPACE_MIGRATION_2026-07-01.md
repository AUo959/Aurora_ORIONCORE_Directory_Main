# Workspace Migration: iCloud Drive → Local Disk (2026-07-01)

**Audience:** every agent (Codex, Claude Code, or other) and every human
working in this workspace. Read this before trusting any absolute path you
find in configs, reports, session state, or your own memory/history.

**One-line summary:** on 2026-07-01 the entire Aurora/ORIONCORE workspace was
migrated from iCloud Drive to local disk at
`/Users/travisstreets/dev/Aurora_ORIONCORE_Directory_Main`. The iCloud copy
still exists but is deliberately inert. Work only in `~/dev`.

---

## 1. Canonical locations (current truth)

| Repo (registry name) | Canonical path |
|---|---|
| root (control plane) | `~/dev/Aurora_ORIONCORE_Directory_Main` |
| aurora-cloudbank-symbolic-main | `~/dev/Aurora_ORIONCORE_Directory_Main/GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main` |
| CanonRec | `~/dev/Aurora_ORIONCORE_Directory_Main/GUMAS_SIM_2.5/CanonRec` |
| DuelSim_v2.0 | `~/dev/Aurora_ORIONCORE_Directory_Main/GUMAS_SIM_2.5/DuelSim/DuelSim_v2.0` |
| qgia-knowledge-library-main | `~/dev/Aurora_ORIONCORE_Directory_Main/qgia-knowledge-library-main` |
| qgia-knowledge-spine-main | `~/dev/Aurora_ORIONCORE_Directory_Main/qgia-knowledge-spine-main` |

If `pwd` (or any path you are about to write to) contains
`Library/Mobile Documents`, **stop**: you are in a dead copy. Re-open the
`~/dev` path and re-read `catalog/session_state.json` from there.

## 2. Why the move happened (root cause, in detail)

The symptom was misdiagnosed for a while as a git credential problem. It was
not. Both repos authenticate over SSH (`git@github-aurora:...`) and auth
always worked.

Actual chain of failure:

1. The workspace lived in iCloud Drive with macOS **Optimize Mac Storage**
   enabled, meaning macOS may silently evict any file to a "dataless"
   placeholder and re-download it on access.
2. Docker Desktop (installed 2026-06-25) consumed ~20 GB of disk: a 12 GB
   failed model download in `~/.docker/models`, images, and ~4.5 GB of build
   cache.
3. Disk pressure triggered mass iCloud eviction — including files inside
   `.git/` (objects, index, refs).
4. Any git command touching an evicted file blocked while iCloud tried to
   re-materialize it: `git status` took 5+ minutes, `git push` hung ~10
   minutes or forever. A Docker container also bind-mounted the iCloud
   `reports/analysis` path, keeping the directory hot.
5. Fix: reclaimed the Docker disk, `rsync`'d the workspace to `~/dev`
   (initially excluding `.venv`, `node_modules`, `archives`), repointed the
   Docker stack at `~/dev`. Results: `git status` 5 min → 0.5 s, push 10 min
   → 2.5 s.

Corollary that stays true today: free disk was ~16 GB after cleanup.
Eviction pressure can recur, so **nothing under iCloud should ever be
treated as reliably materialized**.

## 3. What exactly was done

### 3.1 Initial migration (2026-07-01, first pass)
- `rsync` of the full workspace tree iCloud → `~/dev`, excluding `.venv`,
  `node_modules`, `archives`.
- Docker stack repointed to `~/dev`.

### 3.2 Archives brought local and deduplicated
- `archives/` (17.6 GB in iCloud, mostly evicted) was fully materialized into
  `~/dev/.../archives`, then deduplicated: 659 manifest-verified duplicates
  removed from `reviewed_quarantine_delete_candidates/` (8.66 GB) plus 386
  more via hash dedup (0.26 GB). `~/dev` totals ~10 GB.

### 3.3 Post-migration delta sync (2026-07-01, second pass)
A Codex session had **kept working in the iCloud path after the migration**,
so the two trees diverged. Six deltas were synced into `~/dev`, making it a
strict superset of the iCloud copy:
- `catalog/session_state.json` (Codex's updates, including a session claim)
- the PR-1060 blocker report
  (`reports/analysis/cloudbank_scenario_seed_adapter_pr_ready_blocker__2026-07-01.md`)
- SSMT maintenance files from 2026-06-30 missed by the first rsync.

Overwritten files got backups next to them named
`*.pre-icloud-sync-20260701.bak` (e.g.
`catalog/session_state.json.pre-icloud-sync-20260701.bak`).

### 3.4 iCloud copy made inert (guard rails)
So no agent silently resumes work there:
- Guard notices added in the iCloud tree: `MOVED_TO_LOCAL_DISK.md`, a root
  `CLAUDE.md`, and banners in root `AGENTS.md` and the nested CloudBank
  `CLAUDE.md`/`AGENTS.md`.
- Git disabled **fail-fast** in all six iCloud checkouts (root, both qgia
  repos, CanonRec, CloudBank, DuelSim_v2.0) by renaming
  `.git/HEAD` → `.git/HEAD.repo-moved-to-dev`. Any git command there now
  fails immediately with "not a git repository" instead of hanging.
- **Rollback** (if ever needed): move the file back —
  `mv .git/HEAD.repo-moved-to-dev .git/HEAD` in the affected checkout.
  Documented in the iCloud tree's `MOVED_TO_LOCAL_DISK.md`.
- Nothing was deleted. Deleting the iCloud tree (which propagates to all
  devices on the account) is an **open decision reserved for the Pilot**.

### 3.5 Settings and tooling repointed (2026-07-02, this cleanup)
- `~/.codex/config.toml`: the five `[projects.*]` trust entries that pointed
  at iCloud paths were replaced with their `~/dev` equivalents, and a trust
  entry for `qgia-knowledge-spine-main` was added. Backup:
  `~/.codex/config.toml.pre-dev-migration-20260702.bak`. Side effect: opening
  the iCloud copy in Codex now triggers a trust prompt — that is intentional
  friction.
- Governance skill roots converted to **repo-relative** form (resolved
  against `--repo` at runtime, so they survive any future relocation):
  - `skills/threadcore-governor/scripts/threadcore_rules.py`
    (`DEFAULT_CANONICAL_ROOTS`) and
    `skills/threadcore-governor/references/canonical_roots.md`
  - `skills/aurora-governance-orchestrator/scripts/orchestrate_governance.py`
    (all four `*_FALLBACK` root lists)
  - `skills/aurora-narrative-tone-governor/scripts/narrative_tone_scan.py`
    (two `GUMAS_SIM_2.0` roots gained the `projects/` prefix)
  - zipwiz-governor had already been converted earlier and was the pattern
    followed.
- Absolute-path examples updated to `~/dev` in:
  `skills/aurora-skill-finder/SKILL.md`, `skills/aurora-quantum-forge-ops/`
  (SKILL.md + `references/forge_api_contract.md`),
  `skills/aurora-selective-integration/references/protocol_mapping_v2_5.md`.
- `make skills-install` run; installed runtime at `~/.codex/skills` matches
  the repo `skills/` source again. Skill test suites pass
  (orchestrator 8/8, threadcore 13/13).
- `docs/AURORA_REVIEWER_ORIENTATION_v1.md` Rule 7 rewritten for the new
  environment; `reports/automation/aurora-package-watch/memory.md` got a
  migration note so future watch runs use `~/dev`.

## 4. Old-path → new-path mapping (for anything you find in history)

Two legacy path families appear in historical artifacts. Map them as follows:

| Legacy prefix | Maps to |
|---|---|
| `~/Library/Mobile Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main/<tail>` | `~/dev/Aurora_ORIONCORE_Directory_Main/<tail>` (same tail) |
| `~/Library/Mobile Documents/3L68KQB4HG~com~readdle~CommonDocuments/Documents/Aurora_ORIONCORE_Directory_Main/<tail>` | see per-tail table below — that container **no longer exists at all** |

The Readdle-era layout was absorbed into the repo with moved tails:

| Readdle-era tail | Current repo-relative path |
|---|---|
| `GUMAS_SIM_2.5` | `GUMAS_SIM_2.5` (unchanged) |
| `Aurora_Project_Cloudhub_Deploy` | `projects/Aurora_Project_Cloudhub_Deploy` |
| `GUI_Cloudhub` | `projects/GUI_Cloudhub` |
| `Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main` | `Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main` (root-level tree; the authoritative nested repo is `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`) |
| `GUMAS_SIM_2.0/...` | `projects/GUMAS_SIM_2.0/...` |
| `ZipWiz_Chamber_6_28/ZIPWIZ_Documents` | `archives/unzipped/ZipWiz_Chamber_6_28/ZIPWIZ_Documents` |
| `Non_can_reports/ZIPWIZ_CHAMBER_TECHNICAL_REFERENCE.md` | `reports/analysis/non_can_reports/ZIPWIZ_CHAMBER_TECHNICAL_REFERENCE.md` |
| `Auora2.5_DEV/...` | `projects/Auora2.5_DEV/...` |

Historical reports under `reports/` intentionally still contain legacy paths —
they are records of what happened, not live configuration. Do not "fix" them.

## 5. Standing rules for agents

1. **Never work in `Library/Mobile Documents`.** Check `pwd` / repo root at
   session start. The correct root is `~/dev/Aurora_ORIONCORE_Directory_Main`.
2. **Never write new absolute iCloud paths.** For governance roots, prefer
   repo-relative paths; the orchestrator's `resolve_roots()` also rebases
   stale absolute paths on the `Aurora_ORIONCORE_Directory_Main/` marker as a
   safety net, but don't rely on it for new work.
3. **Treat legacy paths in artifacts as historical data.** Use the mapping in
   §4 when you need the current location.
4. **Don't delete the iCloud tree.** That decision belongs to the Pilot and
   propagates across devices.
5. **Watch disk pressure.** If git or file IO suddenly hangs machine-wide,
   check free disk and Docker usage before suspecting credentials or repo
   corruption (`docker system df`, `df -h`).
6. When you finish a session, update `catalog/session_state.json` per the
   protocol in `AGENTS.md` — from `~/dev`, and push from `~/dev`.

## 6. Open items

- **Pilot decision pending:** disposition of 31 iCloud sync-conflict
  duplicates (`* 2.*`) in `projects/GUI_Cloudhub/` and `intake/` — full
  hashed inventory in
  `reports/analysis/icloud_conflict_duplicates__2026-07-02.md` (25 identical
  to base, 4 content forks, 2 orphans). No deletions performed.
- **Pilot decision pending:** delete or keep the inert iCloud tree
  (`~/Library/Mobile Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main`).
- `reports/analysis/aurora_*_latest.json` snapshots generated before the
  cleanup may still cite iCloud paths; they will self-correct on their next
  regeneration from `~/dev`.
- If Codex desktop was running while `~/.codex/config.toml` was edited
  (2026-07-02), it may rewrite the file on quit; if the iCloud trust entries
  reappear, re-apply §3.5 from the `.bak`.

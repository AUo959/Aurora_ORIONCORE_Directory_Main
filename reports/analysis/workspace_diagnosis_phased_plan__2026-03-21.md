# Workspace Diagnosis Phased Plan

Generated at: 2026-03-21
Scope: Root control-plane repo plus registered nested repos
Method: root verification, registry validation, git status/diff inspection, manifest/relocation correlation

## Executive Summary

The root control-plane verification surface passes, but the workspace is not operationally clean.

Highest-risk finding:
- `aurora-cloudbank-symbolic-main` is in severe destructive drift (`427` deletions, `31` untracked, `3` modified) while `HEAD` still matches the registered canonical SHA.

Secondary findings:
- The root control plane is tracking `20` L2 files under `GUMAS_SIM_2.5` outside the three registered nested repo boundaries.
- The planned-move backlog remains high (`252` entries), and one relocation record is inconsistent: `deep-research-report.md` is listed as already moved in the relocation plan but still exists at root and remains a manifest `planned_move`.

Verifier posture:
- `python3 tools/workspace_verify.py` returned `pass`
- `python3 tools/workspace_verify.py --check-determinism --exercise-relocation` returned `pass`

Interpretation:
- The control-plane manifests are internally consistent.
- The broader workspace still has repo-boundary, migration, and cleanup issues that root verification does not treat as blocking.

## Phase 1: Stabilize `aurora-cloudbank-symbolic-main`

Status: BLOCK

### Evidence

- Registered path and canonical SHA are recorded in [catalog/repo_registry.yaml](/Users/travisstreets/Library/Mobile%20Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main/catalog/repo_registry.yaml:6).
- The repo `HEAD` resolves to the same SHA: `42e0b9fb9f1e0e10a9091d595cf2811f2c14eacf`.
- `git status --porcelain` summary:
  - modified: `3`
  - deleted: `427`
  - untracked: `31`
- `git diff --stat` summary:
  - `430 files changed`
  - `128,916 deletions`

Deletion concentration by top-level area:
- `docs`: `136`
- `scripts`: `19`
- `venv_opal2`: `16`
- `src`: `15`
- `.security`: `13`
- `.github`: `11`
- `.aurora`: `9`

Untracked additions cluster around a new migration surface:
- `.aurora/*`
- `runtime/mesh/*`
- `deployment/launchd/*`
- `scripts/install_mesh_runtime_launch_agent.sh`
- `scripts/mesh-runtime-launch.sh`
- `scripts/uninstall_mesh_runtime_launch_agent.sh`

Concrete handoff defect:
- The new launchd plist points to an external automation script at [com.aurora.mesh-runtime.plist](/Users/travisstreets/Library/Mobile%20Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main/GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/deployment/launchd/com.aurora.mesh-runtime.plist:7) and uses the non-authoritative root-style path `Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main` for `WorkingDirectory` and logs at [com.aurora.mesh-runtime.plist](/Users/travisstreets/Library/Mobile%20Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main/GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/deployment/launchd/com.aurora.mesh-runtime.plist:11).
- The authoritative nested repo path is under `GUMAS_SIM_2.5`, as defined in [catalog/repo_registry.yaml](/Users/travisstreets/Library/Mobile%20Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main/catalog/repo_registry.yaml:7) and reinforced by [AGENTS.md](/Users/travisstreets/Library/Mobile%20Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main/AGENTS.md:57).
- The installer copies that plist as-is at [install_mesh_runtime_launch_agent.sh](/Users/travisstreets/Library/Mobile%20Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main/GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/scripts/install_mesh_runtime_launch_agent.sh:7).
- The repo-local launcher itself is coherent and repo-relative at [mesh-runtime-launch.sh](/Users/travisstreets/Library/Mobile%20Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main/GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/scripts/mesh-runtime-launch.sh:4), which makes the plist wiring mismatch more likely a migration defect than an intentional architecture.

Additional operational issue:
- `main` has no upstream configured in this nested repo, while `CanonRec` and `DuelSim_v2.0` track `origin/main`.

### Assessment

This looks like an unfinished migration from a broad legacy ops surface into a new persistent-state and mesh-runtime model, not random churn. That inference is supported by the clustered untracked `.aurora`, `deployment`, and `runtime/mesh` additions.

However, because the deletions are much larger than the replacement surface and the runtime handoff is misrouted, this repo should be treated as destructive drift until an intentional migration boundary is confirmed.

### Phase Actions

1. Freeze this repo before any cleanup commit or publication.
2. Capture a preservation receipt: `git status --short --branch`, `git diff --stat`, and a tar/backup of the current worktree if the state is valuable.
3. Decide whether the migration is intentional. If yes, write a repo-local migration spec before deleting more tracked surface.
4. Fix the launchd wiring to the authoritative nested repo path and repo-local launcher before treating the new runtime as active.
5. Configure an upstream for `main` only after the worktree state is stabilized.

## Phase 2: Reassert Root Control-Plane Boundaries

Status: REVIEW

### Evidence

- Root policy says this repo is metadata-first and that nested repo internals stay out of root Git history in [README.md](/Users/travisstreets/Library/Mobile%20Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main/README.md:12).
- Layer-separation rules are explicit in [AGENTS.md](/Users/travisstreets/Library/Mobile%20Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main/AGENTS.md:96).
- The root repo is currently tracking `20` files under `GUMAS_SIM_2.5` outside the three registered nested repos:
  - `13` files in `GUMAS_SIM_2.5/FORGE__GUMAS_v3.0__2026-02-19`
  - `7` files in `GUMAS_SIM_2.5/SIM_ENGINE_OUTPUTS`
- Modified root-tracked L2 files currently include:
  - `GUMAS_SIM_2.5/FORGE__GUMAS_v3.0__2026-02-19/l2_source_manifest.json`
  - `GUMAS_SIM_2.5/FORGE__GUMAS_v3.0__2026-02-19/l2_state.py`
  - `GUMAS_SIM_2.5/SIM_ENGINE_OUTPUTS/hourly_retrospective.py`

### Assessment

This is likely control-plane boundary drift. The root repo is carrying L2 engine/source artifacts directly even though the workspace policy positions the root as docs/manifests/tools only.

This is not necessarily invalid by itself, but it requires an explicit authority decision:
- either these files belong to a registered implementation repo
- or the root control plane needs an explicit exception recorded in manifests and docs

### Phase Actions

1. Decide the authoritative home for `FORGE__GUMAS_v3.0__2026-02-19` and `SIM_ENGINE_OUTPUTS`.
2. If they are implementation surfaces, route them into the correct nested repo boundary instead of root Git.
3. If they must remain in root temporarily, record that exception explicitly rather than relying on implicit drift.
4. Do not publish further L2 changes from the root repo until the authority decision is made.

## Phase 3: Reduce Relocation and Intake Drift

Status: REVIEW

### Evidence

- `catalog/workspace_manifest.yaml` currently contains `252` `planned_move` entries.
- `251` of those belong to `wave4_root_intake_cleanup_initial`.
- Planned-move kind counts:
  - `250` `intake_file`
  - `1` `intake_collection`
  - `1` `analysis_report`
- The similarly named root path `Aurora_Sim_Architecture` is still a root `planned_move` intake collection in [workspace_manifest.yaml](/Users/travisstreets/Library/Mobile%20Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main/catalog/workspace_manifest.yaml:164), which preserves the path hazard warned about in [AGENTS.md](/Users/travisstreets/Library/Mobile%20Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main/AGENTS.md:57).
- `_entropy_quarantine` remains protected review-before-delete in [workspace_manifest.yaml](/Users/travisstreets/Library/Mobile%20Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main/catalog/workspace_manifest.yaml:228).

Concrete inconsistency:
- The relocation plan records `deep-research-report.md` as already moved to `reports/analysis/deep-research-report.md` in [catalog/relocation_plan.json](/Users/travisstreets/Library/Mobile%20Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main/catalog/relocation_plan.json:74).
- The manifest still lists `deep-research-report.md` as a root `planned_move` with no `batch_id` in [workspace_manifest.yaml](/Users/travisstreets/Library/Mobile%20Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main/catalog/workspace_manifest.yaml:290).
- Both files currently exist, and their hashes differ:
  - root: `d578f42e53a2c4ce3c2bcbfc201a697baa6bc49620b6c9a76d0690ae7f983eb8`
  - reports copy: `95d5b5ca11a781943d4da78fee917a4b0c5b71ed263a6751f854c3efbd57a5c0`

### Assessment

Most of the backlog is straightforward intake debt, but `deep-research-report.md` is not just backlog. It is a real state inconsistency between the manifest, relocation plan, and filesystem.

### Phase Actions

1. Resolve `deep-research-report.md` first:
   - choose the authoritative copy
   - update the manifest/relocation state so the repo no longer claims both “moved” and “still pending”
2. Keep `_entropy_quarantine` intact until duplicate review is complete.
3. Process `wave4_root_intake_cleanup_initial` as a bounded batch rather than ad hoc root cleanup.
4. Clear the `Aurora_Sim_Architecture` root intake ambiguity only after confirming nothing there is being mistaken for the registered nested repo.

## Commands Executed

```bash
python3 tools/workspace_scan.py
python3 tools/workspace_plan_moves.py
python3 tools/workspace_verify.py
python3 tools/workspace_verify.py --check-determinism --exercise-relocation
python3 /Users/travisstreets/.codex/skills/aurora-repo-stabilizer/scripts/repo_stabilizer_scan.py --repo . --out /tmp/repo_stabilizer_scan.json --pretty
git status --short --branch
git diff --stat
git -C GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main status --short --branch
git -C GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main diff --stat
git -C GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main rev-parse --abbrev-ref --symbolic-full-name @{u}
git ls-files 'GUMAS_SIM_2.5/**'
jq/rg/nl inspection of workspace manifest, relocation plan, and runtime wiring files
```

## Notes

- Running `workspace_scan.py` and `workspace_plan_moves.py` refreshed generated control surfaces in the root repo. That is a diagnostic side effect, not a manual content edit.
- No code or policy fixes were applied in this phase. This report is a diagnosis and remediation receipt only.

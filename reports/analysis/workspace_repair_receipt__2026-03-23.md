# Workspace Repair Receipt

Date: 2026-03-23
Scope: Aurora / ORIONCORE workspace repair
Status: partial repair; broad deletion set still unresolved
Authority: derived diagnostic receipt, not a canon promotion artifact

## Repo Snapshot

### Root control plane

- Repo top level confirmed as `/Users/travisstreets/Library/Mobile Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main`
- `git status --short --branch`: `## main...origin/main`
- Counts: `modified=28 deleted=0 untracked=12`
- Diff is concentrated in `catalog/`, `docs/`, `reports/`, and a few root control-plane files
- `core.worktree` is unset
- `git sparse-checkout list` reports `fatal: this worktree is not sparse`

### `aurora-cloudbank-symbolic-main`

- Repo top level confirmed as `/Users/travisstreets/Library/Mobile Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main/GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`
- `HEAD` confirmed as `42e0b9fb9f1e0e10a9091d595cf2811f2c14eacf`
- `git status --short --branch`: `## main`
- Counts before and after local repair: `modified=9 deleted=427 untracked=37`
- Diff is driven by tracked deletions in:
  - `docs` (`137`)
  - `scripts` (`19`)
  - `venv_opal2` (`16`)
  - `src` (`15`)
  - `.security` (`13`)
  - `.github` (`11`)
  - `.aurora` (`9`)
- `core.worktree` is unset
- `git sparse-checkout list` reports `fatal: this worktree is not sparse`
- `.git` is a local directory, not a linked worktree file

### `CanonRec`

- Repo top level confirmed as `/Users/travisstreets/Library/Mobile Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main/GUMAS_SIM_2.5/CanonRec`
- `git status --short --branch`: `## main...origin/main`
- Counts: `modified=0 deleted=0 untracked=0`

### `DuelSim_v2.0`

- Repo top level confirmed as `/Users/travisstreets/Library/Mobile Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main/GUMAS_SIM_2.5/DuelSim/DuelSim_v2.0`
- `git status --short --branch`: `## main...origin/main`
- Counts: `modified=0 deleted=0 untracked=0`

## Drift Diagnosis

### Ruled out

- No sparse checkout in root or any named nested repo
- No `core.worktree` override in root or any named nested repo
- No `.icloud` placeholders found under `aurora-cloudbank-symbolic-main`
- No broken symlinks found under `aurora-cloudbank-symbolic-main`
- The specific alternate workspace path from the repair brief does not exist:
  - `/Users/travisstreets/Library/Mobile Documents/3L68KQB4HG~com~readdle~CommonDocuments/Documents/Aurora_ORIONCORE_Directory_Main`

### Duplicate-path findings

- The root intake path `/Users/travisstreets/Library/Mobile Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main` exists, but it only contains a narrow `runtime/mesh` subtree and does not contain any of the `427` Git-deleted tracked files from the named nested repo
- A second local clone exists at `/Users/travisstreets/Documents/Documents - Travis’s MacBook Air/GitHub/aurora-cloudbank-symbolic`
- That Documents clone is not a safe bulk-restore source:
  - `HEAD` is `43793c49c0d0a0f9b27b9d94786168b4eacfafe9`
  - its last commit is dated `2025-09-29 08:46:49 +0000`
  - its `remote.origin.url` is `https://github.com/AUo959/aurora-cloudbank-symbolic.git`
  - only `186` of the `427` deleted tracked paths exist there
  - shared tracked files differ materially from the CloudDocs repo state, for example `README.md`, `package.json`, and `services/command_node/modules/threadcore.js`

### Most likely interpretation

- The root and two other named nested repos do not show large destructive drift
- The large diff is isolated to `aurora-cloudbank-symbolic-main`
- Evidence in the current untracked stabilization notes indicates an in-progress local migration rather than a clean sync loss:
  - `docs/PHASE1_MESH_RUNTIME_BOUNDARY.md` explicitly records that historical docs are missing from the current worktree
  - `.aurora/PHASE1_STABILIZATION_RECEIPT__2026-03-21.md` records a partial path-handoff repair and explicitly leaves the broad deletion set unresolved
- Because no complete local mirror of the deleted set was found, and because the available alternate clone is divergent, a broad restore was not safe to perform without overwriting possible in-progress migration intent

## Applied Repair

### Local `.venv` wrapper repair in `aurora-cloudbank-symbolic-main`

- Repaired `59` stale `.venv/bin/*` wrappers that still embedded the non-authoritative root-style path:
  - old path: `/Users/travisstreets/Library/Mobile Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`
  - new path: `/Users/travisstreets/Library/Mobile Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main/GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`
- Confirmed afterward that no old root-style path references remain under `.venv/bin`
- Confirmed `.venv` remains ignored by Git:
  - `.gitignore:72:.venv/`

This repair was limited to local non-canonical virtualenv wrappers. It does not change tracked Git content.

## Validation

### `aurora-cloudbank-symbolic-main`

- `plutil -lint deployment/launchd/com.aurora.mesh-runtime.plist`: `OK`
- `zsh -n scripts/mesh-runtime-launch.sh`: `OK`
- `zsh -n scripts/install_mesh_runtime_launch_agent.sh`: `OK`
- `./.venv/bin/pytest --version`: `pytest 9.0.2`
- `./.venv/bin/uvicorn --version`: `Running uvicorn 0.41.0 with CPython 3.11.11 on Darwin`
- `cd <repo> && ./.venv/bin/python -c 'from pathlib import Path; from src.mesh.runtime import MeshRuntime; ...'`: `operational 6 22`
- `cd <repo> && ./.venv/bin/pytest tests/test_mesh_runtime_surface.py tests/test_mesh_runtime_api_surface.py -q`: `2 passed`
- Residual warning during API-surface tests:
  - FastAPI `@app.on_event` deprecation warnings remain in `src/servers/l2_integration_server.py`

### Root control plane

- `python3 tools/workspace_verify.py` still fails with a blocking manifest-coverage finding:
  - missing from manifest: `Aurora_Project_Context_Onboarding_Brief.pdf`
  - missing from manifest: `THREAD_MEMORY_COMPRESSION_BEACON_V2.zip`
  - missing from manifest: `thread_core_v_3.md`
  - missing from manifest: `threadcore_comprehensive_manifest_and_meta_narrative.md`

## Remaining Blockers

- `aurora-cloudbank-symbolic-main` still has `427` tracked deletions and `37` untracked paths
- No safe local source was confirmed for a bulk restoration of the deleted tracked set
- The repo has no upstream shown in `git status --branch`
- The current worktree contains evidence of partial migration intent, but not a complete migration record for the deleted surfaces
- Root workspace verification is still blocking on manifest coverage unrelated to the `.venv` wrapper repair

## Safe Next Actions

1. Classify the `427` deleted tracked paths in `aurora-cloudbank-symbolic-main` into:
   - restore now
   - retain deleted with written migration/deprecation record
   - environment-only artifacts that should remain absent
2. If restoration is approved, restore narrowly from the same repo history on a per-file or per-category basis rather than broad reset
3. Regenerate the root manifest surfaces after reviewing the four missing root artifacts
4. Migrate FastAPI startup/shutdown hooks to lifespan handlers when ready

# Aurora Workspace Management Repo

This root repository is the workspace control plane for
`Aurora_ORIONCORE_Directory_Main`.

It does **not** replace the three active nested Git repositories:

- `Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main`
- `GUMAS_SIM_2.5/DuelSim/DuelSim_v2.0`
- `GUMAS_SIM_2.5/CanonRec`

Phase 1 is metadata-first. The root repo tracks only workspace docs, manifests,
policies, reports, and tooling. Large archives, binary dumps, caches, and
nested repo internals stay out of root Git history.

## Start Here

- Human overview: [docs/workspace-map.md](docs/workspace-map.md)
- Source of truth: [catalog/workspace_manifest.yaml](catalog/workspace_manifest.yaml)
- Persistent overrides: [catalog/classification_overrides.yaml](catalog/classification_overrides.yaml)
- Nested repos: [catalog/repo_registry.yaml](catalog/repo_registry.yaml)
- Planned moves only: [catalog/relocation_plan.json](catalog/relocation_plan.json)

## Logical Zones

- `repos/`: logical home for active codebases; nested repos stay in place in phase 1
- `projects/`: structured non-repo project bundles
- `archives/`: cold and hot archive families plus quarantine targets
- `reports/automation/`: canonical destination for future automation outputs
- `reports/analysis/`: one-off workspace scans and verification outputs
- `docs/`: human navigation and operating guidance
- `catalog/`: machine-readable manifests and move contracts
- `tools/`: the only supported workspace reorganization surface
- `intake/`: ambiguous loose items pending review
- `_staging/`: rehearsals and rollback-safe staging

## Supported Commands

```bash
python3 tools/workspace_scan.py
python3 tools/workspace_plan_moves.py
python3 tools/workspace_apply_moves.py --batch-id wave3_small_intake_files_initial
python3 tools/workspace_verify.py --check-determinism --exercise-relocation
```

## Operating Rules

- Do not restore `.git_decommissioned_*`; it remains a rollback artifact only.
- Keep non-control content routed through `catalog/classification_overrides.yaml`; do not hand-edit the generated manifest.
- Do not move nested repos until their surrounding automation and scripts resolve
  through `catalog/repo_registry.yaml`.
- Do not delete duplicates directly. Plan quarantine moves first, verify hashes,
  then review before any hard delete.
- Keep tracked files below the workspace control-plane size ceiling enforced by
  `tools/workspace_verify.py`.
- `intake/`, `projects/`, `archives/`, `repos/`, and `_staging/` are organization
  zones, not tracked content stores in phase 1.

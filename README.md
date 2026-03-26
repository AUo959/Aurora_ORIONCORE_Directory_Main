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
- GFA posture: [docs/GFA_POSTURE.md](docs/GFA_POSTURE.md)
- Source of truth: [catalog/workspace_manifest.yaml](catalog/workspace_manifest.yaml)
- Repo authority policy: [catalog/repo_authority_policy.yaml](catalog/repo_authority_policy.yaml)
- Persistent overrides: [catalog/classification_overrides.yaml](catalog/classification_overrides.yaml)
- Nested repos: [catalog/repo_registry.yaml](catalog/repo_registry.yaml)
- Planned moves only: [catalog/relocation_plan.json](catalog/relocation_plan.json)

## Repo Authority Model

- Root is the control plane for the whole Aurora / ORIONCORE project workspace.
  That scope is broader than the repos currently registered today.
- Named repos keep their own Git and GitHub source-history authority.
- A nested local checkout is a working clone only. Local-only state is not
  published project state until it is committed and pushed.
- For a named repo, the published GitHub branch, normally `origin/main`, is the
  baseline unless an explicit publication flow says otherwise.
- `catalog/repo_registry.yaml` is the machine-readable list of repos currently
  registered for automation and audit. If a project repo is missing there, that
  is a registration gap in the control plane, not permission to ignore the repo
  boundary.

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
python3 tools/workspace_verify.py
python3 tools/workspace_verify.py --persist-report
python3 tools/workspace_verify.py --report-out /tmp/workspace_verify.json
python3 tools/workspace_verify.py --check-determinism --exercise-relocation
```

`python3 tools/workspace_verify.py` is side-effect free by default and prints a
JSON report to stdout. Use `--persist-report` to refresh the tracked
`reports/analysis/workspace_verify_latest.json` artifact, or `--report-out` to
write the report to an explicit path. The pre-commit hook continues to call
`python3 tools/workspace_verify.py --git-pre-commit` and only blocks commits on
blocking findings.

Specialized deploy / THREADCORE receipt utilities:

```bash
python3 tools/threadcore_deploy_accesskey.py validate /path/to/THREADCORE_DEPLOY_ACCESSKEY.json
python3 tools/threadcore_deploy_accesskey.py generate --symbolic-key THREADCORE_DEPLOY::EXAMPLE --associated-bundle THREADCORE_DEPLOY_SEAL_v1.zip --vector EXAMPLE::VECTOR --registered-node VISIBLE_NODE[01] --linked-echochain EXAMPLE::ECHOCHAIN
python3 tools/threadcore_visible_node.py validate /path/to/THREADCORE_VISIBLE_NODE_01.json
python3 tools/threadcore_visible_node.py generate --node-id VISIBLE_NODE[01] --vector EXAMPLE::VECTOR --linked-manifest EXAMPLE_manifest.json --patch-id EXAMPLE_patch.json --bundle EXAMPLE.zip --alias "Example Node"
python3 tools/threadcore_echochain_link.py validate /path/to/QEM_ECHOCHAIN_LINK_DRIFTNEXUS.json
python3 tools/threadcore_echochain_link.py generate --node EXAMPLE::VECTOR --linked-to EXAMPLE::ECHOCHAIN --glyph 🜃 --integration "Example linkage"
python3 tools/aurora_qem_patch_release.py validate /path/to/AURORA_QEM_SN1_PATCH_FULLTHREAD_v1.1.json
python3 tools/aurora_qem_patch_release.py generate --patch-code AURORA-QEM-SN1-PATCH-V1-FULLTHREAD --version v1.1 --vector-origin EXAMPLE::BASELINE --include "Example component" --glyph 🜃 --sealed-in EXAMPLE.zip --vector-released-as EXAMPLE::RELEASE
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

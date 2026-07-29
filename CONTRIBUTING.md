# Contributing to the Aurora Workspace Control Plane

This repository coordinates the Aurora workspace. It is not the CloudBank
application or the CanonRec authority repository, and changes must preserve
those Git and authority boundaries.

## Before opening a pull request

1. Read `README.md` and `docs/AURORA_REVIEWER_ORIENTATION_v1.md`.
2. Confirm that this root repository is the correct target. Runtime changes
   belong in `AUo959/aurora-cloudbank-symbolic`; canon changes belong in
   `AUo959/CanonRec`.
3. Do not silently promote draft, staged, recovered, or generated material to
   canonical status.
4. Regenerate generated control surfaces with their owning tools. Do not
   hand-edit `catalog/workspace_manifest.yaml`, `catalog/repo_registry.yaml`,
   `docs/workspace-map.md`, or the latest workspace-verification report.
5. Keep credentials, private personal material, caches, and unreviewed
   recovery artifacts out of commits and pull-request text.

## Local setup and validation

The root is an operator workspace, not an installable Python distribution.
Use the Makefile entry points:

```bash
make setup
make test-quick
python3 tools/workspace_verify.py
make devkit-check
make session-state-check
```

Run the narrower checks appropriate to the paths changed. Changes to a nested
repository must be validated and proposed from that repository's own Git
boundary.

## Pull-request expectations

A pull request should state:

- the repository and layer affected;
- what changed and why;
- the authority or evidence supporting the change;
- exact validation commands and results;
- remaining uncertainty or owner decisions;
- whether generated files were regenerated and by which command.

Public review does not relax Aurora's canon, provenance, or mutation gates.

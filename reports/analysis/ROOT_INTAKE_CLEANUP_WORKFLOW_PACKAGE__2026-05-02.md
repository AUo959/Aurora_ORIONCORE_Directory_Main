# Root Intake Cleanup Workflow Package

- Generated: 2026-05-02
- Scope: root control-plane cleanup only
- Package type: runbook plus receipt
- Target batch: `wave4_root_intake_cleanup_initial`

## Receipt

This package documents the next root intake cleanup workflow. It does not execute
moves, promote staged tooling, touch nested repos, or include the macOS starter.

Current root state:

- `python3 tools/workspace_verify.py --persist-report` last refreshed
  `reports/analysis/workspace_verify_latest.json` with `status: pass`,
  `finding_count: 0`, `blocking_count: 0`, and `warning_count: 0`.
- `git diff --shortstat` shows generated scan-refresh churn only:
  `12 files changed, 16 insertions(+), 16 deletions(-)`.
- `docs/workspace-map.md` lists two planned move candidates:
  `Aurora_Sim_Architecture` and `QGIA_SPACE_NAVAGATION_GUIDE.md`.
- `cmp -s QGIA_SPACE_NAVAGATION_GUIDE.md docs/QGIA_SPACE_NAVIGATION_GUIDE.md`
  returns `0`, so the top-level QGIA navigation guide is duplicate material and
  should stay intake-routed rather than canonical.
- `Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/runtime/mesh/mesh_runtime.stderr.log`
  changed during package preparation, from `32034699` bytes at
  `2026-05-01 22:39:39` to `32034906` bytes at `2026-05-01 22:39:49`.
  Treat this as active-runtime residue until a stability check proves otherwise.

## Cleanup Targets

Route these root-level planned move candidates only:

- `QGIA_SPACE_NAVAGATION_GUIDE.md` -> `intake/QGIA_SPACE_NAVAGATION_GUIDE.md`
- `Aurora_Sim_Architecture` -> `intake/Aurora_Sim_Architecture`

Do not use this package to change these excluded surfaces:

- `skills/agent-dispatcher/`
- `tests/test_agent_dispatcher_skill.py`
- `reports/analysis/agent_dispatcher_forward_test_receipt_2026-04-25.md`
- `tools/aurora_macos_starter/`
- `GUMAS_SIM_2.5/Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/workflow_output/skill_finder/`

## Execution Workflow

Run the baseline status check first.

```bash
git status --short --branch
```

Verify that the active mesh runtime log is stable before moving the
`Aurora_Sim_Architecture` tree.

```bash
python3 - <<'PY'
from pathlib import Path
import time

path = Path("Aurora_Sim_Architecture/aurora-cloudbank-symbolic-main/runtime/mesh/mesh_runtime.stderr.log")
samples = []
for _ in range(3):
    stat = path.stat()
    samples.append((stat.st_size, int(stat.st_mtime)))
    time.sleep(5)

for size, mtime in samples:
    print(f"{size} {mtime}")

if len(set(samples)) != 1:
    raise SystemExit("mesh runtime log is still changing; do not execute the move")
PY
```

Regenerate a temporary move plan immediately before dry-run. Keep these files in
`/private/tmp` so the planning gate does not dirty tracked control surfaces.

```bash
python3 tools/workspace_plan_moves.py \
  --out /private/tmp/root_intake_cleanup_relocation_plan.json \
  --aliases-out /private/tmp/root_intake_cleanup_path_aliases.csv
```

Dry-run the planned batch against the temporary plan.

```bash
python3 tools/workspace_apply_moves.py \
  --plan /private/tmp/root_intake_cleanup_relocation_plan.json \
  --batch-id wave4_root_intake_cleanup_initial \
  --report-out /private/tmp/root_intake_cleanup_dry_run.json
```

Require a zero-error dry-run before any execution.

```bash
python3 - <<'PY'
import json
from pathlib import Path

report = json.loads(Path("/private/tmp/root_intake_cleanup_dry_run.json").read_text())
if report.get("errors"):
    raise SystemExit(f"dry-run errors: {report['errors']}")
if not report.get("moved"):
    raise SystemExit("dry-run moved no paths")
print("dry-run ok")
PY
```

Execute only after explicit operator approval and only if the dry-run had zero
errors. The `--allow-unapproved` flag is required because the generated plan
marks these review moves as unapproved until the operator approves this package.

```bash
python3 tools/workspace_apply_moves.py \
  --plan /private/tmp/root_intake_cleanup_relocation_plan.json \
  --batch-id wave4_root_intake_cleanup_initial \
  --allow-unapproved \
  --execute \
  --report-out reports/analysis/workspace_apply_moves_wave4_root_intake_cleanup_initial_execute.json
```

After execution, regenerate the root control-plane surfaces and verifier receipt.

```bash
python3 tools/workspace_scan.py
python3 tools/workspace_plan_moves.py
python3 tools/workspace_verify.py --persist-report
```

Finish with non-mutating validation.

```bash
python3 tools/workspace_verify.py
git diff --check
```

## Blocked State

If the mesh runtime log changes during the stability check or if the dry-run
reports `pre_hash_mismatch` for `Aurora_Sim_Architecture`, stop. Record the
blocker as active-runtime residue and do not force the move.

The QGIA duplicate should remain in the same batch unless a future root tooling
change supports a reviewed subset move. Do not hand-move it outside the
workspace move tooling.

## Acceptance Criteria

- The package remains root-control cleanup only.
- No nested repo files are edited or moved by package creation.
- `workspace_apply_moves.py --execute` is not run during package creation.
- The root verifier passes after package creation.
- `git diff --check` reports no whitespace errors.

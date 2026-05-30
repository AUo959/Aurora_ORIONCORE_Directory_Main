# Workspace Recovery Tooling Receipt - 2026-05-20

## Scope

Persistent root-control-plane recovery tooling for early local Aurora /
CloudBank work. This receipt covers tool creation, report generation, docs, and
validation. It does not promote recovered material into canon and does not edit
nested repos.

## Added Surfaces

- Config: `catalog/recovery_index_manifest.json`
- Tool: `tools/workspace_recovery_index.py`
- Workflow: `docs/RECOVERY_INDEX_WORKFLOW_v1.md`
- Focused tests: `tests/test_workspace_recovery_index.py`
- Latest report: `reports/analysis/workspace_recovery_index_latest.json`

## Entrypoints

- `python3 tools/workspace_recovery_index.py`
- `python3 tools/workspace_recovery_index.py --summary`
- `python3 tools/workspace_recovery_index.py --persist-report`
- `make recovery-index`
- `make recovery-report`

## Initial Report Result

- Status: `READY`
- Mode: `read_only`
- Scanned files: `3491`
- Candidates retained: `100`
- Candidates discovered: `1168`
- Candidate cap applied: `true`
- Findings: `none`

Target hints in the retained candidate set:

- `aurora-cloudbank-symbolic-main`: `47`
- `root`: `36`
- `qgia-knowledge-spine-main`: `7`
- `qgia-knowledge-library-main`: `1`
- `review-required`: `9`

Source-status mix in the retained candidate set:

- `archive`: `44`
- `intake`: `31`
- `staged`: `22`
- `loose_root_intake`: `3`

## Validation

```bash
python3 -m pytest -q tests/test_workspace_recovery_index.py
python3 tools/workspace_recovery_index.py --summary
python3 tools/workspace_recovery_index.py --persist-report --summary
```

Results:

- focused recovery-index tests: `3 passed`
- live recovery index summary: `READY`
- persisted latest report size: `90728` bytes

## Promotion Rule

The recovery index is a review surface only. Every candidate remains
`pending_review` and `not_promoted` until a separate extraction decision names
the owner surface, compares against canonical repo state, validates behavior,
and leaves a receipt or PR.

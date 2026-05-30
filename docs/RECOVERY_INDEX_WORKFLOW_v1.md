# Aurora Recovery Index Workflow v1

This workflow turns the control-plane provenance rule into a repeatable
read-only tool lane. It exists because the root control-plane repo began as a
local file archive, while CloudBank already existed separately on GitHub. Early
local work may therefore contain valuable logic or design evidence that never
entered GitHub history.

## Scope

The recovery indexer is root-control-plane tooling. It does not move files,
write into nested repos, publish recovered material, or promote anything into
canon. Its job is to make recoverable material visible with stable evidence and
route hints.

Primary surfaces:

- Config: `catalog/recovery_index_manifest.json`
- Tool: `tools/workspace_recovery_index.py`
- Latest report: `reports/analysis/workspace_recovery_index_latest.json`
- Provenance rule: `docs/CONTROL_PLANE_PROVENANCE.md`

## Commands

Print a full JSON report without writing tracked files:

```bash
python3 tools/workspace_recovery_index.py
```

Print a compact summary:

```bash
python3 tools/workspace_recovery_index.py --summary
```

Refresh the tracked latest report:

```bash
python3 tools/workspace_recovery_index.py --persist-report
```

Run the focused tests:

```bash
python3 -m pytest -q tests/test_workspace_recovery_index.py
```

Run the root verifier after tooling or report changes:

```bash
python3 tools/workspace_verify.py
```

## Procedure

1. Run the indexer from the root control-plane repo.
2. Review candidates by `target_repo_hint`, `source_status`, `signals`, and
   `value_score`.
3. Treat every candidate as `pending_review` and `not_promoted`.
4. Compare any CloudBank-adjacent candidate against the canonical nested
   CloudBank repo before extraction.
5. Extract only into the owner surface named by the review decision.
6. Leave a receipt when extraction occurs, including source path, hash, target,
   validation command, and promotion status.

## Interpretation

`target_repo_hint` is a routing hint, not authority. It helps reviewers decide
where a recovered item probably belongs. The actual promotion decision still
requires repo evidence and validation.

`restricted_material_possible` means the candidate matched key, token, secret,
or credential language. Do not copy the raw contents into reports, prompts,
issues, or PRs without a separate handling decision.

`candidate_limit_applied` means the report retained the highest-scoring
candidates only. For focused recovery, narrow the manifest scan roots or raise
`max_candidates` for a local run.

## Promotion Gate

Recovery indexing is not canon promotion. Promotion requires:

- named target repo or root control surface
- rationale for extraction
- evidence that the material is absent, incomplete, or still valuable compared
  with the current canonical surface
- validation command and result
- receipt or PR that preserves the source path and hash

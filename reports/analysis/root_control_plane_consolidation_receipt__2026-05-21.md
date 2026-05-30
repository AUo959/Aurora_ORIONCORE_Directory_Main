# Root Control-Plane Consolidation Receipt - 2026-05-21

## Scope

Consolidated the current root-control branch after related work landed across
threads. Scope stayed in the root control plane. No nested repo files were
edited, and no intake, recovery, staged, or generated material was promoted
into canon.

## Consolidated Surfaces

- Command intent safety fields and tests:
  `tools/aurora_command_intent.py`,
  `plugins/aurora-command-grammar/skills/aurora-command-grammar/references/command-intent-envelope.schema.json`,
  `tests/test_aurora_command_intent.py`.
- Cross-artifact audit handoff wrapper:
  `plugins/aurora-command-grammar/skills/aurora-command-grammar/references/audit-handoff-record.schema.json`.
- Root integration gate:
  `tools/aurora_integration_gate.py`,
  `tests/test_aurora_integration_gate.py`,
  `make integration-gate`.
- Advisory recommendation engine:
  `catalog/recommendation_engine_manifest.json`,
  `tools/aurora_recommendation_engine.py`,
  `reports/analysis/aurora_recommendations_latest.json`.
- Confidence audit gateway:
  `catalog/contracts/aurora_confidence_audit_contract_v1.json`,
  `catalog/schemas/aurora_confidence_record.schema.json`,
  `docs/AURORA_CONFIDENCE_AUDIT_WORKFLOW_v1.md`,
  `tools/aurora_confidence_audit.py`,
  `reports/analysis/aurora_confidence_audit_latest.json`.
- Root discovery surfaces:
  `AGENTS.md`, `README.md`, `Makefile`, GitHub command grammar templates.
- Generated root inventory surfaces refreshed through the supported scan/plan
  flow, including `catalog/workspace_manifest.yaml`,
  `catalog/repo_registry.yaml`, `catalog/relocation_plan.json`,
  `docs/workspace-map.md`, and `reports/analysis/workspace_scan_summary.json`.

## Validation

Commands run during the consolidation sweep:

```bash
python3 tools/workspace_verify.py
python3 tools/aurora_integration_gate.py --summary
python3 -m pytest -q tests/test_aurora_command_intent.py tests/test_aurora_command_grammar_plugin.py tests/test_aurora_integration_gate.py tests/test_aurora_recommendation_engine.py tests/test_aurora_confidence_audit.py
python3 -m pytest -q tests
python3 tools/workspace_scan.py
python3 tools/workspace_plan_moves.py
python3 tools/aurora_recommendation_engine.py --persist-report --summary
python3 tools/aurora_confidence_audit.py score --claim-type analysis --text "Confidence audit tooling is available in the root control plane." --evidence-level verified_artifact --authority-ref docs/AURORA_CONFIDENCE_AUDIT_WORKFLOW_v1.md --evidence-ref tools/aurora_confidence_audit.py --persist-report --summary
python3 tools/workspace_verify.py --persist-report
python3 tools/aurora_integration_gate.py --summary
git diff --check
```

Results:

- `workspace_verify`: pass, `0` findings.
- `aurora_integration_gate`: pass; run mode `read_only`; nested repo mutation
  `false`.
- Focused command/integration/recommendation/confidence tests: `34 passed`.
- Root test suite under `tests/`: `133 passed, 23 skipped`.
- Recommendation report: `11` open advisory recommendations, `0` blocking,
  `11` approval-required.
- Confidence audit bootstrap report: pass, `1` record, `0` user alerts,
  score `0.93`.
- `git diff --check`: pass.

## Remaining Follow-Up

- Review restricted recovery candidates through the recovery workflow before
  any extraction or promotion.
- Keep system-level devkit items approval-gated: Homebrew, Docker, full Xcode,
  Rust, and Go.
- If any nested repo cleanup is desired next, name the repo explicitly and use
  `catalog/repo_registry.yaml` as the scope authority.

---
name: aurora-python-ingest-autowire
description: Automatically ingest new or changed Aurora Python modules into package entrypoints by scanning module symbols, validating adapter/fallback runtime contracts, and reconciling __init__.py exports with deterministic output. Use when users ask to auto-ingest new Python code or logic, wire imports/__all__, validate fallback adapters (for example pdp_v2_mvp/core/pneumatic_engine.py), or prepare Python module changes for safe integration. Do not use for governance or canonization gating tasks.
author: Aurora ORIONCORE
---

# Aurora Python Ingest Autowire

Run deterministic Python package ingestion for new code/logic updates, then surface actionable findings and export patches.

## Workflow

1. Confirm the package directory (for example `pdp_v2_mvp/core` or `pdp_v2_mvp/services`).
2. Run the ingestion scanner in dry-run mode first.
3. Review findings and export diffs in the JSON report.
4. Apply `__init__.py` rewiring only when proposed exports are valid.
5. Re-run package tests after applying ingestion updates.

## Commands

Dry run:

```bash
python3 scripts/ingest_python_package.py \
  --package-dir <absolute-or-relative-package-path> \
  --print-init-preview
```

Apply export rewiring:

```bash
python3 scripts/ingest_python_package.py \
  --package-dir <absolute-or-relative-package-path> \
  --apply-init \
  --strict
```

Write report to custom location:

```bash
python3 scripts/ingest_python_package.py \
  --package-dir <package-path> \
  --report-json <output-file.json>
```

## Output Contract

The ingestion script writes a JSON report with:

- `modules`: per-module scan output (symbols, adapter shape, parse errors)
- `existing_exports` and `proposed_exports`
- `missing_exports` and `extra_exports`
- `findings` and `severity_counts`
- `applied_init_update`

## Git Automation Policy

- Never require the user to run manual git commands.
- Run required git commands directly during execution (`status`, `add`, `commit`) when task scope implies integration completion.
- Commit only files touched by ingestion work, and use a deterministic commit message.
- Do not push unless explicitly requested.

## Boundaries

- Keep this skill focused on Python module ingestion and export wiring.
- Route governance/canonization requests to Aurora governance skills.
- Do not force lint/test policy changes in this skill.

## References

- Contract details: `references/ingest_contract.md`
- Trigger examples: `references/example_prompts.md`

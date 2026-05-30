---
name: aurora-exec-brief-pipeline
description: Build Aurora-first executive decision briefs from mixed data folders containing JSON, CSV, Markdown, and ZIP artifacts. Use when users ask to synthesize messy exports into leadership-ready status and risk summaries, pipeline mixed archives into one brief, produce markdown plus machine-readable findings, triage operational drift from logs/manifests/checkpoints, or generate an executive snapshot from Aurora artifacts. Not for governance gating, canon promotion, THREADCORE validation, ZIPWIZ governance, or script-surface hardening; route those requests to aurora-governance-orchestrator, aurora-canon-reconciler, threadcore-governor, zipwiz-governor, or aurora-script-governor.
author: Aurora ORIONCORE
---

# Aurora Exec Brief Pipeline

## Overview

Produce a concise executive brief and a structured JSON findings artifact from mixed Aurora data inputs. Prioritize recency and operational signal, preserve deterministic ranking, and redact likely sensitive tokens in outputs.

## Quick Start

Run the bundled CLI:

```bash
python3 /Users/travisstreets/.codex/skills/aurora-exec-brief-pipeline/scripts/build_exec_brief.py \
  --input-dir /path/to/folder \
  --emit-run-manifest
```

Outputs are written to `/path/to/folder/reports` by default:
- `executive_brief.md`
- `executive_brief.json`
- `run_manifest.json` (when requested)

## Workflow

### 1) Confirm scope and boundary

Use this skill for leadership-oriented synthesis from mixed files (`.json`, `.csv`, `.md`, `.zip`).

Do not use this skill for governance verdicts or canon governance work. Route those requests to specialized governance skills.

### 2) Run ingestion and analysis

Use optional controls when needed:

```bash
python3 /Users/travisstreets/.codex/skills/aurora-exec-brief-pipeline/scripts/build_exec_brief.py \
  --input-dir /path/to/folder \
  --out-dir /path/to/folder/reports \
  --max-files 200 \
  --include-globs "*.json,*.csv,*.md,*.zip" \
  --top-findings 12 \
  --strict \
  --emit-run-manifest
```

Behavior:
- Collect files recursively by glob.
- Exclude output folder from ingestion.
- Scan ZIP members without extracting to disk.
- Rank by recency, filename signal, and extension signal with deterministic path tie-break.

### 3) Read and report outputs

Read `executive_brief.md` first for a leadership summary, then use `executive_brief.json` for downstream automation or dashboards.

The markdown contract is stable:
- `Decision Snapshot`
- `Top Risks`
- `Operational Signals`
- `Recommended Actions`
- `Evidence Appendix`

### 4) Handle strict mode

When `--strict` is enabled, the script exits non-zero if high risks or parse failures are present. Use this for CI-style gating of briefing quality.

## Default audience and output

- Audience: Ops leadership.
- Output contract: Markdown brief plus JSON findings.
- Safety: likely secrets are redacted in snippets; pattern counts are preserved.

## References

- Schema: `references/brief_schema.md`
- Signal model: `references/signal_keywords.md`

## Workflow Position

- Upstream: `gumas-simulation-engine`, `aurora-quantum-forge-ops`, or mixed-data ingestion.
- Downstream: optional `aurora-narrative-tone-governor` before final leadership delivery when prose governance matters.
- Preset reference: `/Users/travisstreets/.codex/skills/aurora-governance-orchestrator/references/workflow_presets.md`.

## Trigger examples

Use this skill when requests resemble:
- "Build an executive brief from this Aurora archive folder."
- "Scan these JSON/CSV/Markdown/ZIP exports and summarize top risks."
- "Produce leadership-ready markdown plus machine-readable findings from this mixed data drop."
- "Create a decision snapshot from these manifests, logs, and status files."

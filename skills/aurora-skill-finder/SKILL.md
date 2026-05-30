---
name: aurora-skill-finder
description: Scan Aurora project trees and map code, logic, modules, scripts, and docs to the best-matching Codex skills with deterministic, precision-first scoring. Use when users ask to find which skill applies to a repo/path, surface skill-to-module routing, build a skill coverage map, reduce skill selection ambiguity, or audit where existing skills should be used before implementation. Not for implementing feature code directly, governance promotion verdicts, or canon reconciliation itself.
author: Aurora ORIONCORE
---

# Aurora Skill Finder

## Overview
Build a deterministic skill-map from repository evidence. Emit dual views:
- skill -> best matching modules/paths
- module/path -> best matching skills

Prefer precision over recall. Suppress weak/noisy matches and route borderline results to ambiguity review.

## Quick Start
Run the scanner with focused defaults:

```bash
python3 /Users/travisstreets/.codex/skills/aurora-skill-finder/scripts/scan_skill_fit.py \
  --root /Users/travisstreets/Library/Mobile\ Documents/com~apple~CloudDocs/Aurora_ORIONCORE_Directory_Main \
  --scope focused
```

Use explicit outputs when needed:

```bash
python3 /Users/travisstreets/.codex/skills/aurora-skill-finder/scripts/scan_skill_fit.py \
  --root /path/to/root \
  --scope focused \
  --catalog /Users/travisstreets/.codex/skills/aurora-skill-finder/references/session_skill_catalog.json \
  --out-json /tmp/skill_map.json \
  --out-md /tmp/skill_map.md \
  --min-score 0.45 \
  --max-skills-per-module 3 \
  --max-modules-per-skill 25 \
  --pretty
```

## Workflow
1. Resolve roots with `focused`, `repos-only`, or `full` scope.
2. Scan candidate files (`.py`, `.js`, `.mjs`, `.ts`, `.sh`, `.md`, `.json`, `.yaml`, `.yml`, `.html`, `.toml`).
3. Score each file against catalog entries using path/content keywords, path hints, filetype bias, structural boosts, boundary penalties, and archive/noise penalties.
4. Keep only matches above effective thresholds.
5. Emit:
- `skills_view` for top skill-aligned paths
- `modules_view` for per-module routing
- `ambiguity_queue` for close/uncertain decisions
6. Review ambiguity before downstream automation.

## Tuning
Adjust only the catalog and thresholds unless the scoring engine is clearly incorrect.

- Update `references/session_skill_catalog.json` to improve triggers.
- Use `references/aurora_core_skill_catalog.json` when you want Aurora-first routing with utility skills suppressed.
- Use `references/general_utility_skill_catalog.json` when you want only generic helper skills.
- Raise `--min-score` to increase precision.
- Lower `--min-score` only when missing known hotspots.
- Keep boundary penalties active to avoid cross-domain bleed.

## Guardrails
- Do not mutate scanned project files.
- Do not treat sub-threshold matches as authoritative.
- Do not promote low-confidence archive hits without manual confirmation.

## Outputs
Top-level JSON schema keys:
- `metadata`
- `scan_roots`
- `catalog`
- `excluded_paths`
- `skills_view`
- `modules_view`
- `ambiguity_queue`
- `stats`

Default output location (no `--out-*`):
- `<scan_root>/workflow_output/skill_finder/skill_map_<timestamp>.json`
- `<scan_root>/workflow_output/skill_finder/skill_map_<timestamp>.md`

## Resources
- `scripts/scan_skill_fit.py`: deterministic scanner and report generator.
- `scripts/validate_skill_package.py`: package validator for installed skills, catalogs, and referenced assets.
- `references/session_skill_catalog.json`: source of truth for session-skill mapping.
- `references/aurora_core_skill_catalog.json`: Aurora-core routing profile.
- `references/general_utility_skill_catalog.json`: generic utility routing profile.
- `references/scoring_rules.md`: scoring and penalty policy.
- `assets/templates/skill_finder_report.md`: markdown report template.

## Workflow Position

- Use this skill first when the correct specialist is unclear.
- If multiple governance domains are implicated, prefer `aurora-governance-orchestrator` over single-domain governor skills.
- Use `--catalog-profile aurora-core` when you want the package to behave as an Aurora-first product rather than a mixed utility bundle.

## Trigger Examples
Use this skill for prompts like:
- "Scan this project and tell me which Codex skills fit each module."
- "Find where threadcore-governor vs zipwiz-governor should apply."
- "Build a skill coverage map before we start implementation."
- "Surface the best skill routing for this Aurora codebase."

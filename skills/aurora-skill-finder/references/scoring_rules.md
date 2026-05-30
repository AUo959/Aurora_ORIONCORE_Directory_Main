# Aurora Skill Finder Scoring Rules

## Objective
Use deterministic, precision-first routing from repository evidence to the best matching Codex skill.

## Inputs
Each candidate file contributes:
- normalized relative path
- path tokens
- lightweight content snippet (text files only)
- extension/filetype
- root metadata (scope and root membership)

Catalog entry fields:
- `include_keywords`
- `exclude_keywords`
- `path_hints`
- `filetype_bias`
- `min_confidence_override` (optional)

## Score Composition
Base components:
- Include keyword hits in path: strong positive.
- Include keyword hits in content snippet: moderate positive.
- Path hint hits: strong positive for known hotspots.
- Filetype bias: small positive/negative adjustment.

Penalty components:
- Exclude keyword hits: strong negative.
- Archive/noise path indicators: negative.
- Report-heavy areas (`docs/operational/reports`): negative.

Structural boosts:
- Known deterministic hotspot -> skill alignments get an explicit boost.
Examples:
- `auto_selective_ingest_gate.py` -> `aurora-selective-integration`
- `duelsim_arena_game.html` -> `develop-web-game`
- `pdp_v2_mvp/core/pneumatic_engine.py` -> `aurora-python-ingest-autowire`
- Hotspot boosts can reach `1.0` only when the file has both path support and content support for that skill.
- Boosted single-channel matches are capped below max so canonical hotspots stay strong without flattening rank order.

Overlap adjustments:
- Prefer `aurora-governance-orchestrator` when multiple governance families appear in the same path/content context.
- Prefer `aurora-script-governor` over `aurora-repo-stabilizer` for setup/wrapper/cleanup/hazard work.
- Prefer `aurora-repo-stabilizer` over `aurora-script-governor` for hooks/CI/workflow/repo-ops work.
- Prefer `aurora-selective-integration` over `aurora-exec-brief-pipeline` for include/backup/reject triage.
- Prefer `aurora-exec-brief-pipeline` over `aurora-selective-integration` for executive brief and decision-snapshot work.

Final score:
- Clamp to `[0.0, 1.0]`
- Round to 4 decimals

Evidence ordering:
- Emit structural boost evidence first.
- Emit boost-cap and penalty decisions next.
- Emit path hints, path keywords, content keywords, and filetype bias after that.
- Keep evidence ordering deterministic so the top rationale lines explain the score-shaping decisions first.

Catalog profiles:
- `session`: all installed session skills.
- `aurora-core`: Aurora-first routing profile.
- `general-utility`: generic utilities only.

## Thresholding
Effective threshold per skill:
- `max(--min-score, skill.min_confidence_override if set)`

Default `--min-score`: `0.45`.

Precision-first policy:
- Emit only matches above threshold.
- Route near-threshold or close-rank conflicts to `ambiguity_queue`.

## Confidence Bands
- `high`: `>= 0.75`
- `medium`: `>= 0.60`
- `low`: `< 0.60` and `>= threshold`

## Ambiguity Rules
Add module/path to `ambiguity_queue` when:
- top two scores are close (`delta < 0.08`) near/above threshold, or
- no score passes threshold but best score is within 75% of threshold.

## Determinism
Keep ordering stable by:
- sorting roots, files, and skills before scoring
- sorting results by score desc then path/name asc
- avoiding nondeterministic random behavior

## Non-Goals
- Do not mutate scanned files.
- Do not auto-apply selected skills.
- Do not treat low-confidence archive hits as authoritative routing.

# Executive Brief JSON Schema

This file documents the JSON output contract for `executive_brief.json`.

## Top-level fields

- `summary` (object)
- `top_risks` (array)
- `key_signals` (array)
- `recommended_actions` (array)
- `evidence` (array)
- `sensitive_pattern_counts` (object)
- `analysis_scope` (object)

## `summary`

Required fields:
- `generated_at` (string, ISO-8601 UTC)
- `audience` (string; default `ops_leadership`)
- `input_dir` (string)
- `out_dir` (string)
- `source_files_considered` (integer)
- `source_files_selected` (integer)
- `files_scanned` (integer)
- `parse_failures` (integer)
- `high_risk_count` (integer)

## `top_risks[]`

Each item:
- `risk_id` (string)
- `severity` (`high` | `medium` | `low`)
- `title` (string)
- `impact` (string)
- `recommendation` (string)
- `evidence_count` (integer)
- `source_count` (integer)
- `sources` (array of strings)

## `key_signals[]`

Each item:
- `signal` (string)
- `value` (number|string)

## `recommended_actions[]`

Each item:
- `priority` (`P1` | `P2` | `P3`)
- `action` (string)
- `owner` (string)
- `rationale` (string)

## `evidence[]`

Each item:
- `source` (string)
- `type` (string)
- `signal` (string)
- `snippet` (string; redacted)

## `sensitive_pattern_counts`

Object map of pattern name to count. Common keys:
- `private_key_block`
- `api_key_assignment`
- `bearer_token`
- `openai_style_key`
- `aws_access_key`
- `long_token_like`

## `analysis_scope`

Required fields:
- `mode` (string; default `mixed_folder_scan`)
- `include_globs` (array of strings)
- `max_files` (integer)
- `ranking_strategy` (string)
- `tie_breaker` (string)
- `excluded_paths` (array of strings)
- `selected_sources` (array of strings)
- `zip_members_scanned` (integer)
- `zip_archives` (array of objects)

Each `zip_archives[]` item:
- `source` (string)
- `kind` (`zip`)
- `members_total` (integer)
- `members_scanned` (integer)
- `members_skipped` (integer)

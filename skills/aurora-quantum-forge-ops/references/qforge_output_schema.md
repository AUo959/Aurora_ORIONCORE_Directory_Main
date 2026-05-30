# QForge Output Schema

`quantum_forge_run_report.json` top-level keys:

- `run_summary`
- `validation_status`
- `engine_metrics`
- `event_breakdown`
- `capsule_metrics`
- `payload_context`
- `risk_flags`
- `artifacts`
- `analysis_scope`

## run_summary

- `status`: `ok` | `attention_required`
- `generated_at_utc`: ISO-8601 UTC
- `strict_mode`: boolean

## validation_status

- `ran`: boolean
- `exit_code`: integer | null
- `tests_passed`: integer | null
- `tests_total`: integer | null
- `passed`: boolean | null
- `summary_line_detected`: boolean
- `stdout_tail`: string
- `stderr_tail`: string

## engine_metrics

- `seed`: integer
- `turns_requested`: integer
- `turns_executed`: integer
- `total_v3_events`: integer
- `faction_count`: integer
- `leader_count`: integer
- `per_turn`: list of turn summaries

Each `per_turn` item:

- `turn`
- `event_count`
- `new_insurgencies`
- `civil_wars_started`
- `tech_breakthroughs`
- `migrations`
- `fragmentation_events`
- `negotiations_concluded`
- `intelligence_ops`

## event_breakdown

Object keyed by event type with integer counts.

## capsule_metrics

- `generated`: boolean
- `capsule_out`: string | null
- `generated_count`: integer
- `verification_requested`: boolean
- `verified_count`: integer
- `failed_count`: integer
- `verification_pass_rate`: float (when verification is run)
- `bundle_paths`: object (leader_id -> bundle_path)

## payload_context

- `qforge_manifest`: object | null
  - `path`
  - `module_id`
  - `engine`
  - `status`
  - `ethics_protocol`
  - `binding_layer`
  - `capabilities_count`
- `vector_injections`: object | null
  - `path`
  - `count`
  - `ids`
  - `tag_distribution`

## risk_flags

List of objects:

- `code`
- `severity`: `high` | `medium`
- `message`

## artifacts

- `json_report`
- `markdown_report`
- `v3_state_snapshot`
- `capsule_verification` (optional)
- `run_manifest` (optional)

## analysis_scope

- `forge_root`
- `out_dir`
- `qforge_manifest`
- `vector_injections`
- `seed`
- `turns`
- `run_validation`
- `generate_capsules`
- `verify_capsules`

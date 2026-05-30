# Module Manifest Schema

`--modules-json` expects a JSON array of module objects.

## Required (strict mode)

- `id` (string)
- `category` (string)
- `path` (string)
- `integration_path` (string)

## Recommended

- `redundancy_flag` (0 or 1)
- `telemetry` (array of strings)
- `notes` (string)
- `utility_score` (0.0-1.0)
- `improvement_score` (0.0-1.0)
- `maintenance_burden` (0.0-1.0)
- `conflict_risk` (0.0-1.0)
- `specialist` (string)
- `risk_notes` (string)
- `backout_plan` (string)
- `decision` (`include` | `backup_only` | `reject`) optional manual override

## Example

```json
[
  {
    "id": "agent_scaffolds",
    "category": "scaffold",
    "path": "kits/agents/scaffolds/",
    "integration_path": "characters/",
    "redundancy_flag": 0,
    "telemetry": ["adoption_rate", "bug_reports"],
    "notes": "Reusable archetypes for AI characters; no canon overwrite.",
    "utility_score": 0.86,
    "improvement_score": 0.71,
    "maintenance_burden": 0.22,
    "conflict_risk": 0.18,
    "specialist": "Elena"
  },
  {
    "id": "legacy_prompt_pack",
    "category": "prompt_pack",
    "path": "kits/legacy/prompts/",
    "integration_path": "archives/prompts/",
    "redundancy_flag": 1,
    "telemetry": ["usage_count"],
    "notes": "Legacy set retained for fallback only.",
    "utility_score": 0.48,
    "improvement_score": 0.31,
    "maintenance_burden": 0.41,
    "conflict_risk": 0.27,
    "specialist": "Naomi"
  }
]
```

## Optional triage override file (`--triage-json`)

Array of objects with fields:
- `module_id`
- `specialist`
- `decision`
- `risk_notes`
- `backout_plan`

If provided, these entries override auto-generated triage fields for matching `module_id`.

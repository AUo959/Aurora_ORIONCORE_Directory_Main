# Root Intake Visibility Receipt - 2026-05-18

## Scope

Root control-plane intake visibility for local early project material that is
safe on disk but not applied to GitHub as canonical repo content.

## Newly Surfaced Intake

- Path: `narrative_engine_spec_parameters_to_narrative_core_v_0.md`
- Disposition: `planned_move`
- Planned path: `intake/narrative_engine_spec_parameters_to_narrative_core_v_0.md`
- Git boundary: `none`
- Owner: `intake-review`
- Line count: `6721`
- Size: `182197` bytes
- SHA-256: `a4aedede0cdd2423eab718025504f5823924e67c96283d781db5d7519044de46`

## Control-Plane Action

Added a persistent `scan_policy: include` override in
`catalog/classification_overrides.yaml` so root scans include this file in
intake routing metadata instead of redacting it as `auto_scope_unknown`.

This receipt does not promote the source document into canon, copy it into a
nested repo, or publish the document body to GitHub. It records the local file
as reviewable intake pending a separate canonical-promotion decision.

## Next Review Decision

The likely next decision is whether this specification should stay as root
intake evidence, become a tracked root report/module, or be reworked into the
canonical CloudBank repository as implementation-facing specification material.

# L3 Bridge Mapping

ZIPWIZ Governor emits optional bridge output under `l3_bridge` with three entity arrays.

## `protocol_update`

Shape:
- `entity_type`: `protocol_update`
- `protocol`: `zipwiz_packaging`
- `protocol_docs`: files used for protocol evidence
- `drift_rules`: triggered protocol-related rule IDs
- `generated_at`: timestamp

## `schema_definition`

Shape:
- `entity_type`: `schema_definition`
- `schema_family`: `zipwiz_manifests`
- `artifact_count`: count of bundle/staging artifacts
- `variant_rules`: schema drift/variant rule IDs
- `generated_at`: timestamp

## `anchor_rule`

Shape:
- `entity_type`: `anchor_rule`
- `anchor_seed_expected`: `EOS_SEED_ORION`
- `ethics_protocol_expected`: `Picard_Delta_3`
- `violations`: count of anchor/ethics-related findings
- `evolution_milestones`: number of timeline events
- `generated_at`: timestamp

This bridge is standalone and does not import any external runtime tooling.

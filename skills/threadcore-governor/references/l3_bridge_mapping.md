# L3 Bridge Mapping

The scanner can emit optional bridge entities aligned with L3 canon semantics.

## protocol_update

Fields:

- `protocol_name`
- `version`
- `change_description`
- `affected_layers`
- `backward_compatible`
- `anchor_impact`

THREADCORE mapping:

- protocol defaults to `Picard_Delta_3`
- version derived from dominant artifact versions
- compatibility inferred from blocking findings

## schema_definition

Fields:

- `schema_name`
- `version`
- `fields`

THREADCORE mapping:

- schema captures observed family contracts from scan output

## anchor_rule

Fields:

- `anchor_id`
- `rule_description`
- `affected_layers`

THREADCORE mapping:

- anchor ID defaults to `THREADCORE::VISIBLE_NODE.ORION.*`
- description references registry governance requirements

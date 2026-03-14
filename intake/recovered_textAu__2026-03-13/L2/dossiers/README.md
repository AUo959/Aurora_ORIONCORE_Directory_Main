# L2 Schema Dossiers

Status: staged, schema-based, not yet promoted  
Prepared from:

- `../01_galactic_union_canon_reconciliation.md`
- `../02_galactic_union_character_roster.md`
- `../03_galactic_union_mechanics_and_models.md`

## Contents

- `l2_polity_dossiers__recovered_textAu.json`
  - validator-friendly polity dossiers
- `l2_character_dossiers__recovered_textAu.json`
  - validator-friendly character dossiers
- `l2_ship_dossiers__recovered_textAu.json`
  - validator-friendly ship dossier set
- `l2_mechanic_registry__recovered_textAu.md`
  - structured mechanic dossiers held as a registry draft
- `validation/`
  - validation receipts for the `polity`, `character`, and `ship` dossier sets

## Notes

- All certainty tags remain `STAGING` or `UNCONFIRMED`.
- Name normalization follows the current engine where corroboration exists.
- The mechanic registry uses the intended mechanic schema, but the current validator has an
  `entity_kind` inconsistency for L2 mechanics, so it is staged separately from the validated
  dossier files.
- Validation status at creation time:
  - polity dossiers: pass
  - character dossiers: pass
  - ship dossiers: pass

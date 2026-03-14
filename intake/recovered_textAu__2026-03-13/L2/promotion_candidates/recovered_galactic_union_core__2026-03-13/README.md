# Recovered Galactic Union Core Promotion Candidate

Layer: L2  
Status: CANON_PROMOTE candidate set  
Prepared: 2026-03-13

## Purpose

This packet isolates the highest-confidence portion of the recovered Galactic Union material
and prepares it for downstream canon promotion review.

## Included

- `promotion_polities__recovered_galactic_union_core.json`
- `promotion_characters__recovered_galactic_union_core.json`
- `promotion_manifest.json`
- `recommendations.json`
- `REPORT__Recovered_Galactic_Union_Core__CANON_PROMOTE__2026-03-13.md`
- `DRIFT_LOG__Recovered_Galactic_Union_Core__2026-03-13.md`
- `evidence_receipt.json`
- `CONTEXT_SCAN_SUMMARY__Recovered_Galactic_Union_Core__2026-03-13.md`
- `evidence_receipt_with_context_scan.json`
- `validation/`

## Scope Of Promotion

### Included entities

- 6 polities
- 10 characters

These are the entities with the strongest combination of:

- validated schema completeness
- corroboration against later engine files
- clean layer integrity
- explicit user-reviewed promotion intent for this packet

### Excluded from this packet

- `POL-AI-HARDLINE-001`
- `CHAR-GU-DRAYEN-01`
- `SHIP-GU-JUDICATOR-01`
- the `Judicator Prime` operational cast beyond the core Union leadership
- the mechanic registry, which remains staged because of the current validator mismatch

## Validation Status

- promotion polities: pass
- promotion characters: pass
- combined promotion entities: pass
- combined promotion entities with context scan: pass

## Recommendation Status

`recommendations.json` records the reconciler advisor output for every included entity.
Each included entity currently recommends `CANON_PROMOTE` under the clean-validation,
no-conflict, user-reviewed assumptions used for this packet.

## Context Scan Status

The packet has now also been checked with a broader context-aware scan rooted at
`GUMAS_SIM_2.5`.

- result: 16 passed, 0 blocked
- warning: 1 expected alias collision around `Prime Construct` as both polity alias and character name

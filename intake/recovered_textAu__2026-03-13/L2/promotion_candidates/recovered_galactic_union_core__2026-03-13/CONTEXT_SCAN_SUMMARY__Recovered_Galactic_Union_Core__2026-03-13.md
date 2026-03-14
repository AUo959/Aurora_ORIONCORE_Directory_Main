# Context Scan Summary

Date: 2026-03-13  
Scope: `promotion_entities__recovered_galactic_union_core.json`  
Context root: `GUMAS_SIM_2.5`

## Result

- entities checked: 16
- passed: 16
- blocked: 0
- evidence verdict: `PASS`

## Key Outcome

The broader context-aware scan did not surface any blocking conflicts for the 16-entity
promotion pack when checked against the preferred canonical roots under `GUMAS_SIM_2.5`.

## Observed Warning

One warning was emitted:

- `BATCH_DUPLICATE` for `Prime Construct`
  - cause: the polity dossier uses `Prime Construct` as an alias while the character dossier
    uses `Prime Construct` as its canonical name
  - interpretation: expected and acceptable if the project intentionally models both the
    sovereign AI polity and its primary sovereign actor as linked but distinct entities

## Evidence

- Context-scan validation receipt: `96ed9bd4990d3aae43a262bd08d9718af06397db07782ab4c1bde4dd9b90c5d3`
- Context-scan evidence receipt: `bf542e62426ac750cd3c87c70b65f6149001cdb72b9d2af449b02d8340108093`

## Reviewer Note

User review confirmed that `Prime Construct` is a canonical name. The alias overlap is therefore
accepted for this packet and is not treated as a blocker to promotion or commit.

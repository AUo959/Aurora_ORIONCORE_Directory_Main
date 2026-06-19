# L2 Scenario Seed Catalog Artifact - 2026-06-18

Status: root-control-plane artifact created. No CloudBank or CanonRec files were
edited.

## Inputs

- `reports/analysis/l2_scenario_seed_catalog_extraction__2026-06-15.md`
- `reports/analysis/l2_scenario_seed_catalog_extraction__2026-06-15.json`

## Outputs

- `catalog/l2_scenario_seed_catalog.json`
- `catalog/contracts/l2_scenario_fixture_generator_contract_v1.json`
- `catalog/schemas/l2_scenario_seed_catalog.schema.json`
- `docs/L2_SCENARIO_SEED_CATALOG_WORKFLOW_v1.md`
- `tests/test_l2_scenario_seed_catalog.py`

## What Changed

- Promoted the June 15 extraction report into a maintained root catalog artifact.
- Preserved 87 `v0.2.15` cards as active maintained root entries.
- Incorporated the five complete `v0.2.2` lineage-only Dune cards as maintained
  root entries by owner override:
  `SCN-0103`, `SCN-0105`, `SCN-0106`, `SCN-0107`, and `SCN-0108`.
- Normalized the fusion table and card wiring into ID-first references with
  explicit `ready`, `manual_review`, and `unresolved` statuses.
- Added fixture-ready blueprints for the high-value shortlist, with first
  candidates `SCN-0903`, `SCN-0708`, and `SCN-0805`.
- Added explicit Dune-inspired thematic coverage so `SCN-0101` through
  `SCN-0108` are eligible for root fixture candidates. The `v0.2.2` cards keep
  source-version provenance and remain root-catalog-only, not canon/runtime.
- Added a root generator contract that defines candidate fixture shape, output
  path policy, validation rules, and non-promotion boundaries.

## Reference Normalization

- Fusion pairings: 34 total.
- Fusion pairings ready after canonical handle normalization: 20.
- Fusion pairings requiring manual review because an ID label points at a
  different current card concept: 14.
- Unresolved fusion pairings: 0.
- Wiring entries with references: 10.
- Unresolved wiring entries: 1.

The unresolved wiring entry is `SCN-0407` referencing `SCN-0208 (The Small
Become Essential)`. No `SCN-0208` card exists in the available HTML lineage
captured by the June 15 extraction.

## Integrity Note

The primary source hash confirmed by the June 15 report table and a fresh
`shasum -a 256` run is:

`59d9caa58f3dd424a7c92d0a826c7ee094161741c5c80ff5267114ccd8845dfe`

The older selective-integration capsule subfield carried a different source
hash. The maintained catalog records this as a stale capsule hash and uses the
source table plus fresh hash as the normalization basis.

## Validation

Run:

```bash
python3 -m unittest tests/test_l2_scenario_seed_catalog.py
python3 tools/workspace_verify.py
```

The catalog and contract do not create fixture output files yet. A future
generator pass should emit root candidate files under
`catalog/generated_watch_scenarios/` and a receipt under `reports/analysis/`,
then separately request owner approval before any CloudBank or CanonRec work.

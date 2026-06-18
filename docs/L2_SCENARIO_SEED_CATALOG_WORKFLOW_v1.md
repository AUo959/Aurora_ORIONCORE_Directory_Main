# L2 Scenario Seed Catalog Workflow v1

Status: root-control-plane workflow. This document maintains the recovered L2
scenario seed catalog as routing and fixture-planning metadata only.

## Purpose

`catalog/l2_scenario_seed_catalog.json` converts the June 15 extraction reports
into a maintained root artifact. It preserves the latest `v0.2.15` scenario
cards as active root catalog entries, preserves the five `v0.2.2` lineage-only
cards as `backup_only`, and records normalized support structures for fixture
generation.

This is not canon promotion, runtime wiring, or approval to copy source HTML/PDF
material into a nested repo.

## Authority

Inputs:

- `reports/analysis/l2_scenario_seed_catalog_extraction__2026-06-15.md`
- `reports/analysis/l2_scenario_seed_catalog_extraction__2026-06-15.json`

Maintained outputs:

- `catalog/l2_scenario_seed_catalog.json`
- `catalog/contracts/l2_scenario_fixture_generator_contract_v1.json`
- `catalog/schemas/l2_scenario_seed_catalog.schema.json`

Validation:

- `python3 -m unittest tests/test_l2_scenario_seed_catalog.py`

## Disposition Rules

- Cards from `ORION_SCENARIO_CATALOG_v0_2_15.html` are `maintained` and
  `include` for root catalog and fixture-planning use.
- `SCN-0103`, `SCN-0105`, `SCN-0106`, `SCN-0107`, and `SCN-0108` remain
  `backup_only` lineage cargo because they exist in `v0.2.2` only.
- `backup_only` cards must not be emitted into fixture candidates unless the
  owner explicitly changes their disposition.
- Source HTML/PDF files remain local ignored lineage sources. Do not move them
  into root Git without a separate packaging decision.

## Reference Normalization

The maintained catalog keeps IDs as primary keys.

- If an ID exists and the label only differs by article or stale wording, the
  catalog records the current canonical handle.
- If an ID exists but the label points to a different concept, the pair remains
  `manual_review`; the catalog does not rewrite the ID silently.
- If an ID is absent from latest cards and backup-only cards, the reference is
  `unresolved_id` and blocks runtime fixture emission.

Current unresolved wiring reference:

- `SCN-0407` references `SCN-0208 (The Small Become Essential)`, but no matching
  card exists in the available lineage.

## Fixture Contract

The generator contract starts from `fixture_ready_shortlist`, sorted by score.
The first fixture candidates are:

- `SCN-0903` - The War Nobody Names
- `SCN-0708` - The One vs the Many Selves
- `SCN-0805` - The Ship That Must Survive

Fixture candidates are root JSON overlays only until a separate task authorizes
an owning runtime repo. The contract requires root output paths and receipts,
and explicitly keeps CanonRec and CloudBank out of scope.

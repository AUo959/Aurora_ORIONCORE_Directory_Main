# catalog/sources — tracked source artifacts

Source artifacts that maintained root catalogs were derived from. Files here
are byte-identical copies of the original local material, committed so the
derivation can be re-checked without the owner's machine.

These are lineage sources, not canon. Committing a file here does not promote
its content to CanonRec or wire it into any runtime.

## ORION_SCENARIO_CATALOG_v0_2_15.html

| Field | Value |
|---|---|
| Title | ORION Scenario Catalog — v0.2.15 |
| Doc ID | `ORION.L3.SCN.CATALOG.0001` |
| Last updated (in document) | 2026-02-15 |
| Original local path | `GUMAS_SIM_2.5/ORION_SCENARIO_CATALOG_v0_2_15.html` (git-ignored) |
| Size | 204853 bytes |
| sha256 | `59d9caa58f3dd424a7c92d0a826c7ee094161741c5c80ff5267114ccd8845dfe` |
| Added to git | 2026-11-28 |

**Derived artifact:** `catalog/l2_scenario_seed_catalog.json`. 87 of its 92
cards (`source_version: "v0.2.15"`) were extracted from this file. The other 5
(`SCN-0103`, `SCN-0105`–`SCN-0108`) come from `v0.2.2` lineage by owner
override and are not in this file.

**Provenance check:** the sha256 above equals the hash recorded for the
`primary_machine_source` entry in the seed catalog's `source_evidence` and in
`reports/analysis/l2_scenario_seed_catalog_extraction__2026-06-15.md`, so this
is the exact file the extraction read. The seed catalog entry carries a
`tracked_copy` pointer to this path, and
`tests/test_l2_scenario_seed_catalog.py` asserts the hash matches.

Only one copy of v0.2.15 HTML existed on the owner's machine, so there was no
canonical-version choice to make. The PDF rendering (`..._v0_2_15.pdf`) and
the v0.2.12–v0.2.14 lineage files remain local and ignored.

Pre-commit scan: no scripts, external URLs, email addresses, file paths,
credentials or personal data. Matches for words such as "secret", "token" and
"bearer" are scenario prose (for example "SCN-0928 — The Queen's Secret").

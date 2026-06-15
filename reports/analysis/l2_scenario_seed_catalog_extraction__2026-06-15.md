# L2 Scenario Seed Catalog Extraction - 2026-06-15

Status: read-only root analysis extraction. No source HTML/PDF was moved, and no
scenario card was promoted into CanonRec, CloudBank runtime, or watch scenario
fixtures by this pass.

## Context Refreshed

- `catalog/session_state.json` still has active task `salvage-operation-icloud-promotion-2026-06-12` suspended; this pass stays within its rule: do not copy iCloud/staging/archive material directly into canon or runtime.
- `AGENTS.md`, `README.md`, `catalog/workspace_manifest.yaml`, and `catalog/repo_registry.yaml` confirm root-control-plane scope and nested-repo separation.
- `reports/analysis/simulation_discovery_index__2026-06-13.md` identifies `ORION_SCENARIO_CATALOG_v0_2_12..15` as the scenario catalog source and recommends mining `v0_2_15` into watch scenarios later.
- `reports/analysis/l2_lineage_genesis__2026-06-13.md` confirms the older L2 scenario-seed lineage and distinguishes it from current engine/canon realization.

## Source Evidence

| Role | Path | Status | SHA-256 |
|---|---|---|---|
| primary_machine_source | `GUMAS_SIM_2.5/ORION_SCENARIO_CATALOG_v0_2_15.html` | local_ignored | `59d9caa58f3dd424a7c92d0a826c7ee094161741c5c80ff5267114ccd8845dfe` |
| primary_human_rendering | `GUMAS_SIM_2.5/ORION_SCENARIO_CATALOG_v0_2_15.pdf` | local_ignored | `17db06763b410ad04853aa1a1cb0bd9831fdb94a98d427b3d58b6333b75ee582` |
| scenario_card_schema_reference | `projects/GUMAS_SIM_2.0/02_DEVELOPMENT/Project_Main/Project_Files_GUMAS2_0/ORION_SCENARIO_CATALOG_SPEC_v0_3.html` | local_ignored | `7a065b1ce8405d35b0e4c80e571297d36007faf483324fe27a78cfe4512f2a36` |
| narrative_engine_generalized_pattern_reference | `narrative_engine_spec_parameters_to_narrative_core_v_0.md` | local_ignored | `a4aedede0cdd2423eab718025504f5823924e67c96283d781db5d7519044de46` |

Root Git tracking evidence: `git ls-files` returned no tracked entries for the
primary catalog/spec paths, and `git status --ignored` reports them as ignored
local workspace material. The generated files in `reports/analysis/` are review
artifacts only.

## Extraction Summary

- Primary source: `GUMAS_SIM_2.5/ORION_SCENARIO_CATALOG_v0_2_15.html`
- Catalog metadata: `ORION.L3.SCN.CATALOG.0001`, anchor `EOS_SEED_ORION`
- Extracted scenario cards: 87
- Field coverage: core patterns `True`, roles `True`, end states `True`
- Machine-readable index: `reports/analysis/l2_scenario_seed_catalog_extraction__2026-06-15.json`

## Category Counts

| Category | Cards |
|---|---:|
| Core set (SCN-0001-0099) | 13 |
| Dumas-derived Intrigue & Vengeance (SCN-0920-0929) | 10 |
| Dune-derived expansion (SCN-0101-0199) | 3 |
| Firefly-derived expansion (SCN-0401-0499) | 8 |
| Game of Thrones-derived expansion (SCN-0601-0699) | 8 |
| Jet Li action-cinema expansion (SCN-0701-0799) | 8 |
| LOTR-derived expansion (SCN-0201-0299) | 2 |
| Pokemon-derived expansion (SCN-0901-0999) | 9 |
| Star Trek-derived expansion (SCN-0501-0599) | 8 |
| Star Wars-derived expansion (SCN-0301-0399) | 8 |
| Status Inversion & Institutional Capture (SCN-0910-0919) | 2 |
| The Expanse-derived expansion (SCN-0801-0899) | 8 |

## Selective Integration Decisions

| Module | Decision | Specialist | Risk Notes |
|---|---|---|---|
| orion_scenario_catalog_v0_2_15 | include | Codex/root-control-plane | Source-derived expansion labels require setting-neutral treatment and owner review before any runtime or CanonRec use. |
| orion_scenario_catalog_spec_v0_3 | include | Codex/root-control-plane | Schema reference only; do not infer canon authority from local ignored source. |
| narrative_engine_generalized_pattern_spec | include | Codex/root-control-plane | Early spec remains planned intake; reference only until owner-surface review. |
| orion_scenario_catalog_lineage_v0_2_2_to_v0_2_14 | backup_only | Codex/root-control-plane | Redundant with latest v0.2.15; use only to verify lineage or recover deleted cards. |
| orion_scenario_catalog_pdf_twins | backup_only | Codex/root-control-plane | Binary/PDF assets stay ignored; do not copy into root Git without explicit packaging decision. |

Interpretation of `include`: include as a root analysis/intake candidate only.
It is not canonization, runtime wiring, public publication, or approval to copy
source text into a nested repo.

## Findings

1. `ORION_SCENARIO_CATALOG_v0_2_15.html` is the likely L2 scenario seed catalog the owner described: it is a portable scenario-card library built around core patterns, role slots, pressures, knobs, ethical hooks, end states, tags, and fusion/reskin grammar.
2. `ORION_SCENARIO_CATALOG_SPEC_v0_3.html` is the schema companion: it defines the context-agnostic card format, controlled tag vocabulary, and fusion provenance rule.
3. `narrative_engine_spec_parameters_to_narrative_core_v_0.md` is the narrative-engine companion: it explicitly describes generalized pattern extraction from historical accounts, fictional arcs, or event chains into portable scenario forms.
4. The current root watch scenario JSONs remain hand-authored operational scenarios. This pass did not rewrite them.
5. The main risk is source-derived expansion provenance. Before public/runtime promotion, retain only setting-neutral abstractions and avoid carrying proper-noun lore or unverifiable source claims.


Recommended next step after owner confirmation: create a maintained root catalog
or fixture-generation plan that maps selected `SCN-*` cards into watch scenario
JSON tests. Do this in a new gated pass; do not edit CloudBank or CanonRec by
implication from this report.
## Second-Pass Audit

Status: valuable material confirmed, with one extraction correction. The first
pass fully captured the latest `v0.2.15` card set, but it did not extract the
non-card support structures or the five early lineage-only Dune cards.

### Completeness Checks

- Latest `v0.2.15` cards: 87.
- Required card fields checked: core pattern, roles, objective, opposition,
  pressure, knobs, ethical hook, end states, tags.
- Missing required fields in latest extraction: 0.
- Low-richness cards in latest extraction: 0.
- Unique card IDs across available HTML lineage after second pass: 92.

### Added Non-Card Structures

- Controlled tag vocabulary: 12 tags.
- Fusion table: 34 proven pairings.
- Reskin glossary: 37 role tokens and 7 domain tokens.

### Lineage-Only Cards Added As Backup Candidates

| ID | Handle | Core Pattern | Tags |
|---|---|---|---|
| `SCN-0103` | Planetary Redesign | A long-term transformation conflicts with short-term political and economic incentives. | Stability, Justice, Truth |
| `SCN-0105` | Alliance With the Local Power | Outsiders need an alliance with locals who understand the environment, and the alliance reshapes both sides. | Identity, Survival, Justice |
| `SCN-0106` | System Addiction | A civilization becomes dependent on a substance or service that grants advantage, and withdrawal becomes existential. | Stability, Scarcity, Power |
| `SCN-0107` | Foreknowledge Trap | Prediction offers advantage, but acting on it changes the future and narrows choices into a self-fulfilling cage. | Truth, Power, Stability |
| `SCN-0108` | Human Specialist Guilds | A ban on certain technology forces reliance on rare human specialists who become power centers. | Power, Access, Legitimacy |

These five cards exist in `v0.2.2` only and are absent from `v0.2.6` onward.
They are valuable, but their disposition is `backup_only lineage cargo` until
owner review decides whether to restore them into the maintained catalog.

### High-Value Shortlist

| ID | Handle | Score | Value Lanes |
|---|---|---:|---|
| `SCN-0903` | The War Nobody Names | 9.75 | canon_engine, ethics_gate, narrative_engine, runtime_fixture |
| `SCN-0708` | The One vs the Many Selves | 9.5 | canon_engine, ethics_gate, narrative_engine, runtime_fixture |
| `SCN-0805` | The Ship That Must Survive | 8.5 | canon_engine, ethics_gate, narrative_engine, runtime_fixture |
| `SCN-0307` | Synthetic Personhood Dispute | 8.5 | canon_engine, ethics_gate, narrative_engine |
| `SCN-0002` | The Contested Claim | 8.5 | canon_engine, ethics_gate, narrative_engine |
| `SCN-0928` | The Queen's Secret | 7.75 | canon_engine, ethics_gate, narrative_engine |
| `SCN-0906` | Creature Labor Substitutes Industry | 7.75 | canon_engine, ethics_gate, narrative_engine |
| `SCN-0902` | The Protein Line | 7.75 | canon_engine, ethics_gate, narrative_engine, runtime_fixture |
| `SCN-0705` | The Handler's Weapon Learns Freedom | 7.5 | canon_engine, ethics_gate, narrative_engine, runtime_fixture |
| `SCN-0506` | The Time Loop Investigation | 7.5 | canon_engine, ethics_gate, narrative_engine, runtime_fixture |
| `SCN-0505` | The Sentient Tool Dispute | 7.5 | canon_engine, ethics_gate, narrative_engine |
| `SCN-0405` | War Veteran Faultline | 7.5 | canon_engine, ethics_gate, narrative_engine, runtime_fixture |

### Audit Warnings

- Fusion/wiring references contain stale labels: 48 ID/label issues were recorded in the JSON audit.
- One unresolved wiring reference appears in the latest cards: `SCN-0208` / `The Small Become Essential` is referenced by `SCN-0407` but no matching card exists in the available HTML lineage.
- These warnings do not invalidate the cards; they mean the fusion table and wiring links need a normalization pass before becoming runtime fixtures.

## Downstream Gate

Recommended next step after owner confirmation: normalize the catalog support
structures into a maintained root catalog or fixture-generation plan. Include a
specific decision on whether to restore the five `v0.2.2` lineage-only cards and
how to resolve stale fusion/wiring references. Do not edit CloudBank or CanonRec
by implication from this report.

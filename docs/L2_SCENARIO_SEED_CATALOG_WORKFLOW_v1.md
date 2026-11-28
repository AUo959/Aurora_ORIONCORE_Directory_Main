# L2 Scenario Seed Catalog Workflow v1

Status: root-control-plane workflow. This document maintains the recovered L2
scenario seed catalog as routing and fixture-planning metadata only.

## Purpose

`catalog/l2_scenario_seed_catalog.json` converts the June 15 extraction reports
into a maintained root artifact. It preserves the latest `v0.2.15` scenario
cards as active root catalog entries, incorporates the five complete `v0.2.2`
lineage-only Dune cards by owner override, and records normalized support
structures for fixture generation.

This is not canon promotion, runtime wiring, or approval to copy source HTML/PDF
material into a nested repo.

## Authority

Inputs:

- `reports/analysis/l2_scenario_seed_catalog_extraction__2026-06-15.md`
- `reports/analysis/l2_scenario_seed_catalog_extraction__2026-06-15.json`

Maintained outputs:

- `catalog/l2_scenario_seed_catalog.json`
- `catalog/contracts/l2_scenario_fixture_generator_contract_v1.json`
- `catalog/contracts/l2_scenario_seed_uptake_contract_v1.json`
- `catalog/schemas/l2_scenario_seed_catalog.schema.json`
- `catalog/schemas/l2_scenario_seed_uptake_contract.schema.json`
- `tools/l2_scenario_seed_uptake.py`

Tracked source:

- `catalog/sources/ORION_SCENARIO_CATALOG_v0_2_15.html`

Validation:

- `python3 -m unittest tests/test_l2_scenario_seed_catalog.py`
- `python3 -m unittest tests/test_l2_scenario_seed_uptake.py`
- `python3 tools/l2_scenario_seed_uptake.py --summary`
- `python3 tools/l2_scenario_fixture_generator.py --check`
- `python3 -m pytest tests/test_l2_scenario_fixtures.py`

## Disposition Rules

- Cards from `ORION_SCENARIO_CATALOG_v0_2_15.html` are `maintained` and
  `include` for root catalog and fixture-planning use.
- `SCN-0103`, `SCN-0105`, `SCN-0106`, `SCN-0107`, and `SCN-0108` are also
  `maintained` and `include` by owner override because their `v0.2.2` source
  cards contain the complete scenario-card field set.
- The owner-promoted `v0.2.2` cards keep explicit `source_version` and
  `source_status` provenance; incorporation here is not canon promotion or
  runtime wiring.
- `ORION_SCENARIO_CATALOG_v0_2_15.html`, the primary machine source, is tracked
  as a byte-identical copy at `catalog/sources/ORION_SCENARIO_CATALOG_v0_2_15.html`
  (packaging decision 2026-11-28; provenance in `catalog/sources/README.md`).
  The PDF rendering and older lineage HTML/PDF files remain local ignored
  lineage sources. Do not move them into root Git without a separate packaging
  decision.

## Reference Normalization

The maintained catalog keeps IDs as primary keys.

- If an ID exists and the label only differs by article or stale wording, the
  catalog records the current canonical handle.
- If an ID exists but the label points to a different concept, the pair remains
  `manual_review`; the catalog does not rewrite the ID silently.
- If an ID is absent from maintained cards and promoted lineage cards, the
  reference is `unresolved_id` and blocks runtime fixture emission.

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

### Generated fixtures (2026-11-28)

All 25 shortlist cards are emitted as runnable watch-scenario overlays. Root
hosts them because the runner (`tools/hour_aboard.py`) lives here; CloudBank and
CanonRec are read, never written.

- Generator: `tools/l2_scenario_fixture_generator.py` writes
  `catalog/generated_watch_scenarios/<fixture_id>.json`, the manifest
  `catalog/generated_watch_scenarios/index.json`, and a receipt at
  `reports/analysis/l2_scenario_fixture_generation__<date>.md`. Output is
  deterministic; `--check` (`make l2-scenario-fixtures-check`) fails on drift,
  stale, missing, or orphan fixtures. Generation fails closed on `unresolved_id`
  in a card's own wiring links, setting-specific lore, prohibited outcome keys,
  nested output paths, and sub-minimum emergence dimensions.
- Runner: `tools/l2_scenario_fixture_run.py --fixture SCN-0903` or `--all`
  (`make l2-scenario-fixtures-run`). Each fixture runs through `hour_aboard.py`
  on an isolated, fresh station clock (deterministic per seed; Orion Station's
  chronicle and `catalog/station_state.json` are untouched), then its uptake
  packet goes through CloudBank `simulation/scenario_seed_initializer.py`. Run
  artifacts go to git-ignored `reports/scenario_fixture_runs/`; `--all` refreshes
  `reports/analysis/l2_scenario_fixture_runs_latest.json`.
- Seed dynamics: `tools/scenario_seed_dynamics.py` compiles each fixture's
  `scenario_seed_overlay` into the run at that hour's seed. Knobs are scored
  into six pressure channels (range knobs such as `weak->totalizing` are sampled
  at a seed-chosen point; the dominant-solver knob picks one option per seed).
  Pressure axes become per-hour shocks that either stall an open task for the
  hour or are absorbed (crew on a task stalled last hour adapt and absorb).
  Coercive solvers escalate shocks once the decision path closes; other solvers
  raise absorption. Each seed role becomes a role-position task that end-state
  branching waits on, and scarcity diverts a share of the crew each hour. The
  L3 audit then receives run-derived pressures (open stalls, the ethics gate,
  unheld role positions, a coercive solver), so its verdict follows the run.
  The harness wraps only its own sim instance; CloudBank code is unchanged, and
  scenarios without an overlay run exactly as before. Receipts carry an
  `observations.seed_dynamics` block and a `seed_dynamics_applied` check; the
  `--all` summary reports `distinct_run_signatures` and the L3 verdict mix.
- Contract candidates (`SCN-0307`, `SCN-0002`, `SCN-0928`, `SCN-0906`,
  `SCN-0505`, `SCN-0911`; no `runtime_fixture` lane) are emitted on owner
  direction and carry `emission_basis:
  contract_candidate_emitted_by_owner_direction_2026-11-28`.
- Fixture tasks keep the five-step blueprint and add structural ordering only
  (framing before mapping and solver selection; the ethics gate after solver
  selection; end-state branching last). Expected end states stay
  `expected_end_state_categories` for observation.
- Tests: `tests/test_l2_scenario_fixtures.py` (the end-to-end run tests are
  `@simulation` and need the CloudBank and CanonRec clones) and
  `tests/test_scenario_seed_dynamics.py` (CloudBank-independent plan and audit
  derivation tests).

## Uptake And Emergence Contract

`catalog/contracts/l2_scenario_seed_uptake_contract_v1.json` defines the
consumer surfaces that scenario seeds may feed:

- root fixture generator
- state-builder evidence envelope
- simulation initializer
- ethics gate
- narrative renderer
- canon-promotion gate

The uptake contract does not implement nested repo adapters. It creates a
root-control-plane packet shape and validation rule set so future adapters know
what to consume and what they are forbidden to infer.

Scenario seeds must remain pressure fields and initial-condition templates, not
scripts. The validator requires enough degrees of freedom for emergence:

- at least four roles
- at least two pressure axes
- at least five knob axes
- at least three expected end-state categories

Expected end states are observation categories for branch coverage. They are
not required endings, winners, or canon facts. Adapters may bound input shape,
traceability, and safety gates; they must leave actor choices, pressure
responses, branch timing, and outcome selection open to the simulation.

## Dune-Inspired Lane

The catalog also carries a thematic coverage lane named
`dune_inspired_scenario_seeds` so score-only fixture selection does not hide the
Dune-derived abstraction family.

Maintained cards eligible for root fixture candidates:

- `SCN-0101` - Resource Monopoly
- `SCN-0102` - Myth Weaponization
- `SCN-0103` - Planetary Redesign
- `SCN-0104` - Formal Intrigue
- `SCN-0105` - Alliance With the Local Power
- `SCN-0106` - System Addiction
- `SCN-0107` - Foreknowledge Trap
- `SCN-0108` - Human Specialist Guilds

For thematic fixture batches, include at least one maintained `SCN-010x` card.
The `v0.2.2` cards must preserve their lineage provenance in any generated
fixture candidate.

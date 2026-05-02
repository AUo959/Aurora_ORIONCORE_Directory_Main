# QGIA Knowledge Closed-Loop Contract v1

## Status

This document is a root control-plane contract package for the sibling repos
`qgia-knowledge-library` and `qgia-knowledge-spine`.

It is adoption-ready but not yet active in either nested repo. Current repo-local
manifests still publish only `knowledge-index`, so this package should be treated
as the canonical proposal surface for the next implementation slice.

## Purpose

The QGIA stack needs a closed learning loop, not just synchronized markdown.

The contract defined here separates:

- live evidence intake
- forecast issuance and revision
- outcome adjudication
- calibration and scoring
- prior rebasing
- downstream consumption by the rest of Aurora

This prevents silent prior drift, unverifiable accuracy claims, and corpus/spine
boundary collapse.

## Declared Runtime Center

The QGIA material is centered on the following declared live runtime surface:

- Perplexity Space: <https://www.perplexity.ai/spaces/foreign-policy-and-global-poli-_IZgsdmvSo2Yxe7LAZ5HSQ>

Status:

- runtime designation: `declared-live-runtime`
- verification status: `user-declared`

This means the runtime target is intentionally recorded as an authoritative
integration surface in repo metadata, but the external page contents were not
independently fetched during this contract-writing slice.

## Authority Model

### `qgia-knowledge-library`

Authoritative for:

- live evidence intake records
- resolved outcome records tied to real-world events
- promoted case knowledge and domain lessons
- curated domain and reference corpus

Not authoritative for:

- forecast method definitions
- calibration transforms
- prior rebasing rules
- resolution policy semantics

### `qgia-knowledge-spine`

Authoritative for:

- forecast record structure
- methodological references and taxonomy
- resolution policy
- prior tables
- calibration reports and correction transforms

Not authoritative for:

- raw live-source intake
- adjudicated domain truth absent linked evidence
- narrative case promotion into the corpus

## Closed-Loop Flow

1. Evidence enters the library as append-only intake records.
2. The spine issues or updates forecasts using linked evidence and current priors.
3. The library resolves outcomes against the spine-owned resolution policy.
4. The spine recomputes calibration and rebases priors from resolved outcomes.
5. The library promotes stable lessons and case updates into curated corpus material.
6. Aurora runtime and forecasting systems consume machine-readable artifacts, not
   ad hoc markdown inference.

## Recommended Adoption Layout

### `qgia-knowledge-library`

- `data/intake/evidence-ledger.jsonl`
- `data/truth/outcome-ledger.jsonl`
- existing curated markdown corpus remains in the numbered content directories

### `qgia-knowledge-spine`

- `data/forecasts/forecast-ledger.jsonl`
- `data/priors/prior-table.json`
- `data/calibration/calibration-report.json`
- `policies/resolution-policy.md`

## Artifact Families

### Evidence Record

- file form: JSONL
- owner: `qgia-knowledge-library`
- schema: `catalog/schemas/qgia_evidence_record.schema.json`
- purpose: append-only capture of new live information with provenance, timing,
  and linked topics/entities

### Forecast Record

- file form: JSONL
- owner: `qgia-knowledge-spine`
- schema: `catalog/schemas/qgia_forecast_record.schema.json`
- purpose: append-only forecast issuance and revision history, including priors,
  methods, evidence refs, and resolution horizon

### Outcome Record

- file form: JSONL
- owner: `qgia-knowledge-library`
- schema: `catalog/schemas/qgia_outcome_record.schema.json`
- purpose: explicit adjudication of whether a forecasted event occurred,
  including basis, resolver, and Brier eligibility

### Prior Table

- file form: JSON
- owner: `qgia-knowledge-spine`
- schema: `catalog/schemas/qgia_prior_table.schema.json`
- purpose: versioned prior/base-rate table used by forecasting workflows and
  documented rebasing

### Calibration Report

- file form: JSON
- owner: `qgia-knowledge-spine`
- schema: `catalog/schemas/qgia_calibration_report.schema.json`
- purpose: scored performance surface for team and domain-level accuracy,
  calibration drift, and correction transforms

## Event Contract

These event types are the canonical names for cross-repo and downstream sync:

- `qgia.evidence.ingested`
- `qgia.forecast.issued`
- `qgia.forecast.updated`
- `qgia.outcome.resolved`
- `qgia.priors.rebased`
- `qgia.calibration.updated`
- `qgia.case.promoted`

### Event Semantics

`qgia.evidence.ingested`
- producer: library
- meaning: new evidence record appended
- minimum payload keys: `evidence_id`, `topic_refs`, `observed_at`, `ingested_at`

`qgia.forecast.issued`
- producer: spine
- meaning: new open forecast created
- minimum payload keys: `forecast_id`, `domain`, `question_type`, `target_resolves_by`

`qgia.forecast.updated`
- producer: spine
- meaning: open forecast revised from new evidence or method state
- minimum payload keys: `forecast_id`, `revision_id`, `evidence_refs`, `probability`

`qgia.outcome.resolved`
- producer: library
- meaning: forecast outcome explicitly adjudicated
- minimum payload keys: `outcome_id`, `forecast_id`, `resolved_at`, `observed_outcome`

`qgia.priors.rebased`
- producer: spine
- meaning: prior table regenerated from new scored outcomes
- minimum payload keys: `prior_table_id`, `effective_from`, `supersedes`, `outcome_refs`

`qgia.calibration.updated`
- producer: spine
- meaning: calibration report regenerated
- minimum payload keys: `report_id`, `sample_window`, `resolved_forecast_count`

`qgia.case.promoted`
- producer: library
- meaning: resolved truth and lessons promoted into curated corpus material
- minimum payload keys: `source_outcome_ids`, `target_paths`

## Downstream Consumption Rules

### Retrieval and analyst grounding

Consume:

- evidence records from the library
- outcome records from the library
- curated case and domain markdown from the library

Do not consume:

- open forecasts as if they were resolved truth

### Forecast generation and automated reasoning

Consume:

- forecast records from the spine
- prior table from the spine
- calibration report from the spine
- methodology and resolution policy from the spine

Do not consume:

- raw evidence without provenance filtering
- promoted library prose as a substitute for current priors

### Governance and audit

Consume:

- outcome records
- calibration reports
- prior table lineage
- linked evidence refs and resolver identity

## Non-Negotiable Rules

- No forecast probability may change without a new forecast record revision or a
  new prior table version.
- No outcome may be treated as truth without an explicit outcome record.
- No calibration claim may be published without reference to resolved forecast
  count and sample window.
- No curated corpus update may silently overwrite a prior, score, or outcome.
- Open forecasts and resolved outcomes must remain distinguishable at the schema
  level.

## Adoption Order

1. Add `policies/resolution-policy.md` to `qgia-knowledge-spine`.
2. Add `forecast-ledger.jsonl`, `prior-table.json`, and `calibration-report.json`
   to the spine repo.
3. Add `evidence-ledger.jsonl` and `outcome-ledger.jsonl` to the library repo.
4. Extend both repo-local constellation contracts beyond `knowledge-index`.
5. Wire event publication to the canonical event names above.
6. Only then promote downstream consumers to use the new artifacts.

## Non-Goals For v1

- direct raw-feed ingestion code
- storage backend decisions outside repo-tracked artifacts
- model selection policy
- UI/reporting surfaces beyond the machine-readable schemas

# Aurora Confidence Audit Workflow v1

## Status

This is a root control-plane workflow for attaching confidence metadata to
Aurora outputs. It is an audit-layer surface, not a runtime truth oracle.

## Purpose

Every concrete conclusion, analysis, prediction, or recommendation can be
wrapped as a confidence assessment record. The record preserves:

- the claim text and type
- evidence and authority references
- a confidence score from `0` to `1`
- the threshold used for alerting
- whether a user alert is required
- the calibration profile that produced or adjusted the score

Scores may remain internal, but records belong in receipts, handoffs,
automation memory, or downstream ledgers when the output affects a decision.

## Contract Surfaces

- Tool: `tools/aurora_confidence_audit.py`
- Record schema: `catalog/schemas/aurora_confidence_record.schema.json`
- Contract: `catalog/contracts/aurora_confidence_audit_contract_v1.json`
- Latest generated report: `reports/analysis/aurora_confidence_audit_latest.json`

## Claim Types

- `conclusion`: a concrete finding or determination.
- `analysis`: an interpretive assessment or synthesis.
- `prediction`: an expected future outcome or trajectory.
- `recommendation`: a proposed action or decision path.

## Evidence Levels

The bootstrap scoring rubric uses these evidence levels:

- `verified_artifact`
- `direct_observation`
- `deterministic_check`
- `corroborated_inference`
- `inference`
- `projection`
- `speculation`
- `unsupported`

This initial rubric is deliberately conservative. Later calibration should be
based on resolved predictions, reviewer adjudication, and domain-specific
outcome history.

## Alert Rule

Default threshold: `0.70`

If `confidence.score < confidence.threshold`, the record sets:

- `audit.requires_user_alert: true`
- `audit.alert_reason: confidence_below_threshold`
- `audit.user_facing_message` with the concrete score and threshold

This does not require every score to be visible in normal UI. It requires the
audit layer to retain the score and requires low-confidence outputs to be
surfaced before the system or user relies on them.

## Examples

Score one recommendation:

```bash
python3 tools/aurora_confidence_audit.py score \
  --claim-type recommendation \
  --text "Proceed with root-only validation before nested repo publication." \
  --evidence-level deterministic_check \
  --authority-ref AGENTS.md \
  --evidence-ref reports/analysis/workspace_verify_latest.json
```

Audit a JSONL batch and persist the current report:

```bash
python3 tools/aurora_confidence_audit.py audit \
  --input claims.jsonl \
  --jsonl \
  --threshold 0.70 \
  --persist-report
```

Use strict alert gating in CI or automation:

```bash
python3 tools/aurora_confidence_audit.py audit \
  --input claims.json \
  --fail-on-alert
```

Exit code `2` means at least one output fell below the configured threshold.

## Adoption Notes

Root control-plane use can begin immediately for receipts and handoffs. Nested
runtime adoption should happen only through the owning repo surfaces. For QGIA,
this complements the existing forecast confidence and calibration artifacts; it
does not replace the QGIA closed-loop contract.

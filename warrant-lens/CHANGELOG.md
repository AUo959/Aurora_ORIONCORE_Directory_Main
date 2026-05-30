# Changelog

All notable changes to Warrant Lens are recorded here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-05-26

First implementation of the v1 build spec
(`/SPEC__WARRANT_LENS__v1.md`). Encodes Principles 1–9 structurally; tests
in §9 are the acceptance contract.

### Added — pipeline

- `model.ClaimRecord` — single source of truth contract between stages.
- `segment` — heuristic sentence/assertion segmentation with char offsets.
- `classify` — taxonomy-driven typing via `LLMClient` Protocol.
- `filter` — drops non-load-bearing claims (no evidentiary demand).
- `warrant` — structural checks: source presence, locatability, role,
  chain, fit. §7 settled-vs-frontier hard boundary enforced via
  default-to-`FRONTIER_HANDOFF` when consensus is unencoded.
- `restate` — emits the tool's paraphrase before any flag (Principle 7).
- `emit_inline` — text-marker rendering for terminal / pipeline use.
- `emit_trace` — JSONL provenance trace, archival filename convention
  `WARRANTLENS__TRACE__[topic]__v1.0__YYYY-MM-DD.jsonl`.
- `emit_html` — self-contained HTML inline-annotation viewer with hover
  cards. No JS, no CDN, no network calls.
- `pipeline.analyze` — pure-function orchestrator.
- `__main__` — CLI: `analyze` and `calibrate` subcommands.

### Added — clients

- `llm_client.LLMClient` Protocol — the single seam where a model call can
  enter the pipeline (SPEC §11).
- `llm_client.HeuristicClient` — deterministic, no-network default for v1.
- `anthropic_client.AnthropicClient` — production client. Imports the
  `anthropic` SDK only here; closed-set label validation; defensive against
  malformed / empty / prose-wrapped responses.
- `anthropic_client.MockClient` — drop-in test double.

### Added — calibration

- `calibrate.run_calibration` — replay a JSONL trace, accept human labels
  (yes / no / unsure), compute precision (unsure-excluded denominator) and
  best-effort recall (only when silent claims are also labelled).
- CSV and interactive labelling modes.
- Output: `*.labels.jsonl` + `*.calibration.md`.

### Added — configuration

- `config/taxonomy.yaml` — claim types and evidentiary demand.
- `config/fit_table.yaml` — source-type × claim-type fit per owning domain.
  Includes `general_empirical` and `software_engineering` domains plus
  settled-claim consensus markers.
- `config/config.yaml` — delivery directness, precision bias, default
  standard.

### Added — tests

- `tests/test_acceptance.py` — all 11 §9 rows: T-FILTER, T-DEMAND, T-PAIR,
  T-CLIMATE (tier-1), T-PRIMARY, T-CHAIN, T-RESTATE, T-FRONTIER, T-DELIVERY
  (tier-1), T-BLINDSPOT, T-CALIB, plus filename convention.
- `tests/test_anthropic_client.py` — production client parsing, closed-set
  validation, defensive failure paths, prose-wrapped JSON recovery.
- `tests/test_calibrate.py` — precision / recall semantics, unsure
  exclusion, archival filename preservation, Principle-2 reminder.
- `tests/test_emit_html.py` — flagged-only wrapping, hover metadata
  presence, HTML escaping, no external resources, directness affects
  phrasing only.

### Tooling

- `Makefile` with local targets: `install`, `test`, `test-tier1`, `smoke`,
  `html-demo`, `calibrate-demo`, `clean`.

### Invariants enforced (codified, not promised)

- Principle 1 — pipeline is source-agnostic; no input-type branches.
- Principle 2 — no truth verification; `verified`/`is true` strings are
  absent from output (asserted by T-BLINDSPOT).
- Principle 3 — directness changes phrasing only; flagged sets identical
  across delivery modes (asserted by T-DELIVERY).
- Principle 4 — every raised flag carries `human_handoff`, phrased as an
  invitation.
- Principle 5 — `FitAssessment` always pairs source class with claim type;
  no standalone source-quality badge anywhere in output (asserted by
  T-PAIR).
- Principle 6 — three editable YAML files; structural checks live in code.
- Principle 7 — `restate` runs before `check_warrant`; non-empty
  `tool_restatement` required on every flagged record (asserted by
  T-RESTATE).
- Principle 8 — `standard_invoked` populated from config on every record.
- Principle 9 — `blind_spot_note` default on every record.

### Out of scope (do not "helpfully" add)

- Truth verification / live retrieval.
- Auto-collapsing the restatement step.
- Standalone source-credibility score.
- Tone hardening under repeated dismissals.
- Inferring settledness from public controversy.

---

## [Unreleased]

### Planned for v2

- Dialogic argue-back loop: rejection of `tool_restatement` opens a
  structured exchange instead of just voiding the flag. Schema is already
  forward-compatible.
- Logprob enrichment via `confidence_signal` (schema slot exists, currently
  `null`).
- Citation-chain crawling across documents (still no truth verification).
- Per-domain consensus encodings (more `settled_claim_markers` entries).

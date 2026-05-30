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

## [1.1.0] — 2026-05-26

Heuristic hardening release driven by dogfooding `examples/mixed_corpus.txt`
(29 mixed real-world-style claims) against v1.0. Five mechanical bugs the
unit tests didn't surface — all fixed with regression tests locked in.

### Fixed

- **Empirical-hint regex too narrow.** v1.0 left 13/29 dogfood claims
  `unclassified`. Expanded vocab now covers progressive forms (rising,
  falling), more nouns (consumption, demand, share, cost), and more verbs
  (emitted, deployed, declined). Dogfood `unclassified` dropped to 9/29.
- **Source extractor missed leading articles.** "According to the IEA" and
  "Per the official press release" were ignored because the regex required
  `[A-Z]` immediately after the trigger word. Now allows optional `the / a
  / an` before the source name.
- **Code-api regex over-triggered on citation parens.** `(Brown et al.,
  2017)` was being read as a function call. Tightened to require no
  whitespace between identifier and `(`.
- **Citation pattern was a claim-type instead of a source marker.** v1.0
  classified `"X causes Y (Doe 2024)"` as `named_citation`. Citations are
  now a fallback that only fires when nothing more substantive matched.
- **`FRONTIER_HANDOFF` fired on non-empirical claim types.** Code-API
  signatures and temporal facts have no settled-vs-frontier semantics.
  Gated to `consequential_empirical / specific_statistic / causal_mechanism`.
- **Statistic+year claims misread as bare `temporal_fact`.** "Emitted 552
  metric tons in 2024" is a statistic, not a date fact. Reordered checks.
- **Scientific causation vocabulary unrecognised.** Added `induces /
  inhibits / suppresses / activates / mediates / triggers / drives /
  produces / generates / prevents / reduces / raises / amplifies /
  attenuates` to `_CAUSAL_RE`.

### Added

- `examples/mixed_corpus.txt` — 29-claim representative corpus spanning all
  9 claim types and all 5 §9 failure modes. Used as the dogfood fixture
  and as a stable reference for benchmarks.
- `tests/test_v11_regressions.py` — 16 new tests, one parametrized group
  per fix above. Locks the v1.0 bugs out permanently.

### Numbers

- Tests: 33 → 49.
- Dogfood `unclassified` rate: 45% → 31%.
- False `FRONTIER_HANDOFF` flags on code claims: 2 → 0.
- T-CLIMATE and T-DELIVERY (tier-1) still green.

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
- LLM-backed attribution detection ("X has argued that Y") — the dogfood
  shows the heuristic can't separate this from substantive empirical
  claims. This is what `AnthropicClient` is for; benchmark module exists
  to quantify the gain.

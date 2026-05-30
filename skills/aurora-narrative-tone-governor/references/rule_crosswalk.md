# Rule Crosswalk

## Narrative Principles to Lint IDs

| Principle | Intent | Primary Lint Binding | CTL Support Patterns |
|---|---|---|---|
| R1 Information Density | Prefer concrete operational state over filler | LINT-NARR-003 (warn tokens), LINT-NARR-002 (empty contrast scaffold) | P002, P005, P303 |
| R2 No Meta-Narration | Ban commentary about the act of narration/logging | LINT-NARR-001 | P101 |
| R3 No Fake-Depth Devices | Ban vague depth language without measurable state | LINT-NARR-003 or LINT-NARR-004 (hard bans) | P003, P102 |
| R4 Concrete Closers | End on operational fact, not thematic flourish | LINT-NARR-001 (thematic closer trigger) | P003 |
| R5 Traceable Claims | Ensure claims map to events/state deltas | LINT-NARR-006 plus metadata checks (`event_ledger_id`, `paired_output_id`, `trace_map`) | P301 (certainty inflation risk) |
| R6 Audience Clarity | Require explanation of non-obvious identifiers | LINT-NARR-005 | P303 |

## LINT-NARR Semantics

| Lint ID | Modes | Severity | Action | Notes |
|---|---|---|---|---|
| LINT-NARR-001 | MODE_LOG, MODE_RECAP | error | reject_output | Meta-narration or thematic closer |
| LINT-NARR-002 | MODE_LOG, MODE_RECAP | error | reject_output | Empty contrast scaffold (proxy new-state test) |
| LINT-NARR-003 | MODE_LOG, MODE_RECAP | warn | annotate_output | Warn tokens / weak fake-depth indicators |
| LINT-NARR-004 | MODE_LOG, MODE_RECAP | error | reject_output | Hard banned phrases |
| LINT-NARR-005 | MODE_LOG, MODE_RECAP | warn | annotate_output | Unexplained identifiers in Story Track |
| LINT-NARR-006 | MODE_RECAP | warn | annotate_output | Missing stakes/decisions metadata |

## CTL Pattern Families (v0.2.2)

- Cadence: `P001..P005`
- Tone/meta: `P101..P104`
- Rhetoric: `P201`
- Confidence/clarity: `P301..P304`

Scoring guidance from canonical CTL ruleset:
- APS rewrite threshold: `>= 3`
- APS fail threshold: `>= 7`
- Hard overrides: `P001_NO_NO_JUST`, `P301_CERTAINTY_INFLATION`

## Verdict Mapping

- `BLOCK`: any LINT error (`001`, `002`, `004`) or unresolved CTL hard override risk.
- `REVIEW`: warning-only outcomes (`003`, `005`, `006`) or moderate CTL drift indicators.
- `PASS`: no blocking hits and no material warning drift.

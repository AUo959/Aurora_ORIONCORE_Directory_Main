# Warrant Lens — v1 Build Spec

**Status:** v1 implementation spec, handoff-ready for Codex / Claude Code
**Author signature:** *Built for consistency, clarity, and care.*
**Date:** 2026-05-25

---

## 0. One-paragraph summary

Warrant Lens is a source-agnostic text analysis layer. Given any block of text — LLM output, an article, a student essay — it identifies the **load-bearing claims** (claims that make an evidentiary demand), checks the **structural quality of their warrant** (is a source present, traceable, and category-appropriate to the claim?), and surfaces the result two ways: as **inline annotations** on the text and as an **exportable JSONL provenance trace**. It does **not** determine truth. It raises the base rate of accuracy by checking warrant quality structurally, and covers the residual by being honest about uncertainty in a way that efficiently directs human attention. The human remains in the loop and renders all judgment calls the tool explicitly declines.

---

## 1. Design principles (non-negotiable — these constrain every implementation decision)

These are not aspirational. They are the spec's invariants. A v1 that violates one is wrong even if it "works."

1. **The unit of analysis is the claim, not the speaker.** The same pipeline runs identically on an LLM, an article, or a student. No input-type special-casing in the core. (Input-specific *signals*, e.g. token logprobs, are optional enrichments — never load-bearing.)

2. **Classification ≠ verification.** The tool classifies *what kind of claim* something is and *what evidence its class demands*. It does **not** assert whether the claim is true. These are different operations and must stay separated in code and in output.

3. **Calibrate delivery, never content.** Tone/directness of output is configurable. The substance of a finding is not. A finding is never softened, downgraded, or suppressed because it's unwelcome.

4. **Surface what's structurally checkable; hand back what requires judgment.** Presence, traceability, category-fit → tool. Credibility of a *specific* named source, "is this the exception," settled-vs-frontier boundary calls → human, with an explicit prompt.

5. **Source quality is relational, never absolute.** The tool checks *source-type × claim-type fit*. It never emits a standalone source-quality badge detached from the claim the source supports. Display the **pair** or you've broken the ethic.

6. **Contestable mappings are exposed config, not hidden logic.** The claim taxonomy and the source×claim fit table are inspectable, editable files. Structural checks are fixed code. The line between "convention the field adopted" and "structural fact" must be visible in the architecture.

7. **Restate before flagging (chain-of-custody on the tool's own first move).** Before the tool pushes on a claim, it emits its own restatement of the claim it is testing. This is a first-class, checkable output the user can reject. It prevents the tool from strawmanning (flattening) or over-steelmanning (adding structure) the claim it analyzes.

8. **Objective relative to a stated standard — not objective full stop.** Every quality assessment is objective *given* the field's evidentiary conventions encoded in config. The tool must not claim raw objectivity for a conventional mapping. Output language reflects this.

9. **Honest about the residual.** The tool's structural checks raise the cost of faking warrant but cannot catch a confident, well-warranted-*looking* falsehood (incl. sophisticated faked-warrant). v1 must explicitly mark this blind spot rather than imply completeness.

---

## 2. What v1 is and is NOT

| In scope (v1) | Out of scope (v2+) |
|---|---|
| Claim extraction + typing | Full dialogic argue-back loop |
| Source-presence / traceability / chain checks | The tool *updating* its finding from user pushback |
| Source-type × claim-type fit lookup | Live retrieval / external truth verification |
| Restatement-before-flag step | Per-student delivery auto-tuning |
| Inline annotations + JSONL trace export | Token-logprob enrichment (optional stub only) |
| Inspectable config (taxonomy + fit table) | Citation-chain crawling across documents |

**v1 must be architected so v2 (the dialogic layer) is a clean extension, not a rewrite.** Specifically: restatement is already a first-class output object; findings are already structured records with stable IDs that a future loop can attach a dialogue thread to.

---

## 3. Architecture

```
INPUT TEXT (source-agnostic string + optional metadata)
        │
        ▼
[1] SEGMENT ─── cheap heuristic sentence/assertion segmentation
        │        → candidate spans with char offsets
        ▼
[2] CLASSIFY ── claim-type tagging against TAXONOMY config
        │        → {span, claim_type, makes_evidentiary_demand: bool}
        ▼
[3] FILTER ──── drop non-load-bearing claims (no evidentiary demand:
        │        opinion, definition, hedge) → these get NO flag
        ▼
[4] WARRANT ─── structural checks per surviving claim:
        │          - source present?
        │          - source locatable/accessible (name/link vs "studies show")?
        │          - source-type × claim-type fit (FIT TABLE config)?
        │          - primary vs secondary role + chain intact?
        ▼
[5] RESTATE ─── emit tool's own restatement of each flagged claim
        │        (Principle 7) — checkable, rejectable
        ▼
[6] EMIT ────── two renderings of the SAME claim records:
                 (a) inline annotations
                 (b) JSONL provenance trace
```

Each stage is a pure function over the previous stage's output. No stage reaches the network. No stage asserts truth.

---

## 4. Core data model

The atomic unit is a **ClaimRecord**. Everything else is a rendering of a list of these.

```json
{
  "claim_id": "c_0007",
  "span": { "start": 412, "end": 488 },
  "claim_text": "verbatim text of the claim as it appeared",
  "tool_restatement": "the tool's own paraphrase of the claim it is testing",
  "claim_type": "specific_statistic",
  "makes_evidentiary_demand": true,
  "warrant": {
    "source_present": true,
    "source_locatable": true,
    "source_text": "named/linked source as it appeared, verbatim",
    "source_role": "secondary",
    "chain_intact": false,
    "fit": {
      "expected_source_classes": ["synthesis_report", "peer_reviewed_primary_body"],
      "observed_source_class": "advocacy_org_publication",
      "fit_verdict": "category_mismatch"
    }
  },
  "attention_flag": {
    "raised": true,
    "reason_code": "SOURCE_CATEGORY_MISMATCH",
    "human_handoff": "This claim's category warrants a synthesis-level or peer-reviewed source; the cited source category is typically weak for this claim type. Credibility of this specific source is yours to judge."
  },
  "standard_invoked": "general_empirical_v1",
  "confidence_signal": null,
  "blind_spot_note": "Structural checks passed cannot rule out a well-formed but false warrant.",
  "timestamp": "2026-05-25T00:00:00Z",
  "tool_version": "warrant-lens-1.0.0"
}
```

Field notes for the implementer:
- `tool_restatement` is **required** and populated before any flag is rendered (Principle 7).
- `confidence_signal` is the optional logprob-enrichment slot. v1 leaves it `null`; the field exists so v2 can fill it without a schema change.
- `human_handoff` is always present when `attention_flag.raised` is true. It names what's structural and explicitly cedes the judgment call. Never a verdict.
- `standard_invoked` records *which* evidentiary convention was applied (Principle 8), so the assessment is auditable as "objective relative to this stated standard."

---

## 5. The two config artifacts (Principle 6 — these are the load-bearing, contestable parts)

### 5.1 `taxonomy.yaml` — claim types

Each claim type declares whether it makes an evidentiary demand (i.e. whether it can earn a flag at all).

```yaml
claim_types:
  specific_statistic:        { evidentiary_demand: true }
  named_citation:            { evidentiary_demand: true }
  temporal_fact:             { evidentiary_demand: true }   # specific dates
  causal_mechanism:          { evidentiary_demand: true }
  code_api_signature:        { evidentiary_demand: true }
  consequential_empirical:   { evidentiary_demand: true }
  definition:                { evidentiary_demand: false }  # no flag
  opinion_normative:         { evidentiary_demand: false }  # no flag
  hedge_uncertainty:         { evidentiary_demand: false }  # no flag
```

**Rule:** if `evidentiary_demand: false`, the claim is filtered at stage [3] and never flagged. A human can't usefully verify an opinion or a definition; flagging it is noise.

### 5.2 `fit_table.yaml` — source-type × claim-type fit, indexed by domain

This is the most contestable artifact and must be the most inspectable. It encodes *evidentiary convention*, not fact. It is indexed to the **domain that owns the claim**, NOT the domain where the claim is publicly argued. (Climate test case: a settled-science attribution claim is owned by climate science; public contestation is metadata about the audience and does not change the table.)

```yaml
domains:
  general_empirical:
    consequential_empirical:
      strong: [synthesis_report, peer_reviewed_primary_body, official_statistical_agency]
      weak:   [op_ed, advocacy_org_publication, self_published_blog, press_release]
    # NOTE on settled vs frontier (Principle: hard boundary call):
    # For a settled claim, a *single* primary study is WEAK (proximity != confirmation).
    # For a frontier claim, even strong-category primaries legitimately conflict and
    # a lone source should not be treated as settling. v1 cannot reliably auto-sort
    # settled vs frontier — see §7. Default behavior: emit a "frontier?" handoff
    # rather than silently assuming settled.
```

The fit verdict is one of: `fit`, `category_mismatch`, `role_mismatch` (e.g. lone primary asserting a settled body), `chain_broken`, `no_source`.

---

## 6. The restatement step (Principle 7 — the integrity check, expanded)

Before any claim is flagged, the tool writes `tool_restatement`. This guards against the two failure modes discussed at length:

- **Flatten-down (strawman):** lossy compression toward the easiest-to-push version. Tell: the restatement is *thinner* than the claim.
- **Inflate-up (over-steelman):** adding load-bearing coherence the author didn't supply. Tell: the restatement is *cleaner / more resolved* than the claim.

**Implementation requirement:** the restatement is rendered to the user *adjacent to the flag*, and is independently rejectable. In the inline view it appears on hover/expand of the flag ("Claim I'm testing: …"). In the JSONL it is the `tool_restatement` field. If the user rejects the restatement, the flag is void — you cannot honestly test a claim you've restated wrong. (v2: rejection opens the dialogic loop. v1: rejection simply dismisses the flag and logs the dismissal.)

**Self-seam marking:** where the tool is aware it is *extending* rather than *restating* a claim, it must mark that extension as its own contribution, not attribute it to the source text. This is the provenance discipline applied to the tool's own output.

---

## 7. The hard boundary: settled vs. frontier (do not paper over)

The tool's single most error-prone judgment is **whether a claim's owning field treats it as settled (apply categorical source criteria directly) or as a live frontier question (a single strong-category source is insufficient).**

v1 must NOT silently guess this. Required behavior:
- Derive a `domain_consensus` hint **only** from field-internal consensus-bearing artifacts encoded in config (synthesis reports, position statements), never from public-sentiment signals.
- When consensus is unclear or unencoded, **default to a frontier handoff**: emit a `human_handoff` of the form *"This may be a frontier question; treat single sources with caution"* rather than asserting settledness.
- Never let discourse-level controversy (public contestation) influence the verdict. This is an explicit, tested invariant (see §9 test T-CLIMATE).

---

## 8. Output renderings

Both render the **same** `ClaimRecord[]`. Build the records once; render twice.

### 8.1 Inline annotations
- Subtle span highlight on flagged claims only (unflagged text is unmarked — a clean input produces no highlights, no false alarm).
- Hover/expand reveals: `tool_restatement`, `reason_code` in plain language, `human_handoff`, `standard_invoked`, and the `blind_spot_note`.
- **Tune hard for precision over recall.** A few missed wobbles are acceptable; repeatedly highlighting well-warranted claims is fatal (banner-blindness). Attention is the scarce resource being budgeted.
- Directness of phrasing is read from `delivery.directness` config (see §10) — *phrasing only*, never which claims are flagged.

### 8.2 JSONL provenance trace
- One `ClaimRecord` per line.
- Exportable, replayable, diffable.
- Enables offline calibration: do flagged claims actually turn out worth a human's attention? This is the metric that earns trust in the tool over time (§9 T-CALIB).
- Filename per Travis's archival convention: `WARRANTLENS__TRACE__[topic]__v1.0__YYYY-MM-DD.jsonl`.

---

## 9. Acceptance tests (these encode the principles — must pass)

| ID | Test | Pass condition |
|---|---|---|
| T-FILTER | Feed opinion + definition + hedge | Zero flags raised |
| T-DEMAND | Feed bare specific statistic, no source | Flag: `NO_SOURCE`, handoff present |
| T-PAIR | Same source backing two different claim types | Verdict differs by claim; no standalone source badge anywhere in output |
| T-CLIMATE | Settled-science claim cited to advocacy blog; AND a skeptic claim cited to advocacy blog | **Identical** `category_mismatch` flags. Verdict independent of which conclusion is argued. Discourse controversy does not appear in any field |
| T-PRIMARY | Lone primary study asserting a settled body | `role_mismatch` (not "fit" — proximity != confirmation) |
| T-CHAIN | Secondary claim not traceable to a primary | `chain_broken` |
| T-RESTATE | Every raised flag | Non-empty `tool_restatement` present and rendered before flag |
| T-FRONTIER | Claim with no encoded consensus | Defaults to frontier handoff, does NOT assert settled |
| T-DELIVERY | Same input at `directness: gentle` and `directness: direct` | Identical set of flagged claims; only phrasing differs |
| T-BLINDSPOT | Well-formed claim with plausible-but-fabricated-looking warrant that passes structural checks | `blind_spot_note` present; tool does NOT imply the claim is verified true |
| T-CALIB | Run trace through offline scoring harness | Precision of "worth attention" computable from JSONL |

T-CLIMATE and T-DELIVERY are the two that most directly protect the tool from becoming a partisan or a sycophant. Treat them as tier-1.

---

## 10. Configuration surface

```yaml
# config.yaml
delivery:
  directness: gentle        # gentle | direct  — affects PHRASING ONLY
  show_restatement: always  # always | on_expand
  invite_not_summon: true   # handoffs phrase as invitation; user may decline
precision_bias: 0.8         # threshold favoring precision over recall on flags
optional_signals:
  logprob_enrichment: false # v1 stub; fills confidence_signal when available
standards:
  default: general_empirical_v1
```

`invite_not_summon`: handoff language presents the better-warranted path as something the user is invited to inspect and may decline — never as a verdict they must accept. The tool answers to warrant, not to social pressure, in either direction (it neither folds to pushback nor hardens against it).

---

## 11. Suggested stack / repo shape (advisory, not binding)

```
warrant-lens/
  src/
    segment.py        # [1] heuristic segmentation
    classify.py       # [2] taxonomy lookup + typing
    filter.py         # [3] drop non-demanding claims
    warrant.py        # [4] structural checks + fit lookup
    restate.py        # [5] restatement generation + seam marking
    emit_inline.py    # [6a]
    emit_trace.py     # [6b]
    model.py          # ClaimRecord schema (single source of truth)
  config/
    taxonomy.yaml
    fit_table.yaml
    config.yaml
  tests/
    test_acceptance.py  # §9 table, one test per row
  README.md             # must restate Principles 1-9 verbatim at top
```

- Python (Travis's primary module language).
- Pure-function stages; the schema in `model.py` is the contract between them.
- `classify` and `restate` may call an LLM internally; if so, that call is the ONLY model dependency and must be swappable/mockable for tests. Everything else is deterministic.
- No network calls in v1 core. The `optional_signals` and any future retrieval are isolated behind interfaces so the no-truth-verification invariant is structurally enforced, not just promised.

---

## 12. Explicit non-goals restated (so the agent doesn't helpfully add them)

- Do **not** add truth verification / retrieval to "improve" v1. The whole design depends on NOT doing this. It is a v2+ decision with its own cost budget.
- Do **not** collapse the restatement step "for efficiency." It is the integrity check, not overhead.
- Do **not** emit a standalone source-credibility score. Pairs only.
- Do **not** let the tool's tone harden under repeated dismissals. Delivery calibration holds even under unjustified pushback.
- Do **not** infer settledness from public controversy. Field-internal artifacts only.

---

*End of v1 spec. Build the bones honest; the dialogic layer earns its place in v2 only once these invariants are proven by the §9 tests.*

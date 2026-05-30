# Warrant Lens

Source-agnostic text analysis layer. Given any block of text, identifies the load-bearing claims, checks the structural quality of their warrant, and surfaces the result as inline annotations + a JSONL provenance trace. **It does not determine truth.**

See [`SPEC__WARRANT_LENS__v1.md`](../SPEC__WARRANT_LENS__v1.md) at the Aurora root for the full v1 build spec.

---

## Principles (verbatim from spec §1 — these are the invariants)

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

## Architecture (pipeline)

```
INPUT TEXT
  → [1] SEGMENT       cheap heuristic sentence/assertion segmentation
  → [2] CLASSIFY      taxonomy lookup; LLMClient protocol (HeuristicClient in v1)
  → [3] FILTER        drop non-load-bearing claims (no evidentiary demand)
  → [4] WARRANT       structural checks: presence, locatable, role, chain, fit
  → [5] RESTATE       tool's own paraphrase of each flagged claim (Principle 7)
  → [6] EMIT          (a) inline annotations  (b) JSONL provenance trace
```

Each stage is a pure function over the previous stage's output. No stage reaches the network. No stage asserts truth.

---

## Install (dev)

```bash
cd warrant-lens
python -m pip install -e ".[dev]"
```

## Run tests

```bash
pytest                    # all
pytest -m tier1           # only the two principle-protecting tests (T-CLIMATE, T-DELIVERY)
```

## Run on a text file

```bash
warrant-lens analyze path/to/input.txt --trace-dir traces/ --topic my-topic
# emits: traces/WARRANTLENS__TRACE__my-topic__v1.0__YYYY-MM-DD.jsonl
#        stdout: inline-annotated text
```

---

## Configuration surface

Three YAML files in `config/`:

| File | Role | Contestable? |
|---|---|---|
| `taxonomy.yaml` | Claim types + whether each makes an evidentiary demand | Yes — field convention |
| `fit_table.yaml` | Source-type × claim-type fit, indexed by domain | Yes — field convention |
| `config.yaml` | Delivery directness, precision bias, default standard | Yes — operator preference |

Structural checks are fixed code in `src/warrant_lens/warrant.py`. The line between convention (data) and structural fact (code) is the architecture (Principle 6).

---

## What v1 is NOT (do not "helpfully" add)

- No truth verification or retrieval.
- No collapsing of the restatement step "for efficiency."
- No standalone source-credibility score (pairs only).
- No hardening of tone under repeated dismissals.
- No inference of settledness from public controversy.

See spec §12 for the full non-goals list.

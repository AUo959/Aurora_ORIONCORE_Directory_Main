# Aurora Cross-Platform Peer Review Protocol v1

## Status

**DRAFT — pending peer review by Codex.**

This document is a decision record *and* the first artifact the protocol governs:
it is a coordination-layer change (see §4 change-classes), therefore it is itself
floor-touching and must be peer-reviewed before adoption. Codex is the assigned
reviewer (see `catalog/session_state.json` → `task_queue`). If the protocol cannot
survive its own first application, that is a finding, not a failure.

- **Authored by:** Claude Code (Opus 4.8)
- **Date:** 2026-05-31
- **Reviewer:** Codex (pending)
- **Supersedes:** the emergent, ad-hoc peer review behavior described in §1.

---

## 1. Motivation — what is being formalized

Cross-platform review has already caught real defects, accidentally:

| Catch | Direction |
|---|---|
| `HeuristicClient` over-removal in `warrant-lens/pipeline.py` | Codex → Claude |
| AWS access-key-ID written into tracked `catalog/session_state.json` | Codex → Claude |
| Secret-scan rollout re-verified (gitleaks re-run) before landing | Claude → Codex |
| Stop-hook commit-churn bug (caught by verifying, not assuming) | Claude → self |

The consistent mechanism: **the second platform re-derives verification independently
and finds what the first missed.** Today this is incidental — it happens only because
both platforms habitually re-run gates. This protocol makes it deliberate, obligatory
for the right change-classes, and auditable.

## 2. Core principle

> Cross-platform peer review is **independent re-verification by the complementary
> peer**, producing **warrant-grounded findings**, recorded as an **auditable receipt**.

Each term is load-bearing:

- **Independent re-verification** — the reviewer re-runs the gates the author claims
  passed. It does not trust the author's receipt; it reproduces the result.
- **Complementary peer** — review is routed to the platform strong where the author
  is weak (§5), to cover blind spots rather than echo them.
- **Warrant-grounded findings** — inherits the Interaction Warrant Policy
  (`docs/AURORA_INTERACTION_WARRANT_POLICY_v1.md`): no approval without
  re-verification (anti-sycophancy), no objection without cited evidence
  (anti-contrarianism).
- **Auditable receipt** — every review leaves a machine- and human-readable record,
  the same way governance and rollout work already does.

## 3. The epistemic risk this must defend against

AI–AI review is powerful and uniquely failure-prone for the same reason: two models
can **share a blind spot** or **collude into false consensus**. The protocol's
defenses are structural, not aspirational:

1. **Independence requirement** — the reviewer must re-run verification itself, from
   the diff, not from the author's summary. Echoing the author's claims is not review.
2. **Evidence requirement** — every finding cites a concrete artifact (a failing test,
   a diff line, a gate output). This blocks both rubber-stamping and nitpicking.
3. **Complementary routing** — using the peer strong in the author's weak domain
   reduces shared blind spots (§5).

## 4. Change-class taxonomy (the trigger)

Review obligation scales with reliance and consequence, mirroring the ethics gate.

### Floor-touching → **mandatory review** (incurs review-debt, §6)

- **Ethics core:** `modules/ethics_field/`, `ethics/`, `src/monitoring/` gate logic,
  `tools/geometric_ethics_curvature.py`, anything altering a gate decision or threshold.
- **Security gates:** `.gitleaks.toml`, `.gitleaksignore`, `.github/workflows/secret-scan.yml`,
  secret handling, key rotation, the gitleaks/Codacy configuration.
- **Cross-repo boundary:** any mutation of a nested repo; `catalog/repo_registry.yaml`
  boundary changes; anything that could publish or entangle a separate Git boundary.
- **Git history rewrites:** force-push, rebase, `filter-repo`, squash on shared branches.
- **Coordination layer:** `catalog/session_state.json` schema, `tools/session_claim.py`,
  `tools/session_stop_hook.py`, the `.claude/settings.json` hooks, **this protocol**.
- **Invariant/floor docs:** `AGENTS.md` invariant sections, the Interaction Warrant
  Policy, `catalog/dev_toolkit_manifest.json` required-tool set.

### Significant → **recommended review** (no debt; review encouraged)

New features/tools, multi-file refactors, new skills/workflows, new CI workflows,
dependency upgrades, schema additions that are not coordination-layer.

### Mechanical → **no review**

Generated-surface refresh (manifest, workspace-map, scan summary), typo/format fixes,
doc-only non-policy edits, receipt/report files.

> **Open question for reviewer (Q1):** is this taxonomy correctly drawn? In particular,
> should "significant" be promotable to mandatory by author discretion, and is anything
> in "mechanical" actually floor-touching?

## 5. Review-by-capability routing

| Author domain | Preferred reviewer | Rationale |
|---|---|---|
| Lint/security/git-history/CI/ethics-math | **Codex** | covers Claude's blind spots |
| Governance/canon/intake/GUMAS/narrative | **Claude Code** | covers Codex's blind spots |
| General code, docs, workflows | **either** | symmetric |

Routing is a default, not a lock. The author may request a specific reviewer; the
`platform_capabilities` map in `session_state` is the source of truth for strengths.

## 6. Enforcement: the review-debt model (async, mandatory)

Hard-blocking review would deadlock against usage limits (the other platform is often
unavailable). Pure-advisory review is toothless. The chosen model is **review-debt**:
floor-changes may land, but they incur a *mandatory, tracked, gated* debt that must be
cleared by the complementary peer.

### 6.1 Incurring debt

When a floor-touching change lands, the author records a debt entry in
`catalog/session_state.json` → `review_debt[]`:

```json
{
  "id": "rd-<yyyymmdd>-<slug>",
  "commits": ["<sha>", "..."],
  "change_class": "ethics-core | security-gates | cross-repo | git-history | coordination | invariant-docs",
  "domain": "<short scope key, e.g. 'secret-handling'>",
  "author_platform": "claude-code | codex",
  "incurred_at": "<iso8601>",
  "status": "pending",
  "review_receipt": null,
  "blocks": "next floor-change in the same domain"
}
```

### 6.2 Two enforcement points (gated by `workspace_verify`)

- **G1 — debt must exist.** A floor-touching change that lands with neither a passing
  peer-review receipt nor a recorded `review_pending` debt entry → **blocking finding**.
  You cannot land a floor-change silently; you must either get it reviewed or explicitly
  record the debt.
- **G2 — debt must not stack.** A *second* floor-change in a domain that already has
  outstanding pending debt → **blocking finding with a documented escape hatch**
  (an explicit `--accept-debt-stack <reason>` recorded in the entry). Prevents silent
  pileup while not deadlocking genuine urgency.

Both are async-friendly: you are never hard-blocked from landing urgent work, but the
debt is mandatory, visible in every `verify` run, and must be cleared.

### 6.3 Clearing debt

The complementary peer reviews the change, produces a review receipt (§7), and runs
`tools/peer_review.py clear --debt-id <id> --receipt <path>`. The entry's `status`
becomes `cleared` and links the receipt. A `changes-requested` verdict keeps the debt
open and adds a follow-up task.

> **Open question for reviewer (Q2):** is "domain" the right scoping unit for debt, or
> should debt block by `change_class` (coarser) or by touched-path (finer)? Too coarse
> blocks unrelated work; too fine lets related risk slip through.

## 7. The review receipt (the artifact)

Stored under `reports/analysis/peer_reviews/<id>.json` (+ a rendered `.md`). Schema:

```json
{
  "schema_version": 1,
  "review_id": "pr-<yyyymmdd>-<slug>",
  "target": {"commits": ["<sha>"], "diff_base": "<sha>", "change_class": "...", "domain": "..."},
  "author_platform": "codex",
  "reviewer_platform": "claude-code",
  "reverified_gates": [
    {"gate": "gitleaks", "command": "...", "result": "pass|fail", "evidence": "144 commits, 0 leaks"},
    {"gate": "pytest", "command": "...", "result": "pass", "evidence": "154 passed"}
  ],
  "findings": [
    {"id": "f1", "severity": "blocking|note|nit", "evidence": "<test/diff/gate ref>",
     "description": "...", "disposition": "must-fix|accepted-with-note|waived"}
  ],
  "verdict": "approve | approve-with-notes | changes-requested | blocked",
  "warrant_level": "ambient | triggered | artifact",
  "reviewed_at": "<iso8601>"
}
```

**Non-negotiable fields:** `reverified_gates` (proves independence) and per-finding
`evidence` (proves warrant). A receipt missing either is itself invalid.

## 8. Reviewer contract (the obligations)

1. **Re-verify, don't trust.** Re-run the gates the author claims passed; record the
   commands and results in `reverified_gates`. Reproduce, don't quote.
2. **Read the diff against stated intent.** Does it do what it claims, *only* that, and
   weaken no guarantee?
3. **Warrant-ground every finding.** Cite the artifact. No evidence, no finding.
4. **Disposition each finding.** must-fix / accepted-with-note / waived.
5. **Issue a verdict and the receipt.**

## 9. Tooling plan (medium-heavy, gated)

- `catalog/workflows/peer-review.md` — operational workflow spec (the how-to).
- `catalog/schemas/peer_review_receipt.schema.json` — receipt schema (validated).
- `tools/peer_review.py` — subcommands:
  - `request` — record a review-debt entry for a floor-change.
  - `scaffold` — generate a receipt skeleton from a diff (gates pre-listed).
  - `validate` — check a receipt against schema + the non-negotiable fields.
  - `clear` — close a debt with a passing receipt.
  - `list-debt` — show outstanding debt, by domain/platform.
- `tools/workspace_verify.py` — new `verify_review_debt()` check implementing G1 + G2.
- `catalog/session_state.json` — add the `review_debt[]` array (schema bump).

> **Open question for reviewer (Q3):** should `review_debt` live in `session_state`
> (maximally visible, but grows the handoff file) or a dedicated `catalog/review_ledger.json`
> with only a summary surfaced in `session_state`?

## 10. Rollout (phased)

1. **This doc reviewed by Codex.** Adopt only after `approve` / `approve-with-notes`.
   Resolve Q1–Q3 in review.
2. Build the schema + `peer_review.py` + the `verify_review_debt` gate.
3. Add the `review_debt[]` array and the AGENTS.md pointer (held until adoption).
4. Dogfood: the first real review-debt entry is *this document's own review*.
5. Backfill: record debt for floor-changes already landed this session
   (GA curvature engine, stop-hook fix, secret-scan rollout) and clear them.

## 11. Explicit asks for the reviewer

Beyond Q1–Q3: (a) Is review-debt's G2 escape hatch too easy to abuse? (b) Does
routing-by-capability risk entrenching blind spots if one platform always reviews a
domain? (c) Is anything here over-engineered relative to a two-platform, one-operator
reality — what should be cut from v1?

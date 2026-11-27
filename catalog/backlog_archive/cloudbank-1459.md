# aurora-cloudbank-symbolic#1459: OPAL2: ship SHERLOCK / WATSON as a neutral evidence-to-understanding product

- URL: https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1459
- State at archive: open
- Author: AUo959
- Created: 2026-08-08T03:44:47Z
- Updated: 2026-09-14T09:17:35Z
- Labels: enhancement, opal2, stale, implementation-needed, backlog
- Milestone: none

## Linked pull requests (head SHA at archive time)

- aurora-cloudbank-symbolic#1460 — feat(opal2): productize SHERLOCK / WATSON evidence workflow — merged — `agent/opal2-sherlock-watson-product` @ `4709859383f311204e2467c5a5656ba659eaecf6`
- aurora-cloudbank-symbolic#1511 — feat(contracts): OPAL2 shipment-manifest schema with worked example (#1510) — merged — `codex/cloudbank-issue-1510-shipment-manifest` @ `86fde15158c5b5b02dc904c2f9d469f397c1df82`

## Branches named in the issue

- `agent/opal2-sherlock-watson-product` — not found on remote

## Original body

## Purpose

Turn the SHERLOCK -> WATSON workflow discovered during Aurora investigations into a standalone OPAL2 product surface that is useful without Aurora knowledge or runtime dependencies.

## Product identity

- **SHERLOCK — Evidence Intelligence**
- **WATSON — Contextual Intelligence**
- **SHERLOCK -> WATSON — Evidence-to-Understanding Workflow**

Aurora is development provenance and one integration profile, not a product dependency.

## Baseline implementation

Branch `agent/opal2-sherlock-watson-product` establishes the provider-neutral protocol core:

- `modules/opal2/tools/sherlock_watson.py`
  - `opal2.sherlock.casefile`
  - `opal2.watson.brief`
  - `opal2.sherlock-watson.verify`
- deterministic canonical JSON + SHA-256 case addressing;
- immutable SHERLOCK -> WATSON digest handoff;
- fail-closed mutation verification;
- neutral OPAL2 registry compatibility;
- focused integrity tests;
- standalone product and discovery-to-product documentation.

The baseline intentionally does **not** claim that it already performs autonomous web/repository retrieval or model synthesis. Those capabilities belong behind provider adapters rather than inside the portable truth/integrity contract.

## Core invariant

> WATSON may interpret an exact SHERLOCK record but may not rewrite it.

A changed SHERLOCK case produces a different digest. Existing WATSON briefs remain bound to the evidence revision they actually analyzed.

## Product modes

1. **Quick Investigate** — SHERLOCK only.
2. **Investigate + Analyze** — SHERLOCK -> locked handoff -> WATSON.
3. **Challenge Analysis** — additional WATSON brief(s) against the same SHERLOCK digest.
4. **Re-investigate** — new SHERLOCK revision; prior analysis remains historically bound.

## Remaining work

- [ ] Register SHERLOCK, WATSON, and verifier in the default OPAL2 standalone API registry.
- [ ] Add concise user-facing API/CLI commands rather than requiring generic tool-envelope knowledge.
- [ ] Define a neutral `InvestigationProvider` interface for repo/web/document/human evidence sources.
- [ ] Define a neutral `SynthesisProvider` interface for hosted/local model or human synthesis.
- [ ] Implement at least one provider pair without adding Aurora as a dependency.
- [ ] Add end-to-end fixture cases for contradiction tracing, challenge analysis, and re-investigation revisions.
- [ ] Add source/claim citation structures suitable for UI display and agent consumption.
- [ ] Export the protocol core as deterministic `.opaltool` artifacts under the existing inspect-only package boundary.
- [ ] Add a minimal UI showing locked SHERLOCK evidence adjacent to WATSON interpretation.
- [ ] Demonstrate clean-room execution in a neutral OPAL2 environment.
- [ ] Document security/privacy rules for sending source material to remote synthesis providers.
- [ ] Add capability-discovery metadata so agents can select the workflow by function, not insider naming.

## OPAL2 project principle

This issue also formalizes a larger purpose of OPAL2: when Aurora work discovers a capability with independent utility, OPAL2 should provide the extraction path from in-system capability -> neutral contract -> validation -> portable product.

See the branch documents:
- `docs/architecture/OPAL2__DISCOVERY_TO_PRODUCT_LOOP__v1.0__2026-08-07.md`
- `docs/architecture/OPAL2__PRODUCT_SPEC__SHERLOCK_WATSON__v1.0__2026-08-07.md`
- `docs/architecture/OPAL2__PRODUCTIZATION_CHECKLIST__v1.0__2026-08-07.md`

## Definition of done

A user or agent with no Aurora context can discover SHERLOCK / WATSON by capability, run the workflow through a neutral OPAL2 deployment, inspect the exact evidence record used by WATSON, challenge or repeat the interpretation without mutating evidence history, and verify the resulting artifacts end-to-end.

## Comments (2)

### AUo959 — 2026-08-08T03:48:32Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1459#issuecomment-5224359044>

Baseline implementation opened as PR #1460 (`feat(opal2): productize SHERLOCK / WATSON evidence workflow`). It implements the provider-neutral digest-bound protocol core, tests, neutral example, and the OPAL2 discovery-to-product architecture. Default API registration/provider adapters/CLI/UI/`.opaltool` clean-room proof remain tracked here rather than being overstated in the baseline.

### github-actions[bot] — 2026-09-14T09:17:34Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1459#issuecomment-5661734230>

This issue has been automatically marked as stale because it has not had activity for 30 days. It will be archived if no further activity occurs.

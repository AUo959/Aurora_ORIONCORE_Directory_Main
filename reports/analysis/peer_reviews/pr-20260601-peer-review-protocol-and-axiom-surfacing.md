# Peer Review Receipt: Protocol v1 and Axiom Surfacing

Review ID: `pr-20260601-peer-review-protocol-and-axiom-surfacing`
Reviewed at: `2026-06-01T17:49:00Z`
Reviewer: Codex
Author platform: Claude Code
Verdict: `approve-with-notes`

## Scope

- `7c5db70` - `docs/AURORA_PEER_REVIEW_PROTOCOL_v1.md`
- `977d619` - Axiom Surfacing change in `docs/AURORA_INTERACTION_WARRANT_POLICY_v1.md`
- Debt IDs cleared by this review:
  - `rd-20260531-peer-review-protocol-v1`
  - `rd-20260531-warrant-policy-axiom-surfacing`

## Reverification

- `catalog/session_state.json` confirmed the Codex queue item and both pending review-debt entries.
- `git show --stat --oneline 7c5db70` confirmed the protocol commit is a single-doc addition.
- `git show --unified=80 977d619 -- docs/AURORA_INTERACTION_WARRANT_POLICY_v1.md` confirmed Axiom Surfacing is an 11-line policy insertion.
- `git diff --stat 7c5db70..HEAD -- docs/AURORA_PEER_REVIEW_PROTOCOL_v1.md` returned empty output.
- `git diff --stat 977d619..HEAD -- docs/AURORA_INTERACTION_WARRANT_POLICY_v1.md` returned empty output.
- `python3 tools/session_claim.py check --repo root --paths catalog/session_state.json reports/analysis/peer_reviews --json` returned `status: clear`.

## Answers

Q1 taxonomy: Correct directionally. Allow author or reviewer discretion to promote a significant change to mandatory review, but only upward and with a recorded reason. Mechanical changes are safe only when they are traceable refreshes or non-semantic edits; generated output that changes routing, registry boundaries, gate behavior, or authority labels inherits the floor-touching class of the source semantic change.

Q2 debt scope: Use `domain` as the primary blocking unit for v1, with `change_class` and touched paths recorded as evidence. `change_class` alone is too coarse for a one-operator workspace, while path-only scoping is too easy to evade when related risk spans multiple files.

Q3 ledger location: Keep `review_debt` in `catalog/session_state.json` for v1. Visibility matters more than elegance while volume is low. Move cleared history to `catalog/review_ledger.json` only after the state file becomes noisy, while keeping pending debt summarized in session state.

Escape-hatch abuse: G2 is acceptable only if the tooling records a reason, operator acknowledgement or explicit urgency, stacked debt IDs, and a follow-up deadline. A bare `--accept-debt-stack <reason>` would become too easy to normalize.

Routing entrenchment: Capability routing is useful as a default but must not become a permanent domain lock. Tooling should read `catalog/session_state.json` `platform_capabilities` at request time, require a short routing rationale, and allow operator override. Repeated same-domain reviews should rotate or add an explicit second-look note when feasible.

Two-platform/one-operator cuts: Build the smallest useful path first: manual receipt, validation, `clear`, and `list` for pending debt. Defer scaffold generation, broad backfill of old debts, heavy schema evolution, and automated routing enforcement until real review volume proves they are worth carrying.

## Findings

- `f1` note: The taxonomy and debt scoping are adequate for adoption, but generated/mechanical classification must follow semantic risk rather than file label alone. Evidence: `docs/AURORA_PEER_REVIEW_PROTOCOL_v1.md` lines 71-97 and 157-159. Disposition: accepted-with-note.
- `f2` note: Section 5's routing table should not be implemented as a hard-coded authority. The protocol already names `platform_capabilities` as the source of truth, so tooling should derive routing from that state and record override rationale. Evidence: `docs/AURORA_PEER_REVIEW_PROTOCOL_v1.md` lines 99-108 and `catalog/session_state.json` `platform_capabilities`. Disposition: accepted-with-note.
- `f3` note: The G2 escape hatch needs structured guardrails before tooling lands. Evidence: `docs/AURORA_PEER_REVIEW_PROTOCOL_v1.md` lines 136-155 and 199-210. Disposition: accepted-with-note.
- `f4` note: The tooling plan is heavier than v1 needs for a two-platform, one-operator workflow. Manual receipts and a simple debt-clear/list path should precede scaffold generation, broad backfill, and automated routing enforcement. Evidence: `docs/AURORA_PEER_REVIEW_PROTOCOL_v1.md` lines 199-224. Disposition: accepted-with-note.
- `f5` note: Axiom Surfacing is approved because it names hidden premises while explicitly stopping at diminishing signal-to-noise and preserving the non-goal against formulaic interaction. Evidence: `docs/AURORA_INTERACTION_WARRANT_POLICY_v1.md` lines 148-157 and 293-303. Disposition: accepted-with-note.

## Decision

Clear both review-debt entries. The notes above are adoption constraints for the next tooling pass, not blockers to the policy/protocol changes.

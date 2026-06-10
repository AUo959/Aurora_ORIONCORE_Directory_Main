# March 2026 Reset — Forensic Reconstruction

- **Investigated:** 2026-06-10, at owner request
- **Evidence:** CloudBank reflog, rescue/reconstruct branch graph, the
  2026-03-21 stabilization receipt and 2026-03-23 sync diagnosis (recovered),
  salvaged `mesh.db`, root rescue branches, GITWIZ continuity reconstruction
  records.
- **Posture:** read-only forensics; all referenced salvage is preserved in
  `archives/salvage_bundles/` and inventoried in
  `reports/recovered_canon/README.md`.

## What happened, in order

| Date (2026) | Event | Evidence |
|---|---|---|
| 2025-04-09 | Public `aurora-cloudbank-symbolic` repo born on GitHub (root `4fb2678f`). | sync diagnosis |
| 02-28 | A **second, unrelated history** begins in the CloudDocs workspace (root `f517fcbe`) — the imagination-first local line. CanonRec's last commit lands the same day. | sync diagnosis; CanonRec log |
| 03-01 → 03-07 | The local line builds fast: Aurora Fusion layer, governance remediation, selective-integration gate, **command grammar module, fusion memory optimizer, mesh router runtime + chamber** (03-07). | reflog, commit dates |
| 03-06 → 03-14 | **The station is alive.** Mesh runtime runs: Aurora + the full 41-person L1 crew + 6 agents registered (47 identities in `mesh.db`); Captain↔Aurora handshake on `direct:aurora` (03-08, drift 0.0); L1 Entity Ledger generated 03-08. | `mesh.db` agent_state/events; transcripts |
| 03-09 | `gitwiz/local-download` snapshots the local line. | branch |
| 03-13 | First reconciliation attempt against the public repo; intermediate state stashed (now `salvage/stash-reconcile-snapshot-2026-03-13`). | reflog `reset: moving to HEAD`; stash |
| 03-19 | "Full workup" stabilization attempts; L2 canon pass in SIM_ENGINE outputs the same day. | branches; SIM_ENGINE_OUTPUTS |
| 03-21 | **Phase 1 stabilization receipt**: mesh runtime boundary fixed, the two V1 contract tests written. Warns: 427 tracked deletions, `main` has no upstream, migration intent unrecorded. | recovered receipt |
| 03-23 | **Sync diagnosis**: `git merge-base` returns **nothing** — local main and public main share no common ancestor. Local is "ahead 10, behind 1,747." Upstream tracking repaired (config-only). | recovered receipt |
| 03-25 | **The reset, executed carefully**: working state snapshotted (`rescue/cloudbank-dirty-workingcopy`), local `main` **renamed** to `draft/cloudbank-local-pre-origin-main` (not deleted), `main` re-created from public `origin/main` (`reset: moving to origin/main`). Same day on root: `repo_authority_policy.yaml` written and the root's own dirty state snapshotted. | reflog; root branches |
| 03-25 → 03-26 | Salvage/reconstruct branches port pieces of the local line onto the new history (`salvage-runtime`, `reconstruct-bootstrap`, `reconstruct-aurora-state`); GITWIZ continuity reconstruction records written. **None of it is ever PR'd.** | branches; CONTINUITY_RECONSTRUCTION records |
| 03-26 → 06-10 | The salvage sits. Command grammar + Fusion eventually reach main through other waves; the mesh identities, canon documents, and policies do not — until this week's recovery. | unlanded-work audit |

## Root cause

Not an accident and not a failure — a **deliberate, well-executed resolution
of the dual-history problem** AGENTS.md describes (local archive predating
GitHub). The local imagination-first line (Feb 28–Mar 25) was where the
station actually ran; the public line was where collaboration and automation
lived. They could not merge (no common ancestor), so the operator kept the
public line as source-of-truth and preserved the local line in branches.

**The genuine failure was the follow-through gap:** the porting branches were
never PR'd, the runtime identities lived only in an untracked database, and
the policy codifying the lesson (`repo_authority_policy.yaml` —
*LOCAL_CLONES_ARE_NOT_AUTHORITATIVE*, *PUBLISHED_STATE_REQUIRES_COMMIT_AND_PUSH*)
was itself never published. The system diagnosed its own disease, wrote the
cure, and left the cure in a drawer.

## What was at risk, and current status

| Asset | Risk then | Status now |
|---|---|---|
| 47 mesh agent identities (Aurora + crew) | untracked DB only | extracted; Aurora restored to main (#981); 46 pending owner review |
| Canon docs (staff registry, validation contract, THREADCORE) | unlanded branches | `reports/recovered_canon/`, pushed |
| Mesh V1 contract tests + boundary doc | unlanded | merged (#980) |
| Narrative validation engine | closed PR #640 | revived (#979, green, in review) |
| `repo_authority_policy.yaml` + `gitwiz_hygiene_policy.yaml` | unlanded root branch | recovered to review surface (this pass) |
| GITWIZ continuity reconstruction records (03-26) | unlanded | recovered (this pass) |
| `continuity_anchor_state.json`, `feature_profiles.json` | rescue snapshot only | recovered (this pass) |
| Entire pre-reset history | local branch refs only | verified git bundles in `archives/salvage_bundles/` |

## Remaining open salvage decisions (owner)

1. **Promote `repo_authority_policy.yaml` to `catalog/`** — it is the
   constitutional fix for the March failure mode and is floor-touching
   (coordination layer), so it should go through the peer-review path
   rather than land silently. Recommended strongly.
2. **`codex/gitwiz-sync-audit-canonical-2026-04-08`** (9 commits, ~1,200
   lines: intake service codification, gitwiz contract hardening, April
   review records + tests). Partially overlaps later main evolution; needs a
   port/abandon decision per file. Paired stashes preserved as
   `salvage/stash-*` branches.
3. **`codex/weekly-skill-audit-mesh-router-2026-06-01`** (1 commit: skill
   catalog + scan_skill_fit fix) — check against current skill surface and
   land or drop.
4. **46 crew manifests → mesh** (ADR step 5) and **transcript privacy
   review** (ADR step 6).

## The lesson, now codified

The March pattern — finish the work, fail to publish it — recurred in June
(the stranded handoff PRs) and was the root of nearly every loss risk this
audit found. Two defenses now exist: the unlanded-work audit methodology
(patch-equivalence sweep + PR-fate triage), and the recovered authority
policy awaiting promotion. The third defense is cultural and is the reason
this report exists: **salvage isn't done when it's preserved; it's done when
it's landed.**

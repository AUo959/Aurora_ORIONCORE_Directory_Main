# Aurora Reviewer Orientation v1

## Purpose

This document orients any reviewer — human, or an AI model arriving with no
prior session context — who is asked to assess this workspace, the root
control-plane repo, or any nested repo. It exists because cold reviews of this
project repeatedly make the same category errors. Read this before forming
findings.

This is orientation for *project-level* review. It complements, and does not
replace, `docs/AURORA_PEER_REVIEW_PROTOCOL_v1.md`, which governs change-level
peer review between platforms.

## Read These First (in order)

1. `README.md` — what the root repo is and is not
2. The two most recent briefs in `reports/state_briefs/` — current posture
   and open risks, so you do not rediscover known findings
3. `docs/CONTROL_PLANE_PROVENANCE.md` — why local material may predate GitHub
4. `docs/AURORA_INTERACTION_WARRANT_POLICY_v1.md` — the evidence standard
   findings are held to here
5. `catalog/repo_registry.yaml` — the authoritative nested-repo list

## Rule 1 — Review the Right Layer

This root repo is a workspace control plane over five nested Git repos. It is
metadata-first by design: manifests, policies, reports, receipts, and tooling.
It is not an application codebase and should not be graded as one.

- "Where are the tests / why so much markdown?" is a layer error at root.
  Application-code standards apply to the nested repos, not the control plane.
- The converse also holds: do not credit the nested repos with the root repo's
  governance. Each nested repo must stand on its own when reviewed directly.
- Never assume a finding about root applies to a nested repo, or vice versa.
  Name the repo in every finding.

## Rule 2 — This Project Runs Two Registers

Aurora deliberately contains both worldbuilding (THREADCORE, glyphs, named
crew, canon layers) and real engineering (verifiers, gates, middleware,
simulators). Cold reviews fail in one of two opposite ways:

- **Credulous failure:** reviewing fictional framing (e.g. "quantum memory")
  as a physics or product claim, and grading the metaphor instead of the code.
- **Dismissive failure:** pattern-matching the worldbuilding to noise and
  missing competent engineering underneath it.

The fiction/engineering boundary is itself a managed artifact here: canon
reconciliation, narrative tone governance, and layer contracts exist to police
register bleed. The reviewable question is not "is this fiction?" but "is the
boundary machinery being applied where the registers leak?" When narrative
vocabulary appears on an engineering surface (READMEs, changelogs, API names),
that is a legitimate finding; cite the surface, not the existence of the
fiction.

## Rule 3 — Know What the Actual Problem Is

The central engineering problem this workspace solves is multi-agent
coordination: several AI platforms (Claude Code, Codex, others) sharing one
filesystem and six Git repos without colliding. Session claims, the CloudBank
issue broker, command-intent envelopes, handoff commits, and receipts are the
protocol for that.

Consequences for review:

- `chore(state): record ... handoff` commits are the inter-agent message bus,
  not commit noise.
- Documentation redundancy is partly load-bearing: with memory-less agents,
  explicit repeated context is the shared memory substrate. Critique
  signal-to-noise, not document count.
- The interesting review target is the coordination protocol itself: do the
  claims, gates, and receipts actually prevent the collisions they describe?

## Rule 4 — Provenance Asymmetry

The local archive predates the GitHub history (see
`docs/CONTROL_PLANE_PROVENANCE.md`). Material in `intake/`, `archives/`, and
`_staging/` may be the only copy of early work, and is non-canonical but
potentially valuable.

- Never recommend bulk deletion of these zones. The operating rules require
  quarantine-then-verify, never direct deletion.
- "This looks like junk" is not a finding. "This candidate is indexed,
  restricted, and untriaged for N weeks" is.

## Rule 5 — Review Trends, Not Snapshots

The receipts exist to make findings longitudinal. A snapshot finding ("branch
X is dirty") is weak; a trend finding ("the same four paths have been dirty
across three consecutive briefs") is strong and is usually the real story.

Before reporting, diff your findings against the last two briefs in
`reports/state_briefs/` and the `*_latest.json` artifacts under
`reports/analysis/`:

- If a finding is already known, report its **age and trajectory**, not its
  existence.
- If a previously open risk is now closed, say so — closure is signal.
- Watch ratios over time, not states: governance-to-payload commit ratio,
  time-flagged-to-time-resolved, nested-repo staleness.

## Rule 6 — The Threat Model Behind the Gates

The pervasive read-only-by-default, mutation-requires-warrant posture is not
ceremony. The threat model is: multiple autonomous agents with shell access on
a personal machine, in a cloud-synced directory, operating across six Git
boundaries. Judge the gates against that model before calling them
over-engineered. "This gate is disproportionate to the threat model" is a
valid finding; "this is bureaucracy" without that analysis is not.

## Rule 7 — Environment Caveat

This workspace lives in iCloud Drive (`com~apple~CloudDocs`). Sync-conflict
duplicates, file eviction placeholders (`*.icloud`), and timestamp drift are
live risks to Git integrity in all six repos. If you observe anomalies
(duplicate files with conflict suffixes, missing blobs, mtime weirdness),
consider sync interference before concluding repo corruption — and flag any
such observation explicitly.

## Reviewer Posture

The warrant policy applies to reviews of this project:

- No approval without verification — re-derive claims from artifacts, do not
  quote the project's own self-assessments back as findings.
- No objection without evidence — every finding cites a file, commit, gate
  output, or receipt.
- Severity-rank findings and separate "defect" from "known, tracked, and
  aging" — the latter category is where this project's real risks usually
  live.

## Minimum Review Checklist

1. State which repo(s) you reviewed and at which HEAD.
2. Confirm you read the two latest state briefs; mark each finding
   new / known-and-aging / regressed / closed.
3. Check the layer rule: no application-code findings against the control
   plane, no control-plane credit given to nested repos.
4. Check register bleed: narrative vocabulary on engineering surfaces, with
   citations.
5. Check the coordination protocol: outstanding session claims, stale
   handoffs, unmerged platform branches, untracked feature branches.
6. Report trends and ages, not just states.

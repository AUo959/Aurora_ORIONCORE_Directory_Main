# Development restart completion and backlog triage — 2026-11-07

## Implementation and evidence

CloudBank's remaining restart work landed in PR #1679. The catalog was
reconciled against official provider model, pricing, and retirement pages.
GPT-4 is disabled after its 2026-10-23 shutdown; its mathematical fallback uses
existing GPT-4o. Sonnet 5 and GPT-4o input prices and GPT output limits were
corrected. Sources and byte digests are in CloudBank's
`docs/MODEL_CATALOG_VERIFICATION_2026-11-07.md`.

The actual local browser smoke exposed a missing system-metrics endpoint and
cross-origin default in the frontend. The fix adds process-local read-only
metrics and uses the existing Vite/reverse proxy. Unknown and missing optional
component measurements are null, rather than fabricated zeros. The dashboard
shares one snapshot poll, detects disconnects even with cached data, and
recovers when the backend returns. Retained simulation results are included in
tracked totals after completion; this is not an all-time counter.

Validation evidence before the last review refinements: full `make check`
3,687 passed / 113 skipped / 9 xfailed / 2 xpassed. Latest focused checks:
65 passed / 1 optional-dependency skip. Frontend production build and strict
lint pass. Chromium verified one initial snapshot poll, live health/models,
GPT-4 unavailable, and disconnect/recovery with no JavaScript page errors.
Required GitHub CI and merge evidence are recorded below when available.
No paid inference or authenticated provider request was used. Only temporary
local signing secrets were used for local smoke testing.

## Final landing evidence

CloudBank [PR #1679](https://github.com/AUo959/aurora-cloudbank-symbolic/pull/1679)
merged at `81fcd6ea5ea4be7f0e8f21067dba6f356e65afa0` after all applicable
checks passed. Final CI on reviewed head `a28ce451` reported **3,689 passed,
113 skipped, 9 xfailed, 2 xpassed, and 101 subtests passed**. The unexpected
passes remain visible; this restart does not claim to resolve their historical
markers. Security, frontend build, catalog verification, and Codacy checks passed.
Staging deployment was skipped; no production deployment is claimed.

The root registry now pins that merged CloudBank commit. The Orion preflight policy repository pin was aligned too, after the first
root test run caught its mismatch. Its independent test attestation was aligned to the new repository commit.
The runtime owner blob remains exactly
`5b6d93515fb219cb26d267db6c6df6c052413ae1`; the simulation tree is unchanged.
No other repo pin or canonical path changed. Earlier restart merges remain AuroraOS #14,
cloudbank-quantum-en #35, legacy symbolic1 #1, and root #102.

Root validation: 728 passed / 41 skipped; session-state schema and explicit
registry-pin checks pass. Queue health reports the retained 38 overdue reviews.

## Backlog snapshot and decisions

Live GitHub snapshot before this landing: root had 13 open PRs (10 drafts,
1 dependency update); CloudBank had 47 (5 drafts, 24 dependency updates,
16 queue proposal PRs). Counts are a snapshot, not a promise that these PRs
are mutually independent or safe to merge.

The existing queue had 39 items: 33 ready and 6 owner waits, all overdue for
review. One obsolete task was closed with source evidence:
`ace-capability-manifest-discovery`. The current core delegates to validated
manifest discovery; the allegedly hardcoded function no longer exists. The
2026-08-15 brief already recorded this implementation. No canon reconciliation
or API runtime change was needed for that closure.

A new high-priority follow-up, `gpt4o-retirement-2027-01-14`, is ready with review
on 2026-12-01. GPT-4o shuts down before the refreshed catalog's ordinary 90-day
freshness window expires. Other old dates and statuses were retained. After
these two changes: 39 open items, 33 ready, 6 waiting, 38 overdue reviews.

## Recommended next work

1. Complete the GPT-4o migration or disable it before 2027-01-14; verify any
   replacement's workload behavior, capabilities, and pricing.
2. Review CloudBank #1635 before touching queue automation. Sixteen pending
   queue proposal PRs need payload comparison and consolidation evidence;
   do not merge them chronologically into a newer live queue.
3. Review root #87's commit-provenance fix and the existing
   `registry-pin-vs-selfheal-hook` item. The current commit-recording helper can
   stamp sync-time metadata on historical commits; the pin gate and auto-heal
   policy have a documented contradiction. Keep those separate from payload work.
4. Review older feature PRs against current main one at a time. Preserve
   provenance; no blanket closure, archive deletion, or canon promotion.

## Item-by-item triage of the original queue

These are routing judgments, not evidence of completed implementations except
for the explicitly closed ACE task. Owner waits retain their existing trigger.
Remote-only/local-only branch claims cannot be resolved from this cloud clone.

| Item | Original state | Triage |
| --- | --- | --- |
| `narrative-promotion-continuation-2026-06` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `0.1-aws-key` | waiting | owner decision: retain existing evidence and wait trigger |
| `roadmap-1.1` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `p7-external-latency-divergence` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `cloudbank-review-r1r10-residual-hardening` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `qgia-runtime-onepager-route` | ready | outside restart implementation scope: retain for scoped review |
| `tobias-qin-draft-reconcile` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `archive-content-triage-450` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `kharon-sablewake-class-assignment` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `ci-dynamic-registry-pins-branch` | ready | partial implementation confirmed: ci.yml reads registry pins; branch-specific publication/retirement still needs historical evidence |
| `naming-gate-owner-records` | waiting | owner decision: retain existing evidence and wait trigger |
| `amelia-rivers-l1-check` | waiting | owner decision: retain existing evidence and wait trigger |
| `canonrec-staff-registry-authority` | waiting | owner decision: retain existing evidence and wait trigger |
| `cloudbank-mcp-v2-migration` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `warrant-lens-root-relocation` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `l2-seat-of-government-locations` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `omega9-sentinel-roster-framing` | waiting | owner decision: retain existing evidence and wait trigger |
| `sovereign-nexus-crisis-event` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `prose-ledger-open-identity-questions` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `prime-construct-ai-political-rights-doctrine` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `kaelors-rift-sentinel-command-overlap` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `sandbox-missing-test-deps` | ready | current cloud repro resolved by provisioned environments; retain canonical-machine question separately |
| `l2-location-subtype-classification` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `cloudbank-local-backlog-publication-2026-08-11` | waiting | owner decision: retain existing evidence and wait trigger |
| `ace-next-scope` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `ace-capability-manifest-discovery` | ready | Closed with source evidence: validated manifest discovery is implemented; see current core/discovery modules and 2026-08-15 brief. |
| `worktree-uncommitted-sweep` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `trade-coalition-gtc-identity` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `mekthor-nature-undetermined` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `varnaks-rest-referent` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `zharis-corridor-referent` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `gsb-uib-directorship-conflict` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `superseded-name-check-wiring` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `registry-sync-branch-field` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `registry-pin-vs-selfheal-hook` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `constellation-connectivity-publication-2026-08-19` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `gumas-phase11-controls-contract` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `prose-ledger-outcome-vocabulary-normalization` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |
| `connectivity-pass-pr-or-retire` | ready | requires focused acceptance/evidence review; no automatic renewal or completion |

## Warrant and limits

The catalog findings and local smoke results are directly observed. Backlog
routing combines live GitHub inventory with source inspection; unresolved
items are not silently promoted to completed work. Confidence is high (0.98)
for these bounded observations. Provider account access, paid responses,
production services, and unrelated canon/feature acceptance remain unverified.

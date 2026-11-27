# Aurora / ORIONCORE — Executive Decision Brief

- **Generated:** 2026-08-28
- **Scope:** Root control-plane repo + 5 local nested repos, at `~/dev/Aurora_ORIONCORE_Directory_Main`
- **Pipeline:** `aurora-exec-brief-pipeline` contract (Decision Snapshot / Top Risks / Operational Signals / Recommended Actions / Evidence Appendix)
- **Posture:** Synthesis plus actions taken — this window was heavily operational, and what was done is reported alongside what was found.
- **Staleness datum:** root HEAD `1676fd8`; CanonRec HEAD `a79dcd2`.
- **Gap since last brief:** 13 days (previous: 2026-08-15). **84 root commits**, 24 CanonRec commits.

---

## Decision Snapshot

**Overall status: GREEN. The headline is that `main` was red for twelve days and nobody knew, because the thing that made it red was a check that could never pass. Fixing it took CI from 6 failures to 0 and unblocked four PRs, one open since 1 August.**

| Dimension | State | Read |
|---|---|---|
| Root workspace integrity | `workspace_verify`: **0 blocking**, 5 warnings | ✅ Held all window |
| Aurora CI on `main` | **green** | ✅ **Resolved** — red for 10 consecutive runs from 2026-08-15 |
| Open PRs | **1** (a draft) | ✅ Was 4; two had been open 26 days |
| Publication debt | **1 live** | ✅ Was 58 |
| Local-only branches | **0** | ✅ Was 49 genuinely at risk; 99 branches verified retrievable from origin |
| Root test suite | **699 passed, 42 skipped, 1 failed** | ✅ Failure is an optional-dependency skip, see Risk 2 |
| Prose claim ledger | **948 / 1044 claims (91%)** | ✅ Was 716 (69%) |
| Canon entity records | **249** | ✅ Was 242; two recovered institutions minted |
| `qgia-knowledge-library-main` | **clean**, last commit 2026-08-15 | ✅ **Resolved** — was 5 dirty paths / 59 days, carried across four briefs |
| AWS IAM key deactivation | Pending owner since 2026-05-30 | ⚠️ **90 days** — still the longest-open owner item |

**One-line:** the workspace's constraint this window was never production — it was landing, and the landing path was blocked by a silent CI defect, a stale registry pin, and a debt ledger nobody trusted.

---

## Top Risks

### Risk 1 — Owner-gated decisions are the only remaining bottleneck (unchanged in kind, sharper in focus)

Seven queue items sit in `waiting` on the owner, three of them HIGH. One is now the *sole* remaining publication debt entry, and it costs a settings change:

- **`connectivity-branch-email-privacy`** — root `integration/connectivity-pass-2026-08-19` is the only branch in any repo with no remote copy. GitHub rejects the push with `GH007`; its three commits carry a private address in author and committer. Two options are recorded with evidence: change the email-privacy setting (no rewrite, address becomes public) or rewrite the three commits (SHAs change on a branch intended to be resumed).
- **`0.1-aws-key`** — 90 days.
- **`canonrec-staff-registry-authority`**, **`cloudbank-local-backlog-publication-2026-08-11`**.

### Risk 2 — Optional dependencies can silently zero the local suite

Found while gathering evidence for this brief. `tests/test_aurora_state_model_contract.py`, which arrived with PR #54, imported `jsonschema` at module level. CI installs it and the repo venv has it, but the macOS system Python does not — and a bare module-level import turns that absence into a **collection error that aborts the whole run**. The observable symptom was 0 tests instead of 699.

Fixed with `importorskip`, matching the convention the repo already uses in two other places. Worth noting as a class: a missing optional dependency should cost one skipped module, never the suite. The related `sandbox-missing-test-deps` item covers the environment gap but not this failure mode.

### Risk 3 — Reporting automation still absent (unchanged, fourth brief)

This brief is hand-written. `automate-executive-brief` remains queued, and `brief_freshness` had reached 84 commits before this one. The gate works; nothing acts on it.

---

## Operational Signals

### The CI defect, and why it hid

ACE capability manifests declare `refresh_on_paths`, and `_refresh_paths_unchanged()` decides staleness by diffing `pinned_sha..observed_head` over those paths. It fails closed when the range is unreadable — correct, since freshness is a safety property.

But `actions/checkout` given a `ref:` defaults to `fetch-depth: 1`. The pinned commit was simply absent, the diff errored, and **every manifest whose pin trailed the registry read as stale regardless of what changed**. The rule could never return "fresh" in CI.

Measured: 7 CanonRec commits between the pinned SHA and observed head, **zero** touching either declared refresh path, 5 tests failing. It survived because the same suite passes locally on a full clone — the failure existed only where nobody looks. Fixed across six workflows, with a regression test derived from the manifests rather than hardcoded.

### Publication debt: 58 → 1

The 2026-08-26 reconciliation (PR #83, merged this window) settled 54 of 58 entries with per-branch evidence — merged-PR head-OID matches, or `range-diff` against fetched PR heads for rebased series. The remaining stack is the four-repo connectivity pass, of which three repos are now backed up and only root's is blocked.

**A correction worth recording:** an earlier analysis in this window put 79 branches as holding unique content. That was wrong by roughly 20×. It used three-dot diffs, which have the same squash-merge blind spot as `git cherry` — for a squash-merged branch the merge base predates the squash, so content that *is* in main still reads as unique. PR-head OID matching is immune. `tools/branch_salvage_triage.py` now carries that limitation in its docstring and exits REVIEW REQUIRED rather than clean when a helper on a named call path changed.

### Canon reconciliation

The prose ledger moved from 69% to 91%. Two findings shaped the work more than the volume:

**Progress was being tracked in memory, and memory drifted.** The queue described `org_prime_construct_polity` (152 claims) as the largest open seam long after it had been fully reconciled. `tools/prose_ledger_coverage.py` now derives coverage from the records themselves, following `superseded_by` — without which every renamed entity reads as untouched.

**The world bible is itself a reconstruction.** 139 of 242 entity records carried a `recovered_source` naming exemption, and every promotion pass is a recovery verb. That inverts how referent gaps should be read: a name attested in prose with no record behind it is material the reconstruction *dropped*, not a novelty awaiting admission. Two were recovered on that basis:

- **`event_operation_silent_dagger`** — `LEDGER-MISSIONS-0001` in the committed marshals/sentinel ledger, with five named operators, their equipment, tactics, opposition, outcome and a casualty. Three records already depended on it. It had no entity.
- **`org_union_military_command`** — attested four times with a formal acronym as the Union's military command HQ'd on Kaelor Prime. Held back on first encounter until compared against all three existing military bodies; Sentinel High Command's jurisdiction is explicitly scoped to the Sentinel program, so the overarching role was vacant.

Six referent gaps remain, all thin. No command relationship was asserted for UMC — the sources name it and place it, and say nothing about its structure.

### Queue lifecycle adopted, without regressing the queue

PR #56 had been open since 1 August and could not merge as authored: it carried the 1 August `session_state.json` — a 25-item queue — which would have replaced the live 38-item one. PR #84 took the contract, tooling and tests, kept main's live data, and added the migration tool #56 never shipped, despite its own checker requiring `pending_for_next_session` to be empty.

The migration deliberately refuses to infer `approval_required`: the owner gate needs `gate_scope`, evidence and two options, and manufacturing those would fabricate a decision the owner never framed.

---

## Recommended Actions

| # | Action | Owner | Why now |
|---|---|---|---|
| 1 | Change the GitHub email-privacy setting, or authorise rewriting three commits | **Owner** | Sole remaining publication debt; the only branch with no remote copy |
| 2 | Rule on `0.1-aws-key` | **Owner** | 90 days |
| 3 | `gumas-phase11-controls-contract` — define the three determinism/substitution controls and the refusing preflight | Either | Last HIGH work item not owner-gated; execution stays blocked |
| 4 | Finish the ledger tail — 96 claims across 59 entities, none above 3 | Either | Closes a standing queue item |
| 5 | `automate-executive-brief` | Either | Fourth brief carrying this recommendation |

---

## Closures This Window

- Aurora CI on `main` — red 10 consecutive runs, now green.
- Publication debt 58 → 1, with per-branch evidence.
- 49 at-risk local-only branches → 0; 99 verified retrievable from origin.
- `qgia-knowledge-library-main` dirty paths — carried across four briefs, now clean.
- Open PRs 4 → 1; #54 and #56 had been open 26 days.
- `gumas-phase10-reporter` — closed as already complete; superseded by a Phase 11 item.
- `ace-v1-orion-owner-compatibility` — re-baselined with contract-surface evidence.
- `ace-manifest-freshness-follow-up` — resolved by the clone-depth fix.

---

## Evidence Appendix

| Claim | Evidence |
|---|---|
| CI red 10 runs from 2026-08-15 | `gh run list --branch main --workflow "Aurora CI"` |
| 7 CanonRec commits, 0 touching refresh paths | `git diff --name-only dc629a56..7581240b -- <refresh_on_paths>` |
| 54 of 58 debt entries settled | `reports/analysis/publication_debt_reconciliation__2026-08-26.md` |
| 99 branches retrievable | `ls-remote` re-read per repo, not push exit codes |
| 948/1044 claims | `tools/prose_ledger_coverage.py` |
| 139/242 recovered_source exemptions | `naming_exemption.type` census across L2 entity records |
| Silent Dagger fully attested | `canon/L2/marshals_sentinels/marshals_sentinel_ledger.md` §LEDGER-MISSIONS-0001 |
| UMC role vacant | `org_sentinel_high_command.jurisdiction` scoped to the Sentinel program |
| Suite 699 passed | `pytest tests/ -q` under the repo venv |

**Method note.** Several claims in this window were wrong on first pass and corrected on evidence — the 79-branch figure, a registry commit whose message and content disagreed because a self-healing hook overwrote it, and two "suspect" extractor matches that were both legitimate. Those corrections are recorded in the commits rather than smoothed over, because the failure mode they share — trusting a derived number without checking what produced it — is the one most likely to recur.

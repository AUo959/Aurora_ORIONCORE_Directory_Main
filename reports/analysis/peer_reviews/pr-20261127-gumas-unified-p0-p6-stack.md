# Independent review: GUMAS Unified P0-P6 stack (#1701-#1712, #1724, #1726)

- Reviewer: claude-code (author: codex)
- Reviewed: 2026-11-27T19:45:00Z
- Verdict: **changes-requested**
- Tracker: [CloudBank #1711](https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1711)
- Excluded: #1730 (Claude-authored, needs Codex review), #1506 (draft, Phase 10 incomplete)

## Heads reviewed

| PR | Head |
|---|---|
| #1701 P0 | `303a7f20` |
| #1702 P1 | `71ecd9e9` |
| #1703 P2 | `f9c036b1` |
| #1704 P3 | `bf4561c4` |
| #1724 P3 corrected | `ea32f28f` |
| #1705 P4 | `cfbd593c` |
| #1726 P4 corrected | `76167093` |
| #1706 P5 | `cfc561fb` |
| #1710 P6 | `642d5747` |
| #1712 P6 corrected | `2bfb38f3` |

## Summary

The code is behaviorally sound and well isolated, but the stack is not landable as-is. The P3 and P4 corrections (#1724, #1726) are side branches that never reached P5/P6, so the final head 2bfb38f3 still carries F821 and the old validate_protocol complexity. F401 deepcopy from P2 was never fixed, and P0/P1/P2/P5 Codacy findings remain, with Universe.validate at CC 147. The #1710 high ErrorProne is attributed (F401 federated_scenario.py:12) and fixed in #1712. Both corrections apply cleanly on top of 2bfb38f3 with 179/179 tests and identical scenario output, so the path forward is one combined candidate plus the deepcopy fix, then the P0 split (#1730, Codex review) and inherited complexity work before merge. Stack not merged; #1711 stays open.

## Reverified gates

| Gate | Result | Command | Evidence |
|---|---|---|---|
| environment | pass | `Detached worktrees of the CloudBank clone at each of the 10 heads; local Python 3.13.18 (CI uses 3.12); gh API read-only` | No live Aurora, CanonRec writes, model-provider credentials or network calls. No PR, branch or issue in CloudBank was modified. |
| stack topology | fail | `gh api pulls/{n} for the 10 PRs; git merge-base each head with origin/main` | Linear chain P0 #1701 -> main, P1..P6 each on the previous original branch, #1712 on P6. The corrected heads are side branches: #1724 sits on P2 (alternate P3), #1726 on ORIGINAL P3 bf4561c4, so neither correction is in the #1706/#1710/#1712 lineage. All heads share merge base 4a4c60b7 and are 28 commits behind main dabaa67. |
| unit suites (per head) | pass | `python -m unittest discover -s tests -p 'test_gumas_unified*.py' in each worktree` | P0 13/13; P1 26/26; P2 49/49; P3 74/74; P3fix 74/74; P4 97/97; P4fix 97/97; P5 130/130; P6 166/166; P6fix 179/179. Matches the author's 74/97/179 counts. |
| scenario scripts (per head) | pass | `python -m simulation.runtime.gumas_unified.{scenario,political_scenario,governance_scenario,distributed_scenario,federated_scenario}; sha256 of stdout` | All exit 0 on every head where present. P0 scenario 621f86f1 identical on all 10 heads. P3 53b00c23, P4 3ed92c90, P5 d67cf074 identical original vs corrected. P6 ba6121ad (original) -> c060255f (corrected); the sorted-JSON diff differs only in digest/before/after/previous/final_state hashes, consistent with #1712 adding shipment times to state without changing receipt shape. |
| P0 validator golden harness | pass | `PYTHONPATH=<head> python -m unittest discover on /mnt/project-files/gumas-p0-validator-split (golden json sha256 93bb99ed...)` | 12/12 tests, all 741 golden outcomes identical on all 10 heads. |
| Codacy (per PR, via check-run annotations) | fail | `gh api check-runs/{id}/annotations for 'Codacy Static Code Analysis' on each head (app.codacy.com API is not reachable from this environment)` | New-issue counts vs each PR's base: #1701 3, #1702 6, #1703 9, #1704 2, #1705 8, #1706 4, #1710 18, #1712 0, #1724 0, #1726 0. Codacy is action_required on all 7 original PRs. #1712/#1724/#1726 'up to standards' is relative to their own bases only. |
| #1710 high ErrorProne attribution | pass | `annotation list for #1710 check run; flake8 --select=F at 642d5747 and 2bfb38f3` | Pyflakes F401 simulation/runtime/gumas_unified/federated_scenario.py:12 '.political_scenario.p3_fixture' imported but unused. Present at 642d5747, absent at 2bfb38f3 (removed in #1712 b34ee452). Matches the tracker's 2026-11-23 attribution. |
| cumulative static check at final head | fail | `flake8 --isolated --select=F and --select=C901 --max-complexity=8; radon cc -n C, at 2bfb38f3` | F401 bindings.py:12 'copy.deepcopy' (from P2 #1703, never fixed); F821 kernel.py:140 'ReliefProposal' (from P3; fixed only in side branch #1724). 7 C901 functions; Universe.validate CC 147 (Codacy flagged 31 at P0), time_alignment 29/23/22, bindings 26/14, governance_rules.validate_protocol 20 (fixed only in side branch #1726), external_evidence 16/16/13/12/11. |
| composition of corrections (scratch only) | pass | `worktree at 2bfb38f3; git apply --3way (bf4561c4..ea32f28f) and (cfbd593c..76167093); rerun suites, scenarios, flake8 F` | Both deltas apply cleanly. 179/179 tests; all five scenario hashes identical to 2bfb38f3; F821 cleared; only F401 deepcopy remains. Nothing pushed. |
| isolation and scope | pass | `git diff --name-only 4a4c60b7 2bfb38f3; grep imports and I/O in simulation/runtime/gumas_unified` | Every changed path is under simulation/runtime/gumas_unified, simulation/specs, simulation/audits, tests/test_gumas_unified*, or .github/workflows/gumas-unified-p0.yml. Stdlib-only imports; no open/socket/requests/subprocess/environ. 2bfb38f3 merges into main without conflict (git merge-tree). |
| hosted checks | pass | `gh api commits/{sha}/check-runs for each head` | isolated-p0 (GUMAS P0-P6 workflow), GitGuardian and evaluate jobs success on all heads. SonarCloud quality gate failed on #1704 and #1705, passed elsewhere. |

## Findings

| ID | Severity | Disposition | Description | Evidence |
|---|---|---|---|---|
| f1 | blocking | must-fix | There is no single coherent head to land. The P3 and P4 corrections live on side branches and are absent from P5/P6/#1712, so landing 'in order using #1724/#1726/#1712' either drops those fixes or conflicts with the original #1704/#1705 commits that #1706+ carry. The composition gate shows they combine cleanly onto 2bfb38f3; that combined branch should be the landing candidate. | stack topology + cumulative static check gates: #1724 base f9c036b1, #1726 base bf4561c4; F821 kernel.py:140 and validate_protocol CC 20 at 2bfb38f3 |
| f2 | blocking | must-fix | F401 'copy.deepcopy' imported but unused in bindings.py:12 (introduced in P2 #1703) survives to the final head. It is the same Pyflakes class as the #1710 ErrorProne finding the tracker treated as a merge blocker. One-line fix. | Codacy annotations #1703 bindings.py:12; flake8 F401 at 2bfb38f3 |
| f3 | blocking | must-fix | Inherited P0/P1/P2/P5 Codacy complexity findings are unresolved, and Universe.validate has grown from CC 31 to 147 across the stack. #1701 targets main, so merging it lands 3 new Codacy issues on main under the repo's zero-new-issues gate. The tracker's own stated gate is to reconcile these before merging any stacked PR; the P0 split is in flight as #1730. | Codacy annotations on #1701/#1702/#1703/#1706; radon at 2bfb38f3; tracker #1711 'Next' and 'Required remediation' item 5 |
| f4 | note | accepted-with-note | The #1710 high ErrorProne finding is identified (F401 federated_scenario.py:12) and fixed in #1712. That part of the #1711 merge gate is satisfied. | #1710 high ErrorProne attribution gate |
| f5 | note | accepted-with-note | Behavior is stable: every head passes its suite, P0-P5 scenario outputs are byte-identical between original and corrected heads, and the 741-outcome P0 validator golden set is identical on all 10 heads. | unit suites, scenario scripts and golden harness gates |
| f6 | note | accepted-with-note | The stack is confined to GUMAS paths, uses only the standard library, does no I/O, and does not touch CanonRec, L1 or live services. | isolation and scope gate |
| f7 | note | accepted-with-note | Reverified on Python 3.13 locally; CI pins 3.12 and its hosted isolated-p0 runs are green on every head. Codacy was read through GitHub check-run annotations because app.codacy.com is blocked by this environment's network policy. | environment gate |
| f8 | note | accepted-with-note | #1730 (P0 validator split) is out of scope here. It is Claude-authored, so under protocol section 5 its review belongs to Codex. | PR #1730 head 397da8b4 authored by claude-code |

## Follow-up

1. Build one combined candidate: 2bfb38f3 + (bf4561c4..ea32f28f) + (cfbd593c..76167093) + drop bindings.py deepcopy import; rerun suites, scenarios and cumulative Codacy vs main.
2. Codex review of #1730 (P0 validator split).
3. Resolve or explicitly disposition the P1/P2/P5 complexity findings before any PR in the stack merges to main.

## Addendum: combined candidate #1735

Head `fcc0bd2b` (2bfb38f3 + (bf4561c4..ea32f28f) + (cfbd593c..76167093) + drop bindings.py deepcopy import + merge main dabaa67). f1 and f2 resolved on #1735; f3 open. Verdict unchanged (changes-requested) until f3 is fixed or explicitly waived by the owner.

| Gate | Result | Evidence |
|---|---|---|
| unit suite | pass | 179/179 |
| scenario scripts | pass | 621f86f1, 53b00c23, 3ed92c90, d67cf074, c060255f: identical to 2bfb38f3 |
| P0 golden harness | pass | 12/12, 741 outcomes identical |
| pyflakes | pass | clean; f1 F821 and f2 F401 resolved |
| hosted checks | pass | isolated-p0, test, build, guardrails, GitGuardian, PR evaluation (0.91) success |
| Codacy vs main | fail | 25 new issues: 23 medium Complexity, 2 minor markdown table style; 0 high or ErrorProne. Largest: Universe.validate CC 147 / 245 LOC; time_alignment 29/23/22; bindings 26/14; external_evidence 16/16/13/12/11; kernel.advance_to 16. |

## Owner decision

On 2026-11-27 at 19:32 UTC, the owner chose to merge now and keep #1711 open. #1735 squash-merged as `e0c41a86`. #1701–#1706, #1710, #1712, #1724 and #1726 are closed as superseded. Finding f3 is accepted as tracked debt in #1711.

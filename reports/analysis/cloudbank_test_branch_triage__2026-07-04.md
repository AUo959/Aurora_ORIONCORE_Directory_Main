# CloudBank Test-Branch Triage — 2026-07-04

Triage of the three test-improvement branches in the landing ledger,
per the publication-debt protocol (publish, retire deliberately, or
exempt). Evaluation was done in a clean detached worktree against
`origin/main` (464de5b6 era, post PR #1182 merge); the dirty canonical
CloudBank checkout was not used as an edit surface.

## Dispositions

### 1. `local/mesh-router-test-stabilization` — RETIRED (superseded)
- Tip: `f941aea93841881962373704cae5356bbb51fe99` (1 commit,
  `test(mesh): stabilize async router acknowledgements`, +34/−21)
- Finding: main already contains an equivalent and stronger adaptation —
  `_all_agent_ids` / `_channel_agent_ids` fixture-derived helpers plus a
  10s `agent_reply` polling deadline sized for the 47-agent roster. The
  branch's variant polls only ~1s for the weaker `agent_ack` condition.
  Rebase conflicted in all 5 hunks, each with a better in-main twin.
- Action: local and remote branch deleted. Tip SHA above is the
  recovery handle during the hosting provider's reflog window.

### 2. `codex/cloudbank-salvage-p2-ord-tests-2026-06-15` — RETIRED (landed)
- Tip: `2588a0eaea58cc7c6a65001cc9a044327d27a312` (1 commit,
  `test(ord): pin salvage threshold behaviors`, +41)
- Finding: rebase onto main dropped the commit as already applied; both
  added test methods (`test_encoding_anomaly_requests_normalization`,
  `test_high_risk_mission_enables_quantum_seal_controls`) exist verbatim
  on main, and `tests/ord/` passes 17/17 there. The ledger's
  "pushed" classification was stale — no matching remote ref existed.
- Action: local branch deleted (nothing existed on origin).

### 3. `copilot/replace-shallow-assertions-tier1` — EXEMPTED (retired in place)
- Tip: `bc9d21bbc66412b5cb1daff26fa15d5c85c3b355` (18 bot commits from
  2026-06-12, +204/−31 net across 7 test files)
- Finding: the transformation is predominantly `assert x` →
  `if not x: raise AssertionError(...)` — a mechanical Bandit-B101
  appeasement that loses pytest assertion introspection and conflicts
  with the repo's since-adopted convention (unittest.TestCase assertion
  methods, established by the PR #1182 B101 fix). Rebase conflicts in 10
  files after three weeks of main drift. A minority of hunks are
  genuinely behavioral upgrades; those are better re-derived fresh under
  the current convention than merged through this stack.
- Action: exemption recorded in `catalog/publication_debt_exemptions.yaml`;
  remote branch kept as the archival copy. Do not merge.

## Follow-up seed

If shallow-assertion hardening is wanted, start a fresh lane against
current main using TestCase assertion methods (the PR #1182 convention),
scoped to the four quantum/ethics test files with the highest bare-assert
counts (test_quantum_core.py 63, test_monitoring_system.py 44,
test_quantum_decision_oracle.py 40, test_ethics_engine.py 34).

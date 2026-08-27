# Publication Debt Reconciliation — 2026-08-26

## Receipt

- Canonical audit root: `/Users/travisstreets/dev/Aurora_ORIONCORE_Directory_Main`
- Live GitHub identity: `AUo959`
- Remote refresh: `gitwiz_sync_audit.py --repo all --fetch --check-gh-auth`
- Initial non-exempt debt: **58 branch entries**
- Evidence-settled here: **54 entries**
- Remaining actionable stack: **4 entries**, all named
  `integration/connectivity-pass-2026-08-19`
- Publication, merge, close, comment, and branch deletion were not inferred
  from an exemption. An exemption records that publication already happened or
  that a stale state-only branch was deliberately retired in place.

The live scan was conservative by design: a squash-merged branch whose remote
head was deleted still appears `stranded_branch`, while a retained remote head
with no *open* PR appears `unpublished_branch`. Live all-state PR history, local
tip OIDs, fetched PR head objects, and `git range-diff` were therefore used to
separate actual debt from retained parallel history.

## Exact local-tip matches

Every row below was confirmed `MERGED` by GitHub, and the current local branch
tip equals the PR's recorded head OID.

### Root

| Local branch | Tip | Merged PR |
|---|---:|---:|
| `agent/github-auth-context-hardening` | `68a4bf13` | #42 |
| `agent/root-license-session-closeout` | `ea3ec49f` | #58 |
| `agent/root-mit-community-profile` | `616cc66f` | #57 |
| `codex/charforge-capsule-implementation-2026-06-14-rebased` | `fcc418da` | #38 |
| `codex/public-readiness-closeout-2026-08-01` | `5a1d8a5f` | #55 |
| `codex/root-cloudbank-pin-refresh-2026-07-29` | `820b0f24` | #51 |
| `codex/root-public-metadata-2026-07-29` | `7467781a` | #53 |
| `fix/ci-dynamic-registry-pins` | `b3bb45c2` | #41 |

### CloudBank

| Local branch | Tip | Merged PR |
|---|---:|---:|
| `agent/aurora-bridge-review-blurb` | `29f683f3` | #1447 |
| `claude/architecture-advancements-review-v2cxi0` | `a47f1a61` | #1194 |
| `codex/cloudbank-canonrec-provenance-2026-07-29` | `9485a06b` | #1385 |
| `codex/cloudbank-codeql-backlog-2026-07-29` | `a49304a3` | #1388 |
| `codex/cloudbank-high-dependabot-2026-07-29` | `9978ab80` | #1389 |
| `codex/cloudbank-issue-1024-instance-bridge-role-closure` | `2a55142f` | #1249 |
| `codex/cloudbank-issue-1056-opal2-standalone-topology` | `ae5051d6` | #1251 |
| `codex/cloudbank-issue-1131-reconcile-closed-queue-items` | `e3f77238` | #1250 |
| `codex/cloudbank-issue-1139-ethics-readme-index` | `78b0898f` | #1197 |
| `codex/cloudbank-issue-1140-topology-qgia-reconcile` | `952fcb23` | #1198 |
| `codex/cloudbank-issue-1142-api-catalog-snapshot-regeneration` | `b17d0bf4` | #1203 |
| `codex/cloudbank-issue-1143-scaling-topology-reconcile` | `09aef951` | #1199 |
| `codex/cloudbank-issue-1144-api-surface-inventory-reconcile` | `edf55408` | #1201 |
| `codex/cloudbank-issue-1145-rd-api-reference-refresh` | `01bbea8b` | #1202 |
| `codex/cloudbank-issue-1146-governance-self-audit` | `8e1388a2` | #1205 |
| `codex/cloudbank-issue-1161-coordination-spine-reconcile` | `c6a86571` | #1196 |
| `codex/cloudbank-issue-1231-qgia-axiom-reconcile` | `8d5bc0ec` | #1262 |
| `codex/cloudbank-issue-1231-qgia-docs-surface` | `4619c989` | #1266 |
| `codex/cloudbank-issue-1231-qgia-index-wiring` | `3cc1fd0a` | #1270 |
| `codex/cloudbank-issue-1231-qgia-roadmap` | `8ac3ca64` | #1274 |
| `codex/cloudbank-issue-1232-docs-cross-reference-module-coverage` | `beb5d701` | #1252 |
| `codex/cloudbank-issue-1235-repo-structural-naming-cleanup` | `a277d5a7` | #1253 |
| `codex/cloudbank-issue-1247-halo-residual-canon` | `9e378fef` | #1258 |
| `codex/cloudbank-issue-1247-halo-system-activation` | `c5f844c8` | #1259 |
| `codex/cloudbank-issue-1255-src-structure-audit` | `97aabec7` | #1261 |
| `codex/cloudbank-issue-1257-onboarding-module` | `0f0b20df` | #1260 |
| `codex/cloudbank-issue-1342-pr-evaluation-blocking` | `1f5e590b` | #1490 |
| `codex/cloudbank-issue-1362-root-test-contract` | `a28f4b87` | #1489 |
| `codex/cloudbank-issue-1403-diagnostics-test-hygiene` | `15618ee5` | #1486 |
| `codex/cloudbank-issue-1424-qgia-casefold-hygiene` | `7beef423` | #1488 |
| `codex/cloudbank-issue-1446-gate-registry-coherence` | `b0c96de3` | #1487 |
| `codex/cloudbank-issue-1460-opal2-codacy-table-spacing` | `5cf98b15` | #1485 |
| `codex/cloudbank-issue-1481-postmerge-1482-hardening` | `18dc169d` | #1500 |
| `codex/public-readiness-debt-2026-07-29` | `76eb57e3` | #1386 |

### CanonRec

| Local branch | Tip | Merged PR |
|---|---:|---:|
| `agent/canonrec-mit-license` | `eac36f0c` | #8 |
| `codex/canonrec-public-readiness-2026-07-29` | `b50086d2` | #6 |
| `codex/canonrec-strict-integrity-recovery-2026-07-29` | `510d5a2b` | #9 |
| `codex/public-vulnerability-reporting-2026-07-29` | `6357fff3` | #7 |

## Rebased or superseded CloudBank series

These seven local tips do not equal the final merged PR head because the PR was
rebased, amended to clear review gates, or continued after the local ref was
left behind. Fetched PR-head objects and `git range-diff` establish the local
series as equal to or a strict subset of the merged work.

| Local branch | Local evidence | Merged publication |
|---|---|---:|
| `codex/cloudbank-issue-1020-mesh-router-contract` | `afb5fa8e` equals first PR commit; PR adds `1fe934f2` | #1191 |
| `codex/cloudbank-issue-1384-mcp-server-compat` | aggregate stable patch-id equals PR series | #1392 |
| `codex/cloudbank-issue-1393-native-vsa-correctness` | both local commits range-match PR commits; aggregate stable patch-id equal | #1397 |
| `codex/ga-ethics-hub-integration-2026-07-08` | both local commits range-match first two PR commits; PR adds three hardening commits | #1193 |
| `codex/l2-scenario-seed-simulation-initializer` | adapter commit range-matches #1182; later branch commits match/subset #1190; current main supersedes the final test-only delta | #1182, #1190 |
| `codex/mesh-security-lint-hardening-2026-07-22` | all three local commits range-match; PR adds the hashed-lock dependency fix | #1306 |
| `codex/narrative-phase2-evidence-2026-07-04` | local commit range-matches first PR commit; PR adds two gate fixes | #1183 |

For the scenario branch, the only tip-to-main file difference is three lines on
`tests/test_scenario_seed_initializer.py`: current main adds `import pytest` and
`pytestmark = pytest.mark.unit`. The local tip does not contain unpublished
behavior beyond the two merged PRs.

## Deliberately retired state-only branch

`codex/cloudbank-backlog-handoff-20260810` contains four commits and changes
only `catalog/session_state.json`. It ends with the 2026-08-10 CloudBank draft
backlog receipt. Current main has a newer structurally merged session ledger
through 2026-08-20, and the canonical checkout has a further 2026-08-26 refresh.
Publishing the older snapshot would regress queue and receipt state. The branch
is retired in place; it was not deleted.

## Remaining actionable publication stack

The only non-exempt branch debt after this decision set is the coordinated
`integration/connectivity-pass-2026-08-19` stack:

| Repo | Tip | Scope |
|---|---:|---|
| `aurora-cloudbank-symbolic-main` | `cb35bfc5` | event schema, publisher, router, health audit |
| `qgia-knowledge-library-main` | `4f3a8bd1` | repair knowledge-index publish gate |
| `qgia-knowledge-spine-main` | `7856e43a` | schema-valid, non-duplicate hub dispatch |
| `root` | `6349b1f8` | control-plane node, registry durability/bootstrap, audit receipt |

The root branch's own receipt requires publication and later merge in this
order: **hub → spine and library → root**. The GUMAS recovery branch explicitly
describes this stack as "unpushed and deliberately paused" and removes its
local-only SHAs from registry pins so unrelated work can land independently.
The four refs remain actionable debt until their named repositories are
authorized for publication and each branch is refreshed and validated against
its current `origin/main`.

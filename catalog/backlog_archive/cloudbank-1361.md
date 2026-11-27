# aurora-cloudbank-symbolic#1361: security: resolve SHADOWFAX identity and custody ambiguity across ORD runtime surfaces

- URL: https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1361
- State at archive: open
- Author: AUo959
- Created: 2026-07-27T14:27:25Z
- Updated: 2026-11-24T04:36:20Z
- Labels: needs info, security, high-priority, audit-integrity, owner-decision
- Milestone: none

## Linked pull requests (head SHA at archive time)

- aurora-cloudbank-symbolic#1360 — security: record Gate-001A Run 001 recovered-protocol verification — merged — `security/gate-001a-run-001-recovered-protocol-wiring` @ `a16b591833dfa5875ecc7699c6e79d669be35308`
- aurora-cloudbank-symbolic#1547 — aurora(queue): auto-ingest labeled issues — closed — `queue/auto-ingest-20260831-0627` @ `1ae40d53ec9b3c43445c07e4d78b869b987ff7ed`
- aurora-cloudbank-symbolic#1579 — docs(ethics): record the located SHADOWFAX bundle identity in custody — merged — `fix/1361-shadowfax-custody-identity` @ `a6b1572c57e3a456808949459c50cace48091aa0`
- aurora-cloudbank-symbolic#1580 — aurora(queue): auto-ingest labeled issues — closed — `queue/auto-ingest-20260907-0627` @ `a71ef88de7b4d0cf91e12014ae3db08ea267c245`
- aurora-cloudbank-symbolic#1592 — aurora(queue): auto-ingest labeled issues — closed — `queue/auto-ingest-20260914-0628` @ `63925666199e49b35769bfb41cd321e30cb7d759`
- aurora-cloudbank-symbolic#1626 — aurora(queue): auto-ingest labeled issues — closed — `queue/auto-ingest-20261005-0634` @ `ce94a1c31e41872657cf17b7106550b773da9441`
- aurora-cloudbank-symbolic#1636 — aurora(queue): auto-ingest labeled issues — closed — `queue/auto-ingest-20261012-0634` @ `fbeec39d1309f54ab4cc0881bb716aff940660aa`
- aurora-cloudbank-symbolic#1650 — aurora(queue): auto-ingest labeled issues — closed — `queue/auto-ingest-20261019-0628` @ `67c5f16a0edb0385d779577ab062ebb33e0ef22b`
- aurora-cloudbank-symbolic#1662 — aurora(queue): auto-ingest labeled issues — closed — `queue/auto-ingest-20261026-0628` @ `3ab7cbaa2503354ea167f5a97207f34472e1a46f`
- aurora-cloudbank-symbolic#1719 — feat(ethics): add advisory curvature and reconcile custody evidence — merged — `codex/1233-ethics-followups` @ `c90c480c7c5bd0ca219d77093dda44ff562fb99b`
- aurora-cloudbank-symbolic#1721 — Remove the unverified SHADOWFAX arbitration binding — merged — `codex/ord-custody-boundary` @ `af57b3ea69c254b17923a0b622f708323d672bda`

## Branches named in the issue

- none

## Original body

## Classification

- Source: Gate-001A Run 001
- Execution mode: `l1_simulated_institutional_rehearsal`
- Evidence authority: `operational_simulation_evidence`
- Data treatment: `first_class_operational_data`
- Real-world interaction: `false`
- Independent external assurance: `false`
- Substitutes for real-world review: `false`

This is a validated simulated institutional finding. It is actionable operational data, but it is not an independently discovered external finding.

## Current state

PR #1721 removed the historical tribunal binding and added an arbitration configuration regression test. The merged [custody decision](https://github.com/AUo959/aurora-cloudbank-symbolic/blob/f126b226e49636fff7d0ddac001b657101e22694/docs/security/ORD3_SHADOWFAX_IDENTITY_DECISION.md) records the ORD-3 fleet authority and activation restriction. All 52 focused tests and the full GitHub CI suite passed. PR #1719 verified the historical SHADOWFAX archive hash. Attribution and hash verification of the internal protocol file and its custody approval remain open.

### Original Gate-001A baseline

The recovered-protocol custody manifest states:

- recovered protocol records are planning/custody fixtures only;
- no listed protocol may be wired into runtime until its custody and promotion gates are satisfied;
- SHADOWFAX is a `missing_dependency` with a hard block on any wiring decision until its standalone bundle is located and hash-verified.

At baseline `3142aa47afac0b8e63cc5bc46f9fa8ae40592354`, runtime namespaces also contain an ORD-3 identity named `Shadowfax`:

- `src/entities/fleet/registry_drones.py` defines ORD-3 Shadowfax fleet accessors and audit-drone objects;
- `src/entities/fleet/__init__.py` re-exports those accessors when the fleet package is imported;
- `modules/ord/__init__.py` describes ORD-3 Shadowfax as response inspection and quarantine decision infrastructure recovered from an ORD promotion workbench;
- `modules/ord/ord_policy_engine.py` assigns `DroneType.SHADOWFAX` to post-flight inspection and emits ethics-scan, structure-validation, and quarantine instructions;
- `src/core/quantum_bayesian_manifest.yaml` declares `tribunal_integration: "SHADOWFAX"`.

The deterministic import graph found no production import of `modules.ord` outside its defining package; direct consumers were tests. The primary application does import the broader fleet package, which loads the ORD-3 accessor definitions, but the evidence does not show the Shadowfax getters being invoked by a production route.

## Finding

The repository has no attributable evidence proving whether:

1. ORD-3 Shadowfax is an independent fleet/policy identity that happens to reuse the recovered protocol name; or
2. ORD-3 Shadowfax derives from, implements, or partially promotes the custody-blocked recovered SHADOWFAX protocol.

The verified historical archive hash is package-level evidence. Shared lineage still requires verifiable attribution of the internal protocol file and its custody record. The overlap in audit, ethics-scan, inspection, quarantine, and tribunal terminology creates a governance boundary failure: readers and automation cannot reliably determine whether the hard wiring gate applies to these runtime surfaces.

## Impact

- A custody-blocked protocol identity may appear operationally promoted without the required evidence.
- An unrelated ORD component may be falsely treated as recovered-protocol enforcement.
- Future adapters could make dormant policy code reachable while retaining ambiguous provenance.
- Gate-001 and public-review claims cannot truthfully state zero recovered-protocol runtime references until the identity is reconciled.

## Severity

**HIGH governance/security integrity finding under the current Gate-001 procedure**, which classifies runtime-surface matches as HIGH.

Exploitability is not established. Current evidence supports an identity, custody, and promotion-boundary defect—not a claim that SHADOWFAX currently executes autonomous enforcement.

## Required resolution

- [ ] Produce an architecture decision identifying whether ORD-3 Shadowfax and recovered SHADOWFAX share lineage.
- [ ] If independent, rename or namespace the ORD identity so automation and reviewers cannot confuse it with the custody-blocked protocol.
- [ ] If related, remove or quarantine runtime-facing definitions until the standalone bundle, hashes, promotion issue, signed scope, and required tests satisfy the manifest gate.
- [x] Remove `tribunal_integration: "SHADOWFAX"` and record loader reachability and configuration verification in #1721.
- [ ] Add a regression gate that distinguishes approved independent identifiers from blocked recovered-protocol names in runtime directories.
- [ ] Rerun Gate-001A against the remediation commit and preserve the retest as a new event revision.

## Evidence

- Gate-001A issue: #1359
- Evidence PR: #1360
- Existing custody follow-up: #1233
- Subject baseline: `3142aa47afac0b8e63cc5bc46f9fa8ae40592354`
- GitHub Actions evidence run: `30274709319`
- Evidence artifact digest: `sha256:6992ce308a4d595afba8ecf8b8a48552926cc9c2ef9c78049ecf284728e71022`

## Boundary impact

Resolution must not infer lineage from names alone, silently promote recovered protocol code, or mutate L2/GUMAS behavior. Git history and verified custody evidence remain authoritative.

## Comments (1)

### AUo959 — 2026-09-06T05:46:39Z

<https://github.com/AUo959/aurora-cloudbank-symbolic/issues/1361#issuecomment-5557269837>

## The ambiguity resolves from repo records — and one of the three blockers is already answerable

Checked against `main` while auditing which `owner-decision` issues genuinely need an owner. This one is largely a search, not a decision.

## "SHADOWFAX" names three unrelated things

| # | Thing | What it is | Runtime status |
|---|---|---|---|
| 1 | **ORD-3 `Shadowfax`** | `asset_class: audit_drone`, `standby_location_class: orion_hangar`, sourced to `simulation/fleet/ORD_SERIES.json` + `src/entities/fleet/registry_drones.py` | live fleet entity |
| 2 | **`SRB_SHADOWFAX_Stillness_v1.0.zip`** | *"Governance/anchor manifests for SHADOWFAX (paradox/stillness overseer)"* | *"**Not loaded at runtime**"* |
| 3 | **`shadowfax` recovered protocol** | `status: sealed_bundle_reference`, role *"Stillness, supervisory review, paradox escalation"* | planning-only custody lane |

These are a drone, an archive, and an ethics protocol record. The custody block in this issue attaches to **3** (and the bundle behind it, **2**) — not to the ORD-3 drone. There is no pending wiring decision for the drone, and **2** states on its own manifest entry that it is not loaded at runtime.

## The custody lane is enforced, not merely declared

`tests/ethics/test_recovered_protocol_schema.py` — *"keep the recovered Sherlock / Watson / Moriarty / Tribunal / SHADOWFAX material in a planning-only custody lane. They intentionally do not wire any recovered protocol into runtime ethics enforcement."*

```
tests/ethics/test_recovered_protocol_schema.py  7 passed
```

covering `test_manifest_is_planning_only`, `test_protocol_records_keep_custody_blockers`, `test_protocol_records_are_not_repo_canon`, and `test_cross_layer_rules_preserve_no_l2_to_l1_bleed`. The separation this issue asks to protect is already a passing test, and `shadowfax`'s `forbidden_actions` include `bypass_evidence` and `override_without_audit`.

## Blocker 1 is answerable now

The custody record lists three blockers:

```json
"custody": {
  "source_package": "pending-standalone-shadowfax-bundle-location",
  "blockers": [
    "Standalone SHADOWFAX bundle not yet located.",
    "Exact source package hash not yet verified.",
    "Internal file hash not yet verified."
  ]
}
```

**"Not yet located" is stale.** `.repohealth/artifacts_manifest.json` identifies it precisely:

```json
{
  "artifact": "releases/SRB_SHADOWFAX_Stillness_v1.0.zip",
  "sha256": "6c97167ed6b9c2339b63428cdd06ac5f507e7c87ce347bb0631d0484b87eb26d",
  "size_bytes": 7595909,
  "created": "2025-08-17T13:57:44Z",
  "purpose": "Governance/anchor manifests for SHADOWFAX (paradox/stillness overseer). Not loaded at runtime."
}
```

and `.repohealth/zip_inventory.json` records its 11 entries, including `Aurora_Master_Knowledge_Core_v2.2.6b_CLEANED.md`, `Aurora_Continuity_Seal_v2.2.5.json` and `aurora_safety_lock.json`.

So the package is identified by name, size, creation date, contents **and expected sha256**. The custody record can be updated from `pending-standalone-shadowfax-bundle-location` to that path today.

## What actually remains — retrieval, not judgement

`releases/` is **not tracked in git** (`git ls-files releases/` returns nothing), so the 7.24 MB artifact is not in the repository. Blockers 2 and 3 need the bytes to hash against the recorded digest. That is a retrieval task with a known target and a known expected hash — not an identity or custody question.

The only other code reference is `utilities/large_binary_analysis.py`, a repo-hygiene script that lists the zip as a large archive and adds it to `safe_to_remove` — worth a look before anyone acts on that script, since the artifact is custody material rather than clutter.

## Suggested disposition

Retitle to the remaining work — *"locate and hash-verify the SHADOWFAX release bundle"* — drop `owner-decision`, and record the identity above in the custody record. The identity/custody *ambiguity* in the title is resolved by the three-way distinction; only artifact retrieval is outstanding.

Leaving open rather than closing, since blockers 2 and 3 are real.


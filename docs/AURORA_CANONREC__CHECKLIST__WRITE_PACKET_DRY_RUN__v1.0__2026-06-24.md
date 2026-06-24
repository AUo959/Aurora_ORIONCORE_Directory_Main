# Aurora CanonRec Write-Packet Dry-Run Checklist

**Version:** v1.0  
**Date:** 2026-06-24  
**Status:** Template / dry-run gate  
**Tracking issue:** #31  

## Purpose

This checklist controls the final preparation step before any CanonRec branch is opened from a bridge packet.

It is deliberately conservative. A packet may be well-formed and still not safe to execute if provenance, ethics, continuity, target path, or rollback evidence is weak.

## Required preflight

- [ ] The candidate has a clear layer: L1, L2, or L3.
- [ ] The candidate has a concrete CanonRec target path.
- [ ] The candidate operation is `create` or `update`; v1 does not allow delete/remove.
- [ ] For updates, the current CanonRec blob SHA has been fetched immediately before packet finalization.
- [ ] Duplicate CanonRec issues/PRs have been checked.
- [ ] Directory_Main tracking issue exists.
- [ ] No private credential material is present in packet, receipt, PR body, or logs.

## Evidence gate

- [ ] Evidence receipt exists.
- [ ] Evidence receipt has stable ID, hash, or durable artifact pointer.
- [ ] Evidence supports the claim being promoted.
- [ ] Missing evidence is labeled `UNKNOWN` or `ASSUMPTION`, not silently upgraded.
- [ ] Chat output alone is not treated as canon evidence.
- [ ] Recovered archive text has provenance and review notes.

## Layer boundary gate

### L1

- [ ] Operational-reality constraints are preserved.
- [ ] Simulation or symbolic material is not imported as physical fact.
- [ ] Command authority, safety, and station realism are not expanded without evidence.

### L2

- [ ] GUMAS determinism is not changed unless explicitly intended and validated.
- [ ] Scenario prompts/seeds are not treated as canon facts.
- [ ] Post-run evidence, ethics review, and continuity review are present for any L2 outcome claim.

### L3

- [ ] THREADCORE/capsule/ethics material is recorded as governance or symbolic mesh logic.
- [ ] L3 material does not override L1 operational reality.
- [ ] L3 material does not force L2 simulation outcomes.

## Ethics gate

- [ ] Ethics gate status is PASS or explicitly reviewed.
- [ ] The packet does not claim enforcement unless code/tests or canon authority support it.
- [ ] Picard_Delta_3 implications are stated when relevant.
- [ ] Agency, consent, and safety risks are labeled where relevant.

## Continuity gate

- [ ] Names, IDs, roles, and paths do not conflict with existing CanonRec records.
- [ ] Legacy aliases are labeled as legacy/superseded when retained.
- [ ] Drift traces are preserved instead of erased.
- [ ] The packet explains why this belongs in CanonRec rather than only Directory_Main or CloudBank.

## Validator gate

Run:

```bash
python3 tools/canonrec_bridge_validate.py --packet reports/automation/AURORA_CANONREC__PACKET__<TOPIC>__vX.X__YYYY-MM-DD.json --summary
```

- [ ] Validator status is `valid`.
- [ ] Any warnings are reviewed and recorded.
- [ ] Packet remains read-only until owner approves the specific CanonRec branch/PR action.

## CanonRec branch gate

Before opening a CanonRec branch:

- [ ] Owner has approved this specific candidate for CanonRec branch creation.
- [ ] Branch name is descriptive and scoped.
- [ ] PR will be draft by default.
- [ ] PR body includes source evidence, target paths, validation, risks, rollback, and merge approval language.
- [ ] Merge remains blocked without explicit owner instruction.

## Post-merge gate

If a CanonRec PR later lands:

- [ ] Run Directory_Main canon sync drift check.
- [ ] Identify CloudBank mirror impact.
- [ ] Open a separate CloudBank PR only if needed.
- [ ] Do not batch unrelated cleanup into mirror PR.
- [ ] Record final disposition in Directory_Main.

## Hard stop conditions

Stop if any of the following are true:

- Target repo or path is uncertain.
- Current file SHA is missing for an update.
- Evidence receipt is missing.
- L1/L2/L3 boundary is ambiguous.
- Ethics or continuity gate is missing.
- Packet requests deletion/removal.
- Packet requests CloudBank mirror mutation directly.
- Private credential material appears anywhere in the proposed change.
- Owner approval is absent for CanonRec branch or merge.

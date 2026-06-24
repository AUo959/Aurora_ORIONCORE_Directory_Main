# Prepared CanonRec Draft PR Body — ORION.ENTITY.0008 Maya Shepard Addenda Normalization

> Prepared in Directory_Main for review only. No CanonRec branch has been opened by this packet.

## Summary

Normalize the `Constellation Addenda (reference/staging)` section in `canon/L1/characters/ORION.ENTITY.0008__maya-shepard.md` so the existing reference content is easier to review.

This candidate should preserve the existing Maya Shepard canon record. It should not expand role authority, alter command status, change L1 identity, or change legacy alias handling.

## Canon target paths

- `canon/L1/characters/ORION.ENTITY.0008__maya-shepard.md`

Current target blob at dry-run preparation:

- `96b8b2ae44268d6efaef818b4c26386cfa0e0269`

## Source evidence

- Directory_Main `reports/analysis/L1_ENTITY_LEDGER__2026-06-10.json`, lines 100-145.
- CanonRec `canon/L1/characters/ORION.ENTITY.0008__maya-shepard.md`, lines 1-52.
- Directory_Main packet: `reports/automation/AURORA_CANONREC__PACKET__ORION_ENTITY_0008_MAYA_SHEPARD_ADDENDA_NORMALIZATION_DRY_RUN__v1.0__2026-06-24.json`.
- Directory_Main receipt: `reports/analysis/AURORA_CANONREC__RECEIPT__ORION_ENTITY_0008_MAYA_SHEPARD_ADDENDA_NORMALIZATION_DRY_RUN__v1.0__2026-06-24.md`.

## Layer classification

- Layer: L1
- Entity: `ORION.ENTITY.0008`
- Name: Lt. Commander Maya Shepard
- Role: Executive Officer (XO)
- Division: Command & Ethics

## Intended content posture

- Preserve front matter.
- Preserve summary.
- Preserve responsibilities.
- Preserve legacy role aliases.
- Preserve legacy drift trace.
- Reformat the reference/staging addenda into a reviewable structure.
- Do not add new canon facts.

## Validation to perform before opening this PR for review

```bash
python3 tools/canonrec_bridge_validate.py --packet reports/automation/AURORA_CANONREC__PACKET__ORION_ENTITY_0008_MAYA_SHEPARD_ADDENDA_NORMALIZATION_DRY_RUN__v1.0__2026-06-24.json --summary
```

Expected result:

- status: `valid`

## Risks

- The addenda content is reference/staging, so formatting should not accidentally imply stronger authority.
- Any truncated or ambiguous reference text should be preserved or explicitly flagged rather than silently repaired.
- This candidate should be abandoned if the addenda source cannot be represented without loss.

## Rollback

If this candidate is later opened and rejected before merge, close the CanonRec PR with an evidence note.

If a later accepted change needs reversal, use a normal revert commit in CanonRec.

## Merge approval

This prepared body does not itself authorize a CanonRec PR or merge. A future CanonRec PR still requires explicit owner approval for the specific branch and target change.

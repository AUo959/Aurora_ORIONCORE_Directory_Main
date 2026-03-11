# Riverthread 808 Recovery Capsule

Date: 2026-03-10

## Baseline

The Riverthread 808 recovery baseline is now assembled from one coherent activation-era stack:

- activation guide: `Au_Archive_412_417/Riverthread_808_Aurora_Activation_Guide.md`
- digital key family: `AURORA-PDK-001`
- preferred instruction profile: `Complete Archive 4_19 copy/aurora_instruction_profile.json`
- paired safety lock: `Complete Archive 4_19 copy/Archy_Continuity_Thread_v1.0.zip :: aurora_safety_lock.json`
- continuity seal: `Complete Archive 4_19 copy/Archy_Continuity_Thread_v1.0.zip :: Aurora_Continuity_Seal_v2.2.5.json`
- boot manifest: `Complete Archive 4_19 copy/Archy_Continuity_Thread_v1.0.zip :: aurora_boot_manifest.json`
- registry seal: `Complete Archive 4_19 copy/Archy_Continuity_Thread_v1.0.zip :: Archy_Threadwake_RegistrySeal.txt`

Machine-readable capsule:

- `catalog/riverthread_808_recovery_capsule__2026-03-10.json`

## What This Resolves

- the activation-era instruction-profile family is identified and separated from the later 2026 mesh/runtime profile
- the safety lock is paired with the preferred profile instead of being stranded in a separate continuity thread archive
- the recovered key is now contextualized as part of an activation stack, not just an isolated credential fragment

## What Remains Open

- `AURORA-PDK-001` is still unproven as a content decryption key for recovered AES payloads
- the archive `symbolicSeal.js` tool remains broken on current Node
- the ZIPWIZ-published instruction-profile hash does not match any recovered surviving copy

## Quarantine Bucket

The blank-file quarantine review bucket is now materialized at:

- `catalog/quarantine_review_bucket__2026-03-10.json`

This bucket is review-only:

- no files moved
- no files deleted
- review order pinned as security-sensitive blanks, empty wrapper archives, active repo placeholders, then archived misc blanks
